"""Tkinter GUI for Netwatch.

This module defines the main application window. It is deliberately
decoupled from `storage.py` and `licensing.py` for now — it only builds
the visual shell (menu bar, toolbar, device table, status bar). Data
wiring comes next session.

Architectural note: everything lives in a single `App` class that
inherits from `tk.Tk`. This is the standard Tkinter pattern. `self` is
the window itself, and every widget we create becomes a child of it.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from .constants import APP_NAME, APP_VERSION


class App(tk.Tk):
    """The main Netwatch window.

    Layout, top to bottom:
        [menu bar]      File / Help
        [toolbar]       Add Device, Edit, Delete, Test Now, Refresh
        [device table]  Status | Name | IP | Port | Latency | Last Check
        [status bar]    Current action / summary text
    """

    def __init__(self):
        super().__init__()

        # ---- window metadata -----------------------------------------
        self.title(f"{APP_NAME} — Network Equipment Monitor")
        self.geometry("960x520")
        self.minsize(800, 400)

        # ---- build the visual layers --------------------------------
        self._build_menu()
        self._build_toolbar()
        self._build_table()
        self._build_statusbar()

    # =================================================================
    # Building blocks
    # =================================================================

    def _build_menu(self) -> None:
        """Top-of-window menu bar."""
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def _build_toolbar(self) -> None:
        """Row of action buttons above the table."""
        bar = ttk.Frame(self, padding=(8, 6))
        bar.pack(fill="x")

        ttk.Button(bar, text="Add Device", command=self._on_add).pack(
            side="left"
        )
        ttk.Button(bar, text="Edit", command=self._on_edit).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(bar, text="Delete", command=self._on_delete).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(bar, text="Test Now", command=self._on_test).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(bar, text="Refresh", command=self._on_refresh).pack(
            side="right"
        )

    def _build_table(self) -> None:
        """The device list — a read-only table with one row per device."""
        columns = (
            "status",
            "name",
            "ip",
            "port",
            "latency",
            "last_check",
        )
        headings = {
            "status": "Status",
            "name": "Name",
            "ip": "IP",
            "port": "Port",
            "latency": "Latency",
            "last_check": "Last Check",
        }
        widths = {
            "status": 90,
            "name": 200,
            "ip": 140,
            "port": 70,
            "latency": 90,
            "last_check": 160,
        }

        # `show="headings"` hides the default first column (the tree
        # expander arrows). We don't need hierarchy — this is a flat list.
        self.tree = ttk.Treeview(
            self, columns=columns, show="headings", selectmode="browse"
        )

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")

        # Color coding per status. Applied when rows are inserted.
        self.tree.tag_configure("online", foreground="#1a7f37")
        self.tree.tag_configure("host_down", foreground="#cf222e")
        self.tree.tag_configure("port_blocked", foreground="#bf8700")
        self.tree.tag_configure("timeout", foreground="#9a6700")
        self.tree.tag_configure("unknown", foreground="#57606a")

        # A scrollbar on the right, in case the list grows long.
        scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=(0, 8))

    def _build_statusbar(self) -> None:
        """A small strip at the bottom for status messages."""
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            padding=(8, 4),
            relief="sunken",
        ).pack(fill="x", side="bottom")

    # =================================================================
    # Stub handlers — wired up next session
    # =================================================================
    #
    # Each of these will eventually call into storage.py and licensing.py.
    # For now, they just show a message so you can see the buttons work.

    def _on_add(self) -> None:
        messagebox.showinfo(
            "Coming soon",
            "Add Device dialog will be wired up next session.",
        )

    def _on_edit(self) -> None:
        messagebox.showinfo(
            "Coming soon",
            "Edit Device dialog will be wired up next session.",
        )

    def _on_delete(self) -> None:
        messagebox.showinfo(
            "Coming soon",
            "Delete will be wired up next session.",
        )

    def _on_test(self) -> None:
        messagebox.showinfo(
            "Coming soon",
            "Live status checking will be wired up next session.",
        )

    def _on_refresh(self) -> None:
        self.status_var.set("Refreshed (nothing to refresh yet).")

    def _show_about(self) -> None:
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\n\n"
            "Local network equipment monitor.\n"
            "No cloud. No telemetry. No subscription.",
        )