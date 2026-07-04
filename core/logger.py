"""
logger.py
---------
Centralized logging configuration for the GeM Manpower Tender Scanner.

This module exposes a single function, `setup_logger`, which configures a
logger that writes simultaneously to:
    1. The console (so the user sees live progress), and
    2. A rotating log file under the `logs/` directory (for later review).

Every other module in this project should call `get_logger(__name__)` to
obtain a logger instance rather than configuring logging itself. This keeps
log formatting consistent across the whole application.
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# Internal flag so we only configure handlers once, even if setup_logger()
# is called multiple times (e.g. from multiple modules).
_LOGGER_CONFIGURED = False


def setup_logger(log_dir: str = "logs", log_file: str = "scanner.log", level=logging.INFO) -> None:
    """
    Configure the root logger for the entire application.

    Args:
        log_dir: Directory where the log file should be stored. Created if missing.
        log_file: Name of the log file.
        level: Logging level (default INFO).

    This should be called exactly once, near the start of main.py, before any
    other module logs a message.
    """
    global _LOGGER_CONFIGURED

    if _LOGGER_CONFIGURED:
        # Already configured (e.g. called twice) - do nothing further.
        return

    # Ensure the logs directory exists before attaching a file handler to it.
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Common formatter used by both console and file handlers.
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler - prints live progress to stdout.
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # Rotating file handler - keeps log files from growing unbounded.
    # Rotates at 5 MB, keeping 3 backups.
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    _LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a named logger. If the root logger has not yet been configured
    (setup_logger() not called), this falls back to a basic console-only
    configuration so modules never crash due to "no handlers found".

    Args:
        name: Usually __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.
    """
    if not _LOGGER_CONFIGURED:
        # Safety net: configure with defaults if nobody has called setup_logger yet.
        setup_logger()
    return logging.getLogger(name)
