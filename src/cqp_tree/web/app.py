from typing import Any

from flask import Flask, jsonify, render_template, request
from timeout_decorator import timeout

import cqp_tree

app = Flask(
    __name__,
    static_url_path='',
    static_folder='static',
)


@app.route("/")
def main():
    return render_template('index.html')


@app.route('/translation', methods=['GET'])
def get_translators():
    translators = sorted(cqp_tree.known_translators.keys())
    return jsonify(translators)


@app.route('/translation', methods=['POST'])
@timeout(seconds=1)
def translate():
    def error(message: str, status: int = 400):
        return jsonify({'error': message}), status

    translation_request = request.get_json()
    if translation_request is None or not isinstance(translation_request, dict):
        return error('Malformed request', 422)

    if not 'text' in translation_request:
        return error('Malformed request', 422)

    text = translation_request['text']
    translator = translation_request.get('translator')
    if translator and translator not in cqp_tree.known_translators:
        return error('Missing required field "translator"', 422)

    try:
        query, additional_steps = cqp_tree.cqp_from_query(
            cqp_tree.translate_input(text, translator)
        )
        result: dict[str, Any] = {'query': str(query)}
        if additional_steps:
            result['additional_steps'] = [
                {'operation': step.operation, 'query': str(step.query)} for step in additional_steps
            ]

        return jsonify(result)

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
