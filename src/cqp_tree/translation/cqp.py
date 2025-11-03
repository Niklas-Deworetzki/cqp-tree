from abc import ABC, abstractmethod
from argparse import Namespace
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from cqp_tree.translation import query
from cqp_tree.utils import (
    LOWERCASE_ALPHABET,
    UPPERCASE_ALPHABET,
    associate_with_names,
    flatmap_set,
    partition_set,
    to_str,
)

Environment = dict[query.Identifier, str]

TOKEN_ALPHABET = LOWERCASE_ALPHABET
QUERY_ALPHABET = UPPERCASE_ALPHABET

CQP_OPERATIONS = {
    query.SetOperator.CONJUNCTION: 'intersect',
    query.SetOperator.DISJUNCTION: 'union',
    query.SetOperator.SUBTRACTION: 'diff',
}


class Query(ABC):
    """Abstract base class for all queries."""

    target_identifier: Optional[query.Identifier]

    @abstractmethod
    def referenced_identifiers(self) -> set[query.Identifier]: ...

    @abstractmethod
    def format(self, environment: Environment) -> str: ...

    def __str__(self):
        environment = associate_with_names(self.referenced_identifiers(), TOKEN_ALPHABET)
        return self.format(environment)


@dataclass
class Sequence(Query):
    """Class representing a sequence of queries."""

    lhs: Query
    rhs: Query

    def referenced_identifiers(self) -> set[query.Identifier]:
        return self.lhs.referenced_identifiers() | self.rhs.referenced_identifiers()

    def format(self, environment: Environment) -> str:
        def format_subquery(q: Query) -> str:
            res = q.format(environment)
            return f'({res})' if isinstance(q, Operator) else res

        lhs_repr = format_subquery(self.lhs)
        rhs_repr = format_subquery(self.rhs)
        return f'{lhs_repr} []* {rhs_repr}'


@dataclass
class Operator(Query):
    """Class representing multiple queries joined by some operator (disjunction, for example)."""

    operator: str
    queries: list[Query]

    def referenced_identifiers(self) -> set[query.Identifier]:
        return flatmap_set(self.queries, lambda q: q.referenced_identifiers())

    def format(self, environment: Environment) -> str:
        parts = []
        for q in self.queries:
            if isinstance(q, (Token, Sequence)):
                parts.append(q.format(environment))
            else:
                parts.append('(' + q.format(environment) + ')')
        return f' {self.operator} '.join(parts)


@dataclass
class Token(Query):
    """Class representing a query for a single token."""

    identifier: query.Identifier
    # Initialize with empty set by default.
    associated_predicates: set[query.Predicate] = field(default_factory=set)
    associated_dependencies: set[query.Dependency] = field(default_factory=set)

    def referenced_identifiers(self) -> set[query.Identifier]:
        identifiers = flatmap_set(
            self.associated_dependencies, lambda r: r.referenced_identifiers()
        )
        identifiers |= flatmap_set(self.associated_predicates, lambda a: a.referenced_identifiers())
        identifiers -= {self.identifier}
        return identifiers

    def format(self, environment: Environment) -> str:
        prefix = environment[self.identifier] + ':' if self.identifier in environment else ''
        predicates = []
        for attribute in self.associated_predicates:
            # Expand conjunction as all predicates on token are already conjunct.
            if isinstance(attribute, query.Conjunction):
                predicates.extend(format_predicate(p, environment) for p in attribute.predicates)
            else:
                predicates.append(format_predicate(attribute, environment))

        for dependency in self.associated_dependencies:
            if dependency.src == self.identifier:
                dst = environment[dependency.dst]
                predicates.append(f'{dst}.dephead = ref')
            else:
                src = environment[dependency.src]
                predicates.append(f'dephead = {src}.ref')

        predicate = ' & '.join(predicates)
        return f'{prefix}[{predicate}]'


