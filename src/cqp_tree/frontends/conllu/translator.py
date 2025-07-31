from typing import List

import conllu

import cqp_tree.translation as ct

ATTRS = ["form", "lemma", "upos", "xpos", "feats", "deprel", "misc"]

def parse(s: str):
    try:
        parsed = conllu.parse(s)
    except conllu.exceptions.ParseException as ex:
        raise ct.ParsingFailed([ct.InputError(None, ex)])
    return parsed[0] # only first parsed CoNLL-U sentence


@ct.translator('conllu')
def query_from_conllu(conllu: str) -> ct.Query:
    tokens: List[ct.Token] = []
    dependencies: List[ct.Dependency] = []

    conllu_lines = parse(conllu)

    ids = [ct.Identifier() for _ in conllu_lines]
    
    def field2op(field, value) -> ct.Operation:
        return ct.Operation(
            ct.Attribute(None, field),
            '=',
            ct.Literal(f'"{value}"')
        )

    for (line,id) in list(zip(conllu_lines, ids)):
        ops = []
        for attr in ATTRS:
            if line[attr] and line[attr] != "_":
                print(line[attr])
                ops.append(field2op(attr, line[attr]))
        tokens.append(ct.Token(id, ct.Conjunction(ops)))
        
        if line["head"] != 0:
            dependencies.append(ct.Dependency(
                id, 
                ids[[line["id"] for line in conllu_lines].index(line["head"])]
            ))

    return ct.Query(tokens=tokens, dependencies=dependencies)