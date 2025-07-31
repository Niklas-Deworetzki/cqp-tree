# CQP/Tree

![CI Pipeline](https://github.com/Niklas-Deworetzki/ctp/actions/workflows/automation.yml/badge.svg?branch=main)
![GitHub Tag](https://img.shields.io/github/v/tag/Niklas-Deworetzki/cqp-tree)
![GitHub License](https://img.shields.io/github/license/Niklas-Deworetzki/cqp-tree)

A framework to translate tree-style linguistic queries into sequential queries for use in [Sketch Engine](https://www.sketchengine.eu/), [Corpus Workbench](https://cwb.sourceforge.io/) or [Korp](https://spraakbanken.gu.se/korp).

## Installation

This module requires Python version 3.12 or higher to be installed.
Installation is possible by cloning this repository and running `pip install`.

```shell
git clone https://github.com/Niklas-Deworetzki/cqp-tree.git
pip install cqp-tree
```

## Translating Queries

The module provides one main executable called `cqp-tree`.
It can translate different queries into a common CQP representation.
Currently, the following other query-languages are (partially) supported:
1. [Grew-match](https://match.grew.fr/)
2. [deptreepy](https://github.com/aarneranta/deptreepy/tree/main)

In order to translate a query, you can provide it either via the command line, as the contents of a file or by directly typing it out into the program:

```shell
$ cqp-tree deptreepy --query 'TREE_ (pos NN) (AND (pos JJ) (word a.*))'
```

```shell
$ cqp-tree grew --file resources/example.grew
```

The converted query is, by default, printed to the screen.
Using the `--output` flag you can specify a file to which it should be written to instead.

## Contributing

Feel free to add to this project.
Read [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

