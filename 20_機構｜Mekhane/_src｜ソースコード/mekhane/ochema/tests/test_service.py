#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/tests/ テスト
# PURPOSE: OchemaService ユニットテスト
"""
OchemaService unit tests.

These tests verify the service layer's routing, singleton pattern,
and model registry without requiring actual LS or Cortex connections.
"""


from __future__ import annotations
import json
from unittest.mock import patch, MagicMock


# --- Singleton ---


class TestSingleton:
    """OchemaService singleton pattern tests."""

    def setup_method(self):
        """Reset singleton before each test."""
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()

    def teardown_method(self):
        """Reset singleton after each test."""
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()

    def test_singleton_identity(self):
        """get() returns the same instance."""
        from mekhane.ochema.service import OchemaService
        a = OchemaService.get()
        b = OchemaService.get()
        assert a is b

    def test_reset_clears_singleton(self):
        """reset() creates a fresh instance on next get()."""
        from mekhane.ochema.service import OchemaService
        a = OchemaService.get()
        OchemaService.reset()
        b = OchemaService.get()
        assert a is not b


# --- Model Routing ---


class TestModelRouting:
    """Model routing logic tests."""

    def setup_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()
        self.svc = OchemaService.get()

    def teardown_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()

    def test_claude_sonnet_routes_to_chat(self):
        """claude-sonnet should route to Cortex chat."""
        assert self.svc._is_claude_model("claude-sonnet") is True

    def test_claude_opus_routes_to_chat(self):
        """claude-opus should route to Cortex chat."""
        assert self.svc._is_claude_model("claude-opus") is True

    def test_proto_model_routes_to_chat(self):
        """Proto enum models should route to Cortex chat."""
        assert self.svc._is_claude_model("MODEL_PLACEHOLDER_M35") is True
        assert self.svc._is_claude_model("MODEL_PLACEHOLDER_M26") is True

    def test_gemini_routes_to_cortex(self):
        """Gemini models should NOT route to chat."""
        assert self.svc._is_claude_model("gemini-3-flash-preview") is False
        assert self.svc._is_claude_model("gemini-3.1-pro-preview") is False
        assert self.svc._is_claude_model("gemini-3-pro-preview") is False

    def test_resolve_model_config_id(self):
        """Friendly names resolve to model_config_id (proto enum)."""
        # CLAUDE_MODEL_MAP maps to MODEL_PLACEHOLDER_* proto enums
        assert self.svc._resolve_model_config_id("claude-sonnet") == "MODEL_PLACEHOLDER_M35"
        assert self.svc._resolve_model_config_id("claude-opus") == "MODEL_PLACEHOLDER_M26"
        assert self.svc._resolve_model_config_id("claude-sonnet-4-5") == "MODEL_PLACEHOLDER_M35"

    def test_resolve_model_config_id_unknown_passes_through(self):
        """Unknown models pass through unchanged."""
        assert self.svc._resolve_model_config_id("custom-model") == "custom-model"




# --- Models Registry ---


class TestModelsRegistry:
    """Model registry tests."""
    from unittest.mock import patch

    def setup_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()
        self.svc = OchemaService.get()

    def teardown_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()

    @patch("mekhane.ochema.cortex_client.CortexClient.fetch_available_models", return_value=[{"name": "models/gemini-3-flash-preview"}, {"name": "models/cortex-chat"}])
    def test_models_returns_dict(self, mock_fetch):
        """models() returns expected structure."""
        result = self.svc.models()
        assert "models" in result
        assert "default" in result
        assert "cortex_available" in result

    @patch("mekhane.ochema.cortex_client.CortexClient.fetch_available_models", return_value=[{"name": "models/gemini-3-flash-preview"}, {"name": "models/cortex-chat"}])
    def test_models_contains_all_providers(self, mock_fetch):
        """Model registry includes Gemini, Cortex, and Claude models."""
        result = self.svc.models()
        models = result["models"]
        assert "gemini-3-flash-preview" in models
        assert "cortex-chat" in models
        assert "claude-sonnet" in models

    @patch("mekhane.ochema.cortex_client.CortexClient.fetch_available_models", return_value=[])
    def test_default_model(self, mock_fetch):
        """Default model is gemini-3-flash-preview."""
        result = self.svc.models()
        assert result["default"] == "gemini-3-flash-preview"


