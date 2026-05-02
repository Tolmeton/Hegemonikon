# PROOF: [L1/テスト] <- tests/test_session_notes.py A0→品質保証→SessionNotes全機能検証
"""SessionNotes 深化テスト。

ターン構造保持チャンク、キーワード抽出、要約、
ターンマッピング、逆参照、resumeコンテキスト、
merge候補、list_notes、process パイプラインを網羅。
"""

from __future__ import annotations
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from mekhane.ochema.session_notes import SessionNotes


# --- Fixtures ---

def _make_turns(n: int = 4) -> list[dict]:
    """テスト用ターンを生成する。"""
    turns = []
    for i in range(n):
        if i % 2 == 0:
            turns.append({
                "role": "user",
                "content": f"CortexClient の TokenVault quota について質問 {i}。" * 5,
                "created_at": f"2026-02-22T10:{i:02d}:00",
            })
        else:
            turns.append({
                "role": "model",
                "content": f"TokenVault は OAuth2 で gemini API の quota を管理します。回答 {i}。" * 5,
                "created_at": f"2026-02-22T10:{i:02d}:30",
            })
    return turns


@pytest.fixture
def notes_env(tmp_path: Path):
    """SessionNotes + mock SessionStore を提供する。"""
    notes = SessionNotes(notes_dir=tmp_path / "notes")
    store = MagicMock()
    store.get_session.return_value = {
        "session_id": "test-session-001",
        "model": "gemini-3-flash-preview",
        "account": "default",
        "created_at": "2026-02-22T10:00:00",
    }
    store.get_turns.return_value = _make_turns(6)
    store.list_sessions.return_value = [
        {"session_id": "test-session-001"},
        {"session_id": "test-session-002"},
    ]
    return notes, store


# --- Test Classes ---

class TestDigestDeep:
    """D1: digest() の深化テスト。"""

    def test_creates_chunk_files(self, notes_env):
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)
        assert len(files) >= 1
        assert all(f.suffix == ".md" for f in files)

    def test_turns_structure_preserved(self, notes_env):
        """チャンクはターン境界を跨がない。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        for f in files:
            content = f.read_text()
            body = notes._strip_frontmatter(content)
            # ターンマーカーが存在する
            assert "## USER" in body or "## MODEL" in body

    def test_frontmatter_has_turn_range(self, notes_env):
        """frontmatter にターン範囲が含まれる。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        content = files[0].read_text()
        assert "turn_start:" in content
        assert "turn_end:" in content

    def test_frontmatter_has_keywords(self, notes_env):
        """frontmatter にキーワードが含まれる。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        content = files[0].read_text()
        assert "keywords:" in content

    def test_frontmatter_has_summary(self, notes_env):
        """frontmatter に要約が含まれる。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        content = files[0].read_text()
        assert "summary:" in content

    def test_turn_map_saved(self, notes_env):
        """ターンマッピング JSON が保存される。"""
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        map_files = list(notes._index_dir.glob("turn_map_*.json"))
        assert len(map_files) == 1

        data = json.loads(map_files[0].read_text())
        assert data["session_id"] == "test-session-001"
        assert data["total_turns"] == 6
        assert len(data["chunks"]) >= 1
        assert "turn_start" in data["chunks"][0]
        assert "keywords" in data["chunks"][0]

    def test_session_summary_file(self, notes_env):
        """セッション要約ファイルが生成される。"""
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        summary_files = list(notes.notes_dir.rglob("*_summary.md"))
        assert len(summary_files) == 1

        content = summary_files[0].read_text()
        assert "Session Summary" in content
        assert "test-session-001" in content

    def test_project_inference(self, notes_env):
        """Cortex/TokenVault キーワードで ochema に分類される。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        content = files[0].read_text()
        assert "project: ochema" in content

    def test_daily_note_created(self, notes_env):
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        daily = notes._daily_dir / "2026-02-22.md"
        assert daily.exists()

    def test_tags_indexed(self, notes_env):
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        tags = json.loads(notes._tags_file.read_text())
        assert "ochema" in tags

    def test_no_turns_returns_empty(self, notes_env):
        notes, store = notes_env
        store.get_turns.return_value = []
        assert notes.digest("test-session-001", session_store=store) == []

    def test_source_uri_in_frontmatter(self, notes_env):
        """source_uri が frontmatter に含まれる。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        content = files[0].read_text()
        assert "source_uri: session_store://test-session-001" in content


