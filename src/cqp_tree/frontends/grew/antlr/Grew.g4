grammar Grew;

request:    pattern requestItem* EOF;

pattern         : 'pattern' body
                ;
requestItem     : 'with' body       # WithItem
                | 'without' body    # WithoutItem
                ;

// List of clauses, final semicolon is optional.
body    : '{' (clause ';')* (clause ';'?)? '}'
        ;
// Supported clauses.
clause  : label=Identifier featureStructure ('|' featureStructure)*     # NodeClause
        | (label=Identifier ':')? src=Identifier arrow dst=Identifier   # EdgeClause
        | lhs=featureValue compare rhs=featureValue                     # ConstraintClause
        | lhs=Identifier order rhs=Identifier                           # OrderClause
        ;

// Different ways of specifying feature structures.
featureStructure    : '[' (feature (',' feature)*)? ']'
                    ;
feature             : Identifier                                                # Presence
                    | '!' Identifier                                            # Absence
                    | Identifier compare (featureValue ('|' featureValue)*)?    # Requires
                    ;

// Different arrows.
arrow           : '->'                          # SimpleArrow
                | '-[' edgeTypes ']->'          # PositiveArrow
                | '-[' '^' edgeTypes ']->'      # NegatedArrow
                ;
edgeTypes       : literal ('|' literal)*
                ;

// Either a Literal or a reference to another tokens feature structure.
featureValue    : Identifier '.' Identifier     # Attribute
                | literal                       # Value
                ;

// All the ways of specifying values.
literal         : String                        # UnicodeString
                | Identifier                    # SimpleString
                | 're' String                   # Regex
                | PCREString                    # PCRE
                | Identifier ':' Identifier     # Subtype
                ;

order           : '<'   # ImmediatePrecedence
                | '<<'  # Precedence
                ;

compare         : '='   # Equality
                | '<>'  # Inequality
                ;


IgnoredWhitespace: [ \t\r\n]+ -> skip;
IgnoredComments: '%' ~( '\r' | '\n' )* -> skip;

Identifier : [0-9]+ | [a-zA-Z_] | [A-Za-z_] [A-Za-z0-9_'\-$]* [a-zA-Z0-9_'$] ;

String : '"' (~'"' | '\\.')* '"';
PCREString : '/' (~'/' | '\\/')* ('/'|'/i')?;
