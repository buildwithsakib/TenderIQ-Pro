"""
matcher.py
----------
Applies the three eligibility conditions to a tender's extracted PDF fields,
as defined in config.json:

    Condition 1: Item Category must contain "Manpower"
    Condition 2: MSE Relaxation for Years Of Experience and Turnover must equal "Yes"
    Condition 3: Name of states / UT for geographical presence must be either
                 "Maharashtra" or "Not Applicable"

A tender is selected only if ALL three conditions are true.
"""

from typing import Dict, Tuple

from core.logger import get_logger
from core.utils import normalize_text

logger = get_logger(__name__)


def is_matching_tender(extracted_fields: Dict[str, str], config: dict) -> Tuple[bool, str]:
    """
    Validate a tender's extracted fields against the configured rules.

    Args:
        extracted_fields: Dict returned by pdf_reader.extract_fields_from_pdf(),
            expected to contain 'item_category', 'mse_relaxation', and
            'geographical_states' keys.
        config: The loaded config.json dictionary, containing
            'allowed_item_category', 'mse_relaxation', and 'allowed_states'.

    Returns:
        A tuple of (matches: bool, reason: str). If matches is False, reason
        explains which condition(s) failed (useful for logging/debugging).
        If matches is True, reason is "All conditions satisfied".
    """
    failures = []

    # ------------------------------------------------------------------
    # Condition 1: Item Category must contain the required keyword
    # (e.g. "Manpower"), case-insensitive substring match.
    # ------------------------------------------------------------------
    required_category = normalize_text(config.get("allowed_item_category", "Manpower"))
    actual_category = normalize_text(extracted_fields.get("item_category", ""))

    condition_1 = bool(actual_category) and required_category in actual_category
    if not condition_1:
        failures.append(
            f"Item Category '{extracted_fields.get('item_category')}' does not contain "
            f"'{config.get('allowed_item_category', 'Manpower')}'"
        )

    # ------------------------------------------------------------------
    # Condition 2: MSE Relaxation must exactly equal the configured value
    # (default "Yes"), case-insensitive.
    # ------------------------------------------------------------------
    required_mse = normalize_text(config.get("mse_relaxation", "Yes"))
    actual_mse = normalize_text(extracted_fields.get("mse_relaxation", ""))

    condition_2 = actual_mse == required_mse
    if not condition_2:
        failures.append(
            f"MSE Relaxation '{extracted_fields.get('mse_relaxation')}' does not equal "
            f"'{config.get('mse_relaxation', 'Yes')}'"
        )

    # ------------------------------------------------------------------
    # Condition 3: Geographical state must be one of the allowed states
    # (default ["Maharashtra", "Not Applicable"]), case-insensitive match.
    # We check both exact match and substring match, since the PDF value
    # may include extra text like "Maharashtra, Not Applicable" for
    # multi-state tenders.
    # ------------------------------------------------------------------
    allowed_states = [normalize_text(s) for s in config.get("allowed_states", ["Maharashtra", "Not Applicable"])]
    actual_state_text = normalize_text(extracted_fields.get("geographical_states", ""))

    condition_3 = bool(actual_state_text) and any(
        allowed_state in actual_state_text for allowed_state in allowed_states
    )
    if not condition_3:
        failures.append(
            f"Geographical state '{extracted_fields.get('geographical_states')}' is not in "
            f"allowed list {config.get('allowed_states')}"
        )

    all_match = condition_1 and condition_2 and condition_3

    if all_match:
        return True, "All conditions satisfied"

    reason = "; ".join(failures)
    return False, reason
