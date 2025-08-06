from spacy_conll import init_parser
import conllu
from marko import convert as to_html
from bs4 import BeautifulSoup
import py3langid as langid

def example2conllquery(md: str, lang=None) -> str:
    (spans, txt) = md2spans(md)
    if not lang:
        lang = guess_lang(txt)
    tree = parse(txt, lang)
    pass
    # TODO:
    # - extract tree of the highlighted span(s) (if any, if not keep the whole tree)
    # - return conll

def md2spans(md: str) -> tuple[list[str], str]:
    soup = BeautifulSoup(to_html(md))
    spans = [tag.text for tag in soup.find_all("strong")]
    return (spans, soup.text)

def guess_lang(txt: str) -> str:
    return langid.classify(txt)[0]

def parse(txt: str, lang: str="en") -> conllu.TokenTree:
    try:
        parser = init_parser(lang, "udpipe")
    except AssertionError:
        print("Language {} not supported. Defaulting to English (en)..."
              .format(lang))
        parser = init_parser("en", "udpipe")
    conllu_str = parser(txt)._.conll_str
    trees = conllu.parse_tree(conllu_str)
    if not trees: # return dummy tree
        return conllu.TokenTree(
            token=conllu.Token(id=1, form="_", head=0, deprel="root"), 
            children=[])
    else:
        if len(trees) > 1:
            print("Ignoring all but the first sentence...")
        return trees[0]