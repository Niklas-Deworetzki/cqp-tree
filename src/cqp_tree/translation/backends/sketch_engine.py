from itertools import permutations
from typing import Iterable, Optional, override

from cqp_tree.translation.backends.common import (
    Configuration,
    GlobalConstraint,
    Operator,
    Query,
    QueryFormatter,
    Span,
    SpanMode,
    Token,
    add_anchors,
    prefix_compact_arrangements,
    query,
)
from cqp_tree.translation.errors import NotSupported
from cqp_tree.utils import filter_is_instance, flatmap, flatmap_set, partition_set

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
    """
    Given an unprocessed query, partitions predicates into those that can
    be placed on a token and global predicates.
    """

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


def get_ordered_fragment(
    q: query.Query,
    tokens: dict[query.Identifier, query.Token],
) -> Optional[Query]:
    order_constraints = filter_is_instance(
        q.constraints, query.OrderConstraint | query.AnchorConstraint
    )
    order_constraints = list(order_constraints)
    if not order_constraints:
        return None

    ordered_token_ids = flatmap_set(order_constraints, lambda x: x)
    mk_token = lambda k, _: tokens[k]
    return prefix_compact_arrangements(ordered_token_ids, order_constraints, mk_token)


def build_linear_query(
    fragments: list[Query],
    predicates: list[set[query.Predicate]],
    dependencies: list[set[query.Dependency]],
    span: str,
) -> Query:
    """
    Builds a linearized query of the following shape, where Fi is fragment i and constraints(i)
    is both predicates and dependencies at i:

    F0 & constraints(0)
    Fn within (<s/> containing F(n-1)) & constraints(n) within <s/>
    """
    s = Span(span, SpanMode.FULL)

    def within(q: Query, other: Query) -> Query:
        return Operator('within', [q, other])

    def s_containing(other: Query) -> Query:
        return Operator('containing', [s, other])

    (q, pred, deps), *tail = zip(fragments, predicates, dependencies)
    result = q
    if not tail:
        # Restrict to span, if requested.
        result = within(result, s)

    if pred or deps:
        result = GlobalConstraint(result, pred, deps)

    for q, pred, deps in tail:
        if isinstance(result, GlobalConstraint):
            # Add 'within <s/>' to allow for global constraints in inner query.
            # But only if necessary.
            result = within(result, s)

        # Add 'within (<s/> containing F(n-1))'
        result = within(result, s_containing(q))

        if pred or deps:
            # Don't emit constraints, if there is nothing to constraint.
            result = GlobalConstraint(result, pred, deps)
    return result


def get_fragments(q: query.Query, span: str, tokens: dict[query.Identifier, Token]) -> list[Query]:
    """
    Returns all query fragments. Fragments are either individual tokens in free order
    or a sequence of tokens in constrained order.

    The span parameter is required to add anchors, if relevant constraints exist.
    """
    token_ids = set(tokens.keys())
    fragments: list[Query] = []

    if ordered_fragment := get_ordered_fragment(q, tokens):
        # Include ordered fragment
        ordered_fragment = add_anchors(ordered_fragment, q, span)
        fragments.append(ordered_fragment)
        token_ids -= ordered_fragment.defined_identifiers()

    # Include all free order fragments
    fragments.extend(tokens[i] for i in token_ids)

    def heuristic_score_order(fragments_to_score: list[Query]) -> float:
        score = 0.0
        available = set()

        for i, fragment in enumerate(fragments_to_score):
            defined_ids = fragment.defined_identifiers()

            # Does this fragment connect to something already bound?
            has_connection = any(
                (d.src in defined_ids and d.dst in available)
                or (d.dst in defined_ids and d.src in available)
                for d in q.dependencies
            )

            if i == 0:
                # This fragment is only matched once and has to be compatible with everything else.
                # Prefer a token with constraints or a complex sequence.
                if isinstance(fragment, Token):
                    score += len(fragment.associated_predicates)
                else:
                    score += 3

            elif i == len(fragments) - 1:
                # The final fragment is fully enumerated.
                # Prefer one that can complete dependencies.
                if has_connection:
                    score += 8

            else:
                # Filter for dependencies as early as possible.
                if has_connection:
                    score += 3
                else:
                    score -= 2

            available.update(fragment.defined_identifiers())
        return score

    # Find the best way of ordering fragments, according to heuristics.
    best_order = max(permutations(fragments), key=heuristic_score_order)
    return list(best_order)


def schedule_predicates(
    order: list[Query],
    predicates: set[query.Predicate],
    dependencies: set[query.Dependency],
) -> tuple[list[set[query.Predicate]], list[set[query.Dependency]]]:
    """
    Given an ordered list of fragments, returns associated predicates and dependencies.
    """
    available: set[query.Identifier] = set()
    remaining_predicates: set[query.Predicate] = predicates
    remaining_dependencies: set[query.Dependency] = dependencies
    scheduled_predicates, scheduled_dependencies = [], []

    for fragment in order:
        available |= fragment.defined_identifiers()

        def can_be_committed(p: query.Predicate | query.Dependency) -> bool:
            return p.referenced_identifiers() <= available

        # See which predicates are ready and keep the remainder around for the next iteration.
        ready, remaining_predicates = partition_set(remaining_predicates, can_be_committed)
        scheduled_predicates.append(ready)

        # See which dependencies are ready and keep the remainder around for the next iteration.
        ready, remaining_dependencies = partition_set(remaining_dependencies, can_be_committed)
        scheduled_dependencies.append(ready)

    return scheduled_predicates, scheduled_dependencies


def sketchengine_from_query(q: query.Query, configuration: Configuration) -> Query:
    span = configuration.span or 's'

    for constraint in q.constraints:
        if isinstance(constraint, query.Constraint.Distance):
            raise NotSupported('Cannot encode distance constraints for (No)Sketch Engine, yet.')

    tokens, global_predicates = associate_predicates(q)
    fragments = get_fragments(q, span, tokens)
    predicates, dependencies = schedule_predicates(
        fragments, global_predicates, set(q.dependencies)
    )
    return build_linear_query(fragments, predicates, dependencies, span)


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
