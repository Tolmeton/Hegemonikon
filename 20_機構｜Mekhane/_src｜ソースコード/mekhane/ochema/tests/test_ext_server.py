#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/tests/ テスト
# PURPOSE: DummyExtServer ユニットテスト


from __future__ import annotations
import socket
import struct
import time
import urllib.request

import pytest

from mekhane.ochema.ext_server import DummyExtServer, _AuthHandler


# --- ヘルパー ---

_USS_SUBSCRIBE = "/exa.extension_server_pb.ExtensionServerService/SubscribeToUnifiedStateSyncTopic"


def _make_subscribe_body(topic: str) -> bytes:
    """Subscribe RPC 用の ConnectRPC フレーム付きリクエストボディを生成。"""
    topic_bytes = topic.encode("utf-8")
    # protobuf: field 1, wire type 2 (length-delimited)
    proto = b'\x0a' + bytes([len(topic_bytes)]) + topic_bytes
    # ConnectRPC frame: flags=0, length (4 bytes big endian)
    return struct.pack('>BI', 0, len(proto)) + proto


class TestDummyExtServer:
    """DummyExtServer のライフサイクルとリクエスト処理テスト。"""

    def test_start_stop(self):
        """起動→停止のライフサイクルが正常に動作すること。"""
        srv = DummyExtServer()
        assert not srv.is_alive
        assert srv.port == 0

        srv.start()
        assert srv.is_alive
        assert srv.port > 0

        srv.stop()
        assert not srv.is_alive
        assert srv.port == 0

    def test_double_start_raises(self):
        """二重起動で RuntimeError が発生すること。"""
        srv = DummyExtServer()
        srv.start()
        try:
            with pytest.raises(RuntimeError, match="already running"):
                srv.start()
        finally:
            srv.stop()

    def test_post_returns_200_empty_proto(self):
        """POST リクエストに HTTP 200 / 空の application/proto を返すこと。"""
        srv = DummyExtServer()
        srv.start()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{srv.port}/exa.extension_server_pb.ExtensionServerService/LanguageServerStarted",
                data=b"{}",
                method="POST",
                headers={"Content-Type": "application/proto"},
            )
            with urllib.request.urlopen(req, timeout=3) as resp:
                assert resp.status == 200
                body = resp.read()
                assert body == b""
        finally:
            srv.stop()

    def test_csrf_is_generated(self):
        """CSRF トークンが自動生成されること。"""
        srv = DummyExtServer()
        assert len(srv.csrf) == 32  # uuid4().hex

    def test_repr(self):
        """repr が正常に動作すること。"""
        srv = DummyExtServer()
        assert "DummyExtServer" in repr(srv)
        assert "alive=False" in repr(srv)


