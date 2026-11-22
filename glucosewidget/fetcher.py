"""Dexcom Share からの取得（バックグラウンドスレッド）とデモデータ"""
from __future__ import annotations

import math
import queue
import random
import threading
import time
from datetime import datetime, timedelta, timezone

from pydexcom import Dexcom
from pydexcom.errors import AccountError

from .config import get_password, is_email
from .constants import (FULL, LONG_GAP, MARGIN, MAX_BACKOFF, PERIOD, RECENT, RESUME_GAP, RETRY,
                        Reading)


# ---------------------------------------------------------------- デモデータ
class DemoSource:
    """架空の血糖値（5分ごと・24時間分）。上下に大きく振れるのでアラートも試せる"""

    def __init__(self):
        self.phase = random.uniform(0, 1000)
        self.offset = random.uniform(0, PERIOD)  # 測定時刻のずれ（実機らしく）
        self.forced: dict[int, tuple[int, str]] = {}

    def _curve(self, ts: float) -> float:
        h = ts / 3600 + self.phase
        return (155 + 65 * math.sin(2 * math.pi * h / 5.3)
                + 32 * math.sin(2 * math.pi * h / 1.9 + 1.3)
                + 8 * math.sin(2 * math.pi * h / 0.55 + 0.7))

    def _slot(self, ts: float) -> int:
        return round((ts - self.offset) / PERIOD)

    def _reading(self, ts: float) -> Reading:
        dt = datetime.fromtimestamp(ts, timezone.utc)
        forced = self.forced.get(self._slot(ts))
        if forced:
            return Reading(forced[0], forced[1], dt)
        v = int(round(min(400, max(40, self._curve(ts)))))
        rate = (self._curve(ts) - self._curve(ts - 900)) / 15  # mg/dL/分
        if rate >= 3:
            trend = "DoubleUp"
        elif rate >= 2:
            trend = "SingleUp"
        elif rate >= 1:
            trend = "FortyFiveUp"
        elif rate > -1:
            trend = "Flat"
        elif rate > -2:
            trend = "FortyFiveDown"
        elif rate > -3:
            trend = "SingleDown"
        else:
            trend = "DoubleDown"
        return Reading(v, trend, dt)

    def readings(self) -> list[Reading]:
        now = time.time()
        last = math.floor((now - self.offset) / PERIOD) * PERIOD + self.offset
        return [self._reading(last - k * PERIOD) for k in range(FULL[1])]

    def simulate(self, kind: str) -> None:
        """今この瞬間に新しい測定値が届いたことにする"""
        now = time.time()
        self.offset = now % PERIOD
        self.forced = {self._slot(now): {
            "low": (54, "SingleDown"), "high": (288, "SingleUp"), "rapid": (178, "DoubleUp"),
        }[kind]}


# ---------------------------------------------------------------- 取得スレッド
class Fetcher(threading.Thread):
    """バックグラウンドで Dexcom Share から値を取ってきてキューに流す

    - 起動時・長い中断のあと・アカウント変更時だけ24時間分を取得し、普段は直近数件を足していく
    - 「最新の測定時刻＋5分」を少し過ぎたら取得、未着なら30〜60秒後に再取得
    - エラーが続いたら間隔を倍々に延ばす（最大15分）
    """

    def __init__(self, cfg: dict, out: queue.Queue, demo: bool):
        super().__init__(daemon=True)
        self.cfg = cfg
        self.out = out
        self.demo = demo
        self.demo_src = DemoSource()
        self.wake = threading.Event()
        self.reset_client = True
        self.clear_data = False
        self.client: Dexcom | None = None
        self.stopped = False
        self.readings: list[Reading] = []  # 新しい順
        self.need_full = True
        self.last_ok = 0.0
        self.errors = 0
        # ログイン失敗後は設定を保存し直すまで再試行しない（アカウントロック防止）
        self.auth_blocked: str | None = None

    def refresh(self, reset: bool = False):
        """reset=True: アカウント・デモ切替などで、ログインからやり直して24時間分を取り直す"""
        if reset:
            self.reset_client = True
            self.auth_blocked = None
            self.need_full = True
            self.clear_data = True
            self.errors = 0
        self.wake.set()

    def run(self):
        while not self.stopped:
            try:
                wait = self._once()
            except Exception as e:  # 想定外でもスレッドは止めない
                self.out.put(("error", str(e)))
                wait = 60
            self.wake.wait(timeout=max(5.0, wait))
            self.wake.clear()

    # ----- 次の取得までの秒数
    def _next_wait(self) -> float:
        latest = self.readings[0] if self.readings else None
        if latest is None:
            return random.uniform(*RETRY)
        due = latest.datetime.timestamp() + PERIOD + MARGIN - time.time()
        if due > 0:
            return min(due, PERIOD + MARGIN)
        return random.uniform(*RETRY)  # 次の値がまだ届いていない

    def _get(self, full: bool) -> list[Reading]:
        minutes, count = FULL if full else RECENT
        raw = self.client.get_glucose_readings(minutes=minutes, max_count=count)
        out = [Reading(int(r.value), str(r.trend_direction), r.datetime) for r in raw or []]
        out.sort(key=lambda r: r.datetime, reverse=True)
        return out

    def _merge(self, new: list[Reading], full: bool) -> None:
        merged = {} if full else {r.datetime: r for r in self.readings}
        for r in new:
            merged[r.datetime] = r
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        self.readings = sorted((r for r in merged.values() if r.datetime >= cutoff),
                               key=lambda r: r.datetime, reverse=True)

    def _once(self) -> float:
        if self.clear_data:
            self.clear_data = False
            self.readings = []
        if self.demo:
            self.readings = self.demo_src.readings()
            self.out.put(("data", list(self.readings)))
            return self._next_wait()

        user = self.cfg.get("username", "")
        pw = get_password(user)
        if not is_email(user) or not pw:
            # メールアドレス以外（以前の版のユーザー名・電話番号・アカウントID）は
            # ログインを試さずに設定し直してもらう（失敗を重ねてアカウントがロックされないように）
            self.out.put(("need_setup", None))
            return 3600  # 設定保存で起こされる
        if self.auth_blocked:
            self.out.put(("auth_error", self.auth_blocked))
            return 3600
        try:
            if self.reset_client or self.client is None:
                self.client = Dexcom(username=user, password=pw, region=self.cfg["region"])
                self.reset_client = False
            full = (self.need_full or not self.readings
                    or time.time() - self.last_ok > LONG_GAP)
            new = self._get(full)
            if not full and new and self.readings:
                # センサーの途切れから復帰した直後は、後から埋まる分もあるので取り直す
                if (new[0].datetime - self.readings[0].datetime).total_seconds() > RESUME_GAP:
                    new, full = self._get(True), True
            self._merge(new, full)
            self.need_full = False
            self.last_ok = time.time()
            self.errors = 0
            self.out.put(("data", list(self.readings)))
            return self._next_wait()
        except AccountError as e:
            self.client = None
            self.reset_client = True
            self.auth_blocked = "err_auth_locked" if "Maximum" in str(e) else "err_auth"
            self.out.put(("auth_error", self.auth_blocked))
            return 3600
        except Exception as e:  # 通信エラーなどは間隔を延ばしながら再試行
            self.client = None
            self.reset_client = True
            self.errors += 1
            self.out.put(("error", str(e)))
            return min(60 * 2 ** (self.errors - 1), MAX_BACKOFF)
