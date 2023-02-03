import re

import pytest
import typer

from tomato import __app_name__, __version__
from tomato.api.cli import _version_callback


@pytest.mark.cli
@pytest.mark.parametrize("value", [None, False, "", 0])
def test_version_callback_without_value(value) -> None:
    """Test for empties."""

    assert _version_callback(value) is None


@pytest.mark.cli
@pytest.mark.parametrize(
    "value",
    [
        True,
        " ",
        1,
        "1",
        "0",
    ],
)
def test_version_callback_with_value(capsys, value):
    """Check output to include name and version, in that order."""
    re_stdout = re.compile(
        rf"\b{re.escape(__app_name__)}\b.+\b{re.escape(__version__)}\b", re.IGNORECASE
    )

    with pytest.raises(typer.Exit):
        _version_callback(value)

    out, err = capsys.readouterr()
    assert re_stdout.search(out) is not None
