import unittest

from cqp_tree import Attribute, Disjunction, Literal, NotSupported, Comparison
from cqp_tree.frontends.deptreepy import translate_deptreepy


class TranslationTests(unittest.TestCase):

    def test_tree_(self):
        with self.assertRaises(NotSupported):
            translate_deptreepy('TREE a b c')

    def test_tree(self):
        translate_deptreepy('TREE_ ((AND (POS NOUN) (DEPREL det))) (OR (LEMMA IN a b c)))')

    def test_field_comparison(self):
        (q,) = translate_deptreepy('field a').queries
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
        (q,) = translate_deptreepy('field IN a b').queries
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
        (q,) = translate_deptreepy('field_ a').queries
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
        (q,) = translate_deptreepy('field_ IN a b').queries
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
