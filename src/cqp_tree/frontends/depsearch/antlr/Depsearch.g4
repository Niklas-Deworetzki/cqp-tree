grammar Depsearch;


query : allQuantified? tokenExpression ('+' tokenExpression)* EOF ;

allQuantified
    : atomicToken '->'
    ;

tokenExpression
    : lhs=tokenExpression '&' rhs=tokenExpression                       # ConjunctionToken
    | lhs=tokenExpression '|' rhs=tokenExpression                       # DisjunctionToken
    // TODO: How does sequencing associate?
    | lhs=atomicToken '.' rhs=atomicToken                               # SequenceToken
    | lhs=atomicToken LinearDistance directionModifier? rhs=atomicToken # DistanceToken
    // t1 > t2 > t3 means t2 and t3 are dependents of t1
    // t1 > (t2 > t3) searches for chains instead.
    | src=negatedToken (dependencyDescription)+                         # DependenciesToken
    | exp=negatedToken                                                  # PossiblyNegatedToken
    ;

negatedToken : Neg exp=atomicToken  # NegationToken
             | exp=atomicToken      # JustAToken
             ;

atomicToken : '(' exp=tokenExpression ')'   # ParenthesizedToken
            | '_'                           # ArbitraryToken
            | key=Value '=' value=Value     # AttributeToken
            | Value                         # WordOrTagToken
            | String                        # WordformToken
            ;

dependencyDescription : dependencyExpression dst=negatedToken
                      ;

// one can use OR operator to query dependency relations
dependencyExpression : lhs=dependencyExpression '|' rhs=dependencyExpression # DisjunctionDependency
                     | Neg atomicDependency                                  # NegationDependency
                     | exp=atomicDependency                                  # JustADependency
                     ;

atomicDependency  : '(' exp=dependencyExpression ')'                                # ParenthesizedDependency
                  | dependencyOperator (negatedType=Neg? Value)? directionModifier? # Dependency
                  ;




dependencyOperator  : '<'   # Governs
                    | '>'   # GovernedBy
                    ;


directionModifier   : '@L'  # LeftOf
                    | '@R'  # RightOf
                    ;

LinearDistance      : '<lin_' '-'? [0-9]+ ':' '-'? [0-9]+
                    ;

Neg    : '!' ;

WhiteSpace  : [ \t\n\r\f]+ -> skip;

// TODO: How do we do regex here?
Value  : ~[\t\n\r\f !|&@=<>(){}]+
       ;

String : '"' (~[\\"] | '\\' .)* '"';
