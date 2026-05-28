import argparse
import sys
from contextlib import ExitStack
from pathlib import Path
from typing import Any, Iterable, Optional

import cqp_tree
from cqp_tree.utils import format_human_readable


def warn(msg: Any):
    print(msg, file=sys.stderr)


CONFIG_KEYS_WITH_EXPLICIT_CLI_FLAG = {'span', 'translator', 'profile'}


def _iterate_configurable_flags() -> Iterable[tuple[str, cqp_tree.DeclaredConfig]]:
    for section, cfg in cqp_tree.iterate_declared_configuration():
        if not (
            section == cqp_tree.GLOBAL_CONFIGURATION_SECTION
            and cfg.key in CONFIG_KEYS_WITH_EXPLICIT_CLI_FLAG
        ):
            yield f'{section or 'config'}.{cfg.key}', cfg


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='cqp-tree',
        description='Translate tree-style corpus queries to CQP queries.',
        add_help=False,
    )

    parser.add_argument(
        '--help',
        '-h',
        action='store_true',
        help='Show this message and exit.',
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Don\'t print a message when reading a query from standard input.',
    )
    parser.add_argument(
        '--output',
        '-o',
        metavar='FILE',
        help='Output file to which results are written. '
        'If omitted, results are printed to stdout instead.',
    )
    parser.add_argument(
        '--encoding',
        '-e',
        default='utf-8',
        metavar='ENC',
        help='Encoding used for reading and writing files.',
    )
    parser.add_argument(
        '--span',
        '-s',
        metavar='SPAN',
        help='Span attribute to which a query should be constrained.',
    )
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
    parser.add_argument(
        '--print-config',
        metavar='FILE',
        nargs="?",
        default=None,
        const=sys.stdout,
        help='Print a configuration value with the current configuration to the given file. '
        'Prints to stdout if no file is given.',
    )

    translator_names = sorted(cqp_tree.known_translators.keys())
    parser.add_argument(
        'translator',
        metavar='TRANSLATOR',
        help='The translator to choose. '
        'If not provided, a translator is determined automatically for each query.\n'
        'Supported options are: ' + ', '.join(translator_names),
        nargs='?',
        choices=translator_names,
    )

    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        '--file',
        '-f',
        metavar='FILE',
        help='Input file containing a query to translate.',
    )
    input_group.add_argument(
        '--query',
        '-q',
        metavar='STR',
        help='A query to translate.',
    )

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
    return parser


def get_input(args: argparse.Namespace) -> Optional[str]:
    if args.file:
        try:
            with open(args.file, 'r', encoding=args.encoding) as f:
                return f.read()
        except IOError as e:
            warn(f'Could not read input file {args.file}: {e}')
            return None

    elif args.query:
        return args.query

    else:
        if not args.quiet:
            warn('No input file specified. Reading from stdin instead.')
            warn('Press Ctrl+D once you finished typing your query.')
        return sys.stdin.read() or None


def translate(query_str: str, config: cqp_tree.Configuration) -> cqp_tree.Recipe | None:
    try:
        return cqp_tree.translate_input(query_str, config)
    except cqp_tree.UnableToGuessTranslatorError as translation_error:
        if translation_error.no_translator_matches():
            warn('Unable to determine translator: No translator accepts the query.')
        else:
            accepting_translators = format_human_readable(
                sorted(translation_error.matching_translators)
            )
            warn(f'Unable to determine translator: Query is accepted by {accepting_translators}')
    return None


def get_configuration(args: argparse.Namespace) -> cqp_tree.Configuration:
    if args.profile:
        cqp_tree.load_builtin_profile(args.profile)
    if args.config:
        cqp_tree.load_profile(Path(args.config))

    for key, cfg in _iterate_configurable_flags():
        value = getattr(args, key)
        if value is not None:
            cfg.put(value)

    cfg = cqp_tree.get_global_config()
    cfg.translator = args.translator if args.translator else None
    cfg.span = args.span if args.span else None
    return cfg


def main():
    parser = argument_parser()
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        return 0

    try:
        configuration = get_configuration(args)
    except ValueError as e:
        warn(f'Could not load configuration: {e}')
        return 1

    if args.list_profiles:
        for profile in cqp_tree.discover_builtin_profiles():
            print(profile)
        return 0

    if args.print_config:
        with (
            open(args.print_config, 'w', encoding=args.encoding)
            if isinstance(args.print_config, str)
            else args.print_config
        ) as dst:
            cqp_tree.print_profile_template(dst)
        return 0

    with ExitStack() as managed_resources:
        output = sys.stdout
        if args.output:
            try:
                output = managed_resources.enter_context(
                    open(args.output, 'w', encoding=args.encoding)
                )
            except IOError as e:
                warn(f'Could not write to output file {args.output}: {e}')
                return 1

        query_str = get_input(args)
        if query_str is None:
            return 1

        try:
            plan = translate(query_str, configuration.translator)
            if not plan:
                return 1

            for line in cqp_tree.format_plan(plan, configuration):
                output.write(line + '\n')

        except cqp_tree.ParsingFailed as parse_failure:
            warn('Query could not be parsed:')
            for error in parse_failure.errors:
                warn(error)
        except cqp_tree.NotSupported as not_supported:
            if not str(not_supported):
                warn('Query cannot be translated.')
            else:
                warn('Query cannot be translated: ' + str(not_supported))

        return 0


if __name__ == '__main__':
    sys.exit(main())
