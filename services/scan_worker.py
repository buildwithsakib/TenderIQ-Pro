"""
scan_worker.py
-------------
QThread worker that runs the GeM tender scanning loop using the existing
backend (core/*) without any modifications. Emits live signals for logs,
statistics, and completion.
"""

import os
import time
import random
import traceback
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.browser import GemBrowser
from core.downloader import wait_for_pdf_ready
from core.pdf_reader import extract_fields_from_pdf
from core.matcher import is_matching_tender
from core.excel_writer import ExcelWriter
from core.processed_bids import load_processed_bids, save_processed_bid
from core.utils import ensure_directories, safe_delete_file, clear_downloads_folder
from core.logger import get_logger
from services.extra_filters import check_extra_requirements

logger = get_logger(__name__)


class ScanWorker(QThread):
    # Signals for the UI
    log_msg = Signal(str)
    stats_update = Signal(int, int, int, int, int)  # checked, matched, rejected, skipped, dup
    scan_finished = Signal(str)        # report path on success, or empty if stopped
    scan_error = Signal(str)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.config = config
        self._stop_flag = False

    def stop(self):
        """Request graceful stop. The loop checks this flag between bids."""
        self._stop_flag = True

    def run(self):
        try:
            self._scan_loop()
        except Exception as e:
            tb = traceback.format_exc()
            self.log_msg.emit(f"FATAL ERROR: {e}\n{tb}")
            self.scan_error.emit(str(e))

    def _scan_loop(self):
        # Unpack config
        keyword = self.config.get("search_keyword", "Manpower")
        download_dir = self.config.get("download_dir", "downloads")
        output_dir = self.config.get("output_dir", "output")
        log_dir = self.config.get("log_dir", "logs")
        output_file = self.config.get("output_file", "matched_tenders.xlsx")
        headless = self.config.get("headless", False)
        min_delay = self.config.get("min_action_delay_s", 1.5)
        max_delay = self.config.get("max_action_delay_s", 3.0)
        skip_duplicates = self.config.get("skip_duplicates", True)
        delete_pdf = self.config.get("delete_pdf_after_processing", True)
        max_bids = self.config.get("max_bids_to_process", 0)
        restart_after = self.config.get("restart_browser_after_bids", 0)

        # Prepare folders
        ensure_directories(download_dir, output_dir, log_dir)
        clear_downloads_folder(download_dir)

        output_path = os.path.join(output_dir, output_file)
        writer = ExcelWriter(output_path)

        processed_bids = set(load_processed_bids()) if skip_duplicates else set()
        self.log_msg.emit(f"Loaded {len(processed_bids)} processed bid(s).")

        stats = {"checked": 0, "matched": 0, "rejected": 0,
                 "skipped": 0, "duplicate": 0}

        browser = None
        bid_count_since_restart = 0

        try:
            browser = GemBrowser(self.config)
            browser.start()
            browser.search_keyword = keyword  # override with user's keyword
            browser.open_and_search()

            page_num = 1
            while not self._stop_flag:
                listings = browser.get_all_listings()
                if not listings:
                    self.log_msg.emit(f"No listings on page {page_num}. Stopping.")
                    break

                self.log_msg.emit(f"Page {page_num}: {len(listings)} bids found.")

                for idx, listing in enumerate(listings, 1):
                    if self._stop_flag:
                        break
                    if max_bids and stats["checked"] >= max_bids:
                        break

                    # Check duplicate
                    if skip_duplicates and listing.bid_number in processed_bids:
                        stats["duplicate"] += 1
                        self._emit_stats(stats)
                        self.log_msg.emit(f"SKIP DUPLICATE: {listing.bid_number}")
                        continue

                    self.log_msg.emit(f"[{stats['checked']+1}] Processing: {listing.bid_number}")
                    stats["checked"] += 1
                    self._emit_stats(stats)

                    pdf_path = None
                    bid_processed = False
                    try:
                        pdf_path = browser.click_bid_number(listing)
                        if not pdf_path:
                            self.log_msg.emit(f"PDF download failed for {listing.bid_number}")
                            stats["skipped"] += 1
                            self._emit_stats(stats)
                            continue

                        if not wait_for_pdf_ready(pdf_path, timeout_seconds=self.config.get("download_timeout_ms", 60000)/1000):
                            self.log_msg.emit(f"PDF not ready for {listing.bid_number}")
                            stats["skipped"] += 1
                            self._emit_stats(stats)
                            continue

                        extracted = extract_fields_from_pdf(pdf_path)
                        self.log_msg.emit(f"Extracted: {extracted}")

                        # Core matcher
                        matches, reason = is_matching_tender(extracted, self.config)

                        # Extra filters (experience & turnover)
                        if matches:
                            extra_ok, extra_reason = check_extra_requirements(pdf_path, self.config)
                            if not extra_ok:
                                matches = False
                                reason = extra_reason

                        # MSE filter mode "Any" bypass
                        mse_mode = self.config.get("mse_filter_mode", "Yes")
                        if mse_mode == "Any":
                            # Override: ignore MSE check, only item category and states matter
                            actual_category = extracted.get("item_category", "").lower()
                            required_category = self.config.get("allowed_item_category", "Manpower").lower()
                            cond1 = required_category in actual_category
                            allowed_states = [s.lower() for s in self.config.get("allowed_states", [])]
                            actual_state = extracted.get("geographical_states", "").lower()
                            cond3 = any(s in actual_state for s in allowed_states)
                            if cond1 and cond3 and (not extra_ok if extra_reason else True):
                                matches = True
                                reason = "All conditions (MSE ignored)"
                            else:
                                matches = False
                                reason = "Failed item category or state check (MSE ignored)"

                        if matches:
                            stats["matched"] += 1
                            self.log_msg.emit(f"MATCH: {listing.bid_number}")
                            writer.add_tender({
                                "bid_number": extracted.get("bid_number") or listing.bid_number,
                                "dated": extracted.get("dated") or listing.start_date,
                                "bid_end_date": extracted.get("bid_end_date") or listing.end_date,
                                "contract_period": extracted.get("contract_period", ""),
                                "address": extracted.get("address", ""),
                                "eligible": "Yes",
                            })
                            writer._save()   # incremental save
                        else:
                            stats["rejected"] += 1
                            self.log_msg.emit(f"REJECTED: {listing.bid_number} - {reason}")

                        bid_processed = True

                    except Exception as e:
                        self.log_msg.emit(f"Error processing {listing.bid_number}: {e}")
                        stats["skipped"] += 1
                    finally:
                        if pdf_path and delete_pdf:
                            safe_delete_file(pdf_path)
                        if bid_processed and skip_duplicates:
                            save_processed_bid(listing.bid_number)
                            processed_bids.add(listing.bid_number)

                    self._emit_stats(stats)

                    # Human-like delay
                    delay = random.uniform(min_delay, max_delay)
                    time.sleep(delay)

                    bid_count_since_restart += 1
                    if restart_after > 0 and bid_count_since_restart >= restart_after:
                        self.log_msg.emit(f"Restarting browser after {bid_count_since_restart} bids...")
                        browser.close()
                        browser.start()
                        browser.search_keyword = keyword
                        browser.open_and_search()
                        bid_count_since_restart = 0

                if self._stop_flag:
                    self.log_msg.emit("Stop requested. Ending after current page.")
                    break
                if max_bids and stats["checked"] >= max_bids:
                    break
                if not browser.go_to_next_page():
                    self.log_msg.emit("Last page reached.")
                    break
                page_num += 1

        except Exception as e:
            self.log_msg.emit(f"Scan error: {e}")
            raise
        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
            writer.finalize()
            final_path = writer.fallback_path if writer._save_failed else output_path
            if os.path.exists(final_path):
                self.log_msg.emit(f"Report saved: {final_path}")
                self.scan_finished.emit(final_path)
            else:
                self.scan_finished.emit("")

    def _emit_stats(self, stats: dict):
        self.stats_update.emit(
            stats["checked"], stats["matched"], stats["rejected"],
            stats["skipped"], stats["duplicate"]
        )