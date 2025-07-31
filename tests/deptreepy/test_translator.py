import unittest

from cqp_tree import Attribute, Disjunction, Literal, NotSupported, Operation
from cqp_tree.frontends.deptreepy import query_from_deptreepy


class TranslationTests(unittest.TestCase):

    def test_tree_(self):
        with self.assertRaises(NotSupported):
            query_from_deptreepy('TREE a b c')

    def test_tree(self):
        q = query_from_deptreepy('TREE_ ((AND (POS NOUN) (DEPREL det))) (OR (LEMMA IN a b c)))')
        self.assertIsNotNone(q)

    def test_field_comparison(self):
        q = query_from_deptreepy('field a')
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Operation(
                Attribute(None, 'field'),
                '=',
                Literal('"a"'),
            ),
        )

    def test_field_in_comparison(self):
        q = query_from_deptreepy('field IN a b')
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Disjunction(
                [
                    Operation(
                        Attribute(None, 'field'),
                        '=',
                        Literal('"a"'),
                    ),
                    Operation(
                        Attribute(None, 'field'),
                        '=',
                        Literal('"b"'),
                    ),
                ]
            ),
        )

    def test_field_contains_comparison(self):
        q = query_from_deptreepy('field_ a')
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Operation(
                Attribute(None, 'field'),
                'contains',
                Literal('"a"'),
            ),
        )

    def test_field_in_contains_comparison(self):
        q = query_from_deptreepy('field_ IN a b')
        (token,) = q.tokens

        self.assertEqual(
            token.attributes,
            Disjunction(
                [
                    Operation(
                        Attribute(None, 'field'),
                        'contains',
                        Literal('"a"'),
                    ),
                    Operation(
                        Attribute(None, 'field'),
                        'contains',
                        Literal('"b"'),
                    ),
                ]
            ),
        )
