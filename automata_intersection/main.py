import argparse
import json
from collections import Counter
from dataclasses import dataclass
from itertools import chain
from typing import Tuple, Dict, List, Optional, Set

from pyformlang.finite_automaton import EpsilonNFA, DeterministicFiniteAutomaton, State
from pyformlang.regular_expression import Regex
from pygraphblas import Matrix
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

    def __init__(self, edges: List[Edge]):
        label_to_edges: Dict[str, Tuple[Indices, Indices]] = {}
        label_to_bool_matrix: Dict[str, Matrix] = {}
        for edge in edges:
            I, J = label_to_edges.setdefault(edge.label, ([], []))
            I.append(edge.node_from)
            J.append(edge.node_to)
        for label, (I, J) in label_to_edges.items():
            label_to_bool_matrix[label] = Matrix.from_lists(I, J, [1] * len(I))
        self.label_to_bool_matrix = label_to_bool_matrix

    @classmethod
    def from_list_of_edges(cls, edges: List[Edge]):
        return cls(edges)

    @classmethod
    def from_file(cls, path_to_file: str):
        with open(path_to_file, 'r') as input_file:
            edges = []
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
    def vertices_num(self):
        return max([max(matrix.ncols, matrix.nrows) for matrix in self.label_to_bool_matrix.values()])

    def collect_paths(self, start_indices: Set[int], end_indices: Set[int]):
        edge_labels_counter = Counter()
        for start_index in start_indices:
            used = [False] * self.vertices_num
            result = []
            self.__dfs(start_index, used, end_indices, result)
            edge_labels_counter.update(Counter([edge.label for edge in result]))
        return edge_labels_counter

    def __dfs(self, start_index: int, used: List[bool], end_indices: Set[int], result: List[Edge]):
        used[start_index] = True
        for label, matrix in self.label_to_bool_matrix.items():
            if start_index < matrix.nrows:
                for to_index, _ in matrix[start_index]:
                    result.append(Edge(start_index, to_index, str(label)))
                    if not used[to_index]:
                        self.__dfs(to_index, used, end_indices, result)


class AutomatonGraphWrapper(GraphWrapper):
    dfa: DeterministicFiniteAutomaton
    dfa_state_to_idx: Dict[State, int]

    def __init__(self, epsilon_nfa: EpsilonNFA):
        edges = []
        dfa = epsilon_nfa.to_deterministic()
        state_to_idx = dict([(state, index) for index, state in enumerate(dfa.states)])
        for state_from, transitions in epsilon_nfa.to_deterministic().to_dict().items():
            for label, state_to in transitions.items():
                edges.append(Edge(node_from=state_to_idx[state_from], node_to=state_to_idx[state_to], label=label))
        self.dfa = dfa
        self.dfa_state_to_idx = state_to_idx
        super().__init__(edges)

    def kronecker_product(self, other: GraphWrapper) -> GraphWrapper:
        label_to_kronecker_product: Dict[str, Matrix] = {}
        empty_matrix = Matrix.sparse(typ=types.INT64,
                                     nrows=len(self.label_to_bool_matrix),
                                     ncols=len(self.label_to_bool_matrix))
        for label, matrix in self.label_to_bool_matrix.items():
            other_matrix = other.label_to_bool_matrix.get(label, empty_matrix)
            result_matrix = matrix.kronecker(other=other_matrix, op=binaryop.TIMES)
            label_to_kronecker_product[label] = result_matrix
        return GraphWrapper._from_label_to_bool_matrix(label_to_kronecker_product)

    @property
    def final_states_indices(self) -> List[int]:
        return [self.dfa_state_to_idx[state] for state in self.dfa.final_states]

    @property
    def start_states_indices(self) -> List[int]:
        return [self.dfa_state_to_idx[state] for state in self.dfa.start_states]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_graph",
                        help="input file with list of edges of the graph in format 'v_from label v_to'")
    parser.add_argument("path_to_regex",
                        help="input file with corresponding regex (see `pyformlang.regular_expression.Regex`)")
    parser.add_argument("path_to_query",
                        help="input file with specified set of vertices in the input graph "
                             "using regex for finding reachability")
    args = parser.parse_args()
    graph = GraphWrapper.from_file(args.path_to_graph)
    with open(args.path_to_regex, 'r') as file:
        line = file.readline()
        regex_epsilon_nfa = Regex(regex=line).to_epsilon_nfa()
        constraint = AutomatonGraphWrapper(regex_epsilon_nfa)
    with open(args.path_to_query, 'r') as file:
        query = json.load(file)
    result = constraint.kronecker_product(graph)

    constraint_start_idxs = constraint.start_states_indices
    step = graph.vertices_num
    all_start_idxs = set(chain(*map(
        lambda idx: [idx * step + i for i in range(step)],
        constraint_start_idxs
    )))
    all_end_idxs = set(range(result.vertices_num))

    if query.get('reachability_between_all'):
        edge_labels_counter = result.collect_paths(all_start_idxs, all_end_idxs)
        print(json.dumps(edge_labels_counter))
    elif "reachability_from_set" in query:
        graph_start_idxs = set(query.get("reachability_from_set"))
        start_idxs = set([idx for idx in all_start_idxs if (idx % step) in graph_start_idxs])
        edge_labels_counter = result.collect_paths(start_idxs, all_end_idxs)
        print(json.dumps(edge_labels_counter))


if __name__ == '__main__':
    main()
