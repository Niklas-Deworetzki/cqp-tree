# Integration Tests for CQP/Tree

This directory contains integration tests for [NoSketch Engine](https://github.com/Niklas-Deworetzki/cqp-tree/blob/main/tests/integration/test_noske.py)
and [Corpus Workbench](https://github.com/Niklas-Deworetzki/cqp-tree/blob/main/tests/integration/cwb.py).
These tests are based on a verticalized version of the [MaiBaam] corpus, which can be found in the [resources directory](https://github.com/Niklas-Deworetzki/cqp-tree/blob/main/resources/testing).

## Test Definition

All test cases are defined in [test-cases.yml](https://github.com/Niklas-Deworetzki/cqp-tree/blob/main/tests/integration/test-cases.yml).
They have the following structure:

```yaml
- description: Description of the behavior the test case tests.
  input: |
    A query in one of the query languages.
    By using | this field is allowed to span multiple lines.
  noske: [100, 102]   # The expected number of results for NoSketch Engine.
  cwb: [100, 101]     # The expected number of results for Corpus Workbench.
  translator: grew    # An optional field specifying which query language is used.
```

A list of numbers can be specified for the expected results, as query translation does not keep a fixed order of translated alternatives.
And apparently in NoSketch Engine, the order of alternatives matters when running a query.

## Tests for NoSketch Engine

The setup for NoSketch Engine uses the [ELTE-DH docker image](https://github.com/ELTE-DH/NoSketch-Engine-Docker).
The docker image is used to encode and index a corpus.
Then, a NoSketch Engine server is started, as well as a CQP/Tree server.
The integration test then navigates the CQP/Tree web client, translates a query and uses the NoSketch Engine integration to run the translated query against the server.
This web interaction is done using Playwright.

## Tests for Corpus Workbench

The setup for Corpus Workbench uses a [custom docker image](https://github.com/niklas-deworetzki/corpus-workbench-docker/pkgs/container/cwb).
This image provides the `cwb-encode` and `cwb-make` tools, which are used to encode the test corpus.
Then, the individual test cases run interacting via command line with CQP/Tree and `cqpcl`.
