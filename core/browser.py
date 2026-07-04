"""
browser.py
----------
Playwright-based browser automation for the GeM Bid Portal.
Handles sort selection (fully automatic), search, bid listing parsing,
PDF download, and pagination.
"""

import shutil
import os
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

from playwright.sync_api import (
    sync_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)

from core.logger import get_logger

logger = get_logger(__name__)


# --------------------------------------------------------------------------
# SELECTOR CONSTANTS
# --------------------------------------------------------------------------
GEM_SEARCH_INPUT_SELECTOR = "input#searchBid"
GEM_SEARCH_BUTTON_SELECTOR = "#searchBidRA"
GEM_RESULTS_CONTAINER_SELECTOR = "#bidCard"
GEM_BID_CARD_SELECTOR = "div.card"
GEM_BID_NUMBER_LINK_SELECTOR = "a.bid_no_hover"
GEM_START_DATE_SELECTOR = "span.start_date"
GEM_END_DATE_SELECTOR = "span.end_date"

SORT_OPTION_LABEL = "Bid Start Date : Latest First"
SORT_OPTION_KEYWORD = "Latest First"       # used to identify the option in custom dropdowns

# Pagination selectors (tried in order)
PAGINATION_SELECTORS = [
    "li.next:not(.disabled) a",
    "a:has-text('Next'):not([disabled])",
    "span.next:not(.disabled) a",
    "a[aria-label='Next page']:not([disabled])",
    "a.paginate_button.next:not(.disabled)",
]


@dataclass
class BidListing:
    """A single bid row."""
    bid_number: str
    start_date: str
    end_date: str
    row_index: int


