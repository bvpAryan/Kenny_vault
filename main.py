"""
main.py - Entry point for the Kenni Secure Personal Vault .
"""

import tkinter as tk
import sys
import os

# Allow relative imports when run as a script
sys.path.insert(0, os.path.dirname(__file__))

from login import LoginScreen
from vault_ui import VaultUI


class VaultApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KENNI")
        self.geometry("980x660")
        self.minsize(860, 560)
        self.configure(bg="#0d0f14")

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 980) // 2
        y = (self.winfo_screenheight() - 660) // 2
        self.geometry(f"980x660+{x}+{y}")

        # Attempt to set a window icon (optional; skip if missing)
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        self._show_login()

    def _show_login(self):
        self._clear()
        LoginScreen(self, on_success=self._on_unlock)

    def _on_unlock(self, fernet_key):
        self._clear()
        VaultUI(self, fernet_key=fernet_key, on_lock=self._on_lock)

    def _on_lock(self):
        self._clear()
        LoginScreen(self, on_success=self._on_unlock)

    def _clear(self):
        for widget in self.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    app = VaultApp()
    app.mainloop()
