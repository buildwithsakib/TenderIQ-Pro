"""
settings_page.py
----------------
Full settings editor for TenderIQ Pro.

Every value is persisted in config.json - the same file the backend in
core/ reads - so the CLI scanner keeps working with identical settings.
Actions: Save, Restore Default, and Reset (discard unsaved edits).
"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QGridLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QScrollArea, QSpinBox,
                               QVBoxLayout, QWidget)

from services.settings_manager import SettingsManager
from ui.widgets.card import Card


class SettingsPage(QWidget):
    """Interactive editor for the advanced configuration in config.json."""

    settings_saved = Signal(dict)

    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self._settings = settings

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Settings")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        layout.addWidget(self._build_portal_card())
        layout.addWidget(self._build_matching_card())
        layout.addWidget(self._build_logging_card())
        layout.addWidget(self._build_appearance_card())
        layout.addLayout(self._build_buttons_row())

        self.status_label = QLabel("")
        self.status_label.setObjectName("HintLabel")
        layout.addWidget(self.status_label)
        layout.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.reset()

    # ------------------------------------------------------------------
    # Card builders
    # ------------------------------------------------------------------
    def _build_portal_card(self) -> Card:
        card = Card("Portal & Browser")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("GeM Portal URL"), 0, 0)
        self.gem_url_input = QLineEdit()
        grid.addWidget(self.gem_url_input, 0, 1)

        grid.addWidget(QLabel("Page Load Timeout"), 1, 0)
        self.page_timeout_spin = QSpinBox()
        self.page_timeout_spin.setRange(10000, 300000)
        self.page_timeout_spin.setSingleStep(5000)
        self.page_timeout_spin.setSuffix(" ms")
        grid.addWidget(self.page_timeout_spin, 1, 1)

        grid.addWidget(QLabel("Download Timeout"), 2, 0)
        self.download_timeout_spin = QSpinBox()
        self.download_timeout_spin.setRange(10000, 300000)
        self.download_timeout_spin.setSingleStep(5000)
        self.download_timeout_spin.setSuffix(" ms")
        grid.addWidget(self.download_timeout_spin, 2, 1)

        grid.addWidget(QLabel("Navigation Retries"), 3, 0)
        self.retry_spin = QSpinBox()
        self.retry_spin.setRange(1, 10)
        grid.addWidget(self.retry_spin, 3, 1)

        grid.addWidget(QLabel("Browser Slow-Mo"), 4, 0)
        self.slowmo_spin = QSpinBox()
        self.slowmo_spin.setRange(0, 5000)
        self.slowmo_spin.setSingleStep(50)
        self.slowmo_spin.setSuffix(" ms")
        grid.addWidget(self.slowmo_spin, 4, 1)

        grid.addWidget(QLabel("Max Bids Per Run"), 5, 0)
        self.max_bids_spin = QSpinBox()
        self.max_bids_spin.setRange(0, 100000)
        self.max_bids_spin.setSpecialValueText("Unlimited")
        grid.addWidget(self.max_bids_spin, 5, 1)

        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)
        return card

    def _build_matching_card(self) -> Card:
        card = Card("Matching")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("Required Item Category"), 0, 0)
        self.category_input = QLineEdit()
        grid.addWidget(self.category_input, 0, 1)
        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)

        hint = QLabel("A tender's Item Category must contain this text to be "
                      "eligible (case-insensitive). Search keyword, MSE, and "
                      "state filters are configured on the Dashboard.")
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        card.body.addWidget(hint)
        return card

    def _build_logging_card(self) -> Card:
        card = Card("Logging")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("Log Folder"), 0, 0)
        self.log_dir_input = QLineEdit()
        grid.addWidget(self.log_dir_input, 0, 1)

        grid.addWidget(QLabel("Log File Name"), 1, 0)
        self.log_file_input = QLineEdit()
        grid.addWidget(self.log_file_input, 1, 1)

        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)
        return card

    def _build_appearance_card(self) -> Card:
        card = Card("Appearance")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("Theme"), 0, 0)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        grid.addWidget(self.theme_combo, 0, 1)

        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)
        return card

    def _build_buttons_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)

        save_button = QPushButton("Save Settings")
        save_button.setObjectName("PrimaryButton")
        save_button.clicked.connect(self.save)

        defaults_button = QPushButton("Restore Defaults")
        defaults_button.clicked.connect(self.restore_defaults)

        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset)

        row.addWidget(save_button)
        row.addWidget(defaults_button)
        row.addWidget(reset_button)
        row.addStretch(1)
        return row

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _populate(self, config: dict) -> None:
        """Fill every field from a configuration dictionary."""
        self.gem_url_input.setText(str(config.get("gem_url", "")))
        self.page_timeout_spin.setValue(int(config.get("page_load_timeout_ms", 60000)))
        self.download_timeout_spin.setValue(int(config.get("download_timeout_ms", 60000)))
        self.retry_spin.setValue(int(config.get("navigation_retry_count", 3)))
        self.slowmo_spin.setValue(int(config.get("browser_slow_mo_ms", 0)))
        self.max_bids_spin.setValue(int(config.get("max_bids_to_process", 0)))
        self.category_input.setText(str(config.get("allowed_item_category", "Manpower")))
        self.log_dir_input.setText(str(config.get("log_dir", "logs")))
        self.log_file_input.setText(str(config.get("log_file", "scanner.log")))
        theme = str(config.get("ui_theme", "dark"))
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findText(theme)))

    def save(self) -> None:
        """Persist every edited value into config.json."""
        config = self._settings.load()
        config.update({
            "gem_url": self.gem_url_input.text().strip(),
            "page_load_timeout_ms": self.page_timeout_spin.value(),
            "download_timeout_ms": self.download_timeout_spin.value(),
            "navigation_retry_count": self.retry_spin.value(),
            "browser_slow_mo_ms": self.slowmo_spin.value(),
            "max_bids_to_process": self.max_bids_spin.value(),
            "allowed_item_category": self.category_input.text().strip() or "Manpower",
            "log_dir": self.log_dir_input.text().strip() or "logs",
            "log_file": self.log_file_input.text().strip() or "scanner.log",
            "ui_theme": self.theme_combo.currentText(),
        })
        self._settings.save(config)
        self.settings_saved.emit(config)
        self.status_label.setText("Settings saved to config.json.")

    def restore_defaults(self) -> None:
        """Overwrite config.json with factory defaults."""
        config = self._settings.restore_defaults()
        self._populate(config)
        self.settings_saved.emit(config)
        self.status_label.setText("Default configuration restored and saved.")

    def reset(self) -> None:
        """Discard unsaved edits and reload values from disk."""
        self._populate(self._settings.load())
        self.status_label.setText("Loaded configuration from config.json.")
