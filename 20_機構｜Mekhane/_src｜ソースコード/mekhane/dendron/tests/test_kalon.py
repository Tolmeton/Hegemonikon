# PROOF: [L3/テスト] <- mekhane/dendron/tests/test_kalon.py
# PURPOSE: Kalon 収束エンジン (Layer 1 + Layer 2) のユニットテスト
"""
Kalon Weight + Convergence テスト

Layer 1: stiffness ランキングの正しさ
Layer 2: JSONL 永続化 + Bayesian Beta 収束判定
"""

from pathlib import Path

import pytest

from mekhane.dendron.kalon_weight import (
    CHECK_TYPE_TO_COORDINATE,
    D_VALUE_TABLE,
    STIFFNESS_TABLE,
    FEPCoordinate,
    KalonSnapshot,
    WeightedIssue,
    make_snapshot,
    weight_issues,
)
from mekhane.dendron.kalon_convergence import (
    HistoryEntry,
    KalonHistory,
    KalonJudgment,
    # 内部 API: 数学関数の境界値テスト用に直接 import
    # 公開 API では到達不可能な数値精度の検証に必要
    _regularized_incomplete_beta,
    _log_binomial,
)
from mekhane.dendron.checker import DendronChecker, ProofStatus


# ═══════════════════════════════════════════════════════
# Layer 1: stiffness ランキング
# ═══════════════════════════════════════════════════════


class TestFEPCoordinate:
    """FEP 座標と d 値テーブルの整合性テスト。"""

    # PURPOSE: 全座標に d 値が定義されていることを確認
    def test_all_coordinates_have_d_value(self):
        """全座標に d 値が存在する。"""
        for coord in FEPCoordinate:
            assert coord in D_VALUE_TABLE, f"{coord} に d 値がない"

    # PURPOSE: 全座標に stiffness が定義されていることを確認
    def test_all_coordinates_have_stiffness(self):
        """全座標に stiffness が存在する。"""
        for coord in FEPCoordinate:
            assert coord in STIFFNESS_TABLE, f"{coord} に stiffness がない"

    # PURPOSE: d 値が 0-3 の範囲内であることを確認
    def test_d_values_are_0_to_3(self):
        """d 値は 0, 1, 2, 3 のいずれか。"""
        for coord, d in D_VALUE_TABLE.items():
            assert d in (0, 1, 2, 3), f"{coord} の d={d} が範囲外"

    # PURPOSE: stiffness = 1/(d+1) の計算が正しいことを確認
    def test_stiffness_formula(self):
        """stiffness = 1/(d+1)。"""
        for coord in FEPCoordinate:
            d = D_VALUE_TABLE[coord]
            expected = 1.0 / (d + 1)
            assert STIFFNESS_TABLE[coord] == pytest.approx(expected), (
                f"{coord}: stiffness={STIFFNESS_TABLE[coord]}, expected={expected}"
            )

    # PURPOSE: Helmholtz (d=0) が最も stiff であることを確認
    def test_helmholtz_is_stiffest(self):
        """Helmholtz (d=0) の stiffness が最大。"""
        assert STIFFNESS_TABLE[FEPCoordinate.HELMHOLTZ] == 1.0

    # PURPOSE: d=0 > d=1 > d=2 > d=3 の順序を確認
    def test_stiffness_ordering(self):
        """d=0 > d=1 > d=2 > d=3 の stiffness 順序。"""
        assert STIFFNESS_TABLE[FEPCoordinate.HELMHOLTZ] > STIFFNESS_TABLE[FEPCoordinate.FLOW]
        assert STIFFNESS_TABLE[FEPCoordinate.FLOW] > STIFFNESS_TABLE[FEPCoordinate.VALUE]
        assert STIFFNESS_TABLE[FEPCoordinate.VALUE] > STIFFNESS_TABLE[FEPCoordinate.SCALE]


