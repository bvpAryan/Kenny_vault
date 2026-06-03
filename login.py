"""
login.py - Master password authentication screen.
"""

import tkinter as tk
from tkinter import messagebox
import storage


# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#0d0f14"
CARD      = "#141720"
BORDER    = "#1e2330"
ACCENT    = "#4f8ef7"
ACCENT2   = "#7c3aed"
TEXT      = "#e8ecf4"
SUBTEXT   = "#6b7280"
ERROR     = "#ef4444"
SUCCESS   = "#10b981"
FONT_HEAD = ("Georgia", 26, "bold")
FONT_SUB  = ("Courier New", 10)
FONT_BODY = ("Segoe UI", 11)
FONT_BTN  = ("Segoe UI", 11, "bold")


class LoginScreen(tk.Frame):
    def __init__(self, master, on_success):
        super().__init__(master, bg=BG)
        self.on_success = on_success
        self.attempt_count = 0
        self.MAX_ATTEMPTS = 5
        self._build()

    def _build(self):
        self.pack(fill="both", expand=True)

        # ── Decorative side bar ──
        #bar = tk.Frame(self, bg=ACCENT2, width=4)
        #bar.pack(side="left", fill="y")

        # ── Centre column ──
        centre = tk.Frame(self, bg=BG)
        centre.pack(expand=True)

        # Shield icon (unicode)
        icon_lbl = tk.Label(centre, text="🔐", font=("Segoe UI Emoji", 52),
                            bg=BG, fg=TEXT)
        icon_lbl.pack(pady=(60, 6))

        tk.Label(centre, text="K E N N I  P E R S O N A L   V A U L T", font=FONT_HEAD,
                 bg=BG, fg=TEXT).pack()
        tk.Label(centre, text="— encrypted  ·  offline  ·  private —",
                 font=FONT_SUB, bg=BG, fg=SUBTEXT).pack(pady=(4, 40))

        # Card
        card = tk.Frame(centre, bg=CARD, padx=40, pady=36,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(ipadx=10, ipady=10)

        self.mode_var = tk.StringVar(value="unlock" if storage.vault_exists() else "create")
        mode = self.mode_var.get()

        if mode == "create":
            tk.Label(card, text="Create Master Password", font=FONT_BODY,
                     bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(0, 6))
        else:
            tk.Label(card, text="Enter Master Password", font=FONT_BODY,
                     bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(0, 6))

        self._pw_var = tk.StringVar()
        pw_frame = tk.Frame(card, bg=BORDER, padx=1, pady=1)
        pw_frame.pack(fill="x")
        pw_inner = tk.Frame(pw_frame, bg=CARD)
        pw_inner.pack(fill="x")

        self._pw_entry = tk.Entry(pw_inner, textvariable=self._pw_var,
                                  show="●", font=("Courier New", 13),
                                  bg=CARD, fg=TEXT, insertbackground=ACCENT,
                                  relief="flat", bd=10, width=28)
        self._pw_entry.pack(side="left", fill="x", expand=True)

        self._show_btn = tk.Label(pw_inner, text="👁", font=("Segoe UI Emoji", 14),
                                  bg=CARD, fg=SUBTEXT, cursor="hand2", padx=8)
        self._show_btn.pack(side="right")
        self._show_btn.bind("<ButtonPress-1>", lambda e: self._pw_entry.config(show=""))
        self._show_btn.bind("<ButtonRelease-1>", lambda e: self._pw_entry.config(show="●"))

        if mode == "create":
            tk.Label(card, text="Confirm Password", font=FONT_BODY,
                     bg=CARD, fg=SUBTEXT).pack(anchor="w", pady=(18, 6))
            self._pw2_var = tk.StringVar()
            pw2_frame = tk.Frame(card, bg=BORDER, padx=1, pady=1)
            pw2_frame.pack(fill="x")
            pw2_inner = tk.Frame(pw2_frame, bg=CARD)
            pw2_inner.pack(fill="x")
            self._pw2_entry = tk.Entry(pw2_inner, textvariable=self._pw2_var,
                                       show="●", font=("Courier New", 13),
                                       bg=CARD, fg=TEXT, insertbackground=ACCENT,
                                       relief="flat", bd=10, width=28)
            self._pw2_entry.pack(fill="x")

        # Status label
        self._status = tk.Label(card, text="", font=("Segoe UI", 9),
                                 bg=CARD, fg=ERROR)
        self._status.pack(pady=(10, 0))

        # Submit button
        btn_text = "CREATE VAULT" if mode == "create" else "UNLOCK VAULT"
        btn = tk.Button(card, text=btn_text, font=FONT_BTN,
                        bg=ACCENT, fg="white", activebackground=ACCENT2,
                        activeforeground="white", relief="flat",
                        cursor="hand2", padx=20, pady=10,
                        command=self._submit)
        btn.pack(fill="x", pady=(20, 0))
        self._bind_hover(btn)

        self._pw_entry.bind("<Return>", lambda e: self._submit())
        self._pw_entry.focus_set()

        # Attempts indicator
        self._attempts_lbl = tk.Label(centre, text="", font=("Segoe UI", 9),
                                       bg=BG, fg=SUBTEXT)
        self._attempts_lbl.pack(pady=8)

    def _bind_hover(self, widget):
        widget.bind("<Enter>", lambda e: widget.config(bg=ACCENT2))
        widget.bind("<Leave>", lambda e: widget.config(bg=ACCENT))

    def _submit(self):
        pw = self._pw_var.get().strip()
        mode = self.mode_var.get()

        if not pw:
            self._set_status("Password cannot be empty.", error=True)
            return

        if mode == "create":
            pw2 = self._pw2_var.get().strip()
            if pw != pw2:
                self._set_status("Passwords do not match.", error=True)
                return
            if len(pw) < 8:
                self._set_status("Password must be at least 8 characters.", error=True)
                return
            fernet_key = storage.create_vault(pw)
            self._set_status("Vault created!", error=False)
            self.after(600, lambda: self.on_success(fernet_key))
        else:
            if self.attempt_count >= self.MAX_ATTEMPTS:
                self._set_status("Too many attempts. Restart the app.", error=True)
                return

            fernet_key = storage.verify_and_unlock(pw)
            if fernet_key:
                self._set_status("Unlocked!", error=False)
                self.after(300, lambda: self.on_success(fernet_key))
            else:
                self.attempt_count += 1
                remaining = self.MAX_ATTEMPTS - self.attempt_count
                self._set_status(f"Wrong password. {remaining} attempt(s) left.", error=True)
                self._pw_var.set("")
                if remaining == 0:
                    self._set_status("Vault locked. Restart required.", error=True)

    def _set_status(self, msg, error=True):
        self._status.config(text=msg, fg=ERROR if error else SUCCESS)
