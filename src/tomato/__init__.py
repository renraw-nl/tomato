"""
Tomato - a timetracker app with a CLI.
"""
from importlib.metadata import version
from pathlib import Path

import structlog

# Inmports of convenience
from . import etc  # noqa: F401
from . import log

# from . import times

__app_name__ = __package__
__version__ = version(__package__)


def init(loglevel_name: str | None = None, logfile: Path | None = None) -> None:
    """Setup the key parts

    PARTS:
        `etc`   : Configuration module
        `log`   : Logger
        `times` : Registered times
    """
    etc.init(reload=True)

    if not loglevel_name:
        loglevel_name = etc.data.get("logging.level", None)

    if not logfile:
        logfile = etc.data.get("logging.logfile", None)

    log.init(loglevel_name, logfile)
    # times.init(etc.data)
    # print(etc.data["tool"]["black"]["exclude"])

    structlog.get_logger().debug("Initialised", etc=etc.data)


# not further used, clean the scope
del version
