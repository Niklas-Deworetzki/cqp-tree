import argparse
from cqp_tree.web.server import server


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='cqp-tree-web',
        description='Translate tree-style corpus queries to CQP queries.',
        add_help=False,
    )

    parser.add_argument(
        '--help',
        action='store_true',
        help='Show this message and exit.',
    )
    parser.add_argument(
        '--host',
        '-h',
        metavar='HOST',
        help='The host to listen on.',
    )
    parser.add_argument(
        '--port',
        '-p',
        metavar='PORT',
        help='The port to bind to.',
    )
    parser.add_argument(
        '--debug',
        '-d',
        action='store_true',
        help='Enable debug mode.',
    )
    return parser


def main():
    parser = argument_parser()
    args = parser.parse_args()
    if args.help:
        parser.print_help()
    else:
        server.run(
            host=args.host or 'localhost',
            port=args.port or 5000,
            debug=args.debug,
        )


if __name__ == '__main__':
    main()
