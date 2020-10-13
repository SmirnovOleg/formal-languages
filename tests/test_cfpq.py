from itertools import chain

import pytest

from wrappers import GrammarWrapper, GraphWrapper

grammars = {
    0: ['S a S b S', 'S'],
    1: ['S a S b', 'S'],
    2: ['S A B', 'S A C', 'C S B', 'A a', 'B b'],
    3: ['S A C B', 'A a', 'C c', 'B b B', 'B'],
    4: ['S a S b', 'S a b'],
    5: ['E E plus E', 'E E minus E', 'E l E r', 'E N', 'N zero', 'N one']
}

graphs = {
    0: ['0 a 1', '1 a 2', '2 a 0', '2 b 3', '3 b 2'],
    1: ['1 a 2', '2 a 3', '2 b 3', '3 b 4', '4 b 5', '5 a 4'],
    2: ['0 a 2', '2 b 3', '3 c 0', '0 c 1'],
    3: ['0 a 1', '1 b 2', '2 a 3', '3 b 4'],
    4: ['0 l 0', '0 zero 1', '1 plus 2', '2 one 3', '3 r 3', '3 minus 4', '4 zero 5'],
    5: ['0 one 1', '1 plus 2', '2 one 3', '3 plus 0']
}


@pytest.fixture(scope="function", params=list(chain(*[
    [
        (grammars[0], graphs[0], algo, [(0, 0), (1, 1), (2, 2), (3, 3), (0, 2), (1, 2), (1, 3), (2, 3), (0, 3)]),
        (grammars[0], graphs[1], algo, [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (1, 3), (1, 5), (2, 4)]),
        (grammars[1], graphs[0], algo, [(0, 0), (1, 1), (2, 2), (3, 3), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]),
        (grammars[2], graphs[0], algo, [(0, 2), (0, 3), (1, 2), (1, 3), (2, 2), (2, 3)]),
        (grammars[3], graphs[2], algo, []),
        (grammars[4], graphs[0], algo, [(2, 2), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]),
        (grammars[0], graphs[3], algo, [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (0, 4), (0, 2), (2, 4)]),
        (grammars[5], graphs[4], algo, [(0, 5), (0, 1), (0, 3), (2, 5), (2, 3), (4, 5)]),
        (grammars[5], graphs[5], algo, [(0, 1), (2, 3), (0, 3), (2, 1)])
    ]
    for algo in ['hellings', 'matrices', 'tensors']
])))
def suite(request):
    grammar, graph, algo, expected = request.param
    return {
        "grammar": GrammarWrapper.from_text(grammar),
        "graph": GraphWrapper.from_text(graph),
        "expected": set(expected),
        "algo": algo
    }


def test_cfpq(suite):
    grammar, graph, algo, expected = suite['grammar'], suite['graph'], suite['algo'], suite['expected']
    solver = graph.__getattribute__(f'cfpq_{algo}')
    assert solver(grammar.cfg) == expected
