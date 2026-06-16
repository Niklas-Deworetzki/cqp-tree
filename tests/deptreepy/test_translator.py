import unittest

import cqp_tree
from cqp_tree import *
from cqp_tree.frontends.deptreepy import translate_deptreepy

CONFIG = cqp_tree.default_configuration().project(
    cqp_tree.GENERAL_CONFIG_SECTION,
    cqp_tree.ANNOTATIONS_CONFIG_SECTION,
    'deptreepy',
)


class TranslationTests(unittest.TestCase):

    def test_tree(self):
        with self.assertRaises(NotSupported):
            translate_deptreepy('TREE a b c', CONFIG)

    def test_tree_(self):
        translate_deptreepy('TREE_ ((AND (POS NOUN) (DEPREL det))) (OR (LEMMA IN a b c)))', CONFIG)

    def test_empty_string(self):
        with self.assertRaises(ParsingFailed):
            translate_deptreepy('', CONFIG)

    def test_field_comparison(self):
        (q,) = translate_deptreepy('field a', CONFIG).queries
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Comparison(
                Attribute(None, 'field'),
                '=',
                Literal('"a"'),
            ),
        )

    def test_field_in_comparison(self):
        (q,) = translate_deptreepy('field IN a b', CONFIG).queries
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Disjunction(
                [
                    Comparison(
                        Attribute(None, 'field'),
                        '=',
                        Literal('"a"'),
                    ),
                    Comparison(
                        Attribute(None, 'field'),
                        '=',
                        Literal('"b"'),
                    ),
                ]
            ),
        )

    def test_field_contains_comparison(self):
        (q,) = translate_deptreepy('field_ a', CONFIG).queries
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Comparison(
                Attribute(None, 'field'),
                'contains',
                Literal('"a"'),
            ),
        )

    def test_field_in_contains_comparison(self):
        (q,) = translate_deptreepy('field_ IN a b', CONFIG).queries
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Disjunction(
                [
                    Comparison(
                        Attribute(None, 'field'),
                        'contains',
                        Literal('"a"'),
                    ),
                    Comparison(
                        Attribute(None, 'field'),
                        'contains',
                        Literal('"b"'),
                    ),
                ]
            ),
        )

    def test_true(self):
        (q,) = translate_deptreepy('TRUE', CONFIG).queries
        self.assertEqual(1, len(q.tokens), 'Query should have one token.')
        self.assertEqual(0, len(q.predicates), 'Query should not have any predicates.')
        (token, ) = q.tokens
        self.assertIsNone(token.attributes)


    def test_and_predicate(self):
        (q,) = translate_deptreepy('(AND (a 1) (b 2))', CONFIG).queries
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Conjunction(
                [
                    Comparison(
                        Attribute(None, 'a'),
                        '=',
                        Literal('"1"'),
                    ),
                    Comparison(
                        Attribute(None, 'b'),
                        '=',
                        Literal('"2"'),
                    ),
                ]
            ),
        )

    def test_or_predicate(self):
        (q,) = translate_deptreepy('(OR (a 1) (b 2))', CONFIG).queries
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Disjunction(
                [
                    Comparison(
                        Attribute(None, 'a'),
                        '=',
                        Literal('"1"'),
                    ),
                    Comparison(
                        Attribute(None, 'b'),
                        '=',
                        Literal('"2"'),
                    ),
                ]
            ),
        )

    def test_not_predicate(self):
        (q,) = translate_deptreepy('(NOT (a 1))', CONFIG).queries
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Negation(
                Comparison(
                    Attribute(None, 'a'),
                    '=',
                    Literal('"1"'),
                )
            ),
        )

    def test_and_dependency(self):
        plan = translate_deptreepy('(AND (TREE_ (r 1) (d 1)) (TREE_ (r 2) (d 2)))', CONFIG)

        self.assertEqual(len(plan.queries), 2)
        self.assertEqual(len(plan.operations), 1)
        (operation,) = plan.operations
        self.assertEqual(operation.identifier, plan.goal)
        self.assertEqual(operation.operator, SetOperator.CONJUNCTION)

    def test_or_dependency(self):
        plan = translate_deptreepy('(OR (TREE_ (r 1) (d 1)) (TREE_ (r 2) (d 2)))', CONFIG)

        self.assertEqual(len(plan.queries), 2)
        self.assertEqual(len(plan.operations), 1)
        (operation,) = plan.operations
        self.assertEqual(operation.identifier, plan.goal)
        self.assertEqual(operation.operator, SetOperator.DISJUNCTION)

    def test_not_dependency(self):
        with self.assertRaises(NotSupported):
            translate_deptreepy('(NOT (TREE_ (r 1) (d 1)))', CONFIG)
