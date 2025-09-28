from dataclasses import dataclass, field
from typing import List, override

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorListener import ErrorListener

import cqp_tree.translation as ct
from cqp_tree.frontends.grew.antlr import GrewLexer, GrewParser


@dataclass
class ParseErrorListener(ErrorListener):
    errors: List[ct.InputError] = field(default_factory=list)

    @override
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(ct.InputError(f'{line}, {column}', msg))


def parse(query: str) -> GrewParser.RequestContext:
    listener = ParseErrorListener()

    lexer = GrewLexer(InputStream(query))
    stream = CommonTokenStream(lexer)
    parser = GrewParser(stream)

    for antlr in [lexer, parser]:
        antlr.removeErrorListeners()
        antlr.addErrorListener(listener)

    result = parser.request()
    if listener.errors:
        raise ct.ParsingFailed(*listener.errors)

    return result


@ct.translator('depsearch')
def translate_depsearch(depsearch: str) -> ct.QueryPlan:
    ...


