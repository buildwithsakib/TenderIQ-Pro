"""
pdf_reader.py
-------------
Reads a downloaded GeM bid PDF and extracts required fields.
Address extraction: captures the Beneficiary block until the next marker.
"""

import re
from typing import Dict
import fitz
from core.logger import get_logger

logger = get_logger(__name__)
NOT_FOUND = ""


def _extract_text(pdf_path: str) -> str:
    text_parts = []
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text_parts.append(page.get_text())
    except Exception as exc:
        logger.error("Failed to read PDF '%s': %s", pdf_path, exc)
        return ""
    full_text = "\n".join(text_parts)
    full_text = re.sub(r"[ \t]+", " ", full_text)
    return full_text


def _search_field(pattern: str, text: str, flags=re.IGNORECASE | re.DOTALL) -> str:
    match = re.search(pattern, text, flags)
    if not match:
        return NOT_FOUND
    value = match.group(1).strip()
    value = value.split("\n")[0].strip()
    return value


def _extract_address(text: str) -> str:
    """
    Capture the address from the Beneficiary block.
    It reads all lines after 'Beneficiary :' up to (but not including)
    the line that contains either 'MII Compliance' or 'MSE Purchase Preference'.
    """
    # Start marker: Beneficiary line (English with optional Hindi prefix)
    # End markers: either MII Compliance or MSE Purchase Preference (both with Hindi prefixes)
    pattern = (
        r"(?:\u0932\u093e\u092d\u093e\u0930\u094d\u0925\u0940\s*/\s*)?Beneficiary\s*:\s*"
        r"(.+?)"
        r"(?=\n.*?(?:\u090f\u092e\u0906\u0908\u0906\u0908\s*\u0905\u0928\u0941\u092a\u093e\u0932\u0928/MII\s*Compliance|\u090f\u092e\u090f\u0938\u0908\s*\u0916\u0930\s*\u0926\s*\u0935\u0930\s*\u092f\u0924\u093e/MSE\s*Purchase\s*Preference))"
    )
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""

    raw = match.group(1).strip()
    # Split into lines, clean each, and rejoin with comma-space
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return ", ".join(lines)


def extract_fields_from_pdf(pdf_path: str) -> Dict[str, str]:
    text = _extract_text(pdf_path)
    if not text:
        logger.warning("No text in PDF: %s", pdf_path)
        return {
            "bid_number": NOT_FOUND, "dated": NOT_FOUND, "bid_end_date": NOT_FOUND,
            "item_category": NOT_FOUND, "mse_relaxation": NOT_FOUND,
            "geographical_states": NOT_FOUND, "address": NOT_FOUND,
            "contract_period": NOT_FOUND,
        }

    fields = {
        "bid_number": _search_field(r"Bid\s*Number\s*[:\-]?\s*(GEM/[A-Za-z0-9/\-\.]+)", text),
        "dated": _search_field(r"\bDated\s*[:\-]?\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})", text),
        "bid_end_date": _search_field(r"Bid\s*End\s*Date(?:/Time)?\s*[:\-]?\s*([0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4}(?:\s+[0-9:]+)?)", text),
        "item_category": _search_field(r"Item\s*Category\s*[:\-]?\s*([^\n]+)", text),
        "mse_relaxation": _search_field(r"MSE\s*Relaxation\s*for\s*Years?\s*Of\s*Experience\s*and\s*Turnover\s*[:\-]?\s*([A-Za-z]+)", text),
        "geographical_states": _search_field(r"Name\s*of\s*states?\s*/?\s*UT\s*for\s*geographical\s*presence\s*is\s*required\s*[:\-]?\s*([^\n]+)", text),
        "contract_period": _search_field(r"(?:\u0905\u0928\u0941\u092c\u0902\u0927\s*\u0905\u0935\u093f\u0927\s*/\s*)?Contract\s*Period\s*[:\-]?\s*([^\n]+)", text),
    }

    fields["address"] = _extract_address(text)

    logger.debug("Extraction result: %s", fields)
    return fields
