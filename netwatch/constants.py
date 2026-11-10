"""Shared constants for Netwatch.

Everything that a future version of us might want to tweak lives here:
the app name, the license tier limits, the free-tier nag message, the
file names used on disk.
"""

APP_NAME = "Netwatch"
APP_VERSION = "0.1.0"

# --- License tiers -----------------------------------------------------

# Tier name -> maximum number of devices allowed.
TIER_LIMITS = {
    "free": 10,
    "personal": 250,
    "pro": 5000,
}

# Short codes used inside license keys. These are what you type into
# tools/keygen.py when you sell a license.
TIER_CODES = {
    "PERS": "personal",
    "PRO": "pro",
}

# The prefix that appears at the start of every license key. Once you
# have sold licenses, DO NOT change this — old keys would stop working.
KEY_PREFIX = "NWTC"

# --- File locations (relative to the data directory) ------------------

DATA_DIRNAME = "data"
DB_FILENAME = "netwatch.json"
LICENSE_FILENAME = "license.key"

# --- Free-tier nag (WinRAR style) -------------------------------------

NAG_TITLE = f"{APP_NAME} — Free Version"

NAG_MESSAGE = (
    "Netwatch is a free, local, privacy-friendly tool.\n\n"
    "If it helps you, please consider supporting the project so I can "
    "buy my first car!"
)