# PROOF: [L1/テスト] <- hermeneus/tests/test_synteleia.py Synteleia 統合テスト
"""
Synteleia Phase 4 TDD テスト — @S マクロ統合

TDD:
- Red: テスト失敗
- Green: 最小実装
- Refactor: 洗練

Test Categories:
1. SynteleiaOrchestrator 基本動作
2. @syn マクロパース
3. Hermeneus 統合 (@syn → Orchestrator)
"""

import pytest
from pathlib import Path
import sys

# パス設定
HEGEMONIKON_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(HEGEMONIKON_ROOT))
sys.path.insert(0, str(HEGEMONIKON_ROOT / "hermeneus"))

from mekhane.synteleia.orchestrator import SynteleiaOrchestrator
from mekhane.synteleia.base import AuditTarget, AuditTargetType


# =============================================================================
# Category 1: SynteleiaOrchestrator 基本動作
# =============================================================================

class TestSynteleiaOrchestrator:
    """SynteleiaOrchestrator の基本機能テスト"""

    # PURPOSE: デフォルトエージェント構成
    def test_init_default_agents(self):
        """デフォルトエージェント構成"""
        orch = SynteleiaOrchestrator()
        
        # Poiēsis: Ousia, Schema, Horme (3)
        assert len(orch.poiesis_agents) == 3
        
        # Kritai: Perigraphe, Kairos, Operator, Logic, Completeness (5)
        assert len(orch.kritai_agents) == 5
        
        # デフォルトモードは inner
        assert orch.mode == "inner"

    # PURPOSE: シンプルなコード監査
    def test_audit_simple_code(self):
        """シンプルなコード監査"""
        orch = SynteleiaOrchestrator()
        target = AuditTarget(
            content="def hello():\n    print('Hello, world!')\n",
            target_type=AuditTargetType.CODE
        )
        result = orch.audit(target)
        
        # 結果構造が正しい
        assert result is not None
        assert hasattr(result, "passed")
        assert hasattr(result, "summary")
        assert hasattr(result, "agent_results")

    # PURPOSE: 計画ドキュメント監査
    def test_audit_plan_document(self):
        """計画ドキュメント監査"""
        orch = SynteleiaOrchestrator()
        target = AuditTarget(
            content="# Implementation Plan\n\n## Purpose\n\nTo implement feature X.\n",
            target_type=AuditTargetType.PLAN
        )
        result = orch.audit(target)
        
        assert result is not None
        # 並列実行時、supports() でフィルタリングされるため結果数は変動
        assert len(result.agent_results) >= 1  # 最低1エージェント

    # PURPOSE: レポートフォーマット
    def test_format_report(self):
        """レポートフォーマット"""
        orch = SynteleiaOrchestrator()
        target = AuditTarget(
            content="print('test')",
            target_type=AuditTargetType.CODE
        )
        result = orch.audit(target)
        report = orch.format_report(result)
        
        assert "Hegemonikón Audit Report" in report
        assert "Target:" in report


# =============================================================================
# Category 2: @syn マクロパース
# =============================================================================

class TestSynMacroParsing:
    """@syn マクロのパーサー認識テスト"""

    # PURPOSE: @syn· (内積) パース
    def test_parse_syn_inner(self):
        """@syn· (内積) パース"""
        from hermeneus.src.parser import CCLParser
        
        parser = CCLParser()
        ast = parser.parse("@syn·")
        
        # MacroRef として認識
        assert ast is not None
        assert ast.__class__.__name__ == "MacroRef"
        assert ast.name == "syn·"

    # PURPOSE: @syn× (外積) パース
    def test_parse_syn_outer(self):
        """@syn× (外積) パース"""
        from hermeneus.src.parser import CCLParser
        
        parser = CCLParser()
        ast = parser.parse("@syn×")
        
        assert ast is not None
        assert ast.__class__.__name__ == "MacroRef"
        assert ast.name == "syn×"

    # PURPOSE: @poiesis パース
    def test_parse_poiesis(self):
        """@poiesis パース"""
        from hermeneus.src.parser import CCLParser
        
        parser = CCLParser()
        ast = parser.parse("@poiesis")
        
        assert ast is not None
        assert ast.__class__.__name__ == "MacroRef"
        assert ast.name == "poiesis"

    # PURPOSE: @dokimasia パース
    def test_parse_dokimasia(self):
        """@dokimasia パース"""
        from hermeneus.src.parser import CCLParser
        
        parser = CCLParser()
        ast = parser.parse("@dokimasia")
        
        assert ast is not None
        assert ast.__class__.__name__ == "MacroRef"
        assert ast.name == "dokimasia"

    # PURPOSE: @S{O,A,K} セレクタ付きパース
    def test_parse_syn_with_selector(self):
        """@S{O,A,K} セレクタ付きパース"""
        from hermeneus.src.parser import CCLParser
        
        parser = CCLParser()
        ast = parser.parse("@S{O,A,K}")
        
        assert ast is not None
        assert ast.__class__.__name__ == "MacroRef"
        assert ast.name == "S"
        assert ast.args == ["O,A,K"]  # セレクタは引数として認識

    # PURPOSE: @S- (最小選択) パース
    def test_parse_syn_minimal(self):
        """@S- (最小選択) パース"""
        from hermeneus.src.parser import CCLParser
        
        parser = CCLParser()
        # @S- は @S(-) として解釈されるべき
        ast = parser.parse("@S-")
        
        assert ast is not None


# =============================================================================
# Category 3: Hermeneus 統合 (NEW)
# =============================================================================

