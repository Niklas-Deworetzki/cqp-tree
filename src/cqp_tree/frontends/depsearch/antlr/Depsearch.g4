grammar Depsearch;


query : allQuantified? tokenExpression ('+' tokenExpression)* EOF ;

allQuantified
    : simpleToken '->'
    ;

tokenExpression
    : lhs=tokenExpression '&' rhs=tokenExpression                       # Conjunction
    | lhs=tokenExpression '|' rhs=tokenExpression                       # Disjunction
    | lhs=simpleToken '.' rhs=simpleToken                               # Sequence
    | lhs=simpleToken LinearDistance directionModifier? rhs=simpleToken # Distance
    | src=simpleToken (dependency)*                                     # Dependencies
    ;

dependency          : edge dst=simpleToken
                    ;

simpleToken : '(' exp=tokenExpression ')'   # ParenthesizedToken
            | Neg exp=simpleToken           # Negation
            | '_'                           # Arbitrary
            | Value '=' Value               # Attribute
            | Value                         # WordOrTag
            | String                        # Wordform
            ;


edge : edgeDescription ('|' edgeDescription)*
     ;

edgeDescription
    :   absent=Neg?
        dependencyOperator
        negatedType=Neg?
        Value?
        directionModifier?
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
