"""Private license-key generator for Netwatch.

Usage:
    python tools/keygen.py personal 42
    python tools/keygen.py pro 100

Run this every time a customer buys a license. Give them the key it
prints. Keep a record of which serial number belongs to which customer
(a spreadsheet is fine) — you'll need it for support.

DO NOT SHIP THIS FILE with the customer-facing app. It contains the
same secret as licensing.py, but this is the tool that *creates* valid
keys. A customer who has it could mint their own licenses.
"""

import sys
from pathlib import Path

# Make `from netwatch import ...` work when this file is run directly.
# Without this, Python would look for `netwatch` starting from tools/
# (which doesn't have it) instead of from the project root (which does).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from netwatch.constants import TIER_CODES
from netwatch.licensing import make_key


USAGE = """\
Generate a Netwatch license key.

Usage:
    python tools/keygen.py <tier> <serial>

Arguments:
    tier     one of: personal, pro
    serial   6-digit-ish customer number (1 to 999999)

Examples:
    python tools/keygen.py personal 42
    python tools/keygen.py pro 100
"""

# Maps friendly names to the short codes used inside license keys.
# We derive it from constants.TIER_CODES so there's a single source
# of truth — add a tier there, and this tool learns it automatically.
TIER_NAME_TO_CODE = {name: code for code, name in TIER_CODES.items()}


def main() -> int:
    args = sys.argv[1:]

    if len(args) != 2 or args[0] in ("-h", "--help"):
        print(USAGE)
        return 0 if args and args[0] in ("-h", "--help") else 1

    tier_name, serial_arg = args
    tier_name = tier_name.lower()

    if tier_name not in TIER_NAME_TO_CODE:
        print(f"Error: unknown tier {tier_name!r}.")
        print(f"Valid tiers: {', '.join(sorted(TIER_NAME_TO_CODE))}")
        return 1

    try:
        serial = int(serial_arg)
    except ValueError:
        print(f"Error: serial must be an integer, got {serial_arg!r}.")
        return 1

    if not (1 <= serial <= 999_999):
        print("Error: serial must be between 1 and 999999.")
        return 1

    tier_code = TIER_NAME_TO_CODE[tier_name]
    key = make_key(tier_code, serial)

    print(f"Tier:   {tier_name}")
    print(f"Serial: {serial:06d}")
    print(f"Key:    {key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())