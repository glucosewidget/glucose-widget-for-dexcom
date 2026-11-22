"""タスクトレイ（アイコン画像・メニュー・ツールチップ。Widget に混ぜて使う）"""
from __future__ import annotations

try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # 無くても動く（トレイ機能なし）
    pystray = None

from . import i18n
from .constants import APP, BTN_BG, FG, GRAY, GREEN, ORANGE, RED, YELLOW
from .i18n import t, trend_text
from .startup import startup_registered

TRAY_AVAILABLE = pystray is not None


# ---------------------------------------------------------------- トレイアイコン画像
_FONT_CACHE: dict[int, object] = {}


def _tray_font(size: int):
    if size not in _FONT_CACHE:
        font = None
        for name in ("segoeuib.ttf", "seguisb.ttf", "arialbd.ttf", "arial.ttf"):
            try:
                font = ImageFont.truetype(name, size)
                break
            except OSError:
                continue
        _FONT_CACHE[size] = font or ImageFont.load_default()
    return _FONT_CACHE[size]


def make_tray_image(text: str, bg: str, fg: str):
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=12, fill=bg)
    fs = 46
    while fs > 12:
        font = _tray_font(fs)
        x0, _, x1, _ = d.textbbox((0, 0), text, font=font)
        if x1 - x0 <= size - 4:
            break
        fs -= 2
    d.text((size / 2, size / 2), text, font=_tray_font(fs), fill=fg, anchor="mm")
    return img


class TrayMixin:
    """トレイアイコンの作成と更新。メニューは Widget._menu_spec() をそのまま使う"""

    def _to_tray(self, spec: list) -> list:
        def cb(fn):
            # トレイのスレッドから呼ばれるので、tk側のキューに渡して実行する
            return lambda icon, item: self.q.put(("ui", lambda: self._do(fn)))

        items = []
        for it in spec:
            kind = it[0]
            if kind == "sep":
                items.append(pystray.Menu.SEPARATOR)
            elif kind == "cmd":
                default = len(it) > 3 and it[3]
                items.append(pystray.MenuItem(it[1], cb(it[2]), default=default))
            elif kind in ("check", "radio"):
                state = bool(it[2]())  # メニュー作成時点の状態
                items.append(pystray.MenuItem(it[1], cb(it[3]), checked=lambda item, s=state: s,
                                              radio=(kind == "radio")))
            elif kind == "sub":
                items.append(pystray.MenuItem(it[1], pystray.Menu(*self._to_tray(it[2]))))
        return items

    def _start_tray(self):
        if not self.tray_ok:
            return
        try:
            self.tray = pystray.Icon(APP, make_tray_image("--", BTN_BG, FG), self._title(),
                                     menu=pystray.Menu(*self._tray_items()))
            self.tray.run_detached()
        except Exception:
            self.tray = None
            self.tray_ok = False
            self._build()
            self._reposition()
            return
        self._tray_refresh()

    def _tray_header(self) -> str:
        latest = self.readings[0] if self.readings else None
        demo = "[DEMO] " if self.demo else ""
        if latest is None:
            return demo + (f"⚠ {self.error_text}" if self.error_text else t("tray_no_data"))
        arrow, label = trend_text(latest.trend_direction)
        _, stale, _, age = self._status(latest)
        hm = latest.datetime.astimezone().strftime('%H:%M')
        text = f"{demo}{latest.value} mg/dL {arrow} {label}  ({hm}, {age})"
        if stale:
            text = "⚠ " + text
        return text

    def _tray_items(self) -> list:
        header = self._tray_header()
        items = [pystray.MenuItem(header, lambda icon, item: None, enabled=False)]
        if self.error_text and self.readings:
            items.append(pystray.MenuItem(f"⚠ {self.error_text}", lambda icon, item: None,
                                          enabled=False))
        items.append(pystray.Menu.SEPARATOR)
        return items + self._to_tray(self._menu_spec())

    def _tray_refresh(self):
        """トレイのアイコン画像・ツールチップ・メニューを最新の状態にする（変化があった時だけ）"""
        if self.tray is None:
            return
        latest = self.readings[0] if self.readings else None
        if latest is None:
            img_key = ("--", BTN_BG, FG)
            tip = self._title()
        else:
            color, stale, _, age = self._status(latest)
            bg, fg = {RED: (RED, "#ffffff"), ORANGE: (ORANGE, "#000000"),
                      YELLOW: (YELLOW, "#000000"), GRAY: (GRAY, "#ffffff")}.get(color, (GREEN, "#000000"))
            img_key = (str(latest.value), bg, fg)
            arrow, label = trend_text(latest.trend_direction)
            tip = f"{self._title()}\n{latest.value} mg/dL {arrow} {label} ({age})"
        try:
            if img_key != self._tray_img_key:
                self._tray_img_key = img_key
                self.tray.icon = make_tray_image(*img_key)
            if self.tray.title != tip[:127]:
                self.tray.title = tip[:127]
            sig = (self._tray_header(), self.error_text, i18n.LANG, self.demo, self.visible,
                   self.cfg.get("show_graph"), self.cfg.get("scale"), self.cfg.get("topmost"),
                   startup_registered())
            if sig != self._tray_sig:
                self._tray_sig = sig
                self.tray.menu = pystray.Menu(*self._tray_items())
        except Exception:
            pass