# --- Stream Validation ---


class TestStreamValidation:
    """Streaming API validation tests."""

    def setup_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()
        self.svc = OchemaService.get()

    def teardown_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()

    @patch("mekhane.ochema.service.OchemaService._get_ls_client")
    def test_stream_claude_routes_to_ls(self, mock_get_ls):
        """stream() routes Claude models to LS chat_stream (DX-010 v9.1)."""
        mock_ls = MagicMock()
        mock_ls.chat_stream.return_value = iter(["Hello", " world"])
        mock_get_ls.return_value = mock_ls
        chunks = list(self.svc.stream("hello", model="claude-sonnet"))
        assert chunks == ["Hello", " world"]
        mock_ls.chat_stream.assert_called_once()

    @patch("mekhane.ochema.service.OchemaService._get_ls_client")
    def test_stream_proto_model_routes_to_ls(self, mock_get_ls):
        """stream() routes proto Claude models to LS chat_stream."""
        mock_ls = MagicMock()
        mock_ls.chat_stream.return_value = iter(["Response"])
        mock_get_ls.return_value = mock_ls
        chunks = list(self.svc.stream("hello", model="MODEL_PLACEHOLDER_M35"))
        assert chunks == ["Response"]
        mock_ls.chat_stream.assert_called_once()

    @patch("mekhane.ochema.service.OchemaService._build_candidates")
    @patch("mekhane.ochema.service.OchemaService._get_ls_client", return_value=None)
    def test_stream_claude_raises_without_ls(self, mock_get_ls, mock_candidates):
        """stream() raises RuntimeError for Claude when LS unavailable."""
        from mekhane.ochema.model_fallback import ModelCandidate
        mock_candidates.return_value = [ModelCandidate(provider="ls", model="claude-sonnet")]

        import pytest
        with pytest.raises(Exception):
            list(self.svc.stream("hello", model="claude-sonnet"))


# --- Constants ---


class TestConstants:
    """Verify exported constants."""

    def test_claude_model_map_keys(self):
        from mekhane.ochema.service import CLAUDE_MODEL_MAP
        assert "claude-sonnet" in CLAUDE_MODEL_MAP
        assert "claude-opus" in CLAUDE_MODEL_MAP

    def test_default_model_value(self):
        from mekhane.ochema.service import DEFAULT_MODEL
        assert DEFAULT_MODEL == "gemini-3-flash-preview"


# --- Repr ---


class TestRepr:
    """OchemaService repr test."""

    def setup_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()

    def teardown_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()

    def test_repr_format(self):
        from mekhane.ochema.service import OchemaService
        svc = OchemaService.get()
        r = repr(svc)
        assert "OchemaService(" in r
        assert "cortex=" in r


# --- DX-010 §L: Platform Constraints Tests ---


