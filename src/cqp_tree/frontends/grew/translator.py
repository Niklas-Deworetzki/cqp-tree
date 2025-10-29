from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Self, Type, override

from antlr4 import CommonTokenStream, InputStream, TerminalNode
from antlr4.error.ErrorListener import ErrorListener

import cqp_tree.translation as ct
from cqp_tree.frontends.grew.antlr import GrewLexer, GrewParser


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
        raise ct.ParsingFailed(*listener.errors)

    return result


Environment = defaultdict[str, ct.Token]


def new_environment() -> Environment:
    return defaultdict(ct.Token)


@ct.translator('grew')
def translate_grew(grew: str) -> ct.Recipe:
    grew_request = parse(grew)
    return QueryBuilder().build(grew_request)


class QueryBuilder:

    def __init__(self, inherited: 'QueryBuilder' = None):
        self.dependencies = list[ct.Dependency]()
        self.constraints = list[ct.Constraint]()
        self.predicates = list[ct.Predicate]()

        self.environment = new_environment()

        if inherited:
            self.dependencies += inherited.dependencies
            self.constraints += inherited.constraints
            self.predicates += inherited.predicates

            for key, value in inherited.environment.items():
                # We never put attributes on tokens, so we are safe to copy references here.
                self.environment[key] = value

    def is_empty(self):
        return not self.environment

    def build_query(self) -> ct.Query:
        return ct.Query(
            tokens=self.environment.values(),
            dependencies=self.dependencies,
            constraints=self.constraints,
            predicates=self.predicates,
        )

    @staticmethod
    def query_operator(
        item: GrewParser.WithItemContext | GrewParser.WithoutItemContext,
    ) -> ct.SetOperator:
        return {
            GrewParser.WithItemContext: ct.SetOperator.CONJUNCTION,
            GrewParser.WithoutItemContext: ct.SetOperator.SUBTRACTION,
        }[type(item)]

    @staticmethod
    def build(request: GrewParser.RequestContext) -> ct.Recipe:
        plan = ct.Recipe.Builder()

        pattern = request.pattern().body()
        root_builder = QueryBuilder().translate_clauses(pattern)
        if root_builder.is_empty():
            # If pattern is empty, match an arbitrary token.
            query = ct.Query(tokens=[ct.Token()])
        else:
            query = root_builder.build_query()

        current = plan.add_query(query)
        goal = current

        for item in request.requestItem():
            builder = QueryBuilder(root_builder).translate_clauses(item.body())
            current = plan.add_query(builder.build_query())

            goal = plan.add_operation(goal, QueryBuilder.query_operator(item), current)

        plan.set_goal(goal)
        return plan.build()

    def translate_clauses(self, clauses: GrewParser.BodyContext) -> Self:
        for clause in clauses.clause():
            self.translate_clause(clause)
        return self

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
        predicates: List[ct.Predicate], ctor: Type[ct.Conjunction | ct.Disjunction]
    ) -> ct.Predicate:
        if len(predicates) > 1:
            return ctor(predicates)
        return predicates[0]

    def translate_clause(self, clause: GrewParser.ClauseContext):
        if isinstance(clause, GrewParser.NodeClauseContext):
            token = self.environment[clause.label.text]
            features = [
                translated_predicate.raise_from(token.identifier)
                for fs in clause.featureStructure()
                if (translated_predicate := self.to_predicate(fs))
            ]

            # Only add predicate if features are present.
            if features:
                predicate = self.wrap(features, ct.Disjunction)
                predicate.raise_from(token.identifier)
                self.predicates.append(predicate)

        elif isinstance(clause, GrewParser.EdgeClauseContext):
            src = self.environment[clause.src.text].identifier
            dst = self.environment[clause.dst.text].identifier

            dependency = ct.Dependency(src, dst)
            self.dependencies.append(dependency)

            arrow = clause.arrow()
            if isinstance(arrow, GrewParser.SimpleArrowContext):
                return  # No dependency types specified. Nothing else to do.

            deprel = ct.Attribute(dst, 'deprel')
            deptypes = [self.to_operand(dt) for dt in arrow.edgeTypes().literal()]
            if isinstance(arrow, GrewParser.PositiveArrowContext):
                dependency_constraint = self.wrap(
                    [ct.Comparison(deprel, '=', deptype) for deptype in deptypes],
                    ct.Disjunction,
                )

            elif isinstance(arrow, GrewParser.NegatedArrowContext):
                dependency_constraint = self.wrap(
                    [ct.Comparison(deprel, '!=', deptype) for deptype in deptypes],
                    ct.Conjunction,
                )

            else:
                raise ct.NotSupported(f'Unknown arrow type: {type(arrow)}')

            self.predicates.append(dependency_constraint)

        elif isinstance(clause, GrewParser.ConstraintClauseContext):
            lhs = self.to_operand(clause.lhs)
            rhs = self.to_operand(clause.rhs)
            predicate = ct.Comparison(
                lhs,
                self.to_cqp_operator(clause.compare()),
                rhs,
            )

            self.predicates.append(predicate)

        elif isinstance(clause, GrewParser.OrderClauseContext):
            lhs = self.environment[clause.lhs.text].identifier
            rhs = self.environment[clause.rhs.text].identifier

            self.constraints.append(ct.Constraint.order(lhs, rhs))
            if isinstance(clause.order(), GrewParser.ImmediatePrecedenceContext):
                self.constraints.append(ct.Constraint.distance(lhs, rhs) == 1)

    def to_predicate(
        self,
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

            alternatives = [self.to_operand(feature) for feature in grew.featureValue()]
            comparison = grew.compare()
            if isinstance(comparison, GrewParser.EqualityContext):
                return self.wrap(
                    [ct.Comparison(attribute, '=', alt) for alt in alternatives],
                    ct.Disjunction,
                )

            if isinstance(comparison, GrewParser.InequalityContext):
                return self.wrap(
                    [ct.Comparison(attribute, '!=', alt) for alt in alternatives],
                    ct.Conjunction,
                )

            raise ct.NotSupported(f'Unknown comparison type: {type(comparison)}')

        # Translate entire feature structure: [Tense, !Number, lemma = re"a.*"]
        if isinstance(grew, GrewParser.FeatureStructureContext):
            if not grew.feature():
                return None

            features = [self.to_predicate(feature) for feature in grew.feature()]
            return self.wrap(features, ct.Conjunction)

        assert False, f'Unknown predicate: {type(grew)}'

    def to_operand(
        self,
        grew: GrewParser.LiteralContext | GrewParser.FeatureValueContext,
    ) -> ct.Operand:
        # Proper string like: "aßσþ"
        if isinstance(grew, GrewParser.UnicodeStringContext):
            text = self.string_of_token(grew.String())
            return ct.Literal(text)

        # Dependency type with subtype: nsubj:pass
        if isinstance(grew, GrewParser.SubtypeContext):
            sup = self.string_of_token(grew.Identifier(0))
            sub = self.string_of_token(grew.Identifier(1))
            return ct.Literal(f'"{sup}:{sub}"')

        # Identifier used as simple string: Tense
        if isinstance(grew, GrewParser.SimpleStringContext):
            text = self.string_of_token(grew.Identifier())
            return ct.Literal(f'"{text}"')

        # Regular expression: re"a.*"
        if isinstance(grew, GrewParser.RegexContext):
            text = self.string_of_token(grew.String())
            return ct.Literal(text, represents_regex=True)

        # PCRE expression: /a.*/i
        if isinstance(grew, GrewParser.PCREContext):
            raise ct.NotSupported('PCRE expressions are not yet supported.')

        # Attribute of another token: X.upos
        if isinstance(grew, GrewParser.AttributeContext):
            instance = self.string_of_token(grew.Identifier(0))
            attribute_name = self.string_of_token(grew.Identifier(1))
            return ct.Attribute(self.environment[instance].identifier, attribute_name)

        # Literal used as part of feature structure, covered by other cases.
        if isinstance(grew, GrewParser.ValueContext):
            return self.to_operand(grew.literal())

        assert False, f'Unknown operand: {type(grew)}'