class TestCheckTypeMapping:
    """Dendron check_type → FEP 座標マッピングのテスト。"""

    # PURPOSE: マッピングの網羅性を確認
    def test_all_mappings_reference_valid_coordinates(self):
        """全マッピングが有効な FEPCoordinate を参照する。"""
        for check_type, coord in CHECK_TYPE_TO_COORDINATE.items():
            assert isinstance(coord, FEPCoordinate), (
                f"{check_type} のマッピングが不正: {coord}"
            )

    # PURPOSE: 主要な check_type が漏れなくマッピングされていることを確認
    def test_key_check_types_exist(self):
        """主要な check_type がマッピングに含まれる。"""
        expected_types = [
            "L1_missing", "L2_missing", "L2_weak",
            "L3_type_missing", "nf2_missing", "nf3_weak", "bcnf_weak",
        ]
        for ct in expected_types:
            assert ct in CHECK_TYPE_TO_COORDINATE, f"{ct} がマッピングにない"


class TestWeightedIssue:
    """WeightedIssue の weight 計算テスト（公開 API のみ使用）。"""

    # PURPOSE: WeightedIssue を直接構築するヘルパー（_make_issue の代替）
    @staticmethod
    def _build_issue(check_type: str, path: str, detail: str, severity: str = "warning") -> WeightedIssue:
        """公開定数テーブルから WeightedIssue を構築する。"""
        coord = CHECK_TYPE_TO_COORDINATE.get(check_type, FEPCoordinate.SCALE)
        d = D_VALUE_TABLE[coord]
        stiffness = STIFFNESS_TABLE[coord]
        return WeightedIssue(
            check_type=check_type, coordinate=coord, d_value=d,
            stiffness=stiffness, path=path, detail=detail, severity=severity,
        )

    # PURPOSE: weight = stiffness × severity_multiplier の計算確認
    def test_weight_calculation(self):
        """weight = stiffness × severity_multiplier。"""
        issue = self._build_issue("L1_missing", "/test.py", "PROOF 欠落", "error")
        # L1_missing → Helmholtz (d=0) → stiffness=1.0 → error 倍率=3.0
        assert issue.weight == pytest.approx(1.0 * 3.0)

    # PURPOSE: severity 別の倍率が正しいことを確認
    def test_severity_multipliers(self):
        """error=3.0, warning=1.0, info=0.5 の倍率。"""
        error = self._build_issue("L1_orphan", "/a.py", "err", "error")
        warning = self._build_issue("L1_orphan", "/b.py", "warn", "warning")
        info = self._build_issue("L1_orphan", "/c.py", "inf", "info")
        # L1_orphan → Flow (d=1) → stiffness=0.5
        assert error.weight == pytest.approx(0.5 * 3.0)
        assert warning.weight == pytest.approx(0.5 * 1.0)
        assert info.weight == pytest.approx(0.5 * 0.5)

    # PURPOSE: 未知の check_type がデフォルト座標にフォールバックすることを確認
    def test_unknown_check_type_defaults_to_scale(self):
        """未知の check_type は Scale (d=3) にフォールバック。"""
        issue = self._build_issue("unknown_type", "/x.py", "テスト", "warning")
        assert issue.coordinate == FEPCoordinate.SCALE
        assert issue.d_value == 3


class TestKalonSnapshot:
    """KalonSnapshot の quality_score 計算テスト。"""

    # PURPOSE: 完全な品質スコアが 1.0 に近いことを確認
    def test_perfect_quality_score(self):
        """issue=0, coverage=100%, ept_ratio=1.0 → quality_score ≈ 1.0。"""
        snapshot = KalonSnapshot(
            coverage=100.0,
            ept_score=10,
            ept_total=10,
            ept_ratio=1.0,
            weighted_issue_count=0,
            total_stiffness=0.0,
            top_stiff_issues=[],
        )
        # 0.4*1.0 + 0.4*1.0 + 0.2*(1/(1+0)) = 0.4 + 0.4 + 0.2 = 1.0
        assert snapshot.quality_score == pytest.approx(1.0)

    # PURPOSE: 最悪の品質スコアのテスト
    def test_worst_quality_score(self):
        """coverage=0, ept_ratio=0, 大量の stiffness。"""
        snapshot = KalonSnapshot(
            coverage=0.0,
            ept_score=0,
            ept_total=10,
            ept_ratio=0.0,
            weighted_issue_count=100,
            total_stiffness=100.0,
            top_stiff_issues=[],
        )
        # 0.4*0 + 0.4*0 + 0.2*(1/(1+100/20)) = 0.2 * (1/6) ≈ 0.033
        expected = 0.2 * (1.0 / (1.0 + 100.0 / 20.0))
        assert snapshot.quality_score == pytest.approx(expected, abs=0.001)

    # PURPOSE: 品質スコアが 0-1 範囲内であることを確認
    def test_quality_score_range(self):
        """quality_score は (0, 1] の範囲内。"""
        for cov, ept_r, stiff in [
            (50, 0.5, 5.0),
            (0, 0, 0),
            (100, 1.0, 0),
            (80, 0.3, 20.0),
        ]:
            s = KalonSnapshot(
                coverage=cov,
                ept_score=int(ept_r * 10),
                ept_total=10,
                ept_ratio=ept_r,
                weighted_issue_count=10,
                total_stiffness=stiff,
                top_stiff_issues=[],
            )
            assert 0.0 <= s.quality_score <= 1.0, (
                f"quality_score={s.quality_score} が範囲外 (cov={cov}, ept={ept_r}, stiff={stiff})"
            )


