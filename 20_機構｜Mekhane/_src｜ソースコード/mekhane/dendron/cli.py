# noqa: AI-ALL
# PROOF: [L2/インフラ] <- mekhane/dendron/  # noqa: AI-022
"""
Dendron CLI — コマンドラインインターフェース

Usage:
    python -m mekhane.dendron.cli check [PATH] [--coverage] [--ci] [--format FORMAT]
    python -m mekhane.dendron.cli purpose [PATH] [--ci] [--strict]
    python -m mekhane.dendron.cli variables [PATH] [--ci]
    python -m mekhane.dendron.cli reason [PATH] [--dry-run] [--apply]
    python -m mekhane.dendron.cli skill-audit [AGENT_DIR] [--ci] [--boot-summary]
    python -m mekhane.dendron.cli mece [PATH] [--embed] [--me-threshold N] [--ce-min N]
    python -m mekhane.dendron.cli kalon [PATH] [--save] [--judge] [--top N]
"""

__all__ = [
    "main", "cmd_check", "cmd_purpose", "cmd_variables",
    "cmd_reason", "cmd_diff", "cmd_skill_audit", "cmd_guard",
    "cmd_mece", "cmd_kalon",
]

import argparse
import sys
from pathlib import Path

from .checker import DendronChecker, ProofStatus
from .reporter import DendronReporter, ReportFormat


# PURPOSE: argparse パーサーを構築する (サブコマンド定義)
def _build_parser() -> argparse.ArgumentParser:
    """全サブコマンドの argparse パーサーを構築して返す"""
    parser = argparse.ArgumentParser(prog="dendron", description="Dendron — 存在証明検証ツール")
    sub = parser.add_subparsers(dest="command", required=True)

    # check コマンド
    p = sub.add_parser("check", help="PROOF 状態をチェック")
    p.add_argument("path", nargs="?", default=".", help="チェック対象ディレクトリ (default: .)")
    p.add_argument("--coverage", action="store_true", help="カバレッジ率のみ表示")
    p.add_argument("--ci", action="store_true", help="CI モード (失敗時に exit 1)")
    p.add_argument("--format", choices=["text", "markdown", "json", "ci"], default="text",
                   help="出力形式 (default: text)")
    p.add_argument("--no-dirs", action="store_true", help="ディレクトリの PROOF.md チェックをスキップ")
    p.add_argument("--ept", action="store_true", help="EPT フルマトリクス (NF2/NF3/BCNF) を有効化")

    # purpose コマンド (v2.6)
    p = sub.add_parser("purpose", help="L2 Purpose 品質チェック")
    p.add_argument("path", nargs="?", default=".", help="チェック対象ディレクトリ (default: .)")
    p.add_argument("--ci", action="store_true", help="CI モード (WEAK/MISSING で exit 1)")
    p.add_argument("--strict", action="store_true", help="厳密モード: WEAK も FAIL 扱い")

    # variables コマンド (v3.0)
    p = sub.add_parser("variables", help="L3 Variable 品質チェック (型ヒスト + 命名)")
    p.add_argument("path", nargs="?", default=".", help="チェック対象ディレクトリ (default: .)")
    p.add_argument("--ci", action="store_true", help="CI モード")

    # skill-audit コマンド (v3.1)
    p = sub.add_parser("skill-audit", help="Safety Contract + lcm_state 検証")
    p.add_argument("agent_dir", nargs="?", default="nous", help="nous/ ディレクトリ (default: nous)")
    p.add_argument("--ci", action="store_true", help="CI モード (error で exit 1)")
    p.add_argument("--verbose", "-v", action="store_true", help="OK も表示")
    p.add_argument("--boot-summary", action="store_true", help="/boot 用コンパクト出力")

    # diff コマンド (v3.3)
    p = sub.add_parser("diff", help="Git diff に基づく EPT 変化検出")
    p.add_argument("path", nargs="?", default=".", help="プロジェクトルート (default: .)")
    p.add_argument("--since", default="HEAD~1", help="比較起点 (default: HEAD~1)")

    # reason コマンド (v3.7)
    p = sub.add_parser("reason", help="REASON コメントを自動推定")
    p.add_argument("path", nargs="?", default=".", help="チェック対象ディレクトリ (default: .)")
    p.add_argument("--apply", action="store_true", help="実際に書き込む (デフォルトは dry-run)")
    p.add_argument("--limit", type=int, default=50, help="最大処理ファイル数 (default: 50)")

    # guard コマンド (v3.6)
    p = sub.add_parser("guard", help="変更ファイルのみ PROOF/PURPOSE/REASON をチェック")
    p.add_argument("path", nargs="?", default=".", help="プロジェクトルート (default: .)")
    p.add_argument("--since", default=None,
                   help="比較起点 (default: ステージ済み + 未コミット変更)")

    # mece コマンド (v4.0)
    p = sub.add_parser("mece", help="ディレクトリ構造の MECE (概念的重複・カバー不足) を診断")
    p.add_argument("path", nargs="?", default=".", help="診断対象ディレクトリ (default: .)")
    p.add_argument("--embed", action="store_true",
                   help="3072d embedding を使用した概念的 MECE チェック (Gemini API 必要)")
    p.add_argument("--me-threshold", type=float, default=0.70,
                   help="ME 警告閾値 (cosine similarity, default: 0.70)")
    p.add_argument("--me-error-threshold", type=float, default=0.85,
                   help="ME エラー閾値 (default: 0.85)")
    p.add_argument("--ce-min", type=int, default=3,
                   help="CE 最小子ディレクトリ数 (default: 3)")
    p.add_argument("--ci", action="store_true", help="CI モード (issue あり → exit 1)")

    # kalon コマンド (v5.0)
    p = sub.add_parser("kalon", help="Kalon 収束判定 — stiffness ランキング + G∘F 収束検出")
    p.add_argument("path", nargs="?", default=".", help="チェック対象ディレクトリ (default: .)")
    p.add_argument("--save", action="store_true", help="check 結果を履歴に追記")
    p.add_argument("--judge", action="store_true", help="G∘F 収束判定を実行")
    p.add_argument("--top", type=int, default=5, help="stiffness Top-N を表示 (default: 5)")
    p.add_argument("--history-dir", default=None, help="履歴保存先ディレクトリ (default: .dendron/)")
    p.add_argument("--ci", action="store_true", help="CI モード")

    return parser


