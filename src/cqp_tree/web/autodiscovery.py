import json
from dataclasses import dataclass
from typing import Any, Iterable

import requests

import cqp_tree


@dataclass(frozen=True)
class Corpus:
    id: str
    name: str
    additional_info: str
    language: str


def sketchengine_request_corpus_data(cfg: cqp_tree.Configuration) -> Iterable[dict[str, Any]]:
    try:
        if cfg.baseurl:
            # TODO: Baseurl or queryurl as configuration?
            data = requests.get(cfg.baseurl + 'bonito/run.cgi/corpora').json()
            return data.get('data', [])
    except requests.exceptions.RequestException:
        return []
    except KeyError:
        return []


def corpora(cfg: cqp_tree.Configuration) -> dict[str, Corpus]:
    parsed_data = [
        Corpus(
            id=corpus.get('corpname'),
            name=corpus.get('name'),
            additional_info=corpus.get('info'),
            language=corpus.get('language_name'),
        )
        for corpus in sketchengine_request_corpus_data(cfg)
    ]
    return {corpus.id: corpus for corpus in parsed_data}
