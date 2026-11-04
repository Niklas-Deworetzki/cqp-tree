import argparse
import json
import time
from pathlib import Path
from typing import Callable, Optional

from tqdm import tqdm

import cqp_tree
from docker import Container

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_ROOT = PROJECT_ROOT / 'resources' / 'evaluation' / 'results'
RESULTS_ROOT.mkdir(parents=True, exist_ok=True)


def make_translator(dialect: cqp_tree.CQPDialect) -> Callable[[str], str]:
    config = get_config(dialect)

    def translator(query: str) -> str:
        recipe = cqp_tree.translate_input(query, config)
        # All queries in the evaluation set can be translated into a single CQP query.
        translated = cqp_tree.parsed_to_cqp(recipe.simple_representation(), config)
        return translated.to_string(config)

    return translator


def get_config(dialect: cqp_tree.CQPDialect) -> cqp_tree.Configuration:
    config_file = PROJECT_ROOT / 'resources' / 'evaluation' / 'configurations' / 'evalcorpus.toml'
    config = cqp_tree.configuration_from_file(config_file)
    config.ud_mode = True
    config.dialect = dialect
    config.span = 's'
    return config


class CWBDocker(Container):
    """
    Docker container configuration for Corpus Workbench on the evaluation corpus.
    """

    def __init__(self):
        super().__init__(
            'ghcr.io/niklas-deworetzki/cwb:3.5',
            command='bash',
            mounts={(PROJECT_ROOT / 'resources' / 'cwb').absolute().as_posix(): '/corpora'},
        )

    def get_result_count(self, query: str) -> int:
        result = self.exec(
            'cqpcl',
            '-D',
            'EVALCORPUS',
            f'A = {query}; size A;',
        )
        return int(result.strip())


class NoSkeDocker(Container):
    """
    Docker container configuration for No Sketch Engine on the evaluation corpus.
    """

    def __init__(self):
        super().__init__(
            'eltedh/nosketch-engine:latest',
            mounts={(PROJECT_ROOT / 'resources' / 'evaluation').absolute().as_posix(): '/corpora'},
        )

    def get_result_count(self, query: str) -> int:
        result = self.exec(
            'corpquery',
            'evalcorpus',
            query,
            '-n',
        )
        return int(result.strip())


# Backend specific variables.
TRANSLATORS = {dialect: make_translator(dialect) for dialect in cqp_tree.CQPDialect}
DOCKER_CONTAINERS = {
    cqp_tree.CQPDialect.CWB: CWBDocker,
    cqp_tree.CQPDialect.SKETCH_ENGINE: NoSkeDocker,
}


def run_evaluation(
    dialect: cqp_tree.CQPDialect, tag: str, number: Optional[int], cutoff: Optional[int]
) -> None:
    with open('queries-Talbanken-2.17.json') as f:
        queries = json.load(f)
    if number is not None:
        queries = queries[:number]

    translator = TRANSLATORS[dialect]
    container = DOCKER_CONTAINERS[dialect]

    for data in tqdm(queries, desc='Translating'):
        before = time.perf_counter_ns()
        data['translation'] = translator(data['query'])
        data['translation_time'] = time.perf_counter_ns() - before

    try:
        with container() as docker:
            for data in tqdm(queries, desc='Executing'):
                if cutoff is None or data['meta']['permutations'] <= cutoff:
                    before = time.perf_counter_ns()
                    data['results'] = docker.get_result_count(data['translation'])
                    data['result_time'] = time.perf_counter_ns() - before
    finally:
        with (RESULTS_ROOT / f'{tag}-{dialect.name.lower()}.json').open('w') as f:
            json.dump(queries, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="""
Evaluate performance of CQP/Tree backends.
This is done by running a fixed test set of queries, measuring translation time, execution time
and number of results in comparison with the expected number of results.
        """.strip(),
    )
    parser.add_argument(
        'tag',
        help='A tag used to identify the generated dataset.',
    )
    parser.add_argument(
        'dialect',
        help='The CQP dialect (backend) to be evaluated.',
    )
    parser.add_argument(
        '--number',
        type=int,
        help='The number of queries to be evaluated. If none is given, the entire query set will be used.',
    )
    parser.add_argument(
        '--cutoff',
        type=int,
        help='A limit on how complex the evaluated queries are. Queries resulting in more than CUTOFF '
        'permutations will be skipped from evaluation.',
    )

    args = parser.parse_args()
    run_evaluation(cqp_tree.CQPDialect(args.dialect), args.tag, args.number, args.cutoff)


if __name__ == '__main__':
    main()
