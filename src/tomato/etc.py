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
from pathlib import Path
from typing import Final

import dotenv
import structlog
import tomlkit

from tomato.utils import filter_paths

# Files where the configuration is expected.
DEFAULT_FILE: Final[str] = r"./var/etc/defaults.toml"
USER_FILE: Final[str] = r"~/.tomato.toml"
DOTENV_FILE: Final[str] = r".tomato.env"
OS_ENV_KEY: Final[str] = "TOMATO_ETC_FILE"
OS_ENV_KEY_SPLIT: Final[str] = ";"
DEFAULT_VALUE = object()

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

    found_files: list[Path] = _gather_files()
    found_data: tomlkit.TOMLDocument

    if not (filtered_files := filter_paths(*found_files)):
        logger.warning(
            "No configuration files found, not even the default file.",
            files=found_files,
        )

    elif not (found_data := _load_files(*filtered_files)):
        logger.warning(
            "No configuration data found from the found files.", files=filtered_files
        )

    else:
        logger.debug("Etc files loaded", files=filtered_files)

    if not data or reload or not isinstance(data, tomlkit.TOMLDocument):
        data = found_data
    else:
        data.update(found_data)


def _gather_files() -> list[Path]:
    """Get the config files in the order to load them, including dotenv files."""

    return [
        Path(DEFAULT_FILE),
        Path(USER_FILE),
        *_files_from_env(),
    ]


def _files_from_env(
    env_key: str = OS_ENV_KEY,
    dotenv_fn: str = DOTENV_FILE,
    split_on: str = OS_ENV_KEY_SPLIT,
) -> list[Path]:
    """
    Find `etc_key` with the location of a configuration file(s) to, eventually, load.

    To Note:
    * No check is done here if the file exists or not.
    * The dotenv file is __only__ loaded when the `env_key` has not been set in the
    environment. This to reduce disk look-ups and potentially polluting the scope.
    """

    env_value: str | None

    # Does it exist, if not try loading the dotenv file.
    if not (env_value := os.environ.get(env_key, None)):
        if env_value := _key_from_dotenv(dotenv_fn, env_key):
            logger.debug(
                "Found and loaded key from dotenv file",
                dotenv_fn=dotenv_fn,
                env_key=env_key,
                env_value=env_value,
            )
            os.environ[env_key] = env_value
        else:
            return []

    logger.debug(
        "Found key in environment variables",
        env_key=env_key,
        env_value=env_value,
    )

    # Split environmental key on `split_on`
    cfg_fns: list[Path] = []
    for fn in env_value.split(sep=split_on):
        cfg_fns.append(Path(fn.strip()))

    return cfg_fns


def _key_from_dotenv(dotenv_fn: str, env_key: str) -> str | None:
    """
    Load the `OS_ENV_KEY` from a dotenv file.

    The value is loaded directly into `os.environ`.
    """
    fn: Path | str | None

    # Find the dot env file
    if not (fn := dotenv.find_dotenv(dotenv_fn)):
        return None

    # Load the values
    c: dict[str, str | None] = dotenv.dotenv_values(fn, interpolate=True)

    # Check if the key is there or return `None`
    return c.get(env_key, None)


def _load_files(*files: Path) -> tomlkit.TOMLDocument:
    """Load configurations from multiple files."""

    loaded_data: tomlkit.TOMLDocument = tomlkit.document()
    for fn in files:
        loaded_data.update(_load_file(fn))

    return loaded_data


def _load_file(fn: Path) -> tomlkit.TOMLDocument:
    """Load configuration from one file."""

    with fn.open(mode="rb") as fp:
        return tomlkit.load(fp)


def write(to: Path) -> None:
    """Write configuration data to the given file."""

    try:
        with to.open(mode="wb") as fp:
            tomlkit.dump(data=data, fp=fp, sort_keys=False)  # type: ignore

    except PermissionError as e:
        if to.exists() and not os.access(to, mode=os.W_OK):
            logger.exception(
                "No write permission to existing configuration file.",
                etc_fn=to,
                e=e,
            )
        elif to.parent.exists() and not os.access(to.parent, os.W_OK):
            logger.exception(
                "No write permission to the directory of the planned."
                "configuration file.",
                etc_fn=to,
                e=e,
            )
        raise
    except FileNotFoundError as e:
        logger.exception(
            "Directory for the configuration file does not exist.",
            etc_fn=to,
            e=e,
        )
        raise


def get(*keys: str, default_value: ... = DEFAULT_VALUE) -> ...:
    """
    Return config value for a set of keys.

    Easier access to multiple tables like `data['logging']['level']`, which can be
    accessed by `get('logging', 'level')` or `get('logging.level')`.
    """

    # Check the keys, make sure it is not called empty
    if not keys:
        raise TypeError("Missing at least one required `key`.")

    elif len(keys) == 1 and isinstance(keys[0], str) and "." in keys[0]:
        # Check for dots in a the single passed `keys`, split on the dot
        keys = keys[0].split(".")

    # Prepare the data source
    d = data

    # Loop over the keys and try each one in succession on the previous key.
    for key in keys:
        if isinstance(key, str) and key.isdigit():
            key = int(key)

        try:
            d = d[key]

        except KeyError:
            # So if the key doesn't exist, return the default when passed.
            if default_value is not DEFAULT_VALUE:
                return default_value

            raise

    # Only return `d` when there were keys.
    if keys:
        return d

    # Return default otherwise
    return default_value
