#!/usr/bin/env python3
# PROOF: [L2/テスト] <- 60_実験/02_テスト/test_hub_shadow.py
"""
Hub MCP Phase 2 テスト — Daimonion + Gate パイプライン

テスト対象:
  1. hub_config: get_tool_scores() のプレフィックス除去
  2. daimonion: Daimonion の record/should_alpha/score_tool
  3. hub_mcp_server: HubProxy の Hub 固有ツール定義
"""
import sys
import time
from pathlib import Path

# PYTHONPATH 設定
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_PROJECT_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"))

import pytest


# ============ hub_config テスト ============

class TestHubConfig:
    """hub_config.py のテスト。"""

    def test_get_tool_scores_direct(self):
        """直接ツール名でスコアを取得できる。"""
        from mekhane.mcp.hub_config import get_tool_scores
        imp, comp = get_tool_scores("hermeneus_run")
        assert imp == 0.9
        assert comp == 0.8

    def test_get_tool_scores_mcp_prefix(self):
        """mcp_{server}_ プレフィックス付きで取得できる。"""
        from mekhane.mcp.hub_config import get_tool_scores
        imp, comp = get_tool_scores("mcp_hermeneus_hermeneus_run")
        assert imp == 0.9
        assert comp == 0.8

    def test_get_tool_scores_server_prefix(self):
        """hermeneus_ プレフィックス付きで取得できる。"""
        from mekhane.mcp.hub_config import get_tool_scores
        imp, comp = get_tool_scores("hermeneus_hermeneus_run")
        assert imp == 0.9
        assert comp == 0.8

    def test_get_tool_scores_ping_zero(self):
        """ping はスコア (0.0, 0.0) を返す。"""
        from mekhane.mcp.hub_config import get_tool_scores
        imp, comp = get_tool_scores("ping")
        assert imp == 0.0
        assert comp == 0.0

    def test_get_tool_scores_unknown_default(self):
        """未知のツール名はデフォルトスコアを返す。"""
        from mekhane.mcp.hub_config import get_tool_scores, DEFAULT_TOOL_SCORES
        imp, comp = get_tool_scores("unknown_tool_xyz")
        assert (imp, comp) == DEFAULT_TOOL_SCORES

    def test_pipeline_config_shadow_enabled(self):
        """PIPELINE_CONFIG で shadow_enabled が True。"""
        from mekhane.mcp.hub_config import PIPELINE_CONFIG
        assert PIPELINE_CONFIG["shadow_enabled"] is True

    def test_pipeline_config_gate_enabled(self):
        """PIPELINE_CONFIG で gate_enabled が True。"""
        from mekhane.mcp.hub_config import PIPELINE_CONFIG
        assert PIPELINE_CONFIG["gate_enabled"] is True

    def test_backends_has_required(self):
        """BACKENDS に主要なバックエンドが含まれている。"""
        from mekhane.mcp.hub_config import BACKENDS
        for name in ["ochema", "hermeneus", "sekisho", "sympatheia", "phantazein"]:
            assert name in BACKENDS, f"{name} not in BACKENDS"

    def test_hub_port(self):
        """HUB_PORT = 9700。"""
        from mekhane.mcp.hub_config import HUB_PORT
        assert HUB_PORT == 9700

    def test_backend_url(self):
        """backend_url() が正しい URL を生成する。"""
        from mekhane.mcp.hub_config import backend_url
        url = backend_url("ochema")
        assert url == "http://127.0.0.1:9701/mcp"


# ============ daimonion テスト ============