class TestPlatformConstraints:
    """Tests for DX-010 §L — known platform constraints and strategic insights."""

    def test_byok_status(self):
        """§L: BYOK is unsupported on local LS (SeatManagementService 404)."""
        from mekhane.ochema.service import BYOK_STATUS
        assert BYOK_STATUS == "unsupported"

    def test_dynamic_project_id(self):
        """§L: cloudaicompanionProject is dynamic per-process."""
        from mekhane.ochema.service import DYNAMIC_PROJECT_ID
        assert DYNAMIC_PROJECT_ID is True

    def test_claude_rest_false_positive(self):
        """§L+§E.3: REST generateChat Claude response is a false positive."""
        from mekhane.ochema.service import CLAUDE_REST_FALSE_POSITIVE
        assert CLAUDE_REST_FALSE_POSITIVE is True

    def test_claude_models_route_to_ls_not_rest(self):
        """§L: Claude models must route to LS, not REST (false positive guard)."""
        from mekhane.ochema.service import OchemaService, CLAUDE_REST_FALSE_POSITIVE
        OchemaService.reset()
        svc = OchemaService.get()
        # If CLAUDE_REST_FALSE_POSITIVE is True, Claude models MUST route to LS
        assert CLAUDE_REST_FALSE_POSITIVE is True
        assert svc._is_claude_model("claude-sonnet") is True
        assert svc._is_claude_model("claude-opus") is True
        OchemaService.reset()

    def test_platform_constraints_complete(self):
        """All §L constants are importable as a set."""
        from mekhane.ochema.service import (
            BYOK_STATUS,
            DYNAMIC_PROJECT_ID,
            CLAUDE_REST_FALSE_POSITIVE,
        )
        # These three constraints define the known platform limitations
        constraints = {
            "byok": BYOK_STATUS,
            "dynamic_project": DYNAMIC_PROJECT_ID,
            "claude_rest_fp": CLAUDE_REST_FALSE_POSITIVE,
        }
        assert len(constraints) == 3


# --- K9 Retry Logic (model not found → LS restart) ---


class TestK9Retry:
    """K9 (model not found) リトライロジックのテスト。

    _ask_ls が RuntimeError("model not found") を受け取った際に:
    1. LS クライアントと NonStandalone マネージャーをリセットする
    2. 1回だけリトライする (無限ループ防止)
    """

    def setup_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()
        self.svc = OchemaService.get()

    def teardown_method(self):
        from mekhane.ochema.service import OchemaService
        OchemaService.reset()

    @patch("mekhane.ochema.service.OchemaService._get_ls_client")
    @patch("mekhane.ochema.service.OchemaService._resolve_ls_proto_model")
    def test_k9_retry_triggers_restart(self, mock_resolve, mock_get_ls):
        """model not found → LS リセット → リトライで成功。"""
        from mekhane.ochema.types import LLMResponse

        mock_resolve.return_value = "MODEL_PLACEHOLDER_M35"

        # 1st call: model not found
        mock_ls_bad = MagicMock()
        mock_ls_bad.ask.side_effect = RuntimeError(
            "HTTP 500 — unknown model key MODEL_PLACEHOLDER_M35: model not found"
        )

        # 2nd call (after reset): success
        mock_ls_good = MagicMock()
        mock_ls_good.ask.return_value = LLMResponse(text="Hello!", model="claude-sonnet-4.6")

        mock_get_ls.side_effect = [mock_ls_bad, mock_ls_good]

        result = self.svc._ask_ls("Hello", model="claude-sonnet")
        assert result.text == "Hello!"
        assert mock_get_ls.call_count == 2  # 1st (fail) + 2nd (retry)

    @patch("mekhane.ochema.service.OchemaService._get_ls_client")
    @patch("mekhane.ochema.service.OchemaService._resolve_ls_proto_model")
    def test_k9_retry_no_infinite_loop(self, mock_resolve, mock_get_ls):
        """model not found が 2 回連続 → リトライは 1 回のみ、2 回目で例外。"""
        mock_resolve.return_value = "MODEL_PLACEHOLDER_M35"

        mock_ls = MagicMock()
        mock_ls.ask.side_effect = RuntimeError("model not found")
        mock_get_ls.return_value = mock_ls

        import pytest
        with pytest.raises(Exception):
            self.svc._ask_ls("Hello", model="claude-sonnet")

        # _get_ls_client: 1st (original) + 2nd (retry) = 2
        assert mock_get_ls.call_count == 2

    @patch("mekhane.ochema.service.OchemaService._get_ls_client")
    @patch("mekhane.ochema.service.OchemaService._resolve_ls_proto_model")
    def test_non_k9_error_not_retried(self, mock_resolve, mock_get_ls):
        """model not found 以外のエラーはリトライしない。"""
        mock_resolve.return_value = "MODEL_PLACEHOLDER_M35"

        mock_ls = MagicMock()
        mock_ls.ask.side_effect = RuntimeError("connection timeout")
        mock_get_ls.return_value = mock_ls

        import pytest
        with pytest.raises(Exception):
            self.svc._ask_ls("Hello", model="claude-sonnet")

        # リトライなし: _get_ls_client は 1 回のみ


