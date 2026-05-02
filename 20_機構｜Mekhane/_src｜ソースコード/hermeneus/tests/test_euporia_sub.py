# PROOF: [L2/Phase2] <- hermeneus/tests/test_euporia_sub.py
"""
EuporiaSubscriber のユニットテスト

定理³ Euporía の環境強制が正しく動作するかを検証する。
6射影スコアリング・ドメイン推定・ドメイン重点座標チェックを含む。
"""
import pytest
from hermeneus.src.event_bus import CognitionEvent, EventType
from hermeneus.src.subscribers.euporia_sub import (
    AYResult,
    AYScorer,
    DEFAULT_ALPHA_SCHEDULE,
    EuporiaSubscriber,
    PRAGMATIC_PATTERNS,
    EPISTEMIC_PATTERNS,
    FUNCTION_PATTERNS,
    PRECISION_PATTERNS,
    TEMPORALITY_PATTERNS,
    SCALE_PATTERNS,
    VALENCE_PATTERNS,
    PROJECTION_PATTERNS,
    DEPTH_THRESHOLDS,
    DOMAIN_NODE_MAP,
    DOMAIN_EMPHASIS,
)


class DummyStepResult:
    """テスト用のダミー StepResult"""
    def __init__(self, output: str):
        self.output = output


# =============================================================================
# パターン検出テスト
# =============================================================================

class TestPatternDetection:
    """affordance パターンの正規表現が正しく機能するか"""

    def test_pragmatic_arrow_next(self):
        """→次 が pragmatic として検出される"""
        assert PRAGMATIC_PATTERNS.search("→次: hermeneus を修正する")

    def test_pragmatic_next_step_ja(self):
        """「次のステップ」が検出される"""
        assert PRAGMATIC_PATTERNS.search("次のステップとして X を実行する")

    def test_pragmatic_task_list(self):
        """未完了タスクリストが検出される"""
        assert PRAGMATIC_PATTERNS.search("- [ ] テストを書く")

    def test_pragmatic_english_next(self):
        """英語の next step が検出される"""
        assert PRAGMATIC_PATTERNS.search("Next step: implement the feature")

    def test_epistemic_discovery_tag(self):
        """[DISCOVERY] タグが検出される"""
        assert EPISTEMIC_PATTERNS.search("[DISCOVERY] 新しいパターンを発見")

    def test_epistemic_finding_ja(self):
        """「判明」が epistemic として検出される"""
        assert EPISTEMIC_PATTERNS.search("調査の結果、原因が判明した")

    def test_epistemic_subjective(self):
        """[主観] が epistemic として検出される"""
        assert EPISTEMIC_PATTERNS.search("[主観] この設計は整合的")

    def test_no_false_positive(self):
        """通常のテキストが誤検知されない"""
        plain = "これは普通の説明文です。特に何もありません。"
        assert not PRAGMATIC_PATTERNS.search(plain)
        assert not EPISTEMIC_PATTERNS.search(plain)


# =============================================================================
# 新規射影パターンテスト
# =============================================================================

