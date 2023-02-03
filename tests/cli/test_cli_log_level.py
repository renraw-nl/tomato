import pytest
import typer

from tomato.api.cli import _log_level_callback


@pytest.mark.cli
@pytest.mark.parametrize("value", [None, False, "", 0])
def test_log_level_callback_without_value(value) -> None:
    """Check no errors are raised if there is no value"""

    assert _log_level_callback(value) is None


@pytest.mark.cli
@pytest.mark.parametrize(
    "value",
    [
        "debug",
        "info",
        "warning",
        "error",
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "WARN",
        "CRITICAL",
        " Debug ",
        " Warning",
        "Error ",
    ],
)
def test_log_level_callback_with_levels(value) -> None:
    """Test the known levels and expect an upper case and trimmed response."""

    assert _log_level_callback(value) == value.strip().upper()


@pytest.mark.cli
@pytest.mark.parametrize(
    "value",
    [
        "info2 ",
        "0",
        "40",
        "NOTSET",
        10,
        40.0,
    ],
)
def test_log_level_callback_faulty_input(value):
    """Check if a value is given, but not a level."""

    with pytest.raises(typer.BadParameter):
        assert _log_level_callback(value) is None
