"""
help_page.py
------------
Help window with beginner-friendly documentation: how the scanner works,
how eligibility is decided, how to start, FAQ, troubleshooting, and best
practices.
"""

from PySide6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

HELP_HTML = """
<h2>How the Scanner Works</h2>
<p>TenderIQ Pro opens the public GeM Bid Portal in a real Chromium browser,
types your search keyword, and walks through every bid in the results.
For each bid it downloads the official PDF, reads the key fields
(Item Category, MSE Relaxation, Geographical States, dates), checks your
eligibility filters, and writes matching tenders into an Excel report.
Processed PDFs are deleted automatically to keep your disk clean.</p>

<h2>How Eligibility Works</h2>
<ul>
<li><b>Item Category</b> must contain your search keyword context (e.g. Manpower).</li>
<li><b>MSE Relaxation</b> is compared with your dropdown choice (Any / Yes / No).</li>
<li><b>Geographical Presence</b> must include at least one of your selected states,
or be marked \u201cNot Applicable\u201d.</li>
</ul>
<p>A tender appears in the Excel report only when every active filter passes.
Rejected bids are listed in the live log together with the exact reason.</p>

<h2>How To Start</h2>
<ol>
<li><b>Step 1:</b> Enter any search keyword on the Dashboard (Manpower, Security, Driver...).</li>
<li><b>Step 2:</b> Select your eligibility filters (MSE, experience, turnover, states).</li>
<li><b>Step 3:</b> Choose your output folder and Excel file name.</li>
<li><b>Step 4:</b> Click <b>START SCAN</b> and watch the live log and statistics.</li>
</ol>

<h2>FAQ</h2>
<p><b>Can I search any keyword?</b> Yes. The keyword is never restricted.</p>
<p><b>Will the same bid be processed twice?</b> No. With \u201cSkip Duplicate Bids\u201d
enabled, already-processed bid numbers are remembered and skipped.</p>
<p><b>Where is my report?</b> In your chosen output folder. Use the
OPEN EXCEL or OPEN OUTPUT FOLDER buttons on the Dashboard.</p>
<p><b>Can I stop mid-scan?</b> Yes. STOP SCAN finishes the current bid and
then stops gracefully; everything processed so far is saved.</p>

<h2>Troubleshooting</h2>
<p><b>Browser fails to launch:</b> reinstall the browser runtime
(<code>playwright install chromium</code> in a development setup).</p>
<p><b>Excel file locked:</b> close the report in Excel before scanning again;
the app automatically writes to a timestamped fallback file if needed.</p>
<p><b>No results found:</b> check your keyword spelling and loosen the filters,
then review the live log for the exact rejection reasons.</p>

<h2>Best Practices</h2>
<ul>
<li>Keep the delay between actions at 1.5\u20133 seconds so the scanner behaves
like a normal user. Stability matters more than speed.</li>
<li>Run one scan at a time and avoid excessively frequent scans.</li>
<li>Use \u201cVisible Browser\u201d the first time so you can watch it work.</li>
<li>Review the log after each run; every decision is recorded there.</li>
</ul>
"""


class HelpPage(QWidget):
    """Scrollable rich-text help documentation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Help")
        title.setObjectName("PageTitle")
        layout.addWidget(title)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML)
        layout.addWidget(browser, 1)
