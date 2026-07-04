"""
sidebar.py
----------
Professional vertical navigation sidebar with application branding,
exclusive navigation buttons, and a theme toggle at the bottom.
"""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QButtonGroup, QFrame, QLabel, QPushButton, QVBoxLayout

from ui.paths import asset_path
from version import APP_NAME, APP_SUBTITLE


class Sidebar(QFrame):
    """Left navigation rail. Emits page_selected(index) and theme_toggled()."""

    page_selected = Signal(int)
    theme_toggled = Signal()

    NAV_ITEMS = [
        ("Dashboard", "dashboard.svg"),
        ("History", "history.svg"),
        ("Settings", "settings.svg"),
        ("Help", "help.svg"),
        ("About", "about.svg"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(6)

        # ---- Branding -------------------------------------------------
        title = QLabel(APP_NAME)
        title.setObjectName("SidebarTitle")
        subtitle = QLabel(APP_SUBTITLE)
        subtitle.setObjectName("SidebarSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(18)

        # ---- Navigation buttons ---------------------------------------
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        for index, (text, icon_file) in enumerate(self.NAV_ITEMS):
            button = QPushButton(f"  {text}")
            button.setObjectName("NavButton")
            button.setIcon(QIcon(asset_path("icons", icon_file)))
            button.setIconSize(QSize(18, 18))
            button.setCheckable(True)
            button.setCursor(Qt.PointingHandCursor)
            if index == 0:
                button.setChecked(True)
            self._group.addButton(button, index)
            layout.addWidget(button)
        self._group.idClicked.connect(self.page_selected.emit)

        layout.addStretch(1)

        # ---- Theme toggle ----------------------------------------------
        theme_button = QPushButton("  Toggle Theme")
        theme_button.setObjectName("NavButton")
        theme_button.setIcon(QIcon(asset_path("icons", "theme.svg")))
        theme_button.setIconSize(QSize(18, 18))
        theme_button.setCursor(Qt.PointingHandCursor)
        theme_button.clicked.connect(self.theme_toggled.emit)
        layout.addWidget(theme_button)
