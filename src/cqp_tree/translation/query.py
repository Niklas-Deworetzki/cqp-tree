from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import count
from typing import ClassVar, Collection, Iterable, List, Optional, Self, Set, override

from cqp_tree.translation.regex import escape_regex_string
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
    """An Operand representing a literal value. It's "value" field is used without modification."""

    value: str

    def __init__(self, value: str, represents_regex: bool = False):
        """
        Construct a new Literal with the given representation.

        :param value: The string used to represent this Literal.
        :param represents_regex: If true, regular expression characters will be escaped
        (default False).
        """
        if not represents_regex:
            value = escape_regex_string(value)
        super().__setattr__('value', value)

    def referenced_identifiers(self) -> set[Identifier]:
        return set()

    def raise_from(self, on: Identifier) -> 'Literal':
        return self

    def lower_onto(self, on: Identifier) -> 'Literal':
        return self


@dataclass(frozen=True)
class Reference(Operand):
    """
    An Operand representing an Identifier.
    If constructed using None, it represents the current label.
    """

    reference: Optional[Identifier]

    def referenced_identifiers(self) -> set[Identifier]:
        if self.reference is None:
            return set()
        return {self.reference}

    def raise_from(self, on: Identifier) -> 'Operand':
        if not self.reference is None:
            return Reference(on)
        return self

    def lower_onto(self, on: Identifier) -> 'Operand':
        if self.reference == on:
            return Reference(None)
        return self


@dataclass(frozen=True)
class Function(Operand):
    """An Operand applying a builtin function."""

    name: str
    args: Iterable[Operand]

    def __init__(self, name: str, *args: Operand):
        """
        Construct a new Function, using the given name and arguments.
        """
        super().__setattr__('name', name)
        super().__setattr__('args', tuple(args))

    def referenced_identifiers(self) -> set[Identifier]:
        return flatmap_set(self.args, lambda o: o.referenced_identifiers())

    def raise_from(self, on: Identifier) -> 'Operand':
        return Function(self.name, *[arg.raise_from(on) for arg in self.args])

    def lower_onto(self, on: Identifier) -> 'Operand':
        return Function(self.name, *[arg.lower_onto(on) for arg in self.args])


@dataclass(frozen=True)
class Attribute(Operand):
    """
    An Operand representing a field on a token.
    If the token reference is None, a field on the current token is referenced.
    """

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
    """Abstract superclass for all Predicates on a token."""

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
class Token:
    identifier: Identifier = field(default_factory=Identifier)
    attributes: Optional[Predicate] = None


@dataclass(frozen=True)
class Dependency:
    src: Identifier
    dst: Identifier

    def referenced_identifiers(self) -> set[Identifier]:
        return {self.src, self.dst}


class Constraint(ABC):
    Order: ClassVar[type['Constraint']]
    Distance: ClassVar[type['Distance']]

    def referenced_identifiers(self) -> set[Identifier]:
        return set(self)

    @abstractmethod
    def __iter__(self): ...

    @staticmethod
    def order(a: Identifier, b: Identifier) -> 'Constraint':
        """
        Creates a new constraint stating that the first token must come
        before the second token in arrangements.
        :param a: Identifier of the first token.
        :param b: Identifier of the second token.
        :return: A new constraint.
        """
        return OrderConstraint(a, b)

    @staticmethod
    def distance(a: Identifier, b: Identifier):
        """
        Returns an object to encode distance constraints between two tokens.
        Distance constraints are created using comparison operators on the returned object.

        # Creates a constraint that the distance between a and b must be less than 3.
        distance(a, b) < 3

        :param a: Identifier of the first token.
        :param b: Identifier of the second token.
        :return: A new object to create distance constraints.
        """

        def make_constraint(order, dist: int) -> 'Constraint':
            return DistanceConstraint(a, b, order, dist)

        class Dist:
            def __eq__(self, other: int) -> 'Constraint':
                return make_constraint(Compare.EQ, other)

            def __ne__(self, other: int) -> 'Constraint':
                return make_constraint(Compare.NE, other)

            def __lt__(self, other: int) -> 'Constraint':
                return make_constraint(Compare.LT, other)

            def __gt__(self, other: int) -> 'Constraint':
                return make_constraint(Compare.GT, other)

            def __le__(self, other: int) -> 'Constraint':
                return self < (other + 1)

            def __ge__(self, other: int) -> 'Constraint':
                return self > (other + 1)

        return Dist()


