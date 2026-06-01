import argparse

from cqp_tree.configuration.configuration import *
from cqp_tree.configuration.profile import *

CONFIG_KEYS_WITH_EXPLICIT_CLI_FLAG = {'span', 'translator', 'profile'}


def configurable_flags_by_section(
    hidden_sections: Iterable[str] = frozenset(),
) -> Iterable[tuple[ConfigurationSection, Iterable[DeclaredConfig]]]:
    for section, entries in iterate_declared_configuration_sections():
        if section in hidden_sections:
            continue

        if section == GLOBAL_CONFIGURATION_SECTION:
            entries = [e for e in entries if e.key not in CONFIG_KEYS_WITH_EXPLICIT_CLI_FLAG]
        else:
            entries = list(entries)

        if entries:  # Don't display empty sections.
            yield section, entries


def _iterate_configurable_flags() -> Iterable[tuple[str, DeclaredConfig]]:
    for section, cfg in iterate_declared_configuration():
        if not (
            section == GLOBAL_CONFIGURATION_SECTION
            and cfg.key in CONFIG_KEYS_WITH_EXPLICIT_CLI_FLAG
        ):
            yield f'{section or 'config'}.{cfg.key}', cfg


def initialize_config_from_args(args: argparse.Namespace) -> Configuration:
    if args.profile:
        load_builtin_profile(args.profile)
    if args.config:
        load_profile(Path(args.config))

    for key, cfg in _iterate_configurable_flags():
        value = getattr(args, key)
        if value is not None:
            cfg.put(value)

    return get_global_config()


def add_default_flags_to_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        '--profile',
        metavar='PROFILE',
        help='Configuration profile to use when determining configuration defaults.',
    )
    parser.add_argument(
        '--list-profiles',
        action='store_true',
        help='List available profiles to choose from.',
    )
    parser.add_argument(
        '--config',
        '-c',
        metavar='FILE',
        help='Configuration file used to set configuration values. '
        'Values set via command line flags have priority over those from the configuration file.',
    )


def add_config_flags_group_to_parser(parser: argparse.ArgumentParser):
    configuration_group = parser.add_argument_group(
        title='Configuration options',
        description='List of available configuration options for this application. '
        'Configuration keys are of the form SECTION.KEY, where the SECTION describes on of the '
        'different parts or frontends of the application. Some configurations only apply to one '
        'of the frontends. Active configuration values are displayed after the configuration key.',
    )
    for key, cfg in _iterate_configurable_flags():
        configuration_group.add_argument(
            f'--{key}',
            help=cfg.readable_description,
            metavar=cfg.get() or cfg.metavar(),
        )