class TestProjectionPatterns:
    """6射影 (Function/Precision/Temporality/Scale/Valence) のパターン検出"""

    # --- Function ---
    def test_function_explore(self):
        """「探索」が Function として検出される"""
        assert FUNCTION_PATTERNS.search("探索的にアプローチする")

    def test_function_exploit(self):
        """「活用」が Function として検出される"""
        assert FUNCTION_PATTERNS.search("既存の知識を活用する")

    def test_function_wf_ref(self):
        """/ske が Function として検出される"""
        assert FUNCTION_PATTERNS.search("/ske で発散する")

    # --- Precision ---
    def test_precision_confidence_label(self):
        """[確信] が Precision として検出される"""
        assert PRECISION_PATTERNS.search("[確信] この API は安定している")

    def test_precision_source(self):
        """SOURCE が Precision として検出される"""
        assert PRECISION_PATTERNS.search("[SOURCE: view_file] 型は str")

    def test_precision_taint(self):
        """TAINT が Precision として検出される"""
        assert PRECISION_PATTERNS.search("[TAINT: 記憶] バージョンは 3.x")

    # --- Temporality ---
    def test_temporality_past(self):
        """「過去」が Temporality として検出される"""
        assert TEMPORALITY_PATTERNS.search("過去のセッションでは")

    def test_temporality_future(self):
        """「今後」が Temporality として検出される"""
        assert TEMPORALITY_PATTERNS.search("今後の対応として")

    def test_temporality_prior(self):
        """prior が Temporality として検出される"""
        assert TEMPORALITY_PATTERNS.search("prior distribution を更新")

    # --- Scale ---
    def test_scale_local(self):
        """「局所」が Scale として検出される"""
        assert SCALE_PATTERNS.search("局所的な修正を行う")

    def test_scale_global(self):
        """「全体」が Scale として検出される"""
        assert SCALE_PATTERNS.search("全体への影響を評価")

    def test_scale_integration(self):
        """「統合」が Scale として検出される"""
        assert SCALE_PATTERNS.search("統合テストを実行")

    # --- Valence ---
    def test_valence_risk(self):
        """「リスク」が Valence として検出される"""
        assert VALENCE_PATTERNS.search("リスクとして考慮すべき")

    def test_valence_tradeoff(self):
        """trade-off が Valence として検出される"""
        assert VALENCE_PATTERNS.search("trade-off を検討する")

    def test_valence_however(self):
        """「ただし」が Valence として検出される"""
        assert VALENCE_PATTERNS.search("ただし、X には懸念がある")

    # --- 偽陽性 ---
    def test_no_false_positive_new_patterns(self):
        """通常テキストが新規パターンに誤検知されない"""
        plain = "天気が良い日にコードを書く。"
        assert not FUNCTION_PATTERNS.search(plain)
        assert not PRECISION_PATTERNS.search(plain)
        assert not TEMPORALITY_PATTERNS.search(plain)
        assert not SCALE_PATTERNS.search(plain)
        assert not VALENCE_PATTERNS.search(plain)


# =============================================================================
# Subscriber ハンドラテスト
# =============================================================================

class TestEuporiaSubscriber:
    """EuporiaSubscriber.handle() の動作テスト"""

    def _make_event(
        self,
        output: str,
        source_node: str = "/noe",
        depth: str = "",
    ) -> CognitionEvent:
        """テスト用イベントを生成"""
        metadata = {}
        if depth:
            metadata["depth"] = depth
        return CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult(output),
            source_node=source_node,
            metadata=metadata,
        )

    def test_empty_output_returns_none(self):
        """空出力には反応しない"""
        sub = EuporiaSubscriber()
        event = self._make_event("")
        assert sub.handle(event) is None

    def test_short_output_returns_none(self):
        """50文字未満の短い出力は L0 とみなしスキップ"""
        sub = EuporiaSubscriber()
        event = self._make_event("短い出力")
        assert sub.handle(event) is None

    def test_no_affordances_warns(self):
        """行為可能性の記載がない出力に警告を出す"""
        sub = EuporiaSubscriber(default_depth="L2")
        output = (
            "これは分析結果です。" * 20  # 十分な長さだが affordance なし
        )
        event = self._make_event(output)
        result = sub.handle(event)
        assert result is not None
        assert "Euporía" in result
        assert "Pragmatic 不足" in result

    def test_pragmatic_only_passes_l1(self):
        """pragmatic のみで L1 は通過する"""
        sub = EuporiaSubscriber(default_depth="L1")
        output = (
            "分析の結果を報告します。" * 10
            + "\n→次: テストを実行して検証する"
        )
        event = self._make_event(output, depth="L1")
        result = sub.handle(event)
        assert result is None  # L1 は pragmatic ≥ 1 で通過

    def test_pragmatic_only_warns_l2(self):
        """pragmatic のみで L2 は epistemic 不足の警告"""
        sub = EuporiaSubscriber(default_depth="L2")
        output = (
            "分析の結果を報告します。" * 10
            + "\n→次: テストを実行\n→次: ドキュメントを更新"
            + "\n探索的にアプローチ"     # Function
            + "\n[確信] この分析は正しい"   # Precision
        )
        event = self._make_event(output, depth="L2")
        result = sub.handle(event)
        assert result is not None
        assert "Epistemic 不足" in result

    def test_full_affordances_passes(self):
        """pragmatic + epistemic + 重点座標が十分なら通過"""
        sub = EuporiaSubscriber(default_depth="L2")
        output = (
            "分析の結果を報告します。" * 10
            + "\n[DISCOVERY] 新しいパターンを発見した"
            + "\n→次: テストを実行"
            + "\n→次: ドキュメントを更新"
            + "\n探索的にアプローチし"     # Function
            + "\n[確信] 正しい"               # Precision
        )
        event = self._make_event(output, depth="L2")
        result = sub.handle(event)
        assert result is None  # L2 通過

    def test_l0_skips_check(self):
        """L0 深度ではチェックをスキップ"""
        sub = EuporiaSubscriber()
        output = "これは単純な操作結果です。" * 10
        event = self._make_event(output, depth="L0")
        result = sub.handle(event)
        assert result is None

    def test_depth_from_modifier_plus(self):
        """source_node の + 修飾子から L3 を推定"""
        sub = EuporiaSubscriber()
        output = (
            "深い分析結果。" * 20
            + "\n→次: Xを実行\n→次: Yを検証\n→次: Zを報告"
            + "\n[DISCOVERY] Aが判明\n[DISCOVERY] Bが発見された"
            + "\n探索的にアプローチ"     # Function
            + "\n[確信] この方針"           # Precision
        )
        event = self._make_event(output, source_node="/noe+")
        result = sub.handle(event)
        # L3 = pragmatic≥3, epistemic≥2 + Cognition 重点座標 → 満たしているので通過
        assert result is None

    def test_depth_from_modifier_minus(self):
        """source_node の - 修飾子から L1 を推定"""
        sub = EuporiaSubscriber()
        output = (
            "軽い分析結果。" * 10
            + "\n→次: 確認する"
        )
        event = self._make_event(output, source_node="/noe-")
        result = sub.handle(event)
        # L1 = pragmatic≥1 → 満たしているので通過
        assert result is None

    def test_l3_insufficient_warns(self):
        """L3 で affordance が不足していると警告"""
        sub = EuporiaSubscriber()
        output = (
            "深い分析結果。" * 20
            + "\n→次: Xを実行"  # pragmatic=1 (要件: ≥3)
            + "\n[DISCOVERY] Aを確認"  # epistemic=1 (要件: ≥2) — 「判明」は EPISTEMIC_PATTERNS にマッチするため回避
        )
        event = self._make_event(output, source_node="/noe+")
        result = sub.handle(event)
        assert result is not None
        assert "Pragmatic 不足" in result
        assert "Epistemic 不足" in result


