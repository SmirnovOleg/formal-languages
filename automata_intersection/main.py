import argparse
from dataclasses import dataclass
from typing import Tuple, Dict, List

from pyformlang.finite_automaton import EpsilonNFA
from pyformlang.regular_expression import Regex
from pygraphblas import Matrix
from pygraphblas import binaryop
from pygraphblas import types

Indices = List[int]


@dataclass
class Edge:
    node_from: int
    node_to: int
    label: str


class GraphWrapper:
    """A class for storing graphs in the form of sparse matrices.

    Each graph is represented by mapping between edge labels and sparse boolean `pygraphblas.Matrix`.
    """
    label_to_bool_matrix: Dict[str, Matrix] = {}

    def __init__(self, label_to_bool_matrix: Dict[str, Matrix]):
        self.label_to_bool_matrix = label_to_bool_matrix

    @classmethod
    def from_file(cls, path_to_file: str):
        with open(path_to_file, 'r') as input_file:
            edges = []
            for line in input_file.readlines():
                vertex_from, label, vertex_to = line.split(' ')
                edges.append(Edge(node_from=int(vertex_from),
                                  node_to=int(vertex_to),
                                  label=label))
        return cls.from_list_of_edges(edges)

    @classmethod
    def from_list_of_edges(cls, edges: List[Edge]):
        label_to_edges: Dict[str, Tuple[Indices, Indices]] = {}
        label_to_bool_matrix: Dict[str, Matrix] = {}
        for edge in edges:
            I, J = label_to_edges.setdefault(edge.label, ([], []))
            I.append(edge.node_from)
            J.append(edge.node_to)
        for label, (I, J) in label_to_edges.items():
            label_to_bool_matrix[label] = Matrix.from_lists(I, J, [1] * len(I))
        return cls(label_to_bool_matrix)

    @classmethod
    def from_epsilon_nfa(cls, epsilon_nfa: EpsilonNFA):
        edges = []
        dfa = epsilon_nfa.to_deterministic()
        states_to_idx = dict([(state, index) for index, state in enumerate(dfa.states)])
        for state_from, transitions in epsilon_nfa.to_deterministic().to_dict().items():
            for label, state_to in transitions.items():
                edges.append(Edge(node_from=states_to_idx[state_from], node_to=states_to_idx[state_to], label=label))
        return cls.from_list_of_edges(edges)

    def get_intersection(self, other):
        """Return the intersection of graphs (automata) using kronecker product."""
        label_to_kron_product: Dict[str, Matrix] = {}
        empty_matrix = Matrix.sparse(typ=types.INT64,
                                     nrows=len(self.label_to_bool_matrix),
                                     ncols=len(self.label_to_bool_matrix))
        for label, matrix in self.label_to_bool_matrix.items():
            other_matrix = other.label_to_bool_matrix.get(label, empty_matrix)
            result_matrix = matrix.kron(other=other_matrix, op=binaryop.TIMES)
            label_to_kron_product[label] = result_matrix
        return GraphWrapper(label_to_kron_product)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_graph",
                        help="input file with list of edges of the graph in format 'v_from label v_to'")
    parser.add_argument("path_to_regexp",
                        help="input file with corresponding regexp (see `pyformlang.regular_expression.Regex`)")
    args = parser.parse_args()
    graph = GraphWrapper.from_file(args.path_to_graph)
    with open(args.path_to_regexp, 'r') as file:
        line = file.readline()
        regex_epsilon_nfa = Regex(regex=line).to_epsilon_nfa()
        query = GraphWrapper.from_epsilon_nfa(regex_epsilon_nfa)
    result = graph.get_intersection(query)


if __name__ == '__main__':
    main()
