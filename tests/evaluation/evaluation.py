import argparse
import json
import time
from pathlib import Path
from typing import Callable

from tqdm import tqdm

import cqp_tree
from docker import Container

PROJECT_ROOT = Path(__file__).parent.parent.parent


def make_translator(dialect: cqp_tree.CQPDialect) -> Callable[[str], str]:
    config = get_config(dialect)

    def translator(query: str) -> str:
        recipe = cqp_tree.translate_input(query, config)
        translated = cqp_tree.parsed_to_cqp(recipe.simple_representation(), config)
        return translated.to_string(config)

    return translator


def get_config(dialect: cqp_tree.CQPDialect) -> cqp_tree.Configuration:
    config_file = PROJECT_ROOT / 'resources' / 'evaluation' / 'configurations' / 'evalcorpus.toml'
    config = cqp_tree.configuration_from_file(config_file)
    config.ud_mode = True
    config.dialect = dialect
    return config


class CWBDocker(Container):
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


TRANSLATORS = {dialect: make_translator(dialect) for dialect in cqp_tree.CQPDialect}
DOCKER_CONTAINERS = {
    cqp_tree.CQPDialect.CWB: CWBDocker,
    cqp_tree.CQPDialect.SKETCH_ENGINE: NoSkeDocker,
}


def main(dialect: cqp_tree.CQPDialect, tag: str) -> None:
    with open('queries-Talbanken-2.17.json') as f:
        queries = json.load(f)

    translator = TRANSLATORS[dialect]
    container = DOCKER_CONTAINERS[dialect]

    for data in tqdm(queries, desc='Translating'):
        before = time.perf_counter_ns()
        data['translation'] = translator(data['query'])
        data['translation_time'] = time.perf_counter_ns() - before

    try:
        with container() as docker:
            for data in tqdm(queries, desc='Executing'):
                if data['meta']['permutations'] < 10:
                    before = time.perf_counter_ns()
                    data['results'] = docker.get_result_count(data['translation'])
                    data['result_time'] = time.perf_counter_ns() - before
                else:
                    data['results'] = 1
                    data['result_time'] = 987654321
    finally:
        results_dir = PROJECT_ROOT / 'resources' / 'evaluation' / 'results'
        results_dir.mkdir(parents=True, exist_ok=True)
        with (results_dir / f'{tag}-{dialect.name.lower()}.json').open('w') as f:
            json.dump(queries, f, indent=2)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(

    )
    parser.add_argument(
        'tag'
    )
    parser.add_argument(
        'dialect'
    )

    args = parser.parse_args()
    main(cqp_tree.CQPDialect(args.dialect), args.tag)
