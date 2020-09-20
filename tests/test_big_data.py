import csv
import os
import time
from functools import wraps
from typing import List

import pytest

from automata_intersection import GraphWrapper, RegexGraphWrapper

data_path = os.path.join(os.getcwd(), 'tests/.big_data/')
graphs_test_suites = os.listdir(data_path)[0]
csv_path = os.path.join(data_path, 'benchmark.csv')
csv_fieldnames = ['algo', 'graph', 'regex', 'nvals', 'building_time', 'inference_time']
iterations_num = 1


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        times = []
        for i in range(iterations_num):
            start_time = time.time_ns()
            func(*args, **kwargs)
            end_time = time.time_ns()
            delta_time = (end_time - start_time) // 1e3
            times.append(delta_time)
        return sum(times) / iterations_num, func(*args, **kwargs)

    return wrapper


@pytest.fixture(scope='session', autouse=True)
def before_session_starts():
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
        writer.writeheader()


@pytest.fixture(scope='function', params=[graphs_test_suites])
def benchmark_suite(request):
    graph_name = request.param
    graph_path = os.path.join(data_path, graph_name)
    regexes_path = os.path.join(graph_path, 'regexes')
    regexes_names = os.listdir(regexes_path)

    return {
        'graph': GraphWrapper.from_file(os.path.join(graph_path, f'{graph_name}.txt')),
        'graph_name': graph_name,
        'regexes': [
            RegexGraphWrapper.from_regex_file(os.path.join(regexes_path, regex_name))
            for regex_name in regexes_names
        ],
        'regexes_names': regexes_names
    }


def test_big_data(benchmark_suite):
    graph: GraphWrapper = benchmark_suite['graph']
    regexes: List[RegexGraphWrapper] = benchmark_suite['regexes']
    graph_name, regexes_names = benchmark_suite['graph_name'], benchmark_suite['regexes_names']

    with open(csv_path, 'w+', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)

        for regex_num, regex in enumerate(regexes):
            print(f'Start regex: {regexes_names[regex_num]}')
            intersection = regex.kronecker_product(graph)

            sq_building_time, sq_closure = timeit(intersection.build_closure_by_squaring)()
            sq_inference_time, sq_nvals = timeit(lambda: sq_closure.nvals)()
            writer.writerow({
                'algo': 'squaring',
                'graph': graph_name,
                'regex': regexes_names[regex_num],
                'nvals': sq_nvals,
                'building_time': sq_building_time,
                'inference_time': sq_inference_time
            })

            mult_building_time, mult_closure = timeit(
                intersection.build_closure_by_adj_matrix_multiplication)()
            mult_inference_time, mult_nvals = timeit(lambda: mult_closure.nvals)()
            writer.writerow({
                'algo': 'multiplying',
                'graph': graph_name,
                'regex': regexes_names[regex_num],
                'nvals': mult_nvals,
                'building_time': mult_building_time,
                'inference_time': mult_inference_time
            })
            assert sq_nvals == mult_nvals
