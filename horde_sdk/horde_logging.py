import os
import sys
from typing import Any

from loguru import logger

# FIXME? This is more of an indev thing. I'd like a less confusing default.
verbosity = 17  # By default we show anything more significant than a progress log

error_levels = ["ERROR", "CRITICAL", "EXCEPTION", "TRACE"]


def set_logger_verbosity(count: int) -> None:
    """Set the verbosity of the logger."""
    global verbosity
    # The count comes reversed. So count = 0 means minimum verbosity
    # While count 5 means maximum verbosity
    # So the more count we have, the lowe we drop the versbosity maximum
    verbosity = 20 - (count * 10)


def is_stdout_log(record: dict[str, Any]) -> bool:
    """Filter for stdout logs levels."""
    return not record["level"].no < verbosity


def is_msg_log(record: dict[str, Any]) -> bool:
    """Filter for stdout logs levels."""
    return not record["level"].no < verbosity


def is_stderr_log(record: dict[str, Any]) -> bool:
    """Filter for stderr logs levels."""
    return not record["level"].name not in error_levels


def is_trace_log(record: dict[str, Any]) -> bool:
    """Filter for trace logs levels."""
    return not record["level"].name not in error_levels


handler_config = [
    {
        "sink": sys.stdout,
        "colorize": True,
        "filter": is_stdout_log,
    },
    {
        "sink": "logs/bridge.log",
        "level": "DEBUG",
        "colorize": False,
        # "filter": is_stdout_log, # FIXME: We may want to filter this at some point
        "retention": "2 days",
        "rotation": "3 hours",
    },
    {
        "sink": "logs/trace.log",
        "level": "TRACE",
        "colorize": False,
        "filter": is_trace_log,
        "retention": "3 days",
        "rotation": "1 days",
        "backtrace": True,
        "diagnose": True,
    },
]

PROGRESS_LOGGER_LABEL = "PROGRESS"
"""The label for request progress log messages. Less severity than INFO."""
COMPLETE_LOGGER_LABEL = "COMPLETE"
"""The label for 'request complete' log messages. Less severity than INFO."""

if os.getenv("HORDE_SDK_DISABLE_CUSTOM_SINKS"):
    PROGRESS_LOGGER_LABEL = "DEBUG"
    COMPLETE_LOGGER_LABEL = "INFO"
else:
    logger.level(COMPLETE_LOGGER_LABEL, no=18, color="<green>", icon="✅")
    logger.level(PROGRESS_LOGGER_LABEL, no=17, color="<cyan>", icon="⏳")

HORDE_SDK_LOG_VERBOSITY = os.getenv("HORDE_SDK_LOG_VERBOSITY")
if HORDE_SDK_LOG_VERBOSITY is not None:
    parsed_verbosity: int | None = None
    try:
        parsed_verbosity = int(HORDE_SDK_LOG_VERBOSITY)
    except ValueError:
        logger.warning("HORDE_SDK_LOG_VERBOSITY is not an integer. Ignoring.")
    if parsed_verbosity is not None:
        verbosity = parsed_verbosity

set_logger_handlers = os.getenv("HORDE_SDK_SET_DEFAULT_LOG_HANDLERS")

if set_logger_handlers:
    logger.configure(handlers=handler_config)
