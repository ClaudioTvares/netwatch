# Netwatch Documentation

Welcome to the complete guide for Netwatch. This document explains every feature, button, color, and setting in plain English.

If you just want to install and start using the app, jump to the [Installation](#installation) section.

---

## Table of Contents

- [Installation](#installation)
- [Getting Started](#getting-started)
- [Main Window](#main-window)
- [Status Colors](#status-colors)
- [Adding a Device](#adding-a-device)
- [Email Settings](#email-settings)
- [Email Alerts](#email-alerts)
- [System Tray](#system-tray)
- [Backup and Restore](#backup-and-restore)
- [Keyboard Shortcuts and Tips](#keyboard-shortcuts-and-tips)
- [FAQ](#faq)
- [Support](#support)

---

## Installation

Netwatch is a single, standalone Windows program. There is **no installer, no Python required, and no admin rights needed**.

### Steps

1. **Download** `Netwatch.exe` from the [latest release](https://github.com/ClaudioTvares/netwatch/releases/latest).
2. **Create a folder** where you want Netwatch to live. For example:
   - `C:\Netwatch\`
   - `C:\Users\YourName\Documents\Netwatch\`
   - Anywhere else that isn't a temporary folder.
3. **Move** the downloaded `Netwatch.exe` into that folder.
4. **Double-click** `Netwatch.exe` to run it.

That's it. On the first launch, Netwatch will create a `data\` subfolder next to the `.exe`. That folder contains your devices and settings. **Do not delete it**, or you will lose your configuration.

### First-launch warning

Windows may show a blue box saying **"Windows protected your PC"** because the `.exe` is not digitally signed. This is normal for small open-source tools. Click **"More info"** → **"Run anyway"** to proceed.

### Uninstalling

To remove Netwatch, simply delete the folder containing `Netwatch.exe`. There are no registry entries, no background services, and no leftover files elsewhere on your system.

---

## Getting Started

When you open Netwatch for the first time:

1. You'll see a **Welcome** popup asking for a voluntary donation. Click **"Continue"** to skip it.
2. The main window opens with an empty device list.
3. Click **"Add Device"** to add your first piece of network equipment.
4. Go to **File → Email Settings** to configure email alerts.
5. Wait 30 seconds. Netwatch will start checking the device automatically.

---

## Main Window

The main window has four parts:

### Top menu bar
- **File** — Email Settings, Backup, Restore, Minimize to background, Exit.
- **Help** — Support the project (opens Ko-fi), About.

### Toolbar (top row of buttons)
- **Add Device** — Opens a form to add a new device.
- **Edit** — Edit the selected device.
- **Delete** — Delete the selected device.
- **Test Now** — Immediately ping the selected device instead of waiting for the next automatic check.
- **Device Search** — Type here to filter the device list by name.
- **Group** — Dropdown to filter by device group.
- **Status text** — Shows how many devices are currently visible.

### Device table (middle)
A row for each device with these columns:

| Column | What it shows |
|---|---|
| **Status** | The current state (see [Status Colors](#status-colors)) |
| **Name** | The custom name you gave the device |
| **Group** | The optional group (e.g., "Servers", "Printers") |
| **IP** | The IP address being monitored |
| **Port** | The TCP port being checked (or `—` if ICMP-only) |
| **Latency** | How long the last check took (in milliseconds) |
| **Last Check** | When the device was last checked |

### Footer
- **"Developed by Claudio Tavares"** — the author credit.

---

## Status Colors

Netwatch uses **four possible states** for each device. The colors are designed to be distinguishable at a glance:

| Color | State | What it means | What to do |
|---|---|---|---|
| 🟢 **Green** | **Online** | The device responded successfully. Everything is fine. | Nothing. |
| 🔴 **Red** | **Host Down** | The device is not responding at all. It might be powered off, disconnected, or unreachable. | Check the physical connection, the power, and the IP address. |
| 🟠 **Amber** | **Port Blocked** | The device is online, but the specific port you're monitoring is closed or filtered. This usually means the *service* is down (e.g., SSH on port 22). | Check the specific service on the device. The server is on, but the service isn't. |
| 🟡 **Yellow** | **Timeout** | The device didn't respond within the timeout window. This can happen on slow networks. | Wait a few minutes. If it persists, treat it as "Host Down". |
| ⚪ **Grey** | **Unknown** | The device has been added but not checked yet. | Wait 30 seconds, or click "Test Now". |

### The difference between "Host Down" and "Port Blocked"

This is Netwatch's most useful feature. Most tools just say "down" when anything fails. Netwatch tells you *what* is down:

- **Host Down** = the computer is unreachable (off, disconnected, wrong IP).
- **Port Blocked** = the computer is on, but the *service* on that port isn't responding.

This saves you hours of debugging.

---

## Adding a Device

Click **"Add Device"** to open the device form. Fields:

| Field | Required | What it does |
|---|---|---|
| **Name** | Yes | A human-friendly label. E.g., "Core Switch", "Reception Printer". |
| **Group** | No | An optional category. E.g., "Servers", "Printers", "Cameras". Used for filtering. |
| **IP address** | Yes | The device's IPv4 address. E.g., `192.168.1.1`. |
| **Port** | No | The TCP port to check. Leave blank to use ICMP (ping) only. Common ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 445 (SMB), 9100 (printer). |
| **Check interval (sec)** | Yes | How often to check (minimum 5 seconds, default 30). |
| **Enable Email alerts** | — | Master switch. If unchecked, this device never sends emails. |
| **Send to (email)** | No | Override the default alert recipient. Leave blank to use the one from Settings. |

---

## Email Settings

Go to **File → Email Settings**. The settings window has three tabs.

### General tab
- **Reminder Interval (hours)** — If a device stays offline for this many hours, send another reminder email. Default: 12. Set to `0` to send a reminder on every check (not recommended — you'll get flooded).

### Company Email tab
Use this if you have a corporate email account (Office 365, Exchange, etc.).

| Field | Example |
|---|---|
| **Login (email)** | `you@yourcompany.com` |
| **Password / App Key** | Your email password, or an app-specific password |
| **Global Fallback Email** | Where to send alerts by default |
| **SMTP Host** | `smtp.office365.com` (ask your IT department) |
| **SMTP Port** | `587` (most common) |

### Personal Email tab
Use this for Gmail, Outlook.com, Yahoo, or any personal email.

| Field | Example |
|---|---|
| **Login (email)** | `yourname@gmail.com` |
| **Password / App Key** | A **Google App Password** (16 characters) — see below |
| **Global Fallback Email** | Where to send alerts by default |
| **SMTP Host** | Leave blank to auto-detect based on the login email |

### How to get a Gmail App Password

Google blocks "normal" passwords for apps like Netwatch. You need a special **App Password**:

1. Go to https://myaccount.google.com/security
2. Ensure **2-Step Verification** is ON.
3. Search for **"App passwords"** in the search bar.
4. Create one named "Netwatch" and copy the 16-character code.
5. Paste it into the **Password / App Key** field.

### Which one does Netwatch use?

**Priority order:**
1. If the **Company Email** has credentials, that's the primary sender.
2. If the **Company Email** is empty, the **Personal Email** is used.
3. If both are empty, no emails are sent.

If a device has its own **"Send to (email)"** set, that address always receives the alert — but the *sender* is still whichever account is configured in Settings.

---

## Email Alerts

Netwatch only sends emails when something **changes**, not on every check. This is called **"edge-triggered"** notifications, and it's what makes the tool usable.

### When Netwatch sends an email

| Trigger | When | Subject |
|---|---|---|
| **First check** | If a device is added and it's offline on the very first check | `[Netwatch] Name — OFFLINE` |
| **State change to offline** | If a device was online and goes down | `[Netwatch] Name — OFFLINE` |
| **State change to port blocked** | If the service on a port stops responding | `[Netwatch] Name — PORT BLOCKED` |
| **State change back to online** | If a device recovers | `[Netwatch] Name — RECOVERED` |
| **Reminder** | Every N hours while a device remains down | Same as the state change |

### When Netwatch does NOT send an email

- If a device is already down and it stays down (unless the reminder interval passes).
- If a device is online and stays online.
- If you haven't configured email credentials in Settings.

---

## System Tray

When you close the Netwatch window by clicking the **X**, the app **minimizes to the system tray** (the area near the clock in the Windows taskbar). It keeps running and keeps monitoring in the background.

### To bring it back
- **Double-click** the blue globe icon in the system tray, OR
- **Right-click** → **"Open Netwatch"**.

### To completely exit
- **Right-click** the tray icon → **"Exit"**.

⚠️ **Emails are only sent while the app is running.** If you fully exit Netwatch, monitoring stops and no alerts are sent.

---

## Backup and Restore

### Backup
**File → Backup Data...** — Saves a `.zip` file containing both your device list and your email settings. Good for:
- Moving to a new PC.
- Keeping a periodic backup.
- Sharing your config with a colleague.

### Restore
**File → Restore Backup...** — Loads a `.zip` file from a previous backup. **This overwrites your current devices and settings**, so only do it when you mean it.

---

## Keyboard Shortcuts and Tips

- **Double-click a row** — opens the Edit Device dialog.
- **Ctrl+F** — focuses the device search box (works when the window is focused).
- **Right-click the tray icon** — access "Open" and "Exit".
- **Type in "Device Search"** — the list filters as you type.

---

## FAQ

### Do I need to keep Netwatch open for it to work?
**Yes.** Netwatch runs on your computer, so it can only check devices while it's running. If you need 24/7 monitoring, leave it minimized to the system tray (or keep the PC on).

### Can I monitor my home network from outside?
**Not directly.** Netwatch checks devices from the computer it's running on. If that computer is outside your home network, it won't be able to reach internal IPs like `192.168.x.x`.

### How many devices can Netwatch handle?
Technically, up to **5,000**. In practice, you're limited by how often you check them and how fast your computer is. For normal use (a few dozen devices), Netwatch will run smoothly even on a decade-old PC.

### Will Netwatch send my data anywhere?
**No.** Everything stays on your computer, in the `data\` folder next to the `.exe`. There is no cloud, no telemetry, no analytics. The only network traffic Netwatch generates is:
1. The TCP/ICMP checks to your devices.
2. The SMTP connections to send email alerts.

### What if a device goes offline overnight?
If Netwatch was running, you'll get the email as soon as the state change is detected. If Netwatch was closed, no email is sent — monitoring resumes when you reopen the app.

### Where are my devices and settings stored?
In `data\netwatch.json` and `data\settings.json`, next to `Netwatch.exe`. You can open these files in any text editor to inspect them.

### The app says "Unknown" for a device that exists.
"Unknown" means the device hasn't been checked yet. Wait 30 seconds, or click **"Test Now"**.

### Why does my device show "Port Blocked" when I expect "Online"?
The device is reachable, but the specific **port** you're monitoring is closed. This means the *service* on that port isn't running. Check the device's services, or remove the port from the device config to fall back to ICMP-only checking.

### Can I monitor a device by hostname instead of IP?
**Not yet.** Netwatch currently requires IPv4 addresses (e.g., `192.168.1.1`). Hostname support may be added in a future version.

---

## Support

Netwatch is free and always will be. If it helps you, consider leaving a small tip:

- ☕ [Ko-fi](https://ko-fi.com/claudiotavares)
- 💬 Or just [open an issue](https://github.com/ClaudioTvares/netwatch/issues) with feedback or bugs — it's equally valuable.

Thank you for using Netwatch!