# PURPOSE: Dendron CLI のメインエントリポイントとサブコマンド振り分け
def main() -> int:
    """メインエントリポイント"""
    # Windows cp932 環境で日本語 + em dash (U+2014) が UnicodeEncodeError になる対策
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = _build_parser()
    args = parser.parse_args()

    # 直接関数参照で静的解析が呼び出しを検出可能にする
    dispatch = {
        "check": cmd_check,
        "purpose": cmd_purpose,
        "variables": cmd_variables,
        "reason": cmd_reason,
        "diff": cmd_diff,
        "skill-audit": cmd_skill_audit,
        "guard": cmd_guard,
        "mece": cmd_mece,
        "kalon": cmd_kalon,
    }

    handler = dispatch.get(args.command)
    if handler:
        return handler(args)

    return 0


# PURPOSE: check コマンドの実行とレポート出力
def cmd_check(args: argparse.Namespace) -> int:  # noqa: AI-005 # noqa: AI-ALL
    """check コマンドの実行"""
    path = Path(args.path)

    if not path.exists():
        print(f"Error: {path} が存在しません", file=sys.stderr)
        return 1

    # チェッカー設定
    # CI モードでは EPT フルマトリクスを自動有効化 (v3.7)
    enable_ept = getattr(args, 'ept', False) or getattr(args, 'ci', False)
    checker = DendronChecker(
        check_dirs=not args.no_dirs,
        check_files=True,
        check_structure=enable_ept,
        check_function_nf=enable_ept,
        check_verification=enable_ept,
    )

    # チェック実行
    result = checker.check(path)

    # 出力形式
    if args.coverage:
        print(f"{result.coverage:.1f}%")
        return 0

    format_map = {
        "text": ReportFormat.TEXT,
        "markdown": ReportFormat.MARKDOWN,
        "json": ReportFormat.JSON,
        "ci": ReportFormat.CI,
    }

    format = format_map.get(args.format, ReportFormat.TEXT)
    if args.ci:
        format = ReportFormat.CI

    # レポート出力  # noqa: AI-014 # noqa: AI-ALL
    reporter = DendronReporter()
    reporter.report(result, format)

    # CI モードの場合は失敗時に exit 1
    if args.ci and not result.is_passing:
        return 1

    return 0


