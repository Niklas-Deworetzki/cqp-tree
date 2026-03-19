from dataclasses import dataclass, field
from typing import Callable, List, override

from antlr4 import CommonTokenStream, InputStream, Parser, TerminalNode
from antlr4.Lexer import Lexer
from antlr4.Token import Token
from antlr4.error.ErrorListener import ErrorListener

import cqp_tree.translation as ct


@dataclass
class ParseErrorListener(ErrorListener):
    errors: List[ct.InputError] = field(default_factory=list)

    @override
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(ct.InputError(f'{line}, {column}', msg))


def make_parse[L: Lexer, P: Parser, R](
    lexer: type[L], parser: type[P], func: Callable[[P], R]
) -> Callable[[str], R]:
    """
    Creates a function of type (str) -> R, that can be used to parse an
    input string using a generated ANTLR parser.

    Callers are required to provide the generated Lexer type, the
    generated Parser type and a reference to the parse that should
    be performed.

    If the returned function cannot parse an input string, it raises
    an ParsingFailed exception with collected error and position
    information from all ANTLR reported errors.
    """

    def parse(inp: str) -> R:
        listener = ParseErrorListener()

        antlr_lexer = lexer(InputStream(inp))
        antlr_parser = parser(CommonTokenStream(antlr_lexer))
        for antlr in [antlr_lexer, antlr_parser]:
            antlr.removeErrorListeners()
            antlr.addErrorListener(listener)

        result = func(antlr_parser)
        if listener.errors:
            raise ct.ParsingFailed(*listener.errors)

        return result

    return parse


def string_of_token(token: TerminalNode | Token) -> str:
    if isinstance(token, Token):
        return token.text
    return token.symbol.text
