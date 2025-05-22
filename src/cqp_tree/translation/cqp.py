import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterator, Iterable

from cqp_tree.translation import query
from cqp_tree.utils import flatmap_set, to_str, partition_set

Environment = dict[query.Identifier, str]

ALPHABET = 'abcdefghijklmnopqrstuvwxyz'


def names():
    """Function producing an infinite stream of fresh names."""
    length = 0
    while True:
        length += 1
        for name in itertools.combinations_with_replacement(ALPHABET, length):
            yield ''.join(name)


class Query(ABC):
    """Abstract base class for all queries."""

    @abstractmethod
    def referenced_identifiers(self) -> set[query.Identifier]: ...

    @abstractmethod
    def format(self, environment: Environment) -> str: ...

    def __str__(self):
        environment = dict(zip(self.referenced_identifiers(), names()))
        return self.format(environment)


@dataclass
class Sequence(Query):
    """Class representing a sequence of queries."""

    lhs: Query
    rhs: Query
    distance: query.Distance

    def referenced_identifiers(self) -> set[query.Identifier]:
        return self.lhs.referenced_identifiers() | self.rhs.referenced_identifiers()

    def format(self, environment: Environment) -> str:
        if self.distance == -1:
            distance_repr = '[]*'
        else:
            distance_repr = ' '.join(['[]'] * self.distance)

        def format_subquery(q: Query) -> str:
            res = q.format(environment)
            return f'({res})' if isinstance(q, Operator) else res

        lhs_repr = format_subquery(self.lhs)
        rhs_repr = format_subquery(self.rhs)
        return f'{lhs_repr} {distance_repr} {rhs_repr}'


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
            if type(q) in {Token, Sequence}:
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
    assert isinstance(operand, query.Literal), 'Operand must be either Attribute or Literal.'
    return operand.value


def format_predicate(predicate: query.Predicate, environment: Environment) -> str:
    if isinstance(predicate, query.Exists):
        return format_operand(predicate.attribute, environment)
    elif isinstance(predicate, query.Negation):
        return f'!{format_predicate(predicate.predicate, environment)}'
    if isinstance(predicate, query.Expression):
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
        return to_str(predicates, '(', f' {operators[predicate.__class__]} ', ')')


def distance_between(
    constraints: Iterable[query.Constraint],
    a: query.Identifier,
    b: query.Identifier,
) -> query.Distance:
    for constraint in constraints:
        if constraint.src == a and constraint.dst == b:
            return constraint.distance
        if constraint.src == b and constraint.dst == a:
            return constraint.distance
    return query.Constraint.ARBITRARY_DISTANCE


def arrangements(
    identifiers: set[query.Identifier],
    constraints: Iterable[query.Constraint],
) -> Iterator[list[query.Identifier]]:
    """Arrange a set of Identifiers into all sequences allowed by the given Constraints"""
    cannot_be_after = {i: set() for i in identifiers}
    for constraint in constraints:
        if constraint.enforces_order:
            cannot_be_after[constraint.dst].add(constraint.src)

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


def from_sequence(
    sequence: list[query.Identifier],
    dependencies: set[query.Dependency],
    predicates: set[query.Predicate],
    constraints: set[query.Constraint],
) -> Query:
    """Build a Query for a sequence of Identifiers."""
    visited_tokens: set[query.Identifier] = set()
    remaining_dependencies = dependencies
    remaining_predicates = predicates

    converted_tokens = [Token(i) for i in sequence]
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
    for index in range(len(sequence) - 1):
        dist = distance_between(
            constraints, converted_tokens[index].identifier, converted_tokens[index + 1].identifier
        )
        res = Sequence(res, converted_tokens[index + 1], dist)
    return res


def from_query(q: query.Query) -> Query:
    """Translate a tree-based query into a CQP query for all different arrangements of tokens."""
    identifiers = {t.identifier for t in q.tokens}
    dependencies = set(q.dependencies)
    constraints = set(q.constraints)

    predicates = set(pred.normalize() for pred in q.predicates)
    for token in q.tokens:  # Raise local predicates to prepare re-ordering.
        if token.attributes is not None:
            raised_predicate = token.attributes.raise_from(token.identifier)
            raised_predicate = raised_predicate.normalize()
            predicates.add(raised_predicate)

    all_arrangements = []
    for arrangement in arrangements(identifiers, q.constraints):
        all_arrangements.append(from_sequence(arrangement, dependencies, predicates, constraints))
    return Operator('|', all_arrangements)
