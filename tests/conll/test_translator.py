import os
import unittest
import cqp_tree as ct

from cqp_tree import NotSupported, ParsingFailed
from cqp_tree.frontends.conll import translate_conll


class TranslationTests(unittest.TestCase):
    dir_path = os.path.dirname(os.path.realpath(__file__))

    def test_empty(self):
        with self.assertRaises(ParsingFailed):
            translate_conll('')

    def test_syntax_error(self):
        with self.assertRaises(ParsingFailed):
            translate_conll('abc')

    def test_id_cannot_be_unspecified(self):
        text = '''
*	This	this	PRON	DT	Number=Sing|PronType=Dem	4	nsubj	_	TokenRange=0:4
'''
        with self.assertRaises((ParsingFailed, NotSupported)):
            translate_conll(text)

    def test_id_cannot_be_no_value(self):
        text = '''
_	This	this	PRON	DT	Number=Sing|PronType=Dem	4	nsubj	_	TokenRange=0:4
'''

        with self.assertRaises((ParsingFailed, NotSupported)):
            translate_conll(text)

    def test_mwe_are_ignored(self):
        text = '''
1	Test	test	NOUN	S	Gender=Masc	0	root	_	TokenRange=0:4
2	trattamento	trattamento	NOUN	S	Gender=Masc|Number=Sing	1	nmod	_	TokenRange=5:16
3-4	delle	_	_	_	_	_	_	_	TokenRange=17:22
3	di	di	ADP	E	_	5	case	_	_
4	le	il	DET	RD	Definite=Def|Gender=Fem|Number=Plur|PronType=Art	5	det	_	_
5	MWE	MWE	PROPN	SP	_	2	nmod	_	SpaceAfter=No|TokenRange=23:26
6	.	.	PUNCT	FS	_	1	punct	_	SpaceAfter=No|TokenRange=26:27
        '''

        translation = translate_conll(text).simple_representation()

        token_count = len(translation.tokens)
        self.assertEqual(token_count, 6, f'Expected {token_count} tokens.')

    def test_empty_nodes_are_ignored(self):
        text = '''
# text = John gave Mary a book and Peter a pen.
1	John	John	PROPN	_	_	2	nsubj	_	_
2	gave	give	VERB	_	_	0	root	_	_
3	Mary	Mary	PROPN	_	_	2	iobj	_	_
4	a	a	DET	_	_	5	det	_	_
5	book	book	NOUN	_	_	2	obj	_	_
6	and	and	CCONJ	_	_	2	cc	_	_
7	Peter	Peter	PROPN	_	_	2	nsubj	_	_
7.1	_	give	VERB	_	_	_	conj	_	SpaceAfter=No
8	a	a	DET	_	_	9	det	_	_
9	pen	pen	NOUN	_	_	2	obj	_	_
10	.	.	PUNCT	_	_	2	punct	_	_
        '''

        translation = translate_conll(text).simple_representation()

        token_count = len(translation.tokens)
        self.assertEqual(token_count, 10, f'Expected {token_count} tokens.')

    def test_ignored_nodes(self):
        text = '''
# text = She can't come but John will.
1	She	she	PRON	_	_	4	nsubj	_	_
2-3	can't	_	_	_	_	_	_	_	_
2	ca	can	AUX	_	_	4	aux	_	_
3	n't	not	PART	_	_	4	advmod	_	_
4	come	come	VERB	_	_	0	root	_	_
5	but	but	CCONJ	_	_	4	cc	_	_
6	John	John	PROPN	_	_	4	nsubj	_	_
7	will	will	AUX	_	_	4	aux	_	_
7.1	_	come	VERB	_	_	_	conj	_	_
8	.	.	PUNCT	_	_	4	punct	_	_
        '''

        res = translate_conll(text).simple_representation()

        token_count = len(res.tokens)
        self.assertEqual(token_count, 8, f'Expected {token_count} tokens.')

    def test_dephead_cannot_be_underspecified(self):
        text = '''
# text = Hope this helps
1	Hope	hope	VERB	VBP	Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin	0	root	_	_
2	this	this	PRON	DT	Number=Sing|PronType=Dem	3	nsubj	_	_
3	helps	help	VERB	VBZ	Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	*	ccomp	_	_
        '''
        #                                                      This * causes an error   ^

        with self.assertRaises(ParsingFailed):
            translate_conll(text)

    def test_dephead_unknown(self):
        text = '''
# text = Hope this helps
1	Hope	hope	VERB	VBP	Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin	0	root	_	_
2	this	this	PRON	DT	Number=Sing|PronType=Dem	3	nsubj	_	_
3	helps	help	VERB	VBZ	Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	131	ccomp	_	_
        '''
        #                                                     This 131 causes an error   ^

        with self.assertRaises(NotSupported):
            translate_conll(text)

    def test_dephead_without_value_does_not_create_dependency(self):
        text = '''
# text = Hope this helps
1	Hope	hope	VERB	VBP	Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin	0	root	_	_
2	this	this	PRON	DT	Number=Sing|PronType=Dem	_	nsubj	_	_
3	helps	help	VERB	VBZ	Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	_	ccomp	_	_
        '''

        translated = translate_conll(text).simple_representation()

        dependencies = translated.dependencies
        self.assertCountEqual(dependencies, {}, 'Query should have no dependencies.')

    def test_attributes_are_extracted(self):
        text = '''
1	Hope	hope	VERB	VBP	_	0	root	_	_
        '''

        res = translate_conll(text).simple_representation()
        expected_attributes = {
            'word': 'Hope',
            'lemma': 'hope',
            'pos': 'VERB',
            'msd': 'VBP',
            'deprel': 'root',
        }

        token, *_ = res.tokens
        for key, value in expected_attributes.items():
            self.assertIn(
                ct.Comparison(
                    ct.Attribute(token.identifier, key),
                    '=',
                    ct.Literal(f'"{value}"', represents_regex=False),
                ),
                res.predicates,
            )

    def test_feats_are_translated(self):
        text = '''
1	_	_	_	_	Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin	0	_	_	_
        '''

        res = translate_conll(text).simple_representation()
        expected_attributes = {
            'Mood': 'Ind',
            'Number': 'Sing',
            'Person': '1',
            'Tense': 'Pres',
            'VerbForm': 'Fin',
        }

        token, *_ = res.tokens
        for key, value in expected_attributes.items():
            self.assertIn(
                ct.Comparison(
                    ct.Attribute(token.identifier, 'ufeats'),
                    'contains',
                    ct.Literal(f'"{key}={value}"', represents_regex=False),
                ),
                res.predicates,
            )

    def test_misc_are_extracted(self):
        text = '''
1	_	_	_	_	_	0	root	_	TokenRange=0:4|SpaceAfter=Yes
        '''

        res = translate_conll(text).simple_representation()
        expected_attributes = {
            'TokenRange': '0:4',
            'SpaceAfter': 'Yes',
        }

        token, *_ = res.tokens
        for key, value in expected_attributes.items():
            self.assertIn(
                ct.Comparison(
                    ct.Attribute(token.identifier, key),
                    '=',
                    ct.Literal(f'"{value}"', represents_regex=False),
                ),
                res.predicates,
            )


