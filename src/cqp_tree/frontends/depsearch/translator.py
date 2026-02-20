import re
from dataclasses import dataclass, field
from typing import Callable, Union

from antlr4.tree.Tree import TerminalNode

import cqp_tree.translation as ct
from cqp_tree.frontends.antlr_utils import make_parse, string_of_token
from cqp_tree.frontends.depsearch.antlr import DepsearchLexer, DepsearchParser as Depsearch

parse: Callable[[str], Depsearch.QueryContext] = make_parse(
    DepsearchLexer, Depsearch, Depsearch.query
)

WORDFORM_ATTRIBUTE = ct.Attribute(None, 'word')
POS_ATTRIBUTE = ct.Attribute(None, 'pos')
LEMMA_ATTRIBUTE = ct.Attribute(None, 'lemma')
DEPREL_ATTRIBUTE = ct.Attribute(None, 'deprel')

LINEAR_DISTANCE_PATTERN = re.compile(r'<lin_-?([0-9]+):-?([0-9]+)')


def extract_bounds_from_distance(distance: TerminalNode) -> tuple[int, int]:
    """Turn a linear distance like <lin_4:8 into the bounds (4, 8)."""
    text = string_of_token(distance)
    try:
        match = LINEAR_DISTANCE_PATTERN.match(text)
        min_dist = int(match.group(1))
        max_dist = int(match.group(2))

        if min_dist < 0:
            raise ValueError(f'{min_dist} cannot be negative')
        if max_dist < 0:
            raise ValueError(f'{max_dist} cannot be negative')
        if min_dist > max_dist:
            raise ValueError(f'{min_dist} may not be larger than {max_dist}')
        return min_dist, max_dist

    except ValueError as e:
        raise ct.ParsingFailed(ct.InputError(distance.getSourceInterval(), str(e) + ' in ' + text))


@ct.translator('depsearch')
def translate_depsearch(depsearch: str) -> ct.Recipe:
    parsed = parse(depsearch)
    return QueryBuilder.translate_query(parsed)


# All abstract antlr types that represent a token.
type DepsearchTokenContext = Union[
    Depsearch.TokenExpressionContext,
    Depsearch.PossiblyNegatedTokenContext,
    Depsearch.AtomicTokenContext,
]

# All abstract antlr types that represent a dependency.
type DepsearchDependencyContext = Union[
    Depsearch.DependencyExpressionContext,
    Depsearch.AtomicDependencyContext,
]


# Types that simply wrap another token expression.
# They have a field .exp that contains the wrapped expression.
WRAPPER_TYPES = (
    Depsearch.PossiblyNegatedTokenContext,
    Depsearch.JustATokenContext,
    Depsearch.ParenthesizedTokenContext,
)

# Types correspond to some predicate.
SUPPORTED_PREDICATE_TYPES = (
    Depsearch.ConjunctionTokenContext,
    Depsearch.DisjunctionTokenContext,
    Depsearch.NegationTokenContext,
    Depsearch.AttributeTokenContext,
    Depsearch.WordOrTagTokenContext,
    Depsearch.WordformTokenContext,
)


