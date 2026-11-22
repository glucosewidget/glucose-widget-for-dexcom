"""Windows 起動時の自動起動（スタートアップフォルダに VBS を置く）"""
from __future__ import annotations

import os
import sys

from .constants import APP, ROOT_DIR


# ---------------------------------------------------------------- スタートアップ登録
def _startup_path() -> str:
    return os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup",
                        f"{APP}.vbs")


def startup_registered() -> bool:
    return os.path.exists(_startup_path())


def set_startup(enable: bool) -> None:
    path = _startup_path()
    if enable:
        if getattr(sys, "frozen", False):  # exe 版：exe 自身を起動
            cmd = f'"""{sys.executable}"""'
        else:                              # スクリプト版：pythonw で起動
            pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.exists(pyw):
                pyw = sys.executable
            cmd = f'"""{pyw}"" ""{os.path.join(ROOT_DIR, "glucose_widget.py")}"""'
        with open(path, "w", encoding="utf-16") as f:  # VBS は UTF-16 なら日本語パスも安全
            f.write(f'CreateObject("WScript.Shell").Run {cmd}, 0, False\n')
    elif os.path.exists(path):
        os.remove(path)
