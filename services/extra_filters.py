"""
extra_filters.py
----------------
Additional eligibility checks (experience and turnover) applied on top
of the unchanged core/matcher.py result.

The values are read directly from the bid PDF text with tolerant
patterns. A missing field never causes a rejection - only an explicit
requirement above the user's declared capability does. Semantics:

    required_experience_years = what the USER has; tenders demanding
        more are rejected. 0 disables the check.
    required_turnover_lakhs   = the USER's annual turnover in lakhs;
        tenders demanding more are rejected. 0 disables the check.
"""

import re
from typing import Tuple

import fitz

from core.logger import get_logger

logger = get_logger(__name__)

EXPERIENCE_PATTERN = re.compile(
    r"Years?\s*of\s*Past\s*Experience\s*Required[^0-9]{0,40}([0-9]+)",
    re.IGNORECASE,
)
TURNOVER_PATTERN = re.compile(
    r"(?:Minimum\s*Average\s*)?Annual\s*Turnover[^0-9]{0,60}"
    r"([0-9][0-9,\.]*)\s*(Lakh|Lac|Crore)?",
    re.IGNORECASE,
)


def _pdf_text(pdf_path: str) -> str:
    """Return the full text of the PDF, or an empty string on failure."""
    try:
        with fitz.open(pdf_path) as doc:
            return "\n".join(page.get_text() for page in doc)
    except Exception as exc:
        logger.warning("extra_filters: could not read '%s': %s", pdf_path, exc)
        return ""


def check_extra_requirements(pdf_path: str, config: dict) -> Tuple[bool, str]:
    """Apply experience and turnover filters against the bid PDF.

    Returns (True, "") when the tender passes (or the checks are
    disabled / the fields are absent), or (False, reason) otherwise.
    """
    user_experience = int(config.get("required_experience_years", 0) or 0)
    user_turnover = float(config.get("required_turnover_lakhs", 0) or 0)

    if user_experience <= 0 and user_turnover <= 0:
        return True, ""

    text = _pdf_text(pdf_path)
    if not text:
        # No text means nothing to check against - do not reject blindly.
        return True, ""

    if user_experience > 0:
        match = EXPERIENCE_PATTERN.search(text)
        if match:
            needed = int(match.group(1))
            if needed > user_experience:
                return False, (f"Tender requires {needed} year(s) experience, "
                               f"filter allows up to {user_experience}")

    if user_turnover > 0:
        match = TURNOVER_PATTERN.search(text)
        if match:
            value = float(match.group(1).replace(",", ""))
            unit = (match.group(2) or "Lakh").lower()
            needed_lakhs = value * 100.0 if unit.startswith("crore") else value
            if needed_lakhs > user_turnover:
                return False, (f"Tender requires turnover {needed_lakhs:g} Lakhs, "
                               f"filter allows up to {user_turnover:g} Lakhs")

    return True, ""
