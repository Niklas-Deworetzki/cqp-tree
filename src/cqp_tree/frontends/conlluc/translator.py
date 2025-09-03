from typing import List

import cqp_tree.frontends.conlluc.tools as conlluc

import cqp_tree.translation as ct

# TODO: CoNLL-U fields mapped to SketchEngine attributes
FIELDS2ATTRS = {
    "form": "word",
    "lemma": "lemma",
    "upos": "pos",  # but upos (actual UD tags) may be added soon
    "feats": "feats",  # actual UD features
    "deprel": "deprel",  # mambadep, but UD relations may be added soon
    # other fields are not treated as attributes
    # some are ignored for the time being
}


def parse(s: str):
    try:
        parsed = conlluc.parse(s)
        print(parsed)
    except:
        raise ct.ParsingFailed(ct.InputError(
            None, 
            "Something went wrong but there was no time to handle exceptions, sorry about that!"))
    return parsed["tokens"]


@ct.translator('conlluc')
def query_from_conlluc(conlluc: str) -> ct.Query:
    tokens: List[ct.Token] = []
    dependencies: List[ct.Dependency] = []

    conll_lines = parse(conlluc)
    print(conll_lines)

    ids = [ct.Identifier() for _ in conll_lines]

    def field2op(field, value) -> ct.Comparison:
        #if field in ["WITHOUT", "ADJACENCY", "IDENTITY"]:
            #raise ct.NotSupported('Only TREE_ is supported for matching subtrees.')
        if type(value) == str:
            return ct.Comparison(ct.Attribute(None, field), '=', ct.Literal(value))
        elif type(value) == list:
            return ct.Disjunction([ct.Comparison(ct.Attribute(None, field), "=", ct.Literal(el)) for el in value])


    def is_empty(line, field):
        print(line)
        return line[field] in [["_"], None]

    for line, id in list(zip(conll_lines, ids)):
        # TODO: actually, HEAD can be underspecified in this format
        print(line)
        if is_empty(line, "id") or is_empty(line, "head"):
            raise ct.NotSupported("IDs and HEADs cannot be omitted.")
        ops = []
        # pylint: disable=consider-using-dict-items
        for field in FIELDS2ATTRS:
            if not is_empty(line, field):
                ops.append(field2op(FIELDS2ATTRS[field], line[field]))
        if ops:
            tokens.append(ct.Token(id, ct.Conjunction(ops)))
        else:  # token with no attributes, only there for structural reasons
            tokens.append(ct.Token(id))

        if line["head"] != "0":
            dependencies.append(
                ct.Dependency(ids[[line["id"] for line in conll_lines].index(line["head"])], id)
            )

    return ct.Query(tokens=tokens, dependencies=dependencies)
