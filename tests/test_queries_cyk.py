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
    '(', ')', ';', '"', ',', 'to'
]

variables = {
    'SCRIPT', 'STMT', 'PATH', 'STRING', 'INT',
    'PATTERN', 'OBJECTIVE', 'GRAPH', 'OTHER_GRAPH', 'ANOTHER_GRAPH',
    'VERTICES', 'SET', 'EDGES', 'PREDICATE', 'VERTEX_IDENT', 'EDGE_IDENT',
    'BOOL_EXPR', 'OTHER_BOOL_EXPR', 'ANOTHER_BOOL_EXPR', 'ATOMIC_BOOL_EXPR',
    'OTHER_PATTERN', 'ANOTHER_PATTERN', 'USER_EPS', 'NON_TERM'
}

grammar = GrammarWrapper.from_file('../query_language_grammar.txt',
                                   use_python_regexes_if_necessary=True,
                                   variables=variables)


def analyze_syntax(script: str):
    for spec in ['\n', ',', '"', '(', ')', ';']:
        script = script.replace(spec, f' {spec} ')
    result = []
    for word in script.split():
        if word in keywords:
            result.append(word)
        else:
            result.extend(word)
    return grammar.accepts(result)


@pytest.fixture(scope="function", params=[
    ('''connect "/home/oleg/db"; ''', True),
    ('''connect "/home/oleg/db"  ''', False),
    ('''select (filter ((u, e, v) satisfy (is_start u)) edges) (name g); ''', True),
    ('''select (filter ((u, e, v) satisfy (is_final v)) edges) (name g); ''', True),
    ('''select (filter ((U, E, V) satisfy (E has_label "LABEL")) edges) (name g); ''', True),
    ('''select (filter ((u, e, v) satisfy (is_start u and e has_label "a" or is_final v)) edges) (name g); ''', True),
    ('''production var(S) to term(a); ''', True),
    ('''production var(S) to (term(a) concat var(S) concat term(b) concat var(S)); ''', True),
    ('''production var(S) to (term(a) concat var(S) concat term(b) concat var(S)) alt e; ''', True),
    ('''production var(S) to (star(term(a)) concat option(var(S)) concat plus(term(b))); ''', True)
])
def suite(request):
    return {
        "script": request.param[0],
        "expected": request.param[1]
    }


def test_queries_cyk(suite):
    assert analyze_syntax(suite['script']) is suite['expected']
