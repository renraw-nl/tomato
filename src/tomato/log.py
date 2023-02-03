"""Logger

Setup the logger for output to the CLI (`stdout`). Output format depends on the
environment, either as a string or JSON dict.

Goal is to have output by this module using `structlog` similar to the stdlib
`logging` output.

SEE:
- https://github.com/madzak/python-json-logger
- https://www.structlog.org/en/stable/index.html

TODO:
- Clean up `type: ignore`,
- Clean up options for logging and level settings (`stdout`, but in: `json` or `rich`)
"""
import datetime
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Final

import structlog
from pythonjsonlogger.jsonlogger import JsonFormatter  # type: ignore

# Fallback values.
LOG_DT_FMT: Final[str] = "%Y-%m-%d %H:%M:%S"
LOG_LVL: Final[str] = "INFO"
LOG_FMT: Final[
    str
] = "%(timestamp)s [%(levelname)s] %(name)s: %(message)s (%(pathname)s:%(lineno)d)"
LOG_FILE: Final[Path] = Path.cwd() / datetime.datetime.today().strftime(
    f"{__package__} %Y-%m-%d.log"
)


class StuctlogJsonFormatter(JsonFormatter):  # type: ignore
    """JSON Formatter to have the output resember that of StructLog"""

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        """Ensure several fields are part of the JSON log to be recorded."""

        super(self.__class__, self).add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            log_record["timestamp"] = datetime.datetime.utcfromtimestamp(
                record.created
            ).strftime(LOG_DT_FMT)

        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname


def init(loglevel_name: str = "INFO", logfile: Path | None = None) -> None:
    """Set up the logger."""

    # No need to run this twice, so save a few cycles.
    if structlog.is_configured():
        return

    if logfile:
        logfile = Path(logfile).resolve()

    # get the default level or use the given one and convert it string to a level
    loglevel: int | None = None
    if loglevel_name:
        loglevel = loglevel_from_str(loglevel_name)

    # Check the level in case a the loglevel_name is not valid
    if not loglevel:
        loglevel = loglevel_from_str(LOG_LVL)

    timestamper = structlog.processors.TimeStamper(fmt=LOG_DT_FMT, utc=True)
    shared_processors: list[Any] = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        timestamper,
    ]

    if sys.stderr.isatty():
        _init_cli_logger(loglevel, shared_processors, logfile)
    else:
        _init_container_logger(loglevel, shared_processors, logfile)


def _init_cli_logger(
    loglevel: int, shared_processors: list[Any], logfile: Path | None
) -> None:
    """Setup logger for interactive command lines."""

    logconfig: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
                "foreign_pre_chain": shared_processors,
            },
        },
        "handlers": {
            "default": {
                "level": loglevel,
                "class": "logging.StreamHandler",
                "formatter": "colored",
            },
        },
        "loggers": {
            "": {
                "handlers": [
                    "default",
                ],
                "level": loglevel,
                "propagate": True,
            },
        },
    }

    if logfile:
        logconfig["formatters"]["plain"] = {
            "()": structlog.stdlib.ProcessorFormatter,
            "processors": [
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(colors=False),
            ],
            "foreign_pre_chain": shared_processors,
        }
        logconfig["handlers"]["file"] = {
            "level": loglevel,
            "class": "logging.handlers.WatchedFileHandler",
            "filename": logfile,
            "formatter": "plain",
        }
        logconfig["loggers"][""]["handlers"].append("file")

    logging.config.dictConfig(logconfig)

    shared_processors = [
        structlog.stdlib.add_log_level,
    ] + shared_processors

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _init_container_logger(
    loglevel: int, shared_processors: list[Any], logfile: Path | None
) -> None:
    """Setup logger for use in a container, ie wrapped in a program."""
    formatter = StuctlogJsonFormatter(LOG_FMT)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(loglevel)
    root_logger.addHandler(handler)

    shared_processors = [
        structlog.stdlib.add_log_level,
    ] + shared_processors

    structlog.configure(
        logger_factory=structlog.stdlib.LoggerFactory(),
        # logger_factory=structlog.BytesLoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(loglevel),
        cache_logger_on_first_use=True,
        context_class=dict,
        processors=shared_processors
        + [
            structlog.contextvars.merge_contextvars,
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
            # structlog.processors.JSONRenderer(serializer=json.dumps),
        ],
    )


def loglevel_from_str(loglevel: str) -> int | None:
    """Convert the level string to its integer."""
    return getattr(logging, loglevel, None)


def _extract_from_record(_: Any, __: Any, event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Extract thread and process names and add them to the event dict.
    """
    record = event_dict["_record"]
    event_dict["thread_name"] = record.threadName
    event_dict["process_name"] = record.processName

    return event_dict


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Helper to get an initialised logger."""
    if not structlog.is_configured():
        init()

    return structlog.get_logger(name)
