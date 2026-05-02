#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- hgk/api/tests/ テスト
# PURPOSE: ls_client のユニットテスト — ls_daemon.json フォールバック + IDE LS 検出
"""ls_client テスト。

daemon (ls_daemon.json) 優先 → IDE LS (/proc+ss) フォールバックの動作を検証する。
"""

from __future__ import annotations

import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# テスト対象モジュール
import hgk.api.ls_client as ls_client


@pytest.fixture(autouse=True)
def _reset_cache():
    """各テスト前にキャッシュをクリアする。"""
    ls_client._cache = {}
    ls_client._cache_ts = 0.0
    yield
    ls_client._cache = {}
    ls_client._cache_ts = 0.0


class TestLoadDaemonInfo:
    """_load_daemon_info() のテスト。"""

    def test_file_missing(self, tmp_path):
        """ファイルが存在しない場合に None を返すこと。"""
        with patch.object(ls_client, "DAEMON_INFO_PATH", tmp_path / "nonexistent.json"):
            result = ls_client._load_daemon_info()
            assert result is None

    def test_valid_single_entry(self, tmp_path):
        """単一辞書形式の JSON から接続パラメータを返すこと。"""
        info_path = tmp_path / "ls_daemon.json"
        info_path.write_text(json.dumps({
            "pid": os.getpid(),  # 自プロセス = 確実に生存
            "port": 12345,
            "csrf": "test_csrf_token",
            "workspace": "nonstd_hgk_0",
            "is_https": True,
        }))
        with patch.object(ls_client, "DAEMON_INFO_PATH", info_path):
            result = ls_client._load_daemon_info()
            assert result is not None
            assert result["pid"] == str(os.getpid())
            assert result["port"] == 12345
            assert result["csrf"] == "test_csrf_token"
            assert result["source"] == "daemon"
            assert result["base_url"] == "http://127.0.0.1:12345"

    def test_valid_list_entry(self, tmp_path):
        """リスト形式 (プール) の JSON から最初の生存エントリを返すこと。"""
        info_path = tmp_path / "ls_daemon.json"
        info_path.write_text(json.dumps([
            {"pid": 999999, "port": 11111, "csrf": "dead"},  # 存在しない PID
            {"pid": os.getpid(), "port": 22222, "csrf": "alive"},  # 生存
        ]))
        with patch.object(ls_client, "DAEMON_INFO_PATH", info_path):
            result = ls_client._load_daemon_info()
            assert result is not None
            assert result["port"] == 22222
            assert result["csrf"] == "alive"

    def test_dead_pid_returns_none(self, tmp_path):
        """全 PID が死亡している場合に None を返すこと。"""
        info_path = tmp_path / "ls_daemon.json"
        info_path.write_text(json.dumps([
            {"pid": 999998, "port": 11111, "csrf": "dead1"},
            {"pid": 999999, "port": 22222, "csrf": "dead2"},
        ]))
        with patch.object(ls_client, "DAEMON_INFO_PATH", info_path):
            result = ls_client._load_daemon_info()
            assert result is None

    def test_corrupted_json(self, tmp_path):
        """不正な JSON の場合に None を返すこと。"""
        info_path = tmp_path / "ls_daemon.json"
        info_path.write_text("{invalid json")
        with patch.object(ls_client, "DAEMON_INFO_PATH", info_path):
            result = ls_client._load_daemon_info()
            assert result is None


class TestGetParams:
    """_get_params() のフォールバック動作テスト。"""

    def test_daemon_priority(self, tmp_path):
        """daemon.json が優先され、_detect_ls_params が呼ばれないこと。"""
        info_path = tmp_path / "ls_daemon.json"
        info_path.write_text(json.dumps({
            "pid": os.getpid(),
            "port": 33333,
            "csrf": "daemon_token",
        }))
        with patch.object(ls_client, "DAEMON_INFO_PATH", info_path), \
             patch.object(ls_client, "_detect_ls_params") as mock_detect:
            params = ls_client._get_params()
            assert params["port"] == 33333
            assert params["source"] == "daemon"
            mock_detect.assert_not_called()

    def test_fallback_to_proc(self, tmp_path):
        """daemon.json が無い場合に _detect_ls_params にフォールバックすること。"""
        with patch.object(ls_client, "DAEMON_INFO_PATH", tmp_path / "nonexistent.json"), \
             patch.object(ls_client, "_detect_ls_params", return_value={
                 "pid": "12345", "port": 44444, "csrf": "ide_token",
                 "base_url": "http://127.0.0.1:44444",
             }) as mock_detect:
            params = ls_client._get_params()
            assert params["port"] == 44444
            mock_detect.assert_called_once()


class TestGetIDEStatus:
    """get_ide_status() のテスト。"""

    def test_source_daemon(self, tmp_path):
        """daemon 経由接続時に source='daemon' が返ること。"""
        info_path = tmp_path / "ls_daemon.json"
        info_path.write_text(json.dumps({
            "pid": os.getpid(),
            "port": 55555,
            "csrf": "status_token",
        }))
        with patch.object(ls_client, "DAEMON_INFO_PATH", info_path):
            status = ls_client.get_ide_status()
            assert status["status"] == "connected"
            assert status["source"] == "daemon"
            assert status["port"] == 55555

    def test_source_ide(self):
        """IDE LS 経由接続時に source='ide' が返ること。"""
        with patch.object(ls_client, "_get_params", return_value={
            "pid": "12345", "port": 66666, "csrf": "ide_csrf",
        }):
            status = ls_client.get_ide_status()
            assert status["status"] == "connected"
            assert status["source"] == "ide"

    def test_disconnected(self):
        """LS が見つからない場合に disconnected が返ること。"""
        with patch.object(ls_client, "_get_params", side_effect=RuntimeError("LS not found")):
            status = ls_client.get_ide_status()
            assert status["status"] == "disconnected"
            assert "LS not found" in status["error"]
