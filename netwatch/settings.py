"""User settings for Netwatch.

Stores SMTP (email) credentials in `data/settings.json`.
This file is git-ignored — credentials never leave the user's machine.
"""

import json
from pathlib import Path

from .storage import DATA_DIR

SETTINGS_PATH = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "company_email": {
        "host": "smtp.office365.com",
        "port": 587,
        "user": "",
        "password": "",
        "to": "",
    },
    "personal_email": {
        "host": "smtp.gmail.com",
        "port": 587,
        "user": "",
        "password": "",
        "to": "",
    }
}


def load_settings() -> dict:
    """Load settings from disk, filling in defaults for missing keys."""
    if not SETTINGS_PATH.exists():
        return _copy(DEFAULT_SETTINGS)
    try:
        with SETTINGS_PATH.open(encoding="utf-8") as f:
            saved = json.load(f)
    except (json.JSONDecodeError, OSError):
        return _copy(DEFAULT_SETTINGS)

    # Merge saved values over defaults, so newly-added default keys
    # appear even in old settings files.
    result = _copy(DEFAULT_SETTINGS)
    for section, values in saved.items():
        if isinstance(values, dict) and section in result:
            result[section].update(values)
        else:
            result[section] = values
    return result


def save_settings(settings: dict) -> None:
    """Write settings to disk as pretty-printed JSON."""
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def _copy(d: dict) -> dict:
    """Deep-ish copy so callers can't accidentally mutate the defaults."""
    return {k: (v.copy() if isinstance(v, dict) else v) for k, v in d.items()}