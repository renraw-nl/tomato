"""
Tomato - a timetracker application
"""
import os
from pathlib import Path
from typing import Optional

import structlog
import typer

import tomato

app = typer.Typer(
    add_help_option=True,
    help=__doc__,
    add_completion=True,
    # no_args_is_help=True,
    invoke_without_command=True,
)


def _version_callback(value: bool) -> None:
    if value:
        print(f"CLI API for: {tomato.__app_name__}.{tomato.__version__=}")
        raise typer.Exit()


def _log_level(value: str) -> str:
    if not tomato.log.loglevel_from_str(value):
        raise typer.BadParameter(
            "Verbose level should be one of `DEBUG`, `INFO`,"
            "`WARNING`, `ERROR`. Exiting."
        )

    return value


def _log_file(fn: str | Path) -> Path | None:
    if not fn:
        return None

    if not isinstance(fn, Path):
        fn = Path(fn)

    fn = fn.expanduser().resolve()
    dn = fn.parent
    if fn.exists() and not os.access(fn, os.W_OK):
        raise typer.BadParameter(
            f"Log file: {fn} exists, but is not writable. Existing."
        )
    elif not dn.exists():
        raise typer.BadParameter(
            f"Directory for log file does not exist: {dn}. Existing."
        )
    elif not os.access(dn, os.W_OK):
        raise typer.BadParameter(
            f"Directory for log file: {dn} exists, but is not writable. Existing."
        )

    return fn


@app.callback()
def main(
    log: Optional[str] = typer.Option(
        "INFO",
        "--log",
        help="Set the log and verbosity level [DEBUG, INFO, WARNING, ERROR].",
        callback=_log_level,
    ),
    logfile: Optional[Path] = typer.Option(
        None,
        "--logfile",
        help="Log file to use, must be writable.",
        callback=_log_file,
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        help="Print version information and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Main CLI entry point.

    This callback is always run before any command.
    """
    tomato.init(loglevel=log, logfile=logfile)

    logger: structlog.BoundLogger = structlog.get_logger(tomato.__app_name__)
    logger.debug("CLI initialised")
