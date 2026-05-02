# PROOF: mekhane/anamnesis/tests/test_hyphe_pipeline.py
# PURPOSE: anamnesis モジュールの hyphe_pipeline に対するテスト
"""hyphe_pipeline.py のユニットテスト。

Mock を使って HypheField への依存を差し替え、
HyphePipeline のオーケストレーションロジックを検証する:
- DissolveResult / Crystal / RecrystallizeResult / DistillResult データクラス
- dissolve (溶解)
- recrystallize (結晶化)
- auto_dissolve (自動溶解)
- distill_with_fallback (3段フォールバック蒸留)
- status (状態取得)
"""

import pytest
from unittest.mock import MagicMock, patch

from mekhane.anamnesis.hyphe_pipeline import (
    HyphePipeline,
    DissolveResult,
    Crystal,
    RecrystallizeResult,
    DistillResult,
)


# ── フィクスチャ ──────────────────────────────────────────

@pytest.fixture
def mock_field():
    """HypheField のモック。"""
    field = MagicMock()
    field.dissolve.return_value = 5
    field.recall.return_value = [
        {
            "id": "chunk_1",
            "content": "FEP は自由エネルギー原理です",
            "title": "FEP 概要",
            "source": "session",
            "session_id": "sess_abc",
            "_field_score": 0.85,
            "_distance": 0.15,
            "precision": 0.8,
            "density": 0.3,
        },
        {
            "id": "chunk_2",
            "content": "能動推論は行動で環境を変える",
            "title": "能動推論",
            "source": "session",
            "session_id": "sess_abc",
            "_field_score": 0.72,
            "_distance": 0.28,
            "precision": 0.6,
            "density": 0.5,
        },
    ]
    field.update_density.return_value = 50
    field.health.return_value = {
        "status": "growing",
        "total_chunks": 50,
        "sources": {"session": 30, "handoff": 20},
        "chunker_mode": "nucleator",
    }
    return field


@pytest.fixture
def pipeline(mock_field):
    """テスト用 HyphePipeline。"""
    return HyphePipeline(field=mock_field, auto_dissolve_interval=5)


# ── データクラス ──────────────────────────────────────────

class TestDataClasses:

    def test_dissolve_result_success(self):
        r = DissolveResult(chunks_count=5, session_id="abc")
        assert r.success is True

    def test_dissolve_result_failure(self):
        r = DissolveResult(chunks_count=0, session_id="abc", error="fail")
        assert r.success is False

    def test_crystal_from_recall(self):
        result = {
            "id": "c1",
            "content": "テスト内容",
            "title": "タイトル",
            "source": "session",
            "session_id": "s1",
            "_field_score": 0.9,
            "_epistemic_value": 0.7,
            "_pragmatic_value": 0.3,
            "precision": 0.8,
        }
        crystal = Crystal.from_recall_result(result)
        assert crystal.chunk_id == "c1"
        assert crystal.content == "テスト内容"
        assert crystal.score == 0.9
        assert crystal.epistemic_value == 0.7
        assert crystal.metadata.get("precision") == 0.8

    def test_recrystallize_result_tokens(self):
        crystals = [
            Crystal(chunk_id="c1", content="a" * 400),
            Crystal(chunk_id="c2", content="b" * 200),
        ]
        r = RecrystallizeResult(crystals=crystals, intent="test")
        assert r.total_tokens_estimate == 150  # (400+200) / 4

    def test_distill_result(self):
        r = DistillResult(
            level="L1", success=True,
            rom_path="/tmp/rom.md",
            chunks_dissolved=5,
            fallback_chain=["L1:attempt", "L1:success"],
        )
        assert r.level == "L1"
        assert r.success is True


# ── dissolve ──────────────────────────────────────────────

class TestDissolve:

    def test_basic_dissolve(self, pipeline, mock_field):
        result = pipeline.dissolve("テストテキスト", session_id="sess_1")
        assert result.success is True
        assert result.chunks_count == 5
        assert result.session_id == "sess_1"
        mock_field.dissolve.assert_called_once()

    def test_dissolve_records_session(self, pipeline):
        pipeline.dissolve("テキスト", session_id="sess_x")
        assert "sess_x" in pipeline._dissolved_sessions

    def test_dissolve_with_trigger(self, pipeline):
        result = pipeline.dissolve("テキスト", session_id="s1", trigger="health")
        assert result.trigger == "health"

    def test_dissolve_error_handling(self, pipeline, mock_field):
        mock_field.dissolve.side_effect = RuntimeError("DB エラー")
        result = pipeline.dissolve("テキスト", session_id="s1")
        assert result.success is False
        assert "DB エラー" in result.error

    def test_dissolve_elapsed_ms(self, pipeline):
        result = pipeline.dissolve("テキスト", session_id="s1")
        assert result.elapsed_ms >= 0


