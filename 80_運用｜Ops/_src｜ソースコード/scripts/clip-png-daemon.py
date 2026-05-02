#!/usr/bin/env python3
"""clip-png-daemon: X410 clipboard BMP→PNG auto-converter.

X410 provides Windows clipboard images as image/bmp only.
Electron (Antigravity IDE) expects image/png.
This daemon watches the X11 clipboard, converts BMP→PNG,
and becomes the clipboard owner serving image/png via X11 protocol.

Unlike xclip -i (which hangs or fails to respond to selection requests),
this uses python-xlib to directly implement the X11 selection owner protocol,
properly responding to SelectionRequest events.
"""

import hashlib
import io
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

try:
    from Xlib import X, Xatom, display, error
    from Xlib.protocol import event
except ImportError:
    print("ERROR: python3-xlib not found. Install: sudo apt install python3-xlib", file=sys.stderr)
    sys.exit(1)

POLL_INTERVAL = float(os.environ.get("CLIP_PNG_POLL", "1"))
DISPLAY_NAME = os.environ.get("DISPLAY", "172.29.160.1:0")


def log(msg: str):
    t = time.strftime("%H:%M:%S")
    print(f"[{t}] {msg}", flush=True)


def get_clipboard_targets(disp_name: str) -> list[str]:
    """xclip で TARGETS を取得する。"""
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "TARGETS", "-o"],
            capture_output=True, timeout=3,
            env={**os.environ, "DISPLAY": disp_name},
        )
        if result.returncode == 0:
            return result.stdout.decode("utf-8", errors="replace").strip().split("\n")
    except (subprocess.TimeoutExpired, Exception):
        pass
    return []


def get_clipboard_bmp(disp_name: str) -> bytes | None:
    """xclip で BMP データを取得する。"""
    try:
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/bmp", "-o"],
            capture_output=True, timeout=10,
            env={**os.environ, "DISPLAY": disp_name},
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout
    except (subprocess.TimeoutExpired, Exception):
        pass
    return None


def convert_bmp_to_png(bmp_data: bytes) -> bytes | None:
    """BMP→PNG 変換。Pillow 優先、フォールバックで ImageMagick。"""
    if HAS_PILLOW:
        return _convert_pillow(bmp_data)
    return _convert_imagemagick(bmp_data)


def _convert_pillow(bmp_data: bytes) -> bytes | None:
    """Pillow でインメモリ変換（高速・ディスク不要）。"""
    try:
        img = Image.open(io.BytesIO(bmp_data))
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=False, compress_level=1)
        return buf.getvalue()
    except Exception:
        return None


