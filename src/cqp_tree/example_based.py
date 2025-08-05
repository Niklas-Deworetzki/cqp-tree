from spacy_conll import init_parser
import conllu

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