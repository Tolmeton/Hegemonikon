from __future__ import annotations
#!/usr/bin/env python3
# PROOF: mekhane/scripts/ci_quality_check.py
# PURPOSE: scripts モジュールの ci_quality_check
"""PURPOSE: CI 品質チェック統合スクリプト — 閾値設定+トレンド比較+品質ゲート

.dendron.yml から閾値を読み、dendron コマンドを集約実行し、
前回 vs 今回のスコア差分 (Δ) を計算して品質ゲート判定を行う。
GitHub Actions の Job Summary にも対応。

使用例:
    python ci_quality_check.py                    # カレントディレクトリ
    python ci_quality_check.py /path/to/project   # 指定ディレクトリ
    python ci_quality_check.py --summary           # GitHub Job Summary 出力
    python ci_quality_check.py --trend             # トレンド比較を表示
"""


import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─── 設定読み込み ──────────────────────────────

# PURPOSE: .dendron.yml のデフォルト値を定義する
_DEFAULTS = {
    "kalon": {
        "quality_score_min": 0.90,
        "quality_score_target": 0.95,
        "max_stiffness": 5.0,
        "max_issues": 20,
        "regression_tolerance": 0.02,
        "convergence_required": False,
    },
    "purpose": {
        "missing_allowed": 0,
        "strict": False,
    },
    "check": {
        "min_coverage": 80.0,
    },
}


# PURPOSE: .dendron.yml から閾値設定を読み込む
def load_config(project_root: Path) -> dict:
    """プロジェクトルートから .dendron.yml を読み込む。
    未設定項目はデフォルト値で補完する。
    """
    config_path = project_root / ".dendron.yml"
    result = {}

    # デフォルトでフラット化
    for section, defaults in _DEFAULTS.items():
        for key, value in defaults.items():
            result[f"{section}.{key}"] = value

    if config_path.exists():
        try:
            import yaml
            with open(config_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f) or {}
            for section, defaults in _DEFAULTS.items():
                section_data = raw.get(section, {})
                if isinstance(section_data, dict):
                    for key in defaults:
                        if key in section_data:
                            result[f"{section}.{key}"] = section_data[key]
        except ImportError:
            # PyYAML がない場合はデフォルトのみ
            print("⚠️ PyYAML 未インストール: .dendron.yml を無視しデフォルト値を使用", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ .dendron.yml 読込エラー: {e} — デフォルト値を使用", file=sys.stderr)

    return result


# ─── データクラス ──────────────────────────────

# PURPOSE: 個別チェック結果を保持する
@dataclass
class CheckResult:
    """1 つの dendron チェック結果"""
    name: str
    command: list[str]
    exit_code: int = -1
    stdout: str = ""
    stderr: str = ""

    @property
    def passed(self) -> bool:
        """チェック成功か"""
        return self.exit_code == 0

    @property
    def icon(self) -> str:
        """結果アイコン"""
        if self.exit_code == -1:
            return "⏭️"
        return "✅" if self.passed else "❌"


# PURPOSE: 品質ゲートの判定レベル
class GateLevel:
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


# PURPOSE: 品質ゲートの個別判定を保持する
@dataclass
class GateCheck:
    """1 つの品質ゲート判定"""
    name: str
    value: float
    threshold: float
    level: str  # GateLevel
    detail: str = ""

    @property
    def icon(self) -> str:
        """判定アイコン"""
        return {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}[self.level]


# PURPOSE: 品質トレンド (前回比) を保持する
@dataclass
class QualityTrend:
    """前回 vs 今回の品質差分"""
    previous_score: Optional[float] = None
    current_score: Optional[float] = None
    delta: Optional[float] = None
    regression: bool = False
    history_length: int = 0

    @property
    def delta_str(self) -> str:
        """Δ の表示文字列"""
        if self.delta is None:
            return "N/A (初回)"
        sign = "+" if self.delta >= 0 else ""
        icon = "✅" if self.delta >= 0 else "❌"
        return f"Δ = {sign}{self.delta:.3f} {icon}"


# PURPOSE: 全チェック結果と品質ゲートを集約する
@dataclass
class QualityReport:
    """集約レポート"""
    results: list[CheckResult] = field(default_factory=list)
    gates: list[GateCheck] = field(default_factory=list)
    trend: Optional[QualityTrend] = None

    @property
    def all_passed(self) -> bool:
        """全チェックと全ゲートが PASS か"""
        checks_ok = all(r.passed for r in self.results if r.exit_code != -1)
        gates_ok = all(g.level != GateLevel.FAIL for g in self.gates)
        trend_ok = not (self.trend and self.trend.regression)
        return checks_ok and gates_ok and trend_ok

    @property
    def total(self) -> int:
        """実行されたチェック数"""
        return sum(1 for r in self.results if r.exit_code != -1)

    @property
    def passed_count(self) -> int:
        """成功したチェック数"""
        return sum(1 for r in self.results if r.passed)


# ─── 実行エンジン ──────────────────────────────

# PURPOSE: 単一の dendron コマンドを実行する
def _run_check(name: str, cmd: list[str], cwd: Path) -> CheckResult:
    """dendron コマンドを実行"""
    result = CheckResult(name=name, command=cmd)
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd),
            capture_output=True, text=True, timeout=120,
        )
        result.exit_code = proc.returncode
        result.stdout = proc.stdout
        result.stderr = proc.stderr
    except subprocess.TimeoutExpired:
        result.exit_code = 124
        result.stderr = "Timeout (120s)"
    except FileNotFoundError:
        result.exit_code = 127
        result.stderr = "Command not found"
    return result


