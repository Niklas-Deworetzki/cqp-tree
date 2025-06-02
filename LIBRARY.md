
# Additional Documentation

This document outlines how the Python module can be used as a library to ***programatically*** convert queries.
This module supports:
1. Arbitrary tokens with predicates on their feature structures.
2. Dependencies between tokens.
3. Automatic re-ordering of predicates. 
4. Constraints on token order.



## How to Use

With this tool, you can build your query and automatically convert it into a query string for execution in Corpus Workbench.
Import this package, build an object, and call the `cqp_from_query` method, returning a CQP query with an according ***string*** representation.

```python
from cqp_tree import *

q = ...  # Build your query.
cqp_from_query(str(q))
```

## Tokens

A query consists of a collection of tokens, each of which have a unique identifier and some predicates on their feature structure.


```python
t1 = Token(
    Identifier(),
    Conjunction(
        Expression(
            Attribute(None, 'upos'), 
            "=", 
            Literal('"Verb"')
        ),
        Exists(
            Attribute(None, 'Tense')
        )
    )
)
q = Query(tokens=[t1])
```

This token would be represented in CQP as `[upos = "VERB" & Tense]`, a token acting as a *VERB* with a *Tense* present on its feature structure.
Here are some important details to note:
1. This library **does not** validate the query.
   It is your responsibility to make sure your data and query refer to the same annotations.
2. Attributes on other tokens can be referred to by providing that tokens identifier instead of `None` as the first argument in Attribute's constructor.


## Dependencies

We expect dependency relations to be annotated as `ref` and `dephead` fields on each token.
The `ref` field encodes a unique identifier for each token within a dependency tree.
The `dephead` field encodes the identifier of another token, from which a dependency points to the current one.

<p align="center">
  <img width="460" height="300" src="resources/example-tree.svg">
</p>

Consider the example tree shown.
It would be encoded as the following sequence of two tokens:

```
[lemma="The", ref="1", dephead="2", deprel="det"] 
[lemma="dog", ref="2", dephead="root", deprel="root"]
```

Adding dependency edges to a query is much easier than this, by simply providing a collection of Dependency objects:

```python
a = Identifier()
b = Identifier()

tokens = [Token(a), Token(b)]
dependencies = [
   Dependency(b, a)
]
q = Query(tokens=tokens, dependencies=dependencies)
```

Notice how this example shares a reference to the same Identifier instance in multiple places of the query.

## How Do I Know Where To Put Predicates?

While predicates on feature structures can be placed on tokens directly, it is also possible to add them as a kind of *"global constraint"*.
This tool will always figure out, where predicates can be placed and re-order them accordingly.

```python
a = Identifier()
b = Identifier()

tokens = [Token(a), Token(b)]
have_same_pos = Expression(
   Attribute(a, 'pos'),
   '=',
   Attribute(b, 'pos')
)
q = Query(tokens=tokens, predicates=[have_same_pos])
```

This query would find two tokens in the same sentence with the same part-of-speech tag.
Note again, how identifiers are referenced multiple times and how the expression specifies equality of attributes on two tokens referred to by two different identifiers.
