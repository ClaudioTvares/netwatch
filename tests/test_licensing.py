"""Tests for netwatch.licensing.

Run with:
    pytest

Or from the project root, with verbose output:
    pytest tests/test_licensing.py -v
"""

import pytest

from netwatch.licensing import (
    License,
    clear_license,
    can_add_device,
    load_license,
    make_key,
    validate_key,
)


# ---------------------------------------------------------------------
# Fixtures: prepare clean state before each test that touches the
# license file on disk.
# ---------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_license_file():
    """Ensure no license.key is left over between tests.

    `autouse=True` means this runs automatically for every test in the
    file, before and after. No manual setup needed in each test.
    """
    clear_license()
    yield
    clear_license()


# ---------------------------------------------------------------------
# Key generation and validation
# ---------------------------------------------------------------------

def test_valid_personal_key():
    key = make_key("PERS", 42)
    license_obj = validate_key(key)

    assert license_obj is not None
    assert license_obj.tier == "personal"
    assert license_obj.serial == "000042"
    assert license_obj.max_devices == 250
    assert license_obj.is_paid is True


def test_valid_pro_key():
    key = make_key("PRO", 100)
    license_obj = validate_key(key)

    assert license_obj is not None
    assert license_obj.tier == "pro"
    assert license_obj.max_devices == 5000


def test_tampered_signature_rejected():
    key = make_key("PERS", 1)
    tampered = key[:-1] + ("0" if key[-1] != "0" else "1")
    assert validate_key(tampered) is None


def test_wrong_prefix_rejected():
    key = make_key("PERS", 1)
    wrong_prefix = "XXXX" + key[4:]
    assert validate_key(wrong_prefix) is None


def test_bad_format_rejected():
    assert validate_key("") is None
    assert validate_key("not-a-key") is None
    assert validate_key("NWTC-WRONG-000001-ABCD1234") is None
    assert validate_key("NWTC-PERS-1-ABCD1234") is None       # serial too short
    assert validate_key("NWTC-PERS-000001-ABCD") is None      # signature too short


def test_case_insensitive_and_whitespace_tolerant():
    key = make_key("PERS", 42)
    padded_lowercase = "  " + key.lower() + "\n"
    license_obj = validate_key(padded_lowercase)
    assert license_obj is not None
    assert license_obj.serial == "000042"


# ---------------------------------------------------------------------
# Persistence and enforcement
# ---------------------------------------------------------------------

def test_free_license_when_no_key_stored():
    license_obj = load_license()
    assert license_obj.tier == "free"
    assert license_obj.max_devices == 10
    assert license_obj.is_paid is False


def test_can_add_device_at_free_tier_limit():
    # Under the limit: allowed
    allowed, reason = can_add_device(5)
    assert allowed is True
    assert reason == ""

    # At the limit: blocked with a helpful message
    allowed, reason = can_add_device(10)
    assert allowed is False
    assert "10 devices" in reason


def test_can_add_device_with_personal_license():
    # Simulate the user entering a valid Personal key, which bumps
    # the limit to 250 devices.
    from netwatch.licensing import save_license_key
    save_license_key(make_key("PERS", 1))

    allowed, _ = can_add_device(10)
    assert allowed is True

    allowed, _ = can_add_device(249)
    assert allowed is True

    allowed, reason = can_add_device(250)
    assert allowed is False
    assert "250" in reason


# ---------------------------------------------------------------------
# Input validation on the generator side
# ---------------------------------------------------------------------

def test_serial_out_of_range_raises():
    with pytest.raises(ValueError):
        make_key("PERS", 0)

    with pytest.raises(ValueError):
        make_key("PERS", 1_000_000)


def test_unknown_tier_code_raises():
    with pytest.raises(ValueError):
        make_key("WIZARD", 1)