# =============================================================================
# ドメイン推定テスト
# =============================================================================

class TestDomainEstimation:
    """_extract_domain() が正しくドメインを推定するか"""

    def _make_event(
        self,
        source_node: str = "/noe",
        domain: str = "",
    ) -> CognitionEvent:
        metadata = {}
        if domain:
            metadata["domain"] = domain
        return CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult("dummy" * 20),
            source_node=source_node,
            metadata=metadata,
        )

    def test_metadata_explicit_domain(self):
        """メタデータで明示されたドメインを優先"""
        sub = EuporiaSubscriber()
        event = self._make_event(source_node="/noe", domain="Linkage")
        assert sub._extract_domain(event) == "Linkage"

    def test_description_domain_from_typos(self):
        """@typos ノードは Description ドメイン"""
        sub = EuporiaSubscriber()
        event = self._make_event(source_node="@typos")
        assert sub._extract_domain(event) == "Description"

    def test_horos_domain_from_proof(self):
        """@proof ノードは Hóros ドメイン (C1': Constraint → Hóros)"""
        sub = EuporiaSubscriber()
        event = self._make_event(source_node="@proof")
        assert sub._extract_domain(event) == "Hóros"

    def test_linkage_domain_from_eat(self):
        """/eat ノードは Linkage ドメイン"""
        sub = EuporiaSubscriber()
        event = self._make_event(source_node="/eat")
        assert sub._extract_domain(event) == "Linkage"

    def test_default_cognition_domain(self):
        """一般的な動詞ノードは Cognition (デフォルト)"""
        sub = EuporiaSubscriber()
        event = self._make_event(source_node="/noe+")
        assert sub._extract_domain(event) == "Cognition"

    def test_horos_domain_from_fit(self):
        """/fit ノードは Hóros ドメイン (C1': Constraint → Hóros)"""
        sub = EuporiaSubscriber()
        event = self._make_event(source_node="/fit")
        assert sub._extract_domain(event) == "Hóros"


# =============================================================================
# 射影計算テスト
# =============================================================================

