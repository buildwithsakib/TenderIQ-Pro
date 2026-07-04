"""
main_window.py
--------------
TenderIQ Pro main application window: sidebar navigation, stacked pages,
status bar, and the bridge between Dashboard UI and the scan worker.
"""

from PySide6.QtCore import QTimer, QElapsedTimer
from PySide6.QtWidgets import (QHBoxLayout, QLabel, QMainWindow,
                               QStackedWidget, QWidget)

from services.scan_worker import ScanWorker
from services.settings_manager import SettingsManager
from services.qt_log_handler import QtLogHandler
from styles.theme import ThemeManager
from ui.dialogs.welcome_dialog import WelcomeDialog
from ui.pages.about_page import AboutPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.help_page import HelpPage
from ui.pages.history_page import HistoryPage
from ui.pages.settings_page import SettingsPage
from ui.widgets.sidebar import Sidebar
from version import APP_DEVELOPER, APP_NAME, APP_SUBTITLE, APP_VERSION

import logging
from datetime import datetime


class MainWindow(QMainWindow):
    """Top-level window owning all application pages and the scan worker."""

    def __init__(self, theme: ThemeManager, settings: SettingsManager):
        super().__init__()
        self._theme = theme
        self._settings = settings
        self._worker = None
        self._elapsed_timer = QElapsedTimer()
        self._elapsed_display_timer = QTimer()
        self._elapsed_display_timer.timeout.connect(self._update_elapsed)

        self.setWindowTitle(f"{APP_NAME} - {APP_SUBTITLE}")
        self.resize(1240, 800)
        self.setMinimumSize(1024, 680)

        # ---- Central layout --------------------------------------------
        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.pages = QStackedWidget()

        self.dashboard = DashboardPage()
        self.history = HistoryPage()
        self.settings_page = SettingsPage(settings)
        self.help_page = HelpPage()
        self.about = AboutPage()
        for page in (self.dashboard, self.history, self.settings_page,
                     self.help_page, self.about):
            self.pages.addWidget(page)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        # ---- Wiring navigation -----------------------------------------
        self.sidebar.page_selected.connect(self.pages.setCurrentIndex)
        self.sidebar.theme_toggled.connect(self._on_theme_toggled)
        self.settings_page.settings_saved.connect(self._on_settings_saved)

        # ---- Dashboard scan signals ------------------------------------
        self.dashboard.start_requested.connect(self._start_scan)
        self.dashboard.stop_requested.connect(self._stop_scan)

        # ---- Live logging bridge (from backend to UI) ------------------
        self._qt_log_handler = QtLogHandler()
        self._qt_log_handler.emitter.message.connect(self.dashboard.append_log)
        logging.getLogger().addHandler(self._qt_log_handler)

        # Populate dashboard from saved config
        self.dashboard.apply_config(settings.load())

        # ---- Status bar ------------------------------------------------
        self.statusBar().showMessage("Ready")
        version_label = QLabel(f"v{APP_VERSION}  |  Developed by {APP_DEVELOPER}")
        version_label.setObjectName("StatusVersion")
        self.statusBar().addPermanentWidget(version_label)

    # ------------------------------------------------------------------
    # First-run guide
    # ------------------------------------------------------------------
    def show_first_run_guide_if_needed(self) -> None:
        if not self._settings.get("first_run_completed", False):
            WelcomeDialog(self).exec()
            self._settings.set("first_run_completed", True)

    # ------------------------------------------------------------------
    # Scan control
    # ------------------------------------------------------------------
    def _start_scan(self) -> None:
        """Build config from dashboard, start scan worker in a thread."""
        # Merge dashboard settings into a full config dict
        dashboard_config = self.dashboard.collect_config()
        full_config = self._settings.load()
        full_config.update(dashboard_config)  # dashboard values override saved settings

        # Disable start / enable stop
        self.dashboard.start_button.setEnabled(False)
        self.dashboard.stop_button.setEnabled(True)
        self.dashboard.append_log("Scan started...")
        self.statusBar().showMessage("Scanning...")

        # Reset statistics
        self.dashboard.stat_checked.set_value(0)
        self.dashboard.stat_matched.set_value(0)
        self.dashboard.stat_rejected.set_value(0)
        self.dashboard.stat_skipped.set_value(0)
        self.dashboard.stat_duplicate.set_value(0)
        self.dashboard.stat_elapsed.set_value("00:00:00")

        # Start elapsed timer
        self._elapsed_timer.start()
        self._elapsed_display_timer.start(1000)

        # Create and start worker
        self._worker = ScanWorker(full_config)
        self._worker.log_msg.connect(self.dashboard.append_log)
        self._worker.stats_update.connect(self._on_stats_update)
        self._worker.scan_finished.connect(self._on_scan_finished)
        self._worker.scan_error.connect(self._on_scan_error)
        self._worker.start()

    def _stop_scan(self) -> None:
        """Request graceful stop."""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self.dashboard.append_log("Stop request sent. Finishing current bid...")
            self.dashboard.stop_button.setEnabled(False)

    def _on_stats_update(self, checked, matched, rejected, skipped, dup):
        """Update dashboard stat cards."""
        self.dashboard.stat_checked.set_value(checked)
        self.dashboard.stat_matched.set_value(matched)
        self.dashboard.stat_rejected.set_value(rejected)
        self.dashboard.stat_skipped.set_value(skipped)
        self.dashboard.stat_duplicate.set_value(dup)

    def _on_scan_finished(self, report_path: str):
        """Cleanup after scan completes (or stops)."""
        self._elapsed_display_timer.stop()
        self._update_elapsed()
        self.dashboard.start_button.setEnabled(True)
        self.dashboard.stop_button.setEnabled(False)
        self.statusBar().showMessage("Scan finished", 5000)

        if report_path:
            self.dashboard.append_log(f"Scan complete. Report: {report_path}")
            # Add to history
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conf = self.dashboard.collect_config()
            self.history.add_record(
                date=now,
                keyword=conf.get("search_keyword", ""),
                checked=int(self.dashboard.stat_checked.value_label.text()),
                matched=int(self.dashboard.stat_matched.value_label.text()),
                rejected=int(self.dashboard.stat_rejected.value_label.text()),
                skipped=int(self.dashboard.stat_skipped.value_label.text()),
                duplicate=int(self.dashboard.stat_duplicate.value_label.text()),
                report_path=report_path
            )
        else:
            self.dashboard.append_log("Scan stopped or no report generated.")

        self._worker = None

    def _on_scan_error(self, error_msg: str):
        """Handle unexpected worker errors."""
        self._elapsed_display_timer.stop()
        self.dashboard.start_button.setEnabled(True)
        self.dashboard.stop_button.setEnabled(False)
        self.statusBar().showMessage("Scan error")
        self.dashboard.append_log(f"SCAN ERROR: {error_msg}")
        self._worker = None

    # ------------------------------------------------------------------
    # Elapsed time display
    # ------------------------------------------------------------------
    def _update_elapsed(self):
        if self._elapsed_timer.isValid():
            elapsed = self._elapsed_timer.elapsed() // 1000
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.dashboard.stat_elapsed.set_value(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    # ------------------------------------------------------------------
    # Theme & settings slots
    # ------------------------------------------------------------------
    def _on_theme_toggled(self):
        self._settings.set("ui_theme", self._theme.toggle())
    def _on_settings_saved(self, config: dict):
        theme = config.get("ui_theme", self._theme.current)
        if theme != self._theme.current:
            self._theme.apply(theme)
        self.dashboard.apply_config(config)
        self.statusBar().showMessage("Settings saved", 5000)
