import argparse
from dataclasses import dataclass
from typing import Tuple, Dict, List

from pyformlang.regular_expression import Regex
from pygraphblas import Matrix

Indices = List[int]


@dataclass
class Edge:
    node_from: int
    label: str
    node_to: int


class GraphWrapper:
    _label_to_bool_matrices: Dict[str, Matrix] = {}

    def __init__(self, edges: List[Edge]):
        label_to_edges: Dict[str, Tuple[Indices, Indices]] = {}
        for edge in edges:
            I, J = label_to_edges.setdefault(edge.label, ([], []))
            I.append(edge.node_from)
            J.append(edge.node_to)
        for label, (I, J) in label_to_edges.items():
            self._label_to_bool_matrices[label] = Matrix.from_lists(I, J, [1] * len(I))


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
        regex = Regex(regex=line)
        regex_enfa = regex.to_epsilon_nfa()


if __name__ == '__main__':
    main()
