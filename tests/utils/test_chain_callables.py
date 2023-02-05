"""Test utils"""

import pytest

from tomato import utils


@pytest.mark.utils
def test_callable_chain_basic() -> None:
    """Basic usage."""

    chain = utils.chain_callables(sq, plus)
    output = list(chain(range(5)))
    expected = [1, 2, 5, 10, 17]

    assert output == expected


@pytest.mark.utils
def test_callable_chain_complexer() -> None:
    """Slightly more complex."""

    chain = utils.chain_callables(twice, duplicate)
    output = list(chain([0, 1, 2, "a", "b", "c"]))
    expected = [0, 0, 2, 2, 4, 4, "aa", "aa", "bb", "bb", "cc", "cc"]

    assert output == expected


@pytest.mark.utils
def test_callable_chain_raise() -> None:
    """Check raising an Exception."""

    n = 10
    chain = utils.chain_callables(throw_exception)
    with pytest.raises(FakeError):
        _ = list(chain(range(n)))


def sq(x: int) -> int:
    """Test helper: square"""
    return x * x


def plus(x: int) -> int:
    """Test helper: add 1"""
    return x + 1


def twice(x: int | str) -> int | str:
    """Test helper: times two"""
    return x * 2


def duplicate(x: int | str) -> int | str:
    """Test helper: return the same entry again"""
    yield x
    yield x


def throw_exception(x: int | str) -> int | str:
    """Test helper: Raise an error"""
    raise FakeError
    return x


class FakeError(Exception):
    """Test helper: A Fake exception"""

    pass
