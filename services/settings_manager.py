"""
settings_manager.py
-------------------
Loads, saves, and restores config.json.

The backend keys are preserved exactly as core/ expects them; UI-specific
keys are additive, so the CLI scanner (main.py) keeps working with the
same file. Missing keys are always filled from DEFAULT_CONFIG so older
config files upgrade transparently.
"""

import json
import os
from copy import deepcopy

from ui.paths import project_root

CONFIG_FILE = os.path.join(project_root(), "config.json")

DEFAULT_CONFIG = {
    # ---- Backend keys (consumed by core/) --------------------------------
    "gem_url": "https://bidplus.gem.gov.in/all-bids",
    "search_keyword": "Pune",
    "allowed_item_category": "Manpower",
    "mse_relaxation": "Yes",
    "allowed_states": ["Maharashtra", "Not Applicable"],
    "download_dir": "downloads",
    "output_dir": "output",
    "output_file": "matched_tenders.xlsx",
    "log_dir": "logs",
    "log_file": "scanner.log",
    "headless": False,
    "page_load_timeout_ms": 60000,
    "download_timeout_ms": 60000,
    "max_bids_to_process": 0,
    "navigation_retry_count": 3,
    "browser_slow_mo_ms": 0,
    # ---- UI keys (additive; ignored by core/) -----------------------------
    "mse_filter_mode": "Yes",            # Any / Yes / No
    "required_experience_years": 0,       # 0 = no filter
    "required_turnover_lakhs": 0.0,       # 0 = no filter
    "min_action_delay_s": 1.5,
    "max_action_delay_s": 3.0,
    "restart_browser_after_bids": 0,      # 0 = never
    "skip_duplicates": True,
    "delete_pdf_after_processing": True,
    "ui_theme": "dark",
    "first_run_completed": False,
}


class SettingsManager:
    """Read/write access to config.json with default merging."""

    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file

    def load(self) -> dict:
        """Return the full configuration, merging defaults with the file."""
        config = deepcopy(DEFAULT_CONFIG)
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except FileNotFoundError:
            # First launch: persist the defaults immediately.
            self.save(config)
        except json.JSONDecodeError:
            # Corrupted file: work with defaults, keep the file for inspection.
            pass
        return config

    def save(self, config: dict) -> None:
        """Write the full configuration back to config.json."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    def restore_defaults(self) -> dict:
        """Overwrite config.json with DEFAULT_CONFIG and return it."""
        config = deepcopy(DEFAULT_CONFIG)
        self.save(config)
        return config

    def get(self, key: str, default=None):
        """Convenience accessor for a single configuration value."""
        return self.load().get(key, default)

    def set(self, key: str, value) -> None:
        """Update a single key and persist immediately."""
        config = self.load()
        config[key] = value
        self.save(config)