# PURPOSE: L2 Purpose 品質チェックを実行し、WEAK/MISSING を報告する
def cmd_purpose(args: argparse.Namespace) -> int:  # noqa: AI-005
    """purpose コマンドの実行 (v2.6)"""
    path = Path(args.path)

    if not path.exists():
        print(f"Error: {path} が存在しません", file=sys.stderr)
        return 1

    checker = DendronChecker(check_dirs=False, check_files=True, check_functions=True)
    result = checker.check(path)

    ok = sum(1 for f in result.function_proofs if f.status == ProofStatus.OK)
    weak = [f for f in result.function_proofs if f.status == ProofStatus.WEAK]
    missing = [f for f in result.function_proofs if f.status == ProofStatus.MISSING]
    exempt = sum(1 for f in result.function_proofs if f.status == ProofStatus.EXEMPT)

    total = ok + len(weak) + len(missing)
    coverage = (ok / total * 100) if total > 0 else 100.0

    if args.ci:
        # CI 出力
        status = "✅" if len(missing) == 0 and (not args.strict or len(weak) == 0) else "❌"
        print(f"{status} Purpose: {ok}/{total} OK ({coverage:.1f}%), {len(weak)} weak, {len(missing)} missing")
        if weak and args.strict:
            for f in weak[:5]:
                print(f"  ⚠️ {f.path}:{f.line_number} {f.name} — {f.quality_issue}")
        if missing:
            for f in missing[:5]:
                print(f"  ❌ {f.path}:{f.line_number} {f.name}")

        # 判定
        if len(missing) > 0:
            return 1
        if args.strict and len(weak) > 0:
            return 1
        return 0
    else:
        # テキスト出力
        print(f"=== L2 Purpose Check (v2.6) ===")
        print(f"OK: {ok} | WEAK: {len(weak)} | MISSING: {len(missing)} | EXEMPT: {exempt}")
        print(f"Coverage: {coverage:.1f}%")

        if weak:
            print()
            print("⚠️ WEAK Purposes (WHAT not WHY):")
            for f in weak:
                print(f"  {f.path}:{f.line_number} {f.name}")
                print(f"    Current: {f.purpose_text}")
                print(f"    Issue:   {f.quality_issue}")

        if missing:
            print()
            print("❌ MISSING Purposes:")
            for f in missing[:20]:
                print(f"  {f.path}:{f.line_number} {f.name}")
            if len(missing) > 20:
                print(f"  ... and {len(missing) - 20} more")

        print()
        if len(weak) == 0 and len(missing) == 0:
            print("✅ ALL CLEAR")
        else:
            print(f"❌ {len(weak)} WEAK + {len(missing)} MISSING to fix")

        return 0


