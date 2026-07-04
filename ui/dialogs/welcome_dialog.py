"""
welcome_dialog.py
-----------------
First-run guided experience: a simple four-step visual guide shown the
first time TenderIQ Pro starts, explaining the workflow in a
beginner-friendly way.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout

from version import APP_NAME

STEPS = [
    ("Step 1", "Enter a Search Keyword on the Dashboard "
               "(e.g. Manpower, Security, Driver, Housekeeping)."),
    ("Step 2", "Select your Eligibility Filters: MSE relaxation, "
               "experience, turnover, and one or more states."),
    ("Step 3", "Choose your Output Folder and the Excel file name."),
    ("Step 4", "Click START SCAN and watch the live log and statistics. "
               "Matching tenders are written into your Excel report."),
]


class WelcomeDialog(QDialog):
    """One-time onboarding dialog with the four getting-started steps."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Welcome to {APP_NAME}")
        self.setModal(True)
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(10)

        heading = QLabel(f"Welcome to {APP_NAME}!")
        heading.setObjectName("AboutAppName")
        layout.addWidget(heading)

        intro = QLabel("TenderIQ Pro scans the GeM portal for tenders that match "
                       "your eligibility and builds an Excel report automatically. "
                       "Getting started takes four simple steps:")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        layout.addSpacing(8)

        for index, (step, text) in enumerate(STEPS):
            step_label = QLabel(f"<b>{step}</b> \u2014 {text}")
            step_label.setWordWrap(True)
            layout.addWidget(step_label)
            if index < len(STEPS) - 1:
                arrow = QLabel("\u2193")
                arrow.setObjectName("HintLabel")
                arrow.setAlignment(Qt.AlignHCenter)
                layout.addWidget(arrow)

        layout.addSpacing(8)
        note = QLabel("You can revisit all of this anytime in the Help section.")
        note.setObjectName("HintLabel")
        note.setWordWrap(True)
        layout.addWidget(note)

        button = QPushButton("Get Started")
        button.setObjectName("PrimaryButton")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(self.accept)
        layout.addWidget(button)
