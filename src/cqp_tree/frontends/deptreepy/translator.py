from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional, Self, Type, override

from pyparsing import ParseException, nestedExpr

import cqp_tree.translation as ct


def parse(s: str):
    # Parsing adapted from:
    # https://github.com/aarneranta/deptreepy/blob/a3fd7aa0b01f169afe6f37277d8bc2c624bcb433/patterns.py#L334
    if not s.startswith('('):  # add outer parentheses if missing
        s = '(' + s + ')'
    try:
        parsed = nestedExpr().parseString(s)
    except ParseException as ex:
        error = ct.InputError(f'line: {ex.line}, col: {ex.col}', ex.msg)
        raise ct.ParsingFailed(error)

    def to_lisp(lisp):
        match lisp:
            case [*args]:
                return [to_lisp(arg) for arg in args]
            case tok:
                return tok

    return to_lisp(parsed[0])


class Result(ABC):

    @abstractmethod
    def as_query(self, builder: ct.Recipe.Builder) -> 'Query': ...

    @abstractmethod
    def as_dependency_constraint(self) -> 'DependencyConstraint': ...


@dataclass
class Query(Result):
    identifier: ct.Identifier

    @override
    def as_query(self, builder: ct.Recipe.Builder) -> Self:
        return self

    @override
    def as_dependency_constraint(self) -> 'DependencyConstraint':
        raise ct.NotSupported('This operation does not support ')


class DependencyConstraint(Result):
    root: ct.Token

    tokens: List[ct.Token]
    dependencies: List[ct.Dependency]

    def __init__(self, token: ct.Token):
        self.root = token
        self.tokens = [token]
        self.dependencies = []

    def add_edge_to(self, target: Result):
        constraint = target.as_dependency_constraint()

        dependency = ct.Dependency(
            src=self.root.identifier,
            dst=constraint.root.identifier,
        )
        self.dependencies.append(dependency)

        self.tokens += constraint.tokens
        self.dependencies += constraint.dependencies

    @override
    def as_query(self, builder: ct.Recipe.Builder) -> Query:
        query = ct.Query(tokens=self.tokens, dependencies=self.dependencies)
        return Query(builder.add_query(query))

    @override
    def as_dependency_constraint(self) -> Self:
        return self


@dataclass
class TokenConstraint(Result):
    predicate: Optional[ct.Predicate]

    @override
    def as_query(self, builder: ct.Recipe.Builder) -> Query:
        return self.as_dependency_constraint().as_query(builder)

    @override
    def as_dependency_constraint(self) -> DependencyConstraint:
        token = ct.Token(attributes=self.predicate)
        return DependencyConstraint(token)


def operation_constructor_for_field(field) -> Callable[[str], ct.Comparison]:
    if not isinstance(field, str):
        raise ct.NotSupported('When matching a field, the field must be a string.')

    comparison_operator = '='
    if field.endswith('_'):
        field = field[:-1]
        comparison_operator = 'contains'

    def constructor(strpatt) -> ct.Comparison:
        if not isinstance(strpatt, str):
            raise ct.NotSupported('When matching a field, the field value must be a string.')
        return ct.Comparison(
            ct.Attribute(None, field),
            comparison_operator,
            ct.Literal(f'"{strpatt}"', represents_regex=True),
        )

    return constructor


@ct.translator('deptreepy')
def translate_deptreepy(deptreepy: str) -> ct.Recipe:
    builder = ct.Recipe.Builder()

    def combine_operation(
        parts: List[Query | DependencyConstraint | TokenConstraint],
        ctor: Type[ct.Conjunction | ct.Disjunction],
        operator: ct.SetOperator,
    ) -> TokenConstraint | Query:
        if all(isinstance(part, TokenConstraint) for part in parts):
            conjuncts = [part.predicate for part in parts if part.predicate]
            pred = ctor(conjuncts)
            return TokenConstraint(predicate=pred)

        else:
            # Promote to queries
            parts = [part.as_query(builder).identifier for part in parts]

            res, *others = parts
            for conj in others:
                res = builder.add_operation(res, operator, conj)
            return Query(res)

    # we want to return here for every possible operator
    # pylint: disable=too-many-return-statements
    def convert(lisp) -> TokenConstraint | DependencyConstraint | Query:
        match lisp:
            case ['TREE', *_]:
                raise ct.NotSupported('Only TREE_ is supported for matching subtrees.')

            case [singleton]:
                return convert(singleton)

            case ['TREE_', *args]:
                if not args:
                    raise ct.NotSupported('TREE_ requires at least 1 argument, got 0.')
                root, *dependents = args

                # TODO: Does this handle nested TREE_ correctly?
                constraint = convert(root).as_dependency_constraint()
                for dep in dependents:
                    constraint.add_edge_to(convert(dep))

                return constraint

            case ['AND', *args]:
                conjuncts = [convert(arg) for arg in args]
                if not conjuncts:  # AND without any predicates will match every token.
                    return TokenConstraint(predicate=None)

                return combine_operation(conjuncts, ct.Conjunction, ct.SetOperator.CONJUNCTION)

            case ['OR', *args]:
                disjuncts = [convert(arg) for arg in args]
                if not disjuncts:
                    raise ct.NotSupported('Empty OR matches no token. This is not supported.')

                return combine_operation(disjuncts, ct.Disjunction, ct.SetOperator.DISJUNCTION)

            case ['NOT', *args]:
                arg, *more = args
                if more:
                    raise ct.NotSupported(f'NOT requires exactly 1 argument, got {len(more) + 1}.')

                negated = convert(arg)
                if not isinstance(negated, TokenConstraint):
                    # TODO: The best way to handle this might be a flag for negated Query instances.
                    # AND containing NOT can then be implemented as subtraction.
                    # NOT in OR / as root will be expensive, querying entire corpus and subtracting.
                    raise ct.NotSupported(
                        'Searching for the absence of dependencies using NOT is not yet supported.'
                    )

                predicate = ct.Negation(negated.predicate)
                return TokenConstraint(predicate=predicate)

            case [field, 'IN', *strpatts]:
                ctor = operation_constructor_for_field(field)
                pred = ct.Disjunction([ctor(strpatt) for strpatt in strpatts])
                return TokenConstraint(predicate=pred)

            case [field, strpatt]:
                pred = operation_constructor_for_field(field)(strpatt)
                return TokenConstraint(predicate=pred)

            case unsupported:
                raise ct.NotSupported(f'Encountered unsupported expression: {unsupported}')

    result = convert(parse(deptreepy))
    if isinstance(result, TokenConstraint):
        result = result.as_dependency_constraint()
    if isinstance(result, DependencyConstraint):
        result = result.as_query(builder)

    builder.set_goal(result.identifier)
    return builder.build()
