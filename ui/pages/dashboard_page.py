"""
dashboard_page.py
-----------------
The main scanning dashboard for TenderIQ Pro.

Contains:
    - Search keyword input (any keyword allowed, never restricted)
    - Eligibility filters (MSE relaxation, experience, turnover, states)
    - Scan & browser settings (visibility, delays, restart, cleanup)
    - Output settings (folders and Excel file name)
    - Action buttons (start / stop / open excel / open folder / reset)
    - Live statistics tiles and elapsed time
    - Live log console

The visual layout and local behaviours are complete here; the scan engine
attaches to the start_requested/stop_requested signals during backend
integration.
"""

import os

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPlainTextEdit, QPushButton, QRadioButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)

from ui.paths import asset_path
from ui.widgets.card import Card
from ui.widgets.stat_card import StatCard

# All Indian states and union territories for the geographical filter.
INDIAN_STATES = [
    "Not Applicable", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
    "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
    "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
    "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu", "Delhi",
    "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]

MSE_OPTIONS = ["Any", "Yes", "No"]
EXPERIENCE_OPTIONS = ["No Filter", "1 Year", "2 Years", "3 Years", "5 Years", "Custom"]
TURNOVER_OPTIONS = ["No Filter", "10 Lakhs", "25 Lakhs", "50 Lakhs", "70 Lakhs", "1 Crore", "Custom"]
DEFAULT_CHECKED_STATES = ("Maharashtra", "Not Applicable")


class DashboardPage(QWidget):
    """Complete dashboard layout with local behaviours."""

    start_requested = Signal()
    stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Dashboard")
        header.setObjectName("PageTitle")
        layout.addWidget(header)

        layout.addWidget(self._build_search_card())

        middle = QGridLayout()
        middle.setSpacing(16)
        middle.addWidget(self._build_filters_card(), 0, 0)
        middle.addWidget(self._build_scan_settings_card(), 0, 1)
        middle.setColumnStretch(0, 1)
        middle.setColumnStretch(1, 1)
        layout.addLayout(middle)

        layout.addWidget(self._build_output_card())
        layout.addLayout(self._build_actions_row())
        layout.addLayout(self._build_stats_row())
        layout.addWidget(self._build_log_card())

        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.append_log("TenderIQ Pro ready. Configure your search and press START SCAN.")

    # ------------------------------------------------------------------
    # Card builders
    # ------------------------------------------------------------------
    def _build_search_card(self) -> Card:
        card = Card("Search Keyword")
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText(
            "Enter any keyword, e.g. Manpower, Security, Driver, Housekeeping, Data Entry...")
        hint = QLabel("The scanner searches the GeM portal for bids containing this "
                      "keyword. Any custom keyword is allowed.")
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        card.body.addWidget(self.keyword_input)
        card.body.addWidget(hint)
        return card

    def _build_filters_card(self) -> Card:
        card = Card("Eligibility Filters")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("MSE Relaxation"), 0, 0)
        self.mse_combo = QComboBox()
        self.mse_combo.addItems(MSE_OPTIONS)
        grid.addWidget(self.mse_combo, 0, 1)

        grid.addWidget(QLabel("Experience"), 1, 0)
        self.experience_combo = QComboBox()
        self.experience_combo.addItems(EXPERIENCE_OPTIONS)
        grid.addWidget(self.experience_combo, 1, 1)
        self.experience_custom = QSpinBox()
        self.experience_custom.setRange(0, 50)
        self.experience_custom.setSuffix(" years")
        self.experience_custom.setEnabled(False)
        grid.addWidget(self.experience_custom, 1, 2)

        grid.addWidget(QLabel("Turnover"), 2, 0)
        self.turnover_combo = QComboBox()
        self.turnover_combo.addItems(TURNOVER_OPTIONS)
        grid.addWidget(self.turnover_combo, 2, 1)
        self.turnover_custom = QDoubleSpinBox()
        self.turnover_custom.setRange(0.0, 100000.0)
        self.turnover_custom.setSuffix(" Lakhs")
        self.turnover_custom.setEnabled(False)
        grid.addWidget(self.turnover_custom, 2, 2)

        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)

        card.body.addWidget(QLabel("Geographical Presence (select one or more states)"))
        self.states_list = QListWidget()
        self.states_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.states_list.setFixedHeight(170)
        for state in INDIAN_STATES:
            item = QListWidgetItem(state)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if state in DEFAULT_CHECKED_STATES else Qt.Unchecked)
            self.states_list.addItem(item)
        card.body.addWidget(self.states_list)

        # Enable custom inputs only when "Custom" is chosen.
        self.experience_combo.currentTextChanged.connect(
            lambda text: self.experience_custom.setEnabled(text == "Custom"))
        self.turnover_combo.currentTextChanged.connect(
            lambda text: self.turnover_custom.setEnabled(text == "Custom"))
        return card

    def _build_scan_settings_card(self) -> Card:
        card = Card("Scan & Browser Settings")

        mode_row = QHBoxLayout()
        self.visible_radio = QRadioButton("Visible Browser")
        self.visible_radio.setChecked(True)
        self.headless_radio = QRadioButton("Headless Browser")
        mode_row.addWidget(self.visible_radio)
        mode_row.addWidget(self.headless_radio)
        mode_row.addStretch(1)
        card.body.addLayout(mode_row)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("Restart Browser After"), 0, 0)
        self.restart_spin = QSpinBox()
        self.restart_spin.setRange(0, 1000)
        self.restart_spin.setSuffix(" bids")
        self.restart_spin.setSpecialValueText("Never")
        grid.addWidget(self.restart_spin, 0, 1)

        grid.addWidget(QLabel("Minimum Delay"), 1, 0)
        self.min_delay_spin = QDoubleSpinBox()
        self.min_delay_spin.setRange(0.5, 30.0)
        self.min_delay_spin.setSingleStep(0.5)
        self.min_delay_spin.setValue(1.5)
        self.min_delay_spin.setSuffix(" s")
        grid.addWidget(self.min_delay_spin, 1, 1)

        grid.addWidget(QLabel("Maximum Delay"), 2, 0)
        self.max_delay_spin = QDoubleSpinBox()
        self.max_delay_spin.setRange(0.5, 60.0)
        self.max_delay_spin.setSingleStep(0.5)
        self.max_delay_spin.setValue(3.0)
        self.max_delay_spin.setSuffix(" s")
        grid.addWidget(self.max_delay_spin, 2, 1)

        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)

        self.skip_duplicates_check = QCheckBox("Skip Duplicate Bids")
        self.skip_duplicates_check.setChecked(True)
        self.delete_pdf_check = QCheckBox("Delete PDF After Processing")
        self.delete_pdf_check.setChecked(True)
        card.body.addWidget(self.skip_duplicates_check)
        card.body.addWidget(self.delete_pdf_check)

        note = QLabel("A random human-like delay between the minimum and maximum is "
                      "applied between actions. Stability is prioritised over speed.")
        note.setObjectName("HintLabel")
        note.setWordWrap(True)
        card.body.addWidget(note)
        return card

    def _build_output_card(self) -> Card:
        card = Card("Output Settings")
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(10)

        grid.addWidget(QLabel("Output Folder"), 0, 0)
        self.output_dir_input = QLineEdit("output")
        grid.addWidget(self.output_dir_input, 0, 1)
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(lambda: self._browse_folder(self.output_dir_input))
        grid.addWidget(output_browse, 0, 2)

        grid.addWidget(QLabel("Downloads Folder"), 1, 0)
        self.download_dir_input = QLineEdit("downloads")
        grid.addWidget(self.download_dir_input, 1, 1)
        download_browse = QPushButton("Browse...")
        download_browse.clicked.connect(lambda: self._browse_folder(self.download_dir_input))
        grid.addWidget(download_browse, 1, 2)

        grid.addWidget(QLabel("Excel File Name"), 2, 0)
        self.excel_name_input = QLineEdit("matched_tenders.xlsx")
        grid.addWidget(self.excel_name_input, 2, 1)

        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)
        return card

    def _build_actions_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)

        self.start_button = QPushButton("  START SCAN")
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.setIcon(QIcon(asset_path("icons", "start.svg")))
        self.start_button.clicked.connect(self._on_start_clicked)

        self.stop_button = QPushButton("  STOP SCAN")
        self.stop_button.setObjectName("DangerButton")
        self.stop_button.setIcon(QIcon(asset_path("icons", "stop.svg")))
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._on_stop_clicked)

        self.open_excel_button = QPushButton("  OPEN EXCEL")
        self.open_excel_button.setIcon(QIcon(asset_path("icons", "excel.svg")))
        self.open_excel_button.clicked.connect(self._open_excel)

        self.open_folder_button = QPushButton("  OPEN OUTPUT FOLDER")
        self.open_folder_button.setIcon(QIcon(asset_path("icons", "folder.svg")))
        self.open_folder_button.clicked.connect(self._open_output_folder)

        self.reset_button = QPushButton("  RESET FILTERS")
        self.reset_button.setIcon(QIcon(asset_path("icons", "reset.svg")))
        self.reset_button.clicked.connect(self.reset_filters)

        for button in (self.start_button, self.stop_button, self.open_excel_button,
                       self.open_folder_button, self.reset_button):
            button.setCursor(Qt.PointingHandCursor)
            row.addWidget(button)
        row.addStretch(1)
        return row

    def _build_stats_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)
        self.stat_checked = StatCard("Checked")
        self.stat_matched = StatCard("Matched", accent="green")
        self.stat_rejected = StatCard("Rejected", accent="red")
        self.stat_skipped = StatCard("Skipped", accent="orange")
        self.stat_duplicate = StatCard("Duplicate", accent="purple")
        self.stat_elapsed = StatCard("Elapsed Time")
        self.stat_elapsed.set_value("00:00:00")
        for stat in (self.stat_checked, self.stat_matched, self.stat_rejected,
                     self.stat_skipped, self.stat_duplicate, self.stat_elapsed):
            row.addWidget(stat, 1)
        return row

    def _build_log_card(self) -> Card:
        card = Card("Live Log")
        self.log_console = QPlainTextEdit()
        self.log_console.setObjectName("LogConsole")
        self.log_console.setReadOnly(True)
        self.log_console.setMinimumHeight(220)
        self.log_console.setMaximumBlockCount(5000)
        card.body.addWidget(self.log_console)
        return card

    # ------------------------------------------------------------------
    # Behaviours
    # ------------------------------------------------------------------
    def _on_start_clicked(self) -> None:
        self.append_log("Start scan requested.")
        self.start_requested.emit()

    def _on_stop_clicked(self) -> None:
        self.append_log("Stop scan requested. The scanner stops after the current bid.")
        self.stop_requested.emit()

    def _browse_folder(self, target: QLineEdit) -> None:
        """Open a folder picker and write the chosen path into the field."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Folder", target.text() or os.getcwd())
        if folder:
            target.setText(folder)

    def _open_output_folder(self) -> None:
        """Open the configured output folder in the system file explorer."""
        folder = os.path.abspath(self.output_dir_input.text().strip() or "output")
        os.makedirs(folder, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _open_excel(self) -> None:
        """Open the generated Excel report with the default application."""
        folder = os.path.abspath(self.output_dir_input.text().strip() or "output")
        name = self.excel_name_input.text().strip() or "matched_tenders.xlsx"
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        else:
            self.append_log(f"Excel file not found yet: {path}")

    def reset_filters(self) -> None:
        """Restore every filter control to its default value."""
        self.keyword_input.clear()
        self.mse_combo.setCurrentIndex(0)
        self.experience_combo.setCurrentIndex(0)
        self.experience_custom.setValue(0)
        self.turnover_combo.setCurrentIndex(0)
        self.turnover_custom.setValue(0.0)
        for i in range(self.states_list.count()):
            item = self.states_list.item(i)
            item.setCheckState(
                Qt.Checked if item.text() in DEFAULT_CHECKED_STATES else Qt.Unchecked)
        self.append_log("Filters reset to defaults.")

    def selected_states(self) -> list:
        """Return the list of states currently checked in the filter."""
        states = []
        for i in range(self.states_list.count()):
            item = self.states_list.item(i)
            if item.checkState() == Qt.Checked:
                states.append(item.text())
        return states

    def append_log(self, text: str) -> None:
        """Append one line to the live log console and auto-scroll."""
        self.log_console.appendPlainText(text)
        # Auto-scroll to bottom
        scrollbar = self.log_console.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    # ------------------------------------------------------------------
    # Configuration sync
    # ------------------------------------------------------------------
    def apply_config(self, config: dict) -> None:
        """Populate every dashboard control from a config dictionary."""
        self.keyword_input.setText(str(config.get("search_keyword", "")))

        mse = str(config.get("mse_filter_mode", "Any"))
        self.mse_combo.setCurrentIndex(max(0, self.mse_combo.findText(mse)))

        years = int(config.get("required_experience_years", 0) or 0)
        preset = "No Filter" if years == 0 else ("1 Year" if years == 1 else f"{years} Years")
        if preset in EXPERIENCE_OPTIONS:
            self.experience_combo.setCurrentText(preset)
        else:
            self.experience_combo.setCurrentText("Custom")
            self.experience_custom.setValue(years)

        lakhs = float(config.get("required_turnover_lakhs", 0) or 0)
        preset_map = {0.0: "No Filter", 10.0: "10 Lakhs", 25.0: "25 Lakhs",
                      50.0: "50 Lakhs", 70.0: "70 Lakhs", 100.0: "1 Crore"}
        if lakhs in preset_map:
            self.turnover_combo.setCurrentText(preset_map[lakhs])
        else:
            self.turnover_combo.setCurrentText("Custom")
            self.turnover_custom.setValue(lakhs)

        allowed = set(config.get("allowed_states", []))
        for i in range(self.states_list.count()):
            item = self.states_list.item(i)
            item.setCheckState(Qt.Checked if item.text() in allowed else Qt.Unchecked)

        headless = bool(config.get("headless", False))
        self.headless_radio.setChecked(headless)
        self.visible_radio.setChecked(not headless)
        self.restart_spin.setValue(int(config.get("restart_browser_after_bids", 0) or 0))
        self.min_delay_spin.setValue(float(config.get("min_action_delay_s", 1.5)))
        self.max_delay_spin.setValue(float(config.get("max_action_delay_s", 3.0)))
        self.skip_duplicates_check.setChecked(bool(config.get("skip_duplicates", True)))
        self.delete_pdf_check.setChecked(bool(config.get("delete_pdf_after_processing", True)))
        self.output_dir_input.setText(str(config.get("output_dir", "output")))
        self.download_dir_input.setText(str(config.get("download_dir", "downloads")))
        self.excel_name_input.setText(str(config.get("output_file", "matched_tenders.xlsx")))

    def collect_config(self) -> dict:
        """Return the dashboard state as config keys (merged by the caller)."""
        exp_text = self.experience_combo.currentText()
        if exp_text == "No Filter":
            years = 0
        elif exp_text == "Custom":
            years = self.experience_custom.value()
        else:
            years = int(exp_text.split()[0])

        turn_text = self.turnover_combo.currentText()
        turn_map = {"No Filter": 0.0, "10 Lakhs": 10.0, "25 Lakhs": 25.0,
                    "50 Lakhs": 50.0, "70 Lakhs": 70.0, "1 Crore": 100.0}
        lakhs = self.turnover_custom.value() if turn_text == "Custom" else turn_map[turn_text]

        mse_mode = self.mse_combo.currentText()
        return {
            "search_keyword": self.keyword_input.text().strip(),
            "mse_filter_mode": mse_mode,
            # core/matcher.py only understands Yes/No; "Any" is bypassed by
            # the integration layer, so keep a valid backend value here.
            "mse_relaxation": mse_mode if mse_mode in ("Yes", "No") else "Yes",
            "required_experience_years": years,
            "required_turnover_lakhs": lakhs,
            "allowed_states": self.selected_states(),
            "headless": self.headless_radio.isChecked(),
            "restart_browser_after_bids": self.restart_spin.value(),
            "min_action_delay_s": self.min_delay_spin.value(),
            "max_action_delay_s": self.max_delay_spin.value(),
            "skip_duplicates": self.skip_duplicates_check.isChecked(),
            "delete_pdf_after_processing": self.delete_pdf_check.isChecked(),
            "output_dir": self.output_dir_input.text().strip() or "output",
            "download_dir": self.download_dir_input.text().strip() or "downloads",
            "output_file": self.excel_name_input.text().strip() or "matched_tenders.xlsx",
        }
