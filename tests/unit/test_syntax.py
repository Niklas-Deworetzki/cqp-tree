import unittest

import cqp_tree.translation.query as query


class SyntaxTests(unittest.TestCase):
    a = query.Identifier()
    b = query.Identifier()

    def test_order_constraint(self):
        constraint = query.Constraint.order(self.a, self.b)
        self.assertIsInstance(constraint, query.Constraint)

    def test_distance_constraint(self):
        constraints = [
            query.Constraint.distance(self.a, self.b) < 1,
            query.Constraint.distance(self.a, self.b) <= 1,
            query.Constraint.distance(self.a, self.b) > 1,
            query.Constraint.distance(self.a, self.b) >= 1,
            query.Constraint.distance(self.a, self.b) == 1,
            query.Constraint.distance(self.a, self.b) != 1,
        ]

        for constraint in constraints:
            self.assertIsInstance(constraint, query.Constraint)

    def test_conjunction_many(self):
        predicates = SyntaxTests.create_predicates(10)

        conjunction = query.Conjunction.of(predicates)

        self.assertIsInstance(conjunction, query.Conjunction)

    def test_conjunction_one(self):
        predicates = SyntaxTests.create_predicates(1)

        predicate = query.Conjunction.of(predicates)

        self.assertNotIsInstance(predicate, query.Conjunction)

    def test_disjunction_many(self):
        predicates = SyntaxTests.create_predicates(10)

        disjunction = query.Disjunction.of(predicates)

        self.assertIsInstance(disjunction, query.Disjunction)

    def test_disjunction_one(self):
        predicates = SyntaxTests.create_predicates(1)

        predicate = query.Disjunction.of(predicates)

        self.assertNotIsInstance(predicate, query.Disjunction)

    @staticmethod
    def create_predicates(n):
        return (query.Exists(query.Attribute(None, f'test{i}')) for i in range(n))
