from functools import reduce
from typing import Iterable, Optional, override

from cqp_tree.translation.backends.common import (
    Configuration,
    GlobalConstraint,
    Operator,
    Query,
    QueryFormatter,
    Sequence,
    Token,
    add_within_and_anchors,
    arrangements,
    query,
)
from cqp_tree.translation.errors import NotSupported
from cqp_tree.utils import flatmap

# manatee does weird things when "0" is included as an identifier.
# The identifier appears to not be resolved properly.
TOKEN_ALPHABET = list(map(str, range(1, 10)))


def where_to_place_predicate(predicate: query.Predicate) -> Optional[query.Identifier]:
    """
    Manatee has strong opinions about how CQP should look like. We use an excerpt from the grammar
    obtained here: https://corpora.fi.muni.cz/noske/current/src/manatee-open-2.225.8.tar.gz

    Expressions for global constraints and within tokens are inductively defined over conjunction,
    disjunction, negation and parentheses:

    globalExpr ::=
    | NUMBER DOT ATTRIBUTE EQ NUMBER DOT ATTRIBUTE
    | NUMBER DOT ATTRIBUTE NEQ NUMBER DOT ATTRIBUTE

    tokenAtom ::=
    | ATTRIBUTE EQ REGEXP
    | ATTRIBUTE NEQ REGEXP

    So we need to disect, where to put a predicate. And maybe we can't even place it.
    """
    match predicate:
        case query.Comparison(lhs=query.Attribute(reference=reference), rhs=query.Literal()):
            return reference

        case query.Comparison(lhs=query.Attribute(), rhs=query.Attribute()):
            return None

        case query.Negation():
            return where_to_place_predicate(predicate.predicate)

        case query.GenericJunction():
            unique_places = {where_to_place_predicate(p) for p in predicate.predicates}
            if len(unique_places) == 1:
                return next(iter(unique_places))

    raise NotSupported('SketchEngine does not support the way token attributes are compared.')


def collect_predicates(q: query.Query) -> set[query.Predicate]:
    predicates = set()
    predicates.update(q.predicates)
    for t in q.tokens:
        if t.attributes is not None:
            predicates.add(t.attributes.raise_from(t.identifier))
    return predicates


def unfold_predicate(predicate: query.Predicate) -> Iterable[query.Predicate]:
    if isinstance(predicate, query.Conjunction):
        for conjunct in predicate.predicates:
            yield from unfold_predicate(conjunct)
    else:
        yield predicate


def associate_predicates(
    q: query.Query,
) -> tuple[dict[query.Identifier, Token], set[query.Predicate]]:
    # Collect all the predicates
    predicates = collect_predicates(q)

    # Decide where to put the predicates
    global_predicates = set()
    per_token_predicates = {token.identifier: set() for token in q.tokens}
    for predicate in flatmap(predicates, unfold_predicate):
        if where := where_to_place_predicate(predicate):
            per_token_predicates[where].add(predicate)
        else:
            global_predicates.add(predicate)

    # Now build tokens with the predicates
    tokens: dict[query.Identifier, Token] = {}
    for token_id, predicates in per_token_predicates.items():
        lowered_predicates = {predicate.lower_onto(token_id) for predicate in predicates}
        tokens[token_id] = Token(token_id, lowered_predicates)
    return tokens, global_predicates


def sketchengine_from_query(q: query.Query, configuration: Configuration) -> Query:
    for constraint in q.constraints:
        if isinstance(constraint, query.Constraint.Distance):
            raise NotSupported('Cannot encode distance constraints for (No)Sketch Engine, yet.')

    tokens, global_predicates = associate_predicates(q)
    alternatives: list[Query] = []
    for arrangement in arrangements(set(tokens.keys()), q.constraints):
        alternative = reduce(Sequence, (tokens[i] for i in arrangement))
        alternatives.append(alternative)

    result = Operator('|', alternatives)
    if global_predicates or q.dependencies:
        result = GlobalConstraint(result, global_predicates, set(q.dependencies))

    return add_within_and_anchors(result, q, configuration)


class SketchEngineFormatter(QueryFormatter):

    @classmethod
    def names(cls) -> Iterable[str]:
        return TOKEN_ALPHABET

    @override
    def format_global_constraint(
        self, base: str, predicates: list[str], dependencies: list[str]
    ) -> str:
        constraint_repr = ' & '.join(predicates + dependencies)
        return f'({base}) & ({constraint_repr})'

    @override
    def format_within_constraint(self, base: str, span: str) -> str:
        return f'{base} within <{span}/>'