# --- Docker LS Priority ---


class TestWriteInfoMerge:
    """ls_daemon.py の _write_info マージ書き込みテスト。"""

    def test_merge_preserves_other_source(self, tmp_path):
        """Docker の _write_info が Local エントリを保持すること。"""
        import json
        from unittest.mock import patch
        from mekhane.ochema.ls_daemon import LSPoolDaemon

        info_path = tmp_path / "ls_daemon.json"

        # 既存の Local エントリを用意
        local_entry = [{"pid": 100, "port": 9000, "csrf": "local_csrf", "workspace": "w0",
                        "is_https": False, "source": "local", "updated_at": 1.0}]
        info_path.write_text(json.dumps(local_entry))

        # Docker daemon の _write_info を呼ぶ
        daemon = LSPoolDaemon(source="docker")
        # ダミーの ls_info を設定
        from types import SimpleNamespace
        daemon.ls_infos = [SimpleNamespace(pid=200, port=37501, csrf="docker_csrf",
                                           workspace="nonstd_hgk_0", is_https=False)]

        with patch("mekhane.ochema.ls_daemon.DAEMON_INFO_PATH", info_path):
            daemon._write_info()

        result = json.loads(info_path.read_text())
        assert len(result) == 2  # local + docker
        sources = {e["source"] for e in result}
        assert sources == {"local", "docker"}
        # Local エントリが保持されている
        local = [e for e in result if e["source"] == "local"]
        assert local[0]["port"] == 9000
        # Docker エントリが追加されている
        docker = [e for e in result if e["source"] == "docker"]
        assert docker[0]["port"] == 37501

    def test_merge_replaces_same_source(self, tmp_path):
        """同じ source のエントリは更新されること。"""
        import json
        from unittest.mock import patch
        from mekhane.ochema.ls_daemon import LSPoolDaemon

        info_path = tmp_path / "ls_daemon.json"

        # 既存の Docker エントリ (古いポート)
        old_entries = [
            {"pid": 100, "port": 9000, "source": "local", "csrf": "lc", "workspace": "w0",
             "is_https": False, "updated_at": 1.0},
            {"pid": 200, "port": 30000, "source": "docker", "csrf": "old_dc", "workspace": "w1",
             "is_https": False, "updated_at": 1.0},
        ]
        info_path.write_text(json.dumps(old_entries))

        # 新しい Docker daemon
        daemon = LSPoolDaemon(source="docker")
        from types import SimpleNamespace
        daemon.ls_infos = [SimpleNamespace(pid=300, port=37501, csrf="new_dc",
                                           workspace="nonstd_hgk_0", is_https=False)]

        with patch("mekhane.ochema.ls_daemon.DAEMON_INFO_PATH", info_path):
            daemon._write_info()

        result = json.loads(info_path.read_text())
        assert len(result) == 2  # local + docker (置換)
        docker = [e for e in result if e["source"] == "docker"]
        assert len(docker) == 1
        assert docker[0]["port"] == 37501  # 新しいポート
        assert docker[0]["csrf"] == "new_dc"

    def test_merge_creates_new_file(self, tmp_path):
        """ファイルが存在しない場合は新規作成。"""
        import json
        from unittest.mock import patch
        from mekhane.ochema.ls_daemon import LSPoolDaemon

        info_path = tmp_path / "ls_daemon.json"
        assert not info_path.exists()

        daemon = LSPoolDaemon(source="local")
        from types import SimpleNamespace
        daemon.ls_infos = [SimpleNamespace(pid=100, port=9000, csrf="new_csrf",
                                           workspace="w0", is_https=False)]

        with patch("mekhane.ochema.ls_daemon.DAEMON_INFO_PATH", info_path):
            daemon._write_info()

        result = json.loads(info_path.read_text())
        assert len(result) == 1
        assert result[0]["source"] == "local"
        assert result[0]["port"] == 9000


