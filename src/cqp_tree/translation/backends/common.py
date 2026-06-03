from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, override

from cqp_tree.configuration import Configuration
from cqp_tree.translation import query
from cqp_tree.utils import (
    associate_with_names,
    filter_is_instance,
    flatmap_set,
    to_str,
)

Environment = dict[query.Identifier, str]


class Query(ABC):
    """Abstract base class for all queries."""

    target_identifier: Optional[query.Identifier]

    @abstractmethod
    def referenced_identifiers(self) -> set[query.Identifier]: ...

    # This is bound in cqp.py after knowing all the backend formatters
    def to_string(self, configuration: Configuration) -> str: ...


@dataclass
class GlobalConstraint(Query):
    base: Query
    # Initialize with empty set by default.
    associated_predicates: set[query.Predicate] = field(default_factory=set)
    associated_dependencies: set[query.Dependency] = field(default_factory=set)

    @override
    def referenced_identifiers(self) -> set[query.Identifier]:
        identifiers = self.base.referenced_identifiers()
        identifiers |= flatmap_set(
            self.associated_dependencies,
            lambda r: r.referenced_identifiers(),
        )
        identifiers |= flatmap_set(
            self.associated_predicates,
            lambda a: a.referenced_identifiers(),
        )
        return identifiers


@dataclass
class WithinConstraint(Query):
    base: Query
    span: str

    def referenced_identifiers(self) -> set[query.Identifier]:
        return self.base.referenced_identifiers()


@dataclass
class Sequence(Query):
    """Class representing a sequence of queries."""

    lhs: Query
    rhs: Query
    tokens_between: bool = True

    @override
    def referenced_identifiers(self) -> set[query.Identifier]:
        return self.lhs.referenced_identifiers() | self.rhs.referenced_identifiers()


@dataclass
class Operator(Query):
    """Class representing multiple queries joined by some operator (disjunction, for example)."""

    operator: str
    queries: list[Query]

    @override
    def referenced_identifiers(self) -> set[query.Identifier]:
        return flatmap_set(self.queries, lambda q: q.referenced_identifiers())


@dataclass
class Token(Query):
    """Class representing a query for a single token."""

    identifier: query.Identifier
    # Initialize with empty set by default.
    associated_predicates: set[query.Predicate] = field(default_factory=set)
    associated_dependencies: set[query.Dependency] = field(default_factory=set)

    @override
    def referenced_identifiers(self) -> set[query.Identifier]:
        identifiers = flatmap_set(
            self.associated_dependencies, lambda r: r.referenced_identifiers()
        )
        identifiers |= flatmap_set(self.associated_predicates, lambda a: a.referenced_identifiers())
        identifiers -= {self.identifier}
        return identifiers


@dataclass
class Span(Query):
    """Class representing begin or end of a text span in the corpus."""

    span: str
    position: query.Position

    @override
    def referenced_identifiers(self) -> set[query.Identifier]:
        return set()


def add_within_and_anchors(
    translated: Query,
    original: query.Query,
    configuration: Configuration,
) -> Query:
    if configuration.span:
        span = configuration.span

        anchors = list(filter_is_instance(original.constraints, query.Constraint.Anchor))
        if anchors:
            translated = add_anchors(translated, anchors, span)

        translated = WithinConstraint(translated, span)
    return translated


def add_anchors(q: Query, anchors: Iterable[query.Constraint.Anchor], span: str) -> Query:
    has_last = any(anchor.is_last() for anchor in anchors)
    if has_last:
        q = Sequence(q, Span(span, query.Position.LAST), tokens_between=False)

    has_first = any(anchor.is_first() for anchor in anchors)
    if has_first:
        q = Sequence(Span(span, query.Position.FIRST), q, tokens_between=False)
    return q


def arrangements(
    identifiers: set[query.Identifier],
    constraints: Iterable[query.Constraint],
) -> Iterable[list[query.Identifier]]:
    """Arrange a set of Identifiers into all sequences allowed by the given Constraints"""
    cannot_be_after = {i: set() for i in identifiers}
    for constraint in constraints:
        if isinstance(constraint, query.Constraint.Order):
            fst, snd = constraint
            cannot_be_after[snd].add(fst)
        elif isinstance(constraint, query.Constraint.Anchor):
            (id,) = constraint
            other_identifiers = identifiers - set(id)
            if constraint.is_first():  # id cannot be after any of the others
                cannot_be_after[id].update(other_identifiers)
            if constraint.is_last():  # No other cannot be after id.
                for other in other_identifiers:
                    cannot_be_after[other].add(id)

    # Buffer with space for all identifiers.
    arrangement: list[query.Identifier] = [None] * len(identifiers)

    def arrange(index: int, remaining_identifiers: set[query.Identifier]):
        if index == len(arrangement):
            yield list(arrangement)  # Everything is put into an order. Yield it!
        else:
            for identifier in remaining_identifiers:
                arrangement[index] = identifier

                restricted = cannot_be_after[identifier]  # Continue for remaining identifiers.
                yield from arrange(index + 1, (remaining_identifiers - restricted) - {identifier})

    yield from arrange(0, identifiers)


