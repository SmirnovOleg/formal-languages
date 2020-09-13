import argparse
from dataclasses import dataclass
from typing import Tuple, Dict, List

from pyformlang.finite_automaton import EpsilonNFA
from pyformlang.regular_expression import Regex
from pygraphblas import Matrix

Indices = List[int]


@dataclass
class Edge:
    node_from: int
    node_to: int
    label: str


class GraphWrapper():
    _label_to_bool_matrices: Dict[str, Matrix] = {}

    def __init__(self, edges: List[Edge]):
        label_to_edges: Dict[str, Tuple[Indices, Indices]] = {}
        for edge in edges:
            I, J = label_to_edges.setdefault(edge.label, ([], []))
            I.append(edge.node_from)
            J.append(edge.node_to)
        for label, (I, J) in label_to_edges.items():
            self._label_to_bool_matrices[label] = Matrix.from_lists(I, J, [1] * len(I))

    @classmethod
    def from_epsilon_nfa(cls, epsilon_nfa: EpsilonNFA):
        edges = []
        dfa = epsilon_nfa.to_deterministic()
        states_to_idx = dict([(state, index) for index, state in enumerate(dfa.states)])
        for state_from, transitions in epsilon_nfa.to_deterministic().to_dict().items():
            for label, state_to in transitions.items():
                edges.append(Edge(node_from=states_to_idx[state_from], node_to=states_to_idx[state_to], label=label))
        return cls(edges)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_graph",
                        help="input file with list of edges of the graph in format 'v_from label v_to'")
    parser.add_argument("path_to_regexp",
                        help="input file with corresponding regexp (see `pyformlang.regular_expression.Regex`)")
    args = parser.parse_args()
    with open(args.path_to_graph, 'r') as file:
        edges = []
        for line in file.readlines():
            vertex_from, label, vertex_to = line.split(' ')
            edges.append(Edge(node_from=int(vertex_from),
                              node_to=int(vertex_to),
                              label=label))
        graph = GraphWrapper(edges)
    with open(args.path_to_regexp, 'r') as file:
        line = file.readline()
        regex_epsilon_nfa = Regex(regex=line).to_epsilon_nfa()
        query = GraphWrapper.from_epsilon_nfa(regex_epsilon_nfa)


if __name__ == '__main__':
    main()
