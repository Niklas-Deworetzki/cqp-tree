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


def from_query(q: query.Query, configuration: Configuration) -> Query:
    return TRANSLATORS[configuration.dialect](q, configuration)


def format_query(q: Query, configuration: Configuration) -> str:
    return FORMATTERS[configuration.dialect].to_str(q, configuration)


Query.to_string = format_query


def format_plan(plan: query.Recipe, configuration: Configuration) -> Iterable[str]:
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
            query_text = from_query(part, configuration).to_string(configuration)
            formatted = query_text + ';'

        if include_assignment:
            formatted = f'{environment[goal]} = {formatted}'
        yield formatted

    yield from rec(plan.goal, include_assignment=False)
