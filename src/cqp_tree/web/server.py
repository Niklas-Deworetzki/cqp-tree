from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request, send_file

import cqp_tree
from cqp_tree import ActiveConfig, DeclaredConfig, Recipe
from cqp_tree.utils import UPPERCASE_ALPHABET, associate_with_names
from cqp_tree.configuration.values import read_corpus_config
from cqp_tree.web import autodiscovery

cqp_tree.declare_configuration(
    'web',
    DeclaredConfig(
        key='branding',
        readable_name='Branding',
        readable_description='Path to an image file which is displayed in the top-left corner.',
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
        readable_description='An url pointing to the the corpus system instance where queries '
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
        default_value='src/cqp_tree/configuration/corpus_configs'
    )
)

# https://www.clarin.si/ske/#concordance?tab=advanced&queryselector=cql&showresults=1&corpname=diccas_ar&cql=%5Bword%3D%22.*%22%5D

# https://www.clarin.si/ske/#concordance
# ?corpname=diccas_ar
# &tab=advanced
# &queryselector=cql
# &attrs=word
# &viewmode=kwic
# &attr_allpos=all
# &refs_up=0
# &shorten_refs=1
# &glue=1
# &gdexcnt=300
# &show_gdex_scores=0
# &itemsPerPage=20
# &structs=s%2Cg
# &refs=%3Dtext.type%2C%3Dtext.book_type
# &default_attr=lemma
# &cql=%5Bword%3D%22B.*%22%5D
# &showresults=1
# &showTBL=0
# &tbl_template=
# &gdexconf=
# &f_tab=basic
# &f_showrelfrq=1
# &f_showperc=0
# &f_showreldens=0
# &f_showreltt=0
# &c_customrange=0
# &t_attr=
# &t_absfrq=0
# &t_trimempty=1
# &t_threshold=5
# &operations=%5B%7B%22name%22%3A%22cql%22%2C%22arg%22%3A%22%5Bword%3D%5C%22B.*%5C%22%5D%22%2C%22query%22%3A%7B%22queryselector%22%3A%22cqlrow%22%2C%22cql%22%3A%22%5Bword%3D%5C%22B.*%5C%22%5D%22%2C%22default_attr%22%3A%22lemma%22%7D%2C%22id%22%3A7693%7D%5D

TEMPLATE_DIR = Path(__file__).parent / 'static'


def setup_server(config: cqp_tree.ActiveConfig) -> Flask:
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

    return server


def serve_index(config: ActiveConfig):
    cfg = config.project('web')
    return render_template(
        'index.html',
        cfg=cfg,
        corpus_configs=[(config_path, read_corpus_config(config_path)) for config_path in Path(cfg.corpus_configs).iterdir()],
        settings=cqp_tree.iterate_configurations_by_section(
            config,
            hidden_sections={'web'},
            hidden_entries={cqp_tree.DEFAULT_CONFIGURATION_SECTION: {'translator'}},
        ),
    )


def serve_branding(config: ActiveConfig):
    cfg = config.project('web')
    if cfg.branding:
        return send_file(cfg.branding)
    return '', 404


def serve_translation(config: ActiveConfig):
    def error(message: str, status: int = 400):
        return jsonify({'error': message}), status

    try:
        text, configuration = extract_request_data(config)
        plan = cqp_tree.translate_input(text, configuration)

        if is_too_complex(plan):
            raise ValueError('Your query is too complex! Try using fewer tokens.')

        format_config = configuration.project(cqp_tree.DEFAULT_CONFIGURATION_SECTION)
        return jsonify(to_json(plan, format_config))

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


def extract_request_data(config: ActiveConfig) -> tuple[str, ActiveConfig]:
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

    request_config = ActiveConfig(sections={}, inherited=config)
    for section, entries in cqp_tree.iterate_configurations_by_section(
        config, hidden_sections={'web'}
    ):
        for entry, _ in entries:
            provided_value = provided_settings.get(f'{section}.{entry.key}')
            if provided_value is not None:
                request_config.put(section, entry.key, provided_value)

    request_config.put(cqp_tree.DEFAULT_CONFIGURATION_SECTION, 'translator', translator)
    return text, request_config


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