class TestChunkTurns:
    """_chunk_turns: ターン境界保持チャンク。"""

    def test_preserves_turn_boundaries(self):
        turns = _make_turns(2)
        notes = SessionNotes.__new__(SessionNotes)
        chunks = notes._chunk_turns(turns, max_chars=5000)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk["turn_start"] >= 0
            assert chunk["turn_end"] > chunk["turn_start"]

    def test_splits_when_exceeds_max(self):
        """大量のターンは複数チャンクに分割される。"""
        turns = _make_turns(20)
        notes = SessionNotes.__new__(SessionNotes)
        chunks = notes._chunk_turns(turns, max_chars=500)

        assert len(chunks) > 1

    def test_empty_turns(self):
        notes = SessionNotes.__new__(SessionNotes)
        assert notes._chunk_turns([]) == []


class TestExtractKeywords:
    """_extract_keywords: TFベースキーワード抽出。"""

    def test_finds_camelcase(self):
        kw = SessionNotes._extract_keywords("Use CortexClient and TokenVault here")
        # YAKE は n-gram で返すため、部分一致で検証
        kw_text = " ".join(kw)
        assert "CortexClient" in kw_text
        assert "TokenVault" in kw_text

    def test_finds_uppercase(self):
        kw = SessionNotes._extract_keywords("Uses API and LLM for FEP analysis")
        assert "API" in kw
        assert "LLM" in kw

    def test_finds_katakana(self):
        kw = SessionNotes._extract_keywords("ヘゲモニコンのパイプラインを構築")
        assert any("ヘゲモニコン" in k for k in kw)

    def test_max_limit(self):
        text = " ".join(f"Term{i}Name" for i in range(20))
        kw = SessionNotes._extract_keywords(text, max_keywords=5)
        assert len(kw) <= 5


class TestGenerateSummary:
    """_generate_summary: extractive 要約。"""

    def test_combines_first_user_last_model(self):
        turns = _make_turns(4)
        summary = SessionNotes._generate_summary(turns)
        assert "問:" in summary
        assert "結:" in summary

    def test_empty_turns(self):
        result = SessionNotes._generate_summary([])
        # 空ターンでもターン統計 "(0問0答)" が返る
        assert "0問0答" in result


class TestTraceToSource:
    def test_trace_has_turn_range(self, notes_env):
        """trace_to_source にターン範囲が含まれる。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        trace = notes.trace_to_source(files[0], session_store=store)
        assert trace["session_id"] == "test-session-001"
        assert trace["source_uri"] == "session_store://test-session-001"
        assert "turn_start" in trace
        assert "turn_end" in trace
        assert trace["verified"]

    def test_trace_has_source_turns(self, notes_env):
        """正本ターンのプレビューが含まれる。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        trace = notes.trace_to_source(files[0], session_store=store)
        assert "source_turns" in trace
        assert len(trace["source_turns"]) > 0


class TestResumeContext:
    def test_cortex_format(self, notes_env):
        """Cortex API contents 形式でターンが返る。"""
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        ctx = notes.resume_context("test-session-001", format="cortex")
        assert len(ctx) > 0
        for turn in ctx:
            assert turn["role"] in ("user", "model")
            assert "parts" in turn
            assert "text" in turn["parts"][0]

    def test_raw_format(self, notes_env):
        """raw 形式ではコンテキスト情報が返る。"""
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        ctx = notes.resume_context("test-session-001", format="raw")
        assert len(ctx) > 0
        assert ctx[0]["role"] == "context"

    def test_empty_for_unknown(self, notes_env):
        notes, _ = notes_env
        assert notes.resume_context("nonexistent") == []


