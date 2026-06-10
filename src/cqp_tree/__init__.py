from cqp_tree.translation import *
from cqp_tree.configuration import *
from cqp_tree import frontends

declare_configuration(
    GENERAL_CONFIG_SECTION,
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
        key='dialect',
        readable_name='CQP Dialect',
        readable_description='The version of the Corpus Query Protocol language to use.',
        validation_type=CQPDialect,
        default_value=CQPDialect.CWB,
    ),
)
declare_configuration(
    ANNOTATIONS_CONFIG_SECTION,
    DeclaredConfig(
        key='form',
        readable_name='Word form',
        readable_description='Name of the field encoding the surface word forms.',
        validation_type=str,
        default_value='word',
    ),
    DeclaredConfig(
        key='lemma',
        readable_name='Lemma',
        readable_description='Name of the field encoding lemmas.',
        validation_type=str,
        default_value='lemma',
    ),
    DeclaredConfig(
        key='upos',
        readable_name='Universal POS tag',
        readable_description='Name of the field (Universal) POS tags.',
        validation_type=str,
        default_value='pos',
    ),
    DeclaredConfig(
        key='xpos',
        readable_name='Language-specific/fine-grained POS tag',
        readable_description='Name of the field encoding language-specific or finer-grained POS '
        'tags, such as XPOS or MSD.',
        validation_type=str,
        default_value='msd',
    ),
    DeclaredConfig(
        key='feats',
        readable_name='Morphological features',
        readable_description='Name of the field encoding morphological features, '
        'such as Universal features.',
        validation_type=str,
        default_value='ufeats',
    ),
    DeclaredConfig(
        key='id',
        readable_name='Token ID',
        readable_description='Name of the field encoding the token ID',
        default_value='ref',
    ),
    DeclaredConfig(
        key='head',
        readable_name='Dependency head ID',
        readable_description='Name of the field encoding the token ID of a token\'s '
        'syntactic head',
        validation_type=str,
        default_value='dephead',
    ),
    DeclaredConfig(
        key='deprel',
        readable_name='Dependency relation',
        readable_description='Name of the field encoding relation labels.',
        validation_type=str,
        default_value='deprel',
    ),
)
