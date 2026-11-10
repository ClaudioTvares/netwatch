"""System tray integration for Netwatch."""

import threading
import tkinter as tk
from pathlib import Path
from PIL import Image
import pystray


def _load_tray_image():
    """Load the .ico as a PIL image for the tray icon."""
    # Find the .ico in the project root (or next to the .exe when frozen)
    try:
        import sys
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).resolve().parent.parent
        icon_path = base / "netwatch.ico"
        return Image.open(icon_path)
    except Exception:
        # Fallback: a plain green circle
        from PIL import ImageDraw
        image = Image.new("RGB", (64, 64), "white")
        dc = ImageDraw.Draw(image)
        dc.ellipse((8, 8, 56, 56), fill="#1a7f37")
        return image


class TrayIcon:
    def __init__(self, app: tk.Tk):
        self.app = app
        self.icon = pystray.Icon(
            "netwatch",
            _load_tray_image(),
            "Netwatch Monitor",
            menu=pystray.Menu(
                pystray.MenuItem("Open Netwatch", self.show_window, default=True),
                pystray.MenuItem("Exit", self.quit_app),
            ),
        )

    def run(self):
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon, item):
        self.app.after(0, self.app.deiconify)
        self.app.after(0, self.app.lift)

    def quit_app(self, icon, item):
        self.icon.stop()
        self.app.after(0, self.app.destroy)