# PURPOSE: Kalon 履歴からトレンドを計算する
def _compute_trend(target: Path, config: dict) -> QualityTrend:
    """Kalon 履歴 JSONL から前回比を計算する"""
    # kalon_convergence の履歴を直接読む
    try:
        from mekhane.dendron.kalon_convergence import KalonHistory
        history = KalonHistory()
        entries = history.load(target)

        if len(entries) < 2:
            return QualityTrend(
                current_score=entries[-1].quality_score if entries else None,
                history_length=len(entries),
            )

        prev = entries[-2].quality_score
        curr = entries[-1].quality_score
        delta = curr - prev
        tolerance = config.get("kalon.regression_tolerance", 0.02)

        return QualityTrend(
            previous_score=prev,
            current_score=curr,
            delta=delta,
            regression=delta < -tolerance,
            history_length=len(entries),
        )
    except Exception:  # noqa: BLE001
        return QualityTrend()


# PURPOSE: 品質ゲート判定を実行する
def _evaluate_gates(target: Path, config: dict) -> list[GateCheck]:
    """kalon snapshot を取得し、.dendron.yml の閾値で判定する"""
    gates: list[GateCheck] = []

    try:
        from mekhane.dendron.checker import DendronChecker
        from mekhane.dendron.kalon_weight import weight_issues, make_snapshot

        checker = DendronChecker(
            check_dirs=True, check_files=True, check_functions=True,
            check_structure=True, check_function_nf=True, check_verification=True,
        )
        result = checker.check(target)
        issues = weight_issues(result)
        snapshot = make_snapshot(result, issues)

        # 品質スコア最低値
        min_score = config.get("kalon.quality_score_min", 0.90)
        gates.append(GateCheck(
            name="品質スコア",
            value=snapshot.quality_score,
            threshold=min_score,
            level=GateLevel.PASS if snapshot.quality_score >= min_score else GateLevel.FAIL,
            detail=f"{snapshot.quality_score:.3f} >= {min_score}",
        ))

        # 品質スコア目標値
        target_score = config.get("kalon.quality_score_target", 0.95)
        gates.append(GateCheck(
            name="品質目標",
            value=snapshot.quality_score,
            threshold=target_score,
            level=GateLevel.PASS if snapshot.quality_score >= target_score else GateLevel.WARN,
            detail=f"{snapshot.quality_score:.3f} vs {target_score} (目標)",
        ))

        # Stiffness 上限
        max_stiff = config.get("kalon.max_stiffness", 5.0)
        gates.append(GateCheck(
            name="Stiffness",
            value=snapshot.total_stiffness,
            threshold=max_stiff,
            level=GateLevel.PASS if snapshot.total_stiffness <= max_stiff else GateLevel.FAIL,
            detail=f"{snapshot.total_stiffness:.2f} <= {max_stiff}",
        ))

        # Issue 数上限
        max_issues = config.get("kalon.max_issues", 20)
        gates.append(GateCheck(
            name="Issue 数",
            value=float(snapshot.weighted_issue_count),
            threshold=float(max_issues),
            level=GateLevel.PASS if snapshot.weighted_issue_count <= max_issues else GateLevel.FAIL,
            detail=f"{snapshot.weighted_issue_count} <= {max_issues}",
        ))

        # カバレッジ
        min_cov = config.get("check.min_coverage", 80.0)
        gates.append(GateCheck(
            name="カバレッジ",
            value=snapshot.coverage,
            threshold=min_cov,
            level=GateLevel.PASS if snapshot.coverage >= min_cov else GateLevel.FAIL,
            detail=f"{snapshot.coverage:.1f}% >= {min_cov}%",
        ))

    except Exception as e:  # noqa: BLE001
        gates.append(GateCheck(
            name="ゲート評価",
            value=0.0,
            threshold=0.0,
            level=GateLevel.FAIL,
            detail=f"エラー: {e}",
        ))

    return gates