def format_operand(operand: query.Operand, environment: Environment) -> str:
    if isinstance(operand, query.Attribute):
        if operand.reference is not None:
            return f'{environment[operand.reference]}.{operand.attribute}'
        return operand.attribute
    elif isinstance(operand, query.Reference):
        if operand.reference is not None:
            return environment[operand.reference]
        return '_'
    elif isinstance(operand, query.Function):
        args = ', '.join(format_operand(arg, environment) for arg in operand.args)
        return f'{operand.name}({args})'
    assert isinstance(operand, query.Literal), 'Operand must be either Attribute or Literal.'
    return operand.value


def format_predicate(predicate: query.Predicate, environment: Environment) -> str:
    if isinstance(predicate, query.Exists):
        return format_operand(predicate.attribute, environment)
    elif isinstance(predicate, query.Negation):
        return f'!{format_predicate(predicate.predicate, environment)}'
    if isinstance(predicate, query.Comparison):
        lhs = format_operand(predicate.lhs, environment)
        rhs = format_operand(predicate.rhs, environment)
        return f'({lhs} {predicate.operator} {rhs})'
    else:
        assert isinstance(predicate, (query.Conjunction, query.Disjunction))
        operators = {
            query.Conjunction: '&',
            query.Disjunction: '|',
        }
        predicates = map(lambda p: format_predicate(p, environment), predicate.predicates)
        return to_str(predicates, '(', f' {operators[type(predicate)]} ', ')')


def arrangements(
    identifiers: set[query.Identifier],
    constraints: Iterable[query.Constraint],
) -> Iterator[list[query.Identifier]]:
    """Arrange a set of Identifiers into all sequences allowed by the given Constraints"""
    cannot_be_after = {i: set() for i in identifiers}
    for constraint in constraints:
        if isinstance(constraint, query.Constraint.Order):
            fst, snd = constraint
            cannot_be_after[snd].add(fst)

    # Buffer with space for all identifiers.
    arrangement: list[query.Identifier | None] = [None] * len(identifiers)

    def arrange(index: int, remaining_identifiers: set[query.Identifier]):
        if index == len(arrangement):
            yield list(arrangement)  # Everything is put into an order. Yield it!
        else:
            for identifier in remaining_identifiers:
                arrangement[index] = identifier

                restricted = cannot_be_after[identifier]  # Continue for remaining identifiers.
                yield from arrange(index + 1, (remaining_identifiers - restricted) - {identifier})

    yield from arrange(0, identifiers)


def from_arrangement(
    arrangement: list[query.Identifier],
    dependencies: set[query.Dependency],
    predicates: set[query.Predicate],
) -> Query:
    """Build a Query for a sequence of Identifiers."""
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
    res = converted_tokens[0]
    for index in range(len(arrangement) - 1):
        res = Sequence(res, converted_tokens[index + 1])
    return res


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


def from_query(q: query.Query) -> Query:
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

    return from_all_arrangements(
        {token.identifier for token in q.tokens},
        set(q.dependencies),
        set(q.constraints),
        predicates,
    )


def format_plan(plan: query.Recipe, args: Namespace | None) -> Iterator[str]:
    span = ''
    if args is not None and args.span is not None:
        span = f' within <{args.span}>'

    environment = associate_with_names(plan.identifiers(), QUERY_ALPHABET)
    parts = plan.as_dict()

    def rec(goal: query.Identifier, include_assignment: bool = True) -> Iterator[str]:
        part = parts[goal]
        if isinstance(part, query.Operation):
            op, lhs, rhs = (
                CQP_OPERATIONS[part.operator],
                environment[part.lhs],
                environment[part.rhs],
            )
            formatted = f'{op} {lhs} {rhs};'
            yield from rec(part.lhs)
            yield from rec(part.rhs)
        else:
            formatted = str(from_query(part)) + span + ';'

        if include_assignment:
            formatted = f'{environment[goal]} = {formatted}'
        yield formatted

    yield from rec(plan.goal, include_assignment=False)
