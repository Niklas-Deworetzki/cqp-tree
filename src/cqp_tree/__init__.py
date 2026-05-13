from cqp_tree.translation import *
from cqp_tree.configuration import *
from cqp_tree import frontends

DEFAULT_CONFIGURATIONS = [
    DeclaredConfig(
        key='translator',
        readable_name='Translator',
        readable_description='The translation unit to use.',
    ),
    DeclaredConfig(
        key='span',
        readable_name='Span',
        readable_description='Text span to which matched results are expanded. '
        'Affects precision of translation.',
        validation_type=str,
    ),
]

for cfg in DEFAULT_CONFIGURATIONS:
    declare_configuration(cfg, None)
