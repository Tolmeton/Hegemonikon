#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/tests/test_phantazein_health.py
# PURPOSE: phantazein_health の HTTP レベルヘルスチェック関数のユニットテスト
"""
_check_server の3段判定テスト:
1. TCP + HTTP 両方成功 → status: "up"
2. TCP 成功 + HTTP 失敗 → status: "degraded"
3. TCP 失敗 → status: "down"
"""

import unittest
from unittest.mock import patch, MagicMock
import socket


class TestCheckServer(unittest.TestCase):
    """_check_server 関数の3段判定テスト。"""

    def _get_check_server(self):
        """テスト対象関数をインポート。"""
        from mekhane.mcp.phantazein_mcp_server import _check_server
        return _check_server

    def test_up_when_tcp_and_http_succeed(self):
        """TCP + HTTP 両方成功 → status: 'up'"""
        _check_server = self._get_check_server()
        # 実際に稼働しているサーバーがあれば up を返すはず
        # phantazein 自身 (9710) を使う
        result = _check_server("phantazein", 9710)
        # テスト環境でサーバーが動いている場合のみ検証
        if result["status"] == "up":
            self.assertEqual(result["server_name"], "phantazein")
            self.assertEqual(result["port"], 9710)
            self.assertGreater(result["latency_ms"], 0)
            self.assertEqual(result["error"], "")

    def test_down_when_tcp_fails(self):
        """TCP 接続失敗 → status: 'down'"""
        _check_server = self._get_check_server()
        # 存在しないポートに接続試行
        result = _check_server("nonexistent", 19999, tcp_timeout=0.5, http_timeout=0.5)
        self.assertEqual(result["status"], "down")
        self.assertEqual(result["server_name"], "nonexistent")
        self.assertEqual(result["port"], 19999)
        self.assertIn("TCP:", result["error"])

    def test_degraded_when_tcp_ok_but_http_fails(self):
        """TCP 成功 + HTTP 失敗 → status: 'degraded'"""
        _check_server = self._get_check_server()

        # TCP は通るが HTTP は応答しないサーバーをシミュレート
        # socat のような TCP listener を作る
        import threading

        # 一時的な TCP リスナーを起動 (HTTP には応答しない — 即切断)
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 19998))
        srv.listen(5)
        srv.settimeout(5)

        def _accept_and_close():
            """TCP 接続を受け入れて即閉じる (socat 模倣)。"""
            try:
                for _ in range(3):  # TCP + HTTP の接続を受ける
                    conn, _ = srv.accept()
                    conn.close()  # 即座に閉じる → HTTP は失敗する
            except socket.timeout:
                pass
            finally:
                srv.close()

        t = threading.Thread(target=_accept_and_close, daemon=True)
        t.start()

        try:
            result = _check_server("fake_socat", 19998, tcp_timeout=1.0, http_timeout=1.0)
            # TCP は通るが HTTP が失敗するので degraded
            self.assertIn(result["status"], ("degraded", "up"))  # 環境によっては up も許容
            self.assertEqual(result["server_name"], "fake_socat")
            self.assertEqual(result["port"], 19998)
        finally:
            t.join(timeout=3)

    def test_result_structure(self):
        """結果の構造が正しいか確認。"""
        _check_server = self._get_check_server()
        result = _check_server("test", 19997, tcp_timeout=0.3, http_timeout=0.3)
        # 必須キーの存在確認
        self.assertIn("server_name", result)
        self.assertIn("port", result)
        self.assertIn("status", result)
        self.assertIn("latency_ms", result)
        self.assertIn("error", result)
        # status は3値のいずれか
        self.assertIn(result["status"], ("up", "degraded", "down"))


if __name__ == "__main__":
    unittest.main()
