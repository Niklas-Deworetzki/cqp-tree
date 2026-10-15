#!/usr/bin/env python3
"""
This utility program can be used to convert CONLLU files to VRT.
"""

import argparse
import re
from pathlib import Path
from typing import Iterable

from conllu import parse_incr
from conllu.parser import DEFAULT_FIELDS


def _no_parse(line: list[str], i: int) -> str:
    return line[i]


FIELD_PARSERS = {field: _no_parse for field in DEFAULT_FIELDS}

ESCAPE_SEQUENCES = [
    ('&', 'amp'),
    ('<', 'lt'),
    ('>', 'gt'),
    ('"', 'quot'),
]


def _escape(s: str) -> str:
    for orig, subst in ESCAPE_SEQUENCES:
        s = s.replace(orig, f'&{subst};')
    return s


def list_files(path: Path) -> Iterable[Path]:
    for file in path.iterdir():
        if file.is_dir():
            yield from list_files(file)
        elif file.suffix == '.conllu':
            yield file


def convert(src: Path, dst: Path, corpus_id: str):
    dst.parent.mkdir(parents=True, exist_ok=True)

    with dst.open('w') as d:
        print(f'<doc id={corpus_id}>', file=d)
        for file in list_files(src):
            with file.open('r') as f:
                for sentence in parse_incr(f, field_parsers=FIELD_PARSERS):
                    meta = ' '.join(
                        f'{key.replace(' ', '_')}="{_escape(value)}"' for key, value in sentence.metadata.items()
                    )
                    print(f'<s {meta}>', file=d)
                    for token in sentence:
                        columns = '\t'.join(token.values())
                        print(columns, file=d)
                    print('</s>', file=d)
        print('</doc>', file=d)


def main():
    parser = argparse.ArgumentParser(
        prog='verticalize.py',
        description='Turn .conllu files into the .vrt format accepted by Corpus Workbench.',
    )
    parser.add_argument(
        'source',
        help='The .conllu file to be converted.',
    )
    parser.add_argument(
        'destination',
        help='The .vrt file to be written.',
    )
    parser.add_argument(
        'corpus_id',
        help='A corpus id embedded in the output file.',
        nargs='?',
    )

    args = parser.parse_args()
    source = Path(args.source)
    destination = Path(args.destination)
    if not args.corpus_id:
        if match := re.match('UD_[a-zA-Z0-9]+-([a-zA-Z0-9]+)', source.name):
            corpus_id = match.group(1)
        else:
            raise ValueError('Missing required corpus id.')
    else:
        corpus_id = args.corpus_id

    convert(source, destination, corpus_id)


if __name__ == '__main__':
    main()
