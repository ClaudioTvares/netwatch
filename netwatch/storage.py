"""Storage layer for Netwatch."""

import atexit
import sys
from pathlib import Path

from tinydb import TinyDB, Query
from tinydb.storages import JSONStorage

from .constants import DATA_DIRNAME, DB_FILENAME
from .models import Device


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

# We use JSONStorage directly instead of CachingMiddleware to prevent
# file corruption if the app is killed or crashes abruptly.
_db = TinyDB(DB_PATH, storage=JSONStorage)
atexit.register(_db.close)

_devices = _db.table("devices")
_status = _db.table("status")
_meta = _db.table("meta")


def close() -> None:
    _db.close()


def reload_database() -> None:
    """Force TinyDB to close and reopen the database file from disk.
    
    This is critical after restoring a backup, because the app has the
    old data cached in memory. Closing the handle and reopening it
    forces TinyDB to read the new file.
    """
    global _db, _devices, _status, _meta
    
    _db.close()
    
    _db = TinyDB(DB_PATH, storage=JSONStorage)
    
    _devices = _db.table("devices")
    _status = _db.table("status")
    _meta = _db.table("meta")


def list_devices() -> list[Device]:
    return [Device.from_dict(row) for row in _devices.all()]


def get_device(device_id: str) -> Device | None:
    q = Query()
    row = _devices.get(q.id == device_id)
    return Device.from_dict(row) if row else None


def count_devices() -> int:
    return len(_devices)


def add_device(device: Device) -> Device:
    _devices.insert(device.to_dict())
    return device


def update_device(device: Device) -> None:
    q = Query()
    _devices.upsert(device.to_dict(), q.id == device.id)


def delete_device(device_id: str) -> None:
    q = Query()
    _devices.remove(q.id == device_id)
    _status.remove(q.device_id == device_id)


def get_status(device_id: str) -> dict | None:
    q = Query()
    return _status.get(q.device_id == device_id)


def list_status() -> dict[str, dict]:
    return {row["device_id"]: row for row in _status.all()}


def save_status(device_id: str, payload: dict) -> None:
    q = Query()
    record = {"device_id": device_id, **payload}
    _status.upsert(record, q.device_id == device_id)


def get_meta(key: str, default=None):
    q = Query()
    row = _meta.get(q.key == key)
    return row["value"] if row else default


def set_meta(key: str, value) -> None:
    q = Query()
    _meta.upsert({"key": key, "value": value}, q.key == key)