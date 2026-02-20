import unittest

from cqp_tree import Constraint, NotSupported, ParsingFailed
from cqp_tree.frontends.depsearch import translate_depsearch

SUPPORTED_QUERIES = [
    '_',
    'L=cat',
    '(L=cat | L=dog) & !Case=Gen',
    'cat > _',
    'cat >amod _',
    'cat >amod _ >amod _',
    'cat >amod (_ >amod _)',
    '_ >!amod _',
    'cat >amod !pretty',
    'first . second',
    'cat <lin_2:3 NOUN',
    'cat <lin_2:3@R NOUN',
    'cat <lin_2:3@L NOUN',
    'walk',
    'London',
    '"Person"',
    'L=olla',
    'NOUN',
    'Par',
    'VerbForm=Inf',
    'Past',
    'PartForm',
    'walk&NOUN',
    'NOUN&Plur&Par',
    'L=tehdä&PartForm=Pres',
    'L=kävellä|L=juosta',
    'can&!AUX',
    '!Tra',
    'voi&!L=voida',
    'walk < _',
    'walk > _',
    '_ < walk',
    '_ <nsubj _',
    '_ >nsubj _',
    '_ <cop _',
    '_ >nsubj:cop _',
    '_ >nsubj:cop _ >cop _',
    '_ <nsubj:cop _ >nmod _',
    '_ >nmod _ >nmod _',
    '_ >nmod _ >nmod _',
    '_ >nmod (_ >nmod _)',
    '_ <nsubj _ >!amod _',
    '_ >!amod _',
    'VERB >nsubj@R _',
    '_ >amod@L _ >amod@R _',
    '_ <case@R _',
    'ADJ&Tra <xcomp _',
    'VerbForm=Part <acl _ >nsubj _',
]

UNSUPPORTED_QUERIES = {
    'all-quantified query': [
        '(_ <nsubj _) -> (Person=3 <nsubj _)',
        '_ -> NOUN',
        'NOUN -> NOUN <acl:relcl _',
    ],
    'disjunction of queries': [
        '(dog <nsubj _) + cat',
        '(VERB >aux _ >aux _) + (_ >conj (_ >conj _))',
    ],
    'absence of dependency relation': [
        '_ !>amod _',
        '_ >nsubj:cop _ !>cop _',
        '_ <advcl _ !>mark _',
        '_ <nmod _ !>case _',
        '_ >nsubj:cop _ !>cop _',
    ],
    'disjunction of dependency relations': [
        'cat >amod|>nmod _',
        '_ <nsubj|<nsubj:cop _',
        'NOUN >amod (_ >amod|>acl _)',
    ],
    'complex dependency expression': [
        '_ <nsubj _ !(>amod|>acl) _',
    ],
}


class TranslatorTests(unittest.TestCase):

    def test_regression(self):
        for i, query in enumerate(SUPPORTED_QUERIES, start=1):
            with self.subTest(msg=f'Translating example #{i}'):
                try:
                    translate_depsearch(query)
                except NotSupported:
                    raise ValueError('Unsupported query: ' + query)

    def test_support_did_not_increase(self):
        self.assertTrue(UNSUPPORTED_QUERIES, msg='All queries are now supported!')
        i = 0
        for reason, queries in UNSUPPORTED_QUERIES.items():
            for query in queries:
                i += 1
                with self.subTest(msg=f'Unsupported example #{i}: {reason}'):
                    with self.assertRaises(NotSupported):
                        translate_depsearch(query)

    def test_arbitrary(self):
        query = '_'

        res = translate_depsearch(query).simple_representation()

        self.assertEqual(len(res.tokens), 1)
        self.assertEqual(len(res.predicates), 0)

    def test_valid_distance(self):
        query = '_ <lin_0:1000 _'

        res = translate_depsearch(query).simple_representation()

        a, b = res.tokens

        self.assertCountEqual(
            [
                Constraint.distance(a.identifier, b.identifier) >= 0,
                Constraint.distance(a.identifier, b.identifier) <= 1000,
            ],
            res.constraints,
        )

    def test_invalid_distance(self):
        distances = [(-1, 0), (-2, -1), (4, 0)]
        for min_dist, max_dist in distances:
            query = f'_ <lin_{min_dist}:{max_dist} _'
            with self.subTest(msg=query):
                with self.assertRaises(ParsingFailed):
                    translate_depsearch(query)

    def test_direction(self):
        res_l = translate_depsearch('_ <lin_0:1000@L _').simple_representation()
        res_r = translate_depsearch('_ <lin_0:1000@R _').simple_representation()

        [l_const] = filter(lambda x: isinstance(x, Constraint.Order), res_l.constraints)
        [r_const] = filter(lambda x: isinstance(x, Constraint.Order), res_r.constraints)
        l_order = list(l_const)
        r_order = list(r_const)

        self.assertNotEqual(
            map(l_order.index, map(lambda x: x.identifier, res_l.tokens)),
            map(r_order.index, map(lambda x: x.identifier, res_r.tokens)),
            '@L and @R constraint should modify token order.',
        )

    def test_dependency(self):
        query = '_ < _'

        res = translate_depsearch(query).simple_representation()

        self.assertNotEqual(len(res.dependencies), 0)

    def test_dependency_direction(self):
        res_l = translate_depsearch('_ < _').simple_representation()
        res_r = translate_depsearch('_ > _').simple_representation()

        [l_dep] = res_l.dependencies
        [r_dep] = res_r.dependencies
        l_idents = list(map(lambda x: x.identifier, res_l.tokens))
        r_idents = list(map(lambda x: x.identifier, res_r.tokens))

        self.assertEqual(
            l_idents.index(l_dep.src),
            r_idents.index(r_dep.dst),
            'Dependency head should be swapped with inverse dependency operator.',
        )
        self.assertEqual(
            l_idents.index(l_dep.dst),
            r_idents.index(r_dep.src),
            'Dependency head should be swapped with inverse dependency operator.',
        )

    def test_dependency_order(self):
        res_l = translate_depsearch('_ <@L _').simple_representation()
        res_r = translate_depsearch('_ <@R _').simple_representation()

        [l_const] = res_l.constraints
        [r_const] = res_r.constraints

        self.assertIsInstance(l_const, Constraint.Order)
        self.assertIsInstance(r_const, Constraint.Order)
        l_order = list(l_const)
        r_order = list(r_const)

        self.assertNotEqual(
            map(l_order.index, map(lambda x: x.identifier, res_l.tokens)),
            map(r_order.index, map(lambda x: x.identifier, res_r.tokens)),
            '@L and @R constraint should modify token order.',
        )
