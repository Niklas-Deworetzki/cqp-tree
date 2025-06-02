from typing import List

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


def query_from_deptreepy(deptreepy: str) -> ct.Query:
    tokens: List[ct.Token] = []
    dependencies: List[ct.Dependency] = []

    def convert(lisp) -> ct.Identifier:
        match lisp:
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
                return ct.Disjunction(
                    [
                        ct.Operation(
                            ct.Attribute(None, field),
                            '=',
                            ct.Literal(f'"{strpatt}"'),
                        )
                        for strpatt in strpatts
                    ]
                )

            case [field, strpatt]:
                return ct.Operation(
                    ct.Attribute(None, field),
                    '=',
                    ct.Literal(f'"{strpatt}"'),
                )

            case args:
                raise ct.NotSupported(str(args))

    convert(parse(deptreepy))
    return ct.Query(tokens=tokens, dependencies=dependencies)
