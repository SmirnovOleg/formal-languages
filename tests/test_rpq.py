import json
import os
import random

import numpy as np
import pytest
from pyformlang.finite_automaton import FiniteAutomaton

from automata_intersection import GraphWrapper, RegexGraphWrapper, Edge
from automata_intersection.main import solve_rpq

rpq_data_path = os.path.join(os.getcwd(), 'tests/rpq_data')
rpq_test_suites = os.listdir(rpq_data_path)


@pytest.fixture(scope="function", params=rpq_test_suites)
def suite(request):
    test_path = os.path.join(rpq_data_path, request.param)

    with open(os.path.join(test_path, "query_all.json"), 'r') as file:
        query_all = json.load(file)
    with open(os.path.join(test_path, "query_from.json"), 'r') as file:
        query_from = json.load(file)
    with open(os.path.join(test_path, "query_from_to.json"), 'r') as file:
        query_from_to = json.load(file)

    with open(os.path.join(test_path, "expected_all.txt"), 'r') as file:
        expected_all = set([tuple(map(int, line.split())) for line in file.readlines()])
    with open(os.path.join(test_path, "expected_from.txt"), 'r') as file:
        expected_from = set([tuple(map(int, line.split())) for line in file.readlines()])
    with open(os.path.join(test_path, "expected_from_to.txt"), 'r') as file:
        expected_from_to = set([tuple(map(int, line.split())) for line in file.readlines()])

    with open(os.path.join(test_path, "expected_intersection_start_final_states.json"), 'r') as file:
        json_file = json.load(file)
        start_states = json_file.get("start_states", [])
        final_states = json_file.get("final_states", [])

    expected_intersection = GraphWrapper.from_file(os.path.join(test_path, "expected_intersection.txt"))
    expected_intersection.start_states = start_states
    expected_intersection.final_states = final_states

    return {
        "graph": GraphWrapper.from_file(os.path.join(test_path, "graph.txt")),
        "constraint": RegexGraphWrapper.from_regex_file(os.path.join(test_path, "regex.txt")),
        "query_all": query_all,
        "query_from": query_from,
        "query_from_to": query_from_to,
        "expected_intersection": expected_intersection,
        "expected_all": expected_all,
        "expected_from": expected_from,
        "expected_from_to": expected_from_to
    }


@pytest.fixture(scope="function", params=[
    (vertices_num, regex)
    for regex in ['a*b*', 'a(b|c)*(c|d)', 'a', '(d|b|c)aa*']
    for vertices_num in [10, 50, 100, 500]
])
def random_suite(request):
    vertices_num, regex = request.param
    edges_num = vertices_num * (vertices_num - 1) // 5
    I = [random.randint(0, vertices_num) for _ in range(edges_num)]
    J = [random.randint(0, vertices_num) for _ in range(edges_num)]
    V = [random.choice(['a', 'b', 'c', 'd']) for _ in range(edges_num)]
    edges = [Edge(node_from=i, node_to=j, label=v) for i, j, v in zip(I, J, V)]
    graph = GraphWrapper.from_list_of_edges(edges)
    return {
        "graph": graph,
        "constraint": RegexGraphWrapper.from_regex(regex)
    }


def test_prepared_rpq(suite):
    graph: GraphWrapper = suite['graph']
    constraint: RegexGraphWrapper = suite['constraint']

    actual_intersection: GraphWrapper = constraint.kronecker_product(graph)
    expected_intersection: GraphWrapper = suite['expected_intersection']
    actual_nfa = actual_intersection.to_nfa(actual_intersection.start_states, actual_intersection.final_states)
    expected_nfa = expected_intersection.to_nfa(expected_intersection.start_states, expected_intersection.final_states)
    actual_nfa: FiniteAutomaton = actual_nfa.minimize()
    expected_nfa: FiniteAutomaton = expected_nfa.minimize()

    if actual_nfa.start_states and expected_nfa.start_states:
        assert expected_nfa.is_equivalent_to(actual_nfa)
    assert suite['expected_all'] == solve_rpq(graph, constraint, suite['query_all'])
    assert suite['expected_from'] == solve_rpq(graph, constraint, suite['query_from'])
    assert suite['expected_from_to'] == solve_rpq(graph, constraint, suite['query_from_to'])


def test_random_rpq(random_suite):
    graph: GraphWrapper = random_suite['graph']
    constraint: RegexGraphWrapper = random_suite['constraint']

    actual_intersection: GraphWrapper = constraint.kronecker_product(graph)
    for label, matrix in actual_intersection.label_to_bool_matrix.items():
        for i, j, _ in zip(*matrix.to_lists()):
            graph_i, graph_j = i % graph.vertices_num, j % graph.vertices_num
            regex_i, regex_j = i // graph.vertices_num, j // graph.vertices_num
            assert graph.label_to_bool_matrix[label][graph_i, graph_j] == 1
            assert constraint.label_to_bool_matrix[label][regex_i, regex_j] == 1
