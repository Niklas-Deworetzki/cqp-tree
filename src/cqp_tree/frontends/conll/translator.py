from typing import Any, Dict, Optional

import conllu
from conllu.exceptions import ParseException

import cqp_tree.translation as ct

type Reference = Any

NO_VALUE = '_'

UNSPECIFIED_VALUE = '*'

# CoNLL-U fields mapped to Språkbanken Korp attributes
FIELDS2ATTRS = {
    "form": "word",
    "lemma": "lemma",
    "upos": "pos",  # but upos (actual UD tags) may be added soon
    "xpos": "msd",  # not sure about this one
    "deprel": "deprel",  # mambadep, but UD relations may be added soon
    # id and head are used for dependencies
    # deps is ignored for now
    # feats is translated as the attribute
    # misc is expanded and added to the token
}


def parse(s: str):
    def is_valid_token(token: conllu.Token) -> bool:
        """
        Used to filter out MWE and empty nodes. Also skips all tokens that don't have an ID field.
        """
        return isinstance(token['id'], int)

    # TODO: Parse global.columns comment in first line to auto-detect fields.
    try:
        parsed = conllu.parse(s)
    except ParseException as ex:
        raise ct.ParsingFailed(ct.InputError(None, str(ex)))
    if len(parsed) == 0:
        raise ct.ParsingFailed(ct.InputError(None, 'Cannot parse an empty .conllu file.'))

    sentence = parsed[0]  # only first parsed CoNLL-U sentence
    tokens = [token for token in sentence if is_valid_token(token)]
    if len(tokens) == 0:
        raise ct.ParsingFailed(ct.InputError(None, 'No tokens were found in the .conllu file.'))

    return tokens


@ct.translator('conll')
def translate_conll(conll: str) -> ct.Recipe:
    tokens = list[ct.Token]()
    dependencies = list[ct.Dependency]()

    parsed = parse(conll)
    identifiers = [ct.Identifier() for _ in parsed]
    identifier_by_id = dict(zip((token['id'] for token in parsed), identifiers))

    for token in parsed:
        id = identifier_by_id[token['id']]

        tokens.append(extract_token(token, id))
        dependency = extract_dependency(token, id, identifier_by_id)
        if dependency is not None:
            dependencies.append(dependency)

    query = ct.Query(tokens=tokens, dependencies=dependencies)
    return ct.Recipe.of_query(query)


def field_to_attribute(key: str, value: Any, operator: str = '=') -> ct.Predicate:
    return ct.Comparison(
        ct.Attribute(None, key),
        operator,
        ct.Literal(f'"{value}"', represents_regex=False),
    )


def extract_token(token: conllu.Token, id: ct.Identifier) -> ct.Token:
    """
    Return a Token instance with predicates from the given annotations.

    :param token: All token annotations
    :param id: Identifier of the token
    """

    def extract_feats():
        features = token['feats']
        if isinstance(features, dict) and features:  # non-empty dictionary
            feature_attributes = [
                field_to_attribute('ufeats', f'{feature_key}={feature_value}', operator='contains')
                for feature_key, feature_value in features.items()
            ]
            yield ct.Conjunction.of(feature_attributes)

    def extract_misc():
        misc = token['misc']
        if isinstance(misc, dict) and misc:  # non-empty dictionary
            for misc_key, misc_value in misc.items():
                yield field_to_attribute(misc_key, misc_value)

    def extract_attribtues():
        for column, mapped_attribute in FIELDS2ATTRS.items():
            value = token[column]
            if value == UNSPECIFIED_VALUE or value is None:
                pass  # Skip unspecified values.

            elif value == NO_VALUE:
                pass  # TODO: How do we do that, though?

            else:
                yield field_to_attribute(mapped_attribute, value)

    attributes = list[ct.Predicate]()
    attributes.extend(extract_attribtues())
    attributes.extend(extract_feats())
    attributes.extend(extract_misc())
    return ct.Token(id, ct.Conjunction.of(attributes))


def extract_dependency(
    token: conllu.Token,
    id: ct.Identifier,
    identifiers: Dict[Reference, ct.Identifier],
) -> Optional[ct.Dependency]:
    """
    Return Dependency if present, None otherwise.

    :param token: All token annotations
    :param id: Identifier of the token
    :param identifiers: Identifiers of other tokens
    """
    dependency = token['head']
    # no value or root dependency
    if dependency in {NO_VALUE, 0}:
        return None

    if dependency not in identifiers:
        if dependency == NO_VALUE or dependency is None:
            return None
        if dependency == UNSPECIFIED_VALUE:
            raise ct.NotSupported('Having an underspecified dependency head is not supported.')
        raise ct.NotSupported(f'Dependency head "{dependency}" is not specified as part of file.')

    return ct.Dependency(identifiers[dependency], id)
