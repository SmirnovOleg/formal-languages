import argparse
import json
from itertools import chain

from pyformlang.regular_expression import Regex

from automata_intersection.graph_wrappers import GraphWrapper, AutomatonGraphWrapper


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
    with open(args.path_to_regex, 'r') as file:
        line = file.readline()
        regex_epsilon_nfa = Regex(regex=line).to_epsilon_nfa()
        constraint = AutomatonGraphWrapper(regex_epsilon_nfa)
    with open(args.path_to_query, 'r') as file:
        query = json.load(file)

    # Calculate kronecker (tensor) product, prepare indices
    result = constraint.kronecker_product(graph)
    constraint_start_idxs = constraint.start_states_indices
    step = graph.vertices_num
    all_start_idxs = set(chain(*map(
        lambda idx: [idx * step + i for i in range(step)],
        constraint_start_idxs
    )))
    all_end_idxs = set(range(result.vertices_num))

    # Parse query from JSON
    if query.get('reachability_between_all'):
        start_idxs, end_idxs = all_start_idxs, all_end_idxs
    elif "reachability_from_set" in query and "reachability_to_set" not in query:
        graph_start_idxs = set(query.get("reachability_from_set"))
        start_idxs = set([idx for idx in all_start_idxs if (idx % step) in graph_start_idxs])
        end_idxs = all_end_idxs
    elif "reachability_from_set" in query and "reachability_to_set" in query:
        graph_start_idxs = set(query.get("reachability_from_set"))
        graph_end_idxs = set(query.get("reachability_to_set"))
        start_idxs = set([idx for idx in all_start_idxs if (idx % step) in graph_start_idxs])
        end_idxs = set([idx for idx in all_end_idxs if (idx % step) in graph_end_idxs])
    else:
        raise KeyError("Incorrect format of the input query")

    # Output reachable pairs from resulting automaton
    reachable_pairs = result.get_reachable_pairs(start_idxs, end_idxs)
    initial_reachable_pairs = set([(pair[0] % step, pair[1] % step) for pair in reachable_pairs])
    for start_idx, end_idx in initial_reachable_pairs:
        print(f'{start_idx} {end_idx}')


if __name__ == '__main__':
    main()
