from typing import Any

from flask import Flask, jsonify, request, send_from_directory

import cqp_tree

app = Flask(__name__)


@app.route("/")
def main():
    return send_from_directory('static', 'index.html')


@app.route('/translators', methods=['GET'])
def get_translators():
    translators = sorted(cqp_tree.known_translators.keys())
    return jsonify(translators)


@app.route('/translate', methods=['POST'])
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
        translated_query = cqp_tree.translate_input(text, translator)
        if translated_query.get_token_count() > 5:
            raise ValueError('Too many tokens. CQP will not be able to handle the resulting query.')
        query, additional_steps = cqp_tree.cqp_from_query(translated_query)

        result: dict[str, Any] = {'query': str(query)}
        if additional_steps:
            result['additional_steps'] = [
                {'operation': step.operation, 'query': str(step.query)} for step in additional_steps
            ]

        return jsonify(result)

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
        (parse_error,) = parse_error.errors
        return error('This query cannot be parsed: ' + parse_error.message)
