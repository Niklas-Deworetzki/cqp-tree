
FILES IN THIS DIRECTORY ARE AUTO-GENERATED.

The only file of interest in here is Grew.g4, the ANTLR4 lexer and parser specification for the supported subset of Grew.
If you updated the specification, re-generate the contents of this directory using the following command:

    antlr4 -Dlanguage=Python3 -no-listener Grew.g4

A decision was made to ship generated files.
This places some additional burden on developers updating the specification, as they (you) have to generate these files.
However, it also enables users to simply use this package without having to install ANTLR as well.
