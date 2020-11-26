from collections import deque
from dataclasses import dataclass
from itertools import chain
from typing import Tuple, Dict, List, Set, Optional, Any

from pyformlang.cfg import Terminal, Variable
from pyformlang.finite_automaton import State, Symbol, NondeterministicFiniteAutomaton
from pygraphblas import Matrix, semiring
from pygraphblas import binaryop
from pygraphblas import types

from wrappers import GrammarWrapper

Indices = List[int]


@dataclass(eq=True, frozen=True)
class Edge:
    node_from: int
    node_to: int
    label: Any


class GraphWrapper:

    def __init__(self, edges: List[Edge],
                 start_states: Optional[Set[int]] = None,
                 final_states: Optional[Set[int]] = None):
        label_to_edges: Dict[Any, Tuple[Indices, Indices]] = {}
        label_to_bool_matrix: Dict[Any, Matrix] = {}
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
            start_states = self.vertices
        self.start_states = start_states
        if final_states is None:
            final_states = self.vertices
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
            vertex_from, label, vertex_to = line.strip().split(' ')
            edges.append(Edge(node_from=int(vertex_from),
                              node_to=int(vertex_to),
                              label=label))
        return cls(edges)

    @classmethod
    def empty(cls):
        return cls(edges=[], start_states=set(), final_states=set())

    @classmethod
    def _from_label_to_bool_matrix(cls, label_to_bool_matrix: Dict[Any, Matrix]):
        instance = cls(edges=[])
        instance.label_to_bool_matrix = label_to_bool_matrix
        instance.matrix_size = instance.vertices_num
        for _, matrix in instance.label_to_bool_matrix.items():
            matrix.resize(instance.matrix_size, instance.matrix_size)
        return instance

    @property
    def vertices_num(self) -> int:
        maximums = [max(matrix.ncols, matrix.nrows) for matrix in self.label_to_bool_matrix.values()]
        return 0 if not maximums else max(maximums)

    @property
    def edges_counter(self) -> Dict[Symbol, int]:
        return {label: matrix.nvals for label, matrix in self.label_to_bool_matrix.items()}

    def kronecker_product(self, other):
        label_to_kronecker_product: Dict[Any, Matrix] = {}
        step = other.matrix_size
        empty_matrix = Matrix.sparse(typ=types.BOOL, nrows=step, ncols=step)
        for label, matrix in self.label_to_bool_matrix.items():
            other_matrix: Matrix = other.label_to_bool_matrix.get(label, empty_matrix.dup())
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

    def cfpq_hellings(self, grammar: GrammarWrapper) -> Set[Tuple[int, int]]:
        result: Dict[Variable, Matrix] = {}
        working_queue = deque()
        if grammar.generate_epsilon:
            result[grammar.cfg.start_symbol] = Matrix.sparse(types.BOOL, self.vertices_num, self.vertices_num)
            for v in self.vertices:
                result[grammar.cfg.start_symbol][v, v] = True
                working_queue.append((v, v, grammar.cfg.start_symbol))
        with semiring.LOR_LAND_BOOL:
            for label, matrix in self.label_to_bool_matrix.items():
                for prod in grammar.cnf.productions:
                    if len(prod.body) == 1 and Terminal(label) == prod.body[0]:
                        if prod.head in result:
                            result[prod.head] += matrix.dup()
                        else:
                            result[prod.head] = matrix.dup()
                        for i, j, _ in matrix:
                            working_queue.append((i, j, prod.head))
        while len(working_queue) != 0:
            node_from, node_to, var = working_queue.popleft()
            update = []
            for var_before, matrix in result.items():
                for node_before, _ in matrix[:, node_from]:
                    for prod in grammar.cnf.productions:
                        if (len(prod.body) == 2
                                and prod.body[0] == var_before
                                and prod.body[1] == var
                                and (prod.head not in result
                                     or result[prod.head].get(node_before, node_to) is None)):
                            update.append((node_before, node_to, prod.head))
            for var_after, matrix in result.items():
                for node_after, _ in matrix[node_to]:
                    for prod in grammar.cnf.productions:
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
        return set([(i, j) for i, j, _ in result.get(grammar.cfg.start_symbol, [])])

    def cfpq_matrices(self, grammar: GrammarWrapper) -> Set[Tuple[int, int]]:
        result: Dict[Variable, Matrix] = {}
        if grammar.generate_epsilon:
            result[grammar.cfg.start_symbol] = Matrix.sparse(types.BOOL, self.vertices_num, self.vertices_num)
            for v in self.vertices:
                result[grammar.cfg.start_symbol][v, v] = True
        term_productions, nonterm_productions = set(), set()
        for production in grammar.cnf.productions:
            if len(production.body) == 2:
                nonterm_productions.add(production)
            elif len(production.body) == 1:
                term_productions.add(production)
        with semiring.LOR_LAND_BOOL:
            for label, matrix in self.label_to_bool_matrix.items():
                for production in term_productions:
                    if Terminal(label) == production.body[0]:
                        if production.head in result:
                            result[production.head] += matrix.dup()
                        else:
                            result[production.head] = matrix.dup()
            has_changed = True
            while has_changed:
                has_changed = False
                for production in nonterm_productions:
                    if production.body[0] not in result or production.body[1] not in result:
                        continue
                    if production.head not in result:
                        result[production.head] = Matrix.sparse(types.BOOL, self.matrix_size, self.matrix_size)
                    old_nvals = result[production.head].nvals
                    result[production.head] += result[production.body[0]] @ result[production.body[1]]
                    has_changed |= result[production.head].nvals != old_nvals
        return set([(i, j) for i, j, _ in result.get(grammar.cfg.start_symbol, [])])

    def cfpq_tensors(self, grammar: GrammarWrapper, from_wcnf=False) -> Set[Tuple[int, int]]:
        current_cfg = grammar.wcnf if from_wcnf else grammar.cfg
        import wrappers.RFA
        rfa = wrappers.RFA.from_cfg(current_cfg)
        return self._cfpq_tensors_from_rfa(rfa)

    def _cfpq_tensors_from_rfa(self, rfa):
        empty_matrix = Matrix.sparse(types.BOOL, self.matrix_size, self.matrix_size)
        result = {label: matrix.dup() for label, matrix in self.label_to_bool_matrix.items()}
        for (state_from, state_to), head in rfa.head_by_start_final_pair.items():
            if state_from == state_to:
                result[head] = empty_matrix.dup()
                for v in self.vertices:
                    result[head][v, v] = True
        for prod in rfa.eps_productions:
            result[prod.head] = empty_matrix.dup()
            for v in self.vertices:
                result[prod.head][v, v] = True
        result = GraphWrapper._from_label_to_bool_matrix(result)
        has_changed = True
        while has_changed:
            tensor_product = rfa.graph.kronecker_product(result)
            closure = tensor_product.build_closure_by_squaring()
            has_changed = False
            for i, j, _ in closure:
                if i in tensor_product.start_states and j in tensor_product.final_states:
                    i_graph, j_graph = i % result.matrix_size, j % result.matrix_size
                    i_rfa, j_rfa = i // result.matrix_size, j // result.matrix_size
                    var = rfa.head_by_start_final_pair[i_rfa, j_rfa]
                    matrix = result.label_to_bool_matrix.setdefault(var, empty_matrix.dup())
                    if not matrix.get(i_graph, j_graph, False):
                        has_changed = True
                    matrix[i_graph, j_graph] = True
        return set([(i, j) for i, j, _ in result.label_to_bool_matrix.get(rfa.start_symbol, [])])