@dataclass(frozen=True)
class QueryBuilder:
    tokens: list[ct.Token] = field(default_factory=list)
    dependencies: list[ct.Dependency] = field(default_factory=list)
    constraints: list[ct.Constraint] = field(default_factory=list)
    predicates: list[ct.Predicate] = field(default_factory=list)

    @staticmethod
    def translate_query(query: Depsearch.QueryContext):
        if query.allQuantified() is not None:
            raise ct.NotSupported(
                'Cannot translate universally-quantified queries using the -> operator.'
            )

        expression, *additional_expressions = list(query.tokenExpression())
        if additional_expressions:
            raise ct.NotSupported('Cannot translate queries using the + operator yet.')

        builder = QueryBuilder()
        builder.translate_token(expression)
        query = ct.Query(
            tokens=builder.tokens,
            dependencies=builder.dependencies,
            constraints=builder.constraints,
            predicates=builder.predicates,
        )
        return ct.Recipe.of_query(query)

    def translate_predicate(self, exp: DepsearchTokenContext) -> ct.Predicate:
        if isinstance(exp, WRAPPER_TYPES):
            return self.translate_predicate(exp.exp)

        elif isinstance(exp, Depsearch.ConjunctionTokenContext):
            lhs = self.translate_predicate(exp.lhs)
            rhs = self.translate_predicate(exp.lhs)
            return ct.Conjunction([lhs, rhs])

        elif isinstance(exp, Depsearch.DisjunctionTokenContext):
            lhs = self.translate_predicate(exp.lhs)
            rhs = self.translate_predicate(exp.lhs)
            return ct.Disjunction([lhs, rhs])

        elif isinstance(exp, Depsearch.NegationTokenContext):
            res = self.translate_predicate(exp.exp)
            return ct.Negation(res)

        elif isinstance(exp, Depsearch.AttributeTokenContext):
            # TODO: Special case for L=cat (lemma = cat)
            key, value = string_of_token(exp.key), string_of_token(exp.value)
            key_attribute = ct.Attribute(None, key)
            value_literal = ct.Literal(f'"{value}"', represents_regex=False)
            return ct.Comparison(key_attribute, '=', value_literal)

        elif isinstance(exp, Depsearch.WordOrTagTokenContext):
            # TODO: Detect whether exp.Value() is a part of speech tag (or wordform otherwise)
            value = string_of_token(exp.Value())
            value_literal = ct.Literal(value, represents_regex=False)
            return ct.Comparison(WORDFORM_ATTRIBUTE, '=', value_literal)

        elif isinstance(exp, Depsearch.WordformTokenContext):
            value = string_of_token(exp.String())
            value_literal = ct.Literal(value, represents_regex=False)
            return ct.Comparison(WORDFORM_ATTRIBUTE, '=', value_literal)

        else:
            # Should only be called with these types.
            assert isinstance(exp, SUPPORTED_PREDICATE_TYPES), f'Unsupported type: {type(exp)}'
            raise ct.NotSupported('This query cannot be translated.')

    def translate_token(self, exp: DepsearchTokenContext) -> ct.Token:
        if isinstance(exp, WRAPPER_TYPES):
            return self.translate_token(exp.exp)

        if isinstance(exp, Depsearch.ArbitraryTokenContext):
            token = ct.Token()
            self.tokens.append(token)
            return token

        elif isinstance(exp, SUPPORTED_PREDICATE_TYPES):
            pred = self.translate_predicate(exp)
            token = ct.Token(attributes=pred)
            self.tokens.append(token)
            return token

        elif isinstance(exp, Depsearch.SequenceTokenContext):
            fst = self.translate_token(exp.lhs)
            snd = self.translate_token(exp.rhs)

            self.constraints.append(
                ct.Constraint.order(fst.identifier, snd.identifier),
            )
            self.constraints.append(
                ct.Constraint.distance(fst.identifier, snd.identifier) == 1,
            )
            return fst

        elif isinstance(exp, Depsearch.DistanceTokenContext):
            fst = self.translate_token(exp.lhs)
            snd = self.translate_token(exp.rhs)

            min_dist, max_dist = extract_bounds_from_distance(exp.LinearDistance())
            self.constraints.append(
                ct.Constraint.distance(fst.identifier, snd.identifier) >= min_dist
            )
            self.constraints.append(
                ct.Constraint.distance(fst.identifier, snd.identifier) <= max_dist
            )

            if direction := exp.directionModifier():
                self.translate_direction(fst.identifier, snd.identifier, direction)

            return fst

        elif isinstance(exp, Depsearch.DependenciesTokenContext):
            src = self.translate_token(exp.src)
            for dependency in exp.dependencyDescription():
                dst = self.translate_token(dependency.dst)
                self.translate_dependencies(
                    src.identifier, dst.identifier, dependency.dependencyExpression()
                )
            return src

        else:
            raise ct.NotSupported('This query cannot be translated.')

    def translate_direction(
        self, a: ct.Identifier, b: ct.Identifier, direction: Depsearch.DirectionModifierContext
    ):
        if isinstance(direction, Depsearch.LeftOfContext):
            order = ct.Constraint.order(a, b)
        else:
            order = ct.Constraint.order(b, a)
        self.constraints.append(order)

    def translate_dependencies(
        self, src: ct.Identifier, dst: ct.Identifier, exp: DepsearchDependencyContext
    ):
        if isinstance(
            exp, Depsearch.JustADependencyContext | Depsearch.ParenthesizedDependencyContext
        ):
            self.translate_dependencies(src, dst, exp.exp)

        elif isinstance(exp, Depsearch.DependencyContext):
            if direction := exp.directionModifier():
                self.translate_direction(src, dst, direction)

            if isinstance(exp.dependencyOperator(), Depsearch.GovernedByContext):
                src, dst = dst, src

            if dependency_type := exp.Value():
                is_negated = bool(exp.negatedType)

                deptype_text = string_of_token(dependency_type)
                deptype_literal = ct.Literal(deptype_text, represents_regex=False)
                deptype_predicate = ct.Comparison(
                    DEPREL_ATTRIBUTE,
                    '!=' if is_negated else '=',
                    deptype_literal,
                )
                self.predicates.append(deptype_predicate.raise_from(dst))

            self.dependencies.append(ct.Dependency(src, dst))

        else:
            # TODO: Optimize cases like cat >amod|>nmod _ into disjunction over dependency types.
            raise ct.NotSupported('Cannot translate complex dependency expressions yet.')