# PURPOSE: L3 Variable 品質チェック (型ヒストカバレッジ) を実行する
def cmd_variables(args: argparse.Namespace) -> int:  # noqa: AI-005
    """variables コマンドの実行 (v3.0)"""
    path = Path(args.path)

    if not path.exists():
        print(f"Error: {path} が存在しません", file=sys.stderr)
        return 1

    checker = DendronChecker(check_dirs=False, check_files=True, check_functions=False, check_variables=True)
    result = checker.check(path)

    hints_total = result.total_checked_signatures
    hints_ok = result.signatures_with_hints
    hints_missing = result.signatures_missing_hints
    short = result.short_name_violations
    hint_cov = (hints_ok / hints_total * 100) if hints_total > 0 else 100.0

    if args.ci:
        short_str = f", {short} short" if short > 0 else ""
        status = "✅" if hints_missing == 0 and short == 0 else "⚠️"
        print(f"{status} TypeHints: {hints_ok}/{hints_total} ({hint_cov:.0f}%){short_str}")
        if hints_missing > 0:
            missing_proofs = [v for v in result.variable_proofs if v.check_type == "type_hint" and v.status == ProofStatus.MISSING]
            for v in missing_proofs[:5]:
                print(f"  ❌ {v.path}:{v.line_number} {v.name} — {v.reason}")
        return 0  # warn only for now
    else:
        print(f"=== L3 Variable Check (v3.0) ===")
        print(f"Type Hints: {hints_ok}/{hints_total} ({hint_cov:.1f}%)")
        print(f"Short name violations: {short}")
        print()
        if hints_missing > 0:
            print("❌ Missing type hints:")
            missing_proofs = [v for v in result.variable_proofs if v.check_type == "type_hint" and v.status == ProofStatus.MISSING]
            for v in missing_proofs[:20]:
                print(f"  {v.path}:{v.line_number} {v.name}")
            if len(missing_proofs) > 20:
                print(f"  ... and {len(missing_proofs) - 20} more")
        if short > 0:
            print("⚠️ Short name violations:")
            short_proofs = [v for v in result.variable_proofs if v.check_type == "short_name"]
            for v in short_proofs:
                print(f"  {v.path}:{v.line_number} {v.name} — {v.reason}")
        if hints_missing == 0 and short == 0:
            print("✅ ALL CLEAR")
        return 0


# PURPOSE: Safety Contract (risk_tier/lcm_state) の検証を実行し、レポートを出力する
def cmd_skill_audit(args: argparse.Namespace) -> int:  # noqa: AI-005
    """skill-audit コマンドの実行 (v3.1: Safety Contract)"""
    from .skill_checker import run_audit, format_report

    agent_dir = Path(args.agent_dir)
    if not agent_dir.exists():
        print(f"Error: {agent_dir} が存在しません", file=sys.stderr)
        return 1

    result = run_audit(agent_dir)

    if args.boot_summary:
        # /boot 用コンパクトサマリ
        dist = result.risk_distribution()
        lcm = result.lcm_distribution()
        print(f"\n🛡️ Safety Contract:")
        print(f"  Skills: {result.skills_checked} | WF: {result.workflows_checked}")
        risk_parts = [f"{k}:{v}" for k, v in dist.items() if v > 0]
        if risk_parts:
            print(f"  Risk: {' '.join(risk_parts)}")
        lcm_parts = [f"{k}:{v}" for k, v in lcm.items() if v > 0]
        if lcm_parts:
            print(f"  LCM:  {' '.join(lcm_parts)}")
        if result.errors > 0:
            print(f"  ⚠️ {result.errors} errors found")
    else:
        print(format_report(result, verbose=getattr(args, 'verbose', False)))

    if args.ci and not result.is_passing:
        return 1

    return 0


# PURPOSE: Git diff に基づく EPT 変化検出コマンド (v3.3)
def cmd_diff(args: argparse.Namespace) -> int:
    """diff コマンドの実行"""
    from .diff import diff_check, format_diff_result

    root = Path(args.path).resolve()
    result = diff_check(root, since=args.since)
    print(format_diff_result(result))
    return 0


