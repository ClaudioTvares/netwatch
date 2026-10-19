"""Email and WhatsApp notification senders.

Two transports are supported:

    * Email via SMTP (any provider: Gmail, Outlook, custom server).
    * WhatsApp via CallMeBot (free, no business account needed).

Both functions read their credentials from `settings.json` — call
`settings.load_settings()` once, modify the returned dict, and pass it
in. `notifier` never touches the disk itself.
"""

import smtplib
from email.message import EmailMessage

import requests


def send_email(settings: dict, subject: str, body: str) -> bool:
    """Send an email alert. Returns True on success, False on any failure."""
    cfg = settings["smtp"]
    if not (cfg["user"] and cfg["password"] and cfg["to"]):
        return False

    msg = EmailMessage()
    msg["From"] = cfg["user"]
    msg["To"] = cfg["to"]
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
            server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[notifier] Email failed: {e}")
        return False


def send_whatsapp(settings: dict, message: str) -> bool:
    """Send a WhatsApp message via CallMeBot. Returns True on success."""
    cfg = settings["whatsapp"]
    if not (cfg["enabled"] and cfg["phone"] and cfg["apikey"]):
        return False

    try:
        r = requests.get(
            "https://api.callmebot.com/whatsapp.php",
            params={
                "phone": cfg["phone"],
                "text": message,
                "apikey": cfg["apikey"],
            },
            timeout=10,
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[notifier] WhatsApp failed: {e}")
        return False


def notify(settings: dict, device, event: str, message: str) -> None:
    """Fire off whatever notification channels are enabled for this device."""
    subject = f"[Netwatch] {device.name} — {event}"
    full_message = f"{subject}\n\n{message}"

    if device.notify_email:
        send_email(settings, subject, message)
    if device.notify_whatsapp:
        send_whatsapp(settings, full_message)