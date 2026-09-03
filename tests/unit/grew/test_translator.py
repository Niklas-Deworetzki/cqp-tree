import unittest
from typing import Callable

import cqp_tree
import cqp_tree.translation as ct
from cqp_tree.frontends.antlr_utils import make_parse
from cqp_tree.frontends.grew.antlr import GrewLexer, GrewParser
from cqp_tree.frontends.grew.translator import QueryBuilder, new_environment


def do_parse[T](construct: Callable, text: str) -> T:
    return make_parse(GrewLexer, GrewParser, construct)(text)


CONFIG = cqp_tree.default_configuration()


def get_builder() -> QueryBuilder:
    return QueryBuilder(CONFIG)


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

        builder = get_builder()
        equality_operator = builder.to_cqp_operator(equality)
        inequality_operator = builder.to_cqp_operator(inequality)

        self.assertEqual(equality_operator, '=')
        self.assertEqual(inequality_operator, '!=')

    def test_to_operand_string_literal(self):
        literal = do_parse(GrewParser.literal, '"aßσþ"')
        self.assertIsInstance(literal, GrewParser.UnicodeStringContext)

        builder = get_builder()
        result = builder.to_operand(literal)

        self.assertEqual(
            result,
            ct.Literal('"aßσþ"'),
        )

    def test_to_operand_regex_literal(self):
        literal = do_parse(GrewParser.literal, 're"a.*|[abc]+"')
        self.assertIsInstance(literal, GrewParser.RegexContext)

        builder = get_builder()
        result = builder.to_operand(literal)

        self.assertEqual(
            result,
            ct.Literal('"a.*|[abc]+"', represents_regex=True),
        )

    def test_to_operand_simple_string_literal(self):
        literal = do_parse(GrewParser.literal, 'Tense')
        self.assertIsInstance(literal, GrewParser.SimpleStringContext)

        builder = get_builder()
        result = builder.to_operand(literal)

        self.assertEqual(
            result,
            ct.Literal('"Tense"'),
        )

    def test_to_operand_pcre_literal(self):
        literal = do_parse(GrewParser.literal, '/a.*|[abc]+/i')
        self.assertIsInstance(literal, GrewParser.PCREContext)

        builder = get_builder()
        with self.assertRaises(ct.NotSupported):
            builder.to_operand(literal)

    def test_to_operand_subtype_relation(self):
        literal = do_parse(GrewParser.literal, 'super:subtype')

        builder = get_builder()
        result = builder.to_operand(literal)

        self.assertEqual(result, ct.Literal('"super:subtype"'))

    def test_to_operand_attribute(self):
        value = do_parse(GrewParser.featureValue, 'a.b')
        self.assertIsInstance(value, GrewParser.AttributeContext)

        a = ct.Identifier()
        builder = get_builder()
        builder.environment['a'] = ct.Token(a)
        result = builder.to_operand(value)

        self.assertEqual(
            result,
            ct.Attribute(a, 'b'),
        )

    def test_to_predicate_presence(self):
        parsed = do_parse(GrewParser.feature, 'Number')
        self.assertIsInstance(parsed, GrewParser.PresenceContext)

        builder = get_builder()
        result = builder.to_predicate(parsed)

        self.assertEqual(
            result,
            ct.Exists(ct.Attribute(None, 'Number')),
        )

    def test_to_predicate_absence(self):
        parsed = do_parse(GrewParser.feature, '!Tense')
        self.assertIsInstance(parsed, GrewParser.AbsenceContext)

        builder = get_builder()
        result = builder.to_predicate(parsed)

        self.assertEqual(
            result,
            ct.Negation(ct.Exists(ct.Attribute(None, 'Tense'))),
        )

    def test_to_predicate_requires_positive(self):
        parsed = do_parse(GrewParser.feature, 'lemma = dog|cat')
        self.assertIsInstance(parsed, GrewParser.RequiresContext)

        builder = get_builder()
        result = builder.to_predicate(parsed)

        self.assertEqual(
            result,
            ct.Disjunction(
                (
                    ct.Comparison(
                        ct.Attribute(None, 'lemma'),
                        '=',
                        ct.Literal('"dog"'),
                    ),
                    ct.Comparison(
                        ct.Attribute(None, 'lemma'),
                        '=',
                        ct.Literal('"cat"'),
                    ),
                )
            ),
        )

    def test_to_predicate_requires_negative(self):
        parsed = do_parse(GrewParser.feature, 'lemma <> dog|cat')
        self.assertIsInstance(parsed, GrewParser.RequiresContext)

        builder = get_builder()
        result = builder.to_predicate(parsed)

        self.assertEqual(
            result,
            ct.Conjunction(
                (
                    ct.Comparison(
                        ct.Attribute(None, 'lemma'),
                        '!=',
                        ct.Literal('"dog"'),
                    ),
                    ct.Comparison(
                        ct.Attribute(None, 'lemma'),
                        '!=',
                        ct.Literal('"cat"'),
                    ),
                )
            ),
        )

    def test_to_predicate_feature_structure(self):
        parsed = do_parse(GrewParser.featureStructure, '[Tense, !Number, lemma = A|B]')
        self.assertIsInstance(parsed, GrewParser.FeatureStructureContext)

        builder = get_builder()
        result = builder.to_predicate(parsed)

        self.assertEqual(
            result,
            ct.Conjunction(
                (
                    ct.Exists(ct.Attribute(None, 'Tense')),
                    ct.Negation(ct.Exists(ct.Attribute(None, 'Number'))),
                    ct.Disjunction(
                        (
                            ct.Comparison(
                                ct.Attribute(None, 'lemma'),
                                '=',
                                ct.Literal('"A"'),
                            ),
                            ct.Comparison(
                                ct.Attribute(None, 'lemma'),
                                '=',
                                ct.Literal('"B"'),
                            ),
                        )
                    ),
                )
            ),
        )

    def test_translate_empty_request(self):
        parsed = do_parse(GrewParser.request, 'pattern {}')
        query, *others = QueryBuilder.build(parsed, CONFIG).queries

        self.assertFalse(others, 'Empty query should not produce multiple queries.')
        self.assertTrue(query.tokens, 'Empty query should match token.')

    def test_translate_multiple_items(self):
        parsed = do_parse(
            GrewParser.request,
            """
        pattern {
            X [];
        }
        with {
            Y [upos=PUNCT];
        }
        without {
            A -> X;
        }
        """,
        )

        result = QueryBuilder.build(parsed, CONFIG)
        self.assertEqual(len(result.queries), 3, 'Query should have 3 query parts.')

    def test_translate_combined_token(self):
        parsed = do_parse(
            GrewParser.request,
            """
        pattern {
            X[lemma=dog];
        }
        with {
            X[upos=NOUN];
        }
        """,
        )

        query1, query2 = QueryBuilder.build(parsed, CONFIG).queries
        self.assertEqual(
            len(query1.tokens),
            1,
            'Main query should search for 1 token.',
        )
        self.assertEqual(
            len(query2.tokens),
            1,
            'Additional query should have 1 token.',
        )
