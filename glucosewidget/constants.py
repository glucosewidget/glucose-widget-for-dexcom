"""アプリ全体で使う定数とデータ型"""
from __future__ import annotations

import os
from dataclasses import dataclass
import datetime as _dt

APP = "GlucoseWidget"                 # 設定フォルダ・資格情報・通知IDの登録名（変えない）
APP_TITLE = "GlucoseWidget for Dexcom"  # 画面に出す名前（ウィンドウ・トレイ・通知・音量ミキサー）
CONF_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP)
CONF_PATH = os.path.join(CONF_DIR, "config.json")
# glucose_widget.py と icon.ico がある場所（パッケージの1つ上）
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RED_BELOW = 50  # この値未満は赤文字

# ---------------------------------------------------------------- 取得タイミング
PERIOD = 300              # センサーの測定間隔（5分）
MARGIN = 20               # 「最新の測定時刻＋5分」からこれだけ過ぎたら取得
RETRY = (30, 60)          # 次の値が未着なら、この範囲の秒数後に再取得
MAX_BACKOFF = 15 * 60     # エラーが続いた時の最大間隔
LONG_GAP = 20 * 60        # 前回の取得成功からこれ以上空いたら24時間分を取り直す
RESUME_GAP = 30 * 60      # 手元の最新値から新着値までこれ以上空いたら24時間分を取り直す
FULL = (1440, 288)        # 24時間分（minutes, max_count）
RECENT = (30, 6)          # 直近数件

# ---------------------------------------------------------------- 色・サイズ
BG = "#1b1d21"
FG = "#f2f2f2"
SUB = "#9aa0a6"
RED = "#ff3b30"
ORANGE = "#ff9f0a"
YELLOW = "#ffd60a"
GRAY = "#6b6f75"
GREEN = "#7ee2a8"
BORDER = "#34383f"
ACCENT = "#3a7bd5"
BTN_BG = "#2a2d33"
BAND = "#1f2e27"
GRID = "#2c3036"
LINE = "#5b6068"
TIP_BG = "#2b2f36"
FONT = "Yu Gothic UI"

SCALES = {"小": 0.8, "中": 1.0, "大": 1.3, "特大": 1.6}   # キーは設定ファイル互換のため日本語のまま
RANGES = [1, 3, 6, 12, 24]                       # グラフ期間（時間）
TICKS = {1: 15, 3: 30, 6: 60, 12: 120, 24: 240}   # 時刻目盛り間隔（分）
GRAPH_W, GRAPH_H_MIN = 460, 80
Y_MIN, Y_MAX = 40, 400


@dataclass(frozen=True)
class Reading:
    value: int
    trend_direction: str
    datetime: _dt.datetime  # UTC（tz付き）