class TestWeightIssuesIntegration:
    """weight_issues + make_snapshot の結合テスト (tmp_path ベース)。"""

    # PURPOSE: テスト用プロジェクトディレクトリを生成する fixture
    @pytest.fixture
    def tmp_project(self, tmp_path):
        """テスト用ファイルを作成するファクトリ。"""
        def _create(files: dict) -> Path:
            for name, content in files.items():
                fp = tmp_path / name
                fp.parent.mkdir(parents=True, exist_ok=True)
                fp.write_text(content, encoding="utf-8")
            return tmp_path
        return _create

    # PURPOSE: PROOF 欠落ファイルが issue として検出されることを確認
    def test_missing_proof_generates_issues(self, tmp_project):
        """PROOF ヘッダーなしのファイルは L1_missing issue を生成する。"""
        root = tmp_project({
            "example.py": "def foo(): pass\n",
        })
        checker = DendronChecker(
            check_dirs=False, check_files=True, check_functions=False,
            exempt_patterns=[],  # テスト用: exempt を無効化
        )
        result = checker.check(root)
        issues = weight_issues(result)

        # PROOF なしのファイルが file_proofs に MISSING として記録されているか
        missing_proofs = [fp for fp in result.file_proofs if fp.status == ProofStatus.MISSING]
        assert len(missing_proofs) >= 1, f"file_proofs: {[(str(fp.path), fp.status) for fp in result.file_proofs]}"

        # weight_issues でも issue として抽出されるか
        assert len(issues) >= 1, f"issues: {[(i.check_type, i.detail) for i in issues]}"

    # PURPOSE: PROOF ありファイルが issue 0 になることを確認
    def test_proper_file_no_issues(self, tmp_project):
        """PROOF ヘッダーありのファイルは L1 issue を生成しない。"""
        root = tmp_project({
            "good.py": '# PROOF: [L2/テスト] <- test\ndef foo(): pass\n',
        })
        checker = DendronChecker(check_dirs=False, check_files=True, check_functions=False)
        result = checker.check(root)
        issues = weight_issues(result)

        l1_issues = [i for i in issues if i.check_type.startswith("L1_")]
        assert len(l1_issues) == 0

    # PURPOSE: make_snapshot が正しく計算されることを確認
    def test_make_snapshot_consistency(self, tmp_project):
        """make_snapshot と weight_issues の整合性。"""
        root = tmp_project({
            "test.py": "x = 1\n",
        })
        checker = DendronChecker(check_dirs=False, check_files=True, check_functions=False)
        result = checker.check(root)
        issues = weight_issues(result)
        snapshot = make_snapshot(result, issues)

        assert snapshot.weighted_issue_count == len(issues)
        assert snapshot.coverage == result.coverage


# ═══════════════════════════════════════════════════════
# Layer 2: 収束判定エンジン
# ═══════════════════════════════════════════════════════


