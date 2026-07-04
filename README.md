# TenderIQ Pro

**Automated GeM Bid Scanner with a Modern Desktop UI**

TenderIQ Pro scans the [Government e-Marketplace (GeM)](https://bidplus.gem.gov.in/all-bids) for manpower tenders, downloads and reads every bid PDF, validates them against user‑configurable rules, and exports a clean Excel report – all through an intuitive PySide6 interface.  
A headless `main.py` script is also included for server/automation use.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/UI-PySide6-41cd52.svg" alt="PySide6"/>
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"/>
</p>

---

## Features

- 🖥️ **Desktop Application** – Built with PySide6, featuring a dashboard, history, settings, and theme support (light/dark).
- 🔍 **One‑Click Scanning** – Enter a keyword (default: `manpower`), set the maximum number of bids, and let the app do the rest.
- 📄 **PDF Parsing** – Automatically extracts Bid Number, Dated, Bid End Date, Item Category, MSE Relaxation, and States/UT from downloaded GeM bid documents.
- ✅ **Smart Filtering** – Three configurable rules decide if a tender qualifies (item category, MSE relaxation, allowed states).
- 📊 **Excel Export** – Only matched tenders are written to `output/matched_tenders.xlsx`.
- 🧹 **Automatic Cleanup** – Downloaded PDFs are deleted after processing to keep the workspace clean.
- 📈 **History & Statistics** – All scan results are stored in a local SQLite database and can be reviewed on the History page.
- ⚙️ **Configurable** – All filtering criteria and timeouts are adjustable via the Settings page (or `config.json`).
- 🔄 **Duplicate Prevention** – Already‑processed bid numbers are tracked in `processed_bids.json`.
- 📝 **Detailed Logging** – Every action is logged to the console and to `logs/scanner.log`.
- 🆙 **Built‑in Updater** – Checks for new releases on GitHub and can download updates.
- 🧰 **Headless Mode** – Run the scanner without the UI using `python main.py` (ideal for scheduled tasks).

---

## Validation Rules

A tender appears in the final Excel report **only if all three conditions are met**:

| # | Field                                                       | Required Value                            |
|---|-------------------------------------------------------------|-------------------------------------------|
| 1 | Item Category                                               | Contains “Manpower”                       |
| 2 | MSE Relaxation for Years Of Experience and Turnover         | Equals “Yes”                              |
| 3 | Name of States / UT for geographical presence is required   | “Maharashtra” **or** “Not Applicable”     |

These values can be changed under **Settings** in the desktop app or directly in `config.json`.

---

## Folder Structure
folder structure : 
tenderiq-pro-main/
│   .gitignore
│   app.py
│   CHANGELOG.md
│   config.json
│   LICENSE
│   main.py
│   main.spec
│   processed_bids.json
│   README.md
│   requirements.txt
│   setup.bat
│   TenderIQPro.spec.txt
│   version.py
│
├───assets
│   └───icons
│           about.svg
│           dashboard.svg
│           excel.svg
│           folder.svg
│           help.svg
│           history.svg
│           logo.svg
│           reset.svg
│           settings.svg
│           start.svg
│           stop.svg
│           theme.svg
│
├───core
│       browser.py
│       downloader.py
│       excel_writer.py
│       logger.py
│       matcher.py
│       pdf_reader.py
│       processed_bids.py
│       utils.py
│       __init__.py
│
├───database
│       .gitkeep
│       history.db
│       history_db.py
│       __init__.py
│
├───docs
│       INTEGRATION_PLAN.md
│
├───downloads
├───logs
│       scanner.log
│
├───output
│       matched_tenders.xlsx
│
├───resources
│       .gitkeep
│
├───services
│       extra_filters.py
│       qt_log_handler.py
│       scan_worker.py
│       settings_manager.py
│       updater.py
│       __init__.py
│
├───styles
│       dark.qss
│       light.qss
│       theme.py
│
└───ui
    │   main_window.py
    │   paths.py
    │   __init__.py
    │
    ├───dialogs
    │      update_dialog.py
    │      welcome_dialog.py
    │      __init__.py
    │   
    │
    ├───pages
    │       about_page.py
    │       dashboard_page.py
    │       help_page.py
    │       history_page.py
    │       settings_page.py
    │       __init__.py
    │
    └───widgets
           card.py
           sidebar.py
           stat_card.py
           __init__.py

---

## Installation

python -m venv venv  
venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller

---

### Prerequisites

- Python **3.10** or later
- Internet connection (GeM portal must be reachable)
- Windows, macOS, or Linux with a graphical environment (the desktop app requires a display; headless mode does not)

### One‑Command Setup (Windows)

```bat
setup.bat

This creates a virtual environment, installs all dependencies, and downloads the required Chromium browser binary.

After completion, activate the environment:

CMD: venv\Scripts\activate.bat

PowerShell: venv\Scripts\Activate.ps1

Manual Setup
bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright's Chromium browser (required for both UI and headless)
playwright install chromium
On Linux, if you encounter missing system libraries, run:

bash
playwright install-deps chromium
Usage
Desktop Application
From the project root, with the virtual environment activated:

bash
python app.py
Use the Dashboard to start/stop a scan, view live logs, and see quick stats.

Settings lets you adjust the keyword, filter rules, maximum bids, and timeouts – changes are saved to config.json.

Review past results on the History page; double‑click a row to open the Excel file.

Switch between light and dark themes via the toggle in the sidebar.

Headless Mode (Terminal)
bash
python main.py
This runs the scanner in the background (no GUI) and writes the same Excel output.
You can limit the number of bids processed by setting max_bids_to_process in config.json; 0 means process all bids found.

Tip: The headless script is perfect for Windows Task Scheduler, cron jobs, or CI/CD pipelines.

Configuration
All configurable parameters live in config.json:

json
{
  "keyword": "manpower",
  "allowed_item_category": "Manpower",
  "mse_relaxation": "Yes",
  "allowed_states": ["Maharashtra", "Not Applicable"],
  "max_bids_to_process": 0,
  "headless": false,
  "page_load_timeout_ms": 60000,
  "download_timeout_ms": 30000
}
The desktop app writes changes made in the Settings page back to this file.

Building an Executable
TenderIQ Pro can be packaged into a standalone .exe (Windows) using PyInstaller.
A pre‑made spec file (TenderIQPro.spec.txt) is included. Adjust paths if necessary and run:

bash
pyinstaller TenderIQPro.spec.txt
The distributable folder will appear under dist/.

Expected Output
output/matched_tenders.xlsx contains only tenders that passed all three validation rules, with columns:

Sr No	Bid Number	Dated	Bid End Date
1	GEM/2026/B/...	01-07-2026	15-07-2026
2	GEM/2026/B/...	02-07-2026	18-07-2026
Full details of every processed tender (matched/rejected and why) are recorded in logs/scanner.log.

Troubleshooting
Symptom	Likely Solution
Browser fails to launch	Run playwright install chromium again; on Linux also playwright install-deps chromium
Search box or bid links not found	GeM may have updated its HTML. Update selectors in core/browser.py
Downloads timeout	Increase download_timeout_ms in config.json; ensure your OS allows automatic downloads
PDF fields show "Not Found"	Check logs/scanner.log for the exact text and adjust regex patterns in core/pdf_reader.py
Excel file locked	Close matched_tenders.xlsx before re‑running (Windows locks open files)
No matches even though bids look correct	Verify your rules in Settings or config.json; matching is case‑insensitive
UI won't start / missing Qt DLLs	Reinstall PySide6: pip install --upgrade PySide6
Notes on Responsible Use
This tool only interacts with the public, unauthenticated bid listing pages of the GeM portal, exactly as a human user would. It does not bypass any login or access controls. Please respect GeM’s terms of use and avoid running the scanner excessively frequently, which could burden their public servers.

