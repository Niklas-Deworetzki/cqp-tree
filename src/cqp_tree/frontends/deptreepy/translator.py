from typing import Callable, List

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
        raise ct.ParsingFailed([error])

    def to_lisp(lisp):
        match lisp:
            case [*args]:
                return [to_lisp(arg) for arg in args]
            case tok:
                return tok

    return to_lisp(parsed[0])


@ct.translator('deptreepy')
def query_from_deptreepy(deptreepy: str) -> ct.Query:
    tokens: List[ct.Token] = []
    dependencies: List[ct.Dependency] = []

    def convert(lisp) -> ct.Identifier:
        match lisp:
            case ['TREE', *_]:
                raise ct.NotSupported('Only TREE_ is supported for matching subtrees.')

            case [singleton]:
                return convert(singleton)

            case ['TREE_', root, *dependents]:
                root_id = convert(root)
                dep_ids = [convert(dep) for dep in dependents]

                for dep_id in dep_ids:
                    dependencies.append(ct.Dependency(root_id, dep_id))

                return root_id

            case args:
                fresh_id = ct.Identifier()
                pred = convert_predicate(args)
                tokens.append(ct.Token(fresh_id, pred))
                return fresh_id

    def operation_constructor_for_field(field) -> Callable[[str], ct.Operation]:
        if not isinstance(field, str):
            raise ct.NotSupported('When matching a field, the field must be a string.')

        comparison_operator = '='
        if field.endswith('_'):
            field = field[:-1]
            comparison_operator = 'contains'

        def constructor(strpatt: str) -> ct.Operation:
            if not isinstance(strpatt, str):
                raise ct.NotSupported('When matching a field, the field value must be a string.')
            return ct.Operation(
                ct.Attribute(None, field),
                comparison_operator,
                ct.Literal(f'"{strpatt}"'),
            )

        return constructor

    def convert_predicate(lisp) -> ct.Predicate:
        match lisp:
            case [singleton]:
                return convert_predicate(singleton)

            case ['AND', *args]:
                return ct.Conjunction([convert_predicate(arg) for arg in args])

            case ['OR', *args]:
                return ct.Disjunction([convert_predicate(arg) for arg in args])

            case ['NOT', *args]:
                return ct.Negation(convert_predicate(args))

            case [field, 'IN', *strpatts]:
                ctor = operation_constructor_for_field(field)
                return ct.Disjunction([ctor(strpatt) for strpatt in strpatts])

            case [field, strpatt]:
                return operation_constructor_for_field(field)(strpatt)

            case args:
                raise ct.NotSupported(str(args))

    convert(parse(deptreepy))
    return ct.Query(tokens=tokens, dependencies=dependencies)
