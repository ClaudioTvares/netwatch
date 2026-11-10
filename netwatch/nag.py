"""Startup dialog encouraging donations."""

import tkinter as tk
from tkinter import ttk
import webbrowser

from .constants import APP_NAME


class NagDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(f"Support {APP_NAME}")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)

        # Title
        ttk.Label(
            frm, 
            text=f"Thank you for using {APP_NAME}!", 
            font=("", 14, "bold")
        ).pack(anchor="w")
        
        # Personal message
        msg = (
            "Netwatch is completely free, local, and privacy-friendly. "
            "There is no cloud, no telemetry, and no tracking.\n\n"
            "I built this project to help me buy my first car. If Netwatch "
            "saves you time or helps you keep your network running, "
            "please consider supporting the project!"
        )
        ttk.Label(
            frm, 
            text=msg, 
            wraplength=420, 
            justify="left"
        ).pack(anchor="w", pady=(10, 20))

        # Buttons
        btns = ttk.Frame(frm)
        btns.pack(fill="x")

        ttk.Button(
            btns, 
            text="❤ Support the Project", 
            command=self._donate
        ).pack(side="left")

        ttk.Button(
            btns, 
            text="Continue",
            command=self.destroy
        ).pack(side="right")

    def _donate(self):
        # Placeholder link — replace with your actual Ko-fi / Buy Me a Coffee link
        webbrowser.open("https://ko-fi.com/yourusername")
        self.destroy()


def should_show_nag() -> bool:
    """Show the dialog only once per day, or on first launch."""
    # For simplicity, we just always show it on startup for now.
    # You can make this smarter later by storing a "last_nag_date" in settings.
    return True