import unittest

from antlr4 import CommonTokenStream, InputStream
from antlr4.error.ErrorStrategy import BailErrorStrategy

from cqp_tree.frontends.depsearch.antlr import *


def parse(query: str) -> DepsearchParser.QueryContext:
    lexer = DepsearchLexer(InputStream(query))
    stream = CommonTokenStream(lexer)
    parser = DepsearchParser(stream)
    parser._errHandler = BailErrorStrategy()

    for antlr in [lexer, parser]:
        antlr.removeErrorListeners()

    return parser.query()


# These queries are taken from "Dep_search: Efficient Search Tool for Large Dependency Parsebanks"
EXAMPLE_QUERIES_FROM_PAPER = [
    '_',
    'L=cat',
    '(L=cat | L=dog) & !Case=Gen',
    'cat > _',
    'cat >amod _',
    'cat >amod _ >amod _',
    'cat >amod (_ >amod _)',
    '_ !>amod _',
    '_ >!amod _',
    'cat >amod !pretty',
    'cat >amod|>nmod _',
    'first . second',
    'cat <lin_2:3 NOUN',
    'cat <lin_2:3@R NOUN',
    'cat <lin_2:3@L NOUN',
    '(_ <nsubj _) -> (Person=3 <nsubj _)',
    '(dog <nsubj _) + cat',
]

EXAMPLE_QUERIES_FROM_DOCUMENTATION = [
    'walk',
    'London',
    '"Person"',
    'L=olla',
    'NOUN',
    'Par',
    'VerbForm=Inf',
    'Past',
    'PartForm',
    'walk&NOUN',
    'NOUN&Plur&Par',
    'L=tehdä&PartForm=Pres',
    'L=kävellä|L=juosta',
    'can&!AUX',
    '!Tra',
    'voi&!L=voida',
    'walk < _',
    'walk > _',
    '_ < walk',
    '_ <nsubj _',
    '_ >nsubj _',
    '_ <cop _',
    '_ >nsubj:cop _',
    '_ <nsubj|<nsubj:cop _',
    '_ >nsubj:cop _ >cop _',
    '_ <nsubj:cop _ >nmod _',
    '_ >nmod _ >nmod _',
    '_ >nmod _ >nmod _',
    '_ >nmod (_ >nmod _)',
    'NOUN >amod (_ >amod|>acl _)',
    '_ >nsubj:cop _ !>cop _',
    '_ <advcl _ !>mark _',
    '_ <nsubj _ !(>amod|>acl) _',
    '_ <nsubj _ >!amod _',
    '_ !>amod _',
    '_ >!amod _',
    'VERB >nsubj@R _',
    '_ >amod@L _ >amod@R _',
    '_ <case@R _',
    '(VERB >aux _ >aux _) + (_ >conj (_ >conj _))',
    '_ -> NOUN',
    'NOUN -> NOUN <acl:relcl _',
    '_ <nmod _ !>case _',
    '_ >nsubj:cop _ !>cop _',
    'ADJ&Tra <xcomp _',
    'VerbForm=Part <acl _ >nsubj _',
]


class ParserTests(unittest.TestCase):

    def test_parser(self):
        all_test_cases = EXAMPLE_QUERIES_FROM_PAPER + EXAMPLE_QUERIES_FROM_DOCUMENTATION
        for i, query in enumerate(all_test_cases, start=1):
            with self.subTest(msg=f'Parse example #{i}'):
                try:
                    parsed = parse(query)
                    self.assertIsInstance(parsed, DepsearchParser.QueryContext)
                except Exception:
                    raise ValueError('Cannot parse input: ' + query)
