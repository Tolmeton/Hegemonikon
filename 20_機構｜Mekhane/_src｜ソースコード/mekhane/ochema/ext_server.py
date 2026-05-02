# PROOF: [L2/インフラ] <- mekhane/ochema/ IDE依存排除のためのダミー ExtServer
# PURPOSE: IDE なしで Non-Standalone LS を起動するためのスタブ ExtServer
# REASON: LS は ext_server_port へ起動時通知を送る。応答がないと SIGSEGV する。
from __future__ import annotations
from typing import Optional
"""Dummy Extension Server for Non-Standalone LS.

IDE が起動していない環境でも LS を安定稼働させるための最小限サーバー。
uss-oauth トピックに対しては state.vscdb から認証データを返す。
その他の RPC は空の 200/proto 応答を返す。

Proto Schema (binary reverse-engineered):
    UnifiedStateSyncUpdate {
        Topic initial_state = 1;  // oneof update_type
    }
    Topic {
        map<string, Row> data = 1;
    }
    Row {
        Primitive value = 1;
        int64 e_tag = 2;
    }

    state.vscdb の各値は Base64 エンコードされた Topic proto。
    DummyExtServer は全値を decode → 連結 → initial_state に入れる。

ConnectRPC ServerStreaming:
    [flag:1][length:4][proto_payload] + [flag:2][length:4][trailer_json]

Usage:
    server = DummyExtServer()
    server.start()
    print(server.port)
    server.stop()
"""


import base64
import http.server
import logging
import socket
import socketserver
import sqlite3
import struct
import threading
import time
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Paths ---
_STATE_DB = Path.home() / ".config/Antigravity/User/globalStorage/state.vscdb"
_USS_SUBSCRIBE = "/exa.extension_server_pb.ExtensionServerService/SubscribeToUnifiedStateSyncTopic"


# --- Proto encoding helpers ---

def _encode_varint(value: int) -> bytes:
    """Protobuf varint をエンコード。"""
    parts = []
    while value > 0x7F:
        parts.append((value & 0x7F) | 0x80)
        value >>= 7
    parts.append(value & 0x7F)
    return bytes(parts)


def _encode_proto_string(field_num: int, value: str) -> bytes:
    """Protobuf string field をエンコード (wire type 2)。"""
    data = value.encode("utf-8")
    tag = (field_num << 3) | 2
    return bytes([tag]) + _encode_varint(len(data)) + data


def _encode_proto_message(field_num: int, inner: bytes) -> bytes:
    """Protobuf nested message field をエンコード (wire type 2)。"""
    tag = (field_num << 3) | 2
    return bytes([tag]) + _encode_varint(len(inner)) + inner


def _encode_proto_varint(field_num: int, value: int) -> bytes:
    """Protobuf varint field をエンコード (wire type 0)。"""
    tag = (field_num << 3) | 0
    return bytes([tag]) + _encode_varint(value)


def _connectrpc_frame(payload: bytes, flags: int = 0) -> bytes:
    """ConnectRPC envelope frame を構築。

    Format: [flags:1byte][length:4bytes][payload]
    flags=0: data frame, flags=2: trailer frame
    """
    return struct.pack(">BI", flags, len(payload)) + payload


# --- uss-oauth response builder ---

def _build_uss_oauth_response(db_path: Path | str | None = None) -> bytes:
    """state.vscdb から認証データを読み取り、uss-oauth 用 proto を構築。

    Returns:
        UnifiedStateSyncUpdate proto バイナリ。失敗時は空 bytes。
    """
    try:
        # IDE が flock でロック中でも読めるように immutable=1 URI mode で接続
        # immutable=1: read-only, WAL/SHM なし, ロック不要
        target_db = db_path or _STATE_DB
        db_uri = f"file:{target_db}?mode=ro&immutable=1"
        db = sqlite3.connect(db_uri, uri=True, timeout=5.0)

        # uss-oauth に必要な全キーを取得
        USS_PREFIX = "antigravityUnifiedStateSync."
        all_rows = db.execute(
            "SELECT key, value FROM ItemTable WHERE key LIKE ?",
            (f"{USS_PREFIX}%",),
        ).fetchall()
        db.close()

        if not all_rows:
            logger.warning("No antigravityUnifiedStateSync keys found in state.vscdb")
            return b""

        # state.vscdb の各値は Base64 エンコードされた Topic proto (map<string, Row>)
        # 全キーの Topic proto を連結してマージし、
        # UnifiedStateSyncUpdate.initial_state (field 1) に入れる
        topic_bytes = b""
        key_count = 0
        key_names = []
        for db_key, value in all_rows:
            topic_key = db_key[len(USS_PREFIX):]
            if not topic_key or not value:
                continue

            # Base64 decode → Topic proto binary
            try:
                if isinstance(value, str):
                    decoded = base64.b64decode(value)
                elif isinstance(value, bytes):
                    decoded = value
                else:
                    continue
            except Exception:  # Intentional Catch-All (Network/Base64)  # noqa: BLE001
                logger.warning("Failed to base64 decode key %s, skipping", topic_key)
                continue

            # Topic proto を連結 (proto repeated field merger)
            topic_bytes += decoded
            key_count += 1
            key_names.append(topic_key)

        # UnifiedStateSyncUpdate.initial_state (field 1, message) = Topic
        update = _encode_proto_message(1, topic_bytes)

        # Google LS Change Detection (Mitigation)
        # 通常、uss-oauth のトピック数は 10〜30 程度。
        # もしこれが極端に少ない場合や 0 の場合、LS 側のフォーマット変更や
        # status 同期仕様の変更が疑われるためアラートを出す。
        if key_count < 5:
            logger.warning(
                "🚨 [Mitigation] Suspiciously few uss-oauth topics (%d). "
                "Google LS may have changed its state sync format.",
                key_count,
            )

        logger.info(
            "Built uss-oauth response: %d bytes proto (%d topics: %s)",
            len(update), key_count, ", ".join(key_names[:5]) + ("..." if key_count > 5 else ""),
        )
        return update

    except Exception as e:  # Intentional Catch-All (Response Build)  # noqa: BLE001
        logger.error("Failed to build uss-oauth response: %s", e)
        return b""


