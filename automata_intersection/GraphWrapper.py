from dataclasses import dataclass
from itertools import chain
from typing import Tuple, Dict, List, Set, Optional

from pyformlang.finite_automaton import State, Symbol, NondeterministicFiniteAutomaton
from pygraphblas import Matrix, semiring, Accum
from pygraphblas import binaryop
from pygraphblas import types

Indices = List[int]


@dataclass(eq=True, frozen=True)
class Edge:
    node_from: int
    node_to: int
    label: str


class GraphWrapper:
    """A class for storing graphs in the form of sparse matrices.

    Each graph is represented by mapping between edge labels and sparse boolean `pygraphblas.Matrix`.
    """
    label_to_bool_matrix: Dict[str, Matrix] = {}
    start_states: Optional[Indices]
    final_states: Optional[Indices]

    def __init__(self, edges: List[Edge],
                 start_states: Optional[List[int]] = None,
                 final_states: Optional[List[int]] = None):
        label_to_edges: Dict[str, Tuple[Indices, Indices]] = {}
        label_to_bool_matrix: Dict[str, Matrix] = {}
        for edge in edges:
            I, J = label_to_edges.setdefault(edge.label, ([], []))
            I.append(edge.node_from)
            J.append(edge.node_to)
        for label, (I, J) in label_to_edges.items():
            label_to_bool_matrix[label] = Matrix.from_lists(I, J, [1] * len(I))
        self.label_to_bool_matrix = label_to_bool_matrix
        self.start_states = start_states
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
        return max([max(matrix.ncols, matrix.nrows) for matrix in self.label_to_bool_matrix.values()])

    @property
    def edges_counter(self) -> Dict[Symbol, int]:
        return {label: matrix.nvals for label, matrix in self.label_to_bool_matrix.items()}

    def kronecker_product(self, other):
        label_to_kronecker_product: Dict[str, Matrix] = {}
        step = other.vertices_num
        empty_matrix = Matrix.sparse(typ=types.INT64, nrows=step, ncols=step)
        for label, matrix in self.label_to_bool_matrix.items():
            other_matrix: Matrix = other.label_to_bool_matrix.get(label, empty_matrix)
            other_matrix.resize(nrows=step, ncols=step)
            result_matrix = matrix.kronecker(other=other_matrix, op=binaryop.TIMES)
            label_to_kronecker_product[label] = result_matrix
        intersection = GraphWrapper._from_label_to_bool_matrix(label_to_kronecker_product)
        if self.start_states is not None:
            intersection.start_states = list(set(chain(*map(
                lambda idx: [idx * step + i for i in range(step)],
                self.start_states
            ))))
        if self.final_states is not None:
            intersection.final_states = list(set(chain(*map(
                lambda idx: [idx * step + i for i in range(step)],
                self.final_states
            ))))
        return intersection

    def get_reachability_matrix(self) -> Matrix:
        adj_matrix = Matrix.sparse(types.BOOL, self.vertices_num, self.vertices_num)
        for _, matrix in self.label_to_bool_matrix.items():
            matrix.resize(nrows=self.vertices_num, ncols=self.vertices_num)
            adj_matrix = adj_matrix.eadd(matrix, add_op=binaryop.LOR)
        with semiring.LOR_LAND_BOOL, Accum(binaryop.LOR):
            reachability_matrix = Matrix.identity(types.BOOL, nrows=self.vertices_num)
            for i in range(self.vertices_num):
                reachability_matrix @= adj_matrix
        return reachability_matrix

    def get_reachable_pairs(self, start_indices: Set[int], end_indices: Set[int]):
        reachability_matrix = self.get_reachability_matrix()
        result: List[Tuple[int, int]] = []
        for start_index in start_indices:
            for end_index in end_indices:
                if reachability_matrix.get(start_index, end_index, False):
                    result.append((start_index, end_index))
        return result

    def to_nfa(self, start_states: List[int], final_states: List[int]):
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
