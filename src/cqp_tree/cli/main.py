import argparse
import sys
from contextlib import ExitStack
from typing import Any, Optional

import cqp_tree
from cqp_tree.utils import format_human_readable


def warn(msg: Any):
    print(msg, file=sys.stderr)


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

    translator_names = sorted(cqp_tree.known_translators.keys())
    parser.add_argument(
        'translator',
        metavar='TRANSLATOR',
        help='The translator to choose. '
        'If not provided, a translator is determined automatically for each query. '
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


def translate(args: argparse.Namespace, query_str: str) -> cqp_tree.Recipe | None:
    try:
        return cqp_tree.translate_input(query_str, args.translator or None)
    except cqp_tree.UnableToGuessTranslatorError as translation_error:
        if translation_error.no_translator_matches():
            warn('Unable to determine translator: No translator accepts the query.')
        else:
            accepting_translators = format_human_readable(
                sorted(translation_error.matching_translators)
            )
            warn(f'Unable to determine translator: Query is accepted by {accepting_translators}')
    return None


def main():
    parser = argument_parser()
    args = parser.parse_args()
    if args.help:
        parser.print_help()
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
            plan = translate(args, query_str)
            if not plan:
                return 1

            for line in cqp_tree.format_plan(plan, args):
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
