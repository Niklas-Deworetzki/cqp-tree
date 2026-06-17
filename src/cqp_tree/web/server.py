from dataclasses import dataclass
from functools import total_ordering
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urlparse

from flask import Flask, jsonify, redirect, render_template, request, send_file

import cqp_tree
from cqp_tree import Configuration, DeclaredConfig, Recipe
from cqp_tree.utils import UPPERCASE_ALPHABET, associate_with_names
from cqp_tree.web.run_on_url import make_external_search_url

cqp_tree.declare_configuration(
    'web',
    DeclaredConfig(
        key='branding',
        readable_name='Branding',
        readable_description='Path or URL to an image which is displayed in the top-left corner.',
        validation_type=str,
    ),
    DeclaredConfig(
        key='homepage',
        readable_name='Homepage',
        readable_description='URL the user is redirected to when clicking on the branding logo.',
        validation_type=str,
    ),
    DeclaredConfig(
        key='baseurl',
        readable_name='Base URL',
        readable_description='An url pointing to the corpus system instance where queries '
        'are executed. You may use {query} and {corpus} as placeholders for user parameters.',
        validation_type=str,
    ),
    DeclaredConfig(
        key='system_name',
        readable_name='Name of the corpus system',
        readable_description='The name of the corpus system. Displayed in the "Run on {NAME}" link '
        'below the translation output in the UI, which enables users to directly run a '
        'translated query in the live corpus system.',
        validation_type=str,
        default_value='corpus',
    ),
    DeclaredConfig(
        key='corpus_configs',
        readable_name='Corpus configurations',
        readable_description='Path to the directory with configurations for known corpora.',
        validation_type=str,
    ),
    DeclaredConfig(
        key='allow_external_search',
        readable_name='Allow External Search',
        readable_description='Allows to run the translated query on another not '
        'pre-configured corpus. The corpus is provided as an URL, which is then automatically '
        'analyzed and transformed into a proper format.',
        validation_type=bool,
        default_value=False,
    ),
)

TEMPLATE_DIR = Path(__file__).parent / 'static'


def setup_server(config: Configuration) -> Flask:
    server = Flask(__name__, template_folder=str(TEMPLATE_DIR))

    @server.route('/', methods=['GET'])
    def index():
        return serve_index(config)

    @server.route('/branding', methods=['GET'])
    def branding():
        return serve_branding(config)

    @server.route('/translators', methods=['GET'])
    def translators():
        return jsonify(sorted(cqp_tree.known_translators.keys()))

    @server.route('/translate', methods=['POST'])
    def translate():
        return serve_translation(config)

    @server.route('/external_search', methods=['GET'])
    def external_search():
        return serve_external_search()

    @server.route('/about.html', methods=['GET'])
    def about():
        return serve_about(config)

    return server


@total_ordering
@dataclass(frozen=True, eq=True)
class PreconfiguredCorpus:
    corpus_id: str
    display_name: str
    config: Configuration

    @property
    def preselected(self):
        return self.config.preselected or False

    @property
    def preferred(self):
        return self.config.preferred or False

    def __lt__(self, other: 'PreconfiguredCorpus'):
        # Preferred corpora get priority, being displayed above the others.
        if self.preferred and not other.preferred:
            return True
        if not self.preferred and other.preferred:
            return False
        return self.display_name.casefold() < other.display_name.casefold()


def get_preconfigured_corpora(cfg: Configuration) -> Iterable[PreconfiguredCorpus]:
    if not cfg.corpus_configs:
        return

    path = Path(cfg.corpus_configs)
    for configuration_file in path.iterdir():
        config = cqp_tree.configuration_from_file(configuration_file)
        corpus_id = configuration_file.stem
        display_name = config.display_name or cfg.system_name or 'corpus'
        yield PreconfiguredCorpus(corpus_id, display_name, config)


def serve_index(config: Configuration):
    return render_template(
        'index.html',
        cfg=config,
        corpus_configs=sorted(get_preconfigured_corpora(config)),
        settings=cqp_tree.iterate_configurations_by_section(
            config,
            hidden_sections={'web'},
            hidden_entries={cqp_tree.GENERAL_CONFIG_SECTION: {'translator'}},
        ),
    )


def serve_about(config: Configuration):
    return render_template('about.html', cfg=config)


def serve_external_search():
    if 'url' not in request.args or 'query' not in request.args:
        return bad_request('Missing required query parameters "url" or "query".')

    url = unquote(request.args['url'])
    query = unquote(request.args['query'])
    try:
        search_url = make_external_search_url(url, query)
        return redirect(search_url)
    except Exception:
        return render_template(
            'external_search_not_possible.html',
            url=url,
        )


def serve_branding(config: Configuration):
    if config.branding:
        parsed_url = urlparse(config.branding)
        if parsed_url.scheme in ('http', 'https'):
            return redirect(config.branding)
        return send_file(config.branding)
    return '', 404


def serve_translation(config: Configuration):
    try:
        text, configuration = extract_request_data(config)
        plan = cqp_tree.translate_input(text, configuration)

        if is_too_complex(plan):
            raise ValueError('Your query is too complex! Try using fewer tokens.')

        return jsonify(to_json(plan, configuration))

    except ValueError as validation_error:
        return bad_request(str(validation_error), 422)

    except cqp_tree.UnableToGuessTranslatorError as unable_to_guess_translator:
        if unable_to_guess_translator.no_translator_matches():
            return bad_request(
                'This query cannot be translated. '
                'Try checking for syntax errors or manually select the query language.'
            )
        return bad_request(
            'This query is valid in multiple query languages. '
            'Please manually select the query language you intend.'
        )

    except cqp_tree.NotSupported as not_supported:
        return bad_request('This query is not supported: ' + str(not_supported))

    except cqp_tree.ParsingFailed as parse_error:
        parse_error = next(iter(parse_error.errors))
        return bad_request('This query cannot be parsed: ' + parse_error.message)


def is_too_complex(plan: Recipe) -> bool:
    if len(plan.queries) > 20:
        return True
    if any(len(query.tokens) > 5 for query in plan.queries):
        return True
    return False


def extract_request_data(config: Configuration) -> tuple[str, Configuration]:
    translation_request = request.get_json()
    if translation_request is None or not isinstance(translation_request, dict):
        raise ValueError('Malformed request')

    if not 'text' in translation_request:
        raise ValueError('Missing required field "text"')

    text = translation_request['text']
    translator = translation_request.get('translator')
    if translator and translator not in cqp_tree.known_translators:
        raise ValueError('Unknown value for field "translator"')

    provided_settings = translation_request.get('settings', {})

    # Build a new configuration scope, applying configuration requested from client
    request_config = Configuration(sections={}, inherited=config)
    for section, entries in cqp_tree.iterate_configurations_by_section(
        config, hidden_sections={'web'}
    ):
        for entry, _ in entries:
            provided_value = provided_settings.get(f'{section}.{entry.key}')
            if provided_value is not None:
                request_config[entry.key] = entry.parse_value(provided_value)

    request_config.translator = translator
    return text, request_config


def to_json(plan: Recipe, configuration: Configuration) -> dict:
    environment = associate_with_names(plan.identifiers(), UPPERCASE_ALPHABET)

    def convert(query: cqp_tree.Query) -> str:
        return cqp_tree.parsed_to_cqp(query, configuration).to_string(configuration)

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


def bad_request(message: str, status: int = 400):
    return jsonify({'error': message}), status