class ExtensionTests(unittest.TestCase):

    def test_anchor_on_first_token(self):
        text = '''
        1	_	_	_	_	_	_	_	_	anchored=Yes
        2	_	_	_	_	_	_	_	_	_
        '''

        res = translate_conll(text).simple_representation()
        tok = list(res.tokens)[0]

        self.assertIn(
            ct.Constraint.anchor(tok.identifier, is_first=True),
            res.constraints,
        )


    def test_anchor_on_last_token(self):
        text = '''
        1	_	_	_	_	_	_	_	_	_
        2	_	_	_	_	_	_	_	_	anchored=Yes
        '''

        res = translate_conll(text).simple_representation()
        tok = list(res.tokens)[-1]

        self.assertIn(
            ct.Constraint.anchor(tok.identifier, is_last=True),
            res.constraints,
        )


    def test_subsequent_tokens(self):
        text = '''
        1	_	_	_	_	_	_	_	_	_
        2	_	_	_	_	_	_	_	_	subsequent=Yes
        '''

        res = translate_conll(text).simple_representation()
        pre, sub, *_ = res.tokens

        self.assertIn(
            ct.Constraint.distance(pre.identifier, sub.identifier) == 1,
            res.constraints,
        )


    def test_ordered_tokens(self):
        text = '''
        1	_	_	_	_	_	_	_	_	ordered=Yes
        2	_	_	_	_	_	_	_	_	ordered=Yes
        '''

        res = translate_conll(text).simple_representation()
        pre, sub, *_ = res.tokens

        self.assertIn(
            ct.Constraint.order(pre.identifier, sub.identifier),
            res.constraints,
        )