# ── recrystallize ────────────────────────────────────────

class TestRecrystallize:

    def test_basic_recrystallize(self, pipeline, mock_field):
        result = pipeline.recrystallize("FEP について")
        assert len(result.crystals) == 2
        assert result.intent == "FEP について"
        assert result.mode == "exploit"
        mock_field.recall.assert_called_once()

    def test_recrystallize_explore(self, pipeline, mock_field):
        # explore モードの recall 結果を設定
        mock_field.recall.return_value = [
            {
                "id": "c1",
                "content": "新奇な発見",
                "title": "Discovery",
                "source": "session",
                "session_id": "s1",
                "_field_score": 0.65,
                "_epistemic_value": 0.8,
                "_pragmatic_value": 0.2,
            },
        ]
        result = pipeline.recrystallize("未知の概念", mode="explore")
        assert len(result.crystals) == 1
        assert result.crystals[0].epistemic_value == 0.8

    def test_recrystallize_with_session_filter(self, pipeline, mock_field):
        pipeline.recrystallize("テスト", session_id="sess_abc")
        mock_field.recall.assert_called_once_with(
            query="テスト",
            mode="exploit",
            limit=10,
            session_filter="sess_abc",
        )

    def test_recrystallize_empty(self, pipeline, mock_field):
        mock_field.recall.return_value = []
        result = pipeline.recrystallize("存在しない")
        assert len(result.crystals) == 0
        assert result.total_tokens_estimate == 0


# ── auto_dissolve ────────────────────────────────────────

class TestAutoDissolve:

    def test_auto_dissolve_below_interval(self, pipeline):
        """インターバル未満ではスキップ。"""
        steps = [{"text": f"Step {i}"} for i in range(3)]
        result = pipeline.auto_dissolve(steps, session_id="s1")
        assert result is None  # 3 < 5 (interval)

    def test_auto_dissolve_at_interval(self, pipeline, mock_field):
        """インターバル以上で実行。"""
        steps = [{"text": f"Step {i}"} for i in range(5)]
        result = pipeline.auto_dissolve(steps, session_id="s1")
        assert result is not None
        assert result.success is True

    def test_auto_dissolve_health_trigger(self, pipeline, mock_field):
        """health トリガーはインターバルに関係なく即時実行。"""
        steps = [{"text": "緊急"}]
        result = pipeline.auto_dissolve(steps, session_id="s1", trigger="health")
        assert result is not None
        assert result.trigger == "health"

    def test_auto_dissolve_disabled(self, pipeline):
        """自動溶解無効時はスキップ。"""
        pipeline.auto_dissolve_enabled = False
        steps = [{"text": f"Step {i}"} for i in range(10)]
        result = pipeline.auto_dissolve(steps, session_id="s1")
        assert result is None

    def test_auto_dissolve_disabled_health_override(self, pipeline, mock_field):
        """自動溶解無効でも health トリガーは実行。"""
        pipeline.auto_dissolve_enabled = False
        steps = [{"text": "緊急健全性"}]
        result = pipeline.auto_dissolve(steps, session_id="s1", trigger="health")
        assert result is not None

    def test_auto_dissolve_empty_steps(self, pipeline):
        """空ステップは溶解しない。"""
        steps = [{"text": ""}]
        # インターバルに達するようにカウンターを設定
        pipeline._step_counter = 4
        result = pipeline.auto_dissolve(steps, session_id="s1")
        assert result is None

    def test_auto_dissolve_counter_reset(self, pipeline, mock_field):
        """溶解実行後にカウンターがリセットされる。"""
        steps = [{"text": f"Step {i}"} for i in range(5)]
        pipeline.auto_dissolve(steps, session_id="s1")
        assert pipeline._step_counter == 0


# ── distill_with_fallback ────────────────────────────────

