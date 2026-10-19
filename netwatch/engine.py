"""Background monitoring engine for Netwatch."""

import threading
from datetime import datetime, timezone

from . import notifier
from . import settings as settings_module
from . import storage
from .monitor import full_check


class MonitorEngine:
    """Background thread that periodically checks all devices."""

    def __init__(self, on_update=None):
        self._on_update = on_update
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        """Start the background thread."""
        self._thread.start()

    def stop(self) -> None:
        """Signal the thread to stop and wait for it to finish."""
        self._stop_event.set()
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        """The main loop of the thread."""
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                # Never let the engine crash the app. Log and continue.
                print(f"[engine] Error during tick: {e}")

            # Sleep for 2 seconds before checking again. The "real"
            # per-device interval is enforced inside `_tick`.
            self._stop_event.wait(2.0)

    def _tick(self) -> None:
        """Check every enabled device, updating its status in storage."""
        devices = [d for d in storage.list_devices() if d.enabled]
        statuses = storage.list_status()
        any_changed = False

        # Load settings once per tick, not per device.
        current_settings = settings_module.load_settings()

        for device in devices:
            last_status = statuses.get(device.id, {})
            last_check = last_status.get("last_check", "")
            prev_state = last_status.get("state")

            if last_check:
                try:
                    last_dt = datetime.fromisoformat(last_check)
                    elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
                    if elapsed < device.check_interval:
                        continue
                except ValueError:
                    pass  # malformed date, check anyway

            # Run the actual network check.
            result = full_check(ip=device.ip, port=device.port)
            new_state = result.state.value

            # Save the new status.
            storage.save_status(device.id, {
                "state": new_state,
                "latency_ms": result.latency_ms,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": result.error,
            })
            any_changed = True

            # ---- Edge-triggered notification ----
            # Only notify if the state actually CHANGED.
            # (prev_state is None on the very first check — don't notify.)
            if prev_state and prev_state != new_state:
                if new_state == "online":
                    event = "RECOVERED"
                    msg = (
                        f"{device.name} ({device.ip}:{device.port or '—'}) "
                        f"is back ONLINE."
                    )
                elif new_state == "host_down":
                    event = "OFFLINE"
                    msg = (
                        f"{device.name} ({device.ip}:{device.port or '—'}) "
                        f"is NOT RESPONDING."
                    )
                elif new_state == "port_blocked":
                    event = "PORT BLOCKED"
                    msg = (
                        f"{device.name} ({device.ip}) is up, but port "
                        f"{device.port} is closed/filtered."
                    )
                elif new_state == "timeout":
                    event = "TIMEOUT"
                    msg = (
                        f"{device.name} ({device.ip}:{device.port}) "
                        f"timed out."
                    )
                else:
                    continue

                notifier.notify(current_settings, device, event, msg)

        if any_changed and self._on_update:
            self._on_update()