"""Storage layer for Netwatch.

Wraps TinyDB — a pure-Python document database — behind a clean API.
Every function here is the *only* way the rest of the app touches
persistent data. If we ever swap TinyDB for MongoDB, SQLite, or a
cloud API, only this file changes.

TinyDB vocabulary refresher:
    * "table"    = a named collection of documents (like a SQL table)
    * "document" = a Python dict with arbitrary keys (like a SQL row)
    * "Query()"  = a filter object (like a SQL WHERE clause)
    * "upsert"   = insert if missing, update if present
"""

import atexit
import sys
from pathlib import Path

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

from .constants import DATA_DIRNAME, DB_FILENAME
from .models import Device


# ---------------------------------------------------------------------
# Where do we put the database file?
# ---------------------------------------------------------------------
#
# Two scenarios:
#   1. Running from source (this file lives in .../netwatch/storage.py):
#      put data next to the project root.
#   2. Running as a frozen .exe (PyInstaller):
#      put data next to the .exe, NOT inside the temporary unpack folder.
#
# `sys.frozen` is True only when running under PyInstaller.

def _data_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent
    path = base / DATA_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR: Path = _data_dir()
DB_PATH: Path = DATA_DIR / DB_FILENAME


# ---------------------------------------------------------------------
# Database handle
# ---------------------------------------------------------------------
#
# CachingMiddleware buffers writes in memory and flushes to disk
# periodically. Without it, every insert = one full rewrite of the JSON
# file. With it, writes are batched — much friendlier for a desktop app.
#
# Trade-off: if the process is killed with `kill -9` before the buffer
# flushes, you lose the last few writes. For our use case (device list
# changes maybe once a week), that's completely fine. We still call
# close() on app shutdown to force a flush.

_db = TinyDB(DB_PATH, storage=CachingMiddleware(JSONStorage))
atexit.register(_db.close)

_devices = _db.table("devices")
_status = _db.table("status")
_meta = _db.table("meta")


def close() -> None:
    """Flush pending writes and close the DB. Call this on app shutdown."""
    _db.close()


# ---------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------

def list_devices() -> list[Device]:
    """Return every device in the DB, as Device objects."""
    return [Device.from_dict(row) for row in _devices.all()]


def get_device(device_id: str) -> Device | None:
    """Return one device by id, or None if not found."""
    q = Query()
    row = _devices.get(q.id == device_id)
    return Device.from_dict(row) if row else None


def count_devices() -> int:
    """How many devices are currently stored."""
    return len(_devices)


def add_device(device: Device) -> Device:
    """Insert a new device. Returns the same object for chaining."""
    _devices.insert(device.to_dict())
    return device


def update_device(device: Device) -> None:
    """Replace an existing device (matched by id). Inserts if missing."""
    q = Query()
    _devices.upsert(device.to_dict(), q.id == device.id)


def delete_device(device_id: str) -> None:
    """Remove a device and its associated status row."""
    q = Query()
    _devices.remove(q.id == device_id)
    _status.remove(q.device_id == device_id)


# ---------------------------------------------------------------------
# Status (last known state per device)
# ---------------------------------------------------------------------
#
# We keep status separate from the device itself so that:
#   * The device inventory file stays small and human-editable.
#   * A status update doesn't rewrite the whole inventory.
#   * Deleting a device cleanly removes its status row too.

def get_status(device_id: str) -> dict | None:
    """Return the last-known status for one device, or None."""
    q = Query()
    return _status.get(q.device_id == device_id)


def list_status() -> dict[str, dict]:
    """Return all statuses, keyed by device_id, for fast lookup."""
    return {row["device_id"]: row for row in _status.all()}


def save_status(device_id: str, payload: dict) -> None:
    """Insert or update the status row for one device."""
    q = Query()
    record = {"device_id": device_id, **payload}
    _status.upsert(record, q.device_id == device_id)


# ---------------------------------------------------------------------
# Meta (small key/value store for app-level state)
# ---------------------------------------------------------------------
#
# Examples of things that might live here later: schema version,
# install date, "last nag shown" timestamp, analytics counters.

def get_meta(key: str, default=None):
    q = Query()
    row = _meta.get(q.key == key)
    return row["value"] if row else default


def set_meta(key: str, value) -> None:
    q = Query()
    _meta.upsert({"key": key, "value": value}, q.key == key)