# PROOF: [L3/テスト] <- hermeneus/tests/test_verifier.py O4.Energeia(実行) H2.Pistis(確信)
"""
Hermēneus Verifier Unit Tests

Multi-Agent Debate (MAD) によるフォーマル検証のユニットテスト。
AgentRole, VerdictType, DebateArgument, DebateAgent, DebateEngine,
ConvergenceDetector, AuditRecord/Store/Reporter を網羅。
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermeneus.src.audit import AuditRecord, AuditStore, AuditReporter
from hermeneus.src.verifier import (
    AgentRole, VerdictType, DebateArgument, Verdict, DebateRound,
    DebateAgent, DebateEngine,
    RallyTurn, ConvergenceDetector,
)


class TestAgentRole:
    """AgentRole enum が MAD の 3 役割を正しく定義しているか検証"""

    def test_roles(self):
        """PROPOSER/CRITIC/ARBITER の 3 値が定義されていること"""
        assert AgentRole.PROPOSER.value == "proposer"
        assert AgentRole.CRITIC.value == "critic"
        assert AgentRole.ARBITER.value == "arbiter"

    def test_roles_are_exhaustive(self):
        """AgentRole のメンバ数が正確に 3 であること（予期しない追加を検出）"""
        assert len(AgentRole) == 3


class TestVerdictType:
    """VerdictType enum が MAD の判定結果を正しく定義しているか検証"""

    def test_verdict_types(self):
        """ACCEPT/REJECT/UNCERTAIN の 3 値が定義されていること"""
        assert VerdictType.ACCEPT.value == "accept"
        assert VerdictType.REJECT.value == "reject"
        assert VerdictType.UNCERTAIN.value == "uncertain"

    def test_verdict_types_are_exhaustive(self):
        """VerdictType のメンバ数が正確に 3 であること"""
        assert len(VerdictType) == 3


class TestDebateArgument:
    """DebateArgument データクラスの生成と属性保持を検証"""

    def test_create_argument(self):
        """必須フィールド (role, content, confidence) が保持されること"""
        arg = DebateArgument(
            agent_role=AgentRole.PROPOSER,
            content="この主張は妥当です。",
            confidence=0.8
        )
        assert arg.agent_role == AgentRole.PROPOSER
        assert arg.content == "この主張は妥当です。"
        assert arg.confidence == 0.8

    def test_create_argument_zero_confidence(self):
        """確信度 0.0 でも生成できること (エッジケース)"""
        arg = DebateArgument(
            agent_role=AgentRole.CRITIC,
            content="完全に不確実",
            confidence=0.0
        )
        assert arg.confidence == 0.0


class TestDebateAgent:
    """DebateAgent の生成、確信度推定、判定パースを検証"""

    @pytest.mark.parametrize("role", [AgentRole.PROPOSER, AgentRole.CRITIC, AgentRole.ARBITER])
    def test_create_agent_with_role(self, role):
        """全 AgentRole で DebateAgent を生成できること"""
        agent = DebateAgent(role)
        assert agent.role == role
    
    def test_estimate_confidence_high(self):
        """高確信キーワード ('確実', 'definitely') で 0.7 超を返すこと"""
        agent = DebateAgent(AgentRole.PROPOSER)
        text = "これは確実に正しい。明確にそうだ。definitely correct。"
        confidence = agent._estimate_confidence(text)
        assert confidence > 0.7

    def test_estimate_confidence_low(self):
        """低確信キーワード ('おそらく', 'maybe') で 0.6 未満を返すこと"""
        agent = DebateAgent(AgentRole.PROPOSER)
        text = "おそらくそうかもしれない。maybe, perhaps。"
        confidence = agent._estimate_confidence(text)
        assert confidence < 0.6

    def test_estimate_confidence_empty(self):
        """空文字列でもクラッシュせずデフォルト値を返すこと"""
        agent = DebateAgent(AgentRole.PROPOSER)
        confidence = agent._estimate_confidence("")
        assert 0.0 <= confidence <= 1.0
    
    def test_parse_verdict_accept(self):
        """'判定: ACCEPT\n確信度: 85%' → (ACCEPT, 0.85, reasoning)"""
        agent = DebateAgent(AgentRole.ARBITER)
        text = "判定: ACCEPT\n確信度: 85%\n理由: 論拠が十分。"
        verdict_type, confidence, reasoning = agent._parse_verdict(text)

        assert verdict_type == VerdictType.ACCEPT
        assert confidence == 0.85
        assert "論拠" in reasoning
    
    def test_parse_verdict_reject(self):
        """'判定: REJECT\n確信度: 70%' → (REJECT, 0.7, reasoning)"""
        agent = DebateAgent(AgentRole.ARBITER)
        text = "判定: REJECT\n確信度: 70%\n理由: 証拠不足。"
        verdict_type, confidence, reasoning = agent._parse_verdict(text)

        assert verdict_type == VerdictType.REJECT
        assert confidence == 0.7

    def test_parse_verdict_decimal_confidence(self):
        """確信度の小数表記 '0.85' を正しくパースすること"""
        agent = DebateAgent(AgentRole.ARBITER)
        text = "判定: ACCEPT\n確信度: 0.85\n理由: 論拠が十分。"
        verdict_type, confidence, reasoning = agent._parse_verdict(text)

        assert verdict_type == VerdictType.ACCEPT
        assert confidence == 0.85
        assert "論拠" in reasoning

    def test_parse_verdict_fraction_confidence(self):
        """確信度の分数表記 '75/100' を 0.75 にパースすること"""
        agent = DebateAgent(AgentRole.ARBITER)
        text = "判定: REJECT\n確信度: 75/100\n理由: 証拠が不十分。"
        verdict_type, confidence, reasoning = agent._parse_verdict(text)

        assert verdict_type == VerdictType.REJECT
        assert confidence == 0.75

    def test_parse_verdict_no_confidence_uses_estimate(self):
        """確信度行が省略された場合、_estimate_confidence にフォールバックすること"""
        agent = DebateAgent(AgentRole.ARBITER)
        text = "判定: ACCEPT\n理由: 確実に正しい。明確な根拠がある。"
        verdict_type, confidence, reasoning = agent._parse_verdict(text)

        assert verdict_type == VerdictType.ACCEPT
        assert confidence >= 0.7  # 高確信キーワードで推定
        assert confidence != 0.5  # デフォルト 0.5 ではないこと

    def test_parse_verdict_confidence_clamp(self):
        """範囲外の確信度 (150%, 0%) が [0.0, 1.0] にクランプされること"""
        agent = DebateAgent(AgentRole.ARBITER)
        text = "判定: ACCEPT\n確信度: 150%\n理由: テスト。"
        _, confidence, _ = agent._parse_verdict(text)
        assert confidence == 1.0

        text2 = "判定: REJECT\n確信度: 0%\n理由: テスト。"
        _, confidence2, _ = agent._parse_verdict(text2)
        assert confidence2 == 0.0

    def test_parse_verdict_malformed_input(self):
        """'判定:' 行が存在しない不正入力でも UNCERTAIN にフォールバックすること"""
        agent = DebateAgent(AgentRole.ARBITER)
        text = "これは判定フォーマットに従っていないテキストです。"
        verdict_type, confidence, reasoning = agent._parse_verdict(text)

        assert verdict_type == VerdictType.UNCERTAIN
        assert 0.0 <= confidence <= 1.0

    def test_parse_verdict_empty_input(self):
        """空文字列でクラッシュせず UNCERTAIN を返すこと"""
        agent = DebateAgent(AgentRole.ARBITER)
        verdict_type, confidence, reasoning = agent._parse_verdict("")

        assert verdict_type == VerdictType.UNCERTAIN


class TestDebateEngine:
    """DebateEngine の生成・合意構築を検証"""

    def test_create_engine_default(self):
        """デフォルト構成で proposer×1, critic×1, arbiter×1 が生成されること"""
        engine = DebateEngine()
        assert engine.proposer.role == AgentRole.PROPOSER
        assert len(engine.critics) == 1
        assert engine.arbiter.role == AgentRole.ARBITER

    def test_create_engine_multi_critics(self):
        """num_critics=3 で critic が 3 体生成されること"""
        engine = DebateEngine(num_critics=3)
        assert len(engine.critics) == 3
        assert all(c.role == AgentRole.CRITIC for c in engine.critics)
    
    def test_build_consensus_accepted(self):
        """ACCEPT 判定の場合、accepted=True かつメタデータに rally 統計が含まれること"""
        engine = DebateEngine()

        rally = [
            RallyTurn(AgentRole.PROPOSER, "支持論拠", 0.8, 1),
            RallyTurn(AgentRole.CRITIC, "批判1", 0.6, 2),
            RallyTurn(AgentRole.PROPOSER, "反論", 0.85, 3),
            RallyTurn(AgentRole.CRITIC, "同意する、妥当だ", 0.5, 4),
        ]

        rounds = [
            DebateRound(
                round_number=1,
                rally=rally,
                converged=True,
                convergence_reason="@Critic が同意",
                proposition=DebateArgument(AgentRole.PROPOSER, "支持論拠", 0.8),
                critiques=[
                    DebateArgument(AgentRole.CRITIC, "批判1", 0.6),
                ],
            )
        ]

        verdict = Verdict(
            type=VerdictType.ACCEPT,
            reasoning="論拠が勝る",
            confidence=0.75
        )

        result = engine._build_consensus("テスト主張", rounds, verdict)

        assert result.accepted is True
        assert result.confidence == 0.75
        assert len(result.rounds) == 1
        assert result.metadata["total_rally_turns"] == 4
        assert result.metadata["converged"] is True

    def test_build_consensus_rejected(self):
        """REJECT 判定の場合、accepted=False になること"""
        engine = DebateEngine()

        rally = [
            RallyTurn(AgentRole.PROPOSER, "弱い論拠", 0.4, 1),
            RallyTurn(AgentRole.CRITIC, "論拠が不十分", 0.8, 2),
            RallyTurn(AgentRole.PROPOSER, "再考する", 0.3, 3),
            RallyTurn(AgentRole.CRITIC, "やはり不十分", 0.85, 4),
        ]

        rounds = [
            DebateRound(
                round_number=1,
                rally=rally,
                converged=False,
                convergence_reason="",
                proposition=DebateArgument(AgentRole.PROPOSER, "弱い論拠", 0.4),
                critiques=[
                    DebateArgument(AgentRole.CRITIC, "論拠が不十分", 0.8),
                ],
            )
        ]

        verdict = Verdict(
            type=VerdictType.REJECT,
            reasoning="Critic の批判が優勢",
            confidence=0.8
        )

        result = engine._build_consensus("テスト主張", rounds, verdict)

        assert result.accepted is False
        assert result.confidence == 0.8


class TestAuditRecord:
    """AuditRecord データクラスの生成と属性保持を検証"""

    def test_create_record(self):
        """全フィールドが生成時の値を保持すること"""
        record = AuditRecord(
            record_id="audit_001",
            ccl_expression="/noe+",
            execution_result="分析結果",
            debate_summary="ラウンド数: 3",
            consensus_accepted=True,
            confidence=0.85,
            dissent_reasons=[]
        )
        assert record.record_id == "audit_001"
        assert record.ccl_expression == "/noe+"
        assert record.consensus_accepted is True
        assert record.confidence == 0.85
        assert record.dissent_reasons == []

    def test_create_record_with_dissent(self):
        """dissent_reasons が正しく保持されること"""
        record = AuditRecord(
            record_id="audit_002",
            ccl_expression="/dia+",
            execution_result="",
            debate_summary="",
            consensus_accepted=False,
            confidence=0.4,
            dissent_reasons=["論拠不足", "データ不整合"]
        )
        assert len(record.dissent_reasons) == 2
        assert record.consensus_accepted is False


class TestAuditStore:
    """AuditStore のテスト"""
    
    # PURPOSE: 一時ストア
    @pytest.fixture
    def temp_store(self, tmp_path):
        """一時ストア"""
        db_path = tmp_path / "test_audit.db"
        return AuditStore(db_path)
    
    # PURPOSE: 記録と取得
    def test_record_and_get(self, temp_store):
        """記録と取得"""
        record = AuditRecord(
            record_id="",
            ccl_expression="/s+",
            execution_result="成功",
            debate_summary="テスト",
            consensus_accepted=True,
            confidence=0.9,
            dissent_reasons=["反対意見1"]
        )
        
        record_id = temp_store.record(record)
        assert record_id is not None
        
        retrieved = temp_store.get(record_id)
        assert retrieved is not None
        assert retrieved.ccl_expression == "/s+"
        assert retrieved.confidence == 0.9
    
    # PURPOSE: クエリ
    def test_query(self, temp_store):
        """クエリ"""
        # 複数レコードを挿入
        for i in range(5):
            temp_store.record(AuditRecord(
                record_id="",
                ccl_expression=f"/wf{i}+",
                execution_result=f"結果{i}",
                debate_summary="",
                consensus_accepted=i % 2 == 0,
                confidence=0.5 + i * 0.1,
                dissent_reasons=[]
            ))
        
        # 全件クエリ
        all_records = temp_store.query()
        assert len(all_records) == 5
        
        # 確信度フィルタ
        high_conf = temp_store.query(min_confidence=0.7)
        assert len(high_conf) == 3
    
    # PURPOSE: 統計取得
    def test_get_stats(self, temp_store):
        """統計取得"""
        for i in range(4):
            temp_store.record(AuditRecord(
                record_id="",
                ccl_expression="/test+",
                execution_result="",
                debate_summary="",
                consensus_accepted=i < 3,  # 3件受理、1件拒否
                confidence=0.8,
                dissent_reasons=[]
            ))
        
        stats = temp_store.get_stats()
        assert stats.total_records == 4
        assert stats.accepted_count == 3
        assert stats.rejected_count == 1


class TestAuditReporter:
    """AuditReporter のテスト"""
    
    # PURPOSE: 期間パース
    def test_parse_period(self, tmp_path):
        """期間パース"""
        store = AuditStore(tmp_path / "test.db")
        reporter = AuditReporter(store)
        
        now = datetime.now()
        
        since_7d = reporter._parse_period("last_7_days")
        assert (now - since_7d).days <= 7
        
        since_30d = reporter._parse_period("last_30_days")
        assert (now - since_30d).days <= 30


class TestRallyTurn:
    """RallyTurn のテスト"""
    
    def test_create_turn(self):
        """ターン作成"""
        turn = RallyTurn(
            speaker=AgentRole.PROPOSER,
            content="FEP は有望だ",
            confidence=0.8,
            turn_number=1,
        )
        assert turn.speaker == AgentRole.PROPOSER
        assert turn.turn_number == 1


class TestConvergenceDetector:
    """ConvergenceDetector のテスト"""
    
    def test_not_converged_too_few_turns(self):
        """最低ターン数未達では収束しない"""
        history = [
            RallyTurn(AgentRole.PROPOSER, "支持する", 0.8, 1),
            RallyTurn(AgentRole.CRITIC, "同意する", 0.7, 2),
        ]
        converged, reason = ConvergenceDetector.check(history, min_turns=3)
        assert converged is False
    
    def test_converged_mutual_agreement(self):
        """相互同意で収束"""
        history = [
            RallyTurn(AgentRole.PROPOSER, "論拠A", 0.8, 1),
            RallyTurn(AgentRole.CRITIC, "批判B", 0.6, 2),
            RallyTurn(AgentRole.PROPOSER, "確かに妥当な指摘。同意する", 0.7, 3),
            RallyTurn(AgentRole.CRITIC, "修正案に同意する。妥当だ", 0.7, 4),
        ]
        converged, reason = ConvergenceDetector.check(history, min_turns=3)
        assert converged is True
        assert "同意" in reason
    
    def test_converged_critic_concedes(self):
        """Critic が認めて収束"""
        history = [
            RallyTurn(AgentRole.PROPOSER, "論拠A", 0.8, 1),
            RallyTurn(AgentRole.CRITIC, "批判B", 0.6, 2),
            RallyTurn(AgentRole.PROPOSER, "反論C", 0.85, 3),
            RallyTurn(AgentRole.CRITIC, "認めざるを得ない。妥当だ", 0.5, 4),
        ]
        converged, reason = ConvergenceDetector.check(history, min_turns=3)
        assert converged is True
    
    def test_not_converged_insistence(self):
        """固執している場合は収束しない"""
        history = [
            RallyTurn(AgentRole.PROPOSER, "論拠A", 0.8, 1),
            RallyTurn(AgentRole.CRITIC, "批判B", 0.6, 2),
            RallyTurn(AgentRole.PROPOSER, "反論C", 0.85, 3),
            RallyTurn(AgentRole.CRITIC, "しかし認められない。だが同意はできない", 0.7, 4),
        ]
        converged, reason = ConvergenceDetector.check(history, min_turns=3)
        assert converged is False
    
    def test_converged_confidence_stable(self):
        """確信度が安定して収束"""
        history = [
            RallyTurn(AgentRole.PROPOSER, "論拠A", 0.75, 1),
            RallyTurn(AgentRole.CRITIC, "批判B", 0.74, 2),
            RallyTurn(AgentRole.PROPOSER, "反論C", 0.76, 3),
            RallyTurn(AgentRole.CRITIC, "再批判D", 0.75, 4),
        ]
        converged, reason = ConvergenceDetector.check(history, min_turns=3)
        assert converged is True
        assert "収束" in reason


class TestRallyHistory:
    """ラリー履歴フォーマットのテスト"""
    
    def test_format_empty(self):
        """空履歴"""
        agent = DebateAgent(AgentRole.PROPOSER)
        result = agent._format_rally_history([])
        assert result == ""
    
    def test_format_with_mentions(self):
        """@メンション付きフォーマット"""
        agent = DebateAgent(AgentRole.PROPOSER)
        history = [
            RallyTurn(AgentRole.PROPOSER, "支持する", 0.8, 1),
            RallyTurn(AgentRole.CRITIC, "批判する", 0.6, 2),
        ]
        result = agent._format_rally_history(history)
        assert "@Proposer" in result
        assert "@Critic" in result
        assert "Turn 1" in result
        assert "Turn 2" in result


# =============================================================================
# Run
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
