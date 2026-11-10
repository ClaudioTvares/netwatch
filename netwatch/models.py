"""Data models for Netwatch."""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import uuid


def _utc_now_iso() -> str:
    """Timestamp in ISO 8601, in UTC."""
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    """Short unique identifier for a device."""
    return str(uuid.uuid4())


@dataclass
class Device:
    """A single monitored piece of network equipment."""

    name: str
    group: str | None = None
    ip: str = ""
    port: int | None = None
    check_interval: int = 30
    notify_email: bool = True
    notify_email_to: str | None = None
    enabled: bool = True
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_utc_now_iso)

    def to_dict(self) -> dict:
        """Turn this Device into a plain dict — what TinyDB stores."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        """Rebuild a Device from a dict, ignoring unknown keys."""
        known = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        return cls(**known)