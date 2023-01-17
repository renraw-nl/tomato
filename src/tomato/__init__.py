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


def init(loglevel: str = "INFO", logfile: Path = None) -> None:
    """Setup the key parts

    PARTS:
        `etc`   : Configuration module
        `log`   : Logger
        `times` : Registered times
    """
    etc.init()
    log.init(etc.data, loglevel, logfile)
    # times.init(etc.data)

    structlog.get_logger().debug("Initialised")


# not further used, clean the scope
del version
