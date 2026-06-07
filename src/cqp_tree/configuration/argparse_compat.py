import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from cqp_tree.configuration.declaration import (
    DEFAULT_CONFIGURATION_SECTION,
    DeclaredConfig,
    iterate_declared_configurations,
)
from cqp_tree.configuration.values import (
    ActiveConfig,
    configuration_from_file,
)

CONFIG_KEYS_WITH_EXPLICIT_CLI_FLAG = {'span', 'translator'}


def configuration_from_args(args: argparse.Namespace, inherited: ActiveConfig) -> ActiveConfig:
    if args.config:
        config_file = Path(args.config)
        inherited = configuration_from_file(config_file, inherited)

    values: dict[str, dict[str, Any]] = defaultdict(dict)
    for section, key, cfg in _iterate_cli_configs():
        value = getattr(args, f'{section}.{key}')
        if value is not None:
            values[section][key] = cfg.parse_value(value)

    return ActiveConfig(inherited=inherited, sections=values)


def add_config_flag_to_parser(parser: argparse.ArgumentParser):
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
        description='List of available configuration options for this application. Configuration '
        'keys are of the form SECTION.KEY, where the SECTION describes on of the different parts '
        'or frontends of the application. Some configurations only apply to one of the frontends.',
    )
    for section, key, cfg in _iterate_cli_configs():
        configuration_group.add_argument(
            f'--{section}.{key}',
            help=cfg.readable_description,
            metavar=cfg.metavar(),
        )


def _iterate_cli_configs() -> Iterable[tuple[str, str, DeclaredConfig]]:
    for section, entries in iterate_declared_configurations():
        for entry in entries:
            if (
                section == DEFAULT_CONFIGURATION_SECTION
                and entry.key in CONFIG_KEYS_WITH_EXPLICIT_CLI_FLAG
            ):
                continue

            yield section, entry.key, entry
