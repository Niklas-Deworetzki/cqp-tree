import math
import unittest

import cqp_tree.translation.cqp as cqp
import cqp_tree.translation.query as query


class TranslatorTests(unittest.TestCase):

    def test_arrangements_without_constraints(self):
        identifiers = {query.Identifier() for _ in range(7)}

        arrangements = cqp.arrangements(identifiers, [])

        self.assertEqual(
            len(list(arrangements)),
            math.factorial(7),
            '7 independent tokens should be arrangeable in 7! different ways.',
        )

    def test_arrangements(self):
        a = query.Identifier()
        b = query.Identifier()
        c = query.Identifier()
        d = query.Identifier()

        possible_arrangements = [[a, b, c, d], [a, b, d, c], [a, d, b, c]]
        constraints = {
            query.Constraint.order(a, b),
            query.Constraint.order(b, c),
            query.Constraint.order(a, d),
        }

        arrangements = list(cqp.arrangements({a, b, c, d}, constraints))
        self.assertEqual(
            len(arrangements),
            len(possible_arrangements),
            f'There are {len(possible_arrangements)} possible arrangements.',
        )
        for arrangement in arrangements:
            self.assertIn(arrangement, possible_arrangements)
