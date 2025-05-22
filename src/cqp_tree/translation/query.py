from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from itertools import count
from typing import Annotated, ClassVar, Optional, Set, Iterable

from cqp_tree.utils import flatmap_set


class Identifier:
    _ids = count(0)

    def __init__(self):
        self.id = next(self._ids)

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
class Expression(Predicate):
    lhs: Operand
    operator: str
    rhs: Operand

    def referenced_identifiers(self) -> set[Identifier]:
        return flatmap_set([self.lhs, self.rhs], lambda o: o.referenced_identifiers())

    def raise_from(self, on: Identifier) -> 'Expression':
        lhs = self.lhs.raise_from(on)
        rhs = self.rhs.raise_from(on)
        return Expression(lhs, self.operator, rhs)

    def lower_onto(self, on: Identifier) -> 'Expression':
        lhs = self.lhs.lower_onto(on)
        rhs = self.rhs.lower_onto(on)
        return Expression(lhs, self.operator, rhs)

    def normalize(self) -> 'Expression':
        return Expression(self.lhs, self.operator, self.rhs)


@dataclass(frozen=True)
class Exists(Predicate):
    attribute: Attribute

    def referenced_identifiers(self) -> set[Identifier]:
        return self.attribute.referenced_identifiers()

    def raise_from(self, on: Identifier) -> 'Predicate':
        return Exists(self.attribute.raise_from(on))

    def lower_onto(self, on: Identifier) -> 'Predicate':
        return Exists(self.attribute.lower_onto(on))

    def normalize(self) -> 'Predicate':
        return Exists(self.attribute)


@dataclass(frozen=True)
class Negation(Predicate):
    predicate: Predicate

    def referenced_identifiers(self) -> set[Identifier]:
        return self.predicate.referenced_identifiers()

    def raise_from(self, on: Identifier) -> 'Negation':
        return Negation(self.predicate.raise_from(on))

    def lower_onto(self, on: Identifier) -> 'Negation':
        return Negation(self.predicate.lower_onto(on))

    def normalize(self) -> 'Negation':
        return Negation(self.predicate.normalize())


@dataclass(frozen=True)
class Conjunction(Predicate):
    predicates: Iterable[Predicate]

    def __post_init__(self):
        if not self.predicates:
            raise ValueError('Cannot create empty conjunction.')

    def referenced_identifiers(self) -> set[Identifier]:
        result = set()
        for predicate in self.predicates:
            result.update(predicate.referenced_identifiers())
        return result

    def raise_from(self, on: Identifier) -> 'Conjunction':
        predicates = tuple(p.raise_from(on) for p in self.predicates)
        return Conjunction(predicates)

    def lower_onto(self, on: Identifier) -> 'Conjunction':
        predicates = tuple(p.lower_onto(on) for p in self.predicates)
        return Conjunction(predicates)

    def normalize(self) -> 'Conjunction':
        predicates = tuple(p.normalize() for p in self.predicates)
        return Conjunction(predicates)


@dataclass(frozen=True)
class Disjunction(Predicate):
    predicates: Iterable[Predicate]

    def __post_init__(self):
        if not self.predicates:
            raise ValueError('Cannot create empty disjunction.')

    def referenced_identifiers(self) -> set[Identifier]:
        result = set()
        for predicate in self.predicates:
            result.update(predicate.referenced_identifiers())
        return result

    def raise_from(self, on: Identifier) -> 'Disjunction':
        predicates = tuple(p.raise_from(on) for p in self.predicates)
        return Disjunction(predicates)

    def lower_onto(self, on: Identifier) -> 'Disjunction':
        predicates = tuple(p.lower_onto(on) for p in self.predicates)
        return Disjunction(predicates)

    def normalize(self) -> 'Disjunction':
        predicates = tuple(p.normalize() for p in self.predicates)
        return Disjunction(predicates)


@dataclass(frozen=True)
class Token:
    identifier: Identifier
    attributes: Optional[Predicate] = None


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
    tokens: Iterable[Token] = field(default_factory=set)
    dependencies: Iterable[Dependency] = field(default_factory=set)
    constraints: Iterable[Constraint] = field(default_factory=set)
    predicates: Iterable[Predicate] = field(default_factory=set)

    def __post_init__(self):
        defined_identifiers: Set[Identifier] = set()

        for token in self.tokens:
            if token.identifier in defined_identifiers:
                raise ValueError('Multiple tokens share the same identifier.')
            defined_identifiers.add(token.identifier)

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
            raise ValueError('Query uses identifiers not defined by tokens.')