class TestBayesianHelpers:
    """Bayesian Beta ヘルパー関数のテスト。"""

    # PURPOSE: _regularized_incomplete_beta の境界値テスト
    def test_rib_boundary_values(self):
        """I(0; a, b) = 0, I(1; a, b) = 1。"""
        assert _regularized_incomplete_beta(0.0, 2, 3) == 0.0
        assert _regularized_incomplete_beta(1.0, 2, 3) == 1.0

    # PURPOSE: I(0.5; 1, 1) = 0.5 (一様事前分布の場合)
    def test_rib_uniform_prior(self):
        """I(0.5; 1, 1) = 0.5 (一様事前分布)。"""
        result = _regularized_incomplete_beta(0.5, 1, 1)
        assert result == pytest.approx(0.5, abs=0.001)

    # PURPOSE: I(0.5; 5, 2) の数値検証 (α >> β の場合)
    def test_rib_skewed(self):
        """α >> β のとき P(θ > 0.5) は高い → I(0.5; α, β) は小さい。"""
        result = _regularized_incomplete_beta(0.5, 5, 2)
        # α=5, β=2 は改善優勢 → I(0.5) は小さい (ほとんどの密度が 0.5 より上)
        assert result < 0.3

    # PURPOSE: _log_binomial の検算
    def test_log_binomial(self):
        """C(5, 2) = 10 → log(10) ≈ 2.302。"""
        import math
        result = _log_binomial(5, 2)
        assert result == pytest.approx(math.log(10), abs=0.001)


