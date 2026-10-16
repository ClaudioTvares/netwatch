"""Offline license system for Netwatch.

A license key looks like this:

    NWTC-PERS-000123-A7F3B9C2
    ^^^^ ^^^^ ^^^^^^ ^^^^^^^^
    |    |    |      |
    |    |    |      +-- signature (first 8 hex chars of HMAC-SHA256)
    |    |    +--------- serial number (6 digits, for your records)
    |    +-------------- tier code ("PERS" = personal, "PRO" = pro)
    +------------------- fixed prefix (from constants.KEY_PREFIX)

The signature is what makes the key unforgeable. It's computed as:

    HMAC-SHA256(SECRET, f"{tier_code}:{serial}")  →  first 8 hex chars

Only the developer knows SECRET. If a user changes even one character
of a valid key, the recomputed signature won't match and the key is
rejected. This is the same technique used in JWT tokens, AWS API keys,
and webhook signatures.

SECURITY TRADE-OFF
------------------
The SECRET is embedded in this file, so a determined attacker could
extract it by decompiling the packaged .exe. This is acceptable for a
low-priced desktop tool: the cost of a proper online-activation server
outweighs the benefit. If Netwatch ever sells >1000 licenses, revisit
this decision and consider online activation.
"""

import hashlib
import hmac
import re
from dataclasses import dataclass
from pathlib import Path

from .constants import (
    DATA_DIRNAME,
    KEY_PREFIX,
    LICENSE_FILENAME,
    TIER_CODES,
    TIER_LIMITS,
)
from .storage import DATA_DIR


# ---------------------------------------------------------------------
# The SECRET
# ---------------------------------------------------------------------
#
# ⚠️  DO NOT COMMIT THE REAL SECRET TO A PUBLIC GIT REPO.
#
# During development it lives right here. When you're ready to ship,
# you'll load it from an environment variable instead, and keep the
# real value in a local .env file (which is git-ignored).
#
# To make a new secret, run this once in a terminal and paste the output:
#
#   python -c "import secrets; print(secrets.token_hex(32))"
#
# The current value below is a placeholder — replace it before shipping.

_SECRET = b"b5892410848527270cbe01354f1d5c72d32c8b5d2be20497e2f6510f50c41967"


# ---------------------------------------------------------------------
# Key format
# ---------------------------------------------------------------------
#
# Regex breakdown:
#   ^             start of string
#   NWTC          literal prefix (we substitute the real one below)
#   -             dash
#   (PERS|PRO)    tier code: one of these two strings
#   -             dash
#   (\d{6})       exactly 6 digits (serial)
#   -             dash
#   ([0-9A-F]{8}) exactly 8 hex characters, uppercase (signature)
#   $             end of string
#
# We build it dynamically so if you change KEY_PREFIX in constants.py,
# the regex follows.

_TIER_ALTERNATION = "|".join(re.escape(code) for code in TIER_CODES.keys())
_KEY_RE = re.compile(
    rf"^{re.escape(KEY_PREFIX)}-({_TIER_ALTERNATION})-(\d{{6}})-([0-9A-F]{{8}})$"
)


# ---------------------------------------------------------------------
# Signature computation
# ---------------------------------------------------------------------

def _signature_for(tier_code: str, serial: str) -> str:
    """Compute the 8-hex-char signature for a (tier_code, serial) pair.

    Deterministic: same inputs always give the same output. This is
    what lets us validate keys offline — no database lookup needed.
    """
    message = f"{tier_code}:{serial}".encode("ascii")
    digest = hmac.new(_SECRET, message, hashlib.sha256).hexdigest()
    return digest[:8].upper()


