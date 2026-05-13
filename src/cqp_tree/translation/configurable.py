from cqp_tree.configuration import Configuration
from cqp_tree.translation.query import Attribute, Comparison, Literal, Predicate, Token


def wordform_equals(
    token: Token,
    value: str,
    is_regex: bool,
    cfg: Configuration,
) -> Predicate:
    """
    Creates a predicate to compare a tokens word form with a given value.
    """
    return Comparison(
        Attribute(token.identifier, cfg.word),
        '=',
        Literal(value, is_regex),
    )


def dependency_type_equals(
    dependant: Token,
    value: str,
    is_regex: bool,
    cfg: Configuration,
) -> Predicate:
    """
    Creates a predicate to compare a dependency relation type with a given value.
    Assumes that the dependency type information is stored on the dependant.
    """
    return Comparison(
        Attribute(dependant.identifier, cfg.dependency),
        '=',
        Literal(value, is_regex),
    )
