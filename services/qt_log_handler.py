"""
qt_log_handler.py
-----------------
Bridges the backend's standard logging (configured in core/logger.py)
into the Qt UI.

Attach one QtLogHandler to the root logger; every log record is
re-emitted as a Qt signal and appended to the dashboard's live console.
Because the scan runs in a worker thread, the signal/slot connection is
automatically queued, making the console update thread-safe.
"""

import logging

from PySide6.QtCore import QObject, Signal


class LogEmitter(QObject):
    """Small QObject that owns the signal (handlers cannot be QObjects
    themselves because logging.Handler uses its own metaclass)."""

    message = Signal(str)


class QtLogHandler(logging.Handler):
    """logging.Handler that forwards formatted records to a Qt signal."""

    def __init__(self):
        super().__init__()
        self.emitter = LogEmitter()
        # Compact format for the on-screen console; the full format still
        # goes to logs/scanner.log via the backend's own file handler.
        self.setFormatter(logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%H:%M:%S",
        ))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.emitter.message.emit(self.format(record))
        except Exception:
            self.handleError(record)
