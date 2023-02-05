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
- Provide dotted get/set() methods
"""

import os
from itertools import chain
from pathlib import Path
from typing import Final

import dotenv
import structlog
import tomlkit

from tomato.utils import merge_dicts

# Files where the configuration is expected.

DEFAULT_FILE: Final[str] = r"./var/etc/defaults.toml"
USER_FILE: Final[str] = r"~/.tomato.toml"
DOTENV_FILE: Final[str] = r".tomato.env"
OS_ENV_KEY: Final[str] = "TOMATO_ETC_FILE"

# Get the logger, note that configuration only takes place after
# the configuration is loaded.
logger: structlog.stdlib.BoundLogger = structlog.getLogger(__name__)

# The writable configuration container
data: tomlkit.TOMLDocument = None


def init(reload: bool = False) -> None:
    """
    Initiase and load configuration data.

    When called multiple times, the found data replaces any previously set information.
    When called with `reload=True`, all previously existing configuration data is
    replaced with the newly found information.
    """
    global data

    dotenv_fn: Path | None = env_etc_file(DOTENV_FILE)
    files: list[Path]
    found: tomlkit.TOMLDocument

    if not (files := etc_files(dotenv_fn)):
        logger.warning("No configuration files found, not even the default file.")

    elif not (found := load_etc_files(files)):
        logger.warning("No configuration data found from the found files.", files=files)

    else:
        logger.debug("Etc files", files=files)

    if not data or reload or not isinstance(data, tomlkit.TOMLDocument):
        data = found
    else:
        merge_dicts(data, found)


def load_etc_files(files: list[Path]) -> tomlkit.TOMLDocument:
    """Load configurations from multiple files."""

    loaded_data: tomlkit.TOMLDocument = tomlkit.document()
    for fn in files:
        try:
            with fn.open(mode="rb") as fp:
                fn_data: tomlkit.TOMLDocument = tomlkit.load(fp)

        except PermissionError:
            logger.warning(
                "Skipped configuration file due to lack of read permission", file=fn
            )
            continue

        # Found a file, read the data and merge it with previously loaded data
        merge_dicts(loaded_data, fn_data)

    return loaded_data


def env_etc_file(name: str) -> Path | None:
    """
    Find `OS_ENV_KEY` with a reference to a configuration file to load.

    The dotenv file should provide a `OS_ENV_KEY`, of which its value is than used as a
    configuration file. The file is loaded with `override=False` so prevent overloading
    variables set by the environment.
    """
    fn: str | Path

    if fn := dotenv.find_dotenv(name):
        fn = Path(fn)

        dotenv.load_dotenv(fn, override=False)
        logger.debug("Found and loaded dotenv file", name=name, fn=fn)

    if OS_ENV_KEY in os.environ:
        cfg_fn: str = os.environ.get(OS_ENV_KEY)
        logger.debug(
            "Found `OS_ENV_KEY` in environment variables",
            os_env_key=OS_ENV_KEY,
            value=cfg_fn,
        )

        return Path(cfg_fn)

    return None


def etc_files(*extra_files: Path) -> list[Path]:
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
        Path(DEFAULT_FILE),
        Path(USER_FILE),
    ]

    fns: list = []
    for fn in chain(files, extra_files):
        try:
            fn = fn.expanduser().resolve()
        except AttributeError:
            continue

        if fn not in fns and fn.exists():
            fns.append(fn)

    return fns


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
