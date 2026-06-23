from urllib.parse import parse_qs, urlencode, urlparse, urlunparse, quote

CANNOT_FIND_CORPUS_NAME = 'URL seems to be a SketchEngine URL, but no corpus name can be found.'
CANNOT_DETECT_CORPUS_SYSTEM = 'URL does not seem to point to a supported corpus system.'


def make_external_search_url(corpus_url: str, query: str) -> str:
    parsed = urlparse(corpus_url)
    if parsed.fragment.startswith('concordance') or parsed.fragment.startswith('dashboard'):
        corpus = _extract_corpus_from_sketchengine_fragment(parsed.fragment)
        fragment = 'concordance?' + urlencode(
            {
                'tab': 'advanced',
                'queryselector': 'cql',
                'showresults': '1',
                'corpname': corpus,
                'cql': query,
            },
            quote_via=quote,
        )
        parsed = parsed._replace(fragment=fragment)
        return urlunparse(parsed)
    raise ValueError(CANNOT_DETECT_CORPUS_SYSTEM)


def _extract_corpus_from_sketchengine_fragment(fragment: str) -> str:
    _, sep, fragment_query = fragment.partition('?')
    if not sep:
        raise ValueError(CANNOT_FIND_CORPUS_NAME)

    params = parse_qs(fragment_query)
    corpnames = params.get('corpname')
    if not corpnames:
        raise ValueError(CANNOT_FIND_CORPUS_NAME)
    return corpnames[0]