# PURPOSE: 全チェックを順次実行し集約レポートを生成する
def run_all_checks(target: Path, config: dict, show_trend: bool = True) -> QualityReport:
    """全品質チェックを実行"""
    py = sys.executable
    report = QualityReport()

    # dendron コマンド実行
    checks = [
        ("pytest", [py, "-m", "pytest", "-x", "-q", "--tb=short"]),
        ("dendron check", [py, "-m", "mekhane.dendron.cli", "check", "--ci", str(target)]),
        ("dendron purpose", [py, "-m", "mekhane.dendron.cli", "purpose", "--ci", str(target)]),
        ("dendron kalon", [py, "-m", "mekhane.dendron.cli", "kalon", "--ci", "--save", "--judge", str(target)]),
    ]

    for name, cmd in checks:
        print(f"{'─' * 40}")
        print(f"▶ {name}")
        result = _run_check(name, cmd, target)
        report.results.append(result)

        if result.stdout.strip():
            for line in result.stdout.strip().splitlines()[:10]:
                print(f"  {line}")
        print(f"  → {result.icon} exit {result.exit_code}")
        print()

    # 品質ゲート判定
    print(f"{'─' * 40}")
    print("▶ 品質ゲート判定")
    report.gates = _evaluate_gates(target, config)
    for g in report.gates:
        print(f"  {g.icon} {g.name}: {g.detail}")
    print()

    # トレンド比較
    if show_trend:
        print(f"{'─' * 40}")
        print("▶ トレンド比較")
        report.trend = _compute_trend(target, config)
        print(f"  {report.trend.delta_str}")
        if report.trend.history_length > 0:
            print(f"  履歴: {report.trend.history_length} 回")
        if report.trend.regression:
            print(f"  ❌ 品質回帰検出 (許容幅: {config.get('kalon.regression_tolerance', 0.02)})")
        print()

    return report


