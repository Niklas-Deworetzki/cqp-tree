from cqp_tree.translation.cqp import from_query as cqp_from_query, SetOperation
from cqp_tree.translation.errors import InputError, ParsingFailed, NotSupported
from cqp_tree.translation.query import (
    Identifier,
    # Operand + subclasses
    Operand,
    Literal,
    Attribute,
    # Predicate + subclasses
    Predicate,
    Comparison,
    Exists,
    Negation,
    Conjunction,
    Disjunction,
    # Query structure
    Token,
    Dependency,
    Distance,
    Constraint,
    Query,
    # Multi-part queries
    PartType,
)
from cqp_tree.translation.registry import (
    UnableToGuessTranslatorError,
    guess_correct_translator,
    known_translators,
    translate_input,
    translator,
)
