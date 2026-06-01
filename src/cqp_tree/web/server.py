from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

import cqp_tree
from cqp_tree import Recipe
from cqp_tree.utils import UPPERCASE_ALPHABET, associate_with_names

TEMPLATE_DIR = Path(__file__).parent / 'static'

server = Flask(__name__, template_folder=str(TEMPLATE_DIR))


@server.route("/")
def main():
    cfg = cqp_tree.get_frontend_configuration('web')
    return render_template(
        'index.html',
        cfg=cfg,
        settings=cqp_tree.configurable_flags_by_section(hidden_sections={'web'}),
    )


@server.route('/translators', methods=['GET'])
def get_translators():
    translators = sorted(cqp_tree.known_translators.keys())
    return jsonify(translators)


@server.route('/translate', methods=['POST'])
def translate():
    def error(message: str, status: int = 400):
        return jsonify({'error': message}), status

    try:
        text, configuration, translator_configs = extract_request_data()
        plan = cqp_tree.translate_input(text, configuration, translator_configs)

        if is_too_complex(plan):
            raise ValueError('Your query is too complex! Try using fewer tokens.')

        return jsonify(to_json(plan, configuration))

    except ValueError as validation_error:
        return error(str(validation_error), 422)

    except cqp_tree.UnableToGuessTranslatorError as unable_to_guess_translator:
        if unable_to_guess_translator.no_translator_matches():
            return error(
                'This query cannot be translated. '
                'Try checking for syntax errors or manually select the query language.'
            )
        return error(
            'This query is valid in multiple query languages. '
            'Please manually select the query language you intend.'
        )

    except cqp_tree.NotSupported as not_supported:
        return error('This query is not supported: ' + str(not_supported))

    except cqp_tree.ParsingFailed as parse_error:
        parse_error = next(iter(parse_error.errors))
        return error('This query cannot be parsed: ' + parse_error.message)


def is_too_complex(plan: Recipe) -> bool:
    if len(plan.queries) > 20:
        return True
    if any(len(query.tokens) > 5 for query in plan.queries):
        return True
    return False


def extract_request_data() -> tuple[
    str,
    cqp_tree.Configuration,
    dict[cqp_tree.ConfigurationSection, cqp_tree.Configuration],
]:
    translation_request = request.get_json()
    if translation_request is None or not isinstance(translation_request, dict):
        raise ValueError('Malformed request')

    if not 'text' in translation_request:
        raise ValueError('Missing required field "text"')

    text = translation_request['text']
    translator = translation_request.get('translator')
    if translator and translator not in cqp_tree.known_translators:
        raise ValueError('Unknown value for field "translator"')

    provided_settings = translation_request.get('settings', dict())
    configuration = {}

    global_configuration = cqp_tree.get_global_config()
    for provided_section, provided_values in provided_settings.items():
        if provided_section == 'null':
            provided_section = None
            active_namespace = global_configuration
        else:
            active_namespace = cqp_tree.get_frontend_configuration(provided_section, global_configuration)

        for key, value in provided_values.items():
            declared_config = cqp_tree.get_declared_configuration(key, provided_section)
            if declared_config is not None:
                setattr(active_namespace, key, declared_config.parse_value(value))
        configuration[provided_section] = active_namespace

    global_configuration.translator = translator
    return text, global_configuration, configuration


def to_json(plan: Recipe, configuration: cqp_tree.Configuration) -> dict:
    environment = associate_with_names(plan.identifiers(), UPPERCASE_ALPHABET)

    def convert(query: cqp_tree.Query) -> str:
        return cqp_tree.cqp_from_query(query, configuration).to_string(configuration)

    queries = {environment[query.identifier]: convert(query) for query in plan.queries}
    operations = {
        environment[operation.identifier]: {
            'lhs': environment[operation.lhs],
            'rhs': environment[operation.rhs],
            'op': operation.operator,
        }
        for operation in plan.operations
    }

    result: dict[str, Any] = {
        'recipe': {
            'queries': queries,
            'operations': operations,
            'goal': environment[plan.goal],
        }
    }
    if plan.has_simple_representation():
        result['single_query'] = convert(plan.simple_representation())
    if configuration.span:
        result['span'] = configuration.span
    return result