# PURPOSE: 集約レポートをコンソールに出力する
def print_report(report: QualityReport) -> None:
    """集約レポート出力"""
    print("=" * 40)
    print("Dendron Quality Report")
    print("=" * 40)

    # コマンド結果
    print("\n📋 チェック結果:")
    for r in report.results:
        print(f"  {r.icon} {r.name}")

    # 品質ゲート
    if report.gates:
        print("\n🚦 品質ゲート:")
        for g in report.gates:
            print(f"  {g.icon} {g.name}: {g.detail}")

    # トレンド
    if report.trend:
        print(f"\n📈 トレンド: {report.trend.delta_str}")

    # 最終判定
    print()
    if report.all_passed:
        print("✅ ALL CHECKS PASSED")
    else:
        failed = [r.name for r in report.results if not r.passed and r.exit_code != -1]
        failed_gates = [g.name for g in report.gates if g.level == GateLevel.FAIL]
        issues = failed + failed_gates
        if report.trend and report.trend.regression:
            issues.append("品質回帰")
        print(f"❌ FAILED: {', '.join(issues)}")


# PURPOSE: GitHub Actions Job Summary に書き出す
def write_github_summary(report: QualityReport) -> None:
    """GitHub Actions の $GITHUB_STEP_SUMMARY にマークダウンテーブルを出力"""
    import os
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    lines = [
        "## Dendron Quality Report",
        "",
        "### チェック結果",
        "| Check | Result |",
        "|---|---|",
    ]
    for r in report.results:
        lines.append(f"| {r.name} | {r.icon} exit {r.exit_code} |")

    if report.gates:
        lines.extend([
            "",
            "### 品質ゲート",
            "| Gate | Value | Threshold | Result |",
            "|---|---|---|---|",
        ])
        for g in report.gates:
            lines.append(f"| {g.name} | {g.value:.3f} | {g.threshold:.3f} | {g.icon} {g.level} |")

    if report.trend:
        lines.extend(["", f"### トレンド: {report.trend.delta_str}"])

    lines.append("")
    status = "✅ **ALL PASSED**" if report.all_passed else "❌ **FAILED**"
    lines.append(f"**Overall**: {status}")

    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# PURPOSE: PR コメント用 JSON を生成する
def generate_pr_comment(report: QualityReport) -> str:
    """PR コメント用のマークダウンテキストを返す"""
    lines = ["## 🔍 Dendron Quality Report", ""]

    # ゲート結果テーブル
    if report.gates:
        lines.extend([
            "| Gate | Value | Status |",
            "|---|---|---|",
        ])
        for g in report.gates:
            lines.append(f"| {g.name} | {g.detail} | {g.icon} |")
        lines.append("")

    # トレンド
    if report.trend and report.trend.delta is not None:
        lines.append(f"**トレンド**: {report.trend.delta_str}")
        lines.append("")

    # サマリ
    if report.all_passed:
        lines.append("✅ 品質ゲート通過")
    else:
        lines.append("❌ 品質ゲート不通過 — 修正が必要です")

    return "\n".join(lines)


# PURPOSE: CLI エントリポイント
def main() -> int:
    """メインエントリポイント

    全フラグは同時指定可能。run_all_checks は常に 1 回だけ実行される。
    例: --summary --trend --pr-comment を同時指定 → チェック 1 回 + 3 種出力
    """
    # 引数解析
    args = sys.argv[1:]
    positional = [a for a in args if not a.startswith("-")]
    target = Path(positional[0]).resolve() if positional else Path.cwd()
    show_summary = "--summary" in args
    show_trend = "--trend" in args or show_summary
    show_pr_comment = "--pr-comment" in args

    if not target.exists():
        print(f"Error: {target} が存在しません", file=sys.stderr)
        return 1

    # 設定読み込み
    config = load_config(target)

    # チェック実行 (常に 1 回のみ — Elenchos #1 修正)
    report = run_all_checks(target, config, show_trend=show_trend)
    print_report(report)

    # GitHub Summary
    if show_summary:
        write_github_summary(report)

    # PR コメント生成 (既存の report を再利用 — 2 回目のチェック不要)
    if show_pr_comment:
        comment = generate_pr_comment(report)
        comment_path = target / ".dendron" / "pr_comment.md"
        comment_path.parent.mkdir(parents=True, exist_ok=True)
        comment_path.write_text(comment, encoding="utf-8")
        print(f"\n📝 PR コメント: {comment_path}")

    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
