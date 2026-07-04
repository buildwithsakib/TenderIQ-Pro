"""
theme.py
--------
Loads and applies the dark/light QSS stylesheets to the QApplication.
The active theme name is exposed so it can be persisted in settings.
"""

from PySide6.QtWidgets import QApplication

from ui.paths import style_path


class ThemeManager:
    """Applies QSS themes to the application and remembers the active one."""

    THEMES = ("dark", "light")

    def __init__(self, app: QApplication):
        self._app = app
        self.current = "dark"

    def apply(self, name: str) -> None:
        """Load styles/<name>.qss and apply it application-wide."""
        if name not in self.THEMES:
            name = "dark"
        with open(style_path(f"{name}.qss"), "r", encoding="utf-8") as f:
            self._app.setStyleSheet(f.read())
        self.current = name

    def toggle(self) -> str:
        """Switch between dark and light. Returns the new theme name."""
        self.apply("light" if self.current == "dark" else "dark")
        return self.current
