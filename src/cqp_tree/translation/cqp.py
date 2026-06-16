from enum import StrEnum
from typing import Callable, Iterable

from cqp_tree.configuration import Configuration
from cqp_tree.translation import query
from cqp_tree.translation.backends.sketch_engine import (
    SketchEngineFormatter,
    sketchengine_from_query,
)
from cqp_tree.translation.backends.common import Query, QueryFormatter
from cqp_tree.translation.backends.cwb import CwbFormatter, cwb_from_query
from cqp_tree.utils import (
    UPPERCASE_ALPHABET,
    associate_with_names,
)

QUERY_ALPHABET = UPPERCASE_ALPHABET

CQP_OPERATIONS = {
    query.SetOperator.CONJUNCTION: 'intersect',
    query.SetOperator.DISJUNCTION: 'union',
    query.SetOperator.SUBTRACTION: 'diff',
}


class CQPDialect(StrEnum):
    """Supported CQP dialects."""

    CWB = 'Corpus Workbench'
    SKETCH_ENGINE = 'Sketch Engine'


TRANSLATORS: dict[CQPDialect, Callable[[query.Query, Configuration], Query]] = {
    CQPDialect.CWB: cwb_from_query,
    CQPDialect.SKETCH_ENGINE: sketchengine_from_query,
}

FORMATTERS: dict[CQPDialect, type[QueryFormatter]] = {
    CQPDialect.CWB: CwbFormatter,
    CQPDialect.SKETCH_ENGINE: SketchEngineFormatter,
}


def parsed_to_cqp(q: query.Query, configuration: Configuration) -> Query:
    """Convert a parsed query from a frontend into CQP."""
    return TRANSLATORS[configuration.dialect](q, configuration)


def format_query(q: Query, configuration: Configuration) -> str:
    """Format a query into string representation given a configuration."""
    return FORMATTERS[configuration.dialect].to_str(q, configuration)


Query.to_string = format_query


def format_recipe(plan: query.Recipe, configuration: Configuration) -> Iterable[str]:
    """
    Format a parsed recipe into an iterator of strings,
    each of which represents one query of the recipe.

    The order in which strings are produced by this function respects dependencies
    between queries.
    """
    environment = associate_with_names(plan.identifiers(), QUERY_ALPHABET)
    parts = plan.as_dict()

    def rec(goal: query.Identifier, include_assignment: bool = True) -> Iterable[str]:
        part = parts[goal]
        if isinstance(part, query.Operation):
            op, lhs, rhs = (
                CQP_OPERATIONS[part.operator],
                environment[part.lhs],
                environment[part.rhs],
            )
            formatted = f'{op} {lhs} {rhs};'
            yield from rec(part.lhs)
            yield from rec(part.rhs)
        else:
            query_text = parsed_to_cqp(part, configuration).to_string(configuration)
            formatted = query_text + ';'

        if include_assignment:
            formatted = f'{environment[goal]} = {formatted}'
        yield formatted

    yield from rec(plan.goal, include_assignment=False)
