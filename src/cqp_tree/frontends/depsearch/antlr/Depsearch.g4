grammar Depsearch;


query : allQuantified? tokenExpression ('+' tokenExpression)* EOF ;

allQuantified
    : atomicToken '->'
    ;

tokenExpression
    : lhs=tokenExpression '&' rhs=tokenExpression                       # ConjunctionToken
    | lhs=tokenExpression '|' rhs=tokenExpression                       # DisjunctionToken
    | lhs=atomicToken '.' rhs=atomicToken                               # SequenceToken
    | lhs=atomicToken LinearDistance directionModifier? rhs=atomicToken # DistanceToken
    // t1 > t2 > t3 means t2 and t3 are dependents of t1
    // t1 > (t2 > t3) searches for chains instead.
    | src=negatedToken (dependencyDescription)+                         # DependenciesToken
    | negatedToken                                                      # PossiblyNegatedToken
    ;

negatedToken : Neg exp=atomicToken  # NegationToken
             | atomicToken          # JustAToken
             ;

atomicToken : '(' exp=tokenExpression ')'   # ParenthesizedToken
            | '_'                           # ArbitraryToken
            | Value '=' Value               # AttributeToken
            | Value                         # WordOrTagToken
            | String                        # WordformToken
            ;

dependencyDescription : dependencyExpression dst=negatedToken
                      ;

// one can use OR operator to query dependency relations
dependencyExpression : lhs=dependencyExpression '|' rhs=dependencyExpression # DisjunctionDependency
                     | Neg atomicDependency                                  # NegationDependency
                     | atomicDependency                                      # JustADependency
                     ;

atomicDependency  : '(' dependencyExpression ')'                                    # ParenthesizedDependency
                  | dependencyOperator (negatedType=Neg? Value)? directionModifier? # Dependency
                  ;




dependencyOperator  : '<'   # Governs
                    | '>'   # GovernedBy
                    ;


directionModifier   : '@L'  # LeftOf
                    | '@R'  # RightOf
                    ;

LinearDistance      : '<lin' '_' [0-9]+ ':' [0-9]+
                    ;

Neg    : '!' ;

WhiteSpace  : [ \t\n\r\f]+ -> skip;

Value  : ~[\t\n\r\f !|&@=<>(){}]+
       ;

String : '"' (~[\\"] | '\\' .)* '"';
