import unittest
from pathlib import Path
from typing import Optional
import subprocess

from tests.integration.common import TestedBackend, import_test_cases

CORPUS_PATH = Path('resources/cwb').resolve()


def run_cqp_query(query: str) -> int:
    result = subprocess.run(
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

    print(query)

    count = 0
    for line in result.stdout:
        print(line)
    return count


def convert_query(query: str, translator: Optional[str] = None) -> str:
    command = [
        'cqp-tree',
        '--config',
        'resources/testing/configurations/testcorpus.toml',
        '--general.dialect',
        'Corpus Workbench',
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
