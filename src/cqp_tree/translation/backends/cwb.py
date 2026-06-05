from functools import reduce
from typing import Iterable, override

from cqp_tree.translation.backends.common import (
    Configuration,
    Operator,
    Query,
    QueryFormatter,
    Sequence,
    Token,
    add_within_and_anchors,
    arrangements,
    query,
)
from cqp_tree.utils import LOWERCASE_ALPHABET, partition_set

TOKEN_ALPHABET = LOWERCASE_ALPHABET


def from_arrangement(
    arrangement: list[query.Identifier],
    dependencies: set[query.Dependency],
    predicates: set[query.Predicate],
) -> Query:
    """Build a CWB Query for a sequence of Identifiers."""
    visited_tokens: set[query.Identifier] = set()
    remaining_dependencies = dependencies
    remaining_predicates = predicates

    converted_tokens = [Token(i) for i in arrangement]
    for token in converted_tokens:
        visited_tokens.add(token.identifier)

        committable_dependencies, remaining_dependencies = partition_set(
            remaining_dependencies,
            lambda rel: rel.referenced_identifiers().issubset(visited_tokens),
        )
        committable_predicates, remaining_predicates = partition_set(
            remaining_predicates,
            lambda pred: pred.referenced_identifiers().issubset(visited_tokens),
        )

        token.associated_dependencies.update(committable_dependencies)
        token.associated_predicates.update(  # Lower predicates when associating with token.
            p.lower_onto(token.identifier) for p in committable_predicates
        )

    # Build all tokens into a sequence.
    return reduce(Sequence, converted_tokens)


def from_all_arrangements(
    identifiers: set[query.Identifier],
    dependencies: set[query.Dependency],
    constraints: set[query.Constraint],
    predicates: set[query.Predicate],
) -> Query:
    """Build a query over all sequences of Identifiers."""
    all_arrangements = [
        from_arrangement(arrangement, dependencies, predicates)
        for arrangement in arrangements(identifiers, constraints)
    ]
    return Operator('|', all_arrangements)


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
