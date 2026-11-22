"""
GlucoseWidget for Dexcom（非公式 / Unofficial）
Dexcom Share（非公式API）の血糖値をデスクトップに常駐表示する小さなウィジェット

- 現在の血糖値とトレンド（急上昇 / 上昇 / やや上昇 / 維持 / やや下降 / 下降 / 急下降）を表示
- 設定した上限以上・下限以下でアラート音（アプリ自身が WAV を再生 → 音量ミキサーで個別に音量調整可）
- アラーム時に Windows のトースト通知（設定で ON/OFF）
- タスクトレイに常駐（アイコンに現在値。右クリックで現在値とメニュー、左クリックで表示/非表示）
- 最小化（「–」ボタン / メニュー）でウィンドウを隠してトレイに格納
- 右クリック →「推移グラフを表示」で左側にグラフ（1h/3h/6h/12h/24h、マウスで値と時刻）
- 日本語 / 英語（Windows の表示言語で自動選択、設定で切替）。単位は mg/dL のみ
- デモモード（--demo で起動）：Dexcom にログインせず架空データで動作確認

このファイルは起動だけを受け持つ。中身は glucosewidget/ パッケージ：
  constants（定数） / i18n（文言） / config（設定・パスワード） / fetcher（取得・デモ） /
  sound（アラート音・音量） / notify（トースト通知） / startup（自動起動） /
  tray（トレイ） / graph（推移グラフ） / settings_dialog（設定画面） / widget（本体ウィンドウ）

※ 非公式アプリです（Dexcom, Inc. の提供・承認・提携ではありません）。医療機器ではありません。
  治療の判断には使わないでください。
"""
from __future__ import annotations

import sys

from glucosewidget.config import load_config
from glucosewidget.constants import APP_TITLE
from glucosewidget.i18n import set_language, t
from glucosewidget.widget import Widget


def main():
    force_demo = "--demo" in sys.argv[1:]
    if sys.platform == "win32":
        import ctypes
        # 二重起動防止（2つ起動するとアラートも二重に鳴るため）。--demo は通常版と別枠
        global _mutex
        name = "Local\\GlucoseWidget_single" + ("_demo" if force_demo else "")
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, name)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            set_language(load_config().get("language", "auto"))
            ctypes.windll.user32.MessageBoxW(None, t("already_running"), APP_TITLE, 0x40)
            return
        try:  # 高DPIでぼやけないように
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    Widget(force_demo=force_demo).run()


if __name__ == "__main__":
    main()
