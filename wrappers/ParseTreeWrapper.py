import logging
from typing import Optional

from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener
from antlr4.error.Errors import ParseCancellationException
from antlr4.tree.Tree import TerminalNodeImpl
from graphviz import Digraph

from antlr.QueryLanguageGrammarLexer import QueryLanguageGrammarLexer
from antlr.QueryLanguageGrammarListener import QueryLanguageGrammarListener
from antlr.QueryLanguageGrammarParser import QueryLanguageGrammarParser


class ParseTreeWrapper:
    def __init__(self, input_stream: InputStream):
        lexer = QueryLanguageGrammarLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = QueryLanguageGrammarParser(stream)
        parser.removeErrorListeners()
        parser.addErrorListener(self._LoggerErrorListener())
        try:
            self.ast = parser.script()
        except ParseCancellationException:
            self.ast = None

    @property
    def graph(self) -> Optional[Digraph]:
        graph = Digraph(comment="AST")
        if self.ast is not None:
            ParseTreeWalker().walk(self._GraphBuilder(graph), self.ast)
            return graph
        return None

    class _GraphBuilder(QueryLanguageGrammarListener):
        def __init__(self, graph: Digraph):
            self.graph = graph
            self.node_counter = 0
            self.node_to_id = {}
            super(ParseTreeWrapper._GraphBuilder, self).__init__()

        def enterEveryRule(self, ctx: ParserRuleContext):
            if ctx not in self.node_to_id:
                self.graph.node(self._get_node_id(ctx), label=self._get_label(ctx))
            for child in ctx.children:
                self.graph.node(self._get_node_id(child), label=self._get_label(child))
                self.graph.edge(self._get_node_id(ctx), self._get_node_id(child))

        def _get_node_id(self, node: ParserRuleContext) -> str:
            if node not in self.node_to_id:
                self.node_to_id[node] = self.node_counter
                self.node_counter += 1
            return str(self.node_to_id[node])

        @staticmethod
        def _get_label(ctx: ParserRuleContext) -> str:
            if isinstance(ctx, TerminalNodeImpl):
                return ctx.symbol.text
            else:
                return str(type(ctx).__name__).replace('Context', '').lower()

    class _LoggerErrorListener(ErrorListener):
        def syntaxError(self, recognizer, offending_symbol, line, column, msg, e):
            logging.error(f"Error on line: {line} msg: {msg}")
            raise ParseCancellationException(f"line: {line} msg: {msg}")
