"""
history_page.py
---------------
Scan history: a searchable table backed by a local SQLite database,
with delete, CSV export, and open-report actions.
"""

import csv
import os

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QHeaderView, QLabel,
                               QLineEdit, QMessageBox, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from database.history_db import HistoryDB
from ui.widgets.card import Card


class HistoryPage(QWidget):
    """Displays previous scan runs with search, delete, export, and open."""

    COLUMNS = ["Date", "Keyword", "Checked", "Matched", "Rejected",
               "Skipped", "Duplicate", "Excel Report"]

    def __init__(self, db: HistoryDB = None, parent=None):
        super().__init__(parent)
        self.db = db or HistoryDB()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Scan History")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        card = Card("Previous Scans")

        # ---- Search + actions ------------------------------------------
        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search history by keyword or date...")
        self.search_input.textChanged.connect(self.refresh)
        controls.addWidget(self.search_input, 1)

        open_button = QPushButton("Open Report")
        open_button.clicked.connect(self.open_selected_report)
        export_button = QPushButton("Export CSV")
        export_button.clicked.connect(self.export_csv)
        delete_button = QPushButton("Delete Selected")
        delete_button.setObjectName("DangerButton")
        delete_button.clicked.connect(self.delete_selected)
        for button in (open_button, export_button, delete_button):
            controls.addWidget(button)
        card.body.addLayout(controls)

        # ---- Table -------------------------------------------------------
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.itemDoubleClicked.connect(lambda _item: self.open_selected_report())
        card.body.addWidget(self.table)

        hint = QLabel("Every completed scan is recorded here. Double-click a "
                      "row to open its Excel report.")
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        card.body.addWidget(hint)

        layout.addWidget(card, 1)
        self.refresh()

    # ------------------------------------------------------------------
    # Data operations
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Reload the table from the database, applying the search filter."""
        records = self.db.all_scans(self.search_input.text().strip())
        self.table.setRowCount(0)
        for record in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            # record = (id, date, keyword, checked, matched, rejected,
            #           skipped, duplicate, report_path)
            for col, value in enumerate(record[1:]):
                item = QTableWidgetItem("" if value is None else str(value))
                if col == 0:
                    # Keep the database id on the first cell of each row.
                    item.setData(Qt.UserRole, record[0])
                self.table.setItem(row, col, item)

    def add_record(self, date: str, keyword: str, checked: int, matched: int,
                   rejected: int, skipped: int, duplicate: int,
                   report_path: str) -> None:
        """Store a completed scan and refresh the table (used by the scan engine)."""
        self.db.add_scan(date, keyword, checked, matched, rejected, skipped,
                         duplicate, report_path)
        self.refresh()

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _selected_rows(self) -> list:
        """Return the unique selected row indexes, ascending."""
        return sorted({index.row() for index in self.table.selectedIndexes()})

    def delete_selected(self) -> None:
        """Delete every selected scan record after confirmation."""
        rows = self._selected_rows()
        if not rows:
            QMessageBox.information(self, "Delete", "Select one or more rows first.")
            return
        answer = QMessageBox.question(
            self, "Delete",
            f"Delete {len(rows)} selected record(s) from the history?")
        if answer != QMessageBox.Yes:
            return
        for row in rows:
            scan_id = self.table.item(row, 0).data(Qt.UserRole)
            if scan_id is not None:
                self.db.delete_scan(int(scan_id))
        self.refresh()

    def export_csv(self) -> None:
        """Export the current (filtered) table contents to a CSV file."""
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "Export", "There is nothing to export yet.")
            return
        path, _selected = QFileDialog.getSaveFileName(
            self, "Export Scan History", "scan_history.csv", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.COLUMNS)
            for row in range(self.table.rowCount()):
                writer.writerow([
                    self.table.item(row, col).text() if self.table.item(row, col) else ""
                    for col in range(self.table.columnCount())
                ])
        QMessageBox.information(self, "Export", f"History exported to:\n{path}")

    def open_selected_report(self) -> None:
        """Open the Excel report of the first selected row."""
        rows = self._selected_rows()
        if not rows:
            QMessageBox.information(self, "Open Report", "Select a row first.")
            return
        report_item = self.table.item(rows[0], len(self.COLUMNS) - 1)
        path = report_item.text() if report_item else ""
        if path and os.path.isfile(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            QMessageBox.warning(self, "Open Report",
                                f"Report file not found:\n{path or '(no path recorded)'}")
