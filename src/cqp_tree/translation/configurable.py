from cqp_tree.configuration import Configuration
from cqp_tree.translation.query import Attribute, Comparison, Identifier, Operand, Predicate, Token


def wordform_equals(
    token: Identifier | Token,
    value: Operand,
    cfg: Configuration,
) -> Predicate:
    """
    Creates a predicate to compare a tokens word form with a given value.
    """
    return Comparison(
        Attribute(_to_identifier(token), cfg.word),
        '=',
        value,
    )


def dependency_type_equals(
    dependant: Identifier | Token,
    value: Operand,
    cfg: Configuration,
) -> Predicate:
    """
    Creates a predicate to compare a dependency relation type with a given value.
    Assumes that the dependency type information is stored on the dependant.
    """
    return Comparison(
        Attribute(_to_identifier(dependant), cfg.dependency),
        '=',
        value,
    )


def _to_identifier(token_or_identifier: Token | Identifier) -> Identifier:
    if isinstance(token_or_identifier, Token):
        return token_or_identifier.identifier
    return token_or_identifier
