from typing import Annotated, Callable, Iterable, Sequence, Tuple

type NonEmpty[T] = Annotated[Sequence[T], 'Non empty Sequence of T.']


def flatmap_set[X, Y](xs: Iterable[X], f: Callable[[X], Iterable[Y]]) -> set[Y]:
    result = set()
    for x in xs:
        result.update(f(x))
    return result


def partition_set[X](s: set[X], predicate: Callable[[X], bool]) -> Tuple[set[X], set[X]]:
    """
    Partitions a set into two sets using the given predicate.
    """
    t, f = set(), set()
    for e in s:
        if predicate(e):
            t.add(e)
        else:
            f.add(e)
    return t, f


def to_str(strings: Iterable[str], prefix: str = '', sep: str = '', suffix: str = '') -> str:
    """
    Creates a string from all the elements separated using separator and
    using the given prefix and postfix if supplied.
    """
    return prefix + sep.join(strings) + suffix


def format_human_readable(strings: NonEmpty[str]) -> str:
    """
    Returns a human-readable representation of a list of strings,
    separating the first values by a comma and the last one with "and".
    """
    if len(strings) == 1:
        return strings[0]
    else:
        initial = ', '.join(strings[:-1])
        last = strings[-1]
        return f'{initial} and {last}'
