from itertools import chain

import pytest

from wrappers import GrammarWrapper

grammars = [
    ['S a S b S', 'S'],
    ['S a S b', 'S'],
    ['S a S b', 'S a b'],
    ['S A B C', 'A a A', 'A', 'B b B', 'B', 'C c C', 'C']
]


@pytest.fixture(scope="function", params=list(chain(
    [(grammars[0], word, True) for word in ['aabbab', 'ab', '', 'abab', 'abaaabbb']],
    [(grammars[0], word, False) for word in ['aab', 'a', 'b', 'ababa', 'bbaa']],
    [(grammars[1], word, True) for word in ['aabb', 'ab', '', 'aaaabbbb']],
    [(grammars[1], word, False) for word in ['aab', 'a', 'b', 'ba', 'aa']],
    [(grammars[2], word, True) for word in ['aabb', 'ab', 'aaaabbbb']],
    [(grammars[2], word, False) for word in ['aab', 'a', 'b', '', 'ba', 'aa']],
    [(grammars[3], word, True) for word in ['', 'abc', 'a', 'b', 'c', 'aab', 'bbbccccc', 'aabbbbc']],
    [(grammars[3], word, False) for word in ['bac', 'bca', 'acccb', 'dddea', 'f']],
)))
def suite(request):
    grammar, word, expected = request.param
    return {
        "grammar": GrammarWrapper.from_text(grammar),
        "word": word,
        "expected": expected
    }


def test_cyk(suite):
    cfg, word, expected = suite['grammar'], suite['word'], suite['expected']
    assert cfg.accepts(word) == expected
