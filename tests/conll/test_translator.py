import os
import unittest

import conllu

from cqp_tree import ParsingFailed, NotSupported
from cqp_tree.frontends.conll import translate_conll


def n_tokens(conll):
    sentence = conllu.parse(conll)[0]
    return int(sentence[-1].get('id'))


class TranslationTests(unittest.TestCase):
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def test_empty_conll(self):
        self.assertRaises(ParsingFailed, translate_conll, "")

    def test_invalid_conll(self):
        with open(os.path.join(self.dir_path, "invalid.conllu")) as f:
            conll = f.read()

        # parsing fails
        self.assertRaises(ParsingFailed, translate_conll, conll)

    def test_full_conll(self):
        with open(os.path.join(self.dir_path, "full.conllu")) as f:
            conll = f.read()

        (cqp,) = translate_conll(conll).queries

        # the number of tokens and dependencies is correct
        n = n_tokens(conll)
        self.assertEqual(len(cqp.tokens), n)
        self.assertEqual(len(cqp.dependencies), n - 1)

    def test_underspecified_conll(self):
        with open(os.path.join(self.dir_path, "partial.conllu")) as f:
            conll = f.read()

        (cqp,) = translate_conll(conll).queries

        # the number of tokens and dependencies is correct
        n = n_tokens(conll)
        self.assertEqual(len(cqp.tokens), n)
        self.assertEqual(len(cqp.dependencies), n - 1)

        self.assertNotIn('"_"', str(cqp))

    def test_too_underspecified_conll(self):
        with open(os.path.join(self.dir_path, "underspecified.conllu")) as f:
            conll = f.read()

        # leaving IDs and/or HEADs empty is not supported
        self.assertRaises(NotSupported, translate_conll, conll)

    def test_mwe_conll(self):
        with open(os.path.join(self.dir_path, "mwes.conllu")) as f:
            conll = f.read()

        (cqp,) = translate_conll(conll).queries

        # the number of tokens and dependencies is correct, despite MWE lines
        n = n_tokens(conll)
        self.assertEqual(len(cqp.tokens), n)
        self.assertEqual(len(cqp.dependencies), n - 1)
