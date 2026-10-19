"""Entry point for Netwatch.

This file is intentionally tiny. Its only job is to start the GUI.
All logic lives in the `netwatch` package, so this file is what
PyInstaller will wrap into `Netwatch.exe` later.

Two things happen here:
  1. `storage.close()` is registered as a shutdown hook so TinyDB
     flushes to disk when the app exits. (Without this, the last few
     writes could be lost on an unclean close.)
  2. The `App` window is created and its main loop is started.
"""

import atexit

from netwatch.storage import close as close_storage
from netwatch.gui import App


def main() -> None:
    atexit.register(close_storage)
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()