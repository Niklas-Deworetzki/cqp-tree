from typing import Optional

from cqp_tree.configuration import Configuration
from cqp_tree.translation.cqp import CQPDialect
from cqp_tree.translation.errors import NotSupported
from cqp_tree.translation.query import (
    Attribute,
    Comparison,
    Conjunction,
    Disjunction,
    Identifier,
    Literal,
    Negation,
    Operand,
    Predicate,
    Token,
)
from cqp_tree.translation.regex import escape_regex_string

UD_TAGS = {
    'ADJ',
    'ADP',
    'ADV',
    'AUX',
    'CCONJ',
    'DET',
    'INTJ',
    'NOUN',
    'NUM',
    'PART',
    'PRON',
    'PROPN',
    'PUNCT',
    'SCONJ',
    'SYM',
    'VERB',
    'X',
}

UD_FEATURES = {
    'Abbr',
    'Animacy',
    'Aspect',
    'Case',
    'Clusivity',
    'Definite',
    'Degree',
    'Deixis',
    'DeixisRef',
    'Evident',
    'ExtPos',
    'Foreign',
    'Gender',
    'Mood',
    'NounClass',
    'NumType',
    'Number',
    'Person',
    'Polarity',
    'Polite',
    'Poss',
    'PronType',
    'Reflex',
    'Tense',
    'Typo',
    'VerbForm',
    'Voice',
}


def contains(
    cfg: Configuration,
    attr: Attribute,
    *values: Operand,
    negated: bool = False,
) -> Predicate:
    """Creates an expression like [attr contains strings], adapted different corpus systems."""
    if cfg.dialect == CQPDialect.SKETCH_ENGINE:
        # SketchEngine does not have the "contains" operator, so we have to emulate it.
        # We do so by crafting a regex that searches for value with arbitrary pre/suffix.
        expected_strings = []
        for value in values:
            if isinstance(value, Literal):
                string_value: str = value.value
                if string_value[0] == '"' and string_value[-1] == '"':
                    expected_strings.append(string_value[1:-1])
                    continue

            raise NotSupported(
                'In Sketch Engine, you can only use string literals or regular expressions when '
                'checking whether an annotation contains a certain value.'
            )

        contains_regexes = [f'".*{escape_regex_string(string)}.*"' for string in expected_strings]
        pred = Disjunction.of(
            Comparison(attr, '=', Literal(regex, represents_regex=True))
            for regex in contains_regexes
        )

    else:
        pred = Disjunction.of(Comparison(attr, 'contains', value) for value in values)

    if negated:
        pred = Negation(pred)
    return pred


def wordform(
    cfg: Configuration,
    token: Optional[Token | Identifier],
    *values: Operand,
    negated: bool = False,
) -> Predicate:
    """
    Creates a predicate to compare a tokens word form with a set of given values.
    """
    attr = Attribute(_to_identifier(token), cfg.form)
    if not negated:
        return Disjunction.of(Comparison(attr, '=', value) for value in values)
    else:
        return Conjunction.of(Comparison(attr, '!=', value) for value in values)


def upos(
    cfg: Configuration,
    token: Optional[Token | Identifier],
    *tags: Operand,
    negated: bool = False,
):
    """
    Creates a predicate to compare a tokens universal part-of-speech with a set of given values.
    """
    attr = Attribute(_to_identifier(token), cfg.upos)
    if not negated:
        return Disjunction.of(Comparison(attr, '=', value) for value in tags)
    else:
        return Conjunction.of(Comparison(attr, '!=', value) for value in tags)


def dependency_type(
    cfg: Configuration,
    dependant: Optional[Token | Identifier],
    *dependency_types: Operand,
    negated: bool = False,
) -> Predicate:
    """
    Creates a predicate to compare a dependency relation type with a set of given values.
    Assumes that the dependency type information is stored on the dependant.
    """
    attr = Attribute(_to_identifier(dependant), cfg.deprel)
    if not negated:
        return Disjunction.of(Comparison(attr, '=', value) for value in dependency_types)
    else:
        return Conjunction.of(Comparison(attr, '!=', value) for value in dependency_types)


def ud_feature(
    cfg: Configuration,
    token: Optional[Token | Identifier],
    feature: str,
    *values: Operand,
    negated: bool = False,
) -> Predicate:
    """
    Creates a predicate to compare a feature with a set of given values.
    This tries to auto-detect whether the given feature is one of the UD features, and
    therefore encoded on the *feats* column. If it is not one of the UD features, a simple
    [feature = values] predicate is created.

    UD feature detection is only performed if `ud_mode` is true in the given configuration.
    """
    if is_ud_feature(cfg, feature):
        attr = Attribute(_to_identifier(token), cfg.feats)
        try:
            return contains(cfg, attr, *values, negated=negated)
        except NotSupported as e:
            raise NotSupported(
                'Your search for a UD feature has been converted into a "contains" check '
                f'for the {cfg.feats} annotation, which is not supported on Sketch Engine. '
                f'Try disabling UD mode in settings or re-writing your query ({e})'
            ) from e

    else:
        attr = Attribute(_to_identifier(token), feature)
        if not negated:
            return Disjunction.of(Comparison(attr, '=', value) for value in values)
        else:
            return Conjunction.of(Comparison(attr, '!=', value) for value in values)


def is_ud_tag(cfg: Configuration, pos: str) -> bool:
    """
    Returns True, if the given part-of-speech tag is one of the UD tags and the given
    configuration has `ud_mode` set to True.
    """
    return cfg.ud_mode and pos in UD_TAGS


def is_ud_feature(cfg: Configuration, feature: str) -> bool:
    """
    Returns True, if the given feature is one of the UD features and the given
    configuration has `ud_mode` set to True.
    """
    return cfg.ud_mode and feature in UD_FEATURES


def _to_identifier(token_or_identifier: Optional[Token | Identifier]) -> Optional[Identifier]:
    if isinstance(token_or_identifier, Token):
        return token_or_identifier.identifier
    return token_or_identifier
