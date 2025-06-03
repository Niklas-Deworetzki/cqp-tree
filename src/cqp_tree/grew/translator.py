from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, List, override

from antlr4 import CommonTokenStream, InputStream, TerminalNode
from antlr4.error.ErrorListener import ErrorListener

import cqp_tree.translation as ct
from .antlr import GrewLexer, GrewParser


@dataclass
class ParseErrorListener(ErrorListener):
    errors: List[ct.InputError] = field(default_factory=list)

    @override
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(ct.InputError(f'{line}, {column}', msg))


def parse(query: str) -> GrewParser.RequestContext:
    listener = ParseErrorListener()

    lexer = GrewLexer(InputStream(query))
    stream = CommonTokenStream(lexer)
    parser = GrewParser(stream)

    for antlr in [lexer, parser]:
        antlr.removeErrorListeners()
        antlr.addErrorListener(listener)

    result = parser.request()
    if listener.errors:
        raise ct.ParsingFailed(listener.errors)

    return result


Environment = defaultdict[str, ct.Identifier]


def new_environment() -> Environment:
    return defaultdict(ct.Identifier)


def query_from_grew(grew: str) -> ct.Query:
    grew_request = parse(grew)
    builder = QueryBuilder()
    builder.translate_request(grew_request)
    return builder.build()


