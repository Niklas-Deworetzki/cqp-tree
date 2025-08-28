import argparse
import sys
from contextlib import ExitStack
from typing import Any, Iterator

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
        help='Input file(s), each containing a query to translate.',
        action="extend",
        nargs="*",
        type=str,
    )
    input_group.add_argument(
        '--query',
        '-q',
        metavar='STR',
        help='One or more queries to translate.',
        action="extend",
        nargs="*",
        type=str,
    )

    return parser


def get_inputs(args: argparse.Namespace) -> Iterator[str]:
    if args.file:
        for filename in args.file:
            try:
                with open(filename, 'r', encoding=args.encoding) as f:
                    yield f.read()
            except IOError as e:
                warn(f'Could not read input file {filename}: {e}')
    elif args.query:
        yield from args.query

    else:
        warn('No input file specified. Reading from stdin instead.')
        yield from sys.stdin


def translate(args: argparse.Namespace, query_str: str) -> cqp_tree.ExecutionPlan | None:
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

        translated_queries = 0
        for query_str in get_inputs(args):
            try:
                plan = translate(args, query_str)
                if not plan:
                    continue

                if len(plan.queries) > 1:
                    warn(
                        'Multiple steps are necessary to translate this query. '
                        'This is not supported yet.'
                    )
                    continue

                query, *_ = plan.queries
                cqp = cqp_tree.cqp_from_query(query)
                output.write(str(cqp) + '\n')
                translated_queries += 1

            except cqp_tree.ParsingFailed as parse_failure:
                warn('Query could not be parsed:')
                for error in parse_failure.errors:
                    warn(error)
            except cqp_tree.NotSupported as not_supported:
                if not str(not_supported):
                    warn('Query cannot be translated.')
                else:
                    warn('Query cannot be translated: ' + str(not_supported))

        return 0 if translated_queries else 1


if __name__ == '__main__':
    sys.exit(main())
