import json
from dataclasses import dataclass
from math import log
from pathlib import Path
from typing import TypedDict

import itertools

import cqp_tree
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_ROOT = PROJECT_ROOT / 'resources' / 'evaluation' / 'results'


class MetaCharacteristics(TypedDict):
    regexes: int
    tokens: int
    edges: int
    permutations: int


class DataPoint(TypedDict):
    query: str
    expected: int
    results: int
    result_time: int
    translation: int
    translation_time: int
    meta: MetaCharacteristics


@dataclass
class Description:
    tag1: str
    tag2: str
    dialect: cqp_tree.CQPDialect


def _project(field: str, *ds: list[DataPoint], scale: float = 1.0) -> tuple[list[float], ...]:
    return tuple([q[field] / scale for q in d] for d in ds)


def _plot_scatter(d1: list[float], d2: list[float], what: str, description: Description):
    fig, ax = plt.subplots()
    ax.scatter(d1, d2, alpha=0.5, s=20)

    # Reference line
    all_values = d1 + d2
    bounds = [min(all_values), max(all_values)]
    ax.plot(bounds, bounds, "k--", alpha=0.6)

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_aspect('equal', adjustable='box')

    ax.set_xlabel(f'{what} {description.tag1} [ms]')
    ax.set_ylabel(f'{what} {description.tag2} [ms]')
    ax.set_title(f'{what}: {description.tag1} vs {description.tag2} ({description.dialect.value})')
    ax.grid(True, alpha=0.2)

    plt.tight_layout()
    plt.show()


def plot_translation_time(d1: list[DataPoint], d2: list[DataPoint], description: Description):
    a, b = _project('translation_time', d1, d2, scale=1e6)
    _plot_scatter(a, b, 'Translation time', description)


def plot_execution_time(d1: list[DataPoint], d2: list[DataPoint], description: Description):
    a, b = _project('result_time', d1, d2, scale=1e6)
    _plot_scatter(a, b, 'Execution time', description)


def plot_recall_vs_speedup(d1: list[DataPoint], d2: list[DataPoint], description: Description):
    time_a, time_b = _project('result_time', d1, d2)

    (expected,) = _project('expected', d1)
    results_a, results_b = _project('results', d1, d2)

    speedup = [log(ta / tb, 2) for ta, tb in zip(time_a, time_b)]
    recall_a = [res / ex for res, ex in zip(results_a, expected)]
    recall_b = [res / ex for res, ex in zip(results_b, expected)]

    recall_diff = [a - b for a, b in zip(recall_a, recall_b)]

    fig, ax = plt.subplots(figsize=(10, 7))

    # Four quadrants
    ax.axvspan(0, 100, ymin=0.5, ymax=1, color='green', alpha=0.08)
    ax.axvspan(-100, 0, ymin=0, ymax=0.5, color='red', alpha=0.08)
    ax.axvspan(-100, 0, ymin=0.5, ymax=1, color='orange', alpha=0.08)
    ax.axvspan(0, 100, ymin=0, ymax=0.5, color='orange', alpha=0.08)

    ax.scatter(speedup, recall_diff, alpha=0.5, s=20)

    ax.axhline(0, color='black', linewidth=1)
    ax.axvline(0, color='black', linewidth=1)

    ax.set_xlabel(f'Log₂ execution speedup ({description.tag1} / {description.tag2})')
    ax.set_ylabel(f'Recall difference ({description.tag1} - {description.tag2})')
    ax.set_title(f'Execution Speedup vs Recall Change ({description.dialect.value})')

    ax.grid(True, alpha=0.2)

    # Symmetric axes, with some padding
    x_limit = 1.1 * max(abs(s) for s in speedup)
    y_limit = 1.1 * max(abs(r) for r in recall_diff)

    ax.set_xlim(-x_limit, x_limit)
    ax.set_ylim(-y_limit, y_limit)

    plt.tight_layout()
    plt.show()


def _filter(ds: list[DataPoint]) -> list[DataPoint]:
    return [
        i for i in ds
        if i['meta']['permutations'] < 10
    ]

def generate_difference_report(dialect: cqp_tree.CQPDialect, *tags: str):
    for t1, t2 in itertools.combinations(tags, 2):
        t1_file = RESULTS_ROOT / f'{t1}-{dialect.name.lower()}.json'
        t2_file = RESULTS_ROOT / f'{t2}-{dialect.name.lower()}.json'

        with t1_file.open('r') as f1, t2_file.open('r') as f2:
            d1 = _filter(json.load(f1))
            d2 = _filter(json.load(f2))

            limit = min(len(d1), len(d2))
            d1, d2 = d1[:limit], d2[:limit]

            description = Description(t1, t2, dialect)
            plot_translation_time(d1, d2, description)
            plot_execution_time(d1, d2, description)
            plot_recall_vs_speedup(d1, d2, description)


generate_difference_report(cqp_tree.CQPDialect.SKETCH_ENGINE, 'permutations', 'prefix')
