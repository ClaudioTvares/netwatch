"""System tray integration for Netwatch."""

import sys
import threading
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageDraw
import pystray


def _load_tray_image():
    """Load the .ico as a PIL image for the tray icon."""
    try:
        if getattr(sys, "frozen", False):
            # Running as .exe
            base = Path(sys._MEIPASS)
        else:
            # Running as .py script
            base = Path(__file__).resolve().parent.parent
            
        icon_path = base / "netwatch.ico"
        return Image.open(icon_path)
    except Exception:
        # Fallback: a plain green circle
        image = Image.new("RGB", (64, 64), "white")
        dc = ImageDraw.Draw(image)
        dc.ellipse((8, 8, 56, 56), fill="#1a7f37")
        return image


class TrayIcon:
    def __init__(self, app: tk.Tk):
        self.app = app
        
        # Create the icon without a menu first
        self.icon = pystray.Icon(
            "netwatch",
            _load_tray_image(),
            "Netwatch Monitor"
        )
        
        # Build the menu using lambdas to ensure references are kept
        menu = pystray.Menu(
            pystray.MenuItem("Open Netwatch", lambda: self._show_window(), default=True),
            pystray.MenuItem("Exit", lambda: self._quit_app()),
        )
        
        # Attach the menu after the object is fully initialized
        self.icon.menu = menu

    def run(self):
        threading.Thread(target=self.icon.run, daemon=True).start()

    def _show_window(self):
        """Bring the hidden window back."""
        self.app.after(0, self.app.deiconify)
        self.app.after(0, self.app.lift)

    def _quit_app(self):
        """Actually destroy the app."""
        self.icon.stop()
        self.app.after(0, self.app.destroy)