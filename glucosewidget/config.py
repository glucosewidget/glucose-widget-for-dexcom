"""設定ファイルの読み書き、ログインID、パスワード（Windows 資格情報マネージャー）"""
from __future__ import annotations

import json
import os

try:
    import keyring  # パスワードは Windows 資格情報マネージャーに保存
except ImportError:
    keyring = None

from .constants import APP, CONF_DIR, CONF_PATH, RANGES, SCALES
from .i18n import t

DEFAULTS = {
    "username": "",
    "region": "jp",
    "alert_low": 70,          # この値以下でアラート
    "alert_high": 250,        # この値以上でアラート
    "alert_enabled": True,
    "alert_on_rapid": True,   # 急上昇・急下降でも鳴らす
    "repeat_minutes": 15,     # 範囲外が続く間の再アラート間隔
    "stale_minutes": 15,      # これより古いデータは「古い」と警告
    "display_name": "",       # 上部に出す名前（空ならIDを伏せ字で表示）
    "toast_enabled": True,    # アラーム時にトースト通知も出す
    "language": "auto",       # auto / ja / en
    "disclaimer_ok": False,   # 注意書きを確認済みか
    "show_graph": False,
    "graph_hours": 6,
    "scale": "中",
    "alpha": 0.92,
    "topmost": True,
    "right": None,            # ウィンドウ右端のX座標（グラフは左に広がる）
    "y": None,
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    try:
        with open(CONF_PATH, encoding="utf-8") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    if cfg.get("scale") not in SCALES:
        cfg["scale"] = "中"
    if cfg.get("graph_hours") not in RANGES:
        cfg["graph_hours"] = 6
    cfg.pop("demo_mode", None)  # デモは --demo 起動時のみ（設定には持たない）
    cfg.pop("volume", None)  # 音量は Windows の音量ミキサー側で保持（設定ファイルには持たない）
    return cfg


def save_config(cfg: dict) -> None:
    os.makedirs(CONF_DIR, exist_ok=True)
    with open(CONF_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def mask_id(user: str) -> str:
    """ログインIDを伏せ字にする（例: ta***@example.com / ***5678）"""
    user = (user or "").strip()
    if not user:
        return ""
    if "@" in user:
        local, domain = user.split("@", 1)
        return f"{local[:2]}***@{domain}"
    if user.startswith("+") or user.replace("-", "").isdigit():
        return "***" + user[-4:]
    return user[:2] + "***"


# ---------------------------------------------------------------- ログインID（メールアドレスのみ）
def is_email(text: str) -> bool:
    """メールアドレスの簡単な形式チェック（半角・空白なし・@が1つ・ドメインに「.」がある）"""
    text = text or ""
    if not text.isascii() or any(ch <= " " for ch in text) or text.count("@") != 1:
        return False
    local, domain = text.split("@")
    return bool(local) and "." in domain and not domain.startswith(".") and not domain.endswith(".")


def get_password(username: str) -> str | None:
    if keyring and username:
        try:
            return keyring.get_password(APP, username)
        except Exception:
            return None
    return None


def set_password(username: str, password: str) -> None:
    if keyring is None:
        raise RuntimeError(t("no_keyring"))
    keyring.set_password(APP, username, password)
