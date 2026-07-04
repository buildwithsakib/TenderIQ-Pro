"""
version.py
----------
Single source of truth for TenderIQ Pro application metadata.

Used by:
    - The UI (window title, sidebar branding, About window, status bar)
    - The future update system (version comparison, release notes)
    - The PyInstaller / installer build scripts (version resources)
"""

# ---- Application identity -------------------------------------------------
APP_NAME = "TenderIQ Pro"
APP_SUBTITLE = "GeM Tender Intelligence Platform"
APP_VERSION = "1.0.0"
APP_DEVELOPER = "Sakib Shaikh"
ORGANIZATION_NAME = "Sakib Shaikh"
APP_COPYRIGHT = "\u00a9 2026 Sakib Shaikh"

# ---- Contact details (placeholders until public release) ------------------
GITHUB_URL = "https://github.com/buildwithsakib"
CONTACT_EMAIL = "sakibbhaisk7@gmail.com"
CONTACT_PHONE = "+91-9921989670"

# ---- Update system architecture -------------------------------------------
# The update checker (wired during backend integration) compares APP_VERSION
# against the latest version published at UPDATE_FEED_URL. The endpoint is a
# placeholder by design; point it at a real releases.json before shipping.
UPDATE_FEED_URL = "https://example.com/tenderiq/releases.json"
RELEASE_NOTES_URL = "https://example.com/tenderiq/release-notes"
