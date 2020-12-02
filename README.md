## SPBU Formal Language Theory Course

[![Build Status](https://travis-ci.com/SmirnovOleg/formal-languages.svg?branch=master)](https://travis-ci.com/SmirnovOleg/formal-languages)

### Installation & Running tests

 - `git clone https://github.com/SmirnovOleg/formal-languages.git`
 - `cd formal_languages`
 - `docker build -t formal_languages .`
 - `docker run formal_languages /bin/python3 -m pytest`
 
### Query Language for Graph Database Grammar
*UPDATE: Grammar syntax was updated, be careful!*

<pre>
-- Representation of the main script - list of statements
<b>SCRIPT -> STMT ; SCRIPT | eps</b>

-- Connect to the particular database (folder with graphs)
<b>STMT -> connect " PATH "</b>
-- Add new production to the global grammar
<b>STMT -> production NON_TERM to PATTERN</b>
-- Calculate select query with some constraints
<b>STMT -> select OBJECTIVE from GRAPH</b>

-- Graphs can be represented as intersection of 2 other graphs
<b>GRAPH -> GRAPH intersect OTHER_GRAPH | OTHER_GRAPH</b>
-- Graphs can be retrieved from the regex (pattern) as DFA, or from the collected grammar as RSM
<b>OTHER_GRAPH -> query [ PATTERN ] | query grammar</b>
-- Graphs can be loaded from the file with "name" from the connected database
<b>OTHER_GRAPH -> ( GRAPH ) | name " STRING "</b>
-- Also, start and final vertices can be fixed in the graph
<b>OTHER_GRAPH -> set_start_and_final ( VERTICES , VERTICES , GRAPH )</b>

-- Vertices: set, range or none
<b>VERTICES -> ( VERTICES ) | { SET } | range ( INT ; INT ) | none</b>
<b>SET -> INT TAIL</b>
<b>TAIL -> , SET | eps</b>

-- Objective: what should interpreter select from the graph?
-- It can be all the edges, total amount of the edges, or subset of the edges, extracted by filtering another edges
<b>OBJECTIVE -> ( OBJECTIVE ) | EDGES | count EDGES</b>
<b>EDGES -> ( EDGES ) | edges | filter ( PREDICATE , EDGES )</b>
-- Lambda representation for filtering edges
<b>PREDICATE -> ( VERTEX_IDENT , EDGE_IDENT , VERTEX_IDENT ) -> BOOL_EXPR</b>
<b>VERTEX_IDENT STRING</b>
<b>EDGE_IDENT STRING</b>

-- Boolean expression with `or`, `and`, `not` operators
<b>BOOL_EXPR -> BOOL_EXPR OR OTHER_BOOL_EXPR | OTHER_BOOL_EXPR</b>
<b>OTHER_BOOL_EXPR -> OTHER_BOOL_EXPR AND ANOTHER_BOOL_EXPR | ANOTHER_BOOL_EXPR</b>
<b>ANOTHER_BOOL_EXPR -> NOT ANOTHER_BOOL_EXPR | ATOMIC_BOOL_EXPR | ( BOOL_EXPR )</b>
-- Possible conditions for particular edge
<b>ATOMIC_BOOL_EXPR -> EDGE_IDENT has_label " STRING " | is_start VERTEX_IDENT | is_final VERTEX_IDENT</b>
<b>OR -> ||</b>
<b>OR -> or</b>
<b>AND -> &&</b>
<b>AND -> and</b>
<b>NOT -> !</b>
<b>NOT -> not</b>

-- Patterns (regexes) support `alt` (`|`), `concat` (`.`), `*`, `+` and `?` operators
-- Endpoints can be represented as `term`, `var` or `eps` (user's Epsilon)
<b>PATTERN -> PATTERN ALT OTHER_PATTERN | OTHER_PATTERN</b>
<b>OTHER_PATTERN -> OTHER_PATTERN CONCAT ANOTHER_PATTERN | ANOTHER_PATTERN</b>
<b>ANOTHER_PATTERN -> ( ANOTHER_PATTERN ) STAR | ( ANOTHER_PATTERN ) PLUS | ( ANOTHER_PATTERN ) OPTION</b>
<b>ANOTHER_PATTERN -> ( PATTERN ) | USER_EPS | TERM | NON_TERM</b>
<b>TERM -> term ( STRING )</b>
<b>NON_TERM -> var ( STRING )</b>
<b>PLUS -> +</b>
<b>STAR -> *</b>
<b>OPTION -> ?</b>
<b>ALT -> alt</b>
<b>ALT -> |</b>
<b>CONCAT -> concat</b>
<b>CONCAT -> .</b>
<b>USER_EPS -> eps</b>

-- Possible types: path, string or int
<b>INT -> '0' | [1-9] DIGIT*</b>
<b>STRING -> ('_' | '.' | LOWERCASE | UPPERCASE) ('_' | '.' | LOWERCASE | UPPERCASE | DIGIT)*</b>
<b>PATH -> ('/' | '_' | '.' | LOWERCASE | UPPERCASE | DIGIT)+</b>

<b>LOWERCASE -> [a-z] </b>
<b>UPPERCASE -> [A-Z] </b>
<b>DIGIT -> [0-9]</b>

-- Skip: [ \t\r\n]+
</pre>

### Examples 

 - Connect to the database, located in `/home/user/prog/db`:    
   - `connect "/home/user/prog/db";`
 - Add grammar `S -> a S b S | eps`:
   - `production var(S) to (term(a) . var(S) . term(b) . var(S)) | eps;`
 - Extract edges with label "ABC" from the graph located in "path/to/db/graph":
   - `select (filter ((u, e, v) -> (e has_label "ABC"), edges)) from (name "graph.txt");`
 - Count all the edges from the intersection of accumulated grammar (as RSM) and graph "graph":
   - `select (count edges) from ((query grammar) intersect name "graph.txt");`
 - Select edges from the graph "graph" with start state in vertex {0} and final states in vertices {2, 3}:
   - `select (edges) from (set_start_and_final ({0}, {2, 3}, name "g.txt"));`
 - Complex script example:
    ```
    connect "/home/user/db";
    production var(S) to (term(a) . var(S) . term(b));
    production var(S) to eps;
    select (filter ((v1, e, v2) -> (is_start v1), edges)) from (query grammar intersect name "fullgraph");
    select (filter ((u, e, v) -> (is_start u && e has_label "a" || is_final v), edges)) from (name "g");
    select (count edges) from (query grammar intersect name "g");
    ```
 
### Benchmarks

 - *WARNING*: You may need to install `pygraphblas-v3.3.3` to avoid failing with
  `pygraphblas.base.OutOfMemory: b'GraphBLAS error: GrB_OUT_OF_MEMORY`
 - For RPQ:
   - Put the data from this 
   [link](https://drive.google.com/file/d/158g01o2rpdq5eL3Ari8e5SPbbeZTJspr/view?usp=sharing) to the 
   `./tests/big_rpq_data/`
   - Remove `@pytest.mark.skip` decorator from `test_big_rpq_data` function in `test_big_rpq_data.py`
   - Run RPQ benchmarks without caching:
`PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider -v -s tests/test_big_rpq_data.py`
   - There were no difference detected between squaring and multiplying
 by adjacency matrix when building transitive closure on the *LUBM* datasets. 
 - For CFPQ:
   - Put the data from this 
   [link](https://drive.google.com/file/d/1BkiAFd1rYzPA0uoHo7TQvITvp-j8QVFM/view?usp=sharing) to the 
   `./test/big_cfpq_data/`
   - Remove `@pytest.mark.skip` decorator from `test_big_cfpq_data` function in `test_big_cfpq_data.py`
   - Run CFPQ benchmarks:
`python -m pytest -s tests/test_bug_cfpq_data.py`
   - Matrix-based CFPQ algorithm has shown the best performance 
 
### Using CLI to solve RPQ

```
usage: python solve_rpq.py [-h] path_to_graph path_to_regex path_to_query

positional arguments:
  path_to_graph  input file with list of edges of the graph in format 'v_from label v_to'
  path_to_regex  input file with corresponding regex (see `pyformlang.regular_expression.Regex`)
  path_to_query  input file with specified set of vertices in the input graph using regex for finding reachability

optional arguments:
  -h, --help     show this help message and exit

```

 - Queries should be represented as `.json` files
 
   - To get all reachable pairs between *all vertices*, type:
    ```
    { "reachability_between_all": true }
    ```
   - To get all reachable pairs from *specified set of vertices*, type:
    ```
    { "reachability_from_set": [ 0, 1, 2, 3, 4, 5 ] }
    ```
   - To get all reachable pairs from *specified set* of vertices to *another set* of vertices, type:
    ```
    {
        "reachability_from_set": [ 0, 1 ],
        "reachability_to_set": [ 2, 3 ]
    }
    ```

### Using CLI to parse AST of Query Language and generate .dot file

```
usage: python build_ast.py [-h] [-i INPUT] [-o OUTPUT] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to query language script for parsing
  -o OUTPUT, --output OUTPUT
                        Path to output Abstract Syntax Tree (.dot graph representation)
  -v, --view            Open graph in the PDF view immediately

```
**Example of generated AST:**

<img src="https://i.ibb.co/tBcQ9WQ/image.png" alt="AST">