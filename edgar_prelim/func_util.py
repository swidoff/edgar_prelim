from typing import Optional, Iterable, Sequence


def optional(gen: Optional) -> Sequence:
    """Converts an optional into a single valued or empty list."""
    return [gen] if gen is not None else []


def collect_first(f, iterable: Iterable) -> Optional:
    """
    Applies f to each value in iterable until a non-null result is encountered, which is returned
    :return: The first non-None result of f, or None if f returns None for all values of iterable.
    """
    for v in iterable:
        res = f(v)
        if res is not None:
            return res
    return None


def head_option(iterable: Iterable) -> Optional:
    """Returns the first value of an Iterable, nor None if the Iterable is empty."""
    return collect_first(lambda x: x, iterable)
