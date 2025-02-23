from typing import Callable, Iterable, Tuple


def flatmap_set[X, Y](xs: Iterable[X], f: Callable[[X], Iterable[Y]]) -> set[Y]:
    result = set()
    for x in xs:
        result.update(f(x))
    return result


def partition_set[X](s: set[X], predicate: Callable[[X], bool]) -> Tuple[set[X], set[X]]:
    t, f = set(), set()
    for e in s:
        if predicate(e):
            t.add(e)
        else:
            f.add(e)
    return t, f


def to_str(strings: Iterable[str], prefix: str = '', sep: str = '', suffix: str = '') -> str:
    return prefix + sep.join(strings) + suffix
