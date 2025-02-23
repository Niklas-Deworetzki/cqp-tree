import unittest

import cqp_tree.query as query


class ValidationTests(unittest.TestCase):

    def test_referenced_identifiers(self):
        a = query.Identifier()
        b = query.Identifier()
        c = query.Identifier()

        tree = query.Conjunction(
            [
                query.Expression(query.Attribute(a, 'attr_a'), '===', query.Literal('42')),
                query.Disjunction(
                    [
                        query.Exists(
                            query.Attribute(b, 'attr_b'),
                        ),
                        query.Negation(query.Exists(query.Attribute(c, 'attr_d'))),
                    ]
                ),
            ]
        )

        self.assertSetEqual({a, b, c}, tree.referenced_identifiers())

    def test_constraint_references_unknown_identifier(self):
        with self.assertRaises(ValueError):
            a = query.Identifier()
            b = query.Identifier()
            unknown = query.Identifier()

            tokens = [
                query.Token(a, None),
                query.Token(b, None),
            ]
            constraints = [query.Constraint(a, unknown)]

            query.Query(tokens, [], constraints, [])

    def test_relation_references_unknown_identifier(self):
        with self.assertRaises(ValueError):
            a = query.Identifier()
            b = query.Identifier()
            unknown = query.Identifier()

            tokens = [
                query.Token(a, None),
                query.Token(b, None),
            ]
            relations = [query.Dependency(a, unknown)]

            query.Query(tokens, relations, [], [])

    def test_local_predicate_references_unknown_identifier(self):
        with self.assertRaises(ValueError):
            a = query.Identifier()
            unknown = query.Identifier()

            tokens = [
                query.Token(a, query.Exists(query.Attribute(unknown, 'attribute'))),
            ]
            query.Query(tokens, [], [], [])

    def test_global_predicate_references_unknown_identifier(self):
        with self.assertRaises(ValueError):
            a = query.Identifier()
            unknown = query.Identifier()

            tokens = [
                query.Token(a, None),
            ]
            predicates = [
                query.Expression(query.Attribute(unknown, 'attribute'), '=', query.Literal('2'))
            ]

            query.Query(tokens, [], [], predicates)

    def test_duplicate_identifiers(self):
        with self.assertRaises(ValueError):
            duplicate = query.Identifier()

            tokens = [
                query.Token(duplicate, None),
                query.Token(duplicate, None),
            ]
            query.Query(tokens, [], [], [])
