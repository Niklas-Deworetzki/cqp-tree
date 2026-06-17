
# The dep_search Frontend

We support the dep_search query language as described in https://aclanthology.org/W17-0233/.

Tokens can be described in n different ways:
1. The special symbol `_` describes an arbitrary token
2. A (quoted) sequence of characters can be used to search for certain word-forms. Both `"cat"` and `cat` search for tokens with the wordform *cat*.
3. Searches for other annotations are done by explicitly writing key-value pairs, such as `upos=NOUN`
4. To negate the searched attribute, simply prefix a token with `!`, such as `!cat`, `!"cat"` or `!upos=NOUN`
5. Combinations of multiple annotations are expressed using `&` and `|`.

Dependencies are expressed using the `<` or `>` characters, depending on the direction of the dependency relation.
They can also be restricted to only certain dependency types and require the tokens to be in a certain order.
Here are a few examples:
- `walk < _` searches for the word *walk* appearing as the governor of a dependency relation.
- `walk > _` searches for occurrences where *walk* is governed by another token.
- `_ <nsubj _` finds relations of type *nsubj*.
- `cat >amod|>nmod _` finds cat with *amod* or *nmod* dependents

## Regular Expression Support

We extend the capabilities of dep_search to support regular expressions.
When searching for specific annotations, one writes for example `msd=VB.INF.AKT` to search for verbs in infinite active form using the [msd annotation](https://spraakbanken.gu.se/korp/markup/msdtags.html). 
However, when one does not care whether the verbs are active or passive infinitives, a regular expression can be useful instead, that simply looks for the "verbs in infinitive"-prefix of the annotation scheme.
To separate regular expressions from regular values, we require them to be quoted, like this:
`msd="VB.INF.*"`

# Unsupported Features

The following features are not supported:
- Universally-quantified queries (such as `(_ <nsubj _) -> (Person=3 <nsubj
 _)` finding sentences in which all subjects are in third person) are not supported.
- Queries using the `+` operator to combine multiple search results are not supported either.
- Currently, it is also not possible to search for absence or disjunction over dependencies.

When writing `NOUN` and `cat`, dep_search is able to distinguish tags from wordforms and decide which annotation layer is queried.
We don't support this feature (yet).
Consequently, both cases would result in `word=NOUN` and `word=cat`.
We also don't support the special case of `L=cat`, which uses *L* as an abbreviation of *lemma*.
Instead, annotations should always be fully qualified as key-value pairs.

