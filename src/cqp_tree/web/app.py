import argparse
import errno
import sys

from waitress import serve

import cqp_tree
from cqp_tree.web.server import setup_server

DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 31495


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
    parser.add_argument(
        '--log',
        '-l',
        metavar='PATH',
        help='The path to write logs to.',
    )
    cqp_tree.add_config_flag_to_parser(parser)
    cqp_tree.add_config_flags_group_to_parser(parser)
    return parser


def main():
    parser = argument_parser()
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        return

    host = args.host or DEFAULT_HOST
    port = args.port or DEFAULT_PORT

    config = cqp_tree.configuration_from_args(args, cqp_tree.default_configuration())
    if args.log:
        config.log_path = args.log
    server = setup_server(config)
    if args.debug:
        server.run(host=host, port=port, debug=True)
    else:
        try:
            print(f'Starting local server on http://{host}:{port}')
            print('Press CTRL+C to quit.')
            serve(server, host=host, port=port, _quiet=False)
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                print(
                    'Starting the server failed. '
                    'Attempt using the --port option to try a different port.',
                    file=sys.stderr,
                )
            else:
                print(f'Starting the server failed: {e}', file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    main()
