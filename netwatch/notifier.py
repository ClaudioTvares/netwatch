"""Email notification sender."""

import smtplib
from email.message import EmailMessage


def send_email(cfg: dict, subject: str, body: str, to_addr: str | None = None) -> bool:
    """Send an email alert. Returns True on success, False on any failure."""
    recipient = to_addr or cfg.get("to")

    if not (cfg["user"] and cfg["password"] and recipient):
        print("[notifier] Missing credentials or recipient.")
        return False

    msg = EmailMessage()
    msg["From"] = cfg["user"]
    msg["To"] = recipient
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


def notify(settings: dict, device, event: str, message: str) -> None:
    """Fire off whatever notification channels are enabled for this device."""
    if not device.notify_email:
        return

    subject = f"Netwatch Status — {device.name}"
    
    email_body = (
        f"Netwatch Notification\n"
        f"{'-' * 40}\n"
        f"Device: {device.name}\n"
        f"IP Address: {device.ip}\n"
        f"Port: {device.port or 'N/A'}\n"
        f"Event: {event}\n\n"
        f"{message}\n"
    )
    
    # Use per-device email if set, otherwise fall back to company, then personal
    recipient = getattr(device, "notify_email_to", None)
    
    if recipient:
        # If the device has a specific email, use company config to send it
        cfg = settings.get("company_email", {})
        if not cfg.get("user"):
            cfg = settings.get("personal_email", {})
        send_email(cfg, subject, email_body, to_addr=recipient)
    else:
        # Fall back to the default company email if no specific email is set
        cfg = settings.get("company_email", {})
        if cfg.get("user") and cfg.get("to"):
            send_email(cfg, subject, email_body)
        else:
            # Fallback to personal if company is not configured
            cfg = settings.get("personal_email", {})
            if cfg.get("user") and cfg.get("to"):
                send_email(cfg, subject, email_body)