import argparse

from cqp_tree.grew import query_from_grew
from cqp_tree.translation import cqp_from_query


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='cqp-tree',
        description='Translate tree-style corpus queries to CQP queries.',
    )
    parser.add_argument(
        'filename',
        help='input file containing the query to translate',
    )
    parser.add_argument(
        '--encoding',
        '-e',
        default='utf-8',
        metavar='ENC',
        help='encoding of the query file',
    )
    return parser


def main():
    args = argument_parser().parse_args()

    with open(args.filename, encoding=args.encoding) as f:
        query = query_from_grew(f.read())
        cqp = cqp_from_query(query)
        print(str(cqp))


if __name__ == '__main__':
    main()
