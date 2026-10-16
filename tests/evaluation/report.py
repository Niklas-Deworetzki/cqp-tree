import argparse
import itertools
import json
from dataclasses import dataclass
from math import log
from pathlib import Path
from typing import TypedDict

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import cqp_tree

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


def _plot_scatter(
    d1: list[float],
    d2: list[float],
    what: str,
    description: Description,
    lower_is_better: bool,
):
    fig, ax = plt.subplots(figsize=(6, 6))

    equal_X, equal_Y = [], []
    d1_better_X, d1_better_Y = [], []
    d2_better_X, d2_better_Y = [], []

    for (v1, v2) in zip(d1, d2):
        if v1 == v2:
            equal_X.append(v1)
            equal_Y.append(v2)
        elif v1 > v2:
            d1_better_X.append(v1)
            d1_better_Y.append(v2)
        else:
            d2_better_X.append(v1)
            d2_better_Y.append(v2)

    if lower_is_better:
        d1_better_X, d2_better_X = d2_better_X, d1_better_X
        d1_better_Y, d2_better_Y = d2_better_Y, d1_better_Y

    ax.scatter(
        d1_better_X,
        d1_better_Y,
        color='orange',
        alpha=0.5,
        s=20,
        label=f'{description.tag1} better',
    )

    ax.scatter(
        d2_better_X,
        d2_better_Y,
        color='purple',
        alpha=0.5,
        s=20,
        label=f'{description.tag2} better',
    )

    ax.scatter(
        equal_X,
        equal_Y,
        color='gray',
        alpha=0.5,
        s=20,
    )

    # Reference line
    all_values = d1 + d2
    bounds = [min(all_values), max(all_values)]
    ax.plot(bounds, bounds, "k--", alpha=0.6)

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_aspect('equal', adjustable='box')

    ax.set_xlabel(f'{description.tag1} {what}')
    ax.set_ylabel(f'{description.tag2} {what}')
    ax.set_title(f'{what}: {description.tag1} vs {description.tag2} ({description.dialect.value})')
    ax.grid(True, alpha=0.2)
    ax.legend()

    plt.tight_layout()
    plt.show()


def plot_translation_time(d1: list[DataPoint], d2: list[DataPoint], description: Description):
    a, b = _project('translation_time', d1, d2, scale=1e6)
    _plot_scatter(a, b, 'Translation time', description, lower_is_better=True)


def plot_execution_time(d1: list[DataPoint], d2: list[DataPoint], description: Description):
    a, b = _project('result_time', d1, d2, scale=1e6)
    _plot_scatter(a, b, 'Execution time', description, lower_is_better=True)


def plot_recall(d1: list[DataPoint], d2: list[DataPoint], description: Description):
    (expected,) = _project('expected', d1)
    a, b = _project('results', d1, d2, scale=1e6)

    recall_a = [res / ex for res, ex in zip(a, expected)]
    recall_b = [res / ex for res, ex in zip(b, expected)]
    _plot_scatter(recall_a, recall_b, 'Recall', description, lower_is_better=False)


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

    # Legend explaining quadrant colors
    legend_elements = [
        Patch(
            facecolor='green',
            alpha=0.25,
            label=f'{description.tag2} is better',
        ),
        Patch(
            facecolor='red',
            alpha=0.25,
            label=f'{description.tag1} is better',
        ),
    ]
    ax.legend(handles=legend_elements, loc='best')

    plt.tight_layout()
    plt.show()


def _filter(d1: list[DataPoint], d2: list[DataPoint]) -> tuple[list[DataPoint], list[DataPoint]]:
    r1, r2 = [], []
    for i1, i2 in zip(d1, d2):
        if 'result_time' in i1 and 'result_time' in i2:
            r1.append(i1)
            r2.append(i2)
    return r1, r2


def generate_difference_report(dialect: cqp_tree.CQPDialect, *tags: str):
    for t1, t2 in itertools.combinations(tags, 2):
        t1_file = RESULTS_ROOT / f'{t1}-{dialect.name.lower()}.json'
        t2_file = RESULTS_ROOT / f'{t2}-{dialect.name.lower()}.json'

        with t1_file.open('r') as f1, t2_file.open('r') as f2:
            d1, d2 = _filter(json.load(f1), json.load(f2))

            limit = min(len(d1), len(d2))
            d1, d2 = d1[:limit], d2[:limit]

            description = Description(t1, t2, dialect)
            plot_translation_time(d1, d2, description)
            plot_execution_time(d1, d2, description)
            plot_recall(d1, d2, description)
            plot_recall_vs_speedup(d1, d2, description)


generate_difference_report(cqp_tree.CQPDialect.CWB, 'permutations', 'prefix')
generate_difference_report(cqp_tree.CQPDialect.SKETCH_ENGINE, 'permutations', 'linear')

def main():
    parser = argparse.ArgumentParser(
        description='Generates diagrams to compare evaluation results.'
    )
    parser.add_argument(
        'dialect',
        help='The CQP dialect (backend) evaluated.',
    )
    parser.add_argument(
        'tags',
        nargs='+',
        help='References to evaluation data to compare. All given tags will be compared against each other.',
    )

    args = parser.parse_args()
    try:
        dialect = cqp_tree.CQPDialect(args.dialect)
        generate_difference_report(dialect, *args.tags)
    except ValueError as e:
        print(f'Invalid dialect: {args.dialect}. Supported options are:')
        for dialect in cqp_tree.CQPDialect:
            print(' ' + dialect)