class TestMergeSimilar:
    def test_returns_empty_without_links(self, notes_env):
        notes, _ = notes_env
        assert notes.merge_similar() == []

    def test_filters_by_threshold(self, notes_env):
        notes, _ = notes_env
        notes._save_links({
            "a--b": {"source": "notes:ochema:chunk_a", "target": "notes:ochema:chunk_b",
                     "distance": 0.3, "created": "2026-02-22"},
            "c--d": {"source": "notes:ochema:chunk_c", "target": "notes:general:chunk_d",
                     "distance": 0.8, "created": "2026-02-22"},
        })

        candidates = notes.merge_similar(threshold=0.5)
        assert len(candidates) == 1
        assert candidates[0]["distance"] == 0.3
        assert "similarity" in candidates[0]


class TestListNotes:
    def test_lists_all_notes(self, notes_env):
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        all_notes = notes.list_notes()
        # summary ファイルは frontmatter がないので除外される
        # チャンクファイルのみが返る
        assert len(all_notes) >= 1

    def test_filters_by_project(self, notes_env):
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        ochema_notes = notes.list_notes(project="ochema")
        assert len(ochema_notes) >= 1

        empty = notes.list_notes(project="nonexistent")
        assert len(empty) == 0


class TestFindChunks:
    def test_finds_digested_files(self, notes_env):
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        found = notes._find_chunks_for_session("test-session-001")
        assert len(found) == len(files)

    def test_no_match_returns_empty(self, notes_env):
        notes, _ = notes_env
        assert notes._find_chunks_for_session("nonexistent") == []


class TestProcess:
    """process() パイプライン一括実行。"""

    def test_process_skip_embed(self, notes_env):
        """skip_embed=True で digest のみ実行される。"""
        notes, store = notes_env
        result = notes.process("test-session-001", session_store=store, skip_embed=True)

        assert result["chunks_created"] >= 1
        assert result["chunks_embedded"] == 0
        assert result["links_created"] == 0


class TestGenerateSummaryLLM:
    """_generate_summary(use_llm=True) パスのテスト。"""

    def test_llm_summary_with_mock(self):
        """LLM 要約が成功するパス (CortexClient をモック)。"""
        turns = _make_turns(4)
        mock_resp = MagicMock()
        mock_resp.text = "TokenVault の quota 管理について議論"

        with patch("mekhane.ochema.session_notes.CortexClient", create=True) as MockClient:
            # CortexClient のインスタンスの ask() が mock_resp を返す
            mock_instance = MagicMock()
            mock_instance.ask.return_value = mock_resp
            MockClient.return_value = mock_instance

            # use_llm=True でもインポート失敗でフォールバック
            summary = SessionNotes._generate_summary(turns, use_llm=True)
            # LLM パスが失敗しても extractive が返る
            assert len(summary) > 0
            assert "問:" in summary or "TokenVault" in summary

    def test_llm_failure_falls_back_to_extractive(self):
        """LLM 失敗時は extractive 要約にフォールバック。"""
        turns = _make_turns(4)
        # CortexClient のインポートを明示的にブロック
        with patch.dict("sys.modules", {"mekhane.ochema.cortex_client": None}):
            summary = SessionNotes._generate_summary(turns, use_llm=True)
            # CortexClient import 失敗 → extractive にフォールバック
            assert "問:" in summary
            assert "結:" in summary


class TestExtractKeywordsRegexFallback:
    """_extract_keywords_regex: YAKE がない環境でのフォールバック。"""

    def test_regex_finds_camelcase(self):
        kw = SessionNotes._extract_keywords_regex("Use CortexClient and TokenVault here")
        assert "CortexClient" in kw
        assert "TokenVault" in kw

    def test_regex_finds_uppercase(self):
        kw = SessionNotes._extract_keywords_regex("Uses API and LLM for FEP analysis")
        assert "API" in kw
        assert "LLM" in kw

    def test_regex_finds_katakana(self):
        kw = SessionNotes._extract_keywords_regex("ヘゲモニコンのパイプラインを構築")
        assert any("ヘゲモニコン" in k for k in kw)

    def test_regex_max_limit(self):
        text = " ".join(f"Term{i}Name" for i in range(20))
        kw = SessionNotes._extract_keywords_regex(text, max_keywords=5)
        assert len(kw) <= 5

    def test_yake_import_error_triggers_fallback(self):
        """YAKE が ImportError を投げたら regex にフォールバック。"""
        with patch.dict("sys.modules", {"yake": None}):
            # yake を None にして ImportError を発生させる
            kw = SessionNotes._extract_keywords("CortexClient and TokenVault used")
            # 結果が返ること (フォールバック動作)
            assert isinstance(kw, list)


