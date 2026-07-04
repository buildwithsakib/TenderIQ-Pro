"""
about_page.py
-------------
About window content: application identity, version, developer, and
contact details (contact fields are placeholders until public release).
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QGridLayout, QLabel, QPushButton, QVBoxLayout,
                               QWidget)

from ui.dialogs.update_dialog import UpdateDialog
from ui.widgets.card import Card
from version import (APP_COPYRIGHT, APP_DEVELOPER, APP_NAME, APP_SUBTITLE,
                     APP_VERSION, CONTACT_EMAIL, CONTACT_PHONE, GITHUB_URL)


class AboutPage(QWidget):
    """Static application information card."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("About")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        card = Card()
        app_name = QLabel(APP_NAME)
        app_name.setObjectName("AboutAppName")
        subtitle = QLabel(APP_SUBTITLE)
        subtitle.setObjectName("HintLabel")
        card.body.addWidget(app_name)
        card.body.addWidget(subtitle)
        card.body.addSpacing(8)

        grid = QGridLayout()
        grid.setVerticalSpacing(8)
        grid.setHorizontalSpacing(24)
        rows = [
            ("Version", APP_VERSION),
            ("Developer", APP_DEVELOPER),
            ("GitHub", GITHUB_URL),
            ("Email", CONTACT_EMAIL),
            ("Phone", CONTACT_PHONE),
        ]
        for i, (key, value) in enumerate(rows):
            key_label = QLabel(key)
            key_label.setObjectName("HintLabel")
            value_label = QLabel(value)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            grid.addWidget(key_label, i, 0)
            grid.addWidget(value_label, i, 1)
        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)
        card.body.addSpacing(8)

        update_button = QPushButton("Check for Updates")
        update_button.setCursor(Qt.PointingHandCursor)
        update_button.clicked.connect(self._open_update_dialog)
        card.body.addWidget(update_button, 0, Qt.AlignLeft)

        copyright_label = QLabel(APP_COPYRIGHT)
        copyright_label.setObjectName("HintLabel")
        card.body.addWidget(copyright_label)

        layout.addWidget(card)
        layout.addStretch(1)

    def _open_update_dialog(self) -> None:
        """Open the update-check window."""
        UpdateDialog(self).exec()
