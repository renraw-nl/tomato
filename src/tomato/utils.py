from collections.abc import Callable, Iterable, Iterator, Mapping
from pathlib import Path
from types import GeneratorType
from typing import Any


def flag_first_in_loop(loop_over: Iterable) -> Iterator[tuple[Any, bool]]:
    """Loop over an iterable and flag it is the __first__ in the loop."""
    it = iter(loop_over)
    first = next(it)

    yield first, True

    for val in it:
        yield val, False


def flag_last_in_loop(loop_over: Iterable) -> Iterator[tuple[Any, bool]]:
    """Loop over an iterable and flag it is the __last__ in the loop."""
    it = iter(loop_over)
    prev = next(it)

    for val in it:
        yield prev, False
        prev = val

    yield prev, True


def flag_ends_in_loop(loop_over: Iterable) -> Iterator[tuple[Any, bool]]:
    """Loop over an iterable and flag if it is either the __first or the last__."""
    it = iter(loop_over)
    first = next(it)

    yield first, True

    prev = next(it)
    for val in it:
        yield prev, False
        prev = val

    yield prev, True


def chain_callables(*functions: Callable) -> Callable:
    """Create a chain with callables.

    Each of the given functions is run in the passed order.

    RETURNS:
        A Callable which can be fed with an Iterable (List, Dict, Set, etc.) and runs
        all given functions over each element in that Iterable.
    """

    def run_link(function: Callable, generator: Iterable[Any]) -> Iterable[Any]:
        """Helper to pass the generator to the function."""
        for item in generator:
            result: Any = function(item)

            if isinstance(result, GeneratorType):
                yield from result
            else:
                yield result

    def run_all_on(generator: Iterable[Any]) -> Iterable[Any]:
        """Run all the functions in order over the passed Iterable."""

        for function in functions:
            generator = run_link(function, generator)

        return generator

    return run_all_on


def merge_dicts(d1: dict[str, Any], d2: dict[str, Any]) -> None:
    """
    Add dict `d2` to dict `d1`.

    From [poetry.utils.helper](https://github.com/python-poetry/poetry/blob/master/ \
        src/poetry/utils/helpers.py)
    """

    for k in d2.keys():
        if k in d1 and isinstance(d1[k], dict) and isinstance(d2[k], Mapping):
            merge_dicts(d1[k], d2[k])
        else:
            d1[k] = d2[k]


def expand_path(fn: Path) -> Path:
    """Expand and return and absolute path."""

    if fn.is_absolute():
        return fn

    return fn.expanduser().resolve()


def filter_paths(*files: Path | str) -> list[Path]:
    """Return a list of unique existing Paths."""

    fns: list = []
    for fn in files:
        try:
            fn = expand_path(fn)
        except AttributeError:
            # Done to prevent having to check if the instance is a Path object.
            fn = expand_path(Path(fn))

        if fn not in fns and fn.exists():
            fns.append(fn)

    return fns