class TestComputeProjections:
    """_compute_projections() が正しくパターン出現数を返すか"""

    def test_empty_output(self):
        """空出力は全射影 0"""
        sub = EuporiaSubscriber()
        result = sub._compute_projections("")
        assert all(v == 0 for v in result.values())
        assert set(result.keys()) == set(PROJECTION_PATTERNS.keys())

    def test_value_pragmatic_counted(self):
        """pragmatic パターンが Value_P としてカウントされる"""
        sub = EuporiaSubscriber()
        output = "→次: テスト実行\n→次: ドキュメント更新"
        result = sub._compute_projections(output)
        assert result["Value_P"] >= 2

    def test_function_counted(self):
        """探索/活用パターンが Function としてカウントされる"""
        sub = EuporiaSubscriber()
        output = "探索的にアプローチし、既知のパターンを活用する"
        result = sub._compute_projections(output)
        assert result["Function"] >= 2

    def test_precision_counted(self):
        """確信度ラベルが Precision としてカウントされる"""
        sub = EuporiaSubscriber()
        output = "[確信] この実装は正しい。SOURCE で確認済み。"
        result = sub._compute_projections(output)
        assert result["Precision"] >= 2

    def test_mixed_projections(self):
        """複数の射影が同時にカウントされる"""
        sub = EuporiaSubscriber()
        output = (
            "探索の結果、リスクが判明した。\n"
            "全体への影響を考慮し、今後の対応を検討する。\n"
            "→次: 実装を開始\n"
            "[確信] この方針は妥当。"
        )
        result = sub._compute_projections(output)
        assert result["Function"] >= 1     # 探索
        assert result["Valence"] >= 1       # リスク
        assert result["Scale"] >= 1         # 全体
        assert result["Temporality"] >= 1   # 今後
        assert result["Value_P"] >= 1       # →次
        assert result["Precision"] >= 1     # [確信]


# =============================================================================
# ドメイン重点座標テスト (Layer 2)
# =============================================================================

class TestDomainEmphasis:
    """L2+ でドメイン重点座標のチェックが正しく働くか"""

    def _make_event(
        self,
        output: str,
        source_node: str = "/noe",
        depth: str = "",
        domain: str = "",
    ) -> CognitionEvent:
        metadata = {}
        if depth:
            metadata["depth"] = depth
        if domain:
            metadata["domain"] = domain
        return CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult(output),
            source_node=source_node,
            metadata=metadata,
        )

    def test_cognition_emphasis_function_precision(self):
        """Cognition ドメインで Function/Precision が不足すると警告"""
        sub = EuporiaSubscriber()
        # pragmatic/epistemic は満たすが Function/Precision がない
        output = (
            "分析の結果を報告します。" * 10
            + "\n[DISCOVERY] パターン発見"
            + "\n→次: テスト実行\n→次: ドキュメント更新"
        )
        event = self._make_event(output, depth="L2", domain="Cognition")
        result = sub.handle(event)
        assert result is not None
        assert "Function" in result
        assert "Precision" in result
        assert "重点座標" in result

    def test_cognition_emphasis_satisfied(self):
        """Cognition ドメインで Function/Precision も満たせば通過"""
        sub = EuporiaSubscriber()
        output = (
            "分析の結果を報告します。" * 10
            + "\n[DISCOVERY] パターン発見"
            + "\n→次: テスト実行\n→次: ドキュメント更新"
            + "\n探索的にアプローチし"   # Function
            + "\n[確信] 正しい"           # Precision
        )
        event = self._make_event(output, depth="L2", domain="Cognition")
        result = sub.handle(event)
        assert result is None

    def test_horos_emphasis_valence(self):
        """Hóros ドメインで Valence 不足を検出 (C1': Constraint → Hóros)"""
        sub = EuporiaSubscriber()
        output = (
            "定理の判定報告。" * 10
            + "\n[DISCOVERY] 違反パターン発見"
            + "\n→次: 修正実行\n→次: レビュー"
            + "\n[確信] この判定は正しい"   # Precision ✓
            # Valence なし
        )
        event = self._make_event(output, depth="L2", domain="Hóros")
        result = sub.handle(event)
        assert result is not None
        assert "Valence" in result

    def test_l1_skips_emphasis(self):
        """L1 ではドメイン重点座標チェックをスキップ"""
        sub = EuporiaSubscriber()
        output = (
            "分析結果。" * 10
            + "\n→次: 確認する"
        )
        event = self._make_event(output, depth="L1", domain="Cognition")
        result = sub.handle(event)
        # L1 は pragmatic≥1 のみ。重点座標チェックなし
        assert result is None

    def test_linkage_emphasis_scale_temporality_valence(self):
        """Linkage ドメインで Scale/Temporality/Valence が不足すると警告 (C1': Valence 追加)"""
        sub = EuporiaSubscriber()
        output = (
            "索引作成の結果。" * 10
            + "\n[DISCOVERY] 新規論文を発見"
            + "\n→次: 消化実行\n→次: レビュー"
            # Scale/Temporality/Valence なし
        )
        event = self._make_event(output, depth="L2", domain="Linkage")
        result = sub.handle(event)
        assert result is not None
        assert "Scale" in result
        assert "Temporality" in result
        assert "Valence" in result