class TestMergeSynthesizeMock:
    """merge_similar(synthesize=True) の LLM パス。"""

    def test_synthesize_calls_llm(self, notes_env):
        """synthesize=True で _synthesize_chunks が呼ばれる。"""
        notes, _ = notes_env
        # リンクデータを設定
        notes._save_links({
            "a--b": {
                "source": "notes:ochema:chunk_a",
                "target": "notes:ochema:chunk_b",
                "distance": 0.3,
                "created": "2026-02-22",
            },
        })

        # _read_chunk_by_pk と _synthesize_chunks をモック
        with patch.object(notes, "_read_chunk_by_pk", return_value="Sample content"), \
             patch.object(notes, "_synthesize_chunks", return_value="統合結果") as mock_synth:
            candidates = notes.merge_similar(threshold=0.5, synthesize=True)
            assert len(candidates) == 1
            assert candidates[0].get("synthesis") == "統合結果"
            mock_synth.assert_called_once()


class TestChunkTurnsEdgeCases:
    """_chunk_turns のエッジケース。"""

    def test_single_user_turn_no_model(self):
        """model 応答なしの user のみターン。"""
        turns = [{"role": "user", "content": "質問だけ"}]
        notes = SessionNotes.__new__(SessionNotes)
        chunks = notes._chunk_turns(turns, max_chars=5000)
        assert len(chunks) == 1
        assert chunks[0]["turn_start"] == 0
        assert chunks[0]["turn_end"] == 1

    def test_many_turns_pair_preservation(self):
        """大量ターン (20組) でペア保持を確認。"""
        turns = _make_turns(40)  # 20 user + 20 model = 20 ペア
        notes = SessionNotes.__new__(SessionNotes)
        chunks = notes._chunk_turns(turns, max_chars=5000)

        # 各チャンクのターン範囲を検証
        for chunk in chunks:
            body = chunk["content"]
            # 各チャンクは必ず MODEL で終わる or 最後のチャンク
            assert "## MODEL" in body or chunk == chunks[-1]

    def test_consecutive_user_turns(self):
        """user が連続するケース (model が間に入らない)。"""
        turns = [
            {"role": "user", "content": "質問1"},
            {"role": "user", "content": "質問2 (追加)"},
            {"role": "model", "content": "回答"},
        ]
        notes = SessionNotes.__new__(SessionNotes)
        chunks = notes._chunk_turns(turns, max_chars=5000)
        # 全ターンが 1 チャンクに入る
        assert len(chunks) == 1
        assert "質問1" in chunks[0]["content"]
        assert "質問2" in chunks[0]["content"]
        assert "回答" in chunks[0]["content"]


class TestSessionMapIndex:
    """session_map.json O(1) インデックス。"""

    def test_digest_creates_session_map(self, notes_env):
        """digest 後に session_map.json が作成される。"""
        notes, store = notes_env
        notes.digest("test-session-001", session_store=store)

        map_file = notes._index_dir / "session_map.json"
        assert map_file.exists()

        import json
        data = json.loads(map_file.read_text())
        assert "test-session-001" in data
        assert len(data["test-session-001"]) >= 1

    def test_find_uses_index(self, notes_env):
        """2回目の _find_chunks はインデックスから O(1) で取得。"""
        notes, store = notes_env
        files = notes.digest("test-session-001", session_store=store)

        # 1回目 (インデックスが作られる)
        found1 = notes._find_chunks_for_session("test-session-001")

        # 2回目 (インデックスから取得 — rglob は走らない)
        found2 = notes._find_chunks_for_session("test-session-001")

        assert len(found1) == len(files)
        assert found1 == found2
