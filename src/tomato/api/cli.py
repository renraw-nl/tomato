"""
Tomato - a CLI for a timetracker application
"""
import os
from pathlib import Path

import structlog
import typer

import tomato

app: typer.Typer = typer.Typer(
    add_help_option=True,
    help=__doc__,
    add_completion=True,
    # no_args_is_help=True,
    invoke_without_command=True,
)


def _version_callback(value: bool) -> None:
    """Print version and stop."""

    if value:
        print(f"CLI API for '{tomato.__app_name__}', version: {tomato.__version__}")
        raise typer.Exit()


def _log_level_callback(value: str) -> str | None:
    """Typer callback for passed log level string."""

    if not value:
        # Fail quick on empties
        return None
    elif (
        isinstance(value, str)
        and (value := value.strip().upper())
        and tomato.log.loglevel_from_str(value)
    ):
        # A non-empty string matching a log level
        return value

    raise typer.BadParameter(
        "Verbose level should be one of `DEBUG`, `INFO`," "`WARNING`, `ERROR`. Exiting."
    )


def _log_file_callback(fn: str | Path) -> Path | None:
    """Typer callback for passed logfile."""

    if not fn:
        # Fail quick on empty arguments
        return None

    elif isinstance(fn, str) and (fn := fn.strip()):
        # A string and not an empty one.
        fn = Path(fn)

    if not isinstance(fn, Path):
        # Something was passed, but not resembling a Path
        raise typer.BadParameter(f'Log file: "{fn}" is not usable as a file path.')

    fn = fn.expanduser().resolve()
    dn = fn.parent

    if fn.exists() and not os.access(fn, os.W_OK):
        raise typer.BadParameter(
            f"Log file: {fn} exists, but is not writable. Exiting."
        )
    elif not dn.exists():
        raise typer.BadParameter(
            f"Directory for log file does not exist: {dn}. Exiting."
        )
    elif not os.access(dn, os.W_OK):
        raise typer.BadParameter(
            f"Directory for log file: {dn} exists, but is not writable. Exiting."
        )

    return fn


@app.callback()
def main(
    log: str = typer.Option(
        None,
        "--log",
        help="Set the log and verbosity level [DEBUG, INFO, WARNING, ERROR].",
        callback=_log_level_callback,
    ),
    logfile: Path = typer.Option(
        None,
        "--logfile",
        help="Log file to use, must be writable.",
        callback=_log_file_callback,
    ),
    version: bool = typer.Option(
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
    tomato.init(loglevel_name=log, logfile=logfile)

    logger: structlog.BoundLogger = structlog.get_logger(tomato.__app_name__)
    logger.debug("CLI initialised")
