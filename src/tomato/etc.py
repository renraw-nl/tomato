"""Configuration

Loads several configuration parameters in a specific order. The first file sets the
basic values and the other files add new data or overwrites existing data.

Order of loading, and thus in reverse priority;
1. Defaults set in the `./var/etc/defaults.toml`,
2. `~/.tomato.toml` in the users home (`$HOME`) directory,
3. File defined with the `TOMATO_ETC_FILE` environmental variable.

`TOMATO_ETC_FILE` can be set in the terminal or loaded via the dotenv file
(`DOTENV_FILE`).
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Final

import dotenv
import structlog
import tomlkit

from .utils import loop_flag_first

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
    """Initiase and load configuration data."""
    global data

    if not isinstance(data, tomlkit.TOMLDocument) or reload:
        data = tomlkit.document()

    if fn := _load_dotenv(DOTENV_FILE):
        logger.debug(f"Loaded dotenv file: `{fn}`.")

    if not _load(data):
        logger.warning("No configuration data loaded, not even from the default file.")


def _load(data: tomlkit.TOMLDocument) -> bool:
    # Note that the order of the files here is important. The first is assumed to be
    # the defaults file. Files loaded after that, replace previously set
    # configuration values.
    files: set[Path] = _etc_files()

    for fn, first in loop_flag_first(files):
        if not fn.exists():
            if first:
                raise FileNotFoundError(
                    f"Unable to find default configuration data with: `{fn}`."
                )
            continue

        elif not os.access(fn, mode=os.R_OK):
            msg = f"Found the configuration file, but no permission to read it: `{fn}`."
            if first:
                raise PermissionError(msg)

            logger.warning(msg)
            continue

        # Found a file, read the data and merge it with previously loaded data
        with fn.open(mode="rb") as fp:
            etc_data = tomlkit.load(fp)

        data = data | etc_data

    return len(data) > 0


@lru_cache
def _load_dotenv(name: str) -> Path | bool:
    if fn := dotenv.find_dotenv(name):
        dotenv.load_dotenv(fn)
        return fn

    return False


def _etc_files() -> set[Path]:
    # Order of the files here prescribes the order in which they are loaded.
    # Start with the defaults file, next the user, then any environmental based file.
    files = [
        Path(DEFAULT_FILE).resolve(),
        Path(USER_FILE).expanduser().resolve(),
    ]

    if OS_ENV_KEY in os.environ:
        files.append(Path(os.environ.get(OS_ENV_KEY)).resolve())

    return set(files)


def write(to: Path) -> None:
    """Write configuration data to the given file."""

    if to.exists() and not os.access(to, mode=os.W_OK):
        raise PermissionError(
            f"No write permission to existing configuration file at: {to}."
        )
    elif to.parent.exists() and not os.access(to.parent, os.W_OK):
        raise PermissionError(
            "No write permission to the directory of the planned"
            f"configuration file: {to}."
        )
    elif to.parent.exists():
        raise FileNotFoundError(
            f"Directory for the configuration file does not exist: {to}"
        )

    tomlkit.dump(data, to, sort_keys=False)
