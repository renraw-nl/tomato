"""Configuration

Loads several configuration parameters in a specific order. The first file sets the
basic values and the other files add new data or overwrites existing data.

Order of loading, and thus in reverse priority;
1. Defaults set in the `./var/etc/defaults.toml`,
2. `~/.tomato.toml` in the users home (`$HOME`) directory,
3. File defined with the `TOMATO_ETC_FILE` environmental variable.

`TOMATO_ETC_FILE` can be set in the terminal or loaded via the dotenv file
(`DOTENV_FILE`).

TODO:
- Clean up `type: ignore`
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Final

import dotenv
import structlog
import tomlkit

from .utils import flag_first_in_loop

# Files where the configuration is expected.

DEFAULT_FILE: Final[str] = r"./var/etc/defaults.toml"
USER_FILE: Final[str] = r"~/.tomato.toml"
DOTENV_FILE: Final[str] = r".tomato.env"
OS_ENV_KEY: Final[str] = "TOMATO_ETC_FILE"

# Get the logger, note that configuration only takes place after
# the configuration is loaded.
logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

# The writable configuration container
data: tomlkit.TOMLDocument | None = None


def init(reload: bool = False) -> None:
    """Initiase and load configuration data.

    When called multiple times, the found data replaces any previously set information.
    When called with `reload=True`, all previously existing configuration data is
    replaced with the newly found information.
    """
    global data

    if fn := find_dotenv(DOTENV_FILE):
        logger.debug(f"Loaded dotenv file: `{fn}`.")

    if not (files := src_files()):
        logger.warning("No configuration files found, not even the default file.")

    elif not (found := load_files(files)):
        logger.warning("No configuration data found from the found files.", files=files)

    if not isinstance(data, tomlkit.TOMLDocument) or reload:
        data = found
    else:
        data = data | found


def load_files(files: list[Path]) -> tomlkit.TOMLDocument:
    """Load configurations from multiple files."""

    data = tomlkit.document()
    for fn, first in flag_first_in_loop(files):
        if not os.access(fn, mode=os.R_OK):
            msg: str = (
                f"Skipped configuration file, due to lack of read permission: `{fn}`."
            )
            if first:
                raise PermissionError(msg)

            logger.warning(msg)
            continue

        # Found a file, read the data and merge it with previously loaded data
        with fn.open(mode="rb") as fp:
            etc_data: tomlkit.TOMLDocument = tomlkit.load(fp)

        if etc_data:
            data = data | etc_data  # type: ignore

    return data


@lru_cache
def find_dotenv(name: str) -> Path | bool:
    """
    Find file with environmental info in the parents of the current working directory.
    """
    fn: str | Path

    if fn := dotenv.find_dotenv(name):
        if not isinstance(fn, Path):
            fn = Path(fn)

        dotenv.load_dotenv(fn)
        return fn

    return False


def src_files() -> list[Path]:
    """Gather expected configuration files.

    Uses `DEFAULT_FILE` and `USER_FILE`, as well as `OS_ENV_KEY` environmental variable
    to find the files.

    The order of files inserted into the `files`-list determines the order in which the
    files are read and its data loaded. Information in subsequent files takes precedence
    over previously loaded ones.
    """

    # Order of the files here prescribes the order in which they are loaded.
    # Start with the defaults file, next the user, then any environmental based file.
    files: list[Path] = [
        Path(DEFAULT_FILE).resolve(),
        Path(USER_FILE).expanduser().resolve(),
    ]

    if OS_ENV_KEY in os.environ:
        files.append(Path(os.environ.get(OS_ENV_KEY)).resolve())

    return filter(lambda fn: fn.exists(), set(files))


def write(to: Path) -> None:
    """Write configuration data to the given file."""

    if to.exists() and not os.access(to, mode=os.W_OK):
        raise PermissionError(
            f"No write permission to existing configuration file at: {to}."
        )
    elif (parent_exists := to.parent.exists()) and not os.access(to.parent, os.W_OK):
        raise PermissionError(
            "No write permission to the directory of the planned"
            f"configuration file: {to}."
        )
    elif not parent_exists:
        raise FileNotFoundError(
            f"Directory for the configuration file does not exist: {to}"
        )

    with to.open(mode="wb") as fp:
        tomlkit.dump(data=data, fp=fp, sort_keys=False)  # type: ignore
