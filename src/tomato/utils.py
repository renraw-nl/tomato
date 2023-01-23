from types import GeneratorType
from typing import Any, Callable, Iterable, Iterator


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
