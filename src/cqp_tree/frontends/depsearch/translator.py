import re
from dataclasses import dataclass, field
from typing import Callable, Iterator, Union

from antlr4.tree.Tree import TerminalNode

import cqp_tree.translation as ct
from cqp_tree import Configuration, DeclaredConfig
from cqp_tree.frontends.antlr_utils import make_parse, string_of_token
from cqp_tree.frontends.depsearch.antlr import DepsearchLexer, DepsearchParser as Depsearch

parse: Callable[[str], Depsearch.QueryContext] = make_parse(
    DepsearchLexer, Depsearch, Depsearch.query
)


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


@ct.translator(
    'depsearch',
    DeclaredConfig(
        key='pos',
        readable_name='Part-Of-Speech annotation',
        readable_description='Name of the annotation layer encoding part-of-speech tags.',
        validation_type=str,
        default_value='pos',
    ),
)
def translate_depsearch(depsearch: str, config: Configuration) -> ct.Recipe:
    parsed = parse(depsearch)
    return QueryBuilder.translate_query(parsed, config)


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
    configuration: Configuration
    tokens: list[ct.Token] = field(default_factory=list)
    dependencies: list[ct.Dependency] = field(default_factory=list)
    constraints: list[ct.Constraint] = field(default_factory=list)
    predicates: list[ct.Predicate] = field(default_factory=list)

    @staticmethod
    def translate_query(query: Depsearch.QueryContext, config: Configuration):
        if query.allQuantified() is not None:
            raise ct.NotSupported(
                'Cannot translate universally-quantified queries using the -> operator.'
            )

        expression, *additional_expressions = list(query.tokenExpression())
        if additional_expressions:
            raise ct.NotSupported('Cannot translate queries using the + operator yet.')

        builder = QueryBuilder(config)
        builder.translate_token(expression)
        query = ct.Query(
            tokens=builder.tokens,
            dependencies=builder.dependencies,
            constraints=builder.constraints,
            predicates=builder.predicates,
        )
        return ct.Recipe.of_query(query)

    def wordform_attribute(self) -> ct.Attribute:
        return ct.Attribute(None, self.configuration.word)

    def deprel_attribute(self) -> ct.Attribute:
        return ct.Attribute(None, self.configuration.deprel)

    def lemma_attribute(self) -> ct.Attribute:
        return ct.Attribute(None, self.configuration.lemma)

    def pos_attribute(self) -> ct.Attribute:
        return ct.Attribute(None, self.configuration.pos)

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
            key = string_of_token(exp.key)
            key_attribute = ct.Attribute(None, key)

            if exp.value is not None:
                value = string_of_token(exp.value)
                value_literal = ct.Literal(f'"{value}"', represents_regex=False)
            else:
                # This is a non-standard extension we added to support regular expressions.
                regex = string_of_token(exp.regex)
                value_literal = ct.Literal(regex, represents_regex=True)

            return ct.Comparison(key_attribute, '=', value_literal)

        elif isinstance(exp, Depsearch.WordOrTagTokenContext):
            # TODO: Detect whether exp.Value() is a part of speech tag (or wordform otherwise)
            value = string_of_token(exp.Value())
            value_literal = ct.Literal(f'"{value}"', represents_regex=False)
            return ct.Comparison(self.wordform_attribute(), '=', value_literal)

        elif isinstance(exp, Depsearch.WordformTokenContext):
            value = string_of_token(exp.String())
            value_literal = ct.Literal(value, represents_regex=False)
            return ct.Comparison(self.wordform_attribute(), '=', value_literal)

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

            if order := exp.orderModifier():
                self.translate_order(fst.identifier, snd.identifier, order)

            return fst

        elif isinstance(exp, Depsearch.DependenciesTokenContext):
            src = self.translate_token(exp.src)
            for description in exp.dependencyDescription():
                dst = self.translate_token(description.dst)
                dependencies = list(self.collect_dependencies(description.dependencyExpression()))
                self.translate_dependencies(src.identifier, dst.identifier, dependencies)
            return src

        else:
            raise ct.NotSupported('This query cannot be translated.')

    def translate_order(
        self, a: ct.Identifier, b: ct.Identifier, order: Depsearch.OrderModifierContext
    ):
        if isinstance(order, Depsearch.RightOfContext):
            a, b = b, a
        self.constraints.append(ct.Constraint.order(a, b))

    def collect_dependencies(
        self, exp: DepsearchDependencyContext
    ) -> Iterator[Depsearch.DependencyContext]:
        if isinstance(exp, Depsearch.DependencyContext):
            yield exp
        elif isinstance(
            exp, Depsearch.JustADependencyContext | Depsearch.ParenthesizedDependencyContext
        ):
            yield from self.collect_dependencies(exp.exp)
        elif isinstance(exp, Depsearch.DisjunctionDependencyContext):
            yield from self.collect_dependencies(exp.lhs)
            yield from self.collect_dependencies(exp.rhs)
        else:
            raise ct.NotSupported('Negated dependencies cannot be translated yet.')

    def translate_dependencies(
        self,
        src: ct.Identifier,
        dst: ct.Identifier,
        dependencies: list[Depsearch.DependencyContext],
    ):
        governs = False
        governed_by = False
        deprel_types = []

        for dep in dependencies:
            # Each dependency can have an order constraint, make sure to include that.
            if order := dep.orderModifier():
                self.translate_order(src, dst, order)

            # Check the direction of the dependency, this determines where deprel is stored.
            deprel_bearer = dst
            if isinstance(dep.dependencyOperator(), Depsearch.GovernedByContext):
                deprel_bearer = src

                governed_by = True
            else:
                governs = True

            if dependency_type := dep.Value():
                is_negated = bool(dep.negatedType)

                deptype_text = string_of_token(dependency_type)
                deptype_literal = ct.Literal(f'"{deptype_text}"', represents_regex=False)
                deptype_predicate = ct.Comparison(
                    self.deprel_attribute(),
                    '!=' if is_negated else '=',
                    deptype_literal,
                )
                # Collect predicate for dependency type
                deprel_types.append(deptype_predicate.raise_from(deprel_bearer))

        if deprel_types:
            # Build disjunction over all collected dependency types, if present.
            self.predicates.append(ct.Disjunction.of(deprel_types))

        if governs and governed_by:
            raise ct.NotSupported(
                'Cannot translate a dependency relation that has either side as its head.'
            )
        elif governs:
            self.dependencies.append(ct.Dependency(src, dst))
        elif governed_by:
            self.dependencies.append(ct.Dependency(dst, src))
