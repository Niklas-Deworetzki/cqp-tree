from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import count
from typing import Annotated, ClassVar, Collection, Iterable, List, Optional, Self, Set

from cqp_tree.translation.errors import NotSupported
from cqp_tree.utils import flatmap_set


class Identifier:
    _ids = count(0)

    def __init__(self):
        self.id = next(Identifier._ids)

    def __repr__(self):
        return f'Identifier({self.id})'


class Operand(ABC):
    """
    Abstract superclass for values within a Predicate.
    Is either Literal or Attribute.
    """

    @abstractmethod
    def referenced_identifiers(self) -> set[Identifier]:
        """
        Returns a set of all identifiers appearing in this Operand.
        """

    @abstractmethod
    def raise_from(self, on: Identifier) -> 'Operand':
        """
        Raise this Operand into a global context.

        This is done by explicitly introducing an identifier for "local" attributes,
        which had no identifier before.
        """

    @abstractmethod
    def lower_onto(self, on: Identifier) -> 'Operand':
        """
        Lower this Operand into a local context.

        This is done by explicitly removing identifiers to introduce "local" attributes.
        """


@dataclass(frozen=True)
class Literal(Operand):
    value: str

    def referenced_identifiers(self) -> set[Identifier]:
        return set()

    def raise_from(self, on: Identifier) -> 'Literal':
        return self

    def lower_onto(self, on: Identifier) -> 'Literal':
        return self


@dataclass(frozen=True)
class Attribute(Operand):
    reference: Optional[Identifier]
    attribute: str

    def referenced_identifiers(self) -> set[Identifier]:
        return {self.reference} if self.reference else set()

    def raise_from(self, on: Identifier) -> 'Attribute':
        if self.reference is None:
            return Attribute(on, self.attribute)
        return self

    def lower_onto(self, on: Identifier) -> 'Attribute':
        if self.reference == on:
            return Attribute(None, self.attribute)
        return self


class Predicate(ABC):
    @abstractmethod
    def referenced_identifiers(self) -> set[Identifier]: ...

    @abstractmethod
    def raise_from(self, on: Identifier) -> 'Predicate':
        """
        Raise this Predicate into a global context.
        """

    @abstractmethod
    def lower_onto(self, on: Identifier) -> 'Predicate':
        """
        Lower this Predicate into a local context.
        """

    @abstractmethod
    def normalize(self) -> 'Predicate':
        """
        Turns this Predicate into a simplified, immutable, hashable copy of itself.
        """


@dataclass(frozen=True)
class Comparison(Predicate):
    """A Predicate comparing two Operands using an arbitrary operator."""

    lhs: Operand
    operator: str
    rhs: Operand

    def referenced_identifiers(self) -> set[Identifier]:
        return flatmap_set([self.lhs, self.rhs], lambda o: o.referenced_identifiers())

    def raise_from(self, on: Identifier) -> 'Comparison':
        lhs = self.lhs.raise_from(on)
        rhs = self.rhs.raise_from(on)
        return Comparison(lhs, self.operator, rhs)

    def lower_onto(self, on: Identifier) -> 'Comparison':
        lhs = self.lhs.lower_onto(on)
        rhs = self.rhs.lower_onto(on)
        return Comparison(lhs, self.operator, rhs)

    def normalize(self) -> 'Comparison':
        return Comparison(self.lhs, self.operator, self.rhs)


@dataclass(frozen=True)
class Exists(Predicate):
    """A Predicate requiring the existence of an Attribute."""

    attribute: Attribute

    def referenced_identifiers(self) -> set[Identifier]:
        return self.attribute.referenced_identifiers()

    def raise_from(self, on: Identifier) -> 'Exists':
        return Exists(self.attribute.raise_from(on))

    def lower_onto(self, on: Identifier) -> 'Exists':
        return Exists(self.attribute.lower_onto(on))

    def normalize(self) -> 'Exists':
        return Exists(self.attribute)


@dataclass(frozen=True)
class Negation(Predicate):
    """A negated Predicate."""

    predicate: Predicate

    def referenced_identifiers(self) -> set[Identifier]:
        return self.predicate.referenced_identifiers()

    def raise_from(self, on: Identifier) -> 'Negation':
        return Negation(self.predicate.raise_from(on))

    def lower_onto(self, on: Identifier) -> 'Negation':
        return Negation(self.predicate.lower_onto(on))

    def normalize(self) -> Predicate:
        predicate = self.predicate.normalize()
        if isinstance(predicate, Negation):
            return predicate  # remove double negation.
        return Negation(predicate)


