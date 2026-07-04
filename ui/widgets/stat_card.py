"""
stat_card.py
------------
Small statistic tile showing a live counter (or time string) with a
caption underneath. An optional accent colours the value via QSS.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    """Live statistics tile (Checked / Matched / Rejected / etc.)."""

    def __init__(self, caption: str, accent: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        if accent:
            # Picked up by QSS selectors like #StatCard[accent="green"]
            self.setProperty("accent", accent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)

        self.value_label = QLabel("0")
        self.value_label.setObjectName("StatValue")
        self.value_label.setAlignment(Qt.AlignCenter)

        caption_label = QLabel(caption)
        caption_label.setObjectName("StatCaption")
        caption_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.value_label)
        layout.addWidget(caption_label)

    def set_value(self, value) -> None:
        """Update the displayed value (int or preformatted string)."""
        self.value_label.setText(str(value))
