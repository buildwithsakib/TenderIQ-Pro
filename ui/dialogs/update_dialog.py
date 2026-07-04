"""
update_dialog.py
----------------
Check-for-updates window. Uses services/updater.py to query the release
feed, showing current version information and a release-notes area.
While the feed endpoint remains a placeholder, a clear "not available"
message is shown instead of an error.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPushButton,
                               QTextBrowser, QVBoxLayout)

from services.updater import check_for_updates
from version import APP_NAME, APP_VERSION, RELEASE_NOTES_URL


class UpdateDialog(QDialog):
    """Modal window for the future update system."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Check for Updates")
        self.setModal(True)
        self.setMinimumSize(460, 340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(10)

        current = QLabel(f"{APP_NAME} \u2014 current version: v{APP_VERSION}")
        current.setObjectName("CardTitle")
        layout.addWidget(current)

        self.status_label = QLabel("Press the button below to check for a newer version.")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.notes = QTextBrowser()
        self.notes.setOpenExternalLinks(True)
        self.notes.setPlainText(f"Release notes: {RELEASE_NOTES_URL}")
        layout.addWidget(self.notes, 1)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        check_button = QPushButton("Check for Updates")
        check_button.setObjectName("PrimaryButton")
        check_button.setCursor(Qt.PointingHandCursor)
        check_button.clicked.connect(self._check)
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(check_button)
        buttons.addWidget(close_button)
        buttons.addStretch(1)
        layout.addLayout(buttons)

    def _check(self) -> None:
        """Query the release feed and show the outcome."""
        result = check_for_updates()
        self.status_label.setText(result["message"])
        notes = result.get("release_notes", "")
        if notes:
            self.notes.setPlainText(notes)
        elif result.get("status") == "unavailable":
            self.notes.setPlainText(
                "No release feed is configured yet.\n\n"
                f"Release notes will be published at: {RELEASE_NOTES_URL}")
