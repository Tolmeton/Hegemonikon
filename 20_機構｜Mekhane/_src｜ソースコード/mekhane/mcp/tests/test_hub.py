#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/tests/test_hub.py A0→Hub MCP テスト
"""
Hub MCP Proxy — テストスイート

hub_config.py / daimonion.py / hub_mcp_server.py の単体テスト。
外部サービスに依存しない (mock + 単体テスト)。
"""
import sys
import json
import time
import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# =============================================================================
# TestHubConfig — hub_config.py のテスト
# =============================================================================

class TestHubConfig:
    """hub_config.py の設定・ユーティリティテスト"""

    # PURPOSE: backend_url() が正しい URL 構造を返すことを検証
    def test_backend_url_構造(self):
        """backend_url() が http://{host}:{port}/mcp 形式を返す"""
        from mekhane.mcp.hub_config import backend_url, BACKENDS

        for name in BACKENDS:
            if BACKENDS[name].get("type") in ("subprocess", "stdio_mcp"):
                continue
            url = backend_url(name)
            assert url.startswith("http://"), f"{name}: URL が http:// で始まらない"
            assert url.endswith("/mcp"), f"{name}: URL が /mcp で終わらない"
            assert str(BACKENDS[name]["port"]) in url, f"{name}: ポート番号が URL に含まれない"

    # PURPOSE: backend_url() のホスト指定テスト
    def test_backend_url_カスタムホスト(self):
        """backend_url() にカスタムホストを指定できる"""
        from mekhane.mcp.hub_config import backend_url

        url = backend_url("ochema", host="192.168.1.1")
        assert "192.168.1.1" in url

    # PURPOSE: ツールスコアの直接一致テスト
    def test_get_tool_scores_直接一致(self):
        """TOOL_SCORES に直接登録されたツール名で正しいスコアが返る"""
        from mekhane.mcp.hub_config import get_tool_scores

        imp, comp = get_tool_scores("hermeneus_run")
        assert imp == 0.9
        assert comp == 0.8

    # PURPOSE: mcp_ プレフィックス除去テスト
    def test_get_tool_scores_mcp_プレフィックス除去(self):
        """mcp_{server}_ プレフィックスを除去してマッチする"""
        from mekhane.mcp.hub_config import get_tool_scores

        # mcp_periskope_research:
        #   Step 1: 直接一致なし
        #   Step 2: mcp_periskope_ 除去 → stripped='research'
        #           qualified='periskope.research' → TOOL_SCORES にない
        #   Step 3: stripped='research' → TOOL_SCORES にある? → ある (periskope_research は直接マッチ)
        # 実際: periskope_research は直接 TOOL_SCORES に登録されている
        # mcp_periskope_research は Step 1 で直接マッチしない
        # Step 2: stripped='research', qualified='periskope.research' → なし
        # Step 3: stripped='research' → TOOL_SCORES にキー 'research' はない → DEFAULT
        # しかし Step 4: periskope_ プレフィックス除去 → stripped='research' → search TOOL_SCORES → なし
        # → DEFAULT を返す
        # これは設計上の挙動。IDE が mcp_ プレフィックスを付けた場合は
        # DEFAULT になる。このテストはその挙動を記録する。
        imp, comp = get_tool_scores("mcp_phantazein_search")
        # mcp_phantazein_ → stripped='search' → 'phantazein.search' (なし) → 'search' → TOOL_SCORES に 'search' がある!
        assert imp == 0.4  # search の importance
        assert comp == 0.3  # search の complexity

    # PURPOSE: server_ プレフィックス除去テスト
    def test_get_tool_scores_server_プレフィックス除去(self):
        """server_ プレフィックスを除去してマッチする"""
        from mekhane.mcp.hub_config import get_tool_scores

        # periskope_research → research (stripped) → TOOL_SCORES にないが
        # periskope_research は直接マッチする
        imp, comp = get_tool_scores("periskope_research")
        assert imp == 0.7
        assert comp == 0.6

    # PURPOSE: 未登録ツールのデフォルトスコアテスト
    def test_get_tool_scores_デフォルト(self):
        """未登録ツール名は DEFAULT_TOOL_SCORES を返す"""
        from mekhane.mcp.hub_config import get_tool_scores, DEFAULT_TOOL_SCORES

        imp, comp = get_tool_scores("completely_unknown_tool_xyz")
        assert (imp, comp) == DEFAULT_TOOL_SCORES

    # PURPOSE: axis router ポート定義テスト
    def test_axis_ports_定義(self):
        """3 軸 router のポートが固定されていること"""
        from mekhane.mcp.hub_config import AXIS_PORTS, HUB_PORT

        assert AXIS_PORTS == {
            "aisthetikon": 9720,
            "dianoetikon": 9721,
            "poietikon": 9722,
        }
        assert HUB_PORT == 9720

    def test_axis_helper_配置判定(self):
        """axis / profile helper が placement を正しく反映する"""
        from mekhane.mcp.hub_config import (
            get_backends_for_axis,
            get_delegated_backends_for_axis,
            get_runnable_backends_for_axis,
        )

        assert "periskope" in get_backends_for_axis("aisthetikon")
        assert "periskope" not in get_runnable_backends_for_axis("aisthetikon", "local")
        assert "periskope" in get_delegated_backends_for_axis("aisthetikon", "local")
        assert "periskope" in get_runnable_backends_for_axis("aisthetikon", "remote")

    # PURPOSE: パイプライン設定の必須キーが存在するか
    def test_pipeline_config_必須キー(self):
        """PIPELINE_CONFIG に必須キーが全て存在する"""
        from mekhane.mcp.hub_config import PIPELINE_CONFIG

        required_keys = [
            "log_enabled", "shadow_enabled", "shadow_cooldown",
            "shadow_importance_threshold", "shadow_complexity_threshold",
            "shadow_model", "gate_enabled",
        ]
        for key in required_keys:
            assert key in PIPELINE_CONFIG, f"PIPELINE_CONFIG に {key} がない"


