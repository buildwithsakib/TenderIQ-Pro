"""
app.py
------
TenderIQ Pro - desktop application entry point.

Launches the PySide6 user interface that wraps the existing GeM tender
scanner backend (core/). Run with:

    python app.py
"""

import sys

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from services.settings_manager import SettingsManager
from styles.theme import ThemeManager
from ui.main_window import MainWindow
from ui.paths import asset_path
from version import APP_NAME, APP_VERSION, ORGANIZATION_NAME


def main() -> int:
    """Create the QApplication, apply theming, and show the main window."""
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setWindowIcon(QIcon(asset_path("icons", "logo.svg")))

    # Segoe UI is the native Windows font; Qt falls back gracefully elsewhere.
    app.setFont(QFont("Segoe UI", 10))

    settings = SettingsManager()
    theme = ThemeManager(app)
    theme.apply(str(settings.get("ui_theme", "dark")))

    window = MainWindow(theme, settings)
    window.show()
    window.show_first_run_guide_if_needed()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
