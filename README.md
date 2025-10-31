# CQP/Tree

![CI Pipeline](https://github.com/Niklas-Deworetzki/ctp/actions/workflows/automation.yml/badge.svg?branch=main)
![GitHub Tag](https://img.shields.io/github/v/tag/Niklas-Deworetzki/cqp-tree)
![GitHub License](https://img.shields.io/github/license/Niklas-Deworetzki/cqp-tree)

A framework to translate tree-style linguistic queries into sequential queries for use in [Sketch Engine](https://www.sketchengine.eu/), [Corpus Workbench](https://cwb.sourceforge.io/) or [Korp](https://spraakbanken.gu.se/korp).

## Installation

This module requires Python version 3.12 or higher to be installed.
Installation is possible using `pip`.

```shell
pip install cqp-tree
```

If you want to run the current development version, you can clone this repository and install the package locally.

```shell
git clone https://github.com/Niklas-Deworetzki/cqp-tree.git
cd cqp-tree
pip install .
```

## Get Started in the Browser

This package contains a local web-server.
Running it allows you to open a website in your browser which has a user-friendly translation interface available.

```shell
cqp-tree-web
```

Running this command will start the server locally.
Once it's started, click on the link displayed in your terminal or manually enter  http://localhost:5000 to start translating queries.
To stop the server again, press Ctrl and C in your terminal window.

## Translating Queries

The module provides an executable called `cqp-tree`.
It can translate different queries into a common CQP representation and offers the most control over the translation process.
Currently, the following other query-languages are (partially) supported:
1. [Grew-match](https://match.grew.fr/)
2. [deptreepy](https://github.com/aarneranta/deptreepy/tree/main)
3. [CoNLL-U](https://universaldependencies.org/format.html): this is not commonly intended as a query language, but (partial) trees in CoNLL-U format can be interpreted as queries. For details, see [conll_frontend.md](https://github.com/Niklas-Deworetzki/cqp-tree/blob/main/conll_frontend.md)

In order to translate a query, you can provide it either via the command line, as the contents of a file or by directly typing it out into the program:

```shell
cqp-tree deptreepy --query 'TREE_ (pos NN) (AND (pos JJ) (word a.*))'
```

```shell
cqp-tree grew --file resources/example.grew
```

The converted query is, by default, printed to the screen.
Using the `--output` flag you can specify a file to which it should be written to instead.

## Contributing

Feel free to add to this project.
Read [CONTRIBUTING.md](https://github.com/Niklas-Deworetzki/cqp-tree/blob/main/CONTRIBUTING.md) to get started.

