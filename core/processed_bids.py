"""
processed_bids.py
-----------------
Manages a persistent JSON file (processed_bids.json) that keeps track
of Bid Numbers that have already been successfully processed.
Provides helper functions for loading, checking, and saving bid numbers.
"""

import json
import os
from typing import List

from core.logger import get_logger

logger = get_logger(__name__)

PROCESSED_BIDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "processed_bids.json")


def load_processed_bids() -> List[str]:
    """
    Load the list of already processed Bid Numbers from the JSON file.
    If the file does not exist, it is created with an empty list.

    Returns:
        List of Bid Number strings.
    """
    if not os.path.isfile(PROCESSED_BIDS_FILE):
        create_json_if_missing()

    try:
        with open(PROCESSED_BIDS_FILE, "r", encoding="utf-8") as f:
            bids = json.load(f)
        if not isinstance(bids, list):
            logger.warning("processed_bids.json does not contain a list. Resetting to empty list.")
            bids = []
            _save_bids(bids)
        return bids
    except (json.JSONDecodeError, IOError) as exc:
        logger.error("Failed to read processed_bids.json: %s. Starting with an empty list.", exc)
        # Corrupted file – recreate it
        create_json_if_missing()
        return []


def is_processed(bid_number: str) -> bool:
    """
    Check if a Bid Number is already in the processed list.
    """
    return bid_number in load_processed_bids()


def save_processed_bid(bid_number: str) -> None:
    """
    Add a Bid Number to the processed list and persist it to disk immediately.
    """
    bids = load_processed_bids()
    if bid_number not in bids:
        bids.append(bid_number)
        _save_bids(bids)
        logger.info("Saved processed bid: %s", bid_number)
    else:
        logger.debug("Bid %s already in processed list.", bid_number)


def _save_bids(bids: List[str]) -> None:
    """Internal helper to write the list to disk."""
    try:
        with open(PROCESSED_BIDS_FILE, "w", encoding="utf-8") as f:
            json.dump(bids, f, indent=4, ensure_ascii=False)
    except IOError as exc:
        logger.error("Could not write to processed_bids.json: %s", exc)


def create_json_if_missing() -> None:
    """
    Create the processed_bids.json file with an empty list if it doesn't exist.
    """
    if not os.path.isfile(PROCESSED_BIDS_FILE):
        _save_bids([])
        logger.info("Created processed_bids.json with empty list.")
