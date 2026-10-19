"""Tkinter GUI for Netwatch.

Two windows live in this file:

    * `App`          — the main window (device list, toolbar, status bar)
    * `DeviceDialog` — a modal popup for adding or editing a device

Keeping them together is fine while the app is this small. If the GUI
grows much larger, `DeviceDialog` should move to its own module.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .constants import APP_NAME, APP_VERSION
from .licensing import can_add_device
from .models import Device
from . import storage


# Colors for the status column, keyed by Device state.
_STATUS_COLORS = {
    "online":       "#1a7f37",  # green
    "host_down":    "#cf222e",  # red
    "port_blocked": "#bf8700",  # amber
    "timeout":      "#9a6700",  # orange
    "unknown":      "#57606a",  # grey
}


class App(tk.Tk):
    """The main Netwatch window."""

    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} — Network Equipment Monitor")
        self.geometry("960x520")
        self.minsize(800, 400)

        self._build_menu()
        self._build_toolbar()
        self._build_table()
        self._build_statusbar()

        self.refresh_table()   # load whatever is already in the DB

    # =================================================================
    # Building blocks
    # =================================================================

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_toolbar(self) -> None:
        bar = ttk.Frame(self, padding=(8, 6))
        bar.pack(fill="x")

        ttk.Button(bar, text="Add Device", command=self._on_add).pack(side="left")
        ttk.Button(bar, text="Edit",       command=self._on_edit).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Delete",     command=self._on_delete).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Test Now",   command=self._on_test).pack(side="left", padx=(6, 0))
        ttk.Button(bar, text="Refresh",    command=self.refresh_table).pack(side="right")

    def _build_table(self) -> None:
        columns = ("status", "name", "ip", "port", "latency", "last_check")
        headings = {
            "status": "Status", "name": "Name", "ip": "IP",
            "port": "Port", "latency": "Latency", "last_check": "Last Check",
        }
        widths = {
            "status": 90, "name": 200, "ip": 140,
            "port": 70, "latency": 90, "last_check": 160,
        }

        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", selectmode="browse"
        )
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        # One tag per state so rows can be colored.
        for state, color in _STATUS_COLORS.items():
            self.tree.tag_configure(state, foreground=color)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=(0, 8))

    def _build_statusbar(self) -> None:
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            self, textvariable=self.status_var, anchor="w",
            padding=(8, 4), relief="sunken",
        ).pack(fill="x", side="bottom")

    # =================================================================
    # Table refresh — the "view" in MVC
    # =================================================================

    def refresh_table(self) -> None:
        """Reload every device from storage and repaint the table."""
        # Wipe existing rows.
        self.tree.delete(*self.tree.get_children())

        devices = storage.list_devices()
        statuses = storage.list_status()

        for device in devices:
            status = statuses.get(device.id, {})
            state = status.get("state", "unknown")
            latency = status.get("latency_ms")
            last_check = status.get("last_check", "")

            latency_str = f"{latency:.0f} ms" if latency is not None else "—"
            last_check_str = last_check.replace("T", " ")[:19] if last_check else "—"

            self.tree.insert(
                "", "end",
                iid=device.id,
                values=(
                    state.replace("_", " ").title(),
                    device.name,
                    device.ip,
                    device.port if device.port else "—",
                    latency_str,
                    last_check_str,
                ),
                tags=(state,),
            )

        self.status_var.set(
            f"{len(devices)} device(s) — last refreshed just now"
        )

    def _selected_device(self) -> Device | None:
        """Return the Device object for the currently selected row, if any."""
        selection = self.tree.selection()
        if not selection:
            return None
        device_id = selection[0]
        return storage.get_device(device_id)

    # =================================================================
    # Button handlers
    # =================================================================

    def _on_add(self) -> None:
        DeviceDialog(self, device=None, on_saved=self.refresh_table)

    def _on_edit(self) -> None:
        device = self._selected_device()
        if device is None:
            messagebox.showinfo("Edit", "Select a device first.")
            return
        DeviceDialog(self, device=device, on_saved=self.refresh_table)

    def _on_delete(self) -> None:
        device = self._selected_device()
        if device is None:
            messagebox.showinfo("Delete", "Select a device first.")
            return
        if not messagebox.askyesno(
            "Delete device",
            f"Delete '{device.name}' ({device.ip})?\n\nThis cannot be undone.",
        ):
            return
        storage.delete_device(device.id)
        self.refresh_table()
        self.status_var.set(f"Deleted '{device.name}'.")

    def _on_test(self) -> None:
        messagebox.showinfo(
            "Coming soon",
            "Live status checking arrives in Step 3.",
        )

    def _show_about(self) -> None:
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Local network equipment monitor.\n"
            "No cloud. No telemetry. No subscription.",
        )


# =====================================================================
# Device dialog (add / edit)
# =====================================================================

class DeviceDialog(tk.Toplevel):
    """Modal dialog used for both adding and editing a device."""

    def __init__(self, parent: App, device: Device | None, on_saved):
        super().__init__(parent)
        self._on_saved = on_saved
        self._editing = device is not None
        self._device = device

        # Window setup
        self.title("Edit Device" if self._editing else "Add Device")
        self.resizable(False, False)
        self.transient(parent)     # keeps it on top of the main window
        self.grab_set()            # modal: parent window is frozen until this closes

        # State variables — one per input field.
        # Pre-fill from the device if editing.
        self.var_name = tk.StringVar(value=device.name if device else "")
        self.var_ip = tk.StringVar(value=device.ip if device else "")
        self.var_port = tk.StringVar(
            value=str(device.port) if device and device.port else ""
        )
        self.var_interval = tk.StringVar(
            value=str(device.check_interval) if device else "30"
        )
        self.var_email = tk.BooleanVar(value=device.notify_email if device else True)
        self.var_whatsapp = tk.BooleanVar(
            value=device.notify_whatsapp if device else True
        )

        self._build_widgets()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        row = 0
        ttk.Label(frame, text="Name").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.var_name, width=32).grid(
            row=row, column=1, pady=4
        )

        row += 1
        ttk.Label(frame, text="IP address").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.var_ip, width=32).grid(
            row=row, column=1, pady=4
        )

        row += 1
        ttk.Label(frame, text="Port (optional)").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.var_port, width=32).grid(
            row=row, column=1, pady=4
        )

        row += 1
        ttk.Label(frame, text="Check interval (sec)").grid(
            row=row, column=0, sticky="w", pady=4
        )
        ttk.Entry(frame, textvariable=self.var_interval, width=32).grid(
            row=row, column=1, pady=4
        )

        row += 1
        ttk.Checkbutton(
            frame, text="Email alerts", variable=self.var_email
        ).grid(row=row, column=1, sticky="w", pady=(8, 0))

        row += 1
        ttk.Checkbutton(
            frame, text="WhatsApp alerts", variable=self.var_whatsapp
        ).grid(row=row, column=1, sticky="w", pady=(4, 0))

        # Buttons at the bottom.
        row += 1
        buttons = ttk.Frame(frame)
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(
            side="right", padx=(6, 0)
        )
        ttk.Button(buttons, text="Save", command=self._save).pack(side="right")

    def _save(self) -> None:
        # ---- read + trim input ---------------------------------------
        name = self.var_name.get().strip()
        ip = self.var_ip.get().strip()
        port_str = self.var_port.get().strip()
        interval_str = self.var_interval.get().strip()

        # ---- validate name -------------------------------------------
        if not name:
            messagebox.showerror("Invalid", "Name is required.", parent=self)
            return

        # ---- validate IP ---------------------------------------------
        if not _is_valid_ipv4(ip):
            messagebox.showerror(
                "Invalid",
                f"'{ip}' is not a valid IPv4 address.\n\n"
                "Use the format: 192.168.1.1",
                parent=self,
            )
            return

        # ---- validate port (optional, so empty is OK) ----------------
        port: int | None = None
        if port_str:
            try:
                port = int(port_str)
            except ValueError:
                messagebox.showerror(
                    "Invalid", "Port must be a number.", parent=self
                )
                return
            if not (1 <= port <= 65535):
                messagebox.showerror(
                    "Invalid", "Port must be between 1 and 65535.", parent=self
                )
                return

        # ---- validate interval ---------------------------------------
        try:
            interval = int(interval_str)
        except ValueError:
            messagebox.showerror(
                "Invalid", "Check interval must be a number.", parent=self
            )
            return
        if interval < 5:
            messagebox.showerror(
                "Invalid",
                "Check interval must be at least 5 seconds.",
                parent=self,
            )
            return

        # ---- license check (only when adding a new device) -----------
        if not self._editing:
            allowed, reason = can_add_device(storage.count_devices())
            if not allowed:
                messagebox.showwarning("Limit reached", reason, parent=self)
                return

        # ---- save ----------------------------------------------------
        if self._editing and self._device is not None:
            self._device.name = name
            self._device.ip = ip
            self._device.port = port
            self._device.check_interval = interval
            self._device.notify_email = self.var_email.get()
            self._device.notify_whatsapp = self.var_whatsapp.get()
            storage.update_device(self._device)
        else:
            new_device = Device(
                name=name,
                ip=ip,
                port=port,
                check_interval=interval,
                notify_email=self.var_email.get(),
                notify_whatsapp=self.var_whatsapp.get(),
            )
            storage.add_device(new_device)

        # ---- done ----------------------------------------------------
        self.destroy()
        self._on_saved()


# ---------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------

def _is_valid_ipv4(ip: str) -> bool:
    """A pragmatic IPv4 check.

    Doesn't reject leading zeros or edge cases the way `ipaddress` does,
    but catches the common typos (empty input, wrong number of parts,
    out-of-range octets, non-numeric chars).
    """
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        # Reject "01" style — real dotted-quad never needs leading zeros.
        if len(part) > 1 and part.startswith("0"):
            return False
        if not (0 <= int(part) <= 255):
            return False
    return True