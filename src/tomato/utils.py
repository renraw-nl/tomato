from typing import Iterable


def loop_flag_first(loop_over: Iterable) -> tuple[..., bool]:
    """Loop over an iterable and flag it is the __first__ in the loop."""
    it = iter(loop_over)
    first = next(it)

    yield first, True

    for val in it:
        yield val, False


def loop_flag_last(loop_over: Iterable) -> tuple[..., bool]:
    """Loop over an iterable and flag it is the __last__ in the loop."""
    it = iter(loop_over)
    prev = next(it)

    for val in it:
        yield prev, False
        prev = val

    yield prev, True


def loop_flag_first_last(loop_over: Iterable) -> tuple[..., bool]:
    """Loop over an iterable and flag if it is either the __first or the last__."""
    it = iter(loop_over)
    first = next(it)

    yield first, True

    prev = next(it)
    for val in it:
        yield prev, False
        prev = val

    yield prev, True
    yield prev, True
