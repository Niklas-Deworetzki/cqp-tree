import os
import unittest

from cqp_tree.frontends.grew.translator import parse


class ValidationTests(unittest.TestCase):

    def test_parser(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(dir_path + '/supported_constructs.grew') as f:
            result = parse(f.read())
            self.assertIsNotNone(result)
