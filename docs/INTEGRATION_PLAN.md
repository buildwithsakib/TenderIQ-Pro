# TenderIQ Pro - Backend Integration Plan

This document maps every UI control to the existing backend so that the
backend business logic in `core/` is **never modified**. All adaptation
happens in a thin integration layer added during Part 3.

## 1. Architecture Overview

```
app.py (QApplication)
  \-- ui/main_window.py (window, navigation, status bar)
        \-- ui/pages/dashboard_page.py  <-- user input + live output
        \-- ui/pages/*                   (history, settings, help, about)

Part 3 adds:
  services/scan_worker.py   QThread worker that runs the scan loop
  services/config_bridge.py Builds the config dict from UI controls
  services/qt_log_handler.py logging.Handler -> Qt signal -> log console
  database/history_db.py    SQLite scan-history storage
  services/updater.py       Version-check architecture (placeholder feed)
```

## 2. UI Control -> Backend Config Mapping

| UI control (DashboardPage)      | config.json key            | Consumed by            |
|---------------------------------|----------------------------|------------------------|
| keyword_input                   | search_keyword             | core/browser.py        |
| mse_combo (Yes/No)              | mse_relaxation             | core/matcher.py        |
| mse_combo (Any)                 | (condition bypassed by integration layer) | services |
| states_list (checked items)     | allowed_states             | core/matcher.py        |
| visible_radio / headless_radio  | headless                   | core/browser.py        |
| output_dir_input                | output_dir                 | main loop / ExcelWriter|
| download_dir_input              | download_dir               | core/browser.py        |
| excel_name_input                | output_file                | main loop / ExcelWriter|
| skip_duplicates_check           | skip_duplicates (new key)  | integration layer      |
| delete_pdf_check                | delete_pdf_after_processing (new key) | integration layer |
| restart_spin                    | restart_browser_after_bids (new key)  | integration layer |
| min_delay_spin / max_delay_spin | min_action_delay_s / max_action_delay_s (new keys) | integration layer |
| experience_combo/_custom        | required_experience_years (new key)   | integration layer |
| turnover_combo/_custom          | required_turnover_lakhs (new key)     | integration layer |

New keys are additive: `core/` reads only the keys it already knows, so
existing behaviour is unchanged. Experience/turnover filtering and the
MSE "Any" bypass are applied by the integration layer on top of the
unchanged `core/matcher.py` result.

## 3. Threading and Control Flow

- The scan runs inside a QThread worker replicating the loop from
  `main.py`, importing `GemBrowser`, `wait_for_pdf_ready`,
  `extract_fields_from_pdf`, `is_matching_tender`, `ExcelWriter`, and
  `processed_bids` **unchanged**.
- STOP SCAN sets a worker flag checked between bids, mirroring the
  `SHUTDOWN_REQUESTED` pattern in `main.py` (graceful, per-bid stop).
- Random human-like delay (min..max seconds) is inserted between bids by
  the worker, never inside `core/`.

## 4. Live Logs and Statistics

- A custom `logging.Handler` is attached to the root logger configured by
  `core/logger.py`; every backend log record is forwarded through a Qt
  signal to the dashboard log console (thread-safe via queued connections).
- The worker emits structured progress signals (checked, matched,
  rejected, skipped, duplicate) that update the StatCard tiles; a QTimer
  drives the elapsed-time display.

## 5. Persistence

- All UI settings are saved into `config.json` (existing keys reused, new
  keys added) so the CLI `main.py` keeps working with the same file.
- Scan history is stored in `database/history.db` (SQLite, stdlib
  `sqlite3`): date, keyword, statistics, and report path per run.

## 6. Update System Architecture

- `version.py` holds APP_VERSION and UPDATE_FEED_URL.
- The updater compares APP_VERSION with the feed's latest version and
  shows release notes; the feed URL is a placeholder by design until a
  release channel exists.