# =============================================================================
# スコアテスト
# =============================================================================

class TestEuporiaScore:
    """score() が出力長 + 射影カバレッジに応じた値を返すか"""

    def test_no_output_zero_score(self):
        sub = EuporiaSubscriber()
        event = CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=None,
        )
        assert sub.score(event) == 0.0

    def test_short_output_low_score(self):
        sub = EuporiaSubscriber()
        event = CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult("短い"),
        )
        score = sub.score(event)
        assert 0.0 < score < 0.5

    def test_long_output_no_projections(self):
        """長い出力でも射影なしなら中程度のスコア"""
        sub = EuporiaSubscriber()
        event = CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult("x" * 2500),
        )
        score = sub.score(event)
        # base(0.2) + length(0.3) + coverage(0.0) + ay_bonus(0.0) = 0.5
        assert 0.45 <= score <= 0.55

    def test_rich_output_high_score(self):
        """長い出力 + 全射影カバーで高スコア"""
        sub = EuporiaSubscriber()
        output = (
            "x" * 2500
            + "\n→次: 実行する"         # Value_P
            + "\n[DISCOVERY] 判明"       # Value_E
            + "\n探索的に"              # Function
            + "\n[確信] 正しい"          # Precision
            + "\n今後の対応"            # Temporality
            + "\n全体への影響"          # Scale
            + "\nリスクを考慮"          # Valence
        )
        event = CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult(output),
        )
        score = sub.score(event)
        # base(0.2) + length + coverage + ay_bonus ≈ 0.9+
        assert score >= 0.85

    def test_coverage_bonus_partial(self):
        """一部の射影のみカバーで中間的カバレッジボーナス"""
        sub = EuporiaSubscriber()
        output = (
            "x" * 100
            + "\n→次: テスト"           # Value_P
            + "\n探索的に"              # Function
            # 他の射影なし → coverage = 2/6
        )
        event = CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult(output),
        )
        score = sub.score(event)
        # base(0.2) + length(tiny) + coverage(2/6*0.3≈0.1) + ay_bonus
        assert 0.2 < score < 0.7


# =============================================================================
# AYScorer テスト — Layer 1 (micro)
# =============================================================================

class TestAYScorerMicro:
    """AYScorer.compute_micro のテスト"""

    def test_empty_output(self):
        """空出力で micro=0"""
        scorer = AYScorer()
        assert scorer.compute_micro("", "L2") == 0.0

    def test_full_projections_l2(self):
        """全6射影が揃った出力で micro≈1.0 (L2)"""
        scorer = AYScorer()
        output = (
            "→次: テストする\n提案: Aを試す\n"  # Value_P (pragmatic x2)
            + "この発見により\n分析の結果\n"      # Value_E (epistemic x2)
            + "探索的に\n活用する\n"              # Function x2
            + "[確信] 正しい\nエビデンス\n"       # Precision x2
            + "今後の対応\n振り返り\n"            # Temporality x2
            + "全体への影響\nマクロ\n"            # Scale x2
            + "リスクを考慮\n改善する\n"          # Valence x2
        )
        score = scorer.compute_micro(output, "L2")
        assert score > 0.7  # 全射影カバーで高スコア

    def test_partial_projections(self):
        """部分的な射影で 0 < micro < 1"""
        scorer = AYScorer()
        output = (
            "→次: テスト\n"  # Value_P (1)
            + "探索的に\n"    # Function (1)
        )
        score = scorer.compute_micro(output, "L2")
        assert 0.0 < score < 0.8

    def test_depth_scaling_l1_vs_l3(self):
        """L1 vs L3 で同一出力でも正規化が異なる"""
        scorer = AYScorer()
        output = "→次: テスト\nこの発見により\n"
        score_l1 = scorer.compute_micro(output, "L1")
        score_l3 = scorer.compute_micro(output, "L3")
        # L1 は閾値が低い → 同じ出力で充足率が高くなるはず
        assert score_l1 >= score_l3

    def test_l0_bypass(self):
        """L0 でも micro は計算可能 (閾値が0なのでカウント有無のみ)"""
        scorer = AYScorer()
        output = "→次: テスト\n"
        score = scorer.compute_micro(output, "L0")
        assert score > 0.0


# =============================================================================
# AYScorer テスト — Layer 2 (macro)
# =============================================================================

