import argparse
import json
from itertools import chain
from typing import Set, Tuple, Dict, Union, List

from automata_intersection import GraphWrapper, RegexGraphWrapper


def solve_rpq(graph: GraphWrapper, constraint: RegexGraphWrapper,
              query: Dict[str, Union[bool, List[int]]]) -> Set[Tuple[int, int]]:
    # Calculate kronecker (tensor) product, prepare indices
    intersection = constraint.kronecker_product(graph)
    step = graph.vertices_num

    # Parse query from JSON
    if query.get('reachability_between_all'):
        start_idxs, end_idxs = intersection.start_states, intersection.final_states
    elif "reachability_from_set" in query and "reachability_to_set" not in query:
        graph_start_idxs = set(query.get("reachability_from_set"))
        start_idxs = set([idx for idx in intersection.start_states if (idx % step) in graph_start_idxs])
        end_idxs = intersection.final_states
    elif "reachability_from_set" in query and "reachability_to_set" in query:
        graph_start_idxs = set(query.get("reachability_from_set"))
        graph_end_idxs = set(query.get("reachability_to_set"))
        start_idxs = set([idx for idx in intersection.start_states if (idx % step) in graph_start_idxs])
        end_idxs = set([idx for idx in intersection.final_states if (idx % step) in graph_end_idxs])
    else:
        raise KeyError("Incorrect format of the input query")

    # Collect reachable pairs from resulting automaton using transitive closure
    reachable_pairs = intersection.get_reachable_pairs(start_idxs, end_idxs)
    initial_reachable_pairs = set([(pair[0] % step, pair[1] % step) for pair in reachable_pairs])

    return initial_reachable_pairs


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_graph",
                        help="input file with list of edges of the graph in format 'v_from label v_to'")
    parser.add_argument("path_to_regex",
                        help="input file with corresponding regex (see `pyformlang.regular_expression.Regex`)")
    parser.add_argument("path_to_query",
                        help="input file with specified set of vertices in the input graph "
                             "using regex for finding reachability")
    args = parser.parse_args()

    # Load initial data: graph, regexp, query
    graph = GraphWrapper.from_file(args.path_to_graph)
    constraint = RegexGraphWrapper.from_regex_file(args.path_to_regex)
    with open(args.path_to_query, 'r') as file:
        query = json.load(file)

    initial_reachable_pairs = solve_rpq(graph, constraint, query)
    print("Reachable pairs of indices:")
    for start_idx, end_idx in initial_reachable_pairs:
        print(f'{start_idx} ~~> {end_idx}')

    intersection = constraint.kronecker_product(graph)
    print("Counter of edge types in resulting automaton:")
    print(intersection.edges_counter)


if __name__ == '__main__':
    main()
