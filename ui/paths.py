"""
paths.py
--------
Path helpers that work both in development and inside a frozen
PyInstaller executable (where bundled files live under sys._MEIPASS).
"""

import os
import sys


def project_root() -> str:
    """Return the project root folder (or the PyInstaller bundle dir)."""
    if getattr(sys, "_MEIPASS", None):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def asset_path(*parts: str) -> str:
    """Absolute path to a file inside the assets/ folder."""
    return os.path.join(project_root(), "assets", *parts)


def style_path(*parts: str) -> str:
    """Absolute path to a file inside the styles/ folder."""
    return os.path.join(project_root(), "styles", *parts)
