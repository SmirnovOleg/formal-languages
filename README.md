## SPBU Formal Language Theory Course

[![Build Status](https://travis-ci.com/SmirnovOleg/formal-languages.svg?branch=master)](https://travis-ci.com/SmirnovOleg/formal-languages)

#### Installation & Running tests

 - `git clone https://github.com/SmirnovOleg/formal-languages.git`
 - `cd formal_languages`
 - `docker build -t formal_languages .`
 - `docker run formal_languages /bin/python3 -m pytest`
 
#### Benchmarks

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
 
#### Using CLI interface to solve RPQ

```
usage: python -m automata_intersection.main [-h] path_to_graph path_to_regex path_to_query

positional arguments:
  path_to_graph  input file with list of edges of the graph in format 'v_from label v_to'
  path_to_regex  input file with corresponding regex (see `pyformlang.regular_expression.Regex`)
  path_to_query  input file with specified set of vertices in the input graph using regex for finding reachability
     (see tests for query examples)

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