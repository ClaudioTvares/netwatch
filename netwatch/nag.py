"""WinRAR-style nag dialog for the free tier."""

import tkinter as tk
from tkinter import ttk, messagebox

from .constants import APP_NAME, NAG_TITLE, NAG_MESSAGE
from .licensing import load_license, save_license_key


class NagDialog(tk.Toplevel):
    def __init__(self, parent, on_license_updated=None):
        super().__init__(parent)
        self.title(NAG_TITLE)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.on_license_updated = on_license_updated

        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text=f"Thank you for trying {APP_NAME}",
                  font=("", 12, "bold")).pack(anchor="w")
        ttk.Label(frm, text=NAG_MESSAGE, wraplength=460,
                  justify="left").pack(anchor="w", pady=(10, 18))

        btns = ttk.Frame(frm)
        btns.pack(fill="x")

        ttk.Button(btns, text="Enter license key",
                   command=self._enter_key).pack(side="left")
        ttk.Button(btns, text="Continue free",
                   command=self.destroy).pack(side="right")
        ttk.Button(btns, text="Buy now",
                   command=self._buy).pack(side="right", padx=(0, 8))

    def _buy(self):
        messagebox.showinfo(
            "Buy Netwatch",
            "Store page coming soon.\n\n"
            "For now, contact the developer to purchase a license."
        )

    def _enter_key(self):
        dlg = tk.Toplevel(self)
        dlg.title("Enter License Key")
        dlg.transient(self); dlg.grab_set()
        frm = ttk.Frame(dlg, padding=14)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Paste your license key:").pack(anchor="w")
        entry = ttk.Entry(frm, width=46)
        entry.pack(pady=8)
        entry.focus_set()

        def submit():
            raw = entry.get().strip()
            lic = save_license_key(raw)
            if not lic:
                messagebox.showerror("Invalid key", "That key is not valid.", parent=dlg)
                return
            messagebox.showinfo(
                "Activated",
                f"License activated:\n{lic.describe()}",
                parent=dlg,
            )
            dlg.destroy()
            self.destroy()
            if self.on_license_updated:
                self.on_license_updated(lic)

        btns = ttk.Frame(frm)
        btns.pack(fill="x", pady=(4, 0))
        ttk.Button(btns, text="Cancel", command=dlg.destroy).pack(side="right")
        ttk.Button(btns, text="Activate", command=submit).pack(side="right", padx=(0, 6))


def should_show_nag() -> bool:
    return not load_license().is_paid