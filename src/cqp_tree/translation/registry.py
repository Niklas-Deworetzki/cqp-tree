from dataclasses import dataclass
from typing import Callable, Collection, Iterator, Optional, Tuple

from cqp_tree.translation.errors import NotSupported, ParsingFailed
from cqp_tree.translation.query import ExecutionPlan

type TranslationFunction = Callable[[str], ExecutionPlan]

known_translators = dict[str, TranslationFunction]()


def translator(name: str):
    """
    Decorator used to register translation functions.
    """

    def register(func: TranslationFunction) -> TranslationFunction:
        if name in known_translators:
            raise ValueError(f'Another translation function for {name} has already been registered')
        known_translators[name] = func
        return func

    return register


@dataclass(frozen=True)
class UnableToGuessTranslatorError(Exception):
    matching_translators: Collection[str]

    def no_translator_matches(self) -> bool:
        return not self.matching_translators

    def too_many_translators_match(self) -> bool:
        return len(self.matching_translators) > 1

    def __str__(self):
        if self.no_translator_matches():
            reason = 'no translator matches'
        else:
            reason = 'multiple translators match'
        return f'Cannot guess translator for query: {reason}'


def translate_input(inp: str, use_translator: Optional[str] = None) -> ExecutionPlan:
    """
    Translates an input using the given translator. If no translator is given,
    the correct translator is guessed by trying all available translators.

    If guessing the translator gives 0 or multiple possible translators, an
    UnableToGuessTranslatorError is raised, containing all applicable translators.

    If a translator to use is specified, but the translator is not known,
    a KeyError is raised.
    """
    if use_translator is None:
        guessed_translations = list(guess_correct_translator(inp))
        if not guessed_translations:
            raise UnableToGuessTranslatorError(tuple())

        if len(guessed_translations) > 1:
            raise UnableToGuessTranslatorError(tuple(trans for trans, in guessed_translations))

        _, query = guessed_translations[0]
        return query

    if use_translator not in known_translators:
        raise KeyError(f'Unknown translator: {use_translator}')
    return known_translators[use_translator](inp)


def guess_correct_translator(inp: str) -> Iterator[Tuple[str, ExecutionPlan]]:
    """
    Tries to find translators applicable for the input string.
    Returns an iterator over all successfully translated queries and the name of the
    translation frontend that accepted the input.

    If no frontend accepts the input, an empty iterator is returned.

    :param inp: The input for which translation is attempted by all frontends.
    """
    for name, function in known_translators.items():
        try:
            yield name, function(inp)
        except ParsingFailed:
            pass
        except NotSupported:
            pass
