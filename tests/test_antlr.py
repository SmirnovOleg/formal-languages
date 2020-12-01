import re
from typing import Tuple

import pytest
from antlr4 import InputStream
from graphviz import Digraph

from wrappers import ParseTreeWrapper


@pytest.fixture(scope="function", params=[
    ('connect "/home/user/db";', 8),
    ('connect "/home/user/db" ', None),
    ('production var(S) to term(a);', 17),
    ('production var(S) to (term(a) concat var(S) concat term(b) concat var(S));', 44),
    ('production var(S) to (term(a) . var(S) . term(b) . var(S)) | eps;', 48),
    ('production var(S) to ( (term(a))* . (var(S))? . (term(b))+ );', 48),
    ('production var(s) to ( term (a) ));', None),
    ('select (filter ((u, e, v) -> (is_start u), edges)) from (name "g");', 40),
    ('select (filter ((u, e, v) satisfy (is_final v), edges)) from (name "g");', 40),
    ('select (filter ((U, E, V) satisfy (not E has_label "LABEL"), edges)) from (name "g");', 45),
    ('select filter ((u, e, v) satisfy (is_start u and e has_label "a" or not is_final v), edges) from name "g";', 49),
    ('select (count edges) from (name "g");', 21),
    ('select (count (filter ((u, e, v) satisfy (is_start u), edges))) from (name "g");', 44),
    ('select (edges) from (set_start_and_final (range(0; 10), none, name "g"));', 35),
    ('select (edges) from (set_start_and_final ({0, 1, 2}, none, name "g"));', 37),
    ('select (edges) from (set_start_and_final ({0, 1, 2}, {2, 3}, name "g"));', 42),
    ('select (edges) from (set_start_and_final (none, none, query grammar));', 28),
    ('select (edges) from (set_start_and_final (none, none, query [term(a) | term(b)] ));', 43),
    ('select (edges) from (query grammar intersect name "fullgraph");', 25),
    ('''
    
    connect "/home/oleg/db";
    production var(S) to (term(a) . var(S) . term(b) . var(S));
    production var(S) to eps;
    select (filter ((v1, e, v2) -> (is_start v1), edges)) from (query grammar intersect name "fullgraph");
    
    ''', 104),
    ('''
    
connect "/home/oleg/db.name";

production var(S) to eps | (var(A) . var(S) . var(B) . var(S));
    select (filter ((v, e, u) -> (is_start v and not is_final u), edges)) from (name "full_graph");
    
production var(A) to term(a);
production var(B) to term(b);
    select edges from ((query grammar) intersect (name "full_graph"));
    
    ''', 155)
])
def suite(request):
    return {
        "script": request.param[0],
        "expected_number_of_vertices": request.param[1]
    }


def get_number_of_vertices_and_edges(graph: Digraph) -> Tuple[int, int]:
    edges = len([line for line in graph.body if re.match(r'^\t(\d)+ -> (\d)+$', line)])
    vertices = len(graph.body) - edges
    return vertices, edges


def test_antlr(suite):
    ast = ParseTreeWrapper(InputStream(suite['script']))
    expected = suite['expected_number_of_vertices']
    if expected is None:
        assert ast.graph is None
    else:
        assert get_number_of_vertices_and_edges(ast.graph) == (expected, expected - 1)
