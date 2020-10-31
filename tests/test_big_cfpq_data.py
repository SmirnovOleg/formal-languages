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
csv_fieldnames = ['suite', 'graph', 'grammar',
                  'cnf_load_time', 'rfa_load_time',
                  'cnf_hellings_time', 'cnf_matrices_time',
                  'cfg_tensors_time', 'cnf_tensors_time', 'rfa_tensors_time']
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


# @pytest.mark.skip(reason="there is no need to run benchmarks each time")
def test_big_cfpq_data(benchmark_suite):
    suite_name = benchmark_suite['suite']
    graphs_paths = benchmark_suite['graphs_paths']
    grammars_paths = benchmark_suite['grammars_paths']

    for graph_path, grammar_path in product(graphs_paths, grammars_paths):
        graph_name = Path(graph_path).name
        grammar_name = Path(grammar_path).name
        print(f'Start processing graph <{graph_name}>, query grammar <{grammar_name}>')
        graph = GraphWrapper.from_file(graph_path)

        cnf_load_time, grammar = timeit(GrammarWrapper.from_file)(grammar_path, contains_regexes=True)
        rfa_load_time, rfa = timeit(RFA.from_file)(grammar_path)

        cnf_hellings_time, hellings_pairs = timeit(graph.cfpq_hellings)(grammar)
        print('Hellings done')
        cnf_matrices_time, matrices_pairs = timeit(graph.cfpq_matrices)(grammar)
        print('Matrices done')
        cfg_tensors_time, cfg_tensors_pairs = timeit(graph.cfpq_tensors)(grammar, from_wcnf=False)
        print('Tensors CFG done')
        cnf_tensors_time, cnf_tensors_pairs = timeit(graph.cfpq_tensors)(grammar, from_wcnf=True)
        print('Tensors CNF done')
        rfa_tensors_time, rfa_tensors_pairs = timeit(graph._cfpq_tensors_from_rfa)(rfa)
        print('Tensors RFA done')

        assert hellings_pairs == matrices_pairs
        assert matrices_pairs == cfg_tensors_pairs
        assert cfg_tensors_pairs == cnf_tensors_pairs
        assert cnf_tensors_pairs == rfa_tensors_pairs

        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
            writer.writerow({
                'suite': suite_name,
                'graph': graph_name,
                'grammar': grammar_name,
                'cnf_load_time': cnf_load_time,
                'rfa_load_time': rfa_load_time,
                'cnf_hellings_time': cnf_hellings_time,
                'cnf_matrices_time': cnf_matrices_time,
                'cfg_tensors_time': cfg_tensors_time,
                'cnf_tensors_time': cnf_tensors_time,
                'rfa_tensors_time': rfa_tensors_time
            })
