"""
card.py
-------
Rounded card container widget used across all pages. Styling comes from
the active QSS theme via the #Card and #CardTitle object names.
"""

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class Card(QFrame):
    """A rounded, elevated card with an optional title header.

    Add content with `card.body.addWidget(...)` or `card.body.addLayout(...)`.
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(10)
        if title:
            header = QLabel(title)
            header.setObjectName("CardTitle")
            self.body.addWidget(header)
