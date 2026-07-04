"""
utils.py
--------
Shared helper functions used across the GeM Manpower Tender Scanner project.

Responsibilities:
    - Loading and validating config.json
    - Ensuring required project folders exist
    - Safe file deletion (used to clean up downloaded PDFs)
    - Small text-normalization helpers used by the matcher and pdf_reader
"""

import json
import os
import time
import sys

from core.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str = "config.json") -> dict:
    """
    Load and parse the JSON configuration file.

    When running as a PyInstaller bundle (sys.frozen is True), the
    function automatically looks for config.json next to the .exe
    if the default path is used.

    Args:
        config_path: Path to config.json. If not provided, defaults to
                     'config.json' (relative to cwd or exe folder).

    Returns:
        A dictionary containing the configuration values.

    Raises:
        FileNotFoundError: If the config file does not exist.
        json.JSONDecodeError: If the config file is not valid JSON.
    """
    # --- Modification for PyInstaller ---
    if getattr(sys, 'frozen', False):
        # Running as compiled .exe – look next to the executable
        base_dir = os.path.dirname(sys.executable)
        # Only override if the user didn't provide an absolute path
        if not os.path.isabs(config_path):
            config_path = os.path.join(base_dir, config_path)
    # ------------------------------------

    if not os.path.isfile(config_path):
        logger.error("Configuration file not found at '%s'.", config_path)
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        try:
            config = json.load(f)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse config.json: %s", exc)
            raise

    logger.info("Configuration loaded successfully from '%s'.", config_path)
    return config


def ensure_directories(*paths: str) -> None:
    """
    Ensure that each given directory path exists, creating it (and any
    missing parent directories) if necessary.

    Args:
        *paths: One or more directory paths to create if missing.
    """
    for path in paths:
        os.makedirs(path, exist_ok=True)
        logger.debug("Ensured directory exists: %s", path)


def safe_delete_file(file_path: str, retries: int = 3, delay_seconds: float = 0.5) -> bool:
    """
    Safely delete a file from disk, retrying a few times in case the file
    is briefly locked (common right after a browser finishes writing a
    download to disk).

    Args:
        file_path: Path of the file to delete.
        retries: Number of attempts before giving up.
        delay_seconds: Delay between retry attempts.

    Returns:
        True if the file was deleted (or did not exist), False if deletion
        failed after all retries.
    """
    if not os.path.exists(file_path):
        # Nothing to delete - treat as success.
        return True

    for attempt in range(1, retries + 1):
        try:
            os.remove(file_path)
            logger.info("Deleted temporary file: %s", file_path)
            return True
        except OSError as exc:
            logger.warning(
                "Attempt %d/%d to delete '%s' failed: %s", attempt, retries, file_path, exc
            )
            time.sleep(delay_seconds)

    logger.error("Could not delete file after %d attempts: %s", retries, file_path)
    return False


def normalize_text(value: str) -> str:
    """
    Normalize a string for reliable comparison: strips leading/trailing
    whitespace, collapses internal whitespace/newlines, and lowercases it.

    Args:
        value: Raw string value.

    Returns:
        A normalized, lowercase string. Returns an empty string if input is None.
    """
    if value is None:
        return ""
    return " ".join(value.split()).strip().lower()


def clear_downloads_folder(download_dir: str) -> None:
    """
    Remove any leftover files inside the downloads directory. Useful to run
    once at startup so a previous crashed run doesn't leave stale PDFs that
    could be mistaken for a new download.

    Args:
        download_dir: Path to the downloads directory.
    """
    if not os.path.isdir(download_dir):
        return

    for filename in os.listdir(download_dir):
        file_path = os.path.join(download_dir, filename)
        if os.path.isfile(file_path):
            safe_delete_file(file_path)

    logger.info("Cleared stale files from downloads folder: %s", download_dir)