class Compare(StrEnum):
    EQ = '='
    NE = '#'
    LT = '<'
    GT = '>'


@dataclass(frozen=True)
class DistanceConstraint(Constraint):
    a: Identifier
    b: Identifier
    order: Compare
    distance: int

    @override
    def __iter__(self):
        yield self.a
        yield self.b


Constraint.Distance = DistanceConstraint


@dataclass(frozen=True)
class OrderConstraint(Constraint):
    fst: Identifier
    snd: Identifier

    @override
    def __iter__(self):
        yield self.fst
        yield self.snd


Constraint.Order = OrderConstraint


@dataclass(frozen=True)
class Query:
    """
    A combination of tokens, dependencies, predicates and constraints.
    Optionally assigned an explicit identifier.
    """

    tokens: Collection[Token] = field(default_factory=set)
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
            # Don't report identifiers here, since they are synthetic and meaningless for users.
            assert (
                token.identifier not in defined_identifiers
            ), 'Multiple tokens share the same identifier.'
            defined_identifiers.add(token.identifier)

        # Collect all identifiers referenced in query.
        referenced_identifiers = flatmap_set(self.constraints, lambda c: c.referenced_identifiers())
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
        assert not (
            referenced_identifiers - defined_identifiers
        ), 'Query uses identifiers not defined by tokens.'


class SetOperator(StrEnum):
    CONJUNCTION = '&'
    DISJUNCTION = '|'
    SUBTRACTION = '-'


@dataclass(frozen=True)
class Operation:
    """A set operation performed on the results of two queries (or other operations)."""

    lhs: Identifier
    operator: SetOperator
    rhs: Identifier
    identifier: Identifier = field(default_factory=Identifier)


@dataclass(frozen=True)
class Recipe:
    """
    The full recipe to execute and combine a combination of Queries.
    The goal parameter determines what the recipe actually computes.

    Use the static Recipe.of_query(Query) method to construct a recipe of only one query.

    Alternatively, use the Recipe.Builder() class to construct a recipe step-by-step.
    """

    queries: Collection[Query]
    operations: Collection[Operation]
    goal: Identifier

    def __post_init__(self):
        identifiers: Set[Identifier] = set()
        for collection in [self.queries, self.operations]:
            for step in collection:
                assert (
                    step.identifier not in identifiers
                ), 'Multiple steps in recipe share the same identifier.'
                identifiers.add(step.identifier)

        for operation in self.operations:
            assert operation.lhs in identifiers, 'Step in recipe uses undefined query identifier.'
            assert operation.rhs in identifiers, 'Step in recipe uses undefined query identifier.'

    @staticmethod
    def of_query(query: Query) -> 'Recipe':
        return Recipe([query], [], query.identifier)

    def simple_representation(self) -> Optional[Query]:
        simple, *more = self.queries
        if not more and not self.operations:
            return simple
        return None

    def has_simple_representation(self) -> bool:
        return self.simple_representation() is not None

    def identifiers(self) -> Collection[Identifier]:
        query_identifiers = [query.identifier for query in self.queries]
        operation_identifiers = [operation.identifier for operation in self.operations]
        return operation_identifiers + query_identifiers

    def as_dict(self) -> dict[Identifier, Operation | Query]:
        result = {}
        for query in self.queries:
            result[query.identifier] = query
        for operation in self.operations:
            result[operation.identifier] = operation
        return result

    class Builder:
        def __init__(self):
            self.queries = list[Query]()
            self.operations = list[Operation]()
            self.explicit_goal: Optional[Identifier] = None

        def add_query(self, query: Query) -> Identifier:
            self.queries.append(query)
            return query.identifier

        def add_operation(self, lhs: Identifier, op: SetOperator, rhs: Identifier) -> Identifier:
            operation = Operation(lhs, op, rhs)
            self.operations.append(operation)
            return operation.identifier

        def set_goal(self, identifier: Identifier):
            self.explicit_goal = identifier

        def build(self) -> 'Recipe':
            if not self.explicit_goal:
                if len(self.queries) == 1:
                    goal = self.queries[0].identifier
                else:
                    goal = self.operations[-1].identifier
            else:
                goal = self.explicit_goal

            return Recipe(self.queries, self.operations, goal)
