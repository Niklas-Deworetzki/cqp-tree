import unittest

from cqp_tree.utils import *


class UtilsTest(unittest.TestCase):

    def test_names_generates_fresh_names(self):
        limit = 1000

        seen = set()
        for index, name in enumerate(names_from_alphabet('abc')):
            self.assertNotIn(name, seen, f'{name} should be a fresh name.')
            seen.add(name)

            if index == limit:
                break