# =============================================================================
# TestDaimonion — daimonion.py のテスト
# =============================================================================

class TestDaimonion:
    """Daimonion の単体テスト (Gemini API は mock)"""

    def _make_daimonion(self):
        """テスト用 Daimonion を生成 (CortexClient を mock)"""
        with patch("mekhane.ochema.cortex_client.CortexClient"):
            from mekhane.mcp.daimonion import Daimonion

            daimonion = Daimonion()
            daimonion._alpha_enabled = True
            daimonion._last_alpha_time = 0  # クールダウンをリセット
            return daimonion

    # PURPOSE: バッファサイズ上限テスト
    def test_record_バッファサイズ(self):
        """バッファが BUFFER_SIZE を超えない"""
        daimonion = self._make_daimonion()
        from mekhane.mcp.daimonion import BUFFER_SIZE

        for i in range(BUFFER_SIZE + 5):
            daimonion.record(
                backend="test", tool_name="test_tool",
                summary=f"action_{i}",
            )
        assert len(daimonion._buffer) == BUFFER_SIZE

    # PURPOSE: 無効時は should_alpha = False
    def test_should_alpha_無効時(self):
        """enabled=False のとき False を返す"""
        daimonion = self._make_daimonion()
        daimonion._alpha_enabled = False
        daimonion.record(backend="test", tool_name="hermeneus_run", summary="test")
        assert daimonion.should_alpha() is False

    # PURPOSE: 空バッファで should_alpha = False
    def test_should_alpha_バッファ空(self):
        """バッファが空のとき False を返す"""
        daimonion = self._make_daimonion()
        assert daimonion.should_alpha() is False

    # PURPOSE: クールダウン中は should_alpha = False
    def test_should_alpha_クールダウン中(self):
        """直前に α 実行した直後は False を返す"""
        daimonion = self._make_daimonion()
        daimonion._last_alpha_time = time.time()  # 今 α した
        daimonion.record(backend="test", tool_name="hermeneus_run", summary="test")
        assert daimonion.should_alpha() is False

    # PURPOSE: スコア不足で should_alpha = False + skip_count 更新
    def test_should_alpha_スコア不足(self):
        """importance/complexity が閾値未満のとき False + skip_count 増加"""
        daimonion = self._make_daimonion()
        initial_skip = daimonion._skip_count
        daimonion.record(backend="test", tool_name="ping", summary="noop")  # imp=0.0
        assert daimonion.should_alpha() is False
        assert daimonion._skip_count > initial_skip

    # PURPOSE: 発火条件テスト
    def test_should_alpha_発火条件(self):
        """閾値超過 + クールダウン経過 → True"""
        daimonion = self._make_daimonion()
        daimonion._last_alpha_time = 0  # クールダウン済み
        daimonion.record(
            backend="hermeneus", tool_name="hermeneus_run",
            summary="CCL execution",
        )
        assert daimonion.should_alpha() is True

    # PURPOSE: format_piggyback の構造テスト
    def test_format_piggyback_構造(self):
        """ピギーバック出力が所定のマークダウン構造を含む"""
        daimonion = self._make_daimonion()
        from mekhane.mcp.daimonion import DaimonionResult, DaimonionFinding

        result = DaimonionResult(
            mode="α",
            findings=[
                DaimonionFinding(category="見落とし", content="テスト指摘", severity="warning"),
            ],
            counterpoint="反証テスト",
            confidence=0.8,
            raw_text="raw",
            model="gemini-test",
            latency_ms=100,
            action_importance=0.9,
            action_complexity=0.8,
        )

        output = daimonion.format_piggyback(result)
        assert "🔮 Daimonion α" in output
        assert "TAINT" in output
        assert "テスト指摘" in output
        assert "反証テスト" in output
        assert "⚠️" in output  # warning severity のアイコン

    # PURPOSE: 正常 JSON パーステスト
    def test_parse_response_正常JSON(self):
        """JSON レスポンスを DaimonionResult にパースできる"""
        daimonion = self._make_daimonion()
        from mekhane.mcp.daimonion import ActionRecord

        raw_json = json.dumps({
            "findings": [
                {"category": "改善点", "content": "テスト改善", "severity": "info"},
            ],
            "counterpoint": "テスト反証",
            "confidence": 0.75,
        })

        latest = ActionRecord(
            timestamp=time.time(), backend="test",
            tool_name="test", summary="test",
            importance=0.5, complexity=0.3,
        )

        result = daimonion._parse_response(raw_json, latest, 50, mode="α")
        assert len(result.findings) == 1
        assert result.findings[0].category == "改善点"
        assert result.findings[0].mode == "α"
        assert result.counterpoint == "テスト反証"
        assert result.confidence == 0.75
        assert result.mode == "α"

    # PURPOSE: 不正 JSON フォールバックテスト
    def test_parse_response_不正JSON(self):
        """JSON pattern にマッチしない入力 → findings 空 + デフォルト値"""
        daimonion = self._make_daimonion()
        from mekhane.mcp.daimonion import ActionRecord

        latest = ActionRecord(
            timestamp=time.time(), backend="test",
            tool_name="test", summary="test",
            importance=0.5, complexity=0.3,
        )

        result = daimonion._parse_response("これは JSON ではない", latest, 50, mode="α")
        # JSON pattern ({...} or ```json...```) にマッチしない → findings 空
        assert len(result.findings) == 0
        assert result.confidence == 0.5  # デフォルト値
        assert result.counterpoint == ""  # デフォルト値
        assert result.mode == "α"

    # PURPOSE: 監視中は record しないテスト
    def test_record_監視中は記録しない(self):
        """_in_monitor=True のとき record はバッファに追加しない"""
        daimonion = self._make_daimonion()
        daimonion._in_monitor = True
        daimonion.record(backend="test", tool_name="test", summary="should_skip")
        assert len(daimonion._buffer) == 0

    # PURPOSE: stats の構造テスト
    def test_stats_構造(self):
        """stats() が必要なキーを全て含む"""
        daimonion = self._make_daimonion()
        stats = daimonion.stats()
        required_keys = [
            "enabled", "shadow_count", "skip_count",
            "buffer_size", "buffer_max",
            "importance_threshold", "complexity_threshold",
            "cooldown_remaining", "last_actions",
        ]
        for key in required_keys:
            assert key in stats, f"stats に {key} がない"