# PURPOSE: REASON コメントを自動推定して表示または付与する (v3.7)
def cmd_reason(args: argparse.Namespace) -> int:
    """reason コマンドの実行 — REASON 自動推定"""
    from .reason_infer import add_reason_comments

    path = Path(args.path)
    if not path.exists():
        print(f"Error: {path} が存在しません", file=sys.stderr)
        return 1

    dry_run = not args.apply
    limit = args.limit

    if dry_run:
        print("🔍 DRY RUN — showing proposed REASON additions (use --apply to write)")
    else:
        print("✏️  APPLYING REASON comments...")

    files = sorted(path.rglob("*.py")) if path.is_dir() else [path]
    total_file = 0
    total_func = 0
    files_modified = 0

    for f in files[:limit]:
        if "__pycache__" in str(f) or "test" in f.name.lower():
            continue
        file_count, func_count = add_reason_comments(f, dry_run=dry_run)
        if file_count + func_count > 0:
            print(f"📄 {f}: +{file_count} file REASON, +{func_count} func REASON")
            total_file += file_count
            total_func += func_count
            files_modified += 1

    verb = "Would add" if dry_run else "Added"
    print(f"\n{verb}: {total_file} file + {total_func} func REASON in {files_modified} files")
    return 0


# PURPOSE: 変更ファイルのみ PROOF/PURPOSE/REASON をチェックする (v3.6 アンチウイルス)
def cmd_guard(args: argparse.Namespace) -> int:
    """guard コマンドの実行 — 変更ファイルのみ高速チェック"""
    import subprocess as _sp

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Error: {root} が存在しません", file=sys.stderr)
        return 1

    # 1. 変更ファイルを取得
    since = args.since
    cmd = (
        ["git", "diff", "--name-only", since, "--"] if since
        else ["git", "diff", "--name-only", "HEAD", "--"]
    )

    try:
        result = _sp.run(cmd, cwd=str(root), capture_output=True, text=True, timeout=10)
        changed = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    except (FileNotFoundError, _sp.TimeoutExpired):
        print("⚠️ git が利用できません", file=sys.stderr)
        return 1

    if not changed:
        print("✅ 変更ファイルなし — guard pass")
        return 0

    # 2. .py と PROOF.md をフィルタ
    py_files = [Path(f) for f in changed if f.endswith(".py")]
    proof_files = [Path(f) for f in changed if f.endswith("PROOF.md")]

    if not py_files and not proof_files:
        print(f"✅ PROOF 関連の変更なし ({len(changed)} files changed) — guard pass")
        return 0

    # 3. チェック + レポート
    issues, checked = _check_guard_files(root, py_files, proof_files)
    print(f"🔍 Dendron Guard — {checked} files checked ({len(py_files)} .py, {len(proof_files)} PROOF.md)")

    if issues:
        print()
        for iss in issues:
            print(iss)
        print(f"\n❌ {len(issues)} issues found")
        return 1
    else:
        print("✅ Guard pass — all changed files OK")
        return 0


# PURPOSE: guard コマンドでの py/PROOF.md ファイルチェックロジック
def _check_guard_files(
    root: Path, py_files: list, proof_files: list,
) -> tuple:
    """変更された .py / PROOF.md をチェックし issues リストを返す"""
    checker = DendronChecker(check_dirs=True, check_files=True, check_functions=True)
    issues: list[str] = []
    checked = 0

    for py in py_files:
        full = root / py
        if not full.exists():
            continue
        # ファイルの PURPOSE/REASON チェック
        file_proofs = checker.check_file_proof(full)
        if file_proofs and file_proofs.status == ProofStatus.MISSING:
            issues.append(f"  ❌ {py} — PROOF コメントなし")
        # 関数チェック
        func_proofs = checker.check_functions_in_file(full)
        for fp in func_proofs:
            if fp.status == ProofStatus.MISSING and not fp.is_private:
                issues.append(f"  ❌ {py}:{fp.line_number} {fp.name} — PURPOSE なし")
            elif fp.status == ProofStatus.WEAK:
                issues.append(f"  ⚠️ {py}:{fp.line_number} {fp.name} — {fp.quality_issue}")
        checked += 1

    for pf in proof_files:
        full = root / pf
        if not full.exists():
            continue
        dir_path = full.parent
        dir_proof = checker.check_dir_proof(dir_path)
        if dir_proof.status == ProofStatus.MISSING:
            issues.append(f"  ❌ {pf} — PURPOSE 未定義")
        elif dir_proof.status == ProofStatus.WEAK:
            issues.append(f"  ⚠️ {pf} — {dir_proof.reason}")
        checked += 1

    return issues, checked