class TestDistillWithFallback:

    def test_l1_success(self, pipeline, mock_field):
        """L1 成功: rom_save_fn あり + 正常動作。"""
        save_fn = MagicMock(return_value="/tmp/rom.md")
        result = pipeline.distill_with_fallback(
            "テスト全文", "sess_1", rom_save_fn=save_fn,
        )
        assert result.level == "L1"
        assert result.success is True
        assert result.rom_path == "/tmp/rom.md"
        assert "L1:success" in result.fallback_chain
        save_fn.assert_called_once()

    def test_l1_failure_l2_success(self, pipeline, mock_field):
        """L1 失敗 → L2 成功。"""
        save_fn = MagicMock(side_effect=RuntimeError("IO Error"))
        result = pipeline.distill_with_fallback(
            "テスト全文", "sess_1", rom_save_fn=save_fn,
        )
        assert result.level == "L2"
        assert result.success is True
        # チェーン: ["L1:attempt", "L1:failed(...)", "L2:attempt", "L2:success"]
        assert any("L1:failed" in s for s in result.fallback_chain)
        assert "L2:success" in result.fallback_chain

    def test_l2_no_rom_fn(self, pipeline, mock_field):
        """rom_save_fn=None → L1 スキップ → L2 成功。"""
        result = pipeline.distill_with_fallback("テスト全文", "sess_1")
        assert result.level == "L2"
        assert result.success is True

    def test_l2_failure_l3_success(self, pipeline, mock_field):
        """L2 失敗 → L3 成功。"""
        # dissolve が失敗するように設定
        mock_field.dissolve.side_effect = [
            RuntimeError("L2 fail"),  # L2 の dissolve
            3,  # L3 の dissolve
        ]
        result = pipeline.distill_with_fallback("テスト全文", "sess_1")
        assert result.level == "L3"
        assert result.success is True

    def test_l3_with_rom_fn(self, pipeline, mock_field):
        """L3 で rom_save_fn がある場合。"""
        call_count = [0]

        def save_fn(text, sid):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("L1 fail")
            return "/tmp/meta.md"

        mock_field.dissolve.side_effect = RuntimeError("L2 fail")
        result = pipeline.distill_with_fallback(
            "テスト uuid-1234-abcd-5678-ef90 /home/test/file.py",
            "sess_1",
            rom_save_fn=save_fn,
        )
        assert result.level == "L3"
        assert result.success is True
        assert result.rom_path == "/tmp/meta.md"

    def test_all_levels_fail(self, pipeline, mock_field):
        """全段階失敗。"""
        save_fn = MagicMock(side_effect=RuntimeError("save fail"))
        mock_field.dissolve.side_effect = RuntimeError("dissolve fail")
        result = pipeline.distill_with_fallback(
            "テスト", "sess_1", rom_save_fn=save_fn,
        )
        assert result.level == "NONE"
        assert result.success is False
        assert len(result.fallback_chain) >= 3

    def test_fallback_chain_logged(self, pipeline, mock_field):
        """フォールバックチェーンが記録される。"""
        result = pipeline.distill_with_fallback("テスト", "sess_1")
        assert isinstance(result.fallback_chain, list)
        assert len(result.fallback_chain) >= 1


# ── status ───────────────────────────────────────────────

class TestStatus:

    def test_status_returns_dict(self, pipeline):
        status = pipeline.status()
        assert "step_counter" in status
        assert "field" in status

    def test_status_after_dissolve(self, pipeline):
        pipeline.dissolve("テスト", session_id="s1")
        status = pipeline.status()
        assert status["dissolved_sessions"] == 1


# ── _extract_identifiers ─────────────────────────────────

class TestExtractIdentifiers:

    def test_uuid_extraction(self):
        text = "ID は 12345678-abcd-1234-efab-123456789012 です"
        result = HyphePipeline._extract_identifiers(text)
        assert "UUID:" in result

    def test_path_extraction(self):
        text = "ファイルは /home/user/test.py にあります"
        result = HyphePipeline._extract_identifiers(text)
        assert "PATH:" in result

    def test_url_extraction(self):
        text = "参照: https://example.com/api/v1/endpoint"
        result = HyphePipeline._extract_identifiers(text)
        assert "URL:" in result

    def test_no_identifiers_fallback(self):
        text = "識別子のない普通のテキストです" * 10
        result = HyphePipeline._extract_identifiers(text)
        # 冒頭 500 文字がフォールバック
        assert len(result) <= 500

    def test_session_id_extraction(self):
        text = "session_id: abc123_def456 を使用"
        result = HyphePipeline._extract_identifiers(text)
        assert "SESSION:" in result