@dataclass(frozen=True)
class GenericJunction(Predicate, ABC):
    """Abstract superclass for Conjunction and Disjunction.
    Implements all their method in a generic manner."""

    predicates: Iterable[Predicate]

    def __init_subclass__(cls):
        super().__init_subclass__()
        if cls.__name__ not in {'Conjunction', 'Disjunction'}:
            raise TypeError('Only Conjunction and Disjunction are valid subclasses.')

    def __post_init__(self):
        if not self.predicates:
            raise ValueError(f'Cannot create empty {type(self).__name__}.')

    def referenced_identifiers(self) -> set[Identifier]:
        result = set()
        for predicate in self.predicates:
            result.update(predicate.referenced_identifiers())
        return result

    def _construct_instance(self, predicates: Iterable[Predicate]) -> Self:
        return self.__class__(tuple(predicates))

    def raise_from(self, on: Identifier) -> Self:
        predicates = tuple(p.raise_from(on) for p in self.predicates)
        return self._construct_instance(predicates)

    def lower_onto(self, on: Identifier) -> Self:
        predicates = tuple(p.lower_onto(on) for p in self.predicates)
        return self._construct_instance(predicates)

    def normalize(self) -> Predicate:
        normalized_predicates: List[Predicate] = []
        for predicate in self.predicates:
            normalized_predicate = predicate.normalize()
            if isinstance(normalized_predicate, self.__class__):  # unfold nested.
                normalized_predicates.extend(normalized_predicate.predicates)
            else:
                normalized_predicates.append(normalized_predicate)

        if len(normalized_predicates) == 1:  # avoid unnecessary nesting.
            return normalized_predicates[0]
        return self._construct_instance(normalized_predicates)


@dataclass(frozen=True)
class Conjunction(GenericJunction):
    """A conjunction of Predicates. See GenericJunction for implementation."""


@dataclass(frozen=True)
class Disjunction(GenericJunction):
    """A disjunction of Predicates. See GenericJunction for implementation."""


@dataclass(frozen=True)
class Dependency:
    src: Identifier
    dst: Identifier

    def referenced_identifiers(self) -> set[Identifier]:
        return {self.src, self.dst}


Distance = Annotated[int, 'How far should tokens be apart. -1 for arbitrary distance.']


@dataclass(frozen=True)
class Constraint:
    ARBITRARY_DISTANCE: ClassVar[Distance] = -1

    src: Identifier
    dst: Identifier

    enforces_order: bool = False
    distance: Distance = ARBITRARY_DISTANCE


@dataclass(frozen=True)
class Query:
    tokens: Collection[Identifier] = field(default_factory=set)
    dependencies: Collection[Dependency] = field(default_factory=set)
    constraints: Collection[Constraint] = field(default_factory=set)
    predicates: Collection[Predicate] = field(default_factory=set)
    identifier: Identifier = field(default_factory=Identifier)

    def __post_init__(self):
        defined_identifiers: Set[Identifier] = set()
        # Unlike graph-matching systems, we allow every identifier only once, as every identifier
        # is attached to a token and every token is unique.
        # The translation layer should handle unifying multiple references to the same identifier.

        for token in self.tokens:
            if token in defined_identifiers:
                # Don't report identifiers here, since they are synthetic and meaningless for users.
                raise NotSupported('Multiple tokens share the same identifier.')
            defined_identifiers.add(token)

        # Collect all identifiers referenced in query.
        referenced_identifiers = flatmap_set(self.constraints, lambda c: {c.src, c.dst})
        referenced_identifiers |= flatmap_set(
            self.dependencies,
            lambda r: r.referenced_identifiers(),
        )
        referenced_identifiers |= flatmap_set(
            self.predicates,
            lambda p: p.referenced_identifiers(),
        )
        referenced_identifiers |= flatmap_set(
            self.tokens,
            lambda t: t.attributes.referenced_identifiers() if t.attributes else set(),
        )
        if referenced_identifiers - defined_identifiers:
            raise NotSupported('Query uses identifiers not defined by tokens.')


class SetOperator(StrEnum):
    CONJUNCTION = '&'
    DISJUNCTION = '|'
    SUBTRACTION = '-'


@dataclass(frozen=True)
class Operation:
    lhs: Identifier
    operator: SetOperator
    rhs: Identifier
    identifier: Identifier = field(default_factory=Identifier)


@dataclass(frozen=True)
class ExecutionPlan:
    queries: Collection[Query]
    operations: Collection[Operation]
    goal: Identifier

    @staticmethod
    def of_query(query: Query) -> 'ExecutionPlan':
        return ExecutionPlan([query], [], query.identifier)

    class Builder:
        def __init__(self):
            self.queries = list[Query]()
            self.operations = list[Operation]()
            self.explicit_goal: Optional[Identifier] = None

        def add_query(self, query: Query) -> Identifier:
            self.queries.append(query)
            return query.identifier

        def add_operation(self, lhs: Identifier, operator: SetOperator, rhs: Identifier) -> Identifier:
            operation = Operation(lhs, operator, rhs)
            self.operations.append(operation)
            return operation.identifier

        def set_goal(self, identifier: Identifier):
            self.explicit_goal = identifier

        def build(self) -> 'ExecutionPlan':
            if not self.explicit_goal:
                if len(self.queries) == 1:
                    goal = self.queries[0].identifier
                else:
                    goal = self.operations[-1].identifier
            else:
                goal = self.explicit_goal

            return ExecutionPlan(self.queries, self.operations, goal)
