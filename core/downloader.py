"""
downloader.py
-------------
Helper utilities for confirming that a file downloaded by the browser
(triggered in core/browser.py via `page.expect_download()`) has fully
finished writing to disk and is safe to open.

Even though Playwright's `download.save_as()` call blocks until the browser
reports the download as complete, we add an extra readiness check here as a
defensive measure: on some systems/antivirus setups a file can briefly be
present but still locked or partially flushed. This module polls the file
size until it stabilizes and is a valid, non-empty PDF before handing
control back to the caller.
"""

import os
import time

from core.logger import get_logger

logger = get_logger(__name__)


def wait_for_pdf_ready(file_path: str, timeout_seconds: float = 60, poll_interval: float = 0.5) -> bool:
    """
    Wait until the given file exists, is non-empty, and its size has
    stopped changing between two consecutive checks (indicating the write
    has finished), and that it begins with the PDF magic header.

    Args:
        file_path: Absolute or relative path to the downloaded PDF.
        timeout_seconds: Maximum time to wait before giving up.
        poll_interval: Seconds to sleep between size checks.

    Returns:
        True if the file appears fully written and is a valid PDF,
        False if the timeout was reached first or the file is invalid.
    """
    deadline = time.time() + timeout_seconds
    last_size = -1
    stable_checks = 0
    required_stable_checks = 2  # require size to be unchanged twice in a row

    while time.time() < deadline:
        if not os.path.exists(file_path):
            time.sleep(poll_interval)
            continue

        try:
            current_size = os.path.getsize(file_path)
        except OSError:
            time.sleep(poll_interval)
            continue

        if current_size > 0 and current_size == last_size:
            stable_checks += 1
        else:
            stable_checks = 0

        last_size = current_size

        if stable_checks >= required_stable_checks:
            if _is_valid_pdf_header(file_path):
                logger.debug("File is stable and valid PDF: %s (%d bytes)", file_path, current_size)
                return True
            else:
                logger.warning("File stabilized but does not look like a valid PDF: %s", file_path)
                return False

        time.sleep(poll_interval)

    logger.error("Timed out after %.1fs waiting for file to become ready: %s", timeout_seconds, file_path)
    return False


def _is_valid_pdf_header(file_path: str) -> bool:
    """
    Check that a file begins with the standard PDF magic bytes (%PDF-).

    Args:
        file_path: Path to the file to inspect.

    Returns:
        True if the file starts with the PDF signature, False otherwise
        (including if the file can't be read).
    """
    try:
        with open(file_path, "rb") as f:
            header = f.read(5)
        return header == b"%PDF-"
    except OSError as exc:
        logger.warning("Could not read header of '%s': %s", file_path, exc)
        return False