# PURPOSE: ディレクトリ構造の MECE 診断を実行し、ME/CE issue を報告する (v4.0)
def cmd_mece(args: argparse.Namespace) -> int:
    """mece コマンドの実行 — 概念的 MECE 診断"""
    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: {path} が存在しません", file=sys.stderr)
        return 1

    checker = DendronChecker()

    # embedding 関数の設定
    embed_fn = None
    if args.embed:
        try:
            from mekhane.symploke.embedder_factory import get_embed_fn
            from mekhane.anamnesis.constants import EMBED_MODEL, EMBED_DIM
            embed_fn = get_embed_fn()
            print(f"🔬 Embedding モード ({EMBED_MODEL}, {EMBED_DIM}d)")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Embedding 初期化失敗: {e} — テキストモードにフォールバック", file=sys.stderr)

    issues = checker.check_mece(
        path,
        embed_fn=embed_fn,
        me_threshold=args.me_threshold,
        me_error_threshold=args.me_error_threshold,
        ce_min_children=args.ce_min,
    )

    _print_mece_report(issues, path, embed_fn)

    errors = sum(1 for i in issues if i.severity == "error")
    if args.ci and errors > 0:
        return 1

    return 0


# PURPOSE: MECE 診断結果のフォーマット済みレポートを出力する
def _print_mece_report(issues: list, path, embed_fn) -> None:
    """MECE issue リストをセクション分けして表示する"""
    _ICONS = {
        "me_number": "🔢", "me_purpose": "🎯", "me_reason": "📝",
        "ce_decomposition": "🧩", "ce_proof": "📋", "ce_residual": "🕳️",
    }

    mode_label = "3072d embedding" if embed_fn else "テキストベース"
    print(f"\n🔍 Dendron MECE Check ({mode_label})")
    print(f"   対象: {path}")
    print()

    me_issues = [i for i in issues if i.issue_type.startswith("me_")]
    ce_issues = [i for i in issues if i.issue_type.startswith("ce_")]
    bcnf_issues = [i for i in issues if i.issue_type == "bcnf_deletable"]

    if me_issues:
        print("── ME (Mutual Exclusivity) ──")
        for issue in me_issues:
            icon = _ICONS.get(issue.issue_type, "⚠️")
            sev = "❌" if issue.severity == "error" else "⚠️"
            parent_name = issue.parent_path.name if issue.parent_path else "?"
            print(f"  {sev} {icon} [{parent_name}] {issue.suggestion}")
            if issue.paths:
                for p in issue.paths:
                    print(f"       ├─ {p.name}")
            if issue.similarity is not None:
                print(f"       cosine: {issue.similarity:.3f}")
            if issue.d_eff is not None:
                print(f"       d_eff: {issue.d_eff:.2f}")
        print()

    if bcnf_issues:
        print("── BCNF (削除可能性テスト) ──")
        for issue in bcnf_issues:
            sev = "❌" if issue.severity == "error" else "⚠️"
            parent_name = issue.parent_path.name if issue.parent_path else "?"
            path_name = issue.paths[0].name if issue.paths else "?"
            print(f"  {sev} 🗑️ [{parent_name}/{path_name}] {issue.suggestion}")
            if issue.deletability is not None:
                print(f"       deletability: {issue.deletability:.3f}")
            if issue.d_eff is not None:
                print(f"       d_eff_full: {issue.d_eff:.2f}")
            if issue.nearest_neighbor:
                sim_str = f" (cos={issue.neighbor_similarity:.2f})" if issue.neighbor_similarity else ""
                print(f"       最類似: {issue.nearest_neighbor}{sim_str}")
            if issue.shared_concepts:
                print(f"       共有語: {', '.join(issue.shared_concepts)}")
            if issue.unique_concepts:
                print(f"       固有語: {', '.join(issue.unique_concepts)}")
            if issue.differentiation_hint:
                print(f"       → {issue.differentiation_hint}")
        print()

    if ce_issues:
        print("── CE (Collective Exhaustiveness) ──")
        for issue in ce_issues:
            icon = _ICONS.get(issue.issue_type, "⚠️")
            sev = "❌" if issue.severity == "error" else "⚠️"
            parent_name = issue.parent_path.name if issue.parent_path else "?"
            print(f"  {sev} {icon} [{parent_name}] {issue.suggestion}")
            if issue.paths:
                for p in issue.paths:
                    print(f"       ├─ {p.name}")
            if issue.residual is not None:
                print(f"       residual: {issue.residual:.3f}")
        print()

    # サマリ
    total = len(issues)
    errors = sum(1 for i in issues if i.severity == "error")
    warnings = sum(1 for i in issues if i.severity == "warning")

    if total == 0:
        print("✅ MECE — issue なし")
    else:
        print(f"📊 合計: {total} issues ({errors} errors, {warnings} warnings)")
        print(f"   ME: {len(me_issues)} | BCNF: {len(bcnf_issues)} | CE: {len(ce_issues)}")


