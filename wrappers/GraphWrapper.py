from collections import deque
from dataclasses import dataclass
from itertools import chain
from typing import Tuple, Dict, List, Set, Optional

from pyformlang.cfg import CFG, Terminal, Variable
from pyformlang.finite_automaton import State, Symbol, NondeterministicFiniteAutomaton
from pygraphblas import Matrix, semiring
from pygraphblas import binaryop
from pygraphblas import types

Indices = List[int]


@dataclass(eq=True, frozen=True)
class Edge:
    node_from: int
    node_to: int
    label: str


class GraphWrapper:

    def __init__(self, edges: List[Edge],
                 start_states: Optional[Indices] = None,
                 final_states: Optional[Indices] = None):
        label_to_edges: Dict[str, Tuple[Indices, Indices]] = {}
        label_to_bool_matrix: Dict[str, Matrix] = {}
        self.vertices = set()
        for edge in edges:
            I, J = label_to_edges.setdefault(edge.label, ([], []))
            I.append(edge.node_from)
            J.append(edge.node_to)
            self.vertices.add(edge.node_from)
            self.vertices.add(edge.node_to)
        max_size = 0 if not self.vertices else max(self.vertices) + 1
        self.matrix_size = max_size
        for label, (I, J) in label_to_edges.items():
            label_to_bool_matrix[label] = Matrix.from_lists(I=I, J=J, V=[True] * len(I),
                                                            ncols=max_size, nrows=max_size, typ=types.BOOL)
        self.label_to_bool_matrix = label_to_bool_matrix
        if start_states is None:
            start_states = list(self.vertices)
        self.start_states = start_states
        if final_states is None:
            final_states = list(self.vertices)
        self.final_states = final_states

    @classmethod
    def from_list_of_edges(cls, edges: List[Edge]):
        return cls(edges)

    @classmethod
    def from_file(cls, path_to_file: str):
        with open(path_to_file, 'r') as input_file:
            return cls.from_text(input_file.readlines())

    @classmethod
    def from_text(cls, text: List[str]):
        edges = []
        for line in text:
            vertex_from, label, vertex_to = line.split(' ')
            edges.append(Edge(node_from=int(vertex_from),
                              node_to=int(vertex_to),
                              label=label))
        return cls(edges)

    @classmethod
    def _from_label_to_bool_matrix(cls, label_to_bool_matrix: Dict[str, Matrix]):
        instance = cls(edges=[])
        instance.label_to_bool_matrix = label_to_bool_matrix
        return instance

    @property
    def vertices_num(self) -> int:
        maximums = [max(matrix.ncols, matrix.nrows) for matrix in self.label_to_bool_matrix.values()]
        return 0 if not maximums else max(maximums)

    @property
    def edges_counter(self) -> Dict[Symbol, int]:
        return {label: matrix.nvals for label, matrix in self.label_to_bool_matrix.items()}

    def kronecker_product(self, other):
        label_to_kronecker_product: Dict[str, Matrix] = {}
        step = other.vertices_num
        empty_matrix = Matrix.sparse(typ=types.BOOL, nrows=step, ncols=step)
        for label, matrix in self.label_to_bool_matrix.items():
            other_matrix: Matrix = other.label_to_bool_matrix.get(label, empty_matrix)
            result_matrix = matrix.kronecker(other=other_matrix, op=binaryop.TIMES)
            label_to_kronecker_product[label] = result_matrix
        intersection = GraphWrapper._from_label_to_bool_matrix(label_to_kronecker_product)
        intersection.start_states = list(set(chain(*map(
            lambda idx: [idx * step + i for i in range(step)],
            self.start_states
        ))))
        intersection.final_states = list(set(chain(*map(
            lambda idx: [idx * step + i for i in range(step)],
            self.final_states
        ))))
        return intersection

    def build_closure_by_squaring(self) -> Matrix:
        closure = Matrix.sparse(types.BOOL, self.vertices_num, self.vertices_num)
        prev_nvals = closure.nvals
        with semiring.LOR_LAND_BOOL:
            for _, matrix in self.label_to_bool_matrix.items():
                closure += matrix
            while prev_nvals != closure.nvals:
                prev_nvals = closure.nvals
                closure += closure @ closure
        return closure

    def build_closure_by_adj_matrix_multiplication(self) -> Matrix:
        adj_matrix = Matrix.sparse(types.BOOL, self.vertices_num, self.vertices_num)
        prev_nvals = adj_matrix.nvals
        with semiring.LOR_LAND_BOOL:
            for _, matrix in self.label_to_bool_matrix.items():
                adj_matrix += matrix
            closure = adj_matrix.dup()
            while prev_nvals != closure.nvals:
                prev_nvals = closure.nvals
                closure += adj_matrix @ closure
        return closure

    def get_reachable_pairs(self, from_indices: Set[int], to_indices: Set[int]):
        reachability_matrix = self.build_closure_by_squaring()
        result: List[Tuple[int, int]] = []
        for from_index in from_indices:
            for to_index in to_indices:
                if reachability_matrix.get(from_index, to_index, False):
                    result.append((from_index, to_index))
        return result

    def to_nfa(self, start_states: Indices, final_states: Indices):
        self.start_states = start_states
        self.final_states = final_states
        nfa = NondeterministicFiniteAutomaton()
        states = [State(idx) for idx in range(self.vertices_num)]
        symbols = {label: Symbol(label) for label in self.label_to_bool_matrix}
        for start_idx in start_states:
            nfa.add_start_state(states[start_idx])
        for end_idx in final_states:
            nfa.add_final_state(states[end_idx])
        for label, matrix in self.label_to_bool_matrix.items():
            for i, j, _ in zip(*matrix.to_lists()):
                nfa.add_transition(states[i], symbols[label], states[j])
        return nfa

    def cfpq_hellings(self, cfg: CFG) -> Set[Tuple[int, int]]:
        result: Dict[Variable, Matrix] = {}
        working_queue = deque()
        if cfg.generate_epsilon():
            result[cfg.start_symbol] = Matrix.sparse(types.BOOL, self.vertices_num, self.vertices_num)
            for v in self.vertices:
                result[cfg.start_symbol][v, v] = True
                working_queue.append((v, v, cfg.start_symbol))
        cfg = cfg.to_normal_form()
        for label, matrix in self.label_to_bool_matrix.items():
            for prod in cfg.productions:
                if len(prod.body) == 1 and Terminal(label) == prod.body[0]:
                    result[prod.head] = matrix.dup()
                    for i, j, _ in zip(*matrix.to_lists()):
                        working_queue.append((i, j, prod.head))
        while len(working_queue) != 0:
            node_from, node_to, var = working_queue.popleft()
            update = []
            for var_before, matrix in result.items():
                for node_before, _ in matrix[:, node_from]:
                    for prod in cfg.productions:
                        if (len(prod.body) == 2
                                and prod.body[0] == var_before
                                and prod.body[1] == var
                                and (prod.head not in result
                                     or result[prod.head].get(node_before, node_to) is None)):
                            update.append((node_before, node_to, prod.head))
            for var_after, matrix in result.items():
                for node_after, _ in matrix[node_to]:
                    for prod in cfg.productions:
                        if (len(prod.body) == 2
                                and prod.body[0] == var
                                and prod.body[1] == var_after
                                and (prod.head not in result
                                     or result[prod.head].get(node_from, node_after) is None)):
                            update.append((node_from, node_after, prod.head))
            for node_from, node_to, var in update:
                working_queue.append((node_from, node_to, var))
                if var in result:
                    result[var][node_from, node_to] = True
                else:
                    empty_matrix = Matrix.sparse(types.BOOL, self.vertices_num, self.vertices_num)
                    result[var] = empty_matrix
                    result[var][node_from, node_to] = True
        return set([(from_node, to_node) for from_node, to_node, _ in result.get(cfg.start_symbol, [])])

    def cfpq_matrices(self, cfg: CFG) -> Set[Tuple[int, int]]:
        result: Dict[Variable, Matrix] = {}
        if cfg.generate_epsilon():
            result[cfg.start_symbol] = Matrix.sparse(types.BOOL, self.vertices_num, self.vertices_num)
            for v in self.vertices:
                result[cfg.start_symbol][v, v] = True
        cfg = cfg.to_normal_form()
        term_productions, nonterm_productions = set(), set()
        for production in cfg.productions:
            if len(production.body) == 2:
                nonterm_productions.add(production)
            else:
                term_productions.add(production)
        for label, matrix in self.label_to_bool_matrix.items():
            for production in term_productions:
                if Terminal(label) == production.body[0]:
                    result[production.head] = matrix.dup()
        has_changed = True
        while has_changed:
            for production in nonterm_productions:
                if production.body[0] not in result or production.body[1] not in result:
                    continue
                if production.head not in result:
                    result[production.head] = Matrix.sparse(types.BOOL, self.matrix_size, self.matrix_size)
                old_nvals, has_changed = result[production.head].nvals, False
                result[production.head] += result[production.body[0]] @ result[production.body[1]]
                has_changed |= result[production.head].nvals != old_nvals

        return set([(from_node, to_node) for from_node, to_node, _ in result.get(cfg.start_symbol, [])])

# if __name__ == '__main__':
#     grammar = GrammarWrapper.from_text(['S A B', 'S A C', 'C S B', 'A a', 'B b'])
#     graph = GraphWrapper.from_text(['1 a 2', '2 a 0', '0 a 1', '0 b 3', '3 b 0'])
#     print(graph.cfpq_matrices(grammar.cfg))