class TestSubscribeConnectionHolding:
    """M-2: Subscribe 接続維持と graceful shutdown のテスト。"""

    def test_subscribe_holds_connection(self):
        """C-1/C-2: Subscribe が接続を維持し、即座に EOF を返さないこと。

        旧実装では即 EOF → 瞬時に返っていた。新実装では接続が維持される。
        """
        srv = DummyExtServer()
        srv.start()
        try:
            body = _make_subscribe_body("uss-oauth")
            # ソケットを直接使って接続タイムアウトを細かく制御
            sock = socket.create_connection(("127.0.0.1", srv.port), timeout=5)
            try:
                # HTTP POST リクエストを手動送信
                request = (
                    f"POST {_USS_SUBSCRIBE} HTTP/1.1\r\n"
                    f"Host: 127.0.0.1:{srv.port}\r\n"
                    f"Content-Type: application/connect+proto\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"\r\n"
                ).encode() + body
                sock.sendall(request)

                # レスポンスヘッダを読む (200 OK が返るはず)
                sock.settimeout(3)
                header_data = sock.recv(4096)
                assert b"200" in header_data, f"Expected 200 in response: {header_data!r}"

                # 2秒待っても追加データが来ない = 接続が維持されている
                # (旧実装では即 EOF チャンク "0\r\n\r\n" が送られていた)
                sock.settimeout(2)
                try:
                    more_data = sock.recv(4096)
                    # データが返ってきた場合、それが EOF でないことを確認
                    # EOF = "0\r\n\r\n" だけの場合は旧動作
                    if more_data:
                        assert more_data != b"0\r\n\r\n", "Server sent immediate EOF (old behavior)"
                except socket.timeout:
                    pass  # タイムアウト = 接続維持中 ✅ (期待される動作)
            finally:
                sock.close()
        finally:
            srv.stop()

    def test_graceful_shutdown(self):
        """C-2: stop() が接続維持中のハンドラースレッドを即座に終了させること。"""
        srv = DummyExtServer()
        srv.start()
        try:
            body = _make_subscribe_body("uss-oauth")
            # バックグラウンドで Subscribe 接続を開く
            sock = socket.create_connection(("127.0.0.1", srv.port), timeout=5)
            request = (
                f"POST {_USS_SUBSCRIBE} HTTP/1.1\r\n"
                f"Host: 127.0.0.1:{srv.port}\r\n"
                f"Content-Type: application/connect+proto\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"\r\n"
            ).encode() + body
            sock.sendall(request)
            sock.settimeout(2)
            sock.recv(4096)  # ヘッダ読み飛ばし
            time.sleep(0.5)  # 接続維持ループに入るまで待つ

            # C-2: stop() → _shutdown_event.set() → ループ脱出 → shutdown 完了
            t0 = time.monotonic()
            srv.stop()
            elapsed = time.monotonic() - t0

            # 30秒 (pollタイムアウト) 待たずに停止すること — 2秒以内で十分
            assert elapsed < 5.0, f"Shutdown took too long: {elapsed:.1f}s (expected < 5s)"
            assert not srv.is_alive
            sock.close()
        except Exception:
            srv.stop()
            raise

    def test_unknown_topic_returns_empty_initial(self):
        """M-3: 未知トピックの Subscribe で空の initial_state が返ること。"""
        srv = DummyExtServer()
        srv.start()
        try:
            body = _make_subscribe_body("uss-settings")
            sock = socket.create_connection(("127.0.0.1", srv.port), timeout=5)
            try:
                request = (
                    f"POST {_USS_SUBSCRIBE} HTTP/1.1\r\n"
                    f"Host: 127.0.0.1:{srv.port}\r\n"
                    f"Content-Type: application/connect+proto\r\n"
                    f"Content-Length: {len(body)}\r\n"
                    f"\r\n"
                ).encode() + body
                sock.sendall(request)

                sock.settimeout(3)
                header_data = sock.recv(4096)
                # 200 OK が返る
                assert b"200" in header_data
                # 何かしらのデータが含まれている (空 initial_state)
                assert len(header_data) > 20, "Expected initial_state data in response"
            finally:
                sock.close()
        finally:
            srv.stop()


class TestExtractTopicVarint:
    """M-1: _extract_topic の varint デコーダテスト。"""

    def test_short_topic(self):
        """127バイト以下のトピック名が正しく抽出されること。"""
        handler = _AuthHandler.__new__(_AuthHandler)
        topic = "uss-oauth"
        topic_bytes = topic.encode()
        proto = b'\x0a' + bytes([len(topic_bytes)]) + topic_bytes
        body = struct.pack('>BI', 0, len(proto)) + proto
        assert handler._extract_topic(body) == topic

    def test_long_topic_varint(self):
        """128バイト以上のトピック名 (2バイト varint) が正しく抽出されること。"""
        handler = _AuthHandler.__new__(_AuthHandler)
        topic = "a" * 200  # 200バイトのトピック名
        topic_bytes = topic.encode()
        # varint エンコード: 200 = 0xC8 → [0xC8, 0x01]
        varint = bytearray()
        n = len(topic_bytes)
        while n > 0x7F:
            varint.append((n & 0x7F) | 0x80)
            n >>= 7
        varint.append(n)
        proto = b'\x0a' + bytes(varint) + topic_bytes
        body = struct.pack('>BI', 0, len(proto)) + proto
        assert handler._extract_topic(body) == topic

    def test_empty_body(self):
        """空ボディで空文字列が返ること。"""
        handler = _AuthHandler.__new__(_AuthHandler)
        assert handler._extract_topic(b"") == ""
        assert handler._extract_topic(b"\x00\x00") == ""
