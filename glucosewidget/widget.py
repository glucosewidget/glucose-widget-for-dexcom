"""本体ウィンドウ（現在値の表示・メニュー・ドラッグ・アラート判定）"""
from __future__ import annotations

import queue
import time
from datetime import datetime, timezone

import tkinter as tk
from tkinter import messagebox

from .config import load_config, mask_id, save_config
from .constants import (ACCENT, APP_TITLE, BG, BORDER, BTN_BG, FG, FONT, GRAPH_H_MIN, GRAPH_W,
                        GRAY, GREEN, ORANGE, RANGES, RED, RED_BELOW, SCALES, SUB, YELLOW,
                        Reading)
from .fetcher import Fetcher
from .graph import GraphMixin
from .i18n import RAPID, set_language, t, trend_text
from .notify import register_toast_app, show_toast
from .settings_dialog import open_settings
from .sound import Alarm
from .startup import set_startup, startup_registered
from .tray import TRAY_AVAILABLE, TrayMixin


class Widget(GraphMixin, TrayMixin):
    def __init__(self, force_demo: bool = False):
        self.cfg = load_config()
        set_language(self.cfg.get("language", "auto"))
        self.force_demo = force_demo
        self.demo = force_demo  # デモは --demo 起動時のみ
        self.q: queue.Queue = queue.Queue()
        self.alarm = Alarm()
        self.readings: list[Reading] = []
        self.last_alert_key = None   # 同じ状態で何度も鳴らさないため
        self.last_alert_time = 0.0
        self.last_reading_time = None
        self.error_text = ""
        self.body = None
        self.menu = None
        self.tray = None
        self.tray_ok = TRAY_AVAILABLE
        self.visible = True
        self._tray_sig = None
        self._tray_img_key = None
        self._got_data = False       # 一度でも取得に成功したか（「接続中…」表示の判定）
        self.ok = True

        self.root = tk.Tk()
        self.root.title(self._title())
        self.root.overrideredirect(True)            # 枠なし・タスクバー非表示
        self.root.configure(bg=BORDER)
        self.root.attributes("-topmost", bool(self.cfg["topmost"]))
        self.root.attributes("-alpha", float(self.cfg["alpha"]))

        # ルート（トップレベル）に束ねると子ウィジェット全部に効く
        self.root.bind("<ButtonPress-1>", self._drag_start)
        self.root.bind("<B1-Motion>", self._drag_move)
        self.root.bind("<ButtonRelease-1>", self._drag_end)
        self.root.bind("<Button-3>", self._menu_popup)
        self.root.bind("<Double-Button-1>", lambda e: self.refresh_now())
        self.root.bind("<Unmap>", self._on_unmap)

        self._build()
        self._reposition()

        # 初回（未確認のとき）は注意書き。同意しなければ終了
        if not self.cfg.get("disclaimer_ok"):
            self.root.update()
            msg = f"{t('disclaimer')}\n\n{t('disclaimer_ask')}"
            if not messagebox.askokcancel(f"{APP_TITLE} - {t('disclaimer_title')}", msg,
                                          icon="warning", parent=self.root):
                self.ok = False
                self.root.destroy()
                return
            self.cfg["disclaimer_ok"] = True
            save_config(self.cfg)

        self._start_tray()
        register_toast_app()
        if startup_registered():  # exe の名前や場所が変わっても自動起動が切れないように
            try:
                set_startup(True)
            except OSError:
                pass
        self.fetcher = Fetcher(self.cfg, self.q, self.demo)
        self.fetcher.start()
        self.root.after(200, self._poll_queue)
        self.root.after(1000, self._tick)

    def _title(self) -> str:
        return f"{APP_TITLE} [DEMO]" if self.demo else APP_TITLE

    # ---------- サイズ倍率
    @property
    def s(self) -> float:
        return SCALES.get(self.cfg.get("scale"), 1.0)

    def _f(self, size, *style, family=FONT):
        return (family, max(6, round(size * self.s)), *style)

    def _px(self, n) -> int:
        return max(1, round(n * self.s))

    # ---------- レイアウト
    def _reposition(self):
        """右端を固定したまま、中身の大きさに合わせてウィンドウ位置を決める"""
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        right, y = self.cfg.get("right"), self.cfg.get("y")
        if right is None:
            right = self.root.winfo_screenwidth() - 24
        if y is None:
            y = 24
        self.root.geometry(f"+{int(right) - w}+{int(y)}")

    def _build(self):
        """表示サイズ変更・グラフ切替・言語切替のたびに作り直す"""
        if self.body is not None:
            self.body.destroy()
        self.body = tk.Frame(self.root, bg=BG)
        self.body.pack(fill="both", expand=True, padx=2, pady=2)  # 外周2pxが枠（アラート時に点滅）

        # --- 右側：現在値パネル
        panel = tk.Frame(self.body, bg=BG, padx=self._px(14), pady=self._px(8))
        panel.grid(row=0, column=1, sticky="ns")

        head = tk.Frame(panel, bg=BG)
        head.pack(fill="x")
        self.lbl_name = tk.Label(head, text="", font=self._f(9), fg=SUB, bg=BG)
        self.lbl_name.pack(side="left")
        if self.demo:  # デモ中は常に表示
            tk.Label(head, text="DEMO", font=self._f(8, "bold"), fg="#000000", bg=ORANGE,
                     padx=self._px(4)).pack(side="left", padx=(self._px(6), 0))
        if self.tray_ok:  # 最小化（トレイに格納）ボタン
            btn = tk.Label(head, text="–", font=self._f(11, "bold"), fg=SUB, bg=BG,
                           cursor="hand2", padx=self._px(2))
            btn.pack(side="right", padx=(self._px(10), 0))
            btn.bind("<ButtonPress-1>", lambda e: "break")
            btn.bind("<ButtonRelease-1>", lambda e: (self.hide_window(), "break")[1])
            btn.bind("<Double-Button-1>", lambda e: "break")

        top = tk.Frame(panel, bg=BG)
        top.pack(anchor="w")
        self.lbl_value = tk.Label(top, text="---", font=self._f(34, "bold"), fg=FG, bg=BG)
        self.lbl_value.pack(side="left")
        self.lbl_arrow = tk.Label(top, text="", font=self._f(26, "bold", family="Segoe UI Symbol"),
                                  fg=FG, bg=BG)
        self.lbl_arrow.pack(side="left", padx=(self._px(8), 0), pady=(self._px(4), 0))
        self.lbl_unit = tk.Label(top, text="mg/dL", font=self._f(9), fg=SUB, bg=BG)
        self.lbl_unit.pack(side="left", padx=(self._px(6), 0), pady=(self._px(18), 0))

        self.lbl_trend = tk.Label(panel, text=t("connecting"), font=self._f(12, "bold"), fg=FG, bg=BG)
        self.lbl_trend.pack(anchor="w")
        self.lbl_info = tk.Label(panel, text="", font=self._f(10), fg=SUB, bg=BG)
        self.lbl_info.pack(anchor="w")
        self.lbl_warn = tk.Label(panel, text="", font=self._f(10, "bold"), fg=ORANGE, bg=BG,
                                 justify="left", anchor="w")

        # --- 左側：推移グラフ（表示時のみ）
        self.canvas = None
        if self.cfg.get("show_graph"):
            gframe = tk.Frame(self.body, bg=BG, padx=self._px(8), pady=self._px(6))
            gframe.grid(row=0, column=0, sticky="nsew")
            tk.Frame(self.body, bg=BORDER, width=1).grid(row=0, column=0, sticky="nse")
            self.body.grid_columnconfigure(0, weight=1)
            self.body.grid_rowconfigure(0, weight=1)

            bar = tk.Frame(gframe, bg=BG)
            bar.pack(anchor="w", fill="x")
            self.range_btns = {}
            for h in RANGES:
                b = tk.Label(bar, text=f"{h}h", font=self._f(9, "bold"), bg=BG, cursor="hand2",
                             padx=self._px(7), pady=self._px(1))
                b.pack(side="left", padx=(0, self._px(3)))
                b.bind("<Button-1>", lambda e, h=h: self._set_range(h))
                self.range_btns[h] = b
            self._paint_range_btns()

            self.canvas = tk.Canvas(gframe, bg=BG, highlightthickness=0,
                                    width=self._px(GRAPH_W), height=self._px(GRAPH_H_MIN))
            self.canvas.pack(fill="both", expand=True, pady=(self._px(4), 0))
            self.canvas.bind("<Configure>", lambda e: self._draw_graph())
            self.canvas.bind("<Motion>", self._on_hover)
            self.canvas.bind("<Leave>", lambda e: self.canvas.delete("hover"))

        self._render()

    # ---------- メニュー（ウィンドウ右クリックとトレイで同じ内容）
    def _menu_spec(self) -> list:
        spec = [
            ("cmd", t("menu_refresh"), self.refresh_now),
            ("sep",),
            ("check", t("menu_graph"), lambda: bool(self.cfg.get("show_graph")), self._toggle_graph),
            ("sub", t("menu_size"), [
                ("radio", t(f"size_{n}"), (lambda n=n: self.cfg.get("scale") == n),
                 (lambda n=n: self._change_scale(n))) for n in SCALES]),
            ("sep",),
            ("cmd", t("menu_settings"), self.open_settings),
            ("check", t("menu_topmost"), lambda: bool(self.cfg["topmost"]), self._toggle_topmost),
            ("check", t("menu_startup"), startup_registered, self._toggle_startup),
        ]
        if self.demo:
            spec.append(("sub", t("menu_demo"), [
                ("cmd", t("demo_low"), lambda: self._demo_simulate("low")),
                ("cmd", t("demo_high"), lambda: self._demo_simulate("high")),
                ("cmd", t("demo_rapid"), lambda: self._demo_simulate("rapid")),
            ]))
        spec.append(("sep",))
        if self.tray_ok:
            spec.append(("cmd", t("menu_hide") if self.visible else t("menu_show"),
                         self.toggle_window, True))  # True = トレイ左クリックの既定動作
        spec.append(("cmd", t("menu_quit"), self.quit))
        return spec

    def _do(self, fn):
        fn()
        self._tray_refresh()

    def _to_tk(self, menu: tk.Menu, spec: list):
        for it in spec:
            kind = it[0]
            if kind == "sep":
                menu.add_separator()
            elif kind == "cmd":
                menu.add_command(label=it[1], command=lambda f=it[2]: self._do(f))
            elif kind in ("check", "radio"):
                var = tk.BooleanVar(master=menu, value=bool(it[2]()))
                self._menu_vars.append(var)
                add = menu.add_checkbutton if kind == "check" else menu.add_radiobutton
                opts = {} if kind == "check" else {"value": True}
                add(label=it[1], variable=var, command=lambda f=it[3]: self._do(f), **opts)
            elif kind == "sub":
                sub = tk.Menu(menu, tearoff=0)
                self._to_tk(sub, it[2])
                menu.add_cascade(label=it[1], menu=sub)

    def _menu_popup(self, e):
        if self.menu is not None:
            self.menu.destroy()
        self._menu_vars = []
        self.menu = tk.Menu(self.root, tearoff=0)
        self._to_tk(self.menu, self._menu_spec())
        self.menu.tk_popup(e.x_root, e.y_root)

    def refresh_now(self):
        self.fetcher.refresh()

    def _toggle_graph(self):
        self.cfg["show_graph"] = not self.cfg.get("show_graph")
        save_config(self.cfg)
        self._build()
        self._reposition()

    def _change_scale(self, name):
        self.cfg["scale"] = name
        save_config(self.cfg)
        self._build()
        self._reposition()

    def _set_range(self, hours):
        self.cfg["graph_hours"] = hours
        save_config(self.cfg)
        self._paint_range_btns()
        self._draw_graph()

    def _paint_range_btns(self):
        cur = self.cfg.get("graph_hours", 6)
        for h, b in self.range_btns.items():
            if h == cur:
                b.config(bg=ACCENT, fg="#ffffff")
            else:
                b.config(bg=BTN_BG, fg=SUB)

    def _toggle_topmost(self):
        self.cfg["topmost"] = not self.cfg["topmost"]
        self.root.attributes("-topmost", self.cfg["topmost"])
        save_config(self.cfg)

    def _toggle_startup(self):
        try:
            set_startup(not startup_registered())
        except OSError as e:
            messagebox.showerror(APP_TITLE, t("err_startup", e=e))

    def _demo_simulate(self, kind):
        if self.demo:
            self.fetcher.demo_src.simulate(kind)
            self.fetcher.refresh()

    # ---------- ウィンドウの表示/非表示（トレイ格納）
    def hide_window(self):
        if not self.tray_ok:
            return
        self.root.withdraw()
        self.visible = False
        self._tray_refresh()

    def show_window(self):
        self.root.deiconify()
        self.root.attributes("-topmost", bool(self.cfg["topmost"]))
        self.root.lift()
        self.visible = True
        self._reposition()
        self._tray_refresh()

    def toggle_window(self):
        if self.visible:
            self.hide_window()
        else:
            self.show_window()

    def _on_unmap(self, e):
        # 何らかの方法で最小化されたら、隠してトレイに格納する
        if e.widget is self.root and self.tray_ok and self.root.state() == "iconic":
            self.root.after(0, self.hide_window)

    # ---------- ドラッグ
    def _drag_start(self, e):
        self._dx, self._dy = e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y()
        self._moved = False
        if self.alarm.active:  # 鳴っている時はクリックで止める
            self._stop_alarm()

    def _drag_move(self, e):
        self._moved = True
        self.root.geometry(f"+{e.x_root - self._dx}+{e.y_root - self._dy}")

    def _drag_end(self, _e):
        if getattr(self, "_moved", False):
            self.cfg["right"] = self.root.winfo_x() + self.root.winfo_width()
            self.cfg["y"] = self.root.winfo_y()
            save_config(self.cfg)

    def _value_color(self, v):
        if v < RED_BELOW:
            return RED
        if v <= int(self.cfg["alert_low"]):
            return ORANGE
        if v >= int(self.cfg["alert_high"]):
            return YELLOW
        return GREEN

    def _display_name(self) -> str:
        if self.demo:
            return t("demo_name")
        name = (self.cfg.get("display_name") or "").strip()
        if name:
            return name
        return mask_id(self.cfg.get("username", ""))

    def _stop_alarm(self):
        self.alarm.stop()
        self.root.configure(bg=BORDER)

    # ---------- データ受信
    def _poll_queue(self):
        self.root.after(200, self._poll_queue)
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "ui":
                    payload()
                elif kind == "data":
                    self.error_text = ""
                    self._on_readings(payload)
                elif kind == "need_setup":
                    if self.demo:
                        continue
                    self.lbl_trend.config(text=t("setup_hint"), fg=YELLOW)
                    if not getattr(self, "_setup_shown", False):
                        self._setup_shown = True
                        self.open_settings()
                elif kind == "auth_error":
                    self.error_text = t(payload)
                    self._render()
                elif kind == "error":
                    self.error_text = t("err_net")
                    self._render()
        except queue.Empty:
            pass

    def _tick(self):
        self._render()  # 「○分前」表示と古いデータ判定を更新
        self.root.after(15000, self._tick)

    def _on_readings(self, readings):
        self._got_data = True
        self.readings = readings  # 新しい順
        latest = readings[0] if readings else None
        new_reading = latest is not None and latest.datetime != self.last_reading_time
        if latest is not None:
            self.last_reading_time = latest.datetime
        self._render()
        if new_reading:
            self._check_alert(latest)

    # ---------- 表示
    def _status(self, r: Reading):
        """(文字色, 古いか, 経過分, 経過の文言)"""
        age_min = (datetime.now(timezone.utc) - r.datetime).total_seconds() / 60
        stale = age_min >= float(self.cfg["stale_minutes"])
        v = r.value
        if v < RED_BELOW:      # 50未満は古いデータでも赤のまま
            color = RED
        elif stale:
            color = GRAY
        elif v <= int(self.cfg["alert_low"]):
            color = ORANGE
        elif v >= int(self.cfg["alert_high"]):
            color = YELLOW
        else:
            color = FG
        age = t("just_now") if age_min < 1 else t("min_ago", n=int(age_min))
        return color, stale, age_min, age

    def _render(self):
        self._render_panel()
        # 文字の長さで幅が変わったら、右端を固定したまま位置を合わせ直す
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        if w != getattr(self, "_last_w", None):
            self._last_w = w
            self._reposition()
        self._tray_refresh()

    def _render_panel(self):
        self.lbl_name.config(text=self._display_name())
        if self.canvas is not None:
            self._draw_graph()
        latest = self.readings[0] if self.readings else None
        if latest is None:
            self.lbl_value.config(text="---", fg=GRAY)
            self.lbl_arrow.config(text="")
            self.lbl_trend.config(text=t("no_data") if self._got_data else t("connecting"), fg=SUB)
            self.lbl_info.config(text="")
            self._set_warn(f"⚠ {self.error_text}" if self.error_text else "")
            return

        v = latest.value
        arrow, label = trend_text(latest.trend_direction)
        color, stale, age_min, age = self._status(latest)

        trend_color = color if latest.trend_direction in RAPID and not stale else (GRAY if stale else FG)
        self.lbl_value.config(text=str(v), fg=color)
        self.lbl_arrow.config(text=arrow, fg=trend_color)
        self.lbl_trend.config(text=label, fg=trend_color)

        # 前回値との差
        delta = ""
        if len(self.readings) >= 2:
            prev = self.readings[1]
            gap = (latest.datetime - prev.datetime).total_seconds() / 60
            if gap <= 11:
                delta = t("delta", d=v - prev.value)
        hm = latest.datetime.astimezone().strftime('%H:%M')
        self.lbl_info.config(text=t("info", time=hm, age=age) + delta)
        warns = []
        if stale:
            warns.append(t("stale", age=age))
        if self.error_text:
            warns.append(f"⚠ {self.error_text}")
        self._set_warn("\n".join(warns))

    def _set_warn(self, text: str):
        if text:
            self.lbl_warn.config(text=text, wraplength=self.root.winfo_fpixels("3i"))
            if not self.lbl_warn.winfo_ismapped():
                self.lbl_warn.pack(anchor="w", pady=(2, 0))
        else:
            self.lbl_warn.config(text="")
            self.lbl_warn.pack_forget()

    def _notify(self, message: str) -> None:
        """トースト通知。出せなかった時はトレイアイコンのバルーン通知で代用"""
        def balloon():
            if self.tray is not None:
                try:
                    self.tray.notify(message, self._title())
                except Exception:
                    pass
        show_toast(self._title(), message, fallback=balloon)

    # ---------- アラート判定
    def _check_alert(self, r):
        if not self.cfg["alert_enabled"]:
            return
        age_min = (datetime.now(timezone.utc) - r.datetime).total_seconds() / 60
        if age_min >= float(self.cfg["stale_minutes"]):
            return

        v = r.value
        if v <= int(self.cfg["alert_low"]):
            key = "low"
        elif v >= int(self.cfg["alert_high"]):
            key = "high"
        elif self.cfg["alert_on_rapid"] and r.trend_direction in RAPID:
            key = "rapid"
        else:
            self.last_alert_key = None  # 範囲内に戻ったらリセット
            return

        now = time.time()
        repeat = float(self.cfg["repeat_minutes"]) * 60
        if key != self.last_alert_key or now - self.last_alert_time >= repeat:
            self.last_alert_key = key
            self.last_alert_time = now
            self.alarm.play(key)  # パターン3回で自動停止
            self._flash(60)
            if self.cfg.get("toast_enabled"):
                arrow, label = trend_text(r.trend_direction)
                hm = r.datetime.astimezone().strftime('%H:%M')
                self._notify(t(f"toast_{key}", v=v, arrow=arrow, label=label, time=hm))

    def _flash(self, n):
        if n <= 0 or not self.alarm.active:
            self.root.configure(bg=BORDER)
            return
        self.root.configure(bg=RED if n % 2 else BORDER)
        self.root.after(500, self._flash, n - 1)

    def open_settings(self):
        open_settings(self)

    def quit(self):
        self.alarm.stop()
        self.fetcher.stopped = True
        if self.tray is not None:
            try:
                self.tray.stop()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        if self.ok:
            self.root.mainloop()
