grammar Depsearch;


query : allQuantified? tokensExpression ('+' tokensExpression)* EOF ;

allQuantified
    : atomicToken '->'
    ;

tokensExpression
    // TODO: How does sequencing associate?
    : lhs=tokenExpression '.' rhs=tokensExpression                           # SequenceToken
    | lhs=tokenExpression LinearDistance orderModifier? rhs=tokensExpression # DistanceToken
    // t1 > t2 > t3 means t2 and t3 are dependents of t1
    // t1 > (t2 > t3) searches for chains instead.
    | src=tokenExpression (dependencyDescription)+                          # DependenciesToken
    | exp=tokenExpression                                                   # JustAToken
    ;

tokenExpression
    : lhs=tokenExpression '&' rhs=tokenExpression                       # ConjunctionToken
    | lhs=tokenExpression '|' rhs=tokenExpression                       # DisjunctionToken
    | exp=negatedToken                                                  # PossiblyNegatedToken
    ;

negatedToken : Neg exp=atomicToken  # NegationToken
             | exp=atomicToken      # JustATokenAttribute
             ;

atomicToken : '(' exp=tokensExpression ')'  # ParenthesizedToken
            | '_'                           # ArbitraryToken
            | Value                         # WordOrTagToken
            | String                        # WordformToken
            | key=Value '=' (value=Value | regex=String)    # AttributeToken
            ;

dependencyDescription : dependencyExpression dst=tokensExpression
                      ;

// one can use OR operator to query dependency relations
dependencyExpression : lhs=dependencyExpression '|' rhs=dependencyExpression # DisjunctionDependency
                     | Neg atomicDependency                                  # NegationDependency
                     | exp=atomicDependency                                  # JustADependency
                     ;

atomicDependency  : '(' exp=dependencyExpression ')'                            # ParenthesizedDependency
                  | dependencyOperator (negatedType=Neg? Value)? orderModifier? # Dependency
                  ;




dependencyOperator  : '>'   # Governs
                    | '<'   # GovernedBy
                    ;


orderModifier   : '@L'  # LeftOf
                | '@R'  # RightOf
                ;

LinearDistance      : '<lin_' '-'? [0-9]+ ':' '-'? [0-9]+
                    ;

Neg    : '!' ;

WhiteSpace  : [ \t\n\r\f]+ -> skip;

Value  : ~[\t\n\r\f !|&@=<>(){}"]+
       ;

String : '"' (~[\\"] | '\\' .)* '"';