# PURPOSE: Kalon 収束判定 — stiffness ランキング + G∘F 収束検出 (v5.0)
def cmd_kalon(args: argparse.Namespace) -> int:
    """kalon コマンドの実行 — Layer 1 (重み) + Layer 2 (収束) の統合パイプライン"""
    from .kalon_weight import weight_issues, make_snapshot
    from .kalon_convergence import KalonHistory

    path = Path(args.path).resolve()
    if not path.exists():
        print(f"Error: {path} が存在しません", file=sys.stderr)
        return 1

    # 1. check 実行
    checker = DendronChecker(
        check_dirs=True,
        check_files=True,
        check_functions=True,
        check_structure=True,
        check_function_nf=True,
        check_verification=True,
    )
    result = checker.check(path)

    # 2. Layer 1: stiffness ランキング
    issues = weight_issues(result)
    snapshot = make_snapshot(result, issues)

    # レポート出力
    print("=" * 60)
    print("Dendron Kalon — Stiffness ランキング + 収束判定")
    print("=" * 60)
    print()
    print(f"品質スコア: {snapshot.quality_score:.3f}")
    print(f"  Coverage:   {snapshot.coverage:.1f}%")
    print(f"  EPT:        {snapshot.ept_score}/{snapshot.ept_total} ({snapshot.ept_ratio:.1%})")
    print(f"  Issues:     {snapshot.weighted_issue_count} (stiffness合計: {snapshot.total_stiffness:.2f})")
    print()

    top_n = args.top
    if issues:
        print(f"── Top-{min(top_n, len(issues))} Stiff Issues (先に直すべきもの) ──")
        for i, issue in enumerate(issues[:top_n], 1):
            print(f"  {i}. [{issue.coordinate.value} d={issue.d_value}] w={issue.weight:.2f}")
            print(f"     {issue.detail}")
            if issue.path != "<aggregate>":
                print(f"     @ {issue.path}")
        print()
    else:
        print("✅ stiff な issue なし")
        print()

    # 3. Layer 2: 履歴保存
    history_dir = Path(args.history_dir) if args.history_dir else None
    history = KalonHistory(history_dir=history_dir)

    if args.save:
        saved_path = history.save(
            target=path,
            quality_score=snapshot.quality_score,
            coverage=snapshot.coverage,
            ept_score=snapshot.ept_score,
            ept_total=snapshot.ept_total,
            ept_ratio=snapshot.ept_ratio,
            weighted_issue_count=snapshot.weighted_issue_count,
            total_stiffness=snapshot.total_stiffness,
            top_stiff_issues=snapshot.top_stiff_issues,
        )
        print(f"💾 履歴保存: {saved_path}")
        print()

    # 4. Layer 2: 収束判定
    judgment = None
    if args.judge:
        judgment = history.judge_convergence(path)
        print(KalonHistory.format_report(judgment))

    # CI モード — judgment は上で取得済みなら再利用
    if args.ci:
        if args.judge:
            if judgment is None:
                judgment = history.judge_convergence(path)
            if judgment.verdict == "✗":
                return 1
        if not result.is_passing:
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