class MockEmbedder:
    """テスト用のモック embedder"""

    def novelty(self, text1: str, text2: str) -> float:
        """単純な文字列長差による疑似距離"""
        if not text1 or not text2:
            return 0.0
        # 長さの差の比率を疑似距離とする
        max_len = max(len(text1), len(text2))
        if max_len == 0:
            return 0.0
        diff = abs(len(text1) - len(text2))
        return min(diff / max_len, 1.0)


class MockEmbedderFixed:
    """固定値を返すモック embedder"""

    def __init__(self, value: float):
        self._value = value

    def novelty(self, text1: str, text2: str) -> float:
        return self._value


class MockEmbedderError:
    """エラーを投げるモック embedder"""

    def novelty(self, text1: str, text2: str) -> float:
        raise RuntimeError("Embedding API failure")


class TestAYScorerMacro:
    """AYScorer.compute_macro のテスト"""

    def test_no_embedder(self):
        """embedder=None で macro=0 (後方互換)"""
        scorer = AYScorer()
        assert scorer.compute_macro("input", "output", None) == 0.0

    def test_identical_io(self):
        """入出力同一で macro≈0"""
        scorer = AYScorer()
        embedder = MockEmbedder()
        result = scorer.compute_macro("same text", "same text", embedder)
        assert result == 0.0

    def test_different_io(self):
        """入出力が大きく異なると macro>0"""
        scorer = AYScorer()
        embedder = MockEmbedder()
        result = scorer.compute_macro("短い", "これは大きく異なる長い出力テキストです" * 10, embedder)
        assert result > 0.3

    def test_empty_input(self):
        """空入力で macro=0"""
        scorer = AYScorer()
        embedder = MockEmbedder()
        assert scorer.compute_macro("", "output", embedder) == 0.0

    def test_empty_output(self):
        """空出力で macro=0"""
        scorer = AYScorer()
        embedder = MockEmbedder()
        assert scorer.compute_macro("input", "", embedder) == 0.0

    def test_embedder_error_returns_zero(self):
        """embedder がエラーを投げても macro=0"""
        scorer = AYScorer()
        embedder = MockEmbedderError()
        result = scorer.compute_macro("input", "output", embedder)
        assert result == 0.0

    def test_macro_clipped_to_01(self):
        """macro は [0, 1] にクリップされる"""
        scorer = AYScorer()
        embedder = MockEmbedderFixed(1.5)  # 1.0 を超える値
        result = scorer.compute_macro("input", "output", embedder)
        assert result == 1.0

        embedder_neg = MockEmbedderFixed(-0.5)  # 負の値
        result_neg = scorer.compute_macro("input", "output", embedder_neg)
        assert result_neg == 0.0


# =============================================================================
# AYScorer テスト — 統合 compute()
# =============================================================================

class TestAYScorerCompute:
    """AYScorer.compute の統合テスト"""

    def test_no_embedder_micro_only(self):
        """embedder なしでは micro のみ (ay_score = ay_micro)"""
        scorer = AYScorer()
        output = "→次: テスト\nこの発見により\n"
        result = scorer.compute(output=output, depth="L2")
        assert isinstance(result, AYResult)
        assert result.ay_score == result.ay_micro
        assert result.ay_macro == 0.0
        assert result.depth == "L2"
        assert "Value_P" in result.projections

    def test_with_embedder(self):
        """embedder ありで2層統合"""
        scorer = AYScorer()
        embedder = MockEmbedderFixed(0.6)
        output = "→次: テスト\nこの発見により\n"
        result = scorer.compute(
            output=output,
            depth="L2",
            input_context="入力コンテキスト",
            embedder=embedder,
        )
        # L2: α=0.5 → ay_score = 0.5*micro + 0.5*0.6
        assert result.ay_macro == 0.6
        assert result.ay_score != result.ay_micro

    def test_alpha_schedule_l1(self):
        """L1 は α=0.8 で micro 重視"""
        scorer = AYScorer()
        embedder = MockEmbedderFixed(0.5)
        output = "→次: テスト\nこの発見により\n"
        result = scorer.compute(
            output=output, depth="L1",
            input_context="input", embedder=embedder,
        )
        # α=0.8 → micro が支配的
        expected = 0.8 * result.ay_micro + 0.2 * 0.5
        assert abs(result.ay_score - round(expected, 4)) < 0.01

    def test_alpha_schedule_l3(self):
        """L3 は α=0.3 で embedding 重視"""
        scorer = AYScorer()
        embedder = MockEmbedderFixed(0.8)
        output = "→次: テスト\nこの発見により\n"
        result = scorer.compute(
            output=output, depth="L3",
            input_context="input", embedder=embedder,
        )
        # α=0.3 → macro (0.8) が支配的
        expected = 0.3 * result.ay_micro + 0.7 * 0.8
        assert abs(result.ay_score - round(expected, 4)) < 0.01


