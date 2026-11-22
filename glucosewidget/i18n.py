"""表示言語（日本語 / 英語）と文言"""
from __future__ import annotations


STRINGS = {
    "ja": {
        "trend_DoubleUp": "急上昇", "trend_SingleUp": "上昇", "trend_FortyFiveUp": "やや上昇",
        "trend_Flat": "維持", "trend_FortyFiveDown": "やや下降", "trend_SingleDown": "下降",
        "trend_DoubleDown": "急下降", "trend_NotComputable": "判定不可",
        "trend_RateOutOfRange": "変化量が範囲外", "trend_None": "-",
        "size_小": "小", "size_中": "中", "size_大": "大", "size_特大": "特大",
        "connecting": "接続中…",
        "no_data": "直近24時間のデータなし",
        "graph_no_data": "この期間のデータなし",
        "setup_hint": "右クリック →「設定…」",
        "just_now": "たった今",
        "min_ago": "{n}分前",
        "info": "{time}（{age}）",
        "delta": "  前回比 {d:+d}",
        "stale": "⚠ データが古い（{age}）",
        "err_auth_locked": "試行回数オーバーでロック中。しばらく待ってから設定を保存し直してください",
        "err_auth": "ログイン失敗（ID/パスワード/地域/共有設定を確認）",
        "err_net": "通信エラー（自動で再試行）",
        "demo_name": "デモ",
        "menu_refresh": "今すぐ更新",
        "menu_graph": "推移グラフを表示",
        "menu_size": "表示サイズ",
        "menu_settings": "設定…",
        "menu_topmost": "常に最前面",
        "menu_startup": "Windows起動時に自動起動",
        "menu_demo": "デモ",
        "demo_low": "低血糖をシミュレート",
        "demo_high": "高血糖をシミュレート",
        "demo_rapid": "急上昇をシミュレート",
        "menu_hide": "最小化（トレイに格納）",
        "menu_show": "ウィンドウを表示",
        "menu_quit": "終了",
        "tray_no_data": "データなし",
        "toast_low": "低血糖アラート：{v} mg/dL {arrow}（{time}）",
        "toast_high": "高血糖アラート：{v} mg/dL {arrow}（{time}）",
        "toast_rapid": "{label}：{v} mg/dL {arrow}（{time}）",
        "toast_test": "通知のテストです",
        "toast_hint": "通知が表示されない場合は、Windows の通知設定を確認してください。",
        "settings_title": "設定",
        "sec_account": "Dexcom アカウント（共有する本人のもの）",
        "email": "メールアドレス",
        "err_email_empty": "メールアドレスを入力してください",
        "err_email": "メールアドレスの形式を確認してください",
        "password": "パスワード",
        "pw_saved": "パスワード（保存済み：変更時のみ入力）",
        "display_name": "表示名",
        "region": "地域",
        "demo_running": ("デモモードで起動中（--demo）。Dexcom にはログインせず、架空のデータを表示しています。"
                         "アカウント設定はデモ中は使われません。"),
        "sec_alert": "アラート",
        "alert_enabled": "アラートを鳴らす",
        "alert_low": "この値以下で鳴らす (mg/dL)",
        "alert_high": "この値以上で鳴らす (mg/dL)",
        "alert_rapid": "急上昇・急下降でも鳴らす",
        "repeat": "範囲外が続く時の再通知 (分)",
        "toast": "Windows の通知でも知らせる",
        "volume": "アラート音の音量",
        "volume_muted": "ミュート",
        "volume_na": "音量を取得できません（オーディオ機器を確認してください）",
        "sec_general": "その他",
        "language": "表示言語",
        "lang_auto": "自動（Windows に合わせる）",
        "test_low": "低血糖音",
        "test_high": "高血糖音",
        "test_rapid": "急変音",
        "test_toast": "通知テスト",
        "save": "保存",
        "cancel": "キャンセル",
        "err_number": "数値を正しく入力してください",
        "err_lowhigh": "下限は上限より小さくしてください",
        "err_pw": "パスワードを入力してください",
        "err_pw_save": "パスワード保存に失敗しました:\n{e}",
        "err_startup": "スタートアップ登録に失敗しました:\n{e}",
        "already_running": "GlucoseWidget for Dexcom はすでに起動しています。",
        "no_keyring": "keyring がインストールされていません（pip install keyring）",
        "disclaimer_title": "ご注意",
        "disclaimer": (
            "・このアプリの表示やアラートを、治療の判断（インスリン量、補食など）に使わないでください。"
            "判断は必ず Dexcom 公式アプリや血糖測定器で確認し、医師の指示に従ってください。\n"
            "・このアプリは医療機器ではありません。Dexcom Share の非公式APIを使っているため、"
            "予告なく動かなくなったり、値が遅れたり欠けたりすることがあります。\n"
            "・このアプリは非公式です（Dexcom 社の提供・承認・提携ではありません）。\n"
            "・作者は医療関係者でも Dexcom 社の関係者でもありません。"
        ),
        "disclaimer_ask": "上記を理解したうえで使う場合は「OK」を押してください。",
    },
    "en": {
        "trend_DoubleUp": "Rising quickly", "trend_SingleUp": "Rising",
        "trend_FortyFiveUp": "Rising slowly", "trend_Flat": "Steady",
        "trend_FortyFiveDown": "Falling slowly", "trend_SingleDown": "Falling",
        "trend_DoubleDown": "Falling quickly", "trend_NotComputable": "Not computable",
        "trend_RateOutOfRange": "Rate out of range", "trend_None": "-",
        "size_小": "Small", "size_中": "Medium", "size_大": "Large", "size_特大": "Extra large",
        "connecting": "Connecting…",
        "no_data": "No data in the last 24 hours",
        "graph_no_data": "No data in this period",
        "setup_hint": "Right-click → Settings…",
        "just_now": "just now",
        "min_ago": "{n} min ago",
        "info": "{time} ({age})",
        "delta": "  Δ {d:+d}",
        "stale": "⚠ Data is old ({age})",
        "err_auth_locked": "Account locked (too many attempts). Wait a while, then save the settings again",
        "err_auth": "Login failed (check ID / password / region / sharing)",
        "err_net": "Connection error (retrying automatically)",
        "demo_name": "Demo",
        "menu_refresh": "Refresh now",
        "menu_graph": "Show trend graph",
        "menu_size": "Size",
        "menu_settings": "Settings…",
        "menu_topmost": "Always on top",
        "menu_startup": "Start with Windows",
        "menu_demo": "Demo",
        "demo_low": "Simulate low",
        "demo_high": "Simulate high",
        "demo_rapid": "Simulate rapid rise",
        "menu_hide": "Minimize to tray",
        "menu_show": "Show window",
        "menu_quit": "Exit",
        "tray_no_data": "No data",
        "toast_low": "Low alert: {v} mg/dL {arrow} ({time})",
        "toast_high": "High alert: {v} mg/dL {arrow} ({time})",
        "toast_rapid": "{label}: {v} mg/dL {arrow} ({time})",
        "toast_test": "This is a test notification",
        "toast_hint": "If notifications do not appear, check the Windows notification settings.",
        "settings_title": "Settings",
        "sec_account": "Dexcom account (of the person sharing)",
        "email": "Email address",
        "err_email_empty": "Please enter your email address",
        "err_email": "Please check the email address",
        "password": "Password",
        "pw_saved": "Password (saved; enter only to change)",
        "display_name": "Display name",
        "region": "Region",
        "demo_running": ("Running in demo mode (--demo). No Dexcom login; showing made-up data. "
                         "Account settings are not used while in demo mode."),
        "sec_alert": "Alerts",
        "alert_enabled": "Play alert sound",
        "alert_low": "Alert at or below (mg/dL)",
        "alert_high": "Alert at or above (mg/dL)",
        "alert_rapid": "Also alert on rapid rise / fall",
        "repeat": "Repeat while out of range (min)",
        "toast": "Also show a Windows notification",
        "volume": "Alert volume",
        "volume_muted": "Muted",
        "volume_na": "Can't read the volume (check your audio device)",
        "sec_general": "Other",
        "language": "Language",
        "lang_auto": "Auto (follow Windows)",
        "test_low": "Low sound",
        "test_high": "High sound",
        "test_rapid": "Rapid sound",
        "test_toast": "Test notification",
        "save": "Save",
        "cancel": "Cancel",
        "err_number": "Please enter valid numbers",
        "err_lowhigh": "The low limit must be below the high limit",
        "err_pw": "Please enter the password",
        "err_pw_save": "Could not save the password:\n{e}",
        "err_startup": "Could not change the startup setting:\n{e}",
        "already_running": "GlucoseWidget for Dexcom is already running.",
        "no_keyring": "keyring is not installed (pip install keyring)",
        "disclaimer_title": "Important",
        "disclaimer": (
            "- Do not use this app's readings or alerts to make treatment decisions "
            "(insulin doses, eating, etc.). Always confirm with the official Dexcom app or a "
            "blood glucose meter, and follow your doctor's instructions.\n"
            "- This app is not a medical device. It uses an unofficial Dexcom Share API, so it may "
            "stop working without notice, and readings may be delayed or missing.\n"
            "- This is an unofficial app. It is not made, endorsed, owned by or affiliated with Dexcom. "
            "The author is neither a healthcare professional nor affiliated with Dexcom."
        ),
        "disclaimer_ask": "If you understand the above and want to use the app, press OK.",
    },
}
LANG = "ja"


