# Netwatch

A lightweight, offline-first desktop application for monitoring network
equipment availability. Detects when devices go offline, when specific
service ports become unavailable, and alerts the operator via email
and/or WhatsApp.

## Status

🚧 Work in progress — v0.1.0 (foundation)

## Planned Features

- Monitor up to 5,000 devices (free tier: 10 devices)
- TCP port checks + ICMP fallback for accurate port-block detection
- Edge-triggered email and WhatsApp notifications (no alert spam)
- Local, privacy-friendly storage (no cloud, no phone-home)
- One-time purchase, lifetime license

## Tech Stack

- Python 3.11+
- Tkinter (GUI)
- TinyDB (document store, JSON-backed)
- icmplib (ICMP checks without raw sockets)
- PyInstaller (packaging to a single .exe)

## Development

    git clone <your-repo-url>
    cd netwatch
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

## License

Proprietary. See LICENSE.