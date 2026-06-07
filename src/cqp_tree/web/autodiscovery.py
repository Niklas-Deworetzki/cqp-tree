import json
from dataclasses import dataclass
from typing import Any, Iterable

import cqp_tree


@dataclass(frozen=True)
class Corpus:
    id: str
    name: str
    additional_info: str
    language: str


def sketchengine_request_corpus_data(cfg: cqp_tree.Configuration) -> Iterable[dict[str, Any]]:
    try:
        return json.loads(EXAMPLE_JSON).get("data")
    except:
        return []


def corpora(cfg: cqp_tree.Configuration) -> Iterable[Corpus]:
    return [
        Corpus(
            id=corpus.get('corpname'),
            name=corpus.get('name'),
            additional_info=corpus.get('info'),
            language=corpus.get('language_name'),
        )
        for corpus in sketchengine_request_corpus_data(cfg)
    ]


EXAMPLE_JSON = """
{
  "data": [
    {
      "id": null,
      "owner_id": null,
      "owner_name": null,
      "tagset_id": null,
      "sketch_grammar_id": null,
      "term_grammar_id": null,
      "_is_sgdev": false,
      "is_featured": false,
      "access_on_demand": false,
      "terms_of_use": null,
      "sort_to_end": null,
      "tags": [],
      "created": null,
      "needs_recompiling": false,
      "user_can_read": true,
      "user_can_upload": false,
      "user_can_manage": false,
      "is_shared": false,
      "is_error_corpus": false,
      "corpname": "mfida10",
      "language_id": "Slovenian",
      "language_name": "Slovenian",
      "sizes": {
        "tokencount": 6094189351,
        "wordcount": 4727457629,
        "doccount": 15454886,
        "parcount": 51822749,
        "sentcount": 281218815
      },
      "compilation_status": "COMPILED",
      "new_version": "",
      "name": "metaFida v1.0 (zdru\u017eeni korpus)",
      "info": "Slovenski zdru\u017eeni korpus metaFida, v1.0 // Slovene meta corpus metaFida, v1.0",
      "wsdef": "",
      "termdef": "",
      "diachronic": false,
      "aligned": [],
      "docstructure": "text"
    }
  ]
}
"""