def _convert_imagemagick(bmp_data: bytes) -> bytes | None:
    """ImageMagick フォールバック。"""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as bf:
        bf.write(bmp_data)
        bmp_path = bf.name
    png_path = bmp_path.replace(".bmp", ".png")
    try:
        result = subprocess.run(
            ["convert", bmp_path, png_path],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0 and os.path.exists(png_path):
            with open(png_path, "rb") as pf:
                return pf.read()
    except (subprocess.TimeoutExpired, Exception):
        pass
    finally:
        for p in (bmp_path, png_path):
            try:
                os.unlink(p)
            except OSError:
                pass
    return None


class ClipboardOwner:
    """X11 clipboard owner that serves PNG data."""

    def __init__(self, disp_name: str):
        self.disp = display.Display(disp_name)
        self.disp.set_error_handler(self._x_error_handler)
        self.screen = self.disp.screen()
        self.window = self.screen.root.create_window(
            0, 0, 1, 1, 0, self.screen.root_depth,
        )

        self.CLIPBOARD = self.disp.intern_atom("CLIPBOARD")
        self.TARGETS = self.disp.intern_atom("TARGETS")
        self.IMAGE_PNG = self.disp.intern_atom("image/png")
        self.IMAGE_BMP = self.disp.intern_atom("image/bmp")
        self.ATOM = self.disp.intern_atom("ATOM")
        # xlib-native clipboard reading 用の property atoms
        self._TARGETS_PROP = self.disp.intern_atom("_CLIP_PNG_TARGETS")
        self._BMP_PROP = self.disp.intern_atom("_CLIP_PNG_BMP")

        self.png_data: bytes | None = None
        self.is_owner = False

    def _x_error_handler(self, err, request):
        """BadWindow を安全に無視する (Electron requestor race condition 対策)。"""
        if err.code == 3:  # BadWindow
            pass  # requestor gone — expected when Electron closes temp window
        else:
            log(f"❌ X protocol error: {err}")

    def own_clipboard(self, png_data: bytes):
        """クリップボードのオーナーになり PNG データを提供する。"""
        self.png_data = png_data
        self.window.set_selection_owner(self.CLIPBOARD, X.CurrentTime)
        self.disp.flush()
        self.is_owner = True

    def get_targets(self) -> list[str]:
        """CLIPBOARD targets を xlib-native で取得 (subprocess なし)。"""
        self.window.convert_selection(
            self.CLIPBOARD, self.TARGETS, self._TARGETS_PROP, X.CurrentTime,
        )
        self.disp.flush()
        return self._wait_selection_result(self._TARGETS_PROP, atom_list=True)

    def get_bmp_data(self) -> bytes | None:
        """BMP データを xlib-native で取得 (subprocess なし)。"""
        self.window.convert_selection(
            self.CLIPBOARD, self.IMAGE_BMP, self._BMP_PROP, X.CurrentTime,
        )
        self.disp.flush()
        return self._wait_selection_result(self._BMP_PROP, atom_list=False)

    def _wait_selection_result(self, prop, atom_list=False, timeout=3.0):
        """SelectionNotify を待ち、property から結果を読む。"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            while self.disp.pending_events():
                ev = self.disp.next_event()
                if ev.type == X.SelectionNotify:
                    if ev.property == X.NONE:
                        return [] if atom_list else None
                    result = self.window.get_property(
                        prop, 0, 0, 2 ** 24,  # 最大 16MB
                    )
                    self.window.delete_property(prop)
                    if result is None or result.value is None:
                        return [] if atom_list else None
                    if atom_list:
                        return [
                            self.disp.get_atom_name(a)
                            for a in result.value
                        ]
                    return bytes(result.value)
                elif ev.type == X.SelectionRequest:
                    self._handle_selection_request(ev)
                elif ev.type == X.SelectionClear:
                    self.is_owner = False
            time.sleep(0.01)
        return [] if atom_list else None

    def handle_events(self, timeout: float = 0.1):
        """X11 イベントを処理する (SelectionRequest に応答)。"""
        while self.disp.pending_events():
            ev = self.disp.next_event()
            if ev.type == X.SelectionRequest:
                self._handle_selection_request(ev)
            elif ev.type == X.SelectionClear:
                self.is_owner = False

    def _handle_selection_request(self, ev):
        """SelectionRequest イベントに応答する。"""
        try:
            response = event.SelectionNotify(
                time=ev.time,
                requestor=ev.requestor,
                selection=ev.selection,
                target=ev.target,
                property=ev.property or ev.target,
            )

            if ev.target == self.TARGETS:
                # 利用可能なターゲットを返す
                targets = [self.TARGETS, self.IMAGE_PNG]
                ev.requestor.change_property(
                    response.property, self.ATOM, 32,
                    targets,
                )
            elif ev.target == self.IMAGE_PNG and self.png_data:
                # PNG データを返す — 大きいデータはチャンク分割
                self._send_data_chunked(
                    ev.requestor, response.property,
                    self.IMAGE_PNG, self.png_data,
                )
            else:
                # サポートしないターゲット
                response.property = X.NONE

            ev.requestor.send_event(response)
            self.disp.flush()
        except Exception as e:
            log(f"⚠️ SelectionRequest failed (requestor gone?): {e}")

    def _send_data_chunked(self, requestor, prop, data_type, data):
        """大きなデータをチャンク分割して X11 property に書き込む。

        python-xlib の change_property は内部で struct.pack('H', n) を使い、
        65535 バイトを超えるとオーバーフローする。チャンク分割で回避する。
        """
        CHUNK_SIZE = 60000  # 65535 未満に収める
        if len(data) <= CHUNK_SIZE:
            requestor.change_property(prop, data_type, 8, data)
        else:
            # 最初のチャンクで property を作成 (mode=Replace)
            requestor.change_property(prop, data_type, 8, data[:CHUNK_SIZE])
            # 残りを追記 (mode=Append) — flush は最後に1回だけ
            offset = CHUNK_SIZE
            while offset < len(data):
                chunk = data[offset:offset + CHUNK_SIZE]
                requestor.change_property(
                    prop, data_type, 8, chunk,
                    mode=2,  # PropModeAppend
                )
                offset += CHUNK_SIZE
            self.disp.flush()
            log(f"📦 チャンク送信完了 ({len(data)} bytes, {(len(data) // CHUNK_SIZE) + 1} chunks)")

    def close(self):
        self.disp.close()


def main():
    log(f"clip-png-daemon started (DISPLAY={DISPLAY_NAME}, poll={POLL_INTERVAL}s)")

    owner = ClipboardOwner(DISPLAY_NAME)
    last_hash = ""

    def shutdown(signum, frame):
        log("shutting down")
        owner.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    while True:
        # 常に X11 イベントを処理 (selection request に応答するため)
        owner.handle_events()

        # クリップボード監視 (xclip subprocess)
        targets = get_clipboard_targets(DISPLAY_NAME)

        if "image/bmp" in targets and "image/png" not in targets:
            bmp_data = get_clipboard_bmp(DISPLAY_NAME)
            if bmp_data:
                bmp_hash = hashlib.md5(bmp_data).hexdigest()
                if bmp_hash != last_hash:
                    last_hash = bmp_hash
                    png_data = convert_bmp_to_png(bmp_data)
                    if png_data:
                        owner.own_clipboard(png_data)
                        size_kb = len(png_data) // 1024
                        log(f"✅ BMP→PNG 変換完了 ({size_kb}KB)")
                    else:
                        log("⚠️ PNG 変換失敗")

        # 次のポーリングまで、イベント処理を続けながら待機
        wait_until = time.monotonic() + POLL_INTERVAL
        while time.monotonic() < wait_until:
            owner.handle_events()
            time.sleep(0.05)  # 50ms ごとにイベントチェック


if __name__ == "__main__":
    main()