class QueryBuilder:

    def __init__(self):
        self.tokens: list[ct.Token] = []
        self.dependencies: list[ct.Dependency] = []
        self.constraints: list[ct.Constraint] = []
        self.predicates: list[ct.Predicate] = []

    def build(self):
        return ct.Query(
            self.tokens,
            self.dependencies,
            self.constraints,
            self.predicates,
        )

    def translate_request(self, request: GrewParser.RequestContext):
        environment = new_environment()

        for clause in request.pattern().body().clause():
            self.translate_clause(environment, clause)

        for _ in request.requestItem():
            raise ct.NotSupported('Only "pattern" is supported as a query so far.')

    @staticmethod
    def string_of_token(token: TerminalNode) -> str:
        return token.symbol.text

    @staticmethod
    def to_cqp_operator(grew: GrewParser.CompareContext) -> str:
        if isinstance(grew, GrewParser.EqualityContext):
            return '='

        if isinstance(grew, GrewParser.InequalityContext):
            return '!='

        assert False, f'Unknown operator: {type(grew)}'

    @staticmethod
    def wrap(
        predicates: List[ct.Predicate], ctor: Callable[[List[ct.Predicate]], ct.Predicate]
    ) -> ct.Predicate:
        if len(predicates) > 1:
            return ctor(predicates)
        return predicates[0]

    def translate_clause(self, environment: Environment, clause: GrewParser.ClauseContext):
        if isinstance(clause, GrewParser.NodeClauseContext):
            identifier = environment[clause.label.text]
            features = [
                translated_predicate
                for fs in clause.featureStructure()
                if (translated_predicate := self.to_predicate(environment, fs))
            ]
            # Only has empty feature structure.
            if not features:
                token = ct.Token(identifier)
            else:
                token = ct.Token(identifier, self.wrap(features, ct.Disjunction))

            self.tokens.append(token)

        elif isinstance(clause, GrewParser.EdgeClauseContext):
            src = environment[clause.src.text]
            dst = environment[clause.dst.text]

            dependency = ct.Dependency(src, dst)
            self.dependencies.append(dependency)

            arrow = clause.arrow()
            if isinstance(arrow, GrewParser.SimpleArrowContext):
                return  # No dependency types specified. Nothing else to do.

            deprel = ct.Attribute(dst, 'deprel')
            deptypes = [self.to_operand(environment, dt) for dt in arrow.edgeTypes().literal()]
            if isinstance(arrow, GrewParser.PositiveArrowContext):
                dependency_constraint = self.wrap(
                    [ct.Operation(deprel, '=', deptype) for deptype in deptypes],
                    ct.Disjunction,
                )

            elif isinstance(arrow, GrewParser.NegatedArrowContext):
                dependency_constraint = self.wrap(
                    [ct.Operation(deprel, '!=', deptype) for deptype in deptypes],
                    ct.Conjunction,
                )

            else:
                raise ct.NotSupported(f'Unknown arrow type: {type(arrow)}')

            self.predicates.append(dependency_constraint)

        elif isinstance(clause, GrewParser.ConstraintClauseContext):
            lhs = self.to_operand(environment, clause.lhs)
            rhs = self.to_operand(environment, clause.rhs)
            predicate = ct.Operation(
                lhs,
                self.to_cqp_operator(clause.compare()),
                rhs,
            )

            self.predicates.append(predicate)

        elif isinstance(clause, GrewParser.OrderClauseContext):
            if isinstance(clause.order(), GrewParser.ImmediatePrecedenceContext):
                distance = 0
            else:
                distance = ct.Constraint.ARBITRARY_DISTANCE

            lhs = environment[self.string_of_token(clause.lhs)]
            rhs = environment[self.string_of_token(clause.rhs)]

            self.constraints.append(ct.Constraint(lhs, rhs, enforces_order=True, distance=distance))

    def to_predicate(
        self,
        environment: Environment,
        grew: GrewParser.FeatureContext | GrewParser.FeatureStructureContext,
    ) -> ct.Predicate | None:
        # Checking for existence of feature: Tense
        if isinstance(grew, GrewParser.PresenceContext):
            attribute_name = self.string_of_token(grew.Identifier())
            return ct.Exists(ct.Attribute(None, attribute_name))

        # Checking for absence of feature: !Tense
        if isinstance(grew, GrewParser.AbsenceContext):
            attribute_name = self.string_of_token(grew.Identifier())
            return ct.Negation(ct.Exists(ct.Attribute(None, attribute_name)))

        # Requirement of feature to be certain value: Tense <> A|B|C
        if isinstance(grew, GrewParser.RequiresContext):
            attribute_name = self.string_of_token(grew.Identifier())
            attribute = ct.Attribute(None, attribute_name)

            alternatives = [
                self.to_operand(environment, feature) for feature in grew.featureValue()
            ]
            comparison = grew.compare()
            if isinstance(comparison, GrewParser.EqualityContext):
                return self.wrap(
                    [ct.Operation(attribute, '=', alt) for alt in alternatives],
                    ct.Disjunction,
                )

            if isinstance(comparison, GrewParser.InequalityContext):
                return self.wrap(
                    [ct.Operation(attribute, '!=', alt) for alt in alternatives],
                    ct.Conjunction,
                )

            raise ct.NotSupported(f'Unknown comparison type: {type(comparison)}')

        # Translate entire feature structure: [Tense, !Number, lemma = re"a.*"]
        if isinstance(grew, GrewParser.FeatureStructureContext):
            if not grew.feature():
                return None

            features = [self.to_predicate(environment, feature) for feature in grew.feature()]
            return self.wrap(features, ct.Conjunction)

        assert False, f'Unknown predicate: {type(grew)}'

    def to_operand(
        self,
        environment: Environment,
        grew: GrewParser.LiteralContext | GrewParser.FeatureValueContext,
    ) -> ct.Operand:
        # Proper string like: "aßσþ"
        if isinstance(grew, GrewParser.UnicodeStringContext):
            text = self.string_of_token(grew.String())
            return ct.Literal(text)

        # Identifier used as simple string: Tense
        if isinstance(grew, GrewParser.SimpleStringContext):
            text = self.string_of_token(grew.Identifier())
            return ct.Literal(f'"{text}"')

        # Regular expression: re"a.*"
        if isinstance(grew, GrewParser.RegexContext):
            text = self.string_of_token(grew.String())
            return ct.Literal(text)

        # PCRE expression: /a.*/i
        if isinstance(grew, GrewParser.PCREContext):
            raise ct.NotSupported('PCRE expressions are not yet supported.')

        # Attribute of another token: X.upos
        if isinstance(grew, GrewParser.AttributeContext):
            instance = self.string_of_token(grew.Identifier(0))
            attribute_name = self.string_of_token(grew.Identifier(1))
            return ct.Attribute(environment[instance], attribute_name)

        # Literal used as part of feature structure, covered by other cases.
        if isinstance(grew, GrewParser.ValueContext):
            return self.to_operand(environment, grew.literal())

        assert False, f'Unknown operand: {type(grew)}'