class TestRemoteLsRegister:
    """remote_ls_register.py の同期ロジック。"""

    def test_sync_tunnels_writes_local_tunnel_pid(self, tmp_path):
        from unittest.mock import patch
        from mekhane.ochema import remote_ls_register

        info_path = tmp_path / "ls_daemon.json"
        state_file = tmp_path / "tunnel_state.json"

        remote_entries = [{
            "pid": 9911,
            "port": 43001,
            "csrf": "remote_csrf",
            "workspace": "remote_ls_0",
            "is_https": False,
            "source": "local",
        }]

        with patch.object(remote_ls_register, "DAEMON_INFO_PATH", info_path), \
             patch.object(remote_ls_register, "TUNNEL_STATE_FILE", state_file), \
             patch.object(remote_ls_register, "_read_remote_ls_info", return_value=remote_entries), \
             patch.object(remote_ls_register, "_load_tunnel_state", return_value={}), \
             patch.object(remote_ls_register, "_setup_ssh_tunnel", return_value=55123):
            assert remote_ls_register._sync_tunnels("100.83.204.102", "makaron8426", 51000) is True

        saved_entries = json.loads(info_path.read_text())
        assert saved_entries[0]["source"] == "remote"
        assert saved_entries[0]["pid"] == 55123
        assert saved_entries[0]["tunnel_pid"] == 55123
        assert saved_entries[0]["remote_pid"] == 9911
        assert saved_entries[0]["remote_host"] == "100.83.204.102"
        assert saved_entries[0]["remote_port"] == 43001

        saved_state = json.loads(state_file.read_text())
        assert saved_state["51000"]["pid"] == 55123
        assert saved_state["51000"]["remote_port"] == 43001


class TestRemoteLsSelection:
    """AntigravityClient / OchemaService の remote LS 対応。"""

    def test_load_daemon_info_prefers_remote_source(self, tmp_path):
        from pathlib import Path
        from mekhane.ochema.antigravity_client import AntigravityClient

        daemon_dir = tmp_path / ".gemini" / "antigravity"
        daemon_dir.mkdir(parents=True)
        info_path = daemon_dir / "ls_daemon.json"
        info_path.write_text(json.dumps([
            {"pid": 111, "port": 41000, "csrf": "local", "workspace": "w0", "is_https": False, "source": "local"},
            {"pid": 222, "port": 51000, "csrf": "remote", "workspace": "w1", "is_https": False, "source": "remote", "remote_host": "100.83.204.102", "remote_port": 43001},
        ]))

        client = AntigravityClient.__new__(AntigravityClient)
        with patch.object(Path, "home", return_value=tmp_path), \
             patch("mekhane.ochema.antigravity_client.psutil.pid_exists", side_effect=lambda pid: pid in {111, 222}):
            ls_info = client._load_daemon_info()

        assert ls_info is not None
        assert ls_info.source == "remote"
        assert ls_info.pid == 222
        assert ls_info.remote_host == "100.83.204.102"
        assert ls_info.remote_port == 43001

    def test_remote_health_failure_resets_cached_client(self):
        from mekhane.ochema.service import OchemaService

        OchemaService.reset()
        svc = OchemaService.get()
        mock_client = MagicMock()
        mock_client.get_status.side_effect = RuntimeError("connect timeout")
        mock_client.pid = 4321
        mock_client.ls = MagicMock(source="remote")
        svc._ls_client = mock_client

        with patch("os.kill", return_value=None):
            assert svc._check_cached_client() is None
        assert svc._ls_client is None
        OchemaService.reset()
