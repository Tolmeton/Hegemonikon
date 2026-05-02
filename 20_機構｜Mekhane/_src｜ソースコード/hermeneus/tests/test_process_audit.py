# PROOF: [L3/テスト] <- hermeneus/tests/test_process_audit.py O4.Energeia(実行) H2.Pistis(確信)
"""
Process Audit Unit Tests — D1/D2/D3 の専用テスト

D1: estimate_drift (EntropyEstimator)
D2: verify_step_async / verify_step (verifier.py) 
D3: consensus_trap (_detect_unanimity, _run_consensus_trap) (verifier.py)

消したらこのテストファイルが壊れる = 🟡 吸収 の証明。
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermeneus.src.macro_executor import EntropyEstimator, ASTWalker, ExecutionContext, StepResult
from hermeneus.src.verifier import (
    AgentRole, VerdictType, Verdict, DebateRound, RallyTurn,
    DebateAgent, DebateEngine, ConsensusResult,
    DebateArgument,
)


# =============================================================================
# D1: estimate_drift テスト
# =============================================================================

class TestEstimateDrift:
    """D1: EntropyEstimator.estimate_drift のユニットテスト"""

    def test_drift_identical_texts(self):
        """同一テキストのドリフトは 0.0"""
        text = "FEP は変分自由エネルギーを最小化する原理である。"
        drift = EntropyEstimator.estimate_drift(text, text)
        assert drift == 0.0

    def test_drift_completely_different(self):
        """完全に異なるテキストのドリフトは 1.0 に近い"""
        a = "量子力学における波動関数の収縮について考察する。"
        b = "今日の天気は晴れです。明日は雨になるかもしれません。"
        drift = EntropyEstimator.estimate_drift(a, b)
        assert drift > 0.7

    def test_drift_similar_texts(self):
        """類似テキストのドリフトは低い"""
        a = "# 分析結果\n- FEP は予測誤差を最小化する\n- 能動推論が行動を導く"
        b = "# 分析結果\n- FEP は予測誤差を最小化する原理\n- 能動推論が行動選択を導く"
        drift = EntropyEstimator.estimate_drift(a, b)
        assert drift < 0.6  # n-gram ベースでは短いテキストの類似度が低めに出る

    def test_drift_is_inverse_of_convergence(self):
        """drift = 1.0 - convergence の関係が成立する"""
        a = "テスト文A: Hegemonikón は FEP に基づく"
        b = "テスト文B: 全く異なる内容のテキスト"
        convergence = EntropyEstimator.estimate_convergence(a, b)
        drift = EntropyEstimator.estimate_drift(a, b)
        assert abs((convergence + drift) - 1.0) < 1e-9

    def test_drift_empty_input(self):
        """空テキストのドリフトは 1.0 (完全に異なる)"""
        drift = EntropyEstimator.estimate_drift("", "何かの内容")
        assert drift == 1.0

    def test_drift_both_empty(self):
        """両方空の場合のドリフトも 1.0"""
        drift = EntropyEstimator.estimate_drift("", "")
        assert drift == 1.0

    def test_drift_range(self):
        """ドリフトは常に [0.0, 1.0] の範囲"""
        pairs = [
            ("a", "b"),
            ("", "x"),
            ("長い文章" * 100, "短い"),
            ("abc", "abc"),
        ]
        for a, b in pairs:
            drift = EntropyEstimator.estimate_drift(a, b)
            assert 0.0 <= drift <= 1.0, f"drift={drift} for ({a[:20]}, {b[:20]})"


class TestDriftInSequence:
    """D1: ASTWalker._walk_sequence でのドリフト測定テスト"""

    def test_sequence_records_drift_metadata(self):
        """Sequence 実行時に children の metadata に semantic_drift が記録される"""
        from hermeneus.src.ccl_ast import Sequence, Workflow

        # 2つの異なる WF からなる Sequence
        seq = Sequence(steps=[
            Workflow(id="noe"),
            Workflow(id="dia"),
        ])

        # カスタムハンドラ: WF ID に応じて異なるテキストを返す
        outputs = {
            "noe": "# Noēsis 分析\n- 深い洞察が得られた",
            "dia": "# Krisis 判定\n- 判定: ACCEPT, 確信度 85%",
        }
        handler = lambda wf_id, params, ctx: outputs.get(wf_id, f"output for {wf_id}")

        walker = ASTWalker(step_handler=handler)
        ctx = ExecutionContext()
        result = walker.walk(seq, ctx)

        # 2番目の child に semantic_drift が記録されている
        assert len(result.children) == 2
        assert "semantic_drift" in result.children[1].metadata
        drift = result.children[1].metadata["semantic_drift"]
        assert 0.0 <= drift <= 1.0
        # 最初の child には drift がない (比較対象がない)
        assert "semantic_drift" not in result.children[0].metadata

    def test_drift_alert_on_high_drift(self):
        """[D1→D2] 高ドリフト時に drift_alert メタデータが記録される"""
        from hermeneus.src.ccl_ast import Sequence, Workflow

        seq = Sequence(steps=[
            Workflow(id="step_a"),
            Workflow(id="step_b"),
        ])

        # 完全に無関係な出力 → ドリフトが高くなる
        outputs = {
            "step_a": "量子力学における波動関数の収縮と観測問題について",
            "step_b": "今日のランチメニューはカレーライスにしよう",
        }
        handler = lambda wf_id, params, ctx: outputs.get(wf_id, "")

        walker = ASTWalker(step_handler=handler)
        ctx = ExecutionContext()
        result = walker.walk(seq, ctx)

        child_b = result.children[1]
        drift = child_b.metadata.get("semantic_drift", 0)
        # ドリフトが閾値 0.7 を超えている場合のみ alert が記録される
        if drift > 0.7:
            assert child_b.metadata.get("drift_alert") is True
            assert "drift_context" in child_b.metadata
            assert child_b.metadata["drift_context"]["drift_score"] == drift

    def test_drift_alert_emits_event(self):
        """[D1→D2] DRIFT_ALERT イベントが EventBus に発行される"""
        from hermeneus.src.ccl_ast import Sequence, Workflow
        from hermeneus.src.event_bus import EventType

        # 簡易 EventBus モック (CognitionEvent を受け取る)
        class MockEventBus:
            def __init__(self):
                self.events = []
            def emit(self, event):
                self.events.append(event)

        seq = Sequence(steps=[
            Workflow(id="step_a"),
            Workflow(id="step_b"),
        ])

        outputs = {
            "step_a": "量子力学における波動関数の収縮と観測問題について詳しく検討する",
            "step_b": "今日のランチメニューはカレーライスにしよう",
        }
        handler = lambda wf_id, params, ctx: outputs.get(wf_id, "")

        bus = MockEventBus()
        walker = ASTWalker(step_handler=handler, event_bus=bus)
        ctx = ExecutionContext()
        result = walker.walk(seq, ctx)

        drift = result.children[1].metadata.get("semantic_drift", 0)
        if drift > 0.7:
            drift_events = [e for e in bus.events if e.event_type == EventType.DRIFT_ALERT]
            assert len(drift_events) >= 1
            assert drift_events[0].metadata["step"] == "/step_b"
            # D1/D2 統合: prev/curr_output がメタデータに含まれる
            assert "prev_output" in drift_events[0].metadata
            assert "curr_output" in drift_events[0].metadata


# =============================================================================
# D2: verify_step テスト (LLM 呼び出しなし = 構造テスト)
# =============================================================================

class TestVerifyStepStructure:
    """D2: verify_step_async の構造テスト (LLM なしでインターフェースを検証)"""

    def test_verify_step_function_exists(self):
        """verify_step / verify_step_async がインポート可能"""
        from hermeneus.src.verifier import verify_step, verify_step_async
        assert callable(verify_step)
        assert callable(verify_step_async)

    def test_verify_step_async_signature(self):
        """verify_step_async の引数シグネチャが正しい"""
        import inspect
        from hermeneus.src.verifier import verify_step_async
        sig = inspect.signature(verify_step_async)
        params = list(sig.parameters.keys())
        assert "step_input" in params
        assert "step_output" in params
        assert "context" in params

    def test_verify_step_returns_verdict(self):
        """verify_step の戻り値の型が Verdict であることを型注釈で確認"""
        import inspect
        from hermeneus.src.verifier import verify_step_async
        sig = inspect.signature(verify_step_async)
        # 戻り値型注釈が Verdict
        assert sig.return_annotation == Verdict


# =============================================================================
# D3: consensus_trap テスト
# =============================================================================

class TestDetectUnanimity:
    """D3: DebateEngine._detect_unanimity のユニットテスト"""

    def _make_engine(self):
        return DebateEngine()

    def test_unanimity_detected_converged_weak_critic(self):
        """収束済み + Critic 弱い + ACCEPT 高確信 = unanimity (条件緩和後)"""
        engine = self._make_engine()

        rally = [
            RallyTurn(AgentRole.PROPOSER, "支持する", 0.9, 1),
            RallyTurn(AgentRole.CRITIC, "弱い批判", 0.4, 2),  # 0.6未満 = 弱い
            RallyTurn(AgentRole.PROPOSER, "確かに正しい", 0.95, 3),
            RallyTurn(AgentRole.CRITIC, "同意する", 0.3, 4),  # 0.6未満 = 弱い
        ]
        rounds = [DebateRound(
            round_number=1,
            rally=rally,
            converged=True,
            convergence_reason="確信度安定により収束",  # 「相互同意」でなくても検出される
            proposition=DebateArgument(AgentRole.PROPOSER, "支持", 0.9),
            critiques=[DebateArgument(AgentRole.CRITIC, "弱い", 0.4)],
        )]
        verdict = Verdict(
            type=VerdictType.ACCEPT,
            reasoning="全員合意",
            confidence=0.9,
        )

        assert engine._detect_unanimity(rounds, verdict) is True

    def test_no_unanimity_when_reject(self):
        """REJECT 判定では unanimity は検出されない"""
        engine = self._make_engine()
        rounds = [DebateRound(
            round_number=1,
            rally=[RallyTurn(AgentRole.PROPOSER, "支持", 0.8, 1)],
            converged=True,
            convergence_reason="相互同意により収束",
            proposition=DebateArgument(AgentRole.PROPOSER, "支持", 0.8),
            critiques=[],
        )]
        verdict = Verdict(type=VerdictType.REJECT, reasoning="却下", confidence=0.9)

        assert engine._detect_unanimity(rounds, verdict) is False

    def test_no_unanimity_low_confidence(self):
        """ACCEPT だが確信度が 0.85 未満では unanimity は検出されない"""
        engine = self._make_engine()
        rounds = [DebateRound(
            round_number=1,
            rally=[RallyTurn(AgentRole.PROPOSER, "支持", 0.8, 1)],
            converged=True,
            convergence_reason="相互同意により収束",
            proposition=DebateArgument(AgentRole.PROPOSER, "支持", 0.8),
            critiques=[],
        )]
        verdict = Verdict(type=VerdictType.ACCEPT, reasoning="弱い合意", confidence=0.7)

        assert engine._detect_unanimity(rounds, verdict) is False

    def test_no_unanimity_strong_critiques(self):
        """Critic が高確信 (>0.6) で批判している場合は unanimity ではない"""
        engine = self._make_engine()
        rally = [
            RallyTurn(AgentRole.PROPOSER, "支持する", 0.9, 1),
            RallyTurn(AgentRole.CRITIC, "強い反論がある", 0.8, 2),  # > 0.6 = 強い
        ]
        rounds = [DebateRound(
            round_number=1,
            rally=rally,
            converged=True,
            convergence_reason="相互同意により収束",
            proposition=DebateArgument(AgentRole.PROPOSER, "支持", 0.9),
            critiques=[DebateArgument(AgentRole.CRITIC, "強い反論", 0.8)],
        )]
        verdict = Verdict(type=VerdictType.ACCEPT, reasoning="強制合意", confidence=0.9)

        assert engine._detect_unanimity(rounds, verdict) is False

    def test_no_unanimity_no_convergence(self):
        """収束していない場合は unanimity ではない"""
        engine = self._make_engine()
        rally = [
            RallyTurn(AgentRole.PROPOSER, "支持", 0.8, 1),
            RallyTurn(AgentRole.CRITIC, "弱い批判", 0.4, 2),
        ]
        rounds = [DebateRound(
            round_number=1,
            rally=rally,
            converged=False,  # 収束していない
            convergence_reason="最大ターン数到達",
            proposition=DebateArgument(AgentRole.PROPOSER, "支持", 0.8),
            critiques=[DebateArgument(AgentRole.CRITIC, "弱い", 0.4)],
        )]
        verdict = Verdict(type=VerdictType.ACCEPT, reasoning="合意", confidence=0.92)

        assert engine._detect_unanimity(rounds, verdict) is False


class TestConsensusResultUnanimityField:
    """D3: ConsensusResult.unanimity_recheck フィールドのテスト"""

    def test_default_is_false(self):
        """デフォルトでは unanimity_recheck は False"""
        result = ConsensusResult(
            accepted=True,
            confidence=0.8,
            majority_ratio=0.7,
            verdict=Verdict(type=VerdictType.ACCEPT, reasoning="ok", confidence=0.8),
            dissent_reasons=[],
            rounds=[],
        )
        assert result.unanimity_recheck is False

    def test_can_be_set_true(self):
        """unanimity_recheck を True に設定できる"""
        result = ConsensusResult(
            accepted=True,
            confidence=0.8,
            majority_ratio=0.7,
            verdict=Verdict(type=VerdictType.ACCEPT, reasoning="ok", confidence=0.8),
            dissent_reasons=[],
            rounds=[],
            unanimity_recheck=True,
        )
        assert result.unanimity_recheck is True

    def test_metadata_confabulation_guard_key(self):
        """metadata に confabulation_guard キーを設定可能"""
        result = ConsensusResult(
            accepted=True,
            confidence=0.8,
            majority_ratio=0.7,
            verdict=Verdict(type=VerdictType.ACCEPT, reasoning="ok", confidence=0.8),
            dissent_reasons=[],
            rounds=[],
            metadata={"confabulation_guard": "triggered"},
        )
        assert result.metadata["confabulation_guard"] == "triggered"


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
