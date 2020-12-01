grammar QueryLanguageGrammar;

script: (stmt ';')* EOF ;

stmt
    : CONNECT '"' PATH '"'
    | PRODUCTION variable TO pattern
    | SELECT objective FROM graph
    ;

graph
    : '(' graph ')'
    | NAME '"' STRING '"'
    | QUERY GRAMMAR
    | QUERY '[' pattern ']'
    | SET_START_AND_FINAL '(' vertices ',' vertices ',' graph ')'
    | graph INTERSECT graph
    ;

vertices
    : '(' vertices ')'
    | '{' seq '}'
    | RANGE '(' INT ';' INT ')'
    | NONE
    ;

seq: (INT ',')* INT ;

objective
    : '(' objective ')'
    | edges
    | COUNT edges
    ;

edges
    : '(' edges ')'
    | EDGES
    | FILTER '(' predicate ',' edges ')'
    ;

predicate: '(' STRING ',' STRING ',' STRING ')' SATISFY bool_expr ;

bool_expr
    : '(' bool_expr ')'
    | STRING HAS_LABEL '"' STRING '"'
    | IS_START STRING
    | IS_FINAL STRING
    | NOT bool_expr
    | bool_expr AND bool_expr
    | bool_expr OR bool_expr
    ;

pattern
    : EPS
    | terminal
    | variable
    | '(' pattern ')'
    | '(' pattern ')' STAR
    | '(' pattern ')' PLUS
    | '(' pattern ')' OPTION
    | pattern CONCAT pattern
    | pattern ALT pattern
    ;

terminal: TERM '(' STRING ')' ;
variable: VAR '(' STRING ')' ;

CONNECT: 'connect' ;
PRODUCTION: 'production' ;
SELECT: 'select' ;
FROM: 'from';
SET_START_AND_FINAL: 'set_start_and_final' ;
NAME: 'name' ;
QUERY: 'query' ;
GRAMMAR: 'grammar' ;
INTERSECT: 'intersect' ;
TO: 'to' ;
RANGE: 'range' ;
NONE: 'none' ;
COUNT: 'count' ;
EDGES: 'edges' ;
FILTER: 'filter' ;
SATISFY: '->' | 'satisfy' ;
HAS_LABEL: 'has_label' ;
IS_START: 'is_start' ;
IS_FINAL: 'is_final' ;
VAR: 'var' ;
TERM: 'term' ;
STAR: '*' ;
PLUS: '+' ;
OPTION: '?' ;
ALT: '|' | 'alt' ;
CONCAT: '.' | 'concat' ;
NOT: 'not' | '!' ;
AND: 'and' | '&&' ;
OR: 'or' | '||' ;
EPS: 'eps' ;

fragment LOWERCASE : [a-z] ;
fragment UPPERCASE : [A-Z] ;
fragment DIGIT : [0-9] ;

STRING: ('_' | '.' | LOWERCASE | UPPERCASE) ('_' | '.' | LOWERCASE | UPPERCASE | DIGIT)* ;
PATH: ('/' | '_' | '.' | LOWERCASE | UPPERCASE | DIGIT)+ ;
INT: '0' | [1-9] DIGIT* ;
WS : [ \t\r\n]+ -> skip ;