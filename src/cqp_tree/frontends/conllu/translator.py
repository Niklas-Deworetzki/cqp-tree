from typing import List

import conllu

import cqp_tree.translation as ct

# CoNLL-U fields mapped to Språkbanken Korp attributes
FIELDS2ATTRS = {
    "form": "word", 
    "lemma": "lemma", 
    "upos": "pos", # but upos (actual UD tags) may be added soon
    "xpos": "msd", # not sure about this one
    "feats": "ufeats", # actual UD features
    "deprel": "deprel" # mambadep, but UD relations may be added soon
    # id and head are not treated as attributes
    # deps and misc are ignored for the time being
}

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

    def is_empty(line, field):
        return line[field] in ["_", None]

    for (line,id) in list(zip(conllu_lines, ids)):
        if is_empty(line, "id") or is_empty(line, "head"):
            raise ct.NotSupported("IDs and HEADs cannot be omitted.")
        if not isinstance(line["id"], int):
            pass # skip MWE lines
        ops = []
        for field in FIELDS2ATTRS:
            if not is_empty(line, field):
                ops.append(field2op(FIELDS2ATTRS[field], line[field]))
        if ops:
            tokens.append(ct.Token(id, ct.Conjunction(ops)))
        else: # token with no attributes, only there for structural reasons
            tokens.append(ct.Token(id))

        if line["head"] != 0:
            dependencies.append(ct.Dependency(
                id,
                ids[[line["id"] for line in conllu_lines].index(line["head"])]
            ))

    return ct.Query(tokens=tokens, dependencies=dependencies)
