from spacy_conll import init_parser
import conllu
import py3langid as langid

def example2conllquery(ex_sent: str, lang=None) -> str:
    pass
    # TODO:
    # - save highlighted parts
    # - remove highlighting
    # - infer language if necessary
    # - parse
    # - extract tree of the highlighted span(s) (if any, if not keep the whole tree)
    # - return conll

def guess_lang(sent: str) -> str:
    return langid.classify(sent)[0]

def parse(sent: str, lang: str="en") -> conllu.TokenTree:
    try:
        parser = init_parser(lang, "udpipe")
    except AssertionError:
        print("Language {} not supported. Defaulting to English (en)..."
              .format(lang))
        parser = init_parser("en", "udpipe")
    conllu_str = parser(sent)._.conll_str
    trees = conllu.parse_tree(conllu_str)
    if not trees: # return dummy tree
        return conllu.TokenTree(
            token=conllu.Token(id=1, form="_", head=0, deprel="root"), 
            children=[])
    else:
        if len(trees) > 1:
            print("Ignoring all sentences but the first one...")
        return trees[0]