def detect_lang() -> str:
    """Windows の表示言語が日本語なら ja、それ以外は en"""
    try:
        import ctypes
        lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        return "ja" if lid & 0x3FF == 0x11 else "en"
    except Exception:
        import locale
        return "ja" if (locale.getlocale()[0] or "").lower().startswith(("ja", "japanese")) else "en"


def set_language(setting: str) -> None:
    global LANG
    LANG = setting if setting in STRINGS else detect_lang()


def t(key: str, **kw) -> str:
    s = STRINGS[LANG].get(key) or STRINGS["ja"].get(key, key)
    return s.format(**kw) if kw else s


# pydexcom の trend_direction -> 矢印（ラベルは t("trend_...")）
ARROWS = {
    "DoubleUp": "⇈", "SingleUp": "↑", "FortyFiveUp": "↗", "Flat": "→",
    "FortyFiveDown": "↘", "SingleDown": "↓", "DoubleDown": "⇊",
    "NotComputable": "?", "RateOutOfRange": "?", "None": "-",
}
RAPID = {"DoubleUp", "DoubleDown"}


def wrap_ok(text: str) -> str:
    """日本語の折り返しが英単語の前の空白で切れないように、空白を改行しない空白にする"""
    return text.replace(" ", " ") if LANG == "ja" else text


def trend_text(direction: str) -> tuple[str, str]:
    if direction in ARROWS:
        return ARROWS[direction], t(f"trend_{direction}")
    return "?", direction
