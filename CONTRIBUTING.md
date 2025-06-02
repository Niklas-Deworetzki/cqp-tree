# How to Contribute

## Development Tools

This project has an automated pipeline, running a linter and formatter to keep the code base clean.
It is recommended to install [Pylint](https://github.com/pylint-dev/pylint) the [Black Formatter](https://github.com/psf/black) to run these checks offline as well, so you don't have to push every time to see whether you pass the checks.

These 2 commands will run both tools on the source directory.

```shell
pylint src
black src
```

## Adding Your Own Translator

Adding a translator on your own is relatively easy.
Or at least only as complicated as you want it to be.
Our internal data structure handles re-ordering of tokens, predicates and token dependencies on its own.
The complicated part is to parse and convert another query language into the internal representation.
You might want to refer to [LIBRARY.md](LIBRARY.md) for some overview of the representation.

There are 3 ways your translator communicates with the overall framework:

1. A main function accepting a string and converting it into a `cqp_tree.translation.Query`.
This is where the magic happens.
Once your function is implemented, add it to the list of supported translators in [main.py](src/cqp_tree/cli/main.py).

2. Signaling that parsing failed.
As you will have to parse a string representation of your input language, it might happen that a user provides an invalid query.
In this case, you will have to communicate that your translator does not understand the source program.
This is simply done by raising a `cqp_tree.translation.ParsingFailed`.
A list of `InputError` in its constructor provides additional information to the user.

3. Signaling that something is not supported.
As we are translating into a rather limited, sequential query language, not all features will be supported.
If you recognize that a query makes use of some unsupported features (during parsing or later in the translation step),
just raise a `NotSupported` and add what it is that's not supported.