class QueryFormatter(ABC):
    """
    Abstract QueryFormatter superclass, handles the following common functionality:
    1. Recursing on query components
    2. Formatting of predicates, operands and dependencies
    3. Proper parenthesis for subcomponents in Sequence and Operator

    A concrete subclass has to implement a formatting function for each concrete query type.
    """

    configuration: Configuration
    environment: Environment

    def __init__(self, configuration: Configuration, q: Query):
        self.configuration = configuration
        self.environment = associate_with_names(q.referenced_identifiers(), self.names())

    @classmethod
    def to_str(cls, q: Query, configuration: Configuration) -> str:
        return cls(configuration, q).format(q)

    @staticmethod
    def _parens_if(s: str, o: Any, cls: type | tuple) -> str:
        return f'({s})' if isinstance(o, cls) else s

    def format(self, q: query.Query) -> str:
        print('f')
        if isinstance(q, GlobalConstraint):
            base_repr = self.format(q.base)
            predicate_reprs = [self.format_predicate(p) for p in q.associated_predicates]
            dependency_reprs = [
                self.format_dependency(d.src, d.dst) for d in q.associated_dependencies
            ]
            return self.format_global_constraint(base_repr, predicate_reprs, dependency_reprs)

        elif isinstance(q, WithinConstraint):
            base_repr = self.format(q.base)
            return self.format_within_constraint(base_repr, q.span)

        elif isinstance(q, Span):
            return self.format_span(q.span, q.position)

        elif isinstance(q, Sequence):
            lhs_repr = self.format(q.lhs)
            rhs_repr = self.format(q.rhs)
            lhs_repr = self._parens_if(lhs_repr, q.lhs, Operator)
            rhs_repr = self._parens_if(rhs_repr, q.lhs, Operator)
            return self.format_sequence(lhs_repr, rhs_repr, q.tokens_between)

        elif isinstance(q, Operator):
            parts = []
            for q_ in q.queries:
                part = self.format(q_)
                part = self._parens_if(part, q_, (Token, Sequence))
                parts.append(part)
            return self.format_operator(q.operator, parts)

        elif isinstance(q, Token):
            predicates = []
            for attribute in q.associated_predicates:
                # Expand conjunction as all predicates on token are already conjunct.
                if isinstance(attribute, query.Conjunction):
                    predicates.extend(self.format_predicate(p) for p in attribute.predicates)
                else:
                    predicates.append(self.format_predicate(attribute))

            dependencies = []
            for dependency in q.associated_dependencies:
                if dependency.src == q.identifier:
                    part = self.format_dependency(dst=dependency.dst)
                else:
                    part = self.format_dependency(src=dependency.src)
                dependencies.append(part)

            return self.format_token(q.identifier, predicates, dependencies)

        raise ValueError(f'Cannot format query of type {type(q).__name__}')

    @classmethod
    @abstractmethod
    def names(cls) -> Iterable[str]: ...

    @abstractmethod
    def format_global_constraint(
        self,
        base: str,
        predicates: list[str],
        dependencies: list[str],
    ) -> str: ...

    @abstractmethod
    def format_within_constraint(
        self,
        base: str,
        span: str,
    ) -> str: ...

    @abstractmethod
    def format_operator(
        self,
        operator: str,
        queries: list[str],
    ) -> str: ...

    @abstractmethod
    def format_token(
        self,
        identifier: query.Identifier,
        predicates: list[str],
        dependencies: list[str],
    ) -> str: ...

    @abstractmethod
    def format_sequence(
        self,
        lhs: str,
        rhs: str,
        tokens_between: bool,
    ) -> str: ...

    @abstractmethod
    def format_span(
        self,
        span: str,
        position: query.Position,
    ): ...

    def format_dependency(
        self,
        src: Optional[query.Identifier] = None,
        dst: Optional[query.Identifier] = None,
    ) -> str:
        dephead = self.configuration.dephead
        ref = self.configuration.token_id

        src = self.environment[src] if src is not None else None
        dst = self.environment[dst] if dst is not None else None
        match (src, dst):
            case (None, None):
                raise ValueError('Cannot format when `src´ and `dst´ are None')
            case (src, None):
                return f'{dephead} = {src}.{ref}'
            case (None, dst):
                return f'{dst}.{dephead} = {ref}'
            case (src, dst):
                return f'{dst}.{dephead} = {src}.{ref}'

    def format_operand(self, operand: query.Operand) -> str:
        if isinstance(operand, query.Attribute):
            if operand.reference is not None:
                return f'{self.environment[operand.reference]}.{operand.attribute}'
            return operand.attribute
        elif isinstance(operand, query.Reference):
            if operand.reference is not None:
                return self.environment[operand.reference]
            return '_'
        elif isinstance(operand, query.Function):
            args = ', '.join(self.format_operand(arg) for arg in operand.args)
            return f'{operand.name}({args})'
        assert isinstance(operand, query.Literal), 'Operand must be either Attribute or Literal.'
        return operand.value

    def format_predicate(self, predicate: query.Predicate) -> str:
        if isinstance(predicate, query.Exists):
            return self.format_operand(predicate.attribute)
        elif isinstance(predicate, query.Negation):
            return f'!{self.format_predicate(predicate.predicate)}'
        if isinstance(predicate, query.Comparison):
            lhs = self.format_operand(predicate.lhs)
            rhs = self.format_operand(predicate.rhs)
            return f'({lhs} {predicate.operator} {rhs})'
        else:
            assert isinstance(predicate, (query.Conjunction, query.Disjunction))
            operators = {
                query.Conjunction: '&',
                query.Disjunction: '|',
            }
            predicates = map(self.format_predicate, predicate.predicates)
            return to_str(predicates, '(', f' {operators[type(predicate)]} ', ')')
