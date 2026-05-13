from dataclasses import dataclass
from typing import Callable, Collection, Tuple

from cqp_tree.configuration.configuration import (
    Configuration,
    DeclaredConfig,
    declare_configuration,
    get_frontend_configuration,
)
from cqp_tree.translation.errors import NotSupported
from cqp_tree.translation.query import Recipe

type TranslationFunction = Callable[[str, Configuration], Recipe]

known_translators = dict[str, TranslationFunction]()


def translator(name: str, *cf: DeclaredConfig):
    """
    Decorator used to register translation functions.
    """

    for configuration_entry in cf:
        declare_configuration(configuration_entry, name)

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


def translate_input(inp: str, global_config: Configuration) -> Recipe:
    """
    Translates an input using the given translator. If no translator is given,
    the correct translator is guessed by trying all available translators.

    If guessing the translator gives 0 or multiple possible translators, an
    UnableToGuessTranslatorError is raised, containing all applicable translators.

    If a translator to use is specified, but the translator is not known,
    a KeyError is raised.
    """
    if global_config.translator is None:
        guessed_translations = guess_correct_translator(inp, global_config)
        if not guessed_translations:
            raise UnableToGuessTranslatorError(tuple())

        if len(guessed_translations) > 1:
            raise UnableToGuessTranslatorError(tuple(trans for trans, _ in guessed_translations))

        _, query = guessed_translations[0]
        return query

    if global_config.translator not in known_translators:
        raise KeyError(f'Unknown translator: {global_config.translator}')
    return _run_translator_with_configuration(inp, global_config.translator, global_config)


def guess_correct_translator(
    inp: str,
    global_config: Configuration,
) -> list[Tuple[str, Recipe]]:
    """
    Tries to find translators applicable for the input string.
    Returns all successfully translated queries and the name of the translation frontend that
    accepted the input.

    If only one translator parses the query but raises a NotSupported, this exception is propagated.

    :param inp: The input for which translation is attempted by all frontends.
    :param global_config: Configuration applying for all translators.
    """
    translated_queries = list[Tuple[str, Recipe]]()
    unsupported_queries = list[Tuple[str, NotSupported]]()

    for name in known_translators:
        try:
            parsed = _run_translator_with_configuration(inp, name, global_config)
            translated_queries.append((name, parsed))
        except NotSupported as not_supported:
            unsupported_queries.append((name, not_supported))
        except:  # pylint: disable=bare-except
            pass  # Assume that we cannot translate, independent of exception raised.

    if not translated_queries and len(unsupported_queries) == 1:
        trans, raised_exception = unsupported_queries[0]
        # Create a new exception with copied message and include original traceback.
        raise NotSupported(
            f'{raised_exception} (automatically selected {trans} as a translator)'
        ) from raised_exception
    return translated_queries


def _run_translator_with_configuration(
    inp: str, translator_name: str, global_config: Configuration
) -> Recipe:
    """
    Sets up the configuration for a given translator and runs the translator
    on the given input.

    :raise KeyError: If the translator name is not known.
    :raise InputError: If the input is can not be parsed by the translator.
    :raise NotSupported: If the input contains an unsupported feature for the translator.
    """
    cfg = get_frontend_configuration(translator_name, global_config)
    function = known_translators[translator_name]
    return function(inp, cfg)
