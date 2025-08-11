# Translator Frontends

This directory contains the different supported frontends for the translation.
Their task is it to convert a query provided by a user as a string into a query object.
This conversion performs multiple necessary steps:

- parse the input string
- convert features from the input language into the internal data model
- detect and report unsupported (or untranslatable!) features.

## Build Your Own Frontend

Everything you need to build your own frontend is available in the `cqp_tree.translation` module.
As an example, consider the following code which represents an imaginary frontend.
The language it recognizes and supports is quite simple:
Given a number, a query for that many tokens should be created.

```python
import cqp_tree.translation as ct


@ct.translator('example')
def translate(inp: str) -> ct.Query:
    if not inp.isnumeric():
        syntax_error = ct.InputError(inp, 'Input contained non-numeric characters.')
        raise ct.ParsingFailed(syntax_error)

    how_many_tokens = int(inp)
    if how_many_tokens == 0:
        raise ct.NotSupported('Searching for no tokens is not supported!')

    tokens = [ct.Token(ct.Identifier()) for _ in range(how_many_tokens)]
    return ct.Query(tokens=tokens)
```

First, notice the decorator `@ct.translator`.
It marks your function as a translation function for your frontend.
There is nothing more to do.
A submodule within this directory containing a function with this decorator will automatically be recognized.
The CLI and the server will be able to access this function in order to translate 'example' type queries.

There are **2** types of errors that a frontend can recognize and report.
If there is a syntax error, a `ct.ParsingFailed` exception should be raised.
It is provided with encountered errors and their descriptions.
The error message(s) provided here will be shown to the user, so make sure to give useful errors!

The other error raised is a `ct.NotSupported`.
This indicates that a feature of your source language is just not supported.
Either, because it is a bit tricky and might come with a future extension.
Or because it simply cannot be represented in our simplistic data model.
Either way, it is good to give a meaningful explanation to the user here as well.
