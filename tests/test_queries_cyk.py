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
    'alt', 'concat', 'star', 'plus', 'option', 'term', 'nonterm',
    '(', ')', ';', '"', ','
]

grammar = GrammarWrapper.from_file('../query_language_grammar.txt', use_python_regexes_if_necessary=True)


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
    '''connect "/home/oleg/db"; 
    select (filter (u , e , v satisfy (is_start u and e has_label "a")) edges) (name g);
    '''
])
def suite(request):
    return {"script": request.param}


def test_queries_cyk(suite):
    assert analyze_syntax(suite['script']) is True
