import unittest
from pathlib import Path
from typing import Optional
import subprocess

from tests.integration.common import TestedBackend, import_test_cases

CORPUS_PATH = Path('resources/cwb').resolve()


def run_cqp_query(query: str) -> int:
    cqp = subprocess.Popen(
        [
            'docker',
            'run',
            '--rm',
            '--volume',
            f'{CORPUS_PATH}:/corpora:ro',
            'ghcr.io/niklas-deworetzki/cwb:3.5',
            'cqpcl',
            '-D',
            'CQPTREE',
            query,
        ],
        stdout=subprocess.PIPE,
    )
    wc = subprocess.Popen(
        ['wc', '-l'],
        stdin=cqp.stdout,
        stdout=subprocess.PIPE,
    )

    return int(wc.stdout.readline())


def convert_query(query: str, translator: Optional[str] = None) -> str:
    command = [
        'cqp-tree',
        '--config',
        'resources/testing/configurations/testcorpus.toml',
        '--general.dialect',
        'Corpus Workbench',
        '--general.ud_mode',
        'true',
        '--span',
        's',
        '--query',
        query,
    ]
    if translator:
        command.append(translator)

    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout


class TestCWB(unittest.TestCase):

    def do_query(self, query: str, language: Optional[str] = None) -> int:
        translated_query = convert_query(query, translator=language)
        return run_cqp_query(translated_query)


import_test_cases(TestCWB, TestedBackend.CORPUS_WORKBENCH)
