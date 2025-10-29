from typing import Any

from flask import Flask, jsonify, request, send_from_directory

import cqp_tree
from cqp_tree import Recipe
from cqp_tree.utils import UPPERCASE_ALPHABET, associate_with_names

server = Flask(__name__)


@server.route("/")
def main():
    return send_from_directory('static', 'index.html')


@server.route('/translators', methods=['GET'])
def get_translators():
    translators = sorted(cqp_tree.known_translators.keys())
    return jsonify(translators)


@server.route('/translate', methods=['POST'])
def translate():
    def error(message: str, status: int = 400):
        return jsonify({'error': message}), status

    def extract_request_data():
        translation_request = request.get_json()
        if translation_request is None or not isinstance(translation_request, dict):
            raise ValueError('Malformed request')

        if not 'text' in translation_request:
            raise ValueError('Missing required field "text"')

        text = translation_request['text']
        translator = translation_request.get('translator')
        if translator and translator not in cqp_tree.known_translators:
            raise ValueError('Unknown value for field "translator"')
        return text, translator

    try:
        text, translator = extract_request_data()
        plan = cqp_tree.translate_input(text, translator)

        if is_too_complex(plan):
            raise ValueError('Your query is too complex! Try using fewer tokens.')

        return jsonify(to_json(plan))

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


def to_json(plan: Recipe) -> dict:
    environment = associate_with_names(plan.identifiers(), UPPERCASE_ALPHABET)

    queries = {
        environment[query.identifier]: str(cqp_tree.cqp_from_query(query)) for query in plan.queries
    }
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
        result['single_query'] = str(cqp_tree.cqp_from_query(plan.simple_representation()))

    return result
