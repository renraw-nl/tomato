# import pytest

from tomato import utils


def test_first_in_loop():
    """Is the flag true for the first in the iteration?"""
    output = []
    for val, flag in utils.flag_first_in_loop(range(3)):
        output.append([val, flag])

    expected = [[0, True], [1, False], [2, False]]

    assert output == expected


def test_last_in_loop():
    """Is the flag true for the first in the iteration?"""
    output = []
    for val, flag in utils.flag_last_in_loop(range(3)):
        output.append([val, flag])

    expected = [[0, False], [1, False], [2, True]]

    assert output == expected


def test_ends_in_loop():
    """Is the flag true for the first in the iteration?"""
    output = []
    for val, flag in utils.flag_ends_in_loop(range(3)):
        output.append([val, flag])

    expected = [[0, True], [1, False], [2, True]]

    assert output == expected