class TestKalonHistory:
    """KalonHistory の永続化と収束判定テスト。"""

    # PURPOSE: save → load のラウンドトリップテスト
    def test_save_and_load(self, tmp_path):
        """save した履歴を load で正しく読み戻せる。"""
        history = KalonHistory(history_dir=tmp_path)
        target = Path("/test/project")

        history.save(
            target=target,
            quality_score=0.75,
            coverage=80.0,
            ept_score=5,
            ept_total=10,
            ept_ratio=0.5,
            weighted_issue_count=3,
            total_stiffness=2.5,
            top_stiff_issues=["issue1", "issue2"],
            timestamp="2026-01-01T00:00:00Z",
        )

        entries = history.load(target)
        assert len(entries) == 1
        assert entries[0].quality_score == 0.75
        assert entries[0].coverage == 80.0
        assert entries[0].ept_score == 5

    # PURPOSE: 複数回の save が追記されることを確認
    def test_multiple_saves_append(self, tmp_path):
        """save は JSONL として追記される。"""
        history = KalonHistory(history_dir=tmp_path)
        target = Path("/test/project")

        for i in range(3):
            history.save(
                target=target,
                quality_score=0.5 + i * 0.1,
                coverage=70.0 + i * 5,
                ept_score=5 + i,
                ept_total=10,
                ept_ratio=(5 + i) / 10,
                weighted_issue_count=10 - i,
                total_stiffness=5.0 - i,
                top_stiff_issues=[],
                timestamp=f"2026-01-0{i+1}T00:00:00Z",
            )

        entries = history.load(target)
        assert len(entries) == 3
        assert entries[0].quality_score == pytest.approx(0.5)
        assert entries[2].quality_score == pytest.approx(0.7)

    # PURPOSE: 履歴なしの judge_convergence が ◯ を返すことを確認
    def test_judge_no_history(self, tmp_path):
        """履歴なし → ◯ (データ不足)。"""
        history = KalonHistory(history_dir=tmp_path)
        target = Path("/nonexistent")

        judgment = history.judge_convergence(target)
        assert judgment.verdict == "◯"
        assert judgment.trend == "insufficient_data"

    # PURPOSE: 1件のみの履歴でも ◯ を返すことを確認
    def test_judge_single_entry(self, tmp_path):
        """1件のみ → ◯ (データ不足)。"""
        history = KalonHistory(history_dir=tmp_path)
        target = Path("/test/single")
        history.save(
            target=target, quality_score=0.5,
            coverage=50.0, ept_score=5, ept_total=10,
            ept_ratio=0.5, weighted_issue_count=5,
            total_stiffness=3.0, top_stiff_issues=[],
        )
        judgment = history.judge_convergence(target)
        assert judgment.verdict == "◯"
        assert judgment.history_length == 1

    # PURPOSE: 連続改善で ◎ に収束することを確認
    def test_judge_convergence_improving(self, tmp_path):
        """連続改善 → ◎ (収束)。"""
        history = KalonHistory(history_dir=tmp_path)
        target = Path("/test/improving")

        # 品質スコアが単調増加する履歴を生成
        for i in range(5):
            history.save(
                target=target,
                quality_score=0.3 + i * 0.15,  # 0.3, 0.45, 0.6, 0.75, 0.9
                coverage=50.0 + i * 10,
                ept_score=3 + i,
                ept_total=10,
                ept_ratio=(3 + i) / 10,
                weighted_issue_count=10 - i * 2,
                total_stiffness=10.0 - i * 2,
                top_stiff_issues=[],
                timestamp=f"2026-01-0{i+1}T00:00:00Z",
            )

        judgment = history.judge_convergence(target)
        assert judgment.verdict == "◎"
        assert judgment.convergence_probability > 0.95
        assert judgment.trend == "improving"

    # PURPOSE: 連続悪化で ✗ になることを確認
    def test_judge_convergence_degrading(self, tmp_path):
        """連続悪化 → ✗ (悪化)。"""
        history = KalonHistory(history_dir=tmp_path)
        target = Path("/test/degrading")

        for i in range(5):
            history.save(
                target=target,
                quality_score=0.9 - i * 0.15,  # 0.9, 0.75, 0.6, 0.45, 0.3
                coverage=90.0 - i * 10,
                ept_score=9 - i,
                ept_total=10,
                ept_ratio=(9 - i) / 10,
                weighted_issue_count=2 + i * 2,
                total_stiffness=1.0 + i * 2,
                top_stiff_issues=[],
                timestamp=f"2026-01-0{i+1}T00:00:00Z",
            )

        judgment = history.judge_convergence(target)
        assert judgment.verdict == "✗"
        assert judgment.convergence_probability < 0.5
        assert judgment.trend == "degrading"

    # PURPOSE: 安定（変化なし）の場合のテスト
    def test_judge_stable(self, tmp_path):
        """安定 (品質スコア変化なし) → ◯ (stable)。"""
        history = KalonHistory(history_dir=tmp_path)
        target = Path("/test/stable")

        for i in range(4):
            history.save(
                target=target,
                quality_score=0.75,  # 全て同じ
                coverage=80.0,
                ept_score=7,
                ept_total=10,
                ept_ratio=0.7,
                weighted_issue_count=3,
                total_stiffness=2.0,
                top_stiff_issues=[],
                timestamp=f"2026-01-0{i+1}T00:00:00Z",
            )

        judgment = history.judge_convergence(target)
        # 変化なし → success も failure もない → α=1, β=1 → P(θ>0.5)=0.5 → ◯
        assert judgment.verdict == "◯"
        assert judgment.trend == "stable"


class TestKalonJudgmentFormat:
    """format_report のテスト。"""

    # PURPOSE: format_report が文字列を返すことを確認
    def test_format_report_returns_string(self):
        """format_report は文字列を返す。"""
        judgment = KalonJudgment(
            verdict="◎",
            alpha=5,
            beta=2,
            convergence_probability=0.96,
            history_length=6,
            trend="improving",
            quality_scores=[0.3, 0.45, 0.6, 0.75, 0.85, 0.9],
            latest_score=0.9,
        )
        report = KalonHistory.format_report(judgment)
        assert isinstance(report, str)
        assert "◎" in report
        assert "0.96" in report

    # PURPOSE: 全判定の表示テスト
    def test_format_all_verdicts(self):
        """◎, ◯, ✗ 全ての判定が正しくフォーマットされる。"""
        for verdict, expected_text in [
            ("◎", "Fix(G∘F)"),
            ("◯", "改善傾向"),
            ("✗", "悪化傾向"),
        ]:
            j = KalonJudgment(
                verdict=verdict, alpha=1, beta=1,
                convergence_probability=0.5, history_length=1,
                trend="stable", quality_scores=[0.5], latest_score=0.5,
            )
            report = KalonHistory.format_report(j)
            assert expected_text in report, f"verdict={verdict} に '{expected_text}' がない"
