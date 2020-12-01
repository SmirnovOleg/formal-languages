import os

import pytest

from wrappers import GrammarWrapper

keywords = [
    'connect', 'production', 'select',
    'intersect', 'query', 'grammar',
    'name', 'set_start_and_final',
    'set', 'range', 'none',
    'count', 'edges', 'filter', 'satisfy',
    'or', 'and', 'not',
    'has_label', 'is_start', 'is_final',
    'alt', 'concat', 'star', 'plus', 'option', 'term', 'var',
    '(', ')', ';', '"', ',', 'to', '{', '}'
]

variables = {
    'SCRIPT', 'STMT', 'PATH', 'STRING', 'INT',
    'PATTERN', 'OBJECTIVE', 'GRAPH', 'OTHER_GRAPH', 'ANOTHER_GRAPH',
    'VERTICES', 'SET', 'EDGES', 'PREDICATE', 'VERTEX_IDENT', 'EDGE_IDENT',
    'BOOL_EXPR', 'OTHER_BOOL_EXPR', 'ANOTHER_BOOL_EXPR', 'ATOMIC_BOOL_EXPR',
    'OTHER_PATTERN', 'ANOTHER_PATTERN', 'USER_EPS', 'NON_TERM', 'TAIL'
}

grammar = GrammarWrapper.from_file(os.path.join(os.getcwd(), 'old_grammar_draft.txt'),
                                   use_python_regexes_if_necessary=True,
                                   variables=variables)


def analyze_syntax(script: str):
    for spec in ['\n', ',', '"', '(', ')', ';', '{', '}']:
        script = script.replace(spec, f' {spec} ')
    result = []
    for word in script.split():
        if word in keywords:
            result.append(word)
        else:
            result.extend(word)
    return grammar.accepts(result)


@pytest.fixture(scope="function", params=[
    ('connect "/home/user/db";', True),
    ('connect "/home/user/db" ', False),
    ('production var(S) to term(a);', True),
    ('production var(S) to (term(a) concat var(S) concat term(b) concat var(S));', True),
    ('production var(S) to (term(a) concat var(S) concat term(b) concat var(S)) alt e;', True),
    ('production var(S) to (star(term(a)) concat option(var(S)) concat plus(term(b)));', True),
    ('production var(s) to ( term (a) ));', False),
    ('select (filter ((u, e, v) satisfy (is_start u), edges)) (name "g");', True),
    ('select (filter ((u, e, v) satisfy (is_final v), edges)) (name "g");', True),
    ('select (filter ((U, E, V) satisfy (not E has_label "LABEL"), edges)) (name "g");', True),
    ('select (filter ((u, e, v) satisfy (is_start u and e has_label "a" or is_final v), edges)) (name "g");', True),
    ('select (count edges) (name "g");', True),
    ('select (count (filter ((u, e, v) satisfy (is_start u), edges))) (name "g");', True),
    ('select (edges) (set_start_and_final (range(0; 10), none, name "g"));', True),
    ('select (edges) (set_start_and_final (set {0, 1, 2}, none, name "g"));', True),
    ('select (edges) (set_start_and_final (set {0, 1, 2}, set {2, 3}, name "g"));', True),
    ('select (edges) (set_start_and_final (none, none, query grammar));', True),
    ('select (edges) (set_start_and_final (none, none, query term(a) alt term(b)));', True),
    ('select (edges) (query grammar intersect name "fullgraph");', True),
    ('''
        connect "/home/oleg/db";
        production var(S) to (term(a) concat var(S) concat term(b) concat var(S));
        production var(S) to e;
        select (filter ((v1, e, v2) satisfy (is_start v1), edges)) (query grammar intersect name "fullgraph");
    ''', True),
])
def suite(request):
    return {
        "script": request.param[0],
        "expected": request.param[1]
    }


def test_queries_cyk(suite):
    assert analyze_syntax(suite['script']) is suite['expected']