class TestHermeneusIntegration:
    """Hermeneus → Synteleia 統合テスト"""

    # PURPOSE: @syn マクロ実行 → SynteleiaOrchestrator 呼び出し
    def test_syn_macro_execution(self):
        """@syn マクロ実行 → SynteleiaOrchestrator 呼び出し"""
        from hermeneus.src import compile_ccl
        
        # @syn· を含む CCL をコンパイル
        lmql = compile_ccl("@syn·")
        
        # LMQL 出力に Synteleia 呼び出しが含まれる
        assert lmql is not None
        # 期待: Synteleia 関連のコードが生成される
        assert "synteleia" in lmql.lower() or "audit" in lmql.lower()

    # PURPOSE: Synteleia 付き CCL 実行
    def test_execute_with_synteleia(self):
        """Synteleia 付き CCL 実行"""
        from hermeneus.src.runtime import execute_ccl
        
        # コンテキスト付きで @syn 実行
        result = execute_ccl(
            "@syn·",
            context="def foo(): return 42"
        )
        
        # Synteleia 監査結果を含む
        assert result is not None
        assert hasattr(result, "output")

    # PURPOSE: @poiesis のみ実行（生成層）
    def test_poiesis_only_execution(self):
        """@poiesis のみ実行（生成層）"""
        from hermeneus.src.runtime import execute_ccl
        
        result = execute_ccl(
            "@poiesis",
            context="print('hello')"
        )
        
        # 結果が返る（具体的内容は実装依存）
        assert result is not None

    # PURPOSE: @dokimasia のみ実行（審査層）
    def test_dokimasia_only_execution(self):
        """@dokimasia のみ実行（審査層）"""
        from hermeneus.src.runtime import execute_ccl
        
        result = execute_ccl(
            "@dokimasia",
            context="if True: pass"
        )
        
        assert result is not None


# =============================================================================
# Category 4: エッジケース
# =============================================================================

class TestEdgeCases:
    """エッジケースと境界条件"""

    # PURPOSE: 空コンテンツ監査
    def test_empty_content_audit(self):
        """空コンテンツ監査"""
        orch = SynteleiaOrchestrator()
        target = AuditTarget(
            content="",
            target_type=AuditTargetType.CODE
        )
        result = orch.audit(target)
        
        # 空でもエラーにならない
        assert result is not None

    # PURPOSE: 大規模コンテンツ監査
    def test_large_content_audit(self):
        """大規模コンテンツ監査"""
        orch = SynteleiaOrchestrator()
        large_code = "x = 1\n" * 1000  # 1000行
        target = AuditTarget(
            content=large_code,
            target_type=AuditTargetType.CODE
        )
        result = orch.audit(target)
        
        assert result is not None

    # PURPOSE: 逐次 vs 並列実行の結果一致
    def test_sequential_vs_parallel(self):
        """逐次 vs 並列実行の結果一致"""
        target = AuditTarget(
            content="def test(): pass",
            target_type=AuditTargetType.CODE
        )
        
        orch_seq = SynteleiaOrchestrator(parallel=False)
        orch_par = SynteleiaOrchestrator(parallel=True)
        
        result_seq = orch_seq.audit(target)
        result_par = orch_par.audit(target)
        
        # 検出件数は一致するはず
        assert len(result_seq.agent_results) == len(result_par.agent_results)


# =============================================================================
# Category 5: 新機能テスト (with_depth, 外積モード)
# =============================================================================

class TestNewFeatures:
    """with_depth ファクトリと外積モードのテスト"""

    # PURPOSE: with_depth(L0) — 最小構成 (LogicAgent のみ)
    def test_with_depth_l0(self):
        """L0: Poiēsis 0 + Kritai 1 (LogicAgent), inner モード"""
        orch = SynteleiaOrchestrator.with_depth("L0")
        assert len(orch.poiesis_agents) == 0  # L0 は Poiēsis なし
        assert len(orch.kritai_agents) == 1   # LogicAgent のみ
        assert orch.mode == "inner"

    # PURPOSE: with_depth(L1) — デフォルト inner
    def test_with_depth_l1(self):
        """L1: デフォルト構成 (Poiēsis 3 + Kritai 5), inner モード"""
        orch = SynteleiaOrchestrator.with_depth("L1")
        assert len(orch.poiesis_agents) == 3
        assert len(orch.kritai_agents) == 5  # デフォルト全構成
        assert orch.mode == "inner"

    # PURPOSE: with_depth(L2) — フル inner + SemanticAgent
    def test_with_depth_l2(self):
        """L2: Poiēsis 3 + Kritai 6 (5 + SemanticAgent), inner モード"""
        orch = SynteleiaOrchestrator.with_depth("L2")
        assert len(orch.poiesis_agents) == 3
        assert len(orch.kritai_agents) == 6  # デフォルト5 + SemanticAgent
        assert orch.mode == "inner"

    # PURPOSE: with_depth(L3) — 外積モード
    def test_with_depth_l3(self):
        """L3: outer モード + SemanticAgent"""
        orch = SynteleiaOrchestrator.with_depth("L3")
        assert orch.mode == "outer"
        # L3 は kritai に SemanticAgent を含む (6 agents)
        assert len(orch.kritai_agents) >= 5

    # PURPOSE: 外積モードの初期化
    def test_outer_mode_init(self):
        """外積モード: モード設定の確認"""
        orch = SynteleiaOrchestrator(mode="outer")
        assert orch.mode == "outer"

    # PURPOSE: 外積モードの audit (ローカルエージェントのみ)
    def test_outer_mode_audit(self):
        """外積モード: audit が正常に走ること"""
        orch = SynteleiaOrchestrator(mode="outer")
        target = AuditTarget(
            content="def hello(): return 42",
            target_type=AuditTargetType.CODE
        )
        result = orch.audit(target)
        assert result is not None
        # 外積: P×K ペアの数だけ結果が出る
        assert len(result.agent_results) >= 1


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