# =============================================================================
# EuporiaSubscriber 統合テスト — AY スコアリング
# =============================================================================

class TestAYIntegration:
    """EuporiaSubscriber と AYScorer の統合テスト"""

    def test_backward_compat_no_embedder(self):
        """embedder なしで既存の動作を維持"""
        sub = EuporiaSubscriber()
        assert sub.embedder is None
        assert sub.ay_scorer is not None

    def test_subscriber_with_embedder(self):
        """embedder を渡した EuporiaSubscriber の初期化"""
        embedder = MockEmbedder()
        sub = EuporiaSubscriber(embedder=embedder)
        assert sub.embedder is embedder

    def test_handle_records_ay_in_trace(self):
        """handle() の Trace に ay_score が含まれる"""
        sub = EuporiaSubscriber()
        output = (
            "→次: テストする\n提案: Aを試す\n"
            + "この発見により\n分析の結果\n"
            + "探索的に\n"
            + "[確信] 正しい\n"
            + "今後の対応\n"
            + "全体への影響\n"
            + "リスクを考慮\n"
        )
        event = CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult(output),
        )
        result = sub.handle(event)
        # affordance 十分で None を返す
        assert result is None
        # Trace にスコアが記録されている
        assert len(sub.stigmergy_traces) > 0
        trace = sub.stigmergy_traces[-1]
        assert "ay_score" in trace.payload
        assert "ay_micro" in trace.payload
        assert "ay_macro" in trace.payload
        assert trace.payload["ay_macro"] == 0.0  # embedder なし
        assert "presheaf_score" in trace.payload
        assert "reachable_wf_count" in trace.payload

    def test_handle_with_embedder_records_macro(self):
        """embedder あり + input_context ありで macro が記録される"""
        embedder = MockEmbedderFixed(0.5)
        sub = EuporiaSubscriber(embedder=embedder)
        output = (
            "→次: テストする\n提案: Aを試す\n"
            + "この発見により\n分析の結果\n"
            + "探索的に\n"
            + "[確信] 正しい\n"
            + "今後の対応\n"
            + "全体への影響\n"
            + "リスクを考慮\n"
        )
        event = CognitionEvent(
            event_type=EventType.EXECUTION_COMPLETE,
            step_result=DummyStepResult(output),
            metadata={"input_context": "入力テキスト"},
        )
        result = sub.handle(event)
        assert result is None
        trace = sub.stigmergy_traces[-1]
        assert trace.payload["ay_macro"] == 0.5

    def test_custom_alpha_schedule(self):
        """カスタム alpha_schedule での初期化"""
        custom = {"L0": 1.0, "L1": 0.9, "L2": 0.6, "L3": 0.2}
        sub = EuporiaSubscriber(alpha_schedule=custom)
        assert sub.ay_scorer.alpha_schedule == custom


# =============================================================================
# PresheafScorer テスト — E4-4 Stage 2
# =============================================================================

class MockWFResolver:
    """テスト用の WFResolver モック — クラスメソッドで呼ばれるため staticmethod で実装"""
    _wf_dict: dict[str, str] = {}
    
    def __init__(self, wf_dict: dict[str, str]):
        # クラス変数に設定 (monkeypatch 後に WFResolver.load_definition() で呼ばれる)
        MockWFResolver._wf_dict = wf_dict
        
    @staticmethod
    def load_definition(wf_id: str) -> str:
        return MockWFResolver._wf_dict.get(wf_id, "")

