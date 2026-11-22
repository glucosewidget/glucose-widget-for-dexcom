"""Windows のトースト通知"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
import threading

try:
    from PIL import Image
except ImportError:
    Image = None

from .constants import APP, APP_TITLE, CONF_DIR, ROOT_DIR


# ---------------------------------------------------------------- トースト通知
AUMID = APP  # 通知の送り主として Windows に登録する ID


def _resource(name: str) -> str:
    """同梱ファイルの場所（exe 版は一時展開先、スクリプト版は glucose_widget.py の隣）"""
    base = getattr(sys, "_MEIPASS", ROOT_DIR)
    return os.path.join(base, name)


def register_toast_app() -> None:
    """通知の送り主として登録する（HKCU のみ）。

    これで「設定 → システム → 通知」の「アプリやその他の送信者からの通知」に
    名前とアイコン付きで出てきて、このアプリだけオン/オフできるようになる。
    """
    if sys.platform != "win32":
        return
    try:
        import winreg
        icon_png = os.path.join(CONF_DIR, "icon.png")
        try:
            os.makedirs(CONF_DIR, exist_ok=True)
            Image.open(_resource("icon.ico")).save(icon_png)
        except Exception:  # アイコンが無くても登録はする
            pass
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              rf"Software\Classes\AppUserModelId\{AUMID}") as k:
            winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, APP_TITLE)
            if os.path.exists(icon_png):
                winreg.SetValueEx(k, "IconUri", 0, winreg.REG_SZ, icon_png)
    except OSError:
        pass


def show_toast(title: str, message: str, fallback=None) -> None:
    """Windows のトースト通知を出す（Windows PowerShell 経由・別スレッド）。失敗したら fallback()"""
    if sys.platform != "win32":
        if fallback:
            fallback()
        return
    from xml.sax.saxutils import escape
    xml = ('<toast><visual><binding template="ToastGeneric">'
           f"<text>{escape(title)}</text><text>{escape(message)}</text>"
           '</binding></visual><audio silent="true"/></toast>')  # 音はアプリ側で鳴らす
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
        "ContentType = WindowsRuntime] > $null\n"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, "
        "ContentType = WindowsRuntime] > $null\n"
        "$d = New-Object Windows.Data.Xml.Dom.XmlDocument\n"
        f"$d.LoadXml(@'\n{xml}\n'@)\n"
        f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{AUMID}')"
        ".Show([Windows.UI.Notifications.ToastNotification]::new($d))\n"
    )
    encoded = base64.b64encode(script.encode("utf-16-le")).decode("ascii")
    ps = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"),
                      r"System32\WindowsPowerShell\v1.0\powershell.exe")

    def run():
        ok = False
        try:
            r = subprocess.run([ps, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
                                "-EncodedCommand", encoded],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=30,
                               creationflags=0x08000000)  # CREATE_NO_WINDOW
            ok = r.returncode == 0
        except (OSError, subprocess.SubprocessError):
            pass
        if not ok and fallback:
            fallback()

    threading.Thread(target=run, daemon=True).start()
