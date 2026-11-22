"""設定画面"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .config import get_password, is_email, save_config, set_password
from .constants import APP_TITLE, FONT
from .i18n import set_language, t, wrap_ok
from .sound import open_app_volume


def open_settings(app) -> None:
    """設定画面を開く（すでに開いていれば前に出す）。app は Widget"""
    if getattr(app, "_settings_win", None) and app._settings_win.winfo_exists():
        app._settings_win.deiconify()
        app._settings_win.lift()
        return
    win = tk.Toplevel(app.root)
    app._settings_win = win
    win.title(f"{app._title()} - {t('settings_title')}")
    win.attributes("-topmost", True)
    win.resizable(False, False)
    frm = ttk.Frame(win, padding=16)
    frm.pack(fill="both", expand=True)

    lang_names = {"auto": t("lang_auto"), "ja": "日本語", "en": "English"}
    cur_lang = app.cfg.get("language", "auto")
    vars_ = {
        "username": tk.StringVar(value=app.cfg["username"]),
        "display_name": tk.StringVar(value=app.cfg.get("display_name", "")),
        "password": tk.StringVar(value=""),
        "region": tk.StringVar(value=app.cfg["region"]),
        "alert_low": tk.StringVar(value=str(app.cfg["alert_low"])),
        "alert_high": tk.StringVar(value=str(app.cfg["alert_high"])),
        "repeat_minutes": tk.StringVar(value=str(app.cfg["repeat_minutes"])),
        "alert_enabled": tk.BooleanVar(value=bool(app.cfg["alert_enabled"])),
        "alert_on_rapid": tk.BooleanVar(value=bool(app.cfg["alert_on_rapid"])),
        "toast_enabled": tk.BooleanVar(value=bool(app.cfg.get("toast_enabled", True))),
        "language": tk.StringVar(value=lang_names.get(cur_lang, lang_names["auto"])),
    }

    row = 0

    def add(label, widget):
        nonlocal row
        lbl = ttk.Label(frm, text=label)
        lbl.grid(row=row, column=0, sticky="w", pady=3, padx=(0, 10))
        widget.grid(row=row, column=1, sticky="we", pady=3)
        row += 1
        return lbl

    def section(text):
        nonlocal row
        ttk.Separator(frm).grid(row=row, column=0, columnspan=2, sticky="we", pady=8)
        row += 1
        ttk.Label(frm, text=text, font=(FONT, 10, "bold")).grid(row=row, column=0, columnspan=2,
                                                              sticky="w")
        row += 1

    # 注意書き
    note = tk.Frame(frm, bg="#fff4e5", highlightbackground="#f0b45a", highlightthickness=1)
    note.grid(row=row, column=0, columnspan=2, sticky="we", pady=(0, 6))
    tk.Label(note, text=t("disclaimer_title"), font=(FONT, 10, "bold"), bg="#fff4e5",
             fg="#8a4b00").pack(anchor="w", padx=8, pady=(6, 0))
    tk.Label(note, text=wrap_ok(t("disclaimer")), font=(FONT, 9), bg="#fff4e5", fg="#3d2a10",
             justify="left", wraplength=430).pack(anchor="w", padx=8, pady=(2, 6))
    row += 1

    if app.demo:  # --demo 起動時だけ表示（設定からは切り替えられない）
        ttk.Label(frm, text=wrap_ok(t("demo_running")), foreground="#8a4b00", wraplength=430,
                  justify="left").grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 0))
        row += 1

    section(t("sec_account"))
    account_widgets = []
    # ログインIDはメールアドレスのみ。ID・パスワードは半角英数記号だけ入力できる
    # （全角を入力できるのは表示名だけ）
    def ok_id(proposed):
        return all("!" <= ch <= "~" for ch in proposed)

    def ok_pw(proposed):
        return all(" " <= ch <= "~" for ch in proposed)
    saved_id = app.cfg["username"] if is_email(app.cfg["username"]) else ""
    vars_["username"].set(saved_id)  # 以前の版のユーザー名・電話番号などは出さない
    e_user = ttk.Entry(frm, textvariable=vars_["username"], width=28,
                       validate="key", validatecommand=(win.register(ok_id), "%P"))
    add(t("email"), e_user)
    pw_label = t("pw_saved") if saved_id and get_password(saved_id) else t("password")
    e_pw = ttk.Entry(frm, textvariable=vars_["password"], show="●", width=28,
                     validate="key", validatecommand=(win.register(ok_pw), "%P"))
    add(pw_label, e_pw)
    e_name = ttk.Entry(frm, textvariable=vars_["display_name"], width=28)
    add(t("display_name"), e_name)
    e_region = ttk.Combobox(frm, textvariable=vars_["region"], values=["jp", "ous", "us"],
                            state="readonly", width=8)
    add(t("region"), e_region)
    account_widgets += [e_user, e_pw, e_name, e_region]

    if app.demo:
        for w in account_widgets:
            w.state(["disabled"])

    section(t("sec_alert"))
    add("", ttk.Checkbutton(frm, text=t("alert_enabled"), variable=vars_["alert_enabled"]))
    add(t("alert_low"), ttk.Spinbox(frm, from_=40, to=150, increment=5,
                                    textvariable=vars_["alert_low"], width=8))
    add(t("alert_high"), ttk.Spinbox(frm, from_=120, to=400, increment=10,
                                     textvariable=vars_["alert_high"], width=8))
    add("", ttk.Checkbutton(frm, text=t("alert_rapid"), variable=vars_["alert_on_rapid"]))
    add(t("repeat"), ttk.Spinbox(frm, from_=5, to=120, increment=5,
                                 textvariable=vars_["repeat_minutes"], width=8))
    add("", ttk.Checkbutton(frm, text=t("toast"), variable=vars_["toast_enabled"]))
    ttk.Label(frm, text=wrap_ok(t("toast_hint")), foreground="#555555", wraplength=430,
              justify="left").grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 4))
    row += 1
    # 音量スライダー：音量ミキサーの「このアプリの音量」と双方向に連動（0〜100%）
    appvol = open_app_volume()
    vol_row = ttk.Frame(frm)
    vol_pct = ttk.Label(vol_row, width=8, anchor="e")
    vol_state = {"busy": False, "drag": False}

    def show_volume(v, muted):
        vol_pct.config(text=t("volume_muted") if muted else f"{v}%",
                       foreground="#c25700" if muted or v == 0 else "")

    def on_volume(_=None):
        if vol_state["busy"] or appvol is None:
            return
        v = int(round(float(vol_scale.get())))
        try:
            appvol.set(v)
        except OSError:
            pass
        show_volume(v, False)
    vol_scale = ttk.Scale(vol_row, from_=0, to=100, orient="horizontal", length=220,
                          command=on_volume)
    vol_scale.pack(side="left", fill="x", expand=True)
    vol_pct.pack(side="left", padx=(6, 0))
    vol_scale.bind("<ButtonPress-1>", lambda e: vol_state.update(drag=True))
    vol_scale.bind("<ButtonRelease-1>", lambda e: vol_state.update(drag=False))

    def sync_volume():
        # 音量ミキサー側で変えられた値をスライダーに反映（設定画面を開いている間）
        if not win.winfo_exists():
            return
        if not vol_state["drag"]:
            try:
                v, muted = appvol.get()
            except OSError:
                return
            if abs(float(vol_scale.get()) - v) >= 0.5 or vol_pct.cget("text") != (
                    t("volume_muted") if muted else f"{v}%"):
                vol_state["busy"] = True
                vol_scale.set(v)
                vol_state["busy"] = False
                show_volume(v, muted)
        win.after(400, sync_volume)

    if appvol is None:
        vol_scale.state(["disabled"])
        vol_pct.config(text="--")
    else:
        win.bind("<Destroy>", lambda e: appvol.close() if e.widget is win else None, add="+")
        sync_volume()
    add(t("volume"), vol_row)
    tests = ttk.Frame(frm)
    tests.grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 0))
    row += 1

    def test(kind):
        app.alarm.play(kind, 1)
    ttk.Button(tests, text=t("test_low"), command=lambda: test("low")).pack(side="left")
    ttk.Button(tests, text=t("test_high"), command=lambda: test("high")).pack(side="left", padx=4)
    ttk.Button(tests, text=t("test_rapid"), command=lambda: test("rapid")).pack(side="left")
    if app.demo:  # 通知テストはデモ（--demo）のときだけ
        ttk.Button(tests, text=t("test_toast"),
                   command=lambda: app._notify(t("toast_test"))).pack(side="left", padx=4)
    if appvol is None:  # 音量を読めない時だけ理由を出す
        ttk.Label(frm, text=wrap_ok(t("volume_na")), foreground="#555555", wraplength=430,
                  justify="left").grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 0))
        row += 1

    section(t("sec_general"))
    add(t("language"), ttk.Combobox(frm, textvariable=vars_["language"],
                                    values=list(lang_names.values()), state="readonly", width=24))

    btns = ttk.Frame(frm)
    btns.grid(row=row, column=0, columnspan=2, sticky="e", pady=(12, 0))

    def on_save():
        try:
            low = int(vars_["alert_low"].get())
            high = int(vars_["alert_high"].get())
            rep = int(vars_["repeat_minutes"].get())
        except ValueError:
            messagebox.showerror(APP_TITLE, t("err_number"), parent=win)
            return
        if low >= high:
            messagebox.showerror(APP_TITLE, t("err_lowhigh"), parent=win)
            return
        demo = app.demo
        user = vars_["username"].get().strip()
        pw = vars_["password"].get()
        if not demo:
            if not user:
                messagebox.showerror(APP_TITLE, t("err_email_empty"), parent=win)
                return
            if not is_email(user):
                messagebox.showerror(APP_TITLE, t("err_email"), parent=win)
                return
            if not pw and not get_password(user):
                messagebox.showerror(APP_TITLE, t("err_pw"), parent=win)
                return
        else:
            user = app.cfg["username"]  # デモ中はアカウント欄を使わない
        if pw and user:
            try:
                set_password(user, pw)
            except Exception as e:
                messagebox.showerror(APP_TITLE, t("err_pw_save", e=e), parent=win)
                return
        lang = next((k for k, v in lang_names.items() if v == vars_["language"].get()), "auto")
        account_changed = (bool(pw) or user != app.cfg["username"]
                           or vars_["region"].get() != app.cfg["region"]
                           or app.fetcher.auth_blocked is not None)
        app.cfg.update({
            "username": user, "region": vars_["region"].get(),
            "display_name": vars_["display_name"].get().strip(),
            "alert_low": low, "alert_high": high, "repeat_minutes": max(1, rep),
            "alert_enabled": vars_["alert_enabled"].get(),
            "alert_on_rapid": vars_["alert_on_rapid"].get(),
            "toast_enabled": vars_["toast_enabled"].get(),
            "language": lang,
        })
        save_config(app.cfg)
        app.last_alert_key = None
        if account_changed and not demo:
            app.readings = []
            app.last_reading_time = None
            app.error_text = ""
            app._got_data = False
            app.fetcher.refresh(reset=True)
        set_language(lang)
        app.root.title(app._title())
        app._tray_sig = None
        win.destroy()
        app._build()
        app._reposition()

    ttk.Button(btns, text=t("save"), command=on_save).pack(side="left")
    ttk.Button(btns, text=t("cancel"), command=win.destroy).pack(side="left", padx=4)
    frm.columnconfigure(1, weight=1)
