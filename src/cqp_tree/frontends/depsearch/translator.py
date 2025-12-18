from typing import Callable

import cqp_tree.translation as ct
from cqp_tree.frontends.antlr_utils import make_parse
from cqp_tree.frontends.depsearch.antlr import DepsearchLexer, DepsearchParser as Depsearch


parse: Callable[[str], Depsearch.QueryContext] = make_parse(
    DepsearchLexer, Depsearch, Depsearch.query
)


@ct.translator('depsearch')
def translate_depsearch(depsearch: str) -> ct.QueryPlan:
    parsed = parse(depsearch)
    ...

