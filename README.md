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

---

## Installation

**open cmd in current directory** 

setup.bat

---

### Prerequisites

- Python **3.10** or later
- Internet connection (GeM portal must be reachable)
- Windows, macOS, or Linux with a graphical environment (the desktop app requires a display; headless mode does not)

---

## Configuration
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

---
