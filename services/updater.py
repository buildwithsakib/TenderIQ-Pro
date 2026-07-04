"""
updater.py
----------
Future update system for TenderIQ Pro.

Architecture: the application queries UPDATE_FEED_URL (defined in
version.py) for a small JSON document of the form:

    {
        "latest_version": "1.1.0",
        "release_notes": "What changed in this release...",
        "download_url": "https://.../TenderIQPro-Setup-1.1.0.exe"
    }

and compares latest_version against APP_VERSION. The feed endpoint is a
placeholder until a release channel exists, so network failures resolve
to a clear, non-blocking "not available" status.
"""

import json
import urllib.request
from typing import Dict

from version import APP_VERSION, UPDATE_FEED_URL


def _version_tuple(version: str) -> tuple:
    """Convert '1.2.3' into (1, 2, 3) for safe comparison."""
    parts = []
    for piece in version.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def check_for_updates(timeout: float = 8.0) -> Dict[str, str]:
    """Query the release feed and classify the result.

    Returns a dict with keys: status ('update_available' | 'up_to_date' |
    'unavailable'), latest_version, release_notes, download_url, message.
    """
    try:
        with urllib.request.urlopen(UPDATE_FEED_URL, timeout=timeout) as response:
            feed = json.loads(response.read().decode("utf-8"))
        latest = str(feed.get("latest_version", "")).strip()
        notes = str(feed.get("release_notes", ""))
        download = str(feed.get("download_url", ""))
        if latest and _version_tuple(latest) > _version_tuple(APP_VERSION):
            return {
                "status": "update_available",
                "latest_version": latest,
                "release_notes": notes,
                "download_url": download,
                "message": (f"A new version is available: v{latest} "
                            f"(you are on v{APP_VERSION})."),
            }
        return {
            "status": "up_to_date",
            "latest_version": latest or APP_VERSION,
            "release_notes": notes,
            "download_url": download,
            "message": f"You are running the latest version (v{APP_VERSION}).",
        }
    except Exception as exc:
        return {
            "status": "unavailable",
            "latest_version": "",
            "release_notes": "",
            "download_url": "",
            "message": ("Update information is not available right now "
                        f"({exc.__class__.__name__}). The update channel will "
                        "be activated in a future release."),
        }
