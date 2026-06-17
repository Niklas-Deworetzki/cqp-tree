from urllib.parse import urlparse, urlunparse, parse_qs


def make_external_search_url(corpus_url: str, query: str) -> str:
    url = urlparse(corpus_url)
    query_components = parse_qs(url.query)
    if url.fragment:
        # SketchEngine has the shape sketchengine.com/#concordance?corpname=korp
        # which makes the query parameters actually part of the *fragment* and not of the
        # query, so we'll just parse the fragment with its query parameters as well.
        query_components |= parse_qs(url.fragment)

    if 'corpname' in query_components:
        corpus = query_components['corpname'][0]
        search_url = url._replace(
            query=f'tab=advanced&queryselector=cql&showresults=1&corpname={corpus}&cql={query}'
        )

        if search_url.scheme not in ('http', 'https'):
            search_url = search_url._replace(
                scheme='https',
            )

        return urlunparse(search_url)

    raise ValueError('Unable to autodetect corpus and corpus system from url.')
