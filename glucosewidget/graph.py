"""推移グラフ（Widget に混ぜて使う）"""
from __future__ import annotations

from datetime import datetime, timezone

from .constants import (BAND, BORDER, GRID, LINE, ORANGE, SUB, TICKS, TIP_BG, Y_MAX, Y_MIN,
                        YELLOW)
from .i18n import t, trend_text


class GraphMixin:
    """推移グラフの描画とマウスオーバー表示。self.canvas / self.readings / self.cfg を使う"""

    def _graph_geom(self):
        c = self.canvas
        W, H = c.winfo_width(), c.winfo_height()
        left, right = self._px(30), self._px(6)
        top, bottom = self._px(4), self._px(16)
        return left, top, max(left + 10, W - right), max(top + 10, H - bottom)

    def _y(self, v, y0, y1):
        ymax = getattr(self, "_ymax", Y_MAX)
        v = min(max(v, Y_MIN), ymax)
        return y1 - (v - Y_MIN) / (ymax - Y_MIN) * (y1 - y0)

    def _draw_graph(self):
        c = self.canvas
        if c is None or not c.winfo_exists():
            return
        c.delete("all")
        x0, y0, x1, y1 = self._graph_geom()
        hours = self.cfg.get("graph_hours", 6)
        now = datetime.now(timezone.utc)
        t0 = now.timestamp() - hours * 3600
        span = hours * 3600

        def X(dt):
            return x0 + (dt.timestamp() - t0) / span * (x1 - x0)

        low, high = int(self.cfg["alert_low"]), int(self.cfg["alert_high"])
        small = self._f(8)
        pts = [r for r in reversed(self.readings) if r.datetime.timestamp() >= t0]
        # 縦軸の上端：普段は300、データや上限がそれを超えたら50刻みで最大400まで広げる
        top_v = max([high + 30] + [r.value + 20 for r in pts])
        self._ymax = min(Y_MAX, max(300, -(-top_v // 50) * 50))

        # 目標範囲の帯と上限・下限線
        c.create_rectangle(x0, self._y(high, y0, y1), x1, self._y(low, y0, y1),
                           fill=BAND, outline="")
        for v, col in ((low, ORANGE), (high, YELLOW)):
            yy = self._y(v, y0, y1)
            c.create_line(x0, yy, x1, yy, fill=col, dash=(3, 3))
            c.create_text(x0 - self._px(4), yy, text=str(v), anchor="e", fill=col, font=small)
        c.create_line(x0, y1, x1, y1, fill=GRID)
        if self._y(high, y0, y1) - y0 > self._px(14):  # 上限ラベルと重なるときは出さない
            c.create_text(x0 - self._px(4), y0, text=str(self._ymax), anchor="ne", fill=SUB, font=small)

        # 時刻目盛り
        step = TICKS[hours] * 60
        tt = (int(t0) // step + 1) * step
        while tt < now.timestamp():
            xx = x0 + (tt - t0) / span * (x1 - x0)
            c.create_line(xx, y0, xx, y1, fill=GRID)
            label = datetime.fromtimestamp(tt).strftime("%H:%M")
            c.create_text(xx, y1 + self._px(2), text=label, anchor="n", fill=SUB, font=small)
            tt += step

        # 値（古い順に線でつなぐ。11分以上空いたら線を切る）
        # 6時間以下は点＋細線、12時間以上は点が重なるので色付きの線だけにする
        dense = hours >= 12
        self._graph_pts = []
        prev = None
        r_dot = self._px(2.2)
        for r in pts:
            x, y = X(r.datetime), self._y(r.value, y0, y1)
            if prev and (r.datetime - prev[2]).total_seconds() <= 11 * 60:
                if dense:
                    c.create_line(prev[0], prev[1], x, y, fill=self._value_color(r.value),
                                  width=self._px(2), capstyle="round")
                else:
                    c.create_line(prev[0], prev[1], x, y, fill=LINE, width=self._px(1.2))
            prev = (x, y, r.datetime)
            self._graph_pts.append((x, y, r))
        if not dense:
            for x, y, r in self._graph_pts:
                col = self._value_color(r.value)
                c.create_oval(x - r_dot, y - r_dot, x + r_dot, y + r_dot, fill=col, outline="")
        if not pts:
            c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=t("graph_no_data"), fill=SUB, font=small)

    def _on_hover(self, e):
        c = self.canvas
        c.delete("hover")
        pts = getattr(self, "_graph_pts", [])
        if not pts:
            return
        x, y, r = min(pts, key=lambda p: abs(p[0] - e.x))
        if abs(x - e.x) > self._px(20):
            return
        x0, y0, x1, y1 = self._graph_geom()
        c.create_line(x, y0, x, y1, fill=SUB, dash=(2, 2), tags="hover")
        rr = self._px(4)
        c.create_oval(x - rr, y - rr, x + rr, y + rr, outline="#ffffff", width=2, tags="hover")
        arrow = trend_text(r.trend_direction)[0]
        text = f"{r.datetime.astimezone().strftime('%m/%d %H:%M')}  {r.value} mg/dL {arrow}"
        tid = c.create_text(0, 0, text=text, anchor="nw", fill="#ffffff",
                            font=self._f(9, "bold"), tags="hover")
        bx0, by0, bx1, by1 = c.bbox(tid)
        tw, th = bx1 - bx0, by1 - by0
        pad = self._px(4)
        tx = x + self._px(8)
        if tx + tw + pad > x1:            # 右にはみ出すなら左側に出す
            tx = x - self._px(8) - tw
        ty = max(y0, min(y - th - self._px(8), y1 - th))
        c.coords(tid, tx, ty)
        bg = c.create_rectangle(tx - pad, ty - pad, tx + tw + pad, ty + th + pad,
                                fill=TIP_BG, outline=BORDER, tags="hover")
        c.tag_raise(tid, bg)