class TestDaimonion:
    """daimonion.py のテスト。"""

    def test_score_tool_hermeneus_run(self):
        """hermeneus_run は高スコアを返す。"""
        from mekhane.mcp.daimonion import Daimonion
        imp, comp = Daimonion.score_tool("hermeneus_run")
        assert imp >= 0.8

    def test_score_tool_ping_zero(self):
        """ping はスコア 0 を返す。"""
        from mekhane.mcp.daimonion import Daimonion
        imp, comp = Daimonion.score_tool("ping")
        assert imp == 0.0
        assert comp == 0.0

    def test_record_adds_to_buffer(self):
        """record() でバッファにアクションが追加される。"""
        from mekhane.mcp.daimonion import Daimonion
        s = Daimonion()
        assert len(s._buffer) == 0
        s.record("ochema", "ask", "テストメッセージ")
        assert len(s._buffer) == 1
        assert s._buffer[0].backend == "ochema"
        assert s._buffer[0].tool_name == "ask"

    def test_record_skipped_during_monitor(self):
        """監視処理中は record() がスキップされる。"""
        from mekhane.mcp.daimonion import Daimonion
        s = Daimonion()
        s._in_monitor = True
        s.record("ochema", "ask", "テスト")
        assert len(s._buffer) == 0

    def test_should_alpha_false_when_disabled(self):
        """disabled 時は should_alpha() が False を返す。"""
        from mekhane.mcp.daimonion import Daimonion
        s = Daimonion()
        s.enabled = False
        s.record("hermeneus", "hermeneus_run", "テスト")
        assert s.should_alpha() is False

    def test_should_alpha_false_when_empty(self):
        """バッファが空の時は False。"""
        from mekhane.mcp.daimonion import Daimonion
        s = Daimonion()
        assert s.should_alpha() is False

    def test_should_alpha_false_for_ping(self):
        """ping (importance=0.0) は should_alpha() False。"""
        from mekhane.mcp.daimonion import Daimonion
        s = Daimonion()
        s._last_alpha_time = 0  # クールダウンをリセット
        s.record("ochema", "ping", "テスト")
        assert s.should_alpha() is False

    def test_should_alpha_true_for_high_importance(self):
        """高 importance ツールは should_alpha() True。"""
        from mekhane.mcp.daimonion import Daimonion
        s = Daimonion()
        s._last_alpha_time = 0  # クールダウンをリセット
        s.record("hermeneus", "hermeneus_run", "CCL実行テスト")
        assert s.should_alpha() is True

    def test_should_alpha_respects_cooldown(self):
        """クールダウン中は should_alpha() False。"""
        from mekhane.mcp.daimonion import Daimonion
        s = Daimonion()
        s._last_alpha_time = time.time()  # 今実行した
        s.record("hermeneus", "hermeneus_run", "テスト")
        assert s.should_alpha() is False

    def test_stats_returns_dict(self):
        """stats() が dict を返す。"""
        from mekhane.mcp.daimonion import Daimonion
        s = Daimonion()
        stats = s.stats()
        assert isinstance(stats, dict)
        assert "enabled" in stats
        assert "alpha" in stats
        assert "beta" in stats
        assert "shadow_count" in stats

    def test_format_piggyback(self):
        """format_piggyback() が構造化テキストを返す。"""
        from mekhane.mcp.daimonion import Daimonion, DaimonionResult, DaimonionFinding
        s = Daimonion()
        result = DaimonionResult(
            mode="α",
            findings=[DaimonionFinding(category="反証", content="テスト指摘", severity="warning")],
            counterpoint="テスト反証",
            confidence=0.8,
            raw_text="{}",
            model="test",
            latency_ms=100,
            action_importance=0.9,
            action_complexity=0.8,
        )
        text = s.format_piggyback(result)
        assert "Daimonion" in text
        assert "TAINT" in text
        assert "テスト指摘" in text
        assert "テスト反証" in text

    def test_parse_response_fields(self):
        """_parse_response() が現行フィールドを DaimonionResult にパースする。"""
        import json
        from mekhane.mcp.daimonion import Daimonion, ActionRecord
        s = Daimonion()
        raw = json.dumps({
            "findings": [
                {"category": "反証", "content": "ラベル欠損", "severity": "warning"}
            ],
            "counterpoint": "別解あり",
            "confidence": 0.6,
        })
        latest = ActionRecord(
            timestamp=time.time(), backend="test",
            tool_name="test", summary="test", importance=0.8, complexity=0.7, fep_group="I",
        )
        result = s._parse_response(raw, latest, 50)
        assert len(result.findings) == 1
        assert result.mode == "α"
        assert result.findings[0].mode == "α"
        assert result.findings[0].category == "反証"
        assert result.counterpoint == "別解あり"
        assert result.confidence == 0.6
        assert result.action_importance == 0.8
        assert result.action_complexity == 0.7
        assert result.fep_group == "I"

    def test_build_alpha_prompt_includes_current_focus(self):
        """_build_alpha_prompt() が現行 α プロンプトを組み立てる。"""
        from mekhane.mcp.daimonion import Daimonion, ActionRecord
        s = Daimonion()
        latest = ActionRecord(
            timestamp=time.time(), backend="test",
            tool_name="test", summary="テスト", reasoning="判断理由", fep_group="I",
        )
        prompt = s._build_alpha_prompt(["[0秒前] test.test"], latest)
        assert "Daimonion (δαιμόνιον) α" in prompt
        assert "Claude の推論・判断の文脈" in prompt
        assert "前提の隠蔽" in prompt
        assert "counterpoint" in prompt
        assert "JSON のみ出力" in prompt

    def test_singleton_get_daimonion(self):
        """get_daimonion() がシングルトンを返す。"""
        from mekhane.mcp.daimonion import get_daimonion, _instance
        import mekhane.mcp.daimonion as mod
        mod._instance = None  # リセット
        s1 = get_daimonion()
        s2 = get_daimonion()
        assert s1 is s2
        mod._instance = None  # クリーンアップ

    def test_action_record_has_backend(self):
        """ActionRecord に backend フィールドがある。"""
        from mekhane.mcp.daimonion import ActionRecord
        r = ActionRecord(
            timestamp=time.time(),
            backend="hermeneus",
            tool_name="hermeneus_run",
            summary="テスト",
        )
        assert r.backend == "hermeneus"


# ============ hub_mcp_server テスト ============

class TestHubProxy:
    """hub_mcp_server.py HubProxy のテスト。"""

    def test_hub_tools_defined(self):
        """Hub 固有ツールが定義されている。"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        hub = HubProxy()
        tools = hub._hub_tools()
        assert len(tools) >= 3
        names = {t["name"] for t in tools}
        assert "hub_daimonion_status" in names
        assert "hub_stats" in names
        assert "hub_daimonion_judge" in names

    def test_list_tools_for_hub(self):
        """list_tools_for("hub") が Hub 固有ツールを返す。"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        hub = HubProxy()
        tools = hub.list_tools_for("hub")
        assert len(tools) >= 3

    def test_list_tools_for_unknown_returns_empty(self):
        """未接続バックエンドは空リストを返す。"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        hub = HubProxy()
        tools = hub.list_tools_for("nonexistent")
        assert tools == []

    def test_stats_structure(self):
        """stats() が必要なキーを持つ dict を返す。"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        hub = HubProxy()
        stats = hub.stats()
        assert "uptime_seconds" in stats
        assert "backends_connected" in stats
        assert "pipeline" in stats
        assert "shadow" in stats
        assert "gate" in stats

    def test_stats_pipeline_fields(self):
        """stats() の pipeline に log/shadow/gate がある。"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        hub = HubProxy()
        stats = hub.stats()
        pipeline = stats["pipeline"]
        assert "log" in pipeline
        assert "shadow" in pipeline
        assert "gate" in pipeline


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
