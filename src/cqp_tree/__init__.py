from cqp_tree.translation import *
from cqp_tree.configuration import *
from cqp_tree import frontends

DEFAULT_CONFIGURATIONS = [
    DeclaredConfig(
        key='translator',
        readable_name='Translator',
        readable_description='The translation unit to use.',
        validation_options=sorted(known_translators),
    ),
    DeclaredConfig(
        key='span',
        readable_name='Span',
        readable_description='Text span to which matched results are expanded. '
        'Affects precision of translation.',
        validation_type=str,
    ),
    DeclaredConfig(
        key='profile',
        readable_name='Active profile',
        readable_description='Active profile to which matched results are expanded.',
    ),
    DeclaredConfig(
        key='dialect',
        readable_name='CQP Dialect',
        readable_description='The version of the Corpus Query Protocol language to use.',
        validation_type=CQPDialect,
        default_value=CQPDialect.CWB,
    ),
    DeclaredConfig(
        key='word',
        readable_name='Wordform annotation',
        readable_description='Name of the annotation layer encoding word forms.',
        validation_type=str,
        default_value='word',
    ),
    DeclaredConfig(
        key='lemma',
        readable_name='Lemma annotation',
        readable_description='Name of the annotation layer encoding word lemmas.',
        validation_type=str,
        default_value='lemma',
    ),
    DeclaredConfig(
        key='deprel',
        readable_name='Dependency type annotation',
        readable_description='Name of the annotation layer encoding dependency relation types.',
        validation_type=str,
        default_value='deprel',
    ),
    DeclaredConfig(
        key='dephead',
        readable_name='Dependency head annotation',
        readable_description='Name of the annotation layer encoding '
        'the dependency head of a token.',
        validation_type=str,
        default_value='dephead',
    ),
    DeclaredConfig(
        key='token_id',
        readable_name='Dependency identifier annotation',
        readable_description='Name of the annotation layer encoding encoding the id '
        'of a token that is matched by other token\'s dependency heads',
        default_value='ref',
    ),
]

declare_configurations(GLOBAL_CONFIGURATION_SECTION, DEFAULT_CONFIGURATIONS)