# --- HTTP Handler ---

# PURPOSE: ExtServer RPC を処理するハンドラー。uss-oauth は認証データを返し、他は空応答。
class _AuthHandler(http.server.BaseHTTPRequestHandler):
    """Non-Standalone LS 用 ExtServer ハンドラー。

    uss-oauth トピックの SubscribeToUnifiedStateSyncTopic に対して
    state.vscdb の認証データを返す。他の RPC は空応答。
    """

    # クラス変数
    proxy_target: str = ""
    # HTTP/1.1 を使用（chunked transfer encoding に必要）
    protocol_version = "HTTP/1.1"
    # target_db (DI)
    target_db: Path | str | None = None
    # C-2: graceful shutdown 用イベント。stop() で set し、接続維持ループを脱出させる
    _shutdown_event: threading.Event = threading.Event()
    # C-1: Subscribe 接続の最大保持時間 (秒)。スレッド枯渇防止
    _max_hold_seconds: float = 3600.0

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        # uss-oauth トピックの SubscribeToUnifiedStateSyncTopic
        # NOTE: Subscribe は ServerStreaming RPC。接続を維持しないと LS が即再接続し
        #       無限ループになる (47回/秒, 26MB/秒のログ生成 → OOM の原因)。
        #       初回データ送信後、LS が切断するまで接続を保持する。
        if self.path == _USS_SUBSCRIBE:
            topic = self._extract_topic(body)
            logger.debug(
                "USS Subscribe: topic=%s",
                topic,
            )
            
            self.send_response(200)
            self.send_header("Content-Type", "application/connect+proto")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            if topic == "uss-oauth":
                proto_payload = _build_uss_oauth_response(db_path=self.target_db)
                if proto_payload:
                    # data frame chunk
                    data_frame = _connectrpc_frame(proto_payload, flags=0)
                    self._write_chunk(data_frame)
                    # L-2: ログレベルを DEBUG に統一 (初回1回でも一貫性のため)
                    logger.debug("USS uss-oauth: sent %d bytes, holding connection", len(proto_payload))
            else:
                # M-3: 未知トピックにも空の initial_state を返す。
                # データなしで接続維持すると LS の初期化がブロックされる可能性がある。
                empty_topic = b'\x0a\x00'  # Topic { data = {} } (空 map)
                empty_initial = b'\x0a' + bytes([len(empty_topic)]) + empty_topic
                data_frame = _connectrpc_frame(empty_initial, flags=0)
                self._write_chunk(data_frame)
                logger.debug("USS %s: sent empty initial_state, holding connection", topic)

            # ServerStreaming: 接続を維持する。LS が切断するまで待機。
            # EOF (trailer + 空チャンク) を即座に送ると LS が「切断された」と認識し再接続する。
            # C-1: max_hold_seconds で最大接続時間を制限 (スレッド枯渇防止)
            # C-2: _shutdown_event で graceful shutdown を実現
            try:
                poll_interval = 30.0  # recv タイムアウト (秒)
                self.connection.settimeout(poll_interval)
                start_time = time.monotonic()
                while not self._shutdown_event.is_set():
                    # C-1: 最大保持時間チェック
                    elapsed = time.monotonic() - start_time
                    if elapsed >= self._max_hold_seconds:
                        logger.debug("USS Subscribe: max_hold_seconds (%.0f) reached", self._max_hold_seconds)
                        break
                    try:
                        # LS がソケットを閉じたか確認 (recv が 0 bytes = 切断)
                        data = self.connection.recv(1, socket.MSG_PEEK)
                        if not data:
                            break  # LS が切断した
                    except socket.timeout:
                        pass  # タイムアウト = まだ接続中。継続
                    except (OSError, ConnectionError):
                        break  # ソケットエラー = 切断
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass  # 接続が既に閉じている

            # LS 切断後にクリーンアップ (trailer + EOF)
            try:
                trailer = _connectrpc_frame(b'{}', flags=2)
                self._write_chunk(trailer)
                self.wfile.write(b"0\r\n\r\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass  # 既に切断済みなら無視
            logger.debug("USS Subscribe connection closed for topic=%s", topic)
            return

        # プロキシモード
        if self.proxy_target:
            try:
                import urllib.request
                url = f"{self.proxy_target}{self.path}"
                req = urllib.request.Request(
                    url, data=body, method="POST",
                    headers={
                        "Content-Type": content_type or "application/connect+proto",
                    },
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    resp_body = resp.read()
                    self.send_response(resp.status)
                    for key, val in resp.getheaders():
                        if key.lower() not in ("transfer-encoding", "connection"):
                            self.send_header(key, val)
                    self.end_headers()
                    self.wfile.write(resp_body)
                    return
            except Exception as _e:  # Intentional Catch-All (urllib/network)  # noqa: BLE001
                logger.debug("Ignored exception: %s", _e)

        # フォールバック: リクエストの Content-Type に合わせた空応答
        self.send_response(200)
        self.send_header("Content-Type", content_type or "application/connect+proto")
        self.end_headers()
        self.wfile.write(b"")

    def _write_chunk(self, data: bytes) -> None:
        """HTTP/1.1 chunked transfer encoding で 1 チャンクを書き込む。"""
        self.wfile.write(f"{len(data):x}\r\n".encode())
        self.wfile.write(data)
        self.wfile.write(b"\r\n")

    def _extract_topic(self, body: bytes) -> str:
        """ConnectRPC frame からトピック名 (field 1 string) を抽出。

        M-1: protobuf varint デコーダを使用。127バイト超のトピック名にも対応。
        """
        if len(body) < 6:
            return ""
        try:
            # Skip ConnectRPC frame header (5 bytes)
            proto = body[5:]
            if not proto or proto[0] != 0x0a:  # field 1, wire type 2
                return ""
            # M-1: varint デコード (最大5バイト)
            str_len = 0
            shift = 0
            idx = 1
            while idx < len(proto):
                b = proto[idx]
                str_len |= (b & 0x7F) << shift
                idx += 1
                if not (b & 0x80):
                    break
                shift += 7
                if shift >= 35:  # 安全弁: 5バイト超の varint は異常
                    return ""
            return proto[idx:idx + str_len].decode("utf-8", errors="replace")
        except (IndexError, UnicodeDecodeError, ValueError) as _e:
            logger.debug("Ignored exception: %s", _e)
            return ""

    def log_message(self, format: str, *args: object) -> None:
        pass


# --- Server classes ---

class _ReusableTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


# PURPOSE: IDE 不在時に LS が必要とする ExtServer。認証トークンを state.vscdb から提供。
class DummyExtServer:
    """Non-Standalone LS 用の Extension Server。

    バックグラウンドスレッドで HTTP サーバーを起動し、
    uss-oauth トピックに対して state.vscdb の認証データを返す。

    Attributes:
        port: サーバーのリスニングポート
        csrf: 生成された CSRF トークン
    """
    def __init__(self, proxy_target: str = "", db_path: Path | str | None = None) -> None:
        self._server: Optional[_ReusableTCPServer] = None
        self._thread: Optional[threading.Thread] = None
        self.port: int = 0
        self.csrf: str = uuid.uuid4().hex
        self._proxy_target = proxy_target
        self._db_path = db_path

    def start(self) -> None:
        """バックグラウンドスレッドでサーバーを起動する。"""
        if self._server is not None:
            raise RuntimeError("DummyExtServer is already running")

        # C-2: 再起動時に shutdown_event をリセット
        _AuthHandler._shutdown_event.clear()

        # 起動ごとに新しいハンドラークラスを作成して状態を保持させる
        class HandlerWithConfig(_AuthHandler):
            proxy_target = self._proxy_target
            target_db = self._db_path

        self._server = _ReusableTCPServer(("127.0.0.1", 0), HandlerWithConfig)
        self.port = self._server.server_address[1]

        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="dummy-ext-server",
        )
        self._thread.start()

        logger.info(
            "DummyExtServer started: port=%d",
            self.port,
        )

    def stop(self) -> None:
        """サーバーを停止する。

        C-2: _shutdown_event を set してから shutdown を呼ぶことで、
        接続維持ループ (do_POST の while ループ) を即座に脱出させ、
        graceful shutdown を実現する。
        """
        if self._server is not None:
            # C-2: まず接続維持ループを停止させる
            _AuthHandler._shutdown_event.set()
            self._server.shutdown()
            self._server.server_close()
            logger.info("DummyExtServer stopped (port=%d)", self.port)
            self._server = None
            self._thread = None
            self.port = 0

    @property
    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def __del__(self) -> None:
        try:
            self.stop()
        except OSError as _e:
            logger.debug("Ignored exception: %s", _e)

    def __repr__(self) -> str:
        return (
            f"DummyExtServer(port={self.port}, "
            f"alive={self.is_alive})"
        )


# CLI 起動
if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 50100
    server = _ReusableTCPServer(("127.0.0.1", port), _AuthHandler)
    print(f"DummyExtServer listening on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
