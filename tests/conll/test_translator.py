import os
import unittest

from cqp_tree import ParsingFailed, NotSupported
from cqp_tree.frontends.conll import query_from_conll


class TranslationTests(unittest.TestCase):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    
    def n_tokens(self, conll):
        # without importing conll lib because Python messes up with names
        return int(conll.split("\n")[-1].split("\t")[0])

    def test_invalid_conll(self):
        with open(os.path.join(self.dir_path, "invalid.conllu")) as f:
            conll = f.read()
        
        # parsing fails
        self.assertRaises(ParsingFailed, query_from_conll, conll)

    def test_full_conll(self):
        with open(os.path.join(self.dir_path, "full.conllu")) as f:
            conll = f.read()
        cqp = query_from_conll(conll)
        
        # translation does something
        self.assertIsNotNone(cqp)

        # the number of tokens and dependencies is correct
        n = self.n_tokens(conll)
        self.assertEqual(len(cqp.tokens), n)
        self.assertEqual(len(cqp.dependencies), n - 1)

    def test_underspecified_conll(self):
        with open(os.path.join(self.dir_path, "partial.conllu")) as f:
            conll = f.read()

        # translation does something
        cqp = query_from_conll(conll)
        self.assertIsNotNone(cqp)

        # the number of tokens and dependencies is correct
        n = self.n_tokens(conll)
        self.assertEqual(len(cqp.tokens), n)
        self.assertEqual(len(cqp.dependencies), n - 1)

        # empty fields are ignored (no _ in the query)
        def flatten(nested):
            return [el for sublist in nested for el in sublist]
        self.assertNotIn('"_"', str(cqp))

    def test_too_underspecified_conll(self):
        with open(os.path.join(self.dir_path, "underspecified.conllu")) as f:
            conll = f.read()

        # leaving IDs and/or HEADs empty is not supported
        self.assertRaises(NotSupported, query_from_conll, conll)

    def test_mwe_conll(self):
        with open(os.path.join(self.dir_path, "mwes.conllu")) as f:
            conll = f.read()
        cqp = query_from_conll(conll)

        # translation does something
        self.assertIsNotNone(cqp)

        # the number of tokens and dependencies is correct, despite MWE lines
        n = self.n_tokens(conll)
        self.assertEqual(len(cqp.tokens), n)
        self.assertEqual(len(cqp.dependencies), n - 1)