from typing import Callable, Iterable, override

from cqp_tree.translation.backends.common import (
    Configuration,
    Query,
    QueryFormatter,
    Token,
    add_within_and_anchors,
    prefix_compact_arrangements,
    query,
)
from cqp_tree.utils import LOWERCASE_ALPHABET, partition_set

TOKEN_ALPHABET = LOWERCASE_ALPHABET


def _token_constructor(
    dependencies: set[query.Dependency],
    predicates: set[query.Predicate],
) -> Callable[[query.Identifier, set[query.Identifier]], Token]:

    def token_constructor(
        identifier: query.Identifier,
        visited_identifiers: set[query.Identifier],
    ) -> Token:
        _, remaining_dependencies = partition_set(
            dependencies,
            lambda rel: rel.referenced_identifiers().issubset(visited_identifiers),
        )
        _, remaining_predicates = partition_set(
            predicates,
            lambda pred: pred.referenced_identifiers().issubset(visited_identifiers),
        )

        committable_dependencies, _ = partition_set(
            remaining_dependencies,
            lambda rel: rel.referenced_identifiers().issubset(visited_identifiers | {identifier}),
        )
        committable_predicates, _ = partition_set(
            remaining_predicates,
            lambda pred: pred.referenced_identifiers().issubset(visited_identifiers | {identifier}),
        )

        token = Token(identifier)
        token.associated_dependencies.update(committable_dependencies)
        token.associated_predicates.update(  # Lower predicates when associating with token.
            p.lower_onto(token.identifier) for p in committable_predicates
        )
        return token

    return token_constructor


def from_all_arrangements(
    identifiers: set[query.Identifier],
    dependencies: set[query.Dependency],
    constraints: set[query.Constraint],
    predicates: set[query.Predicate],
) -> Query:
    """Build a query over all sequences of Identifiers."""
    ctor = _token_constructor(dependencies, predicates)
    return prefix_compact_arrangements(identifiers, constraints, ctor)


ORDER_TO_OPERATOR = {
    query.Compare.EQ: '=',
    query.Compare.NE: '!=',
    query.Compare.LT: '<',
    query.Compare.GT: '>',
}


def distance_to_operand(constraint: query.Constraint.Distance) -> query.Predicate:
    fst, snd = constraint
    dist_function = query.Function(
        'distabs',
        query.Reference(fst),
        query.Reference(snd),
    )
    distance_literal = query.Literal(str(constraint.distance))
    return query.Comparison(dist_function, ORDER_TO_OPERATOR[constraint.order], distance_literal)


def cwb_from_query(q: query.Query, configuration: Configuration) -> Query:
    """Translate a tree-based query into a CQP query for all different arrangements of tokens."""

    predicates = set(pred.normalize() for pred in q.predicates)
    for constraint in q.constraints:
        if isinstance(constraint, query.Constraint.Distance):
            predicates.add(distance_to_operand(constraint))

    for token in q.tokens:  # Raise local predicates to prepare re-ordering.
        if token.attributes is not None:
            raised_predicate = token.attributes.raise_from(token.identifier)
            raised_predicate = raised_predicate.normalize()
            predicates.add(raised_predicate)

    result = from_all_arrangements(
        {token.identifier for token in q.tokens},
        set(q.dependencies),
        set(q.constraints),
        predicates,
    )

    return add_within_and_anchors(result, q, configuration)


class CwbFormatter(QueryFormatter):

    @classmethod
    def names(cls) -> Iterable[str]:
        return TOKEN_ALPHABET

    @override
    def format_global_constraint(
        self, base: str, predicates: list[str], dependencies: list[str]
    ) -> str:
        constraint_repr = ' & '.join(predicates + dependencies)
        return f'{base} :: {constraint_repr}'

    @override
    def format_within_constraint(self, base: str, span: str) -> str:
        return f'{base} within {span}'
