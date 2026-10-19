"""Tkinter GUI for Netwatch."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timezone

from .constants import APP_NAME, APP_VERSION
from .licensing import can_add_device
from .models import Device
from . import settings as settings_module
from . import storage
from . import notifier
from .monitor import full_check
from .engine import MonitorEngine
from .nag import NagDialog, should_show_nag


_STATUS_COLORS = {
    "online":       "#1a7f37",
    "host_down":    "#cf222e",
    "port_blocked": "#bf8700",
    "timeout":      "#9a6700",
    "unknown":      "#57606a",
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

        self.engine = MonitorEngine(on_update=self._engine_updated)
        self.engine.start()

        self.refresh_table()

        if should_show_nag():
            self.after(500, lambda: NagDialog(self, on_license_updated=self._on_license_updated))

    def _build_menu(self) -> None:
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Settings…", command=self._open_settings)
        file_menu.add_separator()
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

        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        for state, color in _STATUS_COLORS.items():
            self.tree.tag_configure(state, foreground=color)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=(0, 8))

    def _build_statusbar(self) -> None:
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, anchor="w", padding=(8, 4), relief="sunken").pack(fill="x", side="bottom")

    def refresh_table(self) -> None:
        self.tree.delete(*self.tree.get_children())
        devices = storage.list_devices()
        statuses = storage.list_status()

        for device in devices:
            status = statuses.get(device.id, {})
            state = status.get("state", "unknown")
            latency = status.get("latency_ms")
            last_check = status.get("last_check", "")

            latency_str = f"{latency:.0f} ms" if latency is not None else "—"
            
            if last_check:
                dt = datetime.fromisoformat(last_check)
                last_check_str = dt.astimezone().strftime("%Y-%m-%d %H:%M:%S")
            else:
                last_check_str = "—"

            self.tree.insert(
                "", "end", iid=device.id,
                values=(
                    state.replace("_", " ").title(),
                    device.name, device.ip,
                    device.port if device.port else "—",
                    latency_str, last_check_str,
                ),
                tags=(state,),
            )
        self.status_var.set(f"{len(devices)} device(s) — last refreshed just now")

    def _selected_device(self) -> Device | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return storage.get_device(selection[0])

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
        if not messagebox.askyesno("Delete device", f"Delete '{device.name}' ({device.ip})?\n\nThis cannot be undone."):
            return
        storage.delete_device(device.id)
        self.refresh_table()
        self.status_var.set(f"Deleted '{device.name}'.")

    def _on_test(self) -> None:
        device = self._selected_device()
        if device is None:
            messagebox.showinfo("Test", "Select a device first.")
            return
        
        self.status_var.set(f"Testing {device.name}...")
        self.update_idletasks()
        
        result = full_check(ip=device.ip, port=device.port)
        now = datetime.now(timezone.utc).isoformat()
        
        storage.save_status(device.id, {
            "state": result.state.value,
            "latency_ms": result.latency_ms,
            "last_check": now,
            "error": result.error,
        })
        
        self.refresh_table()
        state_name = result.state.value.replace('_', ' ').title()
        self.status_var.set(f"Test complete: {device.name} is {state_name}")

    def _show_about(self) -> None:
        messagebox.showinfo(f"About {APP_NAME}", f"{APP_NAME} v{APP_VERSION}\n\nLocal network equipment monitor.\nNo cloud. No telemetry. No subscription.")

    def _open_settings(self) -> None:
        SettingsDialog(self)

    def _on_license_updated(self, license_obj):
        self.status_var.set(f"License updated: {license_obj.describe()}")

    def _engine_updated(self) -> None:
        self.after(0, self.refresh_table)

    def destroy(self) -> None:
        if hasattr(self, "engine"):
            self.engine.stop()
        super().destroy()


class DeviceDialog(tk.Toplevel):
    def __init__(self, parent: App, device: Device | None, on_saved):
        super().__init__(parent)
        self._on_saved = on_saved
        self._editing = device is not None
        self._device = device

        self.title("Edit Device" if self._editing else "Add Device")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.var_name = tk.StringVar(value=device.name if device else "")
        self.var_ip = tk.StringVar(value=device.ip if device else "")
        self.var_port = tk.StringVar(value=str(device.port) if device and device.port else "")
        self.var_interval = tk.StringVar(value=str(device.check_interval) if device else "30")
        self.var_email = tk.BooleanVar(value=device.notify_email if device else True)
        self.var_email_to = tk.StringVar(value=device.notify_email_to if device and device.notify_email_to else "")

        self._build_widgets()

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        row = 0
        ttk.Label(frame, text="Name").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.var_name, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(frame, text="IP address").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.var_ip, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(frame, text="Port (optional)").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.var_port, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(frame, text="Check interval (sec)").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.var_interval, width=32).grid(row=row, column=1, pady=4)

        row += 1
        self.chk_email = ttk.Checkbutton(
            frame, 
            text="Enable Email alerts", 
            variable=self.var_email, 
            command=self._toggle_email_entry
        )
        self.chk_email.grid(row=row, column=1, sticky="w", pady=(12, 0))

        row += 1
        ttk.Label(frame, text="Send to (Overrides Global)").grid(row=row, column=0, sticky="w", pady=4)
        self.ent_email_to = ttk.Entry(frame, textvariable=self.var_email_to, width=32)
        self.ent_email_to.grid(row=row, column=1, pady=4)
        
        row += 1
        ttk.Label(
            frame, 
            text="Leave blank to use the email from Settings.", 
            foreground="#57606a",
            font=("", 8)
        ).grid(row=row, column=1, sticky="w")

        self._toggle_email_entry()

        row += 1
        buttons = ttk.Frame(frame)
        buttons.grid(row=row, column=0, columnspan=2, sticky="e", pady=(16, 0))
        ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text="Save", command=self._save).pack(side="right")

    def _toggle_email_entry(self) -> None:
        if self.var_email.get():
            self.ent_email_to.configure(state="normal")
        else:
            self.ent_email_to.configure(state="disabled")

    def _save(self) -> None:
        name = self.var_name.get().strip()
        ip = self.var_ip.get().strip()
        port_str = self.var_port.get().strip()
        interval_str = self.var_interval.get().strip()

        if not name:
            messagebox.showerror("Invalid", "Name is required.", parent=self)
            return
        if not _is_valid_ipv4(ip):
            messagebox.showerror("Invalid", f"'{ip}' is not a valid IPv4 address.", parent=self)
            return

        port: int | None = None
        if port_str:
            try:
                port = int(port_str)
            except ValueError:
                messagebox.showerror("Invalid", "Port must be a number.", parent=self)
                return
            if not (1 <= port <= 65535):
                messagebox.showerror("Invalid", "Port must be between 1 and 65535.", parent=self)
                return

        try:
            interval = int(interval_str)
        except ValueError:
            messagebox.showerror("Invalid", "Check interval must be a number.", parent=self)
            return
        if interval < 5:
            messagebox.showerror("Invalid", "Check interval must be at least 5 seconds.", parent=self)
            return

        if not self._editing:
            allowed, reason = can_add_device(storage.count_devices())
            if not allowed:
                messagebox.showwarning("Limit reached", reason, parent=self)
                return

        if self._editing and self._device is not None:
            self._device.name = name
            self._device.ip = ip
            self._device.port = port
            self._device.check_interval = interval
            self._device.notify_email = self.var_email.get()
            self._device.notify_email_to = self.var_email_to.get().strip() or None
            storage.update_device(self._device)
        else:
            new_device = Device(
                name=name, ip=ip, port=port, check_interval=interval,
                notify_email=self.var_email.get(),
                notify_email_to=self.var_email_to.get().strip() or None,
            )
            storage.add_device(new_device)

        self.destroy()
        self._on_saved()


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent: App):
        super().__init__(parent)
        self.title("Settings")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        current = settings_module.load_settings()
        
        c = current.get("company_email", {})
        self.var_co_host = tk.StringVar(value=c.get("host", "smtp.office365.com"))
        self.var_co_port = tk.StringVar(value=str(c.get("port", 587)))
        self.var_co_user = tk.StringVar(value=c.get("user", ""))
        self.var_co_pass = tk.StringVar(value=c.get("password", ""))
        self.var_co_to = tk.StringVar(value=c.get("to", ""))

        p = current.get("personal_email", {})
        self.var_pe_host = tk.StringVar(value=p.get("host", ""))
        self.var_pe_port = tk.StringVar(value=str(p.get("port", 587)))
        self.var_pe_user = tk.StringVar(value=p.get("user", ""))
        self.var_pe_pass = tk.StringVar(value=p.get("password", ""))
        self.var_pe_to = tk.StringVar(value=p.get("to", ""))

        self._build_widgets()

    def _build_widgets(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # TAB 1: COMPANY
        frame_co = ttk.Frame(notebook, padding=16)
        notebook.add(frame_co, text="  Company Email  ")

        row = 0
        ttk.Label(
            frame_co, 
            text="Used to send alerts to IT team members.\nRequires a company SMTP server (e.g., Office 365).",
            foreground="#57606a",
            justify="left"
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 12))

        row += 1
        ttk.Label(frame_co, text="Login (email)").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_co, textvariable=self.var_co_user, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(frame_co, text="Password / App Key").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_co, textvariable=self.var_co_pass, width=32, show="*").grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(frame_co, text="Global Fallback Email").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_co, textvariable=self.var_co_to, width=32).grid(row=row, column=1, pady=4)
        
        row += 1
        ttk.Label(
            frame_co, 
            text="Used only if a device doesn't specify its own email.", 
            foreground="#57606a",
            font=("", 8)
        ).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame_co, text="SMTP Host").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_co, textvariable=self.var_co_host, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(frame_co, text="SMTP Port").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_co, textvariable=self.var_co_port, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Button(frame_co, text="Test Company Email", command=lambda: self._test_email("company")).grid(row=row, column=1, sticky="w", pady=16)

        # TAB 2: PERSONAL
        frame_pe = ttk.Frame(notebook, padding=16)
        notebook.add(frame_pe, text="  Personal Email  ")

        row = 0
        ttk.Label(
            frame_pe, 
            text="Fallback for home users or small setups.\nAuto-detects Gmail, Outlook, Yahoo, and custom domains.",
            foreground="#57606a",
            justify="left"
        ).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 12))

        row += 1
        ttk.Label(frame_pe, text="Login (email)").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_pe, textvariable=self.var_pe_user, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(frame_pe, text="Password / App Key").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_pe, textvariable=self.var_pe_pass, width=32, show="*").grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(frame_pe, text="Global Fallback Email").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_pe, textvariable=self.var_pe_to, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(
            frame_pe, 
            text="Used only if a device doesn't specify its own email.", 
            foreground="#57606a",
            font=("", 8)
        ).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(frame_pe, text="SMTP Host (optional)").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Entry(frame_pe, textvariable=self.var_pe_host, width=32).grid(row=row, column=1, pady=4)

        row += 1
        ttk.Label(
            frame_pe, 
            text="Leave blank to auto-detect based on email provider.", 
            foreground="#57606a",
            font=("", 8)
        ).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Button(frame_pe, text="Test Personal Email", command=lambda: self._test_email("personal")).grid(row=row, column=1, sticky="w", pady=16)

        # BUTTONS
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right", padx=(6, 0))
        ttk.Button(btn_frame, text="Save All Settings", command=self._save).pack(side="right")

    def _save(self) -> None:
        def get_port(port_str):
            try: return int(port_str)
            except ValueError: return 587

        co_cfg = {
            "host": self.var_co_host.get().strip(),
            "port": get_port(self.var_co_port.get().strip()),
            "user": self.var_co_user.get().strip(),
            "password": self.var_co_pass.get(),
            "to": self.var_co_to.get().strip(),
        }
        pe_cfg = {
            "host": self.var_pe_host.get().strip(),
            "port": 587,
            "user": self.var_pe_user.get().strip(),
            "password": self.var_pe_pass.get(),
            "to": self.var_pe_to.get().strip(),
        }

        settings_module.save_settings({
            "company_email": co_cfg,
            "personal_email": pe_cfg
        })
        messagebox.showinfo("Success", "Settings saved successfully.", parent=self)
        self.destroy()

    def _test_email(self, section: str) -> None:
        if section == "company":
            host = self.var_co_host.get().strip()
            user = self.var_co_user.get().strip()
            pwd = self.var_co_pass.get()
            to_addr = self.var_co_to.get().strip()
            port_str = self.var_co_port.get().strip()
        else:
            host = self.var_pe_host.get().strip()
            user = self.var_pe_user.get().strip()
            pwd = self.var_pe_pass.get()
            to_addr = self.var_pe_to.get().strip()
            port_str = "587"

        if not user or not pwd:
            messagebox.showerror("Error", f"Please enter a Login and Password for the {section} email.", parent=self)
            return
        
        if not to_addr:
            messagebox.showerror("Error", f"Please enter a Global Fallback Email for the {section} setup.", parent=self)
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Error", "SMTP Port must be a valid number.", parent=self)
            return

        if not host and "@" in user:
            domain = user.split("@")[1].lower()
            if "gmail" in domain: host = "smtp.gmail.com"
            elif "outlook" in domain or "hotmail" in domain: host = "smtp-mail.outlook.com"
            elif "yahoo" in domain: host = "smtp.mail.yahoo.com"
            else: host = "smtp.gmail.com"  # Sensible default

        cfg = {"host": host, "port": port, "user": user, "password": pwd, "to": to_addr}
        
        self.config(cursor="watch")
        self.update_idletasks()

        success = notifier.send_email(cfg, f"Netwatch Test ({section.title()})", f"This is a test email from the {section} configuration.")

        self.config(cursor="")

        if success:
            messagebox.showinfo("Success", f"Test email sent successfully to {to_addr}!", parent=self)
        else:
            messagebox.showerror("Failed", "Could not send email.\n\nCheck your VS Code terminal for the exact error message.", parent=self)


def _is_valid_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit(): return False
        if len(part) > 1 and part.startswith("0"): return False
        if not (0 <= int(part) <= 255): return False
    return True