import argparse
import sys
from contextlib import ExitStack
from typing import Any, Callable, Iterator, Tuple

from cqp_tree.deptreepy import query_from_deptreepy
from cqp_tree.grew import query_from_grew
from cqp_tree.translation import NotSupported, ParsingFailed, Query, cqp_from_query
from cqp_tree.utils import format_human_readable


def warn(msg: Any):
    print(msg, file=sys.stderr)


TranslationFunction = Callable[[str], Query]

KNOWN_TRANSLATORS: dict[str, TranslationFunction] = {
    'deptreepy': query_from_deptreepy,
    'grew': query_from_grew,
}


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

    translator_names = sorted(KNOWN_TRANSLATORS.keys())
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


def guess_correct_translator(inp: str) -> Iterator[Tuple[str, Query]]:
    for name, function in KNOWN_TRANSLATORS.items():
        try:
            yield name, function(inp)
        except ParsingFailed:
            pass
        except NotSupported:
            pass


def translate(args: argparse.Namespace, query_str: str) -> Query | None:
    if args.translator:
        return KNOWN_TRANSLATORS[args.translator](query_str)
    else:
        guessed_queries = list(guess_correct_translator(query_str))
        if not guessed_queries:
            warn('Unable to determine translator: No translator accepts the query.')
            return None

        if len(guessed_queries) > 1:
            accepting_translators = format_human_readable(name for name, _ in guessed_queries)
            warn(f'Unable to determine translator: Query is accepted by {accepting_translators}')
            return None

        _, query = guessed_queries[0]
        return query


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
                query = translate(args, query_str)
                if query:
                    cqp = cqp_from_query(query)
                    translated_queries += 1
                    output.write(str(cqp) + '\n')
            except ParsingFailed as parse_failure:
                warn('Query could not be parsed:')
                for error in parse_failure.errors:
                    warn(error)
            except NotSupported as not_supported:
                if not str(not_supported):
                    warn('Query cannot be translated.')
                else:
                    warn('Query cannot be translated: ' + str(not_supported))

        return 0 if translated_queries else 1


if __name__ == '__main__':
    sys.exit(main())
