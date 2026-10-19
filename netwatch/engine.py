"""Background monitoring engine for Netwatch."""

import threading
import time
from datetime import datetime, timezone

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
                print(f"[engine] Error during tick: {e}")

            # Sleep for 2 seconds before checking again.
            self._stop_event.wait(2.0)

    def _tick(self) -> None:
        """Check every enabled device, updating its status in storage."""
        devices = [d for d in storage.list_devices() if d.enabled]
        statuses = storage.list_status()
        any_changed = False

        for device in devices:
            last_status = statuses.get(device.id, {})
            last_check = last_status.get("last_check", "")

            if last_check:
                try:
                    last_dt = datetime.fromisoformat(last_check)
                    elapsed = (datetime.now(timezone.utc) - last_dt).total_seconds()
                    if elapsed < device.check_interval:
                        continue
                except ValueError:
                    pass

            # Run the network check.
            result = full_check(ip=device.ip, port=device.port)

            # Save the new status.
            storage.save_status(device.id, {
                "state": result.state.value,
                "latency_ms": result.latency_ms,
                "last_check": datetime.now(timezone.utc).isoformat(),
                "error": result.error,
            })
            any_changed = True

        if any_changed and self._on_update:
            self._on_update()