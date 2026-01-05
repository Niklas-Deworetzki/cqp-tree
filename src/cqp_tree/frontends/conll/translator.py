from enum import StrEnum
from types import NoneType
from typing import Any, Callable, Iterable, Tuple

import conllu
from conllu.exceptions import ParseException

import cqp_tree.translation as ct

"""
This module is used to parse CoNLL-U (and potentially CoNLL-U Plus). Most of 
the format parsing is done by the `conllu` package. Look here for the format 
specification: https://universaldependencies.org/format.html

A CoNLL-U file has different *columns* (id, form, lemma, upos, xpos, feats, 
head, deprel, deps, misc). Some *annotations* live directly in a column
(form, lemma, upos, xpos). Others are encoded as *features* within a column.
In those cases, they are encoded as `Key=Value`.
"""

type Reference = Any

NO_VALUE = '_'

UNSPECIFIED_VALUE = '*'

# CoNLL-U columns that are mapped to Språkbanken Korp annotations.
SPRAAKBANKEN_MAPPED_ANNOTATION_COLUMNS = {
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

# CoNLL-U columns that are mapped to an annotation holding a feature string
# in Språkbanken Korp.
# An entry 'feats': 'ufeats' means that all annotations in the 'feats' column
# are translated into Key=Value pairs contained in the value of the 'ufeats'.
# Tense=Pres,Pers=3 becomes
#           [ufeats contains "Tense=Pres" & ufeats contains "Pers=3"]
SPRAAKBANKEN_MAPPED_FEATURE_COLUMNS = {
    'feats': 'ufeats',
}

# CoNLL-U columns that have their features expanded and translated into
# individual annotations.
# Tense=Pres,Pers=3 becomes
#           [Tense = "Pres" & Pers = "3"]
SPRAAKBANKEN_EXPANDED_FEATURE_COLUMNS = {'misc'}


class ReservedAnnotation(StrEnum):
    """
    All reserved annotations to be ignored when translating.
    """

    # Special meanings for translation
    ORDERED = 'ordered'
    SUBSEQUENT = 'subsequent'
    ANCHORED = 'anchored'

    # Special meanings for graphical tool
    APP_INTERNAL_HIGHLIGHT = 'highlight'

    @classmethod
    def is_reserved(cls, annotation: str) -> bool:
        return annotation in cls


def has_annotation(token: conllu.Token, annotation: ReservedAnnotation) -> bool:
    """
    Does the given CoNLL-U token has an annotation?
    Annotation has to be encoded as Ann=Yes on the misc column.
    """
    all_annotations = token['misc']
    if hasattr(all_annotations, '__getitem__') and annotation.value in all_annotations:
        return all_annotations[annotation.value] == 'Yes'
    return False


class Translation:
    """
    Translation state and configuration.
    """

    mapped_annotation_columns: dict[str, str]
    mapped_feature_columns: dict[str, str]
    expanded_feature_columns: Iterable[str]

    conllu_tokens: list[conllu.Token]

    tokens: list[ct.Token]
    predicates: list[ct.Predicate]
    dependencies: list[ct.Dependency]
    constraints: list[ct.Constraint]

    _identifier_lookup_table: dict[Reference, ct.Identifier]

    def __init__(self, tokens: Iterable[conllu.Token]):
        self.conllu_tokens = list(tokens)

        self.mapped_annotation_columns = SPRAAKBANKEN_MAPPED_ANNOTATION_COLUMNS
        self.mapped_feature_columns = SPRAAKBANKEN_MAPPED_FEATURE_COLUMNS
        self.expanded_feature_columns = SPRAAKBANKEN_EXPANDED_FEATURE_COLUMNS

        self.tokens = [ct.Token() for _ in self.conllu_tokens]
        # Allocate space for the other structures
        self.predicates, self.dependencies, self.constraints = [], [], []

        # Build a lookup table for conllu-ids to internal identifiers.
        self._identifier_lookup_table = {rt['id']: tok.identifier for rt, tok in self}

    def __len__(self):
        return len(self.conllu_tokens)

    def __getitem__(self, index: int) -> Tuple[conllu.Token, ct.Token]:
        return self.conllu_tokens[index], self.tokens[index]

    def __iter__(self):
        return zip(self.conllu_tokens, self.tokens)

    def resolve_reference(self, reference: Reference) -> ct.Identifier:
        if reference in self._identifier_lookup_table:
            return self._identifier_lookup_table[reference]

        if reference == UNSPECIFIED_VALUE:
            raise ct.NotSupported('Having an underspecified dependency head is not supported.')
        raise ct.NotSupported(f'Dependency head "{reference}" is not specified as part of file.')

    @staticmethod
    def parse(s: str) -> 'Translation':
        def is_valid_token(token: conllu.Token) -> bool:
            """
            Used to filter out MWE and empty nodes. Also skips all tokens that don't have an ID field.
            """
            return isinstance(token['id'], int)

        # TODO: Parse header to auto-detect translated fields.
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

        return Translation(tokens)


# Here we have the different functions to do the actual translation parts.


def _map_annotation_columns(translation: Translation, token: conllu.Token, id: ct.Identifier):
    for column, mapping in translation.mapped_annotation_columns.items():
        value = token[column]

        if value == UNSPECIFIED_VALUE or value is None:
            pass  # Skip unspecified values.

        elif value == NO_VALUE:
            pass  # TODO: How do we do that, though?

        else:
            translation.predicates.append(field_to_attribute(id, mapping, value))


def _map_feature_columns(translation: Translation, token: conllu.Token, id: ct.Identifier):
    for column, mapping in translation.mapped_feature_columns.items():
        features = token[column]
        if isinstance(features, dict):
            extracted_attributes = [
                field_to_attribute(
                    id, mapping, f'{feature_key}={feature_value}', operator='contains'
                )
                for feature_key, feature_value in features.items()
            ]

            translation.predicates.extend(extracted_attributes)


def _expand_feature_columns(translation: Translation, token: conllu.Token, id: ct.Identifier):
    for column in translation.expanded_feature_columns:
        features = token[column]
        if isinstance(features, dict):
            extracted_attributes = [
                field_to_attribute(id, field, value)
                for field, value in features.items()
                if not ReservedAnnotation.is_reserved(field)
            ]

            translation.predicates.extend(extracted_attributes)


def _map_dependencies(translation: Translation, token: conllu.Token, id: ct.Identifier):
    dependency: Reference = token['head']
    if dependency in {NO_VALUE, None, 0}:
        return  # no value or root dependency

    dep = ct.Dependency(translation.resolve_reference(dependency), id)
    translation.dependencies.append(dep)


def _extract_anchors(translation: Translation):
    first_rt, first_tok = translation[0]
    if has_annotation(first_rt, ReservedAnnotation.ANCHORED):
        translation.constraints.append(
            ct.Constraint.anchor(first_tok.identifier, is_first=True),
        )

    last_rt, last_tok = translation[-1]
    if has_annotation(last_rt, ReservedAnnotation.ANCHORED):
        translation.constraints.append(
            ct.Constraint.anchor(last_tok.identifier, is_last=True),
        )


def _extract_order(translation: Translation):
    ordered_identifiers = []
    for rt, tok in translation:
        if has_annotation(rt, ReservedAnnotation.ORDERED):
            ordered_identifiers.append(tok.identifier)

    # We now have all identifiers participating in the order
    # make a chain out of them.
    for a, b in zip(ordered_identifiers, ordered_identifiers[1:]):
        translation.constraints.append(
            ct.Constraint.order(a, b),
        )


def _extract_subsequent_tokens(translation: Translation):
    for i in range(1, len(translation)):
        sub_rt, sub_tok = translation[i]
        if has_annotation(sub_rt, ReservedAnnotation.SUBSEQUENT):
            pre_rt, pre_tok = translation[i - 1]

            constraints = [
                ct.Constraint.distance(pre_tok.identifier, sub_tok.identifier) == 1,
                ct.Constraint.order(pre_tok.identifier, sub_tok.identifier),
            ]
            translation.constraints.extend(constraints)


@ct.translator('conll')
def translate_conll(conll: str) -> ct.Recipe:
    translation = Translation.parse(conll)

    def lift(
        f: Callable[[Translation, conllu.Token, ct.Identifier], NoneType],
    ) -> Callable[[Translation], NoneType]:
        def lifted(trans: Translation):
            for rt, tok in trans:
                f(trans, rt, tok.identifier)

        return lifted

    # These are all the things we can translate for now
    extractors = (
        lift(_map_annotation_columns),
        lift(_map_feature_columns),
        lift(_expand_feature_columns),
        lift(_map_dependencies),
        _extract_anchors,
        _extract_order,
        _extract_subsequent_tokens,
    )
    # Perform each supported translation.
    for extractor in extractors:
        extractor(translation)

    query = ct.Query(
        tokens=translation.tokens,
        dependencies=translation.dependencies,
        predicates=translation.predicates,
        constraints=translation.constraints,
    )
    return ct.Recipe.of_query(query)


def field_to_attribute(
    id: ct.Identifier, key: str, value: Any, operator: str = '='
) -> ct.Predicate:
    return ct.Comparison(
        ct.Attribute(id, key),
        operator,
        ct.Literal(f'"{value}"', represents_regex=False),
    )
