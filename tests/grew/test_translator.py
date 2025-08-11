import unittest
from typing import Callable

import cqp_tree.translation as ct
from antlr4 import InputStream, CommonTokenStream

from cqp_tree.frontends.grew.antlr import GrewLexer, GrewParser
from cqp_tree.frontends.grew.translator import ParseErrorListener, QueryBuilder, new_environment


def do_parse[T](construct: Callable[[GrewParser], T], text: str) -> T:
    lexer = GrewLexer(InputStream(text))
    stream = CommonTokenStream(lexer)
    parser = GrewParser(stream)

    listener = ParseErrorListener()
    parser.removeErrorListeners()
    parser.addErrorListener(listener)

    result = construct(parser)
    if listener.errors:
        for error in listener.errors:
            print(error.message)
        raise ct.ParsingFailed(tuple(listener.errors))

    return result


class TranslationTests(unittest.TestCase):

    def test_environment_produces_names(self):
        environment = new_environment()
        known = set()

        for i in range(100):
            name = environment[str(i)]
            self.assertNotIn(name, known, 'Environment should produce a fresh name!')
            known.add(name)

    def test_environment_persists_names(self):
        environment = new_environment()

        a1 = environment['a']
        a2 = environment['a']

        self.assertEqual(a1, a2, 'Name in environment should be persisted!')

    def test_to_cqp_operator(self):
        equality = do_parse(GrewParser.compare, '=')
        inequality = do_parse(GrewParser.compare, '<>')

        builder = QueryBuilder()
        equality_operator = builder.to_cqp_operator(equality)
        inequality_operator = builder.to_cqp_operator(inequality)

        self.assertEqual(equality_operator, '=')
        self.assertEqual(inequality_operator, '!=')

    def test_to_operand_string_literal(self):
        literal = do_parse(GrewParser.literal, '"aßσþ"')
        self.assertIsInstance(literal, GrewParser.UnicodeStringContext)

        builder = QueryBuilder()
        result = builder.to_operand(new_environment(), literal)

        self.assertEqual(
            result,
            ct.Literal('"aßσþ"')
        )

    def test_to_operand_regex_literal(self):
        literal = do_parse(GrewParser.literal, 're"a.*|[abc]+"')
        self.assertIsInstance(literal, GrewParser.RegexContext)

        builder = QueryBuilder()
        result = builder.to_operand(new_environment(), literal)

        self.assertEqual(
            result,
            ct.Literal('"a.*|[abc]+"')
        )

    def test_to_operand_simple_string_literal(self):
        literal = do_parse(GrewParser.literal, 'Tense')
        self.assertIsInstance(literal, GrewParser.SimpleStringContext)

        builder = QueryBuilder()
        result = builder.to_operand(new_environment(), literal)

        self.assertEqual(
            result,
            ct.Literal('"Tense"')
        )

    def test_to_operand_pcre_literal(self):
        literal = do_parse(GrewParser.literal, '/a.*|[abc]+/i')
        self.assertIsInstance(literal, GrewParser.PCREContext)

        builder = QueryBuilder()
        self.assertRaises(ct.NotSupported, lambda: builder.to_operand(new_environment(), literal))

    def test_to_operand_attribute(self):
        value = do_parse(GrewParser.featureValue, 'a.b')
        self.assertIsInstance(value, GrewParser.AttributeContext)

        a = ct.Identifier()
        environment = new_environment()
        environment['a'] = a

        builder = QueryBuilder()
        result = builder.to_operand(environment, value)

        self.assertEqual(
            result,
            ct.Attribute(a, 'b')
        )

    def test_to_predicate_presence(self):
        parsed = do_parse(GrewParser.feature, 'Number')
        self.assertIsInstance(parsed, GrewParser.PresenceContext)

        builder = QueryBuilder()
        result = builder.to_predicate(new_environment(), parsed)

        self.assertEqual(
            result,
            ct.Exists(ct.Attribute(None, 'Number'))
        )

    def test_to_predicate_absence(self):
        parsed = do_parse(GrewParser.feature, '!Tense')
        self.assertIsInstance(parsed, GrewParser.AbsenceContext)

        builder = QueryBuilder()
        result = builder.to_predicate(new_environment(), parsed)

        self.assertEqual(
            result,
            ct.Negation(ct.Exists(ct.Attribute(None, 'Tense')))
        )

    def test_to_predicate_requires_positive(self):
        parsed = do_parse(GrewParser.feature, 'lemma = dog|cat')
        self.assertIsInstance(parsed, GrewParser.RequiresContext)

        builder = QueryBuilder()
        result = builder.to_predicate(new_environment(), parsed)

        self.assertEqual(
            result,
            ct.Disjunction(
                [
                    ct.Comparison(
                        ct.Attribute(None, 'lemma'),
                        '=',
                        ct.Literal('"dog"'),
                    ),
                    ct.Comparison(
                        ct.Attribute(None, 'lemma'),
                        '=',
                        ct.Literal('"cat"'),
                    )
                ]
            )
        )

    def test_to_predicate_requires_negative(self):
        parsed = do_parse(GrewParser.feature, 'lemma <> dog|cat')
        self.assertIsInstance(parsed, GrewParser.RequiresContext)

        builder = QueryBuilder()
        result = builder.to_predicate(new_environment(), parsed)

        self.assertEqual(
            result,
            ct.Conjunction(
                [
                    ct.Comparison(
                        ct.Attribute(None, 'lemma'),
                        '!=',
                        ct.Literal('"dog"'),
                    ),
                    ct.Comparison(
                        ct.Attribute(None, 'lemma'),
                        '!=',
                        ct.Literal('"cat"'),
                    )
                ]
            )
        )

    def test_to_predicate_feature_structure(self):
        parsed = do_parse(GrewParser.featureStructure, '[Tense, !Number, lemma = A|B]')
        self.assertIsInstance(parsed, GrewParser.FeatureStructureContext)

        builder = QueryBuilder()
        result = builder.to_predicate(new_environment(), parsed)

        self.assertEqual(
            result,
            ct.Conjunction(
                [
                    ct.Exists(
                        ct.Attribute(None, 'Tense')
                    ),
                    ct.Negation(
                        ct.Exists(
                            ct.Attribute(None, 'Number')
                        )
                    ),
                    ct.Disjunction(
                        [
                            ct.Comparison(
                                ct.Attribute(None, 'lemma'),
                                '=',
                                ct.Literal('"A"'),
                            ),
                            ct.Comparison(
                                ct.Attribute(None, 'lemma'),
                                '=',
                                ct.Literal('"B"'),
                            )
                        ]
                    )
                ]
            )
        )
