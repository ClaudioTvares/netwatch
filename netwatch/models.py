"""Data models for Netwatch.

A `Device` is the fundamental unit this app works with: one piece of
network equipment that the operator wants to monitor. The dataclass
form gives us free type hints, a clean `__init__`, and pleasant
repr output in the debugger — for free.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import uuid


def _utc_now_iso() -> str:
    """Timestamp in ISO 8601, in UTC, e.g. '2026-10-09T14:32:11.123456+00:00'.

    Always UTC, always timezone-aware. Local time is a display concern,
    never a storage concern — a lesson every data analyst learns the hard way.
    """
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    """Short unique identifier for a device."""
    return str(uuid.uuid4())


@dataclass
class Device:
    """A single monitored piece of network equipment.

    Attributes:
        name: Human-readable label ('Core Switch', 'Reception Printer').
        ip: IPv4 address as a string. We store it as a string, not a
            Python ipaddress object, so JSON serialization stays trivial.
        port: Optional TCP port. If None, we fall back to ICMP-only checks.
        check_interval: Seconds between checks for this device.
        notify_email: Whether this device should trigger email alerts.
        notify_whatsapp: Whether this device should trigger WhatsApp alerts.
        enabled: If False, the monitor skips this device entirely.
        id: Stable unique identifier, generated on creation.
        created_at: UTC timestamp of when this device was added.
    """

    name: str
    ip: str
    port: int | None = None
    check_interval: int = 30
    notify_email: bool = True
    notify_whatsapp: bool = True
    enabled: bool = True
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_utc_now_iso)

    # ---- conversion helpers ------------------------------------------

    def to_dict(self) -> dict:
        """Turn this Device into a plain dict — what TinyDB stores."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Device":
        """Rebuild a Device from a dict, ignoring unknown keys.

        Forward compatibility: if a future version of Netwatch adds a
        new field and a user downgrades, the old code still loads the
        record instead of crashing.
        """
        known = {k: data[k] for k in cls.__dataclass_fields__ if k in data}
        return cls(**known)