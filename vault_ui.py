"""
vault_ui.py - Main vault dashboard with passwords, notes, files tabs.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import os
import time
import storage

# ── Palette ──────────────────────────────────────────────────────────────────
BG        = "#0d0f14"
CARD      = "#141720"
CARD2     = "#1a1f2e"
BORDER    = "#1e2330"
ACCENT    = "#4f8ef7"
ACCENT2   = "#7c3aed"
ACCENT3   = "#10b981"
TEXT      = "#e8ecf4"
SUBTEXT   = "#6b7280"
ERROR     = "#ef4444"
ROW_ODD   = "#14181f"
ROW_EVEN  = "#171c27"
FONT_HEAD = ("Georgia", 18, "bold")
FONT_BODY = ("Segoe UI", 11)
FONT_MONO = ("Courier New", 11)
FONT_SMALL= ("Segoe UI", 9)
FONT_BTN  = ("Segoe UI", 10, "bold")

AUTO_LOCK_SECONDS = 60


class VaultUI(tk.Frame):
    def __init__(self, master, fernet_key, on_lock):
        super().__init__(master, bg=BG)
        self.fernet_key = fernet_key
        self.on_lock = on_lock
        self.vault_data = storage.load_vault(fernet_key)
        self._last_activity = time.time()
        self._build()
        self._start_auto_lock()

    # ── Auto-lock ─────────────────────────────────────────────────────────────
    def _start_auto_lock(self):
        self._auto_lock_job = self.after(5000, self._check_auto_lock)

    def _check_auto_lock(self):
        if time.time() - self._last_activity > AUTO_LOCK_SECONDS:
            self._do_lock()
        else:
            self._auto_lock_job = self.after(5000, self._check_auto_lock)

    def _reset_timer(self, event=None):
        self._last_activity = time.time()

    def _do_lock(self):
        try:
            self.after_cancel(self._auto_lock_job)
        except Exception:
            pass
        self.on_lock()

    def _show_change_password(self):
        """Render the Change Password page inside the main content area."""
        self._active_tab.set("settings")
        # Dim all nav buttons
        for k, (frame, lbl) in self._tab_btns.items():
            frame.config(bg=CARD)
            lbl.config(bg=CARD, fg=SUBTEXT)

        for w in self._content.winfo_children():
            w.destroy()

        ChangePasswordPage(
            self._content,
            on_success=self._do_lock,
            on_cancel=lambda: self._show_tab("passwords"),
            vault_data=self.vault_data,
        ).pack(fill="both", expand=True)

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build(self):
        self.pack(fill="both", expand=True)
        self.bind_all("<Motion>", self._reset_timer)
        self.bind_all("<Key>", self._reset_timer)

        # ── Sidebar ──
        sidebar = tk.Frame(self, bg=CARD, width=220,
                           highlightbackground=BORDER, highlightthickness=1)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="🔐", font=("Segoe UI Emoji", 32),
                 bg=CARD, fg=TEXT).pack(pady=(30, 4))
        tk.Label(sidebar, text="KENNI VAULT", font=("Georgia", 15, "bold"),
                 bg=CARD, fg=TEXT).pack()
        tk.Label(sidebar, text="personal security suite",
                 font=FONT_SMALL, bg=CARD, fg=SUBTEXT).pack(pady=(2, 30))

        separator = tk.Frame(sidebar, bg=BORDER, height=1)
        separator.pack(fill="x", padx=20, pady=(0, 20))

        self._tab_btns = {}
        self._active_tab = tk.StringVar(value="passwords")
        nav_items = [
            ("🔑", "Passwords", "passwords"),
            ("📝", "Notes", "notes"),
            ("📁", "Files", "files"),
        ]
        for icon, label, key in nav_items:
            btn = self._nav_btn(sidebar, icon, label, key)
            self._tab_btns[key] = btn

        # Spacer
        tk.Frame(sidebar, bg=CARD).pack(expand=True)

        # Change password button
        chpw_btn = tk.Button(sidebar, text="🔑  Change Password",
                             font=FONT_BTN, bg=BORDER, fg=SUBTEXT,
                             activebackground=ACCENT2, activeforeground="white",
                             relief="flat", cursor="hand2", pady=10,
                             command=self._show_change_password)
        chpw_btn.pack(fill="x", padx=16, pady=(0, 6))

        # Lock button at bottom
        lock_btn = tk.Button(sidebar, text="🔒  Lock Vault",
                             font=FONT_BTN, bg=BORDER, fg=SUBTEXT,
                             activebackground=ERROR, activeforeground="white",
                             relief="flat", cursor="hand2", pady=10,
                             command=self._do_lock)
        lock_btn.pack(fill="x", padx=16, pady=(0, 20))

        # ── Main content area ──
        self._content = tk.Frame(self, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        self._show_tab("passwords")

    def _nav_btn(self, parent, icon, label, key):
        frame = tk.Frame(parent, bg=CARD, cursor="hand2")
        frame.pack(fill="x", padx=12, pady=2)

        lbl = tk.Label(frame, text=f"  {icon}  {label}",
                       font=FONT_BODY, bg=CARD, fg=SUBTEXT,
                       anchor="w", pady=10, padx=8)
        lbl.pack(fill="x")

        def activate(e=None):
            self._show_tab(key)

        frame.bind("<Button-1>", activate)
        lbl.bind("<Button-1>", activate)

        def on_enter(e):
            if self._active_tab.get() != key:
                frame.config(bg=CARD2)
                lbl.config(bg=CARD2)

        def on_leave(e):
            if self._active_tab.get() != key:
                frame.config(bg=CARD)
                lbl.config(bg=CARD)

        frame.bind("<Enter>", on_enter)
        lbl.bind("<Enter>", on_enter)
        frame.bind("<Leave>", on_leave)
        lbl.bind("<Leave>", on_leave)

        return (frame, lbl)

    def _show_tab(self, key):
        self._active_tab.set(key)
        # Update nav highlights
        for k, (frame, lbl) in self._tab_btns.items():
            if k == key:
                frame.config(bg=ACCENT)
                lbl.config(bg=ACCENT, fg="white")
            else:
                frame.config(bg=CARD)
                lbl.config(bg=CARD, fg=SUBTEXT)

        # Destroy current content
        for w in self._content.winfo_children():
            w.destroy()

        if key == "passwords":
            PasswordsTab(self._content, self.vault_data,
                         self.fernet_key, self._save).pack(fill="both", expand=True)
        elif key == "notes":
            NotesTab(self._content, self.vault_data,
                     self.fernet_key, self._save).pack(fill="both", expand=True)
        elif key == "files":
            FilesTab(self._content, self.vault_data,
                     self.fernet_key, self._save).pack(fill="both", expand=True)
        elif key == "settings":
            ChangePasswordPage(
                self._content,
                on_success=self._do_lock,
                on_cancel=lambda: self._show_tab("passwords"),
                vault_data=self.vault_data,
            ).pack(fill="both", expand=True)

    def _save(self):
        storage.save_vault(self.vault_data, self.fernet_key)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _styled_entry(parent, **kwargs):
    e = tk.Entry(parent, font=FONT_MONO, bg=CARD2, fg=TEXT,
                 insertbackground=ACCENT, relief="flat",
                 highlightbackground=BORDER, highlightthickness=1, bd=8, **kwargs)
    return e

def _styled_btn(parent, text, color=ACCENT, **kwargs):
    btn = tk.Button(parent, text=text, font=FONT_BTN,
                    bg=color, fg="white", activebackground=ACCENT2,
                    activeforeground="white", relief="flat",
                    cursor="hand2", padx=14, pady=7, **kwargs)
    return btn

def _section_header(parent, title, subtitle=""):
    hdr = tk.Frame(parent, bg=BG)
    hdr.pack(fill="x", padx=30, pady=(28, 0))
    tk.Label(hdr, text=title, font=FONT_HEAD, bg=BG, fg=TEXT).pack(side="left")
    if subtitle:
        tk.Label(hdr, text=subtitle, font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(
            side="left", padx=12, pady=4)
    return hdr


# ── Passwords Tab ─────────────────────────────────────────────────────────────

class PasswordsTab(tk.Frame):
    def __init__(self, master, vault_data, fernet_key, save_cb):
        super().__init__(master, bg=BG)
        self.vault_data = vault_data
        self.save_cb = save_cb
        self._build()

    def _build(self):
        hdr = _section_header(self, "🔑  Passwords")
        _styled_btn(hdr, "+ Add Entry", command=self._add_dialog).pack(side="right")

        # Search bar
        sf = tk.Frame(self, bg=BG)
        sf.pack(fill="x", padx=30, pady=(12, 0))
        tk.Label(sf, text="🔍", font=("Segoe UI Emoji", 12), bg=BG, fg=SUBTEXT).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace("w", lambda *a: self._refresh())
        se = tk.Entry(sf, textvariable=self._search_var, font=FONT_BODY,
                      bg=CARD2, fg=TEXT, insertbackground=ACCENT,
                      relief="flat", bd=8, width=30)
        se.pack(side="left", padx=6)

        # Table header
        cols_frame = tk.Frame(self, bg=BORDER)
        cols_frame.pack(fill="x", padx=30, pady=(14, 0))
        for col, w in [("Site / App", 22), ("Username", 20), ("Password", 18), ("Actions", 14)]:
            tk.Label(cols_frame, text=col, font=("Segoe UI", 9, "bold"),
                     bg=BORDER, fg=SUBTEXT, width=w, anchor="w", padx=10, pady=6).pack(side="left")

        # Scrollable list
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, padx=30, pady=(2, 20))

        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self._list_frame = tk.Frame(canvas, bg=BG)
        self._list_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._refresh()

    def _refresh(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        q = self._search_var.get().lower()
        items = self.vault_data.get("passwords", [])
        rows = [i for i in items if q in i.get("site","").lower()
                or q in i.get("username","").lower()] if q else items

        if not rows:
            tk.Label(self._list_frame, text="No entries found.",
                     font=FONT_BODY, bg=BG, fg=SUBTEXT, pady=20).pack()
            return

        for idx, entry in enumerate(rows):
            real_idx = items.index(entry)
            row_bg = ROW_ODD if idx % 2 == 0 else ROW_EVEN
            row = tk.Frame(self._list_frame, bg=row_bg)
            row.pack(fill="x")

            pw_visible = tk.BooleanVar(value=False)
            pw_display = tk.StringVar(value="••••••••••")

            tk.Label(row, text=entry.get("site",""), font=FONT_BODY, bg=row_bg,
                     fg=TEXT, width=22, anchor="w", padx=10, pady=8).pack(side="left")
            tk.Label(row, text=entry.get("username",""), font=FONT_MONO, bg=row_bg,
                     fg=SUBTEXT, width=20, anchor="w", padx=10).pack(side="left")

            pw_lbl = tk.Label(row, textvariable=pw_display, font=FONT_MONO, bg=row_bg,
                              fg=ACCENT3, width=18, anchor="w", padx=10)
            pw_lbl.pack(side="left")

            def toggle_pw(e=None, pv=pw_visible, pd=pw_display, pw=entry.get("password","")):
                if pv.get():
                    pd.set("••••••••••")
                    pv.set(False)
                else:
                    pd.set(pw)
                    pv.set(True)

            act = tk.Frame(row, bg=row_bg)
            act.pack(side="left", padx=6)
            tk.Button(act, text="👁", font=("Segoe UI Emoji", 11), bg=row_bg, fg=SUBTEXT,
                      relief="flat", cursor="hand2", command=toggle_pw).pack(side="left")
            tk.Button(act, text="📋", font=("Segoe UI Emoji", 11), bg=row_bg, fg=SUBTEXT,
                      relief="flat", cursor="hand2",
                      command=lambda pw=entry.get("password",""): self._copy(pw)).pack(side="left")
            tk.Button(act, text="✏️", font=("Segoe UI Emoji", 11), bg=row_bg, fg=SUBTEXT,
                      relief="flat", cursor="hand2",
                      command=lambda i=real_idx: self._edit_dialog(i)).pack(side="left")
            tk.Button(act, text="🗑", font=("Segoe UI Emoji", 11), bg=row_bg, fg=ERROR,
                      relief="flat", cursor="hand2",
                      command=lambda i=real_idx: self._delete(i)).pack(side="left")

    def _copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _add_dialog(self):
        self._entry_dialog(None)

    def _edit_dialog(self, idx):
        self._entry_dialog(idx)

    def _entry_dialog(self, idx):
        existing = self.vault_data["passwords"][idx] if idx is not None else {}
        dlg = tk.Toplevel(self)
        dlg.title("Password Entry")
        dlg.configure(bg=BG)
        dlg.resizable(False, False)
        dlg.grab_set()

        tk.Label(dlg, text="Site / App", font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(
            anchor="w", padx=30, pady=(20, 2))
        site_e = _styled_entry(dlg, width=34)
        site_e.insert(0, existing.get("site",""))
        site_e.pack(padx=30)

        tk.Label(dlg, text="Username / Email", font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(
            anchor="w", padx=30, pady=(12, 2))
        user_e = _styled_entry(dlg, width=34)
        user_e.insert(0, existing.get("username",""))
        user_e.pack(padx=30)

        tk.Label(dlg, text="Password", font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(
            anchor="w", padx=30, pady=(12, 2))
        pw_f = tk.Frame(dlg, bg=BG)
        pw_f.pack(padx=30, fill="x")
        pw_e = _styled_entry(pw_f, show="●", width=28)
        pw_e.insert(0, existing.get("password",""))
        pw_e.pack(side="left")
        show_var = tk.BooleanVar()
        tk.Checkbutton(pw_f, text="Show", variable=show_var, bg=BG, fg=SUBTEXT,
                       selectcolor=CARD2, activebackground=BG,
                       command=lambda: pw_e.config(show="" if show_var.get() else "●")).pack(
            side="left", padx=8)

        tk.Label(dlg, text="Notes (optional)", font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(
            anchor="w", padx=30, pady=(12, 2))
        notes_e = _styled_entry(dlg, width=34)
        notes_e.insert(0, existing.get("notes",""))
        notes_e.pack(padx=30)

        def save():
            entry = {
                "site": site_e.get().strip(),
                "username": user_e.get().strip(),
                "password": pw_e.get(),
                "notes": notes_e.get().strip(),
            }
            if not entry["site"]:
                messagebox.showerror("Error", "Site name required.", parent=dlg)
                return
            if idx is not None:
                self.vault_data["passwords"][idx] = entry
            else:
                self.vault_data["passwords"].append(entry)
            self.save_cb()
            self._refresh()
            dlg.destroy()

        _styled_btn(dlg, "Save Entry", command=save).pack(pady=20)

    def _delete(self, idx):
        if messagebox.askyesno("Delete", "Delete this entry permanently?"):
            self.vault_data["passwords"].pop(idx)
            self.save_cb()
            self._refresh()


# ── Notes Tab ─────────────────────────────────────────────────────────────────

class NotesTab(tk.Frame):
    def __init__(self, master, vault_data, fernet_key, save_cb):
        super().__init__(master, bg=BG)
        self.vault_data = vault_data
        self.save_cb = save_cb
        self._selected = None
        self._build()

    def _build(self):
        hdr = _section_header(self, "📝  Secure Notes")
        _styled_btn(hdr, "+ New Note", command=self._new_note).pack(side="right")

        pane = tk.Frame(self, bg=BG)
        pane.pack(fill="both", expand=True, padx=30, pady=14)

        # Left: note list
        left = tk.Frame(pane, bg=CARD, width=220,
                        highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="Notes", font=("Segoe UI", 10, "bold"),
                 bg=CARD, fg=SUBTEXT, padx=12, pady=10).pack(anchor="w")

        self._list_box = tk.Listbox(left, bg=CARD, fg=TEXT, font=FONT_BODY,
                                    selectbackground=ACCENT, selectforeground="white",
                                    relief="flat", bd=0, activestyle="none")
        self._list_box.pack(fill="both", expand=True)
        self._list_box.bind("<<ListboxSelect>>", self._on_select)

        # Right: editor
        right = tk.Frame(pane, bg=BG)
        right.pack(side="left", fill="both", expand=True)

        title_f = tk.Frame(right, bg=BG)
        title_f.pack(fill="x", pady=(0, 8))
        tk.Label(title_f, text="Title:", font=FONT_BODY, bg=BG, fg=SUBTEXT).pack(side="left")
        self._title_var = tk.StringVar()
        self._title_entry = _styled_entry(title_f, textvariable=self._title_var, width=30)
        self._title_entry.pack(side="left", padx=8)

        self._text_area = tk.Text(right, font=FONT_MONO, bg=CARD2, fg=TEXT,
                                  insertbackground=ACCENT, relief="flat",
                                  highlightbackground=BORDER, highlightthickness=1,
                                  bd=10, wrap="word")
        self._text_area.pack(fill="both", expand=True)

        btn_f = tk.Frame(right, bg=BG)
        btn_f.pack(fill="x", pady=10)
        _styled_btn(btn_f, "💾  Save Note", command=self._save_note).pack(side="left")
        _styled_btn(btn_f, "🗑  Delete", color=ERROR, command=self._delete_note).pack(side="left", padx=8)

        self._refresh_list()

    def _refresh_list(self):
        self._list_box.delete(0, "end")
        for note in self.vault_data.get("notes", []):
            self._list_box.insert("end", "  " + note.get("title", "Untitled"))

    def _on_select(self, event):
        sel = self._list_box.curselection()
        if not sel:
            return
        idx = sel[0]
        self._selected = idx
        note = self.vault_data["notes"][idx]
        self._title_var.set(note.get("title",""))
        self._text_area.delete("1.0", "end")
        self._text_area.insert("1.0", note.get("content",""))

    def _new_note(self):
        self._selected = None
        self._title_var.set("")
        self._text_area.delete("1.0", "end")
        self._title_entry.focus_set()

    def _save_note(self):
        title = self._title_var.get().strip() or "Untitled"
        content = self._text_area.get("1.0", "end-1c")
        note = {"title": title, "content": content}
        if self._selected is not None:
            self.vault_data["notes"][self._selected] = note
        else:
            self.vault_data["notes"].append(note)
            self._selected = len(self.vault_data["notes"]) - 1
        self.save_cb()
        self._refresh_list()

    def _delete_note(self):
        if self._selected is None:
            return
        if messagebox.askyesno("Delete", "Delete this note?"):
            self.vault_data["notes"].pop(self._selected)
            self._selected = None
            self._title_var.set("")
            self._text_area.delete("1.0", "end")
            self.save_cb()
            self._refresh_list()


# ── Change Password Page ──────────────────────────────────────────────────────

class ChangePasswordPage(tk.Frame):
    """Full in-app page for changing the master password."""

    def __init__(self, master, on_success, on_cancel, vault_data):
        super().__init__(master, bg=BG)
        self.on_success  = on_success
        self.on_cancel   = on_cancel
        self.vault_data  = vault_data
        self._build()

    def _build(self):
        # ── Outer centering wrapper ──
        outer = tk.Frame(self, bg=BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        # Header
        tk.Label(outer, text="🔑", font=("Segoe UI Emoji", 40),
                 bg=BG, fg=TEXT).pack(pady=(0, 6))
        tk.Label(outer, text="Change Master Password",
                 font=("Georgia", 20, "bold"), bg=BG, fg=TEXT).pack()
        tk.Label(outer, text="Vault will lock after a successful change",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(pady=(4, 28))

        # Card
        card = tk.Frame(outer, bg=CARD, padx=40, pady=32,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(ipadx=10)

        # ── Current password ──
        tk.Label(card, text="Current Password", font=FONT_BODY,
                 bg=CARD, fg=SUBTEXT).grid(row=0, column=0, sticky="w", pady=(0, 4))

        cur_row = tk.Frame(card, bg=CARD)
        cur_row.grid(row=1, column=0, sticky="ew", pady=(0, 18))
        self._cur_var = tk.StringVar()
        self._cur_entry = _styled_entry(cur_row, textvariable=self._cur_var,
                                        show="●", width=30)
        self._cur_entry.pack(side="left")
        self._cur_show = tk.BooleanVar()
        eye = tk.Label(cur_row, text="👁", font=("Segoe UI Emoji", 13),
                       bg=CARD, fg=SUBTEXT, cursor="hand2", padx=8)
        eye.pack(side="left")
        eye.bind("<ButtonPress-1>",   lambda e: self._cur_entry.config(show=""))
        eye.bind("<ButtonRelease-1>", lambda e: self._cur_entry.config(show="●"))

        # ── New password ──
        tk.Label(card, text="New Password", font=FONT_BODY,
                 bg=CARD, fg=SUBTEXT).grid(row=2, column=0, sticky="w", pady=(0, 4))
        new_row = tk.Frame(card, bg=CARD)
        new_row.grid(row=3, column=0, sticky="ew", pady=(0, 18))
        self._new_var = tk.StringVar()
        self._new_entry = _styled_entry(new_row, textvariable=self._new_var,
                                        show="●", width=30)
        self._new_entry.pack(side="left")
        eye2 = tk.Label(new_row, text="👁", font=("Segoe UI Emoji", 13),
                        bg=CARD, fg=SUBTEXT, cursor="hand2", padx=8)
        eye2.pack(side="left")
        eye2.bind("<ButtonPress-1>",   lambda e: self._new_entry.config(show=""))
        eye2.bind("<ButtonRelease-1>", lambda e: self._new_entry.config(show="●"))

        # Strength bar
        self._strength_lbl = tk.Label(card, text="", font=FONT_SMALL,
                                       bg=CARD, fg=SUBTEXT)
        self._strength_lbl.grid(row=4, column=0, sticky="w", pady=(0, 4))
        self._strength_bar = tk.Frame(card, bg=BORDER, height=4)
        self._strength_bar.grid(row=5, column=0, sticky="ew", pady=(0, 18))
        self._strength_fill = tk.Frame(self._strength_bar, bg=BORDER, height=4)
        self._strength_fill.place(x=0, y=0, relheight=1, relwidth=0)
        self._new_var.trace("w", self._update_strength)

        # ── Confirm new password ──
        tk.Label(card, text="Confirm New Password", font=FONT_BODY,
                 bg=CARD, fg=SUBTEXT).grid(row=6, column=0, sticky="w", pady=(0, 4))
        conf_row = tk.Frame(card, bg=CARD)
        conf_row.grid(row=7, column=0, sticky="ew", pady=(0, 6))
        self._conf_var = tk.StringVar()
        self._conf_entry = _styled_entry(conf_row, textvariable=self._conf_var,
                                          show="●", width=30)
        self._conf_entry.pack(side="left")
        eye3 = tk.Label(conf_row, text="👁", font=("Segoe UI Emoji", 13),
                        bg=CARD, fg=SUBTEXT, cursor="hand2", padx=8)
        eye3.pack(side="left")
        eye3.bind("<ButtonPress-1>",   lambda e: self._conf_entry.config(show=""))
        eye3.bind("<ButtonRelease-1>", lambda e: self._conf_entry.config(show="●"))

        # Status label
        self._status = tk.Label(card, text="", font=("Segoe UI", 9),
                                 bg=CARD, fg=ERROR)
        self._status.grid(row=8, column=0, sticky="w", pady=(6, 0))

        # ── Buttons row ──
        btn_row = tk.Frame(card, bg=CARD)
        btn_row.grid(row=9, column=0, sticky="ew", pady=(20, 0))

        save_btn = tk.Button(btn_row, text="💾  Save Changes",
                             font=FONT_BTN, bg=ACCENT2, fg="white",
                             activebackground=ACCENT, activeforeground="white",
                             relief="flat", cursor="hand2", padx=20, pady=10,
                             command=self._do_change)
        save_btn.pack(side="left", padx=(0, 10))

        cancel_btn = tk.Button(btn_row, text="✕  Cancel",
                               font=FONT_BTN, bg=BORDER, fg=SUBTEXT,
                               activebackground=CARD2, activeforeground=TEXT,
                               relief="flat", cursor="hand2", padx=20, pady=10,
                               command=self.on_cancel)
        cancel_btn.pack(side="left")

        self._cur_entry.focus_set()

    def _update_strength(self, *_):
        pw = self._new_var.get()
        score = 0
        if len(pw) >= 8:  score += 1
        if len(pw) >= 12: score += 1
        if any(c.isupper() for c in pw): score += 1
        if any(c.isdigit() for c in pw): score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pw): score += 1

        colors = ["#ef4444", "#f97316", "#eab308", "#84cc16", "#10b981"]
        labels = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
        idx = max(0, score - 1) if pw else 0
        color = colors[idx] if pw else BORDER
        label = labels[idx] if pw else ""

        self._strength_fill.place(relwidth=score / 5 if pw else 0)
        self._strength_fill.config(bg=color)
        self._strength_lbl.config(text=f"Strength: {label}" if pw else "", fg=color)

    def _do_change(self):
        cur_pw  = self._cur_var.get()
        new_pw  = self._new_var.get()
        conf_pw = self._conf_var.get()

        if not cur_pw:
            self._set_status("Please enter your current password.")
            return

        test_key = storage.verify_and_unlock(cur_pw)
        if test_key is None:
            self._set_status("Current password is incorrect.")
            self._cur_var.set("")
            self._cur_entry.focus_set()
            return

        if len(new_pw) < 8:
            self._set_status("New password must be at least 8 characters.")
            return

        if new_pw != conf_pw:
            self._set_status("New passwords do not match.")
            self._conf_var.set("")
            self._conf_entry.focus_set()
            return

        if new_pw == cur_pw:
            self._set_status("New password must be different from current.")
            return

        try:
            storage.change_master_password(new_pw, self.vault_data, old_key=test_key)
            self._set_status("✓  Password changed! Locking vault…", ok=True)
            self.after(1400, self.on_success)
        except Exception as ex:
            self._set_status(f"Error: {ex}")

    def _set_status(self, msg, ok=False):
        self._status.config(text=msg, fg="#10b981" if ok else ERROR)


# ── Files Tab ──────────────────────────────────────────────────────────────────

import tempfile
import subprocess
import threading
import shutil

# File-type categories → (icon, label, opener)
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".ico", ".svg"}
VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg"}
AUDIO_EXTS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"}
PDF_EXTS   = {".pdf"}


def _get_file_type(filename: str):
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in PDF_EXTS:
        return "pdf"
    return "other"


def _type_icon(filename: str) -> str:
    t = _get_file_type(filename)
    return {"image": "🖼", "video": "🎬", "audio": "🎵", "pdf": "📄", "other": "📦"}[t]


def _type_badge_color(filename: str) -> str:
    t = _get_file_type(filename)
    return {"image": "#0ea5e9", "video": "#8b5cf6", "audio": "#f59e0b",
            "pdf":  "#ef4444", "other": "#6b7280"}[t]


# Temp dir for decrypted previews — cleaned on app exit
_PREVIEW_TMPDIR = tempfile.mkdtemp(prefix="vault_preview_")


def _cleanup_preview_dir():
    try:
        shutil.rmtree(_PREVIEW_TMPDIR, ignore_errors=True)
    except Exception:
        pass


import atexit
atexit.register(_cleanup_preview_dir)


def _open_with_app(filepath: str, filetype: str):
    """Open a file with the correct Windows application."""
    import sys
    if sys.platform != "win32":
        # Fallback for non-Windows (Linux/Mac)
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", filepath])
            else:
                subprocess.Popen(["xdg-open", filepath])
        except Exception:
            pass
        return

    ext = os.path.splitext(filepath)[1].lower()

    if filetype == "pdf":
        # Open with Chrome
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
        for cp in chrome_paths:
            if os.path.exists(cp):
                subprocess.Popen([cp, filepath])
                return
        # Chrome not found — fall back to default PDF handler
        os.startfile(filepath)

    elif filetype in ("video", "audio"):
        # Open with Windows Media Player
        wmp_paths = [
            r"C:\Program Files\Windows Media Player\wmplayer.exe",
            r"C:\Program Files (x86)\Windows Media Player\wmplayer.exe",
        ]
        for wp in wmp_paths:
            if os.path.exists(wp):
                subprocess.Popen([wp, filepath])
                return
        # WMP not found — try Movies & TV / Groove via shell
        os.startfile(filepath)

    elif filetype == "image":
        # Open with Windows Photos app via shell (handles Photos UWP correctly)
        os.startfile(filepath)

    else:
        # Generic: let Windows pick the default app
        os.startfile(filepath)


class FilesTab(tk.Frame):
    def __init__(self, master, vault_data, fernet_key, save_cb):
        super().__init__(master, bg=BG)
        self.vault_data = vault_data
        self.fernet_key = fernet_key
        self.save_cb = save_cb
        self._preview_files = {}   # stored_name → temp path (so we reuse same temp file)
        self._build()

    def _build(self):
        hdr = _section_header(self, "📁  Encrypted Files",
                               "Decrypt & open · AES-encrypted at rest")
        _styled_btn(hdr, "+ Import File", command=self._import_file).pack(side="right")

        # Legend row
        legend = tk.Frame(self, bg=BG)
        legend.pack(fill="x", padx=30, pady=(6, 0))
        for label, color in [("Image", "#0ea5e9"), ("Video", "#8b5cf6"),
                              ("Audio", "#f59e0b"), ("PDF", "#ef4444"), ("Other", "#6b7280")]:
            dot = tk.Label(legend, text="●", font=("Segoe UI", 9), bg=BG, fg=color)
            dot.pack(side="left")
            tk.Label(legend, text=label + "  ", font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(side="left")

        # Column headers
        col_f = tk.Frame(self, bg=BORDER)
        col_f.pack(fill="x", padx=30, pady=(10, 0))
        for col, w in [("Type", 6), ("Filename", 30), ("Size", 10), ("Actions", 22)]:
            tk.Label(col_f, text=col, font=("Segoe UI", 9, "bold"),
                     bg=BORDER, fg=SUBTEXT, width=w, anchor="w", padx=8, pady=6).pack(side="left")

        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, padx=30, pady=(2, 20))

        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        sb = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self._list_frame = tk.Frame(canvas, bg=BG)
        self._list_frame.bind("<Configure>",
                              lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self._list_frame, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._refresh()

    def _refresh(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        files = self.vault_data.get("files", [])
        if not files:
            tk.Label(self._list_frame,
                     text="No encrypted files yet.\nClick '+ Import File' to add one.",
                     font=FONT_BODY, bg=BG, fg=SUBTEXT, pady=30, justify="center").pack()
            return

        for idx, f in enumerate(files):
            name = f.get("original_name", "unknown")
            ftype = _get_file_type(name)
            icon  = _type_icon(name)
            badge = _type_badge_color(name)
            row_bg = ROW_ODD if idx % 2 == 0 else ROW_EVEN

            row = tk.Frame(self._list_frame, bg=row_bg)
            row.pack(fill="x")

            # Type badge
            tk.Label(row, text=icon, font=("Segoe UI Emoji", 14),
                     bg=row_bg, fg=badge, width=6, padx=4, pady=8).pack(side="left")

            # Filename
            tk.Label(row, text=name, font=FONT_BODY,
                     bg=row_bg, fg=TEXT, width=30, anchor="w", padx=6).pack(side="left")

            # Size
            tk.Label(row, text=self._fmt_size(f.get("size", 0)),
                     font=FONT_MONO, bg=row_bg, fg=SUBTEXT, width=10, anchor="w").pack(side="left")

            # Action buttons
            act = tk.Frame(row, bg=row_bg)
            act.pack(side="left", padx=4)

            # ▶ Open button (decrypt → temp file → launch app)
            open_btn = tk.Button(act, text="▶  Open", font=FONT_BTN,
                                 bg=badge, fg="white", activebackground=ACCENT2,
                                 activeforeground="white", relief="flat", cursor="hand2",
                                 padx=10, pady=4,
                                 command=lambda i=idx: self._open_file(i))
            open_btn.pack(side="left", padx=(0, 4))

            # ⬇ Export button
            tk.Button(act, text="⬇", font=FONT_BTN, bg=CARD, fg=ACCENT3,
                      activebackground=CARD2, activeforeground=ACCENT3,
                      relief="flat", cursor="hand2", padx=8, pady=4,
                      command=lambda i=idx: self._export(i)).pack(side="left", padx=(0, 4))

            # 🗑 Delete
            tk.Button(act, text="🗑", font=("Segoe UI Emoji", 12),
                      bg=row_bg, fg=ERROR, relief="flat", cursor="hand2",
                      command=lambda i=idx: self._delete(i)).pack(side="left")

    # ── Open file ──────────────────────────────────────────────────────────────
    def _open_file(self, idx):
        f = self.vault_data["files"][idx]
        name = f.get("original_name", "file")
        stored = f["stored_name"]
        ftype = _get_file_type(name)

        # Reuse existing temp file if already decrypted this session
        if stored in self._preview_files and os.path.exists(self._preview_files[stored]):
            tmp_path = self._preview_files[stored]
            _open_with_app(tmp_path, ftype)
            return

        # Decrypt to a named temp file preserving the original extension
        ext = os.path.splitext(name)[1]
        try:
            data = storage.get_encrypted_file(stored, self.fernet_key)
        except Exception as ex:
            messagebox.showerror("Decryption Error", str(ex))
            return

        # Write to temp file with original filename so apps recognise it
        tmp_path = os.path.join(_PREVIEW_TMPDIR, stored + ext)
        with open(tmp_path, "wb") as fh:
            fh.write(data)

        self._preview_files[stored] = tmp_path

        # Launch in background thread so UI doesn't freeze
        threading.Thread(target=_open_with_app, args=(tmp_path, ftype), daemon=True).start()

    # ── Helpers ────────────────────────────────────────────────────────────────
    def _fmt_size(self, n):
        if n < 1024:      return f"{n} B"
        elif n < 1024**2: return f"{n/1024:.1f} KB"
        else:             return f"{n/1024**2:.1f} MB"

    def _import_file(self):
        path = filedialog.askopenfilename(title="Select a file to encrypt")
        if not path:
            return
        with open(path, "rb") as fh:
            data = fh.read()
        if len(data) > 100 * 1024 * 1024:
            messagebox.showerror("Error", "File too large (max 100 MB).")
            return
        stored_name = storage.add_encrypted_file(os.path.basename(path), data, self.fernet_key)
        self.vault_data.setdefault("files", []).append({
            "original_name": os.path.basename(path),
            "stored_name": stored_name,
            "size": len(data),
        })
        self.save_cb()
        self._refresh()

    def _export(self, idx):
        f = self.vault_data["files"][idx]
        save_path = filedialog.asksaveasfilename(
            title="Export file", initialfile=f.get("original_name", "file"))
        if not save_path:
            return
        try:
            data = storage.get_encrypted_file(f["stored_name"], self.fernet_key)
            with open(save_path, "wb") as fh:
                fh.write(data)
            messagebox.showinfo("Exported", f"File saved to:\n{save_path}")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _delete(self, idx):
        if messagebox.askyesno("Delete", "Permanently delete this encrypted file?"):
            f = self.vault_data["files"][idx]
            stored = f["stored_name"]
            storage.delete_encrypted_file(stored)
            # Clean up temp preview if exists
            if stored in self._preview_files:
                try:
                    os.remove(self._preview_files[stored])
                except Exception:
                    pass
                del self._preview_files[stored]
            self.vault_data["files"].pop(idx)
            self.save_cb()
            self._refresh()