class GemBrowser:
    """Manages Playwright browser for GeM scanning."""

    def __init__(self, config: dict):
        self.config = config
        self.gem_url = config.get("gem_url", "https://bidplus.gem.gov.in/all-bids")
        self.search_keyword = config.get("search_keyword", "manpower")
        self.download_dir = os.path.abspath(config.get("download_dir", "downloads"))
        self.headless = config.get("headless", False)
        self.page_load_timeout_ms = config.get("page_load_timeout_ms", 60000)
        self.retry_count = config.get("navigation_retry_count", 3)
        self.slow_mo_ms = config.get("browser_slow_mo_ms", 0)

        self._playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.close()

    def start(self):
        # --------------------- ADDED LINES ---------------------
        # Set the PLAYWRIGHT_BROWSERS_PATH so that Playwright finds
        # the bundled Chromium (local "browsers" folder)
        if getattr(sys, 'frozen', False):
            # Running as compiled .exe (PyInstaller)
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.join(sys._MEIPASS, 'browsers')
        else:
            # Running from source (development)
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = os.path.join(os.path.dirname(__file__), '..', 'browsers')
        # -------------------------------------------------------

        os.makedirs(self.download_dir, exist_ok=True)
        logger.info("Launching Chromium browser (headless=%s)...", self.headless)
        self._playwright = sync_playwright().start()

        chrome_path = (
            shutil.which("chrome")
            or shutil.which("msedge")
            or shutil.which("brave")
        )

        if chrome_path:
            logger.info("Using system browser: %s", chrome_path)
            self.browser = self._playwright.chromium.launch(
                executable_path=chrome_path,
                headless=self.headless,
                slow_mo=self.slow_mo_ms,
            )
        else:
            logger.info("Using bundled Playwright Chromium.")
            self.browser = self._playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo_ms,
            )

        # Create browser context
        self.context = self.browser.new_context(accept_downloads=True)
        self.context.set_default_timeout(self.page_load_timeout_ms)
        self.page = self.context.new_page()
        logger.info("Browser started successfully.")

    def close(self):
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self._playwright:
                self._playwright.stop()
            logger.info("Browser closed.")
        except Exception as exc:
            logger.warning("Error closing browser: %s", exc)

    # ------------------------------------------------------------------
    # SORT ORDER – fully automatic (multiple strategies)
    # ------------------------------------------------------------------
    def _select_sort_order(self) -> None:
        """
        Automatically set the sort order to "Bid Start Date : Latest First".
        Uses several methods in sequence:
          1. Native <select> with option "Latest First"
          2. Click "Sort By" label, then pick from custom dropdown
          3. Direct click on option element containing "Latest First" (if visible)
        """
        # --- Strategy 1: Native <select> ---
        select_selectors = [
            "#sortbyid",
            "select[id*='sort']",
            "select[class*='sort']",
            "select[name*='sort']",
            "select[aria-label*='Sort']",
        ]
        for sel in select_selectors:
            try:
                select = self.page.locator(sel)
                if select.count() == 0 or not select.first.is_visible():
                    continue
                # Check if it has the required option
                option = select.locator(f"option:has-text('{SORT_OPTION_KEYWORD}')")
                if option.count() > 0:
                    select.first.select_option(label=SORT_OPTION_LABEL)
                    logger.info("Sort order set via native <select> (%s).", sel)
                    time.sleep(1)
                    return
            except Exception as e:
                logger.debug("Selector %s failed: %s", sel, e)
                continue

        # --- Strategy 2: Click "Sort By" trigger, then choose option ---
        try:
            # Locate any element containing "Sort By" (could be label, span, div)
            sort_by_locator = self.page.locator("text=Sort By")
            if sort_by_locator.count() > 0:
                sort_by_locator.first.click()
                logger.debug("Clicked 'Sort By' trigger.")
                time.sleep(1)
                # Now look for the option with "Latest First" inside a dropdown
                option_loc = self.page.locator(
                    f"text={SORT_OPTION_KEYWORD}"
                ).first
                if option_loc.is_visible():
                    option_loc.click()
                    logger.info("Sort order set via custom dropdown.")
                    time.sleep(1)
                    return
        except Exception as e:
            logger.debug("Strategy 2 failed: %s", e)

        # --- Strategy 3: Last resort – click a visible element containing "Latest First" ---
        try:
            direct_option = self.page.locator(f"text={SORT_OPTION_KEYWORD}").first
            if direct_option.is_visible():
                direct_option.click()
                logger.info("Sort order set by clicking '%s' directly.", SORT_OPTION_KEYWORD)
                time.sleep(1)
                return
        except Exception:
            pass

        logger.warning("Could not set sort order automatically – proceeding without it.")

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def open_and_search(self):
        """Navigate, set sort, type keyword, search."""
        last_error = None
        for attempt in range(1, self.retry_count + 1):
            try:
                logger.info("Opening GeM (attempt %d/%d): %s", attempt, self.retry_count, self.gem_url)
                self.page.goto(self.gem_url, wait_until="domcontentloaded")
                self.page.wait_for_selector(GEM_SEARCH_INPUT_SELECTOR, timeout=self.page_load_timeout_ms)

                # Apply sort (fully automatic)
                self._select_sort_order()

                # Type and search
                self.page.fill(GEM_SEARCH_INPUT_SELECTOR, self.search_keyword)
                logger.info("Typed search keyword '%s'.", self.search_keyword)
                self.page.click(GEM_SEARCH_BUTTON_SELECTOR)
                logger.info("Clicked Search. Waiting for results...")
                self.page.wait_for_selector(GEM_RESULTS_CONTAINER_SELECTOR, timeout=self.page_load_timeout_ms)
                time.sleep(2)
                return
            except PlaywrightTimeoutError as exc:
                last_error = exc
                logger.warning("Timeout attempt %d/%d: %s", attempt, self.retry_count, exc)
                time.sleep(2)

        logger.error("Search failed after %d attempts.", self.retry_count)
        raise RuntimeError("Unable to load GeM search results.") from last_error

    # ------------------------------------------------------------------
    # Current page listings
    # ------------------------------------------------------------------
    def get_all_listings(self) -> List[BidListing]:
        """Parse bid cards from the **current** page only."""
        cards = self.page.locator(GEM_BID_CARD_SELECTOR)
        count = cards.count()
        logger.info("Found %d bid cards on this page.", count)

        listings = []
        for i in range(count):
            card = cards.nth(i)
            try:
                link = card.locator(GEM_BID_NUMBER_LINK_SELECTOR)
                if link.count() == 0:
                    continue
                bid_number = link.first.inner_text().strip()
                start = ""
                if card.locator(GEM_START_DATE_SELECTOR).count() > 0:
                    start = card.locator(GEM_START_DATE_SELECTOR).first.inner_text().strip()
                end = ""
                if card.locator(GEM_END_DATE_SELECTOR).count() > 0:
                    end = card.locator(GEM_END_DATE_SELECTOR).first.inner_text().strip()
                listings.append(BidListing(bid_number, start, end, i))
            except Exception as exc:
                logger.warning("Skipping card %d: %s", i, exc)
                continue

        logger.info("Parsed %d listings.", len(listings))
        return listings

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------
    def go_to_next_page(self) -> bool:
        """Click Next, return True if new page loaded."""
        old_first = ""
        try:
            first = self.page.locator(GEM_BID_NUMBER_LINK_SELECTOR).first
            old_first = first.inner_text()
        except Exception:
            pass

        next_btn = None
        for selector in PAGINATION_SELECTORS:
            try:
                loc = self.page.locator(selector)
                if loc.count() > 0 and loc.first.is_visible() and loc.first.is_enabled():
                    next_btn = loc.first
                    logger.debug("Found Next via: %s", selector)
                    break
            except Exception:
                continue

        if next_btn is None:
            logger.info("No clickable Next link found – last page.")
            return False

        logger.info("Clicking Next.")
        next_btn.click()

        try:
            self.page.wait_for_function(
                """
                (old) => {
                    const el = document.querySelector('a.bid_no_hover');
                    return el && el.innerText.trim() !== old;
                }
                """,
                arg=old_first,
                timeout=self.page_load_timeout_ms,
            )
            time.sleep(1)
            return True
        except PlaywrightTimeoutError:
            logger.warning("Next page load timeout.")
            return False
        except Exception as exc:
            logger.error("Pagination error: %s", exc)
            return False

    # ------------------------------------------------------------------
    # PDF download
    # ------------------------------------------------------------------
    def click_bid_number(self, listing: BidListing) -> Optional[str]:
        """Click bid number, save downloaded PDF. Return path or None."""
        cards = self.page.locator(GEM_BID_CARD_SELECTOR)
        if listing.row_index >= cards.count():
            logger.error("Row index %d out of range for %s", listing.row_index, listing.bid_number)
            return None

        link = cards.nth(listing.row_index).locator(GEM_BID_NUMBER_LINK_SELECTOR).first
        try:
            with self.page.expect_download(
                timeout=self.config.get("download_timeout_ms", 60000)
            ) as dl:
                link.click()
                logger.info("Clicked bid number '%s' to download PDF.", listing.bid_number)

            download = dl.value
            safe_name = "".join(c for c in (download.suggested_filename or f"{listing.bid_number}.pdf")
                                if c not in '<>:"/\\|?*')
            dest = os.path.join(self.download_dir, safe_name)
            download.save_as(dest)
            logger.info("Saved PDF to: %s", dest)
            return dest

        except PlaywrightTimeoutError:
            logger.error("Timeout downloading PDF for %s", listing.bid_number)
            return None
        except Exception as exc:
            logger.error("Download error for %s: %s", listing.bid_number, exc)
            return None