def make_key(tier_code: str, serial: int) -> str:
    """Generate a valid license key. Used by tools/keygen.py.

    NOT called by the app at runtime — only by your private keygen tool.
    """
    if tier_code not in TIER_CODES:
        raise ValueError(f"Unknown tier code: {tier_code!r}. "
                         f"Valid codes: {list(TIER_CODES)}")
    if not (1 <= serial <= 999_999):
        raise ValueError("Serial must be between 1 and 999999.")
    serial_str = f"{serial:06d}"
    signature = _signature_for(tier_code, serial_str)
    return f"{KEY_PREFIX}-{tier_code}-{serial_str}-{signature}"


# ---------------------------------------------------------------------
# The License object
# ---------------------------------------------------------------------

@dataclass
class License:
    """A validated license: what tier it is, and its serial number.

    `tier` is one of "free", "personal", "pro". The "free" tier has no
    serial or raw key — it's the default state when no license is stored.
    """
    tier: str
    serial: str | None = None
    raw_key: str | None = None

    @property
    def max_devices(self) -> int:
        return TIER_LIMITS.get(self.tier, TIER_LIMITS["free"])

    @property
    def is_paid(self) -> bool:
        return self.tier != "free"

    def describe(self) -> str:
        """Human-readable one-liner, used in the GUI and About dialog."""
        if self.tier == "free":
            return f"Free edition (up to {self.max_devices} devices)"
        label = self.tier.capitalize()
        return (
            f"{label} edition — serial {self.serial} "
            f"(up to {self.max_devices} devices)"
        )


def validate_key(raw_key: str) -> License | None:
    """Parse and cryptographically verify a license key.

    Returns a License on success, None on any failure (bad format,
    unknown tier, wrong signature).
    """
    if not raw_key:
        return None

    # Normalize: strip whitespace, uppercase (users paste with lowercase).
    candidate = raw_key.strip().upper()

    match = _KEY_RE.match(candidate)
    if not match:
        return None

    tier_code, serial, given_signature = match.groups()

    expected_signature = _signature_for(tier_code, serial)

    # Timing-safe comparison. hmac.compare_digest takes the same time
    # regardless of where the strings first differ, defeating timing
    # attacks. Overkill for a $10 product, but a good habit.
    if not hmac.compare_digest(given_signature, expected_signature):
        return None

    return License(
        tier=TIER_CODES[tier_code],
        serial=serial,
        raw_key=candidate,
    )


# ---------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------

LICENSE_PATH: Path = DATA_DIR / LICENSE_FILENAME


def load_license() -> License:
    """Return the stored license, or Free if none/invalid.

    Never raises. If the file is missing, empty, or contains garbage,
    we simply fall back to Free.
    """
    if not LICENSE_PATH.exists():
        return License(tier="free")
    try:
        raw = LICENSE_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return License(tier="free")
    return validate_key(raw) or License(tier="free")


def save_license_key(raw_key: str) -> License | None:
    """Validate and persist a key. Returns the License, or None if invalid."""
    license_obj = validate_key(raw_key)
    if license_obj is None:
        return None
    LICENSE_PATH.write_text(license_obj.raw_key + "\n", encoding="utf-8")
    return license_obj


def clear_license() -> None:
    """Delete the stored key. Used by tests and a future 'Remove license' button."""
    if LICENSE_PATH.exists():
        LICENSE_PATH.unlink()


# ---------------------------------------------------------------------
# Enforcement (what the GUI calls)
# ---------------------------------------------------------------------

def can_add_device(current_count: int) -> tuple[bool, str]:
    """Check whether the user is allowed to add one more device.

    Returns (allowed, reason_if_not). The GUI calls this before saving
    a new device; if allowed is False, it shows `reason` in a message box.
    """
    license_obj = load_license()
    if current_count < license_obj.max_devices:
        return True, ""
    if license_obj.tier == "free":
        return False, (
            f"The free version is limited to {license_obj.max_devices} devices.\n\n"
            "Upgrade to Personal (250 devices) or Pro (5,000 devices) "
            "to add more."
        )
    return False, (
        f"Your {license_obj.tier} license allows up to "
        f"{license_obj.max_devices} devices.\n\n"
        "Contact the developer to upgrade."
    )