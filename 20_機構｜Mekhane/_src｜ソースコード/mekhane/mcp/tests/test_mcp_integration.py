#!/usr/bin/env python3
# PROOF: mekhane/mcp/tests/test_mcp_integration.py
# PURPOSE: mcp モジュールの mcp_integration に対するテスト
"""
MCP Server Integration Tests — mneme/ochema 統合後の回帰テスト

mneme_server.py に統合した gnosis/sophia tools と
ochema_mcp_server.py に統合した jules tools をテストする。
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


# ============ mneme: search_papers ============

class TestMnemeSearchPapers:
    """gnosis → mneme に移植した search_papers のテスト"""

    def test_search_papers_returns_results(self):
        """正常ケース: 論文検索で結果が返る"""
        mock_results = [
            {
                "title": "Free Energy Principle",
                "source": "semantic_scholar",
                "citations": 100,
                "authors": "Karl Friston",
                "abstract": "The free energy principle...",
                "url": "https://example.com/paper1",
            }
        ]

        with patch("mekhane.anamnesis.index.GnosisIndex") as MockIndex:
            instance = MockIndex.return_value
            instance.search.return_value = mock_results

            # mneme_server の handler を直接テスト
            from mekhane.mcp.mneme_server import _handle_search_papers

            result = _handle_search_papers({"query": "free energy", "limit": 5})
            assert len(result) == 1
            text = result[0].text
            assert "Free Energy Principle" in text
            assert "Karl Friston" in text
            assert "100" in text

    def test_search_papers_empty_query(self):
        """空クエリでエラーメッセージ"""
        from mekhane.mcp.mneme_server import _handle_search_papers

        result = _handle_search_papers({"query": ""})
        assert "Error" in result[0].text

    def test_search_papers_no_results(self):
        """結果なしのケース"""
        with patch("mekhane.anamnesis.index.GnosisIndex") as MockIndex:
            instance = MockIndex.return_value
            instance.search.return_value = []

            from mekhane.mcp.mneme_server import _handle_search_papers

            result = _handle_search_papers({"query": "nonexistent_topic_xyz"})
            assert "No results" in result[0].text


class TestMnemeSearchFacade:
    """search ファサードの入口分離テスト。"""

    def test_search_facade_defaults_to_document_sources(self):
        """scope=all のデフォルトは code を含めない。"""
        from mekhane.mcp import mneme_server

        calls = {}

        def fake_handle_search(arguments):
            calls["arguments"] = arguments
            return [mneme_server.TextContent(type="text", text="ok")]

        with patch.object(mneme_server, "_handle_search", side_effect=fake_handle_search):
            result = asyncio.run(
                mneme_server._handle_search_facade({"query": "BBS proposal"})
            )

        assert result[0].text == "ok"
        assert calls["arguments"]["sources"] == [
            "gnosis",
            "sophia",
            "hgk_core",
            "chronos",
            "kairos",
        ]

    def test_search_facade_rejects_mixed_code_and_docs(self):
        """code と文書ソースを同じ scope=all ランキングへ混ぜない。"""
        from mekhane.mcp.mneme_server import _handle_search_facade

        result = asyncio.run(
            _handle_search_facade(
                {
                    "query": "BBS proposal",
                    "scope": "all",
                    "sources": ["code", "sophia"],
                }
            )
        )

        assert "CODE_SEARCH_SEPARATED" in result[0].text
        assert "scope='code'" in result[0].text

    def test_code_search_explains_score_semantics(self):
        """code search の Score が何の類似度かを表示する。"""
        from mekhane.mcp import mneme_server

        class FakeResult:
            score = 0.687
            doc_id = "demo"
            content = "def propose(): pass"
            metadata = {
                "ki_name": "Demo.propose()",
                "file_path": "demo.py",
                "line_start": 1,
                "line_end": 3,
            }

        class FakeEngine:
            def search(self, query, sources=None, k=10):
                return [FakeResult()]

        with patch.object(mneme_server, "get_engine", return_value=FakeEngine()):
            result = mneme_server._handle_search_code(
                {"query": "proposal", "code_mode": "text"}
            )

        assert "code chunk embedding の cosine 類似度" in result[0].text
        assert "命題支持の強さではありません" in result[0].text


# ============ mneme: recommend_model ============

class TestMnemeRecommendModel:
    """gnosis → mneme に移植した recommend_model のテスト"""

    def test_p1_security(self):
        async def _impl():
            """P1: セキュリティタスク → Claude"""
            from mekhane.mcp.mneme_server import _handle_recommend_model

            result = await _handle_recommend_model({"task_description": "security audit of API"})
            text = result[0].text
            assert "P1" in text
            assert "Claude" in text
        asyncio.run(_impl())

    def test_p2_visual(self):
        async def _impl():
            """P2: 画像/UI タスク → Gemini"""
            from mekhane.mcp.mneme_server import _handle_recommend_model

            result = await _handle_recommend_model({"task_description": "UI design for dashboard"})
            text = result[0].text
            assert "P2" in text
            assert "Gemini" in text
        asyncio.run(_impl())

    def test_p4_batch(self):
        async def _impl():
            """P4: 高速/バッチタスク → Gemini Flash"""
            from mekhane.mcp.mneme_server import _handle_recommend_model

            result = await _handle_recommend_model({"task_description": "fast batch triage"})
            text = result[0].text
            assert "P4" in text
            assert "Gemini Flash" in text
        asyncio.run(_impl())

    def test_p5_default(self):
        async def _impl():
            """P5: マッチなし → Claude (default)"""
            from mekhane.mcp.mneme_server import _handle_recommend_model

            result = await _handle_recommend_model({"task_description": "generic task analysis"})
            text = result[0].text
            assert "P5" in text
            assert "Claude" in text
        asyncio.run(_impl())

    def test_empty_description(self):
        async def _impl():
            """空の task_description でエラー"""
            from mekhane.mcp.mneme_server import _handle_recommend_model

            result = await _handle_recommend_model({"task_description": ""})
            assert "Error" in result[0].text
        asyncio.run(_impl())


# ============ mneme: backlinks ============

class TestMnemeBacklinks:
    """sophia → mneme に移植した backlinks のテスト"""

    def test_backlinks_returns_links(self):
        async def _impl():
            """バックリンクが正しく返る"""
            with patch("mekhane.symploke.sophia_backlinker.SophiaBacklinker") as MockBL:
                instance = MockBL.return_value
                instance.build_graph.return_value = 5
                instance.get_backlinks.return_value = {"KI_A", "KI_B"}
                instance.get_outlinks.return_value = {"KI_C"}

                from mekhane.mcp.mneme_server import _handle_backlinks

                result = await _handle_backlinks({"ki_name": "FEP"})
                text = result[0].text
                assert "KI_A" in text
                assert "KI_B" in text
        asyncio.run(_impl())

    def test_backlinks_empty_ki(self):
        async def _impl():
            """空の ki_name でエラー"""
            from mekhane.mcp.mneme_server import _handle_backlinks

            result = await _handle_backlinks({"ki_name": ""})
            assert "Error" in result[0].text
        asyncio.run(_impl())


# ============ mneme: graph_stats ============

class TestMnemeGraphStats:
    """sophia → mneme に移植した graph_stats のテスト"""

    def test_graph_stats_returns_stats(self):
        async def _impl():
            """グラフ統計が返る"""
            with patch("mekhane.symploke.sophia_backlinker.SophiaBacklinker") as MockBL:
                instance = MockBL.return_value
                instance.build_graph.return_value = 10
                instance.get_stats.return_value = {
                    "nodes": 20,
                    "edges": 15,
                    "isolated": 3,
                    "most_linked": [("FEP", 5), ("HGK", 3)],
                }

                from mekhane.mcp.mneme_server import _handle_graph_stats

                result = await _handle_graph_stats({})
                text = result[0].text
                assert "20" in text
                assert "15" in text
        asyncio.run(_impl())


# ============ ochema: jules API key pool ============

@pytest.mark.skip(reason="_jules_init_pool/_jules_get_key は ochema_mcp_server.py から削除済み (jules_mcp_server.py に分離)")
class TestOchemaJulesPool:
    """jules → ochema に移植した API key pool のテスト"""

    def test_jules_init_pool(self):
        """API key pool の初期化"""
        import mekhane.mcp.ochema_mcp_server as ochema

        ochema._jules_api_key_pool = []

        env_vars = {f"JULES_API_KEY_{i:02d}": f"test_key_{i}" for i in range(1, 4)}
        with patch.dict("os.environ", env_vars, clear=False):
            ochema._jules_init_pool()
            assert len(ochema._jules_api_key_pool) >= 3

    def test_jules_get_key_round_robin(self):
        """Round-robin でキーが巡回する"""
        import mekhane.mcp.ochema_mcp_server as ochema

        ochema._jules_api_key_pool = [(1, "key_a"), (2, "key_b"), (3, "key_c")]
        ochema._jules_api_key_index = 0
        ochema._jules_dashboard = None

        key1, idx1 = ochema._jules_get_key()
        key2, idx2 = ochema._jules_get_key()
        key3, idx3 = ochema._jules_get_key()

        assert key1 == "key_a"
        assert key2 == "key_b"
        assert key3 == "key_c"

    def test_jules_get_key_empty_pool(self):
        """空プールでは None を返す"""
        import mekhane.mcp.ochema_mcp_server as ochema

        ochema._jules_api_key_pool = []
        with patch.dict("os.environ", {}, clear=True):
            key, idx = ochema._jules_get_key()
            # キーがない場合 None
            assert key is None


# ============ ochema: jules handler ============

@pytest.mark.skip(reason="_handle_jules は ochema_mcp_server.py から削除済み (jules_mcp_server.py に分離)")
class TestOchemaJulesHandler:
    """jules → ochema に移植した _handle_jules のテスト"""

    def test_jules_create_task_missing_params(self):
        async def _impl():
            """必須パラメータ不足でエラー"""
            import mekhane.mcp.ochema_mcp_server as ochema

            ochema._jules_api_key_pool = [(1, "test_key")]
            ochema._jules_api_key_index = 0

            from mekhane.mcp.ochema_mcp_server import _handle_jules

            result = await _handle_jules("jules_create_task", {"prompt": "", "repo": ""})
            assert "Error" in result[0].text
        asyncio.run(_impl())

    def test_jules_get_status_missing_id(self):
        async def _impl():
            """session_id 不足でエラー"""
            import mekhane.mcp.ochema_mcp_server as ochema

            ochema._jules_api_key_pool = [(1, "test_key")]
            ochema._jules_api_key_index = 0

            from mekhane.mcp.ochema_mcp_server import _handle_jules

            result = await _handle_jules("jules_get_status", {"session_id": ""})
            assert "Error" in result[0].text
        asyncio.run(_impl())

    def test_jules_list_repos(self):
        async def _impl():
            """list_repos は stub メッセージを返す"""
            import mekhane.mcp.ochema_mcp_server as ochema

            ochema._jules_api_key_pool = [(1, "test_key")]
            ochema._jules_api_key_index = 0

            from mekhane.mcp.ochema_mcp_server import _handle_jules

            result = await _handle_jules("jules_list_repos", {})
            assert "Repositories" in result[0].text
        asyncio.run(_impl())

    def test_jules_no_api_keys(self):
        async def _impl():
            """API キーなしでエラー"""
            import mekhane.mcp.ochema_mcp_server as ochema

            ochema._jules_api_key_pool = []

            with patch.dict("os.environ", {}, clear=True):
                from mekhane.mcp.ochema_mcp_server import _handle_jules

                result = await _handle_jules("jules_create_task", {"prompt": "test", "repo": "owner/repo"})
                assert "Error" in result[0].text or "No JULES" in result[0].text
        asyncio.run(_impl())

    def test_jules_batch_empty_tasks(self):
        async def _impl():
            """空タスクリストでエラー"""
            import mekhane.mcp.ochema_mcp_server as ochema

            ochema._jules_api_key_pool = [(1, "test_key")]
            ochema._jules_api_key_index = 0

            from mekhane.mcp.ochema_mcp_server import _handle_jules

            result = await _handle_jules("jules_batch_execute", {"tasks": []})
            assert "Error" in result[0].text
        asyncio.run(_impl())


# ============ digestor: semantic scholar ============

class TestDigestorS2:
    """semantic-scholar → digestor に移植した S2 tools のテスト"""

    def _mock_paper(self, title="Test Paper", year=2025, citations=42):
        """テスト用 Paper 互換オブジェクト"""
        p = MagicMock()
        p.paper_id = "abc123"
        p.title = title
        p.year = year
        p.abstract = "An abstract."
        p.citation_count = citations
        p.doi = "10.1234/test"
        p.arxiv_id = None
        p.url = "https://example.com/paper"
        p.authors = ["Author A", "Author B"]
        return p

    def test_paper_search_returns_results(self):
        async def _impl():
            """paper_search で結果が返る"""
            paper = self._mock_paper()

            with patch("mekhane.pks.semantic_scholar.SemanticScholarClient") as MockClient:
                instance = MockClient.return_value
                instance.search.return_value = [paper]

                from mekhane.mcp.digestor_mcp_server import handle_semantic_scholar

                result = await handle_semantic_scholar("paper_search", {"query": "FEP"})
                text = result[0].text
                assert "Test Paper" in text
                assert "42" in text
        asyncio.run(_impl())

    def test_paper_search_empty_query(self):
        async def _impl():
            """空クエリでエラー"""
            from mekhane.mcp.digestor_mcp_server import handle_semantic_scholar

            result = await handle_semantic_scholar("paper_search", {"query": ""})
            assert "Error" in result[0].text
        asyncio.run(_impl())

    def test_paper_details_returns_info(self):
        async def _impl():
            """paper_details で論文詳細が返る"""
            paper = self._mock_paper(title="FEP Paper")

            with patch("mekhane.pks.semantic_scholar.SemanticScholarClient") as MockClient:
                instance = MockClient.return_value
                instance.get_paper.return_value = paper

                from mekhane.mcp.digestor_mcp_server import handle_semantic_scholar

                result = await handle_semantic_scholar("paper_details", {"paper_id": "abc123"})
                text = result[0].text
                assert "FEP Paper" in text
                assert "42" in text
        asyncio.run(_impl())

    def test_paper_details_empty_id(self):
        async def _impl():
            """空 paper_id でエラー"""
            from mekhane.mcp.digestor_mcp_server import handle_semantic_scholar

            result = await handle_semantic_scholar("paper_details", {"paper_id": ""})
            assert "Error" in result[0].text
        asyncio.run(_impl())

    def test_paper_citations_returns_list(self):
        async def _impl():
            """paper_citations で被引用論文リストが返る"""
            papers = [self._mock_paper(title="Citing Paper", citations=10)]

            with patch("mekhane.pks.semantic_scholar.SemanticScholarClient") as MockClient:
                instance = MockClient.return_value
                instance.get_citations.return_value = papers

                from mekhane.mcp.digestor_mcp_server import handle_semantic_scholar

                result = await handle_semantic_scholar("paper_citations", {"paper_id": "abc123"})
                text = result[0].text
                assert "Citing Paper" in text
                assert "10" in text
        asyncio.run(_impl())

    def test_paper_citations_empty_id(self):
        async def _impl():
            """空 paper_id でエラー"""
            from mekhane.mcp.digestor_mcp_server import handle_semantic_scholar

            result = await handle_semantic_scholar("paper_citations", {"paper_id": ""})
            assert "Error" in result[0].text
        asyncio.run(_impl())


# ============ sympatheia: basanos_scan ============

class TestSympatheiBasanosScan:
    """basanos_scan ツールのテスト"""

    def test_basanos_import_ok(self):
        async def _impl():
            """AIAuditor が正しくインポートできる"""
            from mekhane.basanos.ai_auditor import AIAuditor
            auditor = AIAuditor(strict=False)
            assert auditor is not None
        asyncio.run(_impl())

    def test_basanos_scan_missing_path(self):
        async def _impl():
            """path 未指定でエラー"""
            from mekhane.mcp.sympatheia_mcp_server import _handle_basanos_scan
            result = await _handle_basanos_scan({})
            assert "Error" in result[0].text
        asyncio.run(_impl())

    def test_basanos_scan_nonexistent_path(self):
        async def _impl():
            """存在しないパスでエラー"""
            from mekhane.mcp.sympatheia_mcp_server import _handle_basanos_scan
            result = await _handle_basanos_scan({"path": "/nonexistent/file.py"})
            assert "not found" in result[0].text
        asyncio.run(_impl())

    def test_basanos_scan_file(self, tmp_path):
        async def _impl():
            """正常ケース: 単一ファイルスキャン"""
            test_file = tmp_path / "test_sample.py"
            test_file.write_text("x = 1\n")

            from mekhane.mcp.sympatheia_mcp_server import _handle_basanos_scan
            result = await _handle_basanos_scan({"path": str(test_file)})
            # Either no issues or issues found — both are valid
            assert len(result) == 1
            assert isinstance(result[0].text, str)
        asyncio.run(_impl())


# ============ sympatheia: peira_health ============

class TestSympatheiaPeiraHealth:
    """peira_health ツールのテスト"""

    def test_peira_import_ok(self):
        async def _impl():
            """run_health_check / format_terminal が正しくインポートできる"""
            from mekhane.peira.hgk_health import run_health_check, format_terminal
            assert callable(run_health_check)
            assert callable(format_terminal)
        asyncio.run(_impl())

    def test_peira_health_returns_text(self):
        async def _impl():
            """peira_health がテキスト結果を返す"""
            from mekhane.mcp.sympatheia_mcp_server import _handle_peira_health
            result = await _handle_peira_health()
            assert len(result) == 1
            assert isinstance(result[0].text, str)
            # Should contain some health-related output
            assert len(result[0].text) > 0
        asyncio.run(_impl())


# ============ mneme: dendron_check ============

class TestMnemeDendronCheck:
    """dendron_check ツールのテスト"""

    def test_dendron_import_ok(self):
        async def _impl():
            """DendronChecker が正しくインポートできる"""
            from mekhane.dendron.checker import DendronChecker
            checker = DendronChecker()
            assert checker is not None
        asyncio.run(_impl())

    def test_dendron_check_missing_path(self):
        async def _impl():
            """path 未指定でエラー"""
            from mekhane.mcp.mneme_server import _handle_dendron_check
            result = await _handle_dendron_check({})
            assert "Error" in result[0].text or "path" in result[0].text.lower()
        asyncio.run(_impl())

    def test_dendron_check_nonexistent_path(self):
        async def _impl():
            """存在しないパスでエラー"""
            from mekhane.mcp.mneme_server import _handle_dendron_check
            result = await _handle_dendron_check({"path": "/nonexistent/file.py"})
            assert "not found" in result[0].text or "Error" in result[0].text
        asyncio.run(_impl())

    def test_dendron_check_file(self, tmp_path):
        async def _impl():
            """正常ケース: PROOF ヘッダー付きファイル"""
            test_file = tmp_path / "test_proof.py"
            test_file.write_text("# PROOF: [L1/test] <- test\n# PURPOSE: test\nx = 1\n")

            from mekhane.mcp.mneme_server import _handle_dendron_check
            result = await _handle_dendron_check({"path": str(test_file)})
            assert len(result) == 1
            assert isinstance(result[0].text, str)
        asyncio.run(_impl())


# ============ mneme: dejavu_check / dejavu_history ============

class TestMnemeDejavu:
    """デジャブ検出ツールのテスト"""

    def test_dejavu_check_empty_text(self):
        """空テキストでエラーを返す"""
        from mekhane.mcp.mneme_server import _handle_dejavu_check
        result = _handle_dejavu_check({"text": ""})
        assert len(result) == 1
        assert "Error" in result[0].text

    def test_dejavu_check_novel_no_engine(self):
        """SearchEngine が None のとき stub 応答を返す"""
        from unittest.mock import patch
        from mekhane.mcp.mneme_server import _handle_dejavu_check

        with patch("mekhane.mcp.mneme_server.get_engine", return_value=None):
            result = _handle_dejavu_check({"text": "まったく新しいテスト入力"})
            assert len(result) == 1
            assert "stub" in result[0].text.lower() or "not available" in result[0].text.lower()

    def test_dejavu_check_novel_below_threshold(self):
        """類似度が閾値未満のとき NOVEL を返す"""
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.score = 0.50
        mock_result.content = "既存ドキュメントの内容"
        mock_result.source = MagicMock()
        mock_result.source.value = "sophia"
        mock_result.doc_id = "test_doc_001"

        mock_engine = MagicMock()
        mock_engine.search.return_value = [mock_result]

        from mekhane.mcp.mneme_server import _handle_dejavu_check

        with patch("mekhane.mcp.mneme_server.get_engine", return_value=mock_engine):
            with patch("mekhane.mcp.mneme_server._dejavu_log_entry"):
                result = _handle_dejavu_check({"text": "新しいテスト入力", "threshold": 0.80})
                assert len(result) == 1
                assert "NOVEL" in result[0].text

    def test_dejavu_check_similar_above_threshold(self):
        """類似度が閾値以上のとき LLM 判定に進む (LLM は mock)"""
        from unittest.mock import patch, MagicMock

        mock_result = MagicMock()
        mock_result.score = 0.92
        mock_result.content = "既に存在する類似ドキュメント"
        mock_result.source = MagicMock()
        mock_result.source.value = "sophia"
        mock_result.doc_id = "existing_doc_001"

        mock_engine = MagicMock()
        mock_engine.search.return_value = [mock_result]

        # LLM の応答を mock
        mock_llm_response = MagicMock()
        mock_llm_response.text = '{"verdict": "SIMILAR", "reason": "関連する既存成果物あり", "references": ["existing_doc_001"]}'

        mock_client = MagicMock()
        mock_client.ask.return_value = mock_llm_response

        from mekhane.mcp.mneme_server import _handle_dejavu_check

        with patch("mekhane.mcp.mneme_server.get_engine", return_value=mock_engine):
            with patch("mekhane.mcp.mneme_server._dejavu_log_entry"):
                with patch("mekhane.ochema.cortex_client.CortexClient", return_value=mock_client):
                    result = _handle_dejavu_check({"text": "類似テスト入力"})
                    assert len(result) == 1
                    assert "SIMILAR" in result[0].text

    def test_dejavu_history_empty(self, tmp_path):
        async def _impl():
            """ログファイルが存在しないとき空メッセージを返す"""
            from unittest.mock import patch
            from mekhane.mcp.mneme_server import _handle_dejavu_history

            with patch("mekhane.mcp.mneme_server._DEJAVU_LOG", tmp_path / "nonexistent.jsonl"):
                result = await _handle_dejavu_history({})
                assert len(result) == 1
                assert "まだありません" in result[0].text
        asyncio.run(_impl())

    def test_dejavu_history_with_entries(self, tmp_path):
        async def _impl():
            """ログエントリがあるとき履歴を返す"""
            import json
            from unittest.mock import patch
            from mekhane.mcp.mneme_server import _handle_dejavu_history

            log_file = tmp_path / "test_dejavu_log.jsonl"
            entry = {
                "timestamp": "2026-03-17T13:00:00+00:00",
                "input_preview": "テスト入力プレビュー",
                "verdict": "NOVEL",
                "reason": "類似候補なし",
                "references": [],
                "hit_count": 0,
                "top_scores": [0.3, 0.2],
            }
            log_file.write_text(json.dumps(entry, ensure_ascii=False) + "\n")

            with patch("mekhane.mcp.mneme_server._DEJAVU_LOG", log_file):
                result = await _handle_dejavu_history({"limit": 5})
                assert len(result) == 1
                assert "NOVEL" in result[0].text
                assert "テスト入力プレビュー" in result[0].text
        asyncio.run(_impl())


# ============ mneme: 旧ツール名エイリアス ============

class TestMnemeLegacyToolAliases:
    """Hub / hub_execute が旧名 (mneme_search 等) で呼んでもファサードに正規化される"""

    def test_mneme_search_to_search(self):
        from mekhane.mcp.mneme_server import _normalize_legacy_tool

        n, a = _normalize_legacy_tool("mneme_search", {"query": "FEP", "k": 3})
        assert n == "search"
        assert a == {"query": "FEP", "k": 3}

    def test_search_papers_sets_scope(self):
        from mekhane.mcp.mneme_server import _normalize_legacy_tool

        n, a = _normalize_legacy_tool("search_papers", {"query": "ai", "limit": 5})
        assert n == "search"
        assert a["scope"] == "papers"
        assert a["query"] == "ai"

    def test_dejavu_check_to_check(self):
        from mekhane.mcp.mneme_server import _normalize_legacy_tool

        n, a = _normalize_legacy_tool("dejavu_check", {"text": "hello"})
        assert n == "check"
        assert a["action"] == "dejavu"

    def test_mneme_backlinks_to_graph(self):
        from mekhane.mcp.mneme_server import _normalize_legacy_tool

        n, a = _normalize_legacy_tool("mneme_backlinks", {"ki_name": "kalon"})
        assert n == "graph"
        assert a["action"] == "backlinks"