# =============================================================================
# TestHubProxy — hub_mcp_server.py のテスト
# =============================================================================

class TestHubProxy:
    """HubProxy の単体テスト (バックエンド接続は mock)"""

    def _make_hub(self):
        """テスト用 HubProxy を生成"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        return HubProxy()

    # PURPOSE: Hub 固有ツールの list_tools テスト
    def test_list_tools_for_hub(self):
        """list_tools_for('hub') が Hub 固有ツール (10件) を返す"""
        hub = self._make_hub()
        tools = hub.list_tools_for("hub")
        assert len(tools) == 10
        names = {t["name"] for t in tools}
        assert "hub_daimonion_status" in names
        assert "hub_stats" in names
        assert "hub_recommend" in names
        assert "hub_daimonion_judge" in names
        assert "hub_execute" in names
        # FEP 認知入口: 3能力 (τὸ -τικόν 系)
        assert "hub_aisthetikon" in names
        assert "hub_dianoetikon" in names
        assert "hub_poietikon" in names

    # PURPOSE: 未接続バックエンドの list_tools テスト
    def test_list_tools_for_未接続バックエンド(self):
        """未接続バックエンドに対して空リストを返す"""
        hub = self._make_hub()
        tools = hub.list_tools_for("nonexistent")
        assert tools == []

    # PURPOSE: 初期状態の stats テスト
    def test_stats_初期状態(self):
        """初期状態の stats が正しい構造を持つ"""
        hub = self._make_hub()
        stats = hub.stats()
        assert stats["backends_connected"] == 0
        assert stats["total_calls"] == 0
        assert "pipeline" in stats
        assert "shadow" in stats
        assert "gate" in stats
        assert stats["gate"]["total"] == 0

    # PURPOSE: 不明な Hub ツール呼出テスト
    def test_call_hub_tool_不明ツール(self):
        """不明な Hub ツール名で Error を返す"""
        hub = self._make_hub()
        result = asyncio.run(hub._call_hub_tool("unknown_tool", {}))
        assert len(result) == 1
        assert "Error" in result[0]["text"]

    # PURPOSE: 未接続バックエンドへの call_tool テスト
    def test_call_tool_未接続バックエンド(self):
        """未接続バックエンドへの call_tool で Error を返す"""
        hub = self._make_hub()
        result = asyncio.run(hub.call_tool("nonexistent", "some_tool", {}))
        assert len(result) == 1
        assert "Error" in result[0]["text"]

    # PURPOSE: hub_stats ツール経由で統計取得
    def test_hub_stats_ツール(self):
        """hub_stats ツールが JSON 統計を返す"""
        hub = self._make_hub()
        result = asyncio.run(hub.call_tool("hub", "hub_stats", {}))
        assert len(result) == 1
        data = json.loads(result[0]["text"])
        assert "uptime_seconds" in data
        assert "backends_connected" in data

    def test_axis_router_aggregates_remote_tools(self):
        """local axis router は upstream remote backend のツールも公開する"""
        from mekhane.mcp.hub_mcp_server import HubProxy

        hub = HubProxy(axis="aisthetikon", placement_profile="local")
        local_conn = MagicMock()
        local_conn.tools = [{"name": "search", "description": "", "inputSchema": {}}]
        local_conn.is_connected = True
        hub.backends["phantazein"] = local_conn

        upstream = MagicMock()
        upstream.tools = [
            {"name": "periskope_search", "description": "", "inputSchema": {}},
            {"name": "hub_execute", "description": "", "inputSchema": {}},
        ]
        upstream.is_connected = True
        hub._upstream_axis = upstream

        tools = hub.list_tools_for("aisthetikon")
        names = {tool["name"] for tool in tools}
        assert "search" in names
        assert "periskope_search" in names
        assert "hub_execute" in names

    def test_axis_router_hub_execute_delegates_remote_backend(self):
        """local axis router の hub_execute は remote backend を upstream に委譲する"""
        from mekhane.mcp.hub_mcp_server import HubProxy

        hub = HubProxy(axis="aisthetikon", placement_profile="local")
        upstream = MagicMock()
        upstream.is_connected = True
        upstream.call_tool = AsyncMock(return_value=[{"type": "text", "text": "delegated"}])
        hub._upstream_axis = upstream

        result = asyncio.run(hub._call_hub_tool("hub_execute", {
            "backend": "periskope",
            "tool": "periskope_search",
            "arguments": {"query": "FEP"},
        }))
        upstream.call_tool.assert_awaited_once()
        assert result[0]["text"] == "delegated"

    def test_axis_router_blocks_cross_axis_execute(self):
        """axis router は他軸 backend への hub_execute を拒否する"""
        from mekhane.mcp.hub_mcp_server import HubProxy

        hub = HubProxy(axis="aisthetikon", placement_profile="local")
        result = asyncio.run(hub._call_hub_tool("hub_execute", {
            "backend": "typos",
            "tool": "typos_compile",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        assert "axis" in result_data["error"]


# =============================================================================
# TestHubRecommend — hub_recommend ツールのテスト
# =============================================================================

class TestHubRecommend:
    """hub_recommend ツール推奨エンジンのテスト"""

    def _make_hub(self):
        from mekhane.mcp.hub_mcp_server import HubProxy
        return HubProxy()

    # PURPOSE: CCL 関連タスクで hermeneus が推奨される
    def test_recommend_ccl(self):
        """CCL 関連タスクで hermeneus が推奨される"""
        hub = self._make_hub()
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "CCL 式 /noe+ を実行したい",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        recs = result_data.get("recommendations", [])
        assert len(recs) >= 1
        assert recs[0]["backend"] == "hermeneus"

    # PURPOSE: 論文検索タスクで digestor が推奨される
    def test_recommend_paper(self):
        """論文検索タスクで digestor が推奨される"""
        hub = self._make_hub()
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "論文を検索して引用数を確認したい",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        recs = result_data.get("recommendations", [])
        backends = {r["backend"] for r in recs}
        assert "digestor" in backends or "phantazein" in backends

    # PURPOSE: マッチなしでデフォルト推奨
    def test_recommend_default(self):
        """マッチなしで ask_cortex がデフォルト推奨される"""
        hub = self._make_hub()
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "qwrtyplmnk",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        recs = result_data.get("recommendations", [])
        assert recs[0]["tool"] == "ask_cortex"
        assert recs[0]["match_score"] == 0.0

    # PURPOSE: 空タスク記述でエラー
    def test_recommend_empty(self):
        """空タスク記述でエラーを返す"""
        hub = self._make_hub()
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "",
        }))
        assert "Error" in result[0]["text"]

    # PURPOSE: 英語キーワードの部分文字列が誤マッチしないことを検証
    def test_recommend_boundary_match(self):
        """英語キーワード 'ask' が 'tasking' にマッチしない (単語境界)"""
        hub = self._make_hub()
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "tasking the team with responsibilities",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        recs = result_data.get("recommendations", [])
        # 'ask' は 'tasking' にマッチしてはならない → ochema/ask_cortex が出ないか確認
        cortex_recs = [r for r in recs if r["tool"] == "ask_cortex" and r["match_score"] > 0]
        assert len(cortex_recs) == 0, "部分文字列 'ask' in 'tasking' が誤マッチした"

    # PURPOSE: 日本語キーワードの部分一致は正常にマッチする
    def test_recommend_cjk_partial_match(self):
        """日本語キーワード '論文' が部分一致でマッチする"""
        hub = self._make_hub()
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "最新の論文を読みたい",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        recs = result_data.get("recommendations", [])
        assert any(r["backend"] == "digestor" for r in recs)


# =============================================================================
# TestHubExecute — hub_execute ツールのテスト (S-006 Stage 2)
# =============================================================================


class TestHubExecute:
    """hub_execute の単体テスト (バックエンド接続は mock)"""

    def _make_hub_with_backend(self, backend_name="phantazein", tool_names=None):
        """テスト用 HubProxy にモック済みバックエンドを注入する。"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        hub = HubProxy()

        mock_conn = MagicMock()
        mock_conn.is_connected = True
        mock_conn.tools = [
            {"name": t} for t in (tool_names or ["search", "search_papers"])
        ]
        mock_conn.call_tool = AsyncMock(return_value=[
            {"type": "text", "text": json.dumps({"status": "ok", "results": []})}
        ])
        hub.backends[backend_name] = mock_conn
        return hub, mock_conn

    # PURPOSE: 必須パラメータのバリデーション
    def test_execute_missing_params(self):
        """backend or tool が空欄のときエラーを返す"""
        hub, _ = self._make_hub_with_backend()
        result = asyncio.run(hub._call_hub_tool("hub_execute", {
            "backend": "",
            "tool": "search",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        assert "error" in result_data

    # PURPOSE: 再帰ガード — Hub 自身のツールへの委託を禁止
    def test_execute_self_reference_blocked(self):
        """hub_recommend や hub_execute など Hub 自身のツールは実行できない"""
        hub, _ = self._make_hub_with_backend()
        for tool in ["hub_recommend", "hub_execute",
                     "hub_daimonion_judge", "hub_gate",  # 新名 + 旧名
                     "hub_daimonion_status", "hub_shadow_status",
                     "hub_stats",
                     "hub_aisthetikon", "hub_sense"]:
            result = asyncio.run(hub._call_hub_tool("hub_execute", {
                "backend": "phantazein",
                "tool": tool,
            }))
            data = json.loads(result[0]["text"])
            # build_return_packet で result.error にラップされる
            error_msg = data.get("error", "") or data.get("result", {}).get("error", "")
            assert "自己言及禁止" in error_msg, f"{tool} がブロックされなか��た"

    # PURPOSE: 未接続バックエンドのエラーハンドリング
    def test_execute_unknown_backend(self):
        """存在しないバックエンド指定でエラー + 利用可能バックエンド一覧"""
        hub, _ = self._make_hub_with_backend()
        result = asyncio.run(hub._call_hub_tool("hub_execute", {
            "backend": "nonexistent",
            "tool": "search",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        assert "error" in result_data
        assert "available_backends" in result_data

    # PURPOSE: 存在しないツール指定のエラーハンドリング
    def test_execute_unknown_tool(self):
        """存在しないツール指定でエラー + 利用可能ツール一覧"""
        hub, _ = self._make_hub_with_backend()
        result = asyncio.run(hub._call_hub_tool("hub_execute", {
            "backend": "phantazein",
            "tool": "nonexistent_tool",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        assert "error" in result_data
        assert "available_tools" in result_data
        assert "search" in result_data["available_tools"]

    # PURPOSE: 正常実行 — バックエンドの call_tool に引数が正しく渡される
    def test_execute_success(self):
        """有効なバックエンド+ツール+引数で正常実行"""
        hub, mock_conn = self._make_hub_with_backend()
        result = asyncio.run(hub._call_hub_tool("hub_execute", {
            "backend": "phantazein",
            "tool": "search",
            "arguments": {"query": "FEP", "k": 5},
        }))
        # call_tool が正しい引数で呼ばれたか
        mock_conn.call_tool.assert_called_once_with(
            "search", {"query": "FEP", "k": 5}
        )
        # 結果がそのまま返されるか
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        assert result_data["status"] == "ok"

    # PURPOSE: 実行ログが _call_log に記録される
    def test_execute_logging(self):
        """正常実行後に _call_log にエントリが追加される"""
        hub, _ = self._make_hub_with_backend()
        initial_log_count = len(hub._call_log)
        asyncio.run(hub._call_hub_tool("hub_execute", {
            "backend": "phantazein",
            "tool": "search",
            "arguments": {"query": "test"},
        }))
        assert len(hub._call_log) == initial_log_count + 1
        entry = hub._call_log[-1]
        assert entry["source"] == "hub_execute"
        assert entry["backend"] == "phantazein"
        assert entry["tool"] == "search"
        assert entry["success"] is True

    # PURPOSE: バックエンドエラー時のハンドリング
    def test_execute_backend_error(self):
        """バックエンド call_tool が例外を投げるとき、エラー JSON を返す"""
        hub, mock_conn = self._make_hub_with_backend()
        mock_conn.call_tool = AsyncMock(side_effect=Exception("Connection lost"))
        result = asyncio.run(hub._call_hub_tool("hub_execute", {
            "backend": "phantazein",
            "tool": "search",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        assert "error" in result_data
        assert "Connection lost" in result_data["error"]
        # エラーログも記録される
        entry = hub._call_log[-1]
        assert entry["success"] is False


# =============================================================================
# TestHubRecommendLLM — LLM ベース hub_recommend のテスト
# =============================================================================


class TestHubRecommendLLM:
    """LLM ベースの hub_recommend 推奨エンジンのテスト"""

    def _make_hub_with_ochema(self, *, llm_response: str | None = None,
                               connected: bool = True,
                               side_effect: Exception | None = None):
        """ochema バックエンド付きの HubProxy を作成する。"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        hub = HubProxy()
        mock_conn = MagicMock()
        mock_conn.is_connected = connected

        if side_effect:
            mock_conn.call_tool = AsyncMock(side_effect=side_effect)
        elif llm_response is not None:
            mock_conn.call_tool = AsyncMock(return_value=[
                {"type": "text", "text": llm_response}
            ])
        else:
            mock_conn.call_tool = AsyncMock(return_value=[
                {"type": "text", "text": "[]"}
            ])

        hub.backends["ochema"] = mock_conn
        return hub, mock_conn

    # PURPOSE: LLM 推奨が正常動作し推奨が返る
    def test_llm_recommend_success(self):
        """LLM が正常な JSON を返すとき、推奨リストが返る"""
        llm_json = json.dumps([
            {"backend": "periskope", "tool": "periskope_research",
             "reason": "調査タスクに最適"},
            {"backend": "phantazein", "tool": "mneme_search",
             "reason": "既存知識の確認"},
        ])
        hub, _ = self._make_hub_with_ochema(llm_response=llm_json)
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "自由エネルギー原理の最新動向を調べたい",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        recs = result_data.get("recommendations", [])
        assert len(recs) == 2
        assert recs[0]["backend"] == "periskope"
        assert recs[0]["tool"] == "periskope_research"
        assert "LLM推論" in result_data["note"]

    # PURPOSE: 返却形式が既存の keyword 推奨と互換
    def test_llm_recommend_format_compatible(self):
        """LLM 推奨の返却形式が既存と互換 (全フィールド存在)"""
        llm_json = json.dumps([
            {"backend": "digestor", "tool": "paper_search",
             "reason": "論文検索に最適"},
        ])
        hub, _ = self._make_hub_with_ochema(llm_response=llm_json)
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "transformer の論文を探す",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        rec = result_data["recommendations"][0]
        # 必須フィールドが全て存在
        required = {"backend", "tool", "reason", "match_score",
                    "importance", "complexity", "connected"}
        assert required.issubset(rec.keys()), f"欠損: {required - rec.keys()}"

    # PURPOSE: ochema 未接続時にキーワードマッチにフォールバック
    def test_llm_recommend_fallback_on_ochema_offline(self):
        """ochema 未接続→キーワードマッチにフォールバック"""
        hub, _ = self._make_hub_with_ochema(connected=False)
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "CCL 式 /noe+ を実行したい",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        # フォールバックしていることを note で確認
        assert "フォールバック" in result_data["note"]
        # キーワードマッチで hermeneus が推奨される
        assert result_data["recommendations"][0]["backend"] == "hermeneus"

    # PURPOSE: LLM 応答がパースできないときフォールバック
    def test_llm_recommend_fallback_on_parse_error(self):
        """LLM が無効な JSON を返す→フォールバック"""
        hub, _ = self._make_hub_with_ochema(
            llm_response="これはJSONではありません"
        )
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "論文を検索したい",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        assert "フォールバック" in result_data["note"]

    # PURPOSE: Hub 自身のツールが LLM 推奨から除外される
    def test_llm_recommend_excludes_hub_self_tools(self):
        """LLM が Hub 自身のツールを推奨しても除外される"""
        llm_json = json.dumps([
            {"backend": "hub", "tool": "hub_recommend",
             "reason": "推奨エンジン"},
            {"backend": "periskope", "tool": "periskope_search",
             "reason": "外部検索"},
        ])
        hub, _ = self._make_hub_with_ochema(llm_response=llm_json)
        result = asyncio.run(hub._call_hub_tool("hub_recommend", {
            "task_description": "何か推奨して",
        }))
        data = json.loads(result[0]["text"])
        result_data = data.get("result", data)
        recs = result_data.get("recommendations", [])
        # hub_recommend は除外されている
        tools = {r["tool"] for r in recs}
        assert "hub_recommend" not in tools
        # periskope_search は残る
        assert "periskope_search" in tools

    # PURPOSE: キーワードマッチ (リネーム後) が引き続き動作する
    def test_keyword_recommend_still_works(self):
        """_recommend_backend_keyword が引き続き正常に動作する"""
        from mekhane.mcp.hub_mcp_server import HubProxy
        hub = HubProxy()
        recs = hub._recommend_backend_keyword("CCL 式を解析したい", 3)
        assert len(recs) >= 1
        assert recs[0]["backend"] == "hermeneus"
