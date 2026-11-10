"""Background monitoring engine for Netwatch."""

import threading
from datetime import datetime, timezone, timedelta

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
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        self._thread.join(timeout=2.0)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._tick()
            except Exception as e:
                print(f"[engine] Error during tick: {e}")
            self._stop_event.wait(2.0)

    def _tick(self) -> None:
        devices = [d for d in storage.list_devices() if d.enabled]
        statuses = storage.list_status()
        any_changed = False
        now = datetime.now(timezone.utc)

        current_settings = settings_module.load_settings()
        
        # Read the user's desired reminder interval (default to 12h if missing)
        try:
            interval_hours = int(current_settings.get("general", {}).get("alert_interval_hours", 12))
        except (ValueError, TypeError):
            interval_hours = 12
            
        reminder_delta = timedelta(hours=interval_hours)

        for device in devices:
            last_status = statuses.get(device.id, {})
            last_check = last_status.get("last_check", "")
            prev_state = last_status.get("state")

            if last_check:
                try:
                    last_dt = datetime.fromisoformat(last_check)
                    elapsed = (now - last_dt).total_seconds()
                    if elapsed < device.check_interval:
                        continue
                except ValueError:
                    pass

            result = full_check(ip=device.ip, port=device.port)
            new_state = result.state.value

            # --- Notification Logic ---
            should_notify = False
            event = ""
            msg = ""

            # 1. Edge-triggered (state changed, or first check and it's down)
            if prev_state and prev_state != new_state:
                should_notify = True
            elif prev_state is None and new_state in ("host_down", "port_blocked", "timeout"):
                should_notify = True

            # 2. Heartbeat (Reminder every X hours if still down)
            elif new_state in ("host_down", "port_blocked", "timeout"):
                last_notified_str = last_status.get("last_notified")
                if last_notified_str:
                    try:
                        last_notified = datetime.fromisoformat(last_notified_str)
                        # Ensure both are timezone-aware
                        if last_notified.tzinfo is None:
                            last_notified = last_notified.replace(tzinfo=timezone.utc)
                        
                        if (now - last_notified) > reminder_delta:
                            should_notify = True
                    except ValueError:
                        pass 
                else:
                    should_notify = True

            # Determine the message if we need to notify
            if should_notify:
                if new_state == "online":
                    event = "RECOVERED"
                    msg = f"{device.name} ({device.ip}:{device.port or '—'}) is back ONLINE."
                elif new_state == "host_down":
                    event = "OFFLINE"
                    msg = f"{device.name} ({device.ip}:{device.port or '—'}) is NOT RESPONDING."
                elif new_state == "port_blocked":
                    event = "PORT BLOCKED"
                    msg = f"{device.name} ({device.ip}) is up, but port {device.port} is closed/filtered."
                elif new_state == "timeout":
                    event = "TIMEOUT"
                    msg = f"{device.name} ({device.ip}:{device.port}) timed out."
                
                notifier.notify(current_settings, device, event, msg)

            # Save the new status.
            status_payload = {
                "state": new_state,
                "latency_ms": result.latency_ms,
                "last_check": now.isoformat(),
                "error": result.error,
            }
            
            if should_notify:
                status_payload["last_notified"] = now.isoformat()
            elif last_status.get("last_notified"):
                status_payload["last_notified"] = last_status["last_notified"]

            storage.save_status(device.id, status_payload)
            any_changed = True

        if any_changed and self._on_update:
            self._on_update()