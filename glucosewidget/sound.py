"""アラート音（WAV を作って再生）と、音量ミキサーのこのアプリの音量"""
from __future__ import annotations

import array
import io
import math
import os
import sys
import tempfile
import time
import wave

try:
    import winsound  # Windows 標準
except ImportError:  # Windows 以外（開発用）
    winsound = None

from .constants import APP


# ---------------------------------------------------------------- アラート音
class Alarm:
    """WAV を作ってアプリ自身が再生する（音量は Windows の音量ミキサーのこのアプリの音量に従う）

    パターンを REPEATS 回鳴らしたら自動で止まる。
    """
    REPEATS = 3
    RATE = 22050
    AMP = 0.8
    # 低血糖は高音で速く、高血糖は低音でゆっくり、急変は2音
    PATTERNS = {
        "low": [(1800, 180), (0, 80), (1800, 180), (0, 80), (1800, 180), (0, 500)],
        "high": [(700, 400), (0, 200), (700, 400), (0, 900)],
        "rapid": [(1200, 200), (900, 200), (0, 900)],
    }

    def __init__(self):
        self._until = 0.0
        self._files: dict[tuple[str, int], str] = {}
        self._dir = os.path.join(tempfile.gettempdir(), APP)

    @property
    def active(self) -> bool:
        return time.time() < self._until

    def _wav_bytes(self, kind: str, repeats: int) -> bytes:
        rate = self.RATE
        samples = array.array("h")
        fade = int(rate * 0.005)  # 5ms のフェードでプチノイズを防ぐ
        for _ in range(repeats):
            for freq, ms in self.PATTERNS[kind]:
                n = int(rate * ms / 1000)
                if not freq:
                    samples.extend([0] * n)
                    continue
                f = min(fade, n // 2) or 1
                k = 2 * math.pi * freq / rate
                amp = self.AMP * 32767
                samples.extend(
                    int(amp * min(1.0, i / f, (n - i) / f) * math.sin(k * i)) for i in range(n))
        if sys.byteorder != "little":
            samples.byteswap()
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(samples.tobytes())
        return buf.getvalue()

    def _path(self, kind: str, repeats: int) -> str:
        key = (kind, repeats)
        if key not in self._files:
            os.makedirs(self._dir, exist_ok=True)
            path = os.path.join(self._dir, f"alert_{kind}_{repeats}.wav")
            with open(path, "wb") as f:
                f.write(self._wav_bytes(kind, repeats))
            self._files[key] = path
        return self._files[key]

    def play(self, kind: str, repeats: int | None = None):
        """kind: 'low' / 'high' / 'rapid'。パターンを repeats 回（既定3回）鳴らして止まる"""
        kind = kind if kind in self.PATTERNS else "high"
        repeats = repeats or self.REPEATS
        self.stop()
        self._until = time.time() + sum(ms for _, ms in self.PATTERNS[kind]) * repeats / 1000
        if winsound is None:
            return
        try:
            winsound.PlaySound(self._path(kind, repeats),
                               winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except (OSError, RuntimeError):
            self._until = 0.0

    def stop(self):
        self._until = 0.0
        if winsound is not None:
            try:
                winsound.PlaySound(None, 0)
            except (OSError, RuntimeError):
                pass


# ---------------------------------------------------------------- アプリ音量（音量ミキサーと同じ値）
class AppVolume:
    """Windows の音量ミキサーに出る「このアプリの音量」を読み書きする（Core Audio / ISimpleAudioVolume）

    PlaySound の音はこのプロセスの既定オーディオセッションで鳴るので、そのセッションの音量を操作する。
    COM は呼び出したスレッド（tk のメインスレッド）で使う。
    """

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        self._c = ctypes
        self._vol = None
        ole32 = ctypes.windll.ole32
        ole32.CoInitializeEx(None, 2)  # STA（初期化済みでも問題なし）

        class GUID(ctypes.Structure):
            _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD), ("d3", wintypes.WORD),
                        ("d4", ctypes.c_ubyte * 8)]

        def guid(text):
            g = GUID()
            ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(g))
            return g

        clsid_enum = guid("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
        iid_enum = guid("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
        iid_mgr = guid("{BFA971F1-4D5E-40BB-935E-967039BFBEE4}")

        enum = ctypes.c_void_p()
        ole32.CoCreateInstance.restype = ctypes.HRESULT
        ole32.CoCreateInstance(ctypes.byref(clsid_enum), None, 23, ctypes.byref(iid_enum),
                               ctypes.byref(enum))
        dev = mgr = None
        try:
            dev = ctypes.c_void_p()
            # IMMDeviceEnumerator::GetDefaultAudioEndpoint(eRender, eConsole, &device)
            self._call(enum, 4, ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_void_p))(
                0, 0, ctypes.byref(dev))
            mgr = ctypes.c_void_p()
            # IMMDevice::Activate(IID_IAudioSessionManager, CLSCTX_ALL, NULL, &mgr)
            self._call(dev, 3, ctypes.POINTER(GUID), wintypes.DWORD, ctypes.c_void_p,
                       ctypes.POINTER(ctypes.c_void_p))(ctypes.byref(iid_mgr), 23, None,
                                                        ctypes.byref(mgr))
            vol = ctypes.c_void_p()
            # IAudioSessionManager::GetSimpleAudioVolume(NULL=既定セッション, FALSE, &vol)
            self._call(mgr, 4, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(ctypes.c_void_p))(
                None, 0, ctypes.byref(vol))
            self._vol = vol
        finally:
            for obj in (mgr, dev, enum):
                if obj:
                    self._release(obj)

    def _call(self, obj, index, *argtypes):
        c = self._c
        vtbl = c.cast(obj, c.POINTER(c.POINTER(c.c_void_p)))[0]
        fn = c.WINFUNCTYPE(c.HRESULT, c.c_void_p, *argtypes)(vtbl[index])
        return lambda *args: fn(obj, *args)

    def _release(self, obj):
        c = self._c
        vtbl = c.cast(obj, c.POINTER(c.POINTER(c.c_void_p)))[0]
        c.WINFUNCTYPE(c.c_ulong, c.c_void_p)(vtbl[2])(obj)

    def get(self) -> tuple[int, bool]:
        """(音量 0〜100, ミュート中か)"""
        c = self._c
        level, mute = c.c_float(), c.c_int()
        self._call(self._vol, 4, c.POINTER(c.c_float))(c.byref(level))   # GetMasterVolume
        self._call(self._vol, 6, c.POINTER(c.c_int))(c.byref(mute))      # GetMute
        return int(round(level.value * 100)), bool(mute.value)

    def set(self, percent: int) -> None:
        c = self._c
        level = min(100, max(0, int(percent))) / 100
        self._call(self._vol, 3, c.c_float, c.c_void_p)(level, None)     # SetMasterVolume
        self._call(self._vol, 5, c.c_int, c.c_void_p)(0, None)           # SetMute(FALSE)

    def close(self) -> None:
        if self._vol:
            self._release(self._vol)
            self._vol = None


def open_app_volume() -> AppVolume | None:
    if sys.platform != "win32":
        return None
    try:
        return AppVolume()
    except Exception:  # オーディオ機器がない等
        return None
