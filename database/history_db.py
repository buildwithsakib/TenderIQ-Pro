"""
history_db.py
-------------
SQLite storage for scan history records using only the Python standard
library. Each completed scan stores its date, keyword, statistics, and
the path of the generated Excel report.

The database lives at database/history.db (ignored by git).
"""

import os
import sqlite3
from typing import List, Tuple

from ui.paths import project_root

DB_PATH = os.path.join(project_root(), "database", "history.db")


class HistoryDB:
    """Thin wrapper around the scan-history SQLite database.

    Intended for use from the UI (main) thread; the scan worker reports
    results through Qt signals, and records are inserted here.
    """

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                keyword TEXT NOT NULL,
                checked INTEGER NOT NULL DEFAULT 0,
                matched INTEGER NOT NULL DEFAULT 0,
                rejected INTEGER NOT NULL DEFAULT 0,
                skipped INTEGER NOT NULL DEFAULT 0,
                duplicate INTEGER NOT NULL DEFAULT 0,
                report_path TEXT
            )
            """
        )
        self._conn.commit()

    def add_scan(self, date: str, keyword: str, checked: int, matched: int,
                 rejected: int, skipped: int, duplicate: int,
                 report_path: str) -> int:
        """Insert one scan record and return its new row id."""
        cursor = self._conn.execute(
            "INSERT INTO scans (date, keyword, checked, matched, rejected, "
            "skipped, duplicate, report_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (date, keyword, checked, matched, rejected, skipped, duplicate,
             report_path),
        )
        self._conn.commit()
        return int(cursor.lastrowid)

    def all_scans(self, search: str = "") -> List[Tuple]:
        """Return all scans, newest first, optionally filtered by a search
        term matched against the keyword and the date."""
        if search:
            like = f"%{search}%"
            cursor = self._conn.execute(
                "SELECT id, date, keyword, checked, matched, rejected, "
                "skipped, duplicate, report_path FROM scans "
                "WHERE keyword LIKE ? OR date LIKE ? ORDER BY id DESC",
                (like, like),
            )
        else:
            cursor = self._conn.execute(
                "SELECT id, date, keyword, checked, matched, rejected, "
                "skipped, duplicate, report_path FROM scans ORDER BY id DESC"
            )
        return cursor.fetchall()

    def delete_scan(self, scan_id: int) -> None:
        """Delete a single scan record by id."""
        self._conn.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
        self._conn.commit()

    def close(self) -> None:
        """Close the underlying connection."""
        self._conn.close()