class TestPresheafScorer:
    """PresheafScorer のユニットテスト"""

    def test_empty_output(self):
        """出力が空の場合、常にスコア0で到達可能WFは0件"""
        from hermeneus.src.subscribers.euporia_sub import PresheafScorer
        scorer = PresheafScorer(drift_threshold=0.8)
        # 空文字列はショートカットで即座に空の PresheafResult を返す
        result = scorer.compute("", "/noe")

        assert result.presheaf_score == 0.0
        assert result.reachable_wf_count == 0
        assert len(result.wf_details) == 0

    def test_compute_with_mocked_classmethod(self, monkeypatch):
        """到達可能な WF の (1 - drift) 加算を検証"""
        from hermeneus.src.macro_executor import WFResolver, EntropyEstimator
        from hermeneus.src.subscribers.euporia_sub import PresheafScorer

        # WF 定義のモック: 特定の動詞のみ定義を返す
        wf_defs = {
            "noe": "definition of noe",
            "bou": "definition of bou",
            "zet": "definition of zet",
        }
        monkeypatch.setattr(
            WFResolver, "load_definition",
            classmethod(lambda cls, wf_id: wf_defs.get(wf_id))
        )

        # Drift のモック: WF 定義テキストに応じて固定値を返す
        drift_map = {
            "definition of noe": 0.1,   # 到達可能 (1 - 0.1 = 0.9)
            "definition of bou": 0.5,   # 到達可能 (1 - 0.5 = 0.5)
            "definition of zet": 0.9,   # 到達不可 (0.9 >= threshold)
        }
        monkeypatch.setattr(
            EntropyEstimator, "estimate_drift",
            classmethod(lambda cls, t1, t2: drift_map.get(t2, 1.0))
        )

        scorer = PresheafScorer(drift_threshold=0.8)
        # /tek からの遷移を計算 (tek 自身は除外される)
        result = scorer.compute("dummy output", "/tek")

        # /noe (0.9) + /bou (0.5) = 1.4
        assert abs(result.presheaf_score - 1.4) < 0.01
        assert result.reachable_wf_count == 2

        # 個別詳細の確認
        noe_d = next(d for d in result.wf_details if d["wf_id"] == "noe")
        bou_d = next(d for d in result.wf_details if d["wf_id"] == "bou")
        zet_d = next(d for d in result.wf_details if d["wf_id"] == "zet")

        assert noe_d["drift"] == 0.1
        assert noe_d["reachable"] is True
        assert bou_d["drift"] == 0.5
        assert bou_d["reachable"] is True
        assert zet_d["drift"] == 0.9
        assert zet_d["reachable"] is False

    def test_source_wf_excluded(self, monkeypatch):
        """実行元 WF は計数から除外されることを検証"""
        from hermeneus.src.macro_executor import WFResolver, EntropyEstimator
        from hermeneus.src.subscribers.euporia_sub import PresheafScorer

        # 全動詞に定義を返す (drift=0.3 で全て到達可能)
        monkeypatch.setattr(
            WFResolver, "load_definition",
            classmethod(lambda cls, wf_id: f"def of {wf_id}")
        )
        monkeypatch.setattr(
            EntropyEstimator, "estimate_drift",
            classmethod(lambda cls, t1, t2: 0.3)
        )

        scorer = PresheafScorer(drift_threshold=0.8)
        result = scorer.compute("some output", "/noe")

        # 36動詞 - 1 (noe 自身) = 35 が到達可能
        assert result.reachable_wf_count == 35
        # noe が details に含まれていないことを確認
        wf_ids = [d["wf_id"] for d in result.wf_details]
        assert "noe" not in wf_ids

    def test_drift_threshold(self, monkeypatch):
        """Drift >= threshold の WF は到達不可と判定される"""
        from hermeneus.src.macro_executor import WFResolver, EntropyEstimator
        from hermeneus.src.subscribers.euporia_sub import PresheafScorer

        monkeypatch.setattr(
            WFResolver, "load_definition",
            classmethod(lambda cls, wf_id: f"def of {wf_id}")
        )
        # 全て drift = 0.8 (ちょうど閾値) → 到達不可
        monkeypatch.setattr(
            EntropyEstimator, "estimate_drift",
            classmethod(lambda cls, t1, t2: 0.8)
        )

        scorer = PresheafScorer(drift_threshold=0.8)
        result = scorer.compute("output", "/noe")

        assert result.reachable_wf_count == 0
        assert result.presheaf_score == 0.0
        # 全 WF が reachable=False
        assert all(not d["reachable"] for d in result.wf_details)

    def test_no_wf_definitions(self, monkeypatch):
        """WF 定義が見つからない場合は全て到達不可"""
        from hermeneus.src.macro_executor import WFResolver
        from hermeneus.src.subscribers.euporia_sub import PresheafScorer

        monkeypatch.setattr(
            WFResolver, "load_definition",
            classmethod(lambda cls, wf_id: None)
        )

        scorer = PresheafScorer(drift_threshold=0.8)
        result = scorer.compute("output", "/noe")

        assert result.reachable_wf_count == 0
        assert result.presheaf_score == 0.0
