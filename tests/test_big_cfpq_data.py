import csv
import os
import time
from functools import wraps
from itertools import product
from pathlib import Path

import pytest

from wrappers import GraphWrapper, GrammarWrapper, RFA

data_path = os.path.join(os.getcwd(), 'tests/big_cfpq_data/')
try:
    test_suites = [name for name in os.listdir(data_path) if os.path.isdir(os.path.join(data_path, name))]
except FileNotFoundError:
    test_suites = []

csv_path = os.path.join(data_path, 'benchmark.csv')
csv_fieldnames = ['suite', 'graph', 'grammar', 'algo', 'reachable_pairs',
                  'same_cg_time_ms', 'nf_cg_time_ms', 'minimized_cg_time_ms']
iterations_num = 1


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        times = []
        for i in range(iterations_num):
            start_time = time.time_ns()
            func(*args, **kwargs)
            end_time = time.time_ns()
            delta_time = (end_time - start_time) // 1000000
            times.append(delta_time)
        return sum(times) // iterations_num, func(*args, **kwargs)

    return wrapper


@pytest.fixture(scope='session', autouse=True)
def before_session_starts():
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
        writer.writeheader()


@pytest.fixture(scope='function', params=test_suites)
def benchmark_suite(request):
    suite_name = request.param
    suite_path = os.path.join(data_path, suite_name)
    graphs_path = os.path.join(suite_path, 'graphs')
    grammars_path = os.path.join(suite_path, 'grammars')
    return {
        'suite': suite_name,
        'graphs_paths': [os.path.join(graphs_path, graph_name) for graph_name in os.listdir(graphs_path)],
        'grammars_paths': [os.path.join(grammars_path, grammar_name) for grammar_name in os.listdir(grammars_path)]
    }


def test_cfpq_big_data(benchmark_suite):
    suite_name = benchmark_suite['suite']
    graphs_paths = benchmark_suite['graphs_paths']
    grammars_paths = benchmark_suite['grammars_paths']

    for graph_path, grammar_path in product(graphs_paths, grammars_paths):
        print(f'Start processing graph <{Path(graph_path).name}>, query grammar <{Path(grammar_path).name}>')
        graph = GraphWrapper.from_file(graph_path)

        cnf_load_time, grammar = timeit(GrammarWrapper.from_file)(grammar_path, contains_regexes=True)
        rfa_load_time, rfa = timeit(RFA.from_file)(grammar_path)

        cnf_hellings_time, hellings_pairs = timeit(graph.cfpq_hellings)(grammar)
        cnf_matrices_time, matrices_pairs = timeit(graph.cfpq_matrices)(grammar)
        cfg_tensors_time, cfg_tensors_pairs = timeit(graph.cfpq_tensors)(grammar, from_wcnf=False)
        cnf_tensors_time, cnf_tensors_pairs = timeit(graph.cfpq_tensors)(grammar, from_wcnf=True)
        rfa_tensors_time, rfa_tensors_pairs = timeit(graph._cfpq_tensors_from_rfa)(rfa)

        assert hellings_pairs == matrices_pairs == cfg_tensors_pairs == cnf_tensors_pairs == rfa_tensors_pairs
