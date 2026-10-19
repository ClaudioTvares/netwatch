# Netwatch

*A local, offline-first desktop monitor for network equipment — checks
devices and service ports, and alerts you by email when something goes down.*

![Netwatch main window](Interface.png)

## Status

🚧 Work in progress — v0.1.0 (foundation)

## Planned Features

- Monitor up to 5,000 devices (free tier: 10 devices)
- TCP port checks + ICMP fallback for accurate port-block detection
- Edge-triggered email notifications with per-device routing (no alert spam)
- Live latency monitoring and automatic updates
- Local, privacy-friendly storage (no cloud, no phone-home)
- One-time purchase, lifetime license

## Tech Stack

- Python 3.11+
- Tkinter (GUI)
- TinyDB (document store, JSON-backed)
- icmplib (ICMP checks without raw sockets)
- PyInstaller (packaging to a single .exe)

## Development

    git clone https://github.com/ClaudioTvares/netwatch.git
    cd netwatch
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python main.py

## Roadmap

- [x] Project scaffolding and Git setup
- [x] Device data model
- [x] Local document-database storage (TinyDB)
- [x] Offline license system (free / personal / pro tiers)
- [x] Test suite for licensing (11 tests, pytest)
- [x] Desktop GUI (Tkinter) — device list, add/edit/delete dialogs
- [x] TCP + ICMP monitoring engine (live background updates)
- [x] Email notification pipeline (Company & Personal SMTP)
- [x] WinRAR-style nag dialog for free tier
- [ ] Packaging to a single `.exe` (PyInstaller)

## License

Proprietary. See LICENSE.