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
