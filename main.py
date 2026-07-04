"""
main.py
-------
GeM Manpower Tender Scanner – writes only eligible bids to Excel,
batching writes per page. Marks all successfully processed bids in JSON.
"""

import os
import sys
import signal

from core.logger import setup_logger, get_logger
from core.utils import load_config, ensure_directories, safe_delete_file, clear_downloads_folder
from core.browser import GemBrowser
from core.downloader import wait_for_pdf_ready
from core.pdf_reader import extract_fields_from_pdf
from core.matcher import is_matching_tender
from core.excel_writer import ExcelWriter
from core.processed_bids import load_processed_bids, save_processed_bid

SHUTDOWN_REQUESTED = False


def _handle_shutdown_signal(signum, frame):
    global SHUTDOWN_REQUESTED
    SHUTDOWN_REQUESTED = True
    print("\n[SHUTDOWN] Ctrl+C detected. Stopping after current bid completes...\n")


def main() -> int:
    signal.signal(signal.SIGINT, _handle_shutdown_signal)

    try:
        config = load_config("config.json")
    except Exception as exc:
        print(f"FATAL: Could not load config.json: {exc}")
        return 1

    setup_logger(
        log_dir=config.get("log_dir", "logs"),
        log_file=config.get("log_file", "scanner.log"),
    )
    logger = get_logger(__name__)
    logger.info("=" * 70)
    logger.info("Starting GeM Manpower Tender Scanner")
    logger.info("Press Ctrl+C at any time to stop gracefully.")
    logger.info("=" * 70)

    download_dir = config.get("download_dir", "downloads")
    output_dir = config.get("output_dir", "output")
    log_dir = config.get("log_dir", "logs")
    ensure_directories(download_dir, output_dir, log_dir)
    clear_downloads_folder(download_dir)

    output_path = os.path.join(output_dir, config.get("output_file", "matched_tenders.xlsx"))
    writer = ExcelWriter(output_path)

    processed_bids = set(load_processed_bids())
    logger.info("Loaded %d previously processed bid(s).", len(processed_bids))

    total_processed = 0
    total_matched = 0
    max_bids = config.get("max_bids_to_process", 0)

    page_eligible_bids = []

    def flush_page_eligible():
        nonlocal total_matched
        if not page_eligible_bids:
            return
        count = len(page_eligible_bids)
        logger.info("Eligible Found: %d", count)
        logger.info("Writing %d records to Excel...", count)
        for tender in page_eligible_bids:
            writer.add_tender(tender)
        writer._save()
        page_eligible_bids.clear()
        logger.info("Excel Updated Successfully.")

    try:
        with GemBrowser(config) as gem:
            gem.open_and_search()
            page_num = 1

            while not SHUTDOWN_REQUESTED:
                listings = gem.get_all_listings()
                if not listings:
                    logger.info("No listings on page %d.", page_num)
                    break

                logger.info("=" * 40)
                logger.info("Processing Page %d: %d listings", page_num, len(listings))
                logger.info("=" * 40)

                for idx, listing in enumerate(listings, start=1):
                    if SHUTDOWN_REQUESTED:
                        logger.info("Shutdown requested – skipping remaining bids on this page.")
                        break
                    if max_bids and total_processed >= max_bids:
                        break

                    if listing.bid_number in processed_bids:
                        logger.info("SKIPPED Already Processed: %s", listing.bid_number)
                        continue

                    logger.info("[Page %d / %d/%d] Processing: %s",
                                page_num, idx, len(listings), listing.bid_number)
                    total_processed += 1
                    pdf_path = None
                    bid_successfully_processed = False

                    try:
                        pdf_path = gem.click_bid_number(listing)
                        if not pdf_path:
                            logger.warning("Skipping bid '%s' - PDF download failed.", listing.bid_number)
                            continue

                        if not wait_for_pdf_ready(pdf_path, timeout_seconds=config.get("download_timeout_ms", 60000)/1000):
                            logger.warning("Skipping bid '%s' - PDF not ready.", listing.bid_number)
                            continue

                        extracted = extract_fields_from_pdf(pdf_path)
                        logger.info("Extracted fields: %s", extracted)
                        matches, reason = is_matching_tender(extracted, config)

                        if matches:
                            total_matched += 1
                            logger.info("MATCH: %s", listing.bid_number)
                            page_eligible_bids.append({
                                "bid_number": extracted.get("bid_number") or listing.bid_number,
                                "dated": extracted.get("dated") or listing.start_date,
                                "bid_end_date": extracted.get("bid_end_date") or listing.end_date,
                                "contract_period": extracted.get("contract_period", ""),
                                "address": extracted.get("address", ""),
                                "eligible": "Yes",
                            })
                        else:
                            logger.info("REJECTED: %s - %s", listing.bid_number, reason)

                        # Bid was fully processed – mark it to avoid re-download
                        bid_successfully_processed = True

                    except Exception as exc:
                        logger.error("Error processing %s: %s", listing.bid_number, exc, exc_info=True)
                        # Not marking as processed – will retry next run
                    finally:
                        if pdf_path:
                            safe_delete_file(pdf_path)
                        if bid_successfully_processed:
                            save_processed_bid(listing.bid_number)

                # Flush eligible bids for the page
                flush_page_eligible()

                if SHUTDOWN_REQUESTED:
                    logger.info("Shutdown after current page.")
                    break

                if max_bids and total_processed >= max_bids:
                    break
                if not gem.go_to_next_page():
                    break
                page_num += 1

            flush_page_eligible()

    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
    finally:
        logger.info("Saving final results...")
        writer.finalize()
        logger.info("=" * 70)
        logger.info("Scan complete. Processed %d bids, %d eligible. Excel saved.",
                    total_processed, total_matched)
        logger.info("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
