from dataclasses import dataclass
from itertools import chain
from typing import Tuple, Dict, List, Set, Optional

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
    label_to_bool_matrix: Dict[str, Matrix] = {}
    start_states: Indices
    final_states: Indices

    def __init__(self, edges: List[Edge],
                 start_states: Optional[Indices] = None,
                 final_states: Optional[Indices] = None):
        label_to_edges: Dict[str, Tuple[Indices, Indices]] = {}
        label_to_bool_matrix: Dict[str, Matrix] = {}
        for edge in edges:
            I, J = label_to_edges.setdefault(edge.label, ([], []))
            I.append(edge.node_from)
            J.append(edge.node_to)
        for label, (I, J) in label_to_edges.items():
            label_to_bool_matrix[label] = Matrix.from_lists(I, J, [True] * len(I), typ=types.BOOL)
        self.label_to_bool_matrix = label_to_bool_matrix
        if start_states is None:
            start_states = list(range(self.vertices_num))
        self.start_states = start_states
        if final_states is None:
            final_states = list(range(self.vertices_num))
        self.final_states = final_states

    @classmethod
    def from_list_of_edges(cls, edges: List[Edge]):
        return cls(edges)

    @classmethod
    def from_file(cls, path_to_file: str):
        edges = []
        with open(path_to_file, 'r') as input_file:
            for line in input_file.readlines():
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
            other_matrix.resize(nrows=step, ncols=step)
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
                matrix.resize(nrows=self.vertices_num, ncols=self.vertices_num)
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
                matrix.resize(nrows=self.vertices_num, ncols=self.vertices_num)
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
