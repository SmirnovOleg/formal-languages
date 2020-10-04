import pytest

from wrappers import GrammarWrapper, GraphWrapper

grammars = [
    ['S a S b S', 'S'],
    ['S a S b', 'S'],
    ['S A B', 'S A C', 'C S B', 'A a', 'B b'],
    ['S A C B', 'A a', 'C c', 'B b B', 'B']
]

graphs = [
    ['0 a 1', '1 a 2', '2 a 0', '2 b 3', '3 b 2'],
    ['1 a 2', '2 a 3', '2 b 3', '3 b 4', '4 b 5', '5 a 4'],
    ['0 a 2', '2 b 3', '3 c 0', '0 c 1']
]


@pytest.fixture(scope="function", params=[
    (grammars[0], graphs[0], [(0, 0), (1, 1), (2, 2), (3, 3), (0, 2), (1, 2), (1, 3), (2, 3), (0, 3)]),
    (grammars[0], graphs[1], [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (1, 3), (1, 5), (2, 4)]),
    (grammars[1], graphs[0], [(0, 0), (1, 1), (2, 2), (3, 3), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]),
    (grammars[2], graphs[0], [(0, 2), (0, 3), (1, 2), (1, 3), (2, 2), (2, 3)]),
    (grammars[3], graphs[2], [])
])
def suite(request):
    grammar, graph, expected = request.param
    return {
        "grammar": GrammarWrapper.from_text(grammar),
        "graph": GraphWrapper.from_text(graph),
        "expected": set(expected)
    }


def test_hellings(suite):
    grammar, graph, expected = suite['grammar'], suite['graph'], suite['expected']
    assert graph.cfpq_hellings(grammar.cfg) == expected
    assert graph.cfpq_matrices(grammar.cfg) == expected
