import math
import unittest

import cqp_tree.translation.cqp as cqp
import cqp_tree.translation.query as query


class TranslatorTests(unittest.TestCase):

    def test_names_generates_fresh_names(self):
        limit = 1000

        seen = set()
        for index, name in enumerate(cqp.names()):
            self.assertNotIn(name, seen, f'{name} should be a fresh name.')
            seen.add(name)

            if index == limit:
                break

    def test_distance_between_defaults(self):
        a = query.Identifier()
        b = query.Identifier()

        distance = cqp.distance_between([], a, b)
        self.assertEqual(
            distance,
            query.Constraint.ARBITRARY_DISTANCE,
            'Invocation should default to arbitrary distance.',
        )

    def test_distance_between_defaults_if_not_found(self):
        a = query.Identifier()
        b = query.Identifier()
        constraints = {
            query.Constraint(a, query.Identifier()),
            query.Constraint(query.Identifier(), a),
            query.Constraint(b, query.Identifier()),
            query.Constraint(query.Identifier(), b),
            query.Constraint(query.Identifier(), query.Identifier()),
        }

        distance = cqp.distance_between(constraints, a, b)
        self.assertEqual(
            distance,
            query.Constraint.ARBITRARY_DISTANCE,
            'Invocation should default to arbitrary distance.',
        )

    def test_distance_between_finds(self):
        a = query.Identifier()
        b = query.Identifier()
        constraints = {query.Constraint(a, b, distance=2)}
        inv_constraints = {query.Constraint(b, a, distance=3)}

        distance = cqp.distance_between(constraints, a, b)
        self.assertEqual(distance, 2)

        inv_distance = cqp.distance_between(inv_constraints, a, b)
        self.assertEqual(inv_distance, 3)

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
            query.Constraint(a, b, enforces_order=True),
            query.Constraint(b, c, enforces_order=True),
            query.Constraint(a, d, enforces_order=True),
        }

        arrangements = list(cqp.arrangements({a, b, c, d}, constraints))
        self.assertEqual(len(arrangements), len(possible_arrangements), f'There are {len(possible_arrangements)} possible arrangements.')
        for arrangement in arrangements:
            self.assertIn(arrangement, possible_arrangements)


