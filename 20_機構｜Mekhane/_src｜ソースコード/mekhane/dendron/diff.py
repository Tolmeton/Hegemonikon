# PROOF: [L2/コア] <- mekhane/dendron/diff.py
"""
Dendron Diff — Git 差分に基づく EPT 変化検出

PURPOSE: Git の差分情報から EPT スコアの変化を検出し、
         コード変更が品質に与える影響を可視化する

Usage:
    python -m mekhane.dendron.cli diff [--since HEAD~1] [PATH]
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

from .checker import DendronChecker


# PURPOSE: Git diff 結果のファイル変更状態を表現する
@dataclass
class FileChange:
    """Git diff で検出されたファイル変更"""
    path: Path
    status: str  # A(dded), M(odified), D(eleted), R(enamed)
    old_path: Optional[Path] = None  # Renamed の場合の旧パス


# PURPOSE: diff チェック結果を格納する構造体
@dataclass
class DiffResult:
    """dendron diff の結果"""
    since: str
    changed_files: List[FileChange] = field(default_factory=list)
    # EPT スコア
    current_score: int = 0
    current_total: int = 0
    # 変化検出
    proof_added: List[Path] = field(default_factory=list)
    proof_removed: List[Path] = field(default_factory=list)
    proof_modified: List[Path] = field(default_factory=list)
    purpose_added: List[Path] = field(default_factory=list)
    reason_added: List[Path] = field(default_factory=list)
    # モジュール
    affected_modules: Set[str] = field(default_factory=set)


# PURPOSE: Git の差分情報を取得する
def get_git_diff_files(root: Path, since: str = "HEAD~1") -> List[FileChange]:
    """Git diff から変更ファイルリストを取得"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", since, "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return []
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    changes: List[FileChange] = []
    for line in result.stdout.strip().splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0][0]  # A, M, D, R の先頭文字
        filepath = Path(parts[-1])
        old_path = Path(parts[1]) if status == "R" and len(parts) > 2 else None
        changes.append(FileChange(path=filepath, status=status, old_path=old_path))

    return changes


# PURPOSE: PROOF コメントの変化を検出する
def detect_proof_changes(
    root: Path, changes: List[FileChange]
) -> tuple:
    """PROOF コメントの追加/削除/変更を検出"""
    proof_added: List[Path] = []
    proof_removed: List[Path] = []
    proof_modified: List[Path] = []
    purpose_added: List[Path] = []
    reason_added: List[Path] = []

    for change in changes:
        if not change.path.suffix == ".py":
            continue

        full_path = root / change.path

        if change.status == "A":
            # 新規ファイル: PROOF があるか確認
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8", errors="replace")
                if "# PROOF:" in content:
                    proof_added.append(change.path)
                if "# PURPOSE:" in content or "PURPOSE:" in content:
                    purpose_added.append(change.path)

        elif change.status == "D":
            # 削除ファイル: PROOF が失われた
            proof_removed.append(change.path)

        elif change.status == "M":
            # 変更ファイル: diff で PROOF 行の変化を検出
            if full_path.exists():
                try:
                    diff_output = subprocess.run(
                        ["git", "diff", "--unified=0", "HEAD~1", "HEAD", "--", str(change.path)],
                        cwd=str(root),
                        capture_output=True, text=True, timeout=5,
                    )
                    diff_text = diff_output.stdout
                    if "+# PROOF:" in diff_text or "-# PROOF:" in diff_text:
                        proof_modified.append(change.path)
                    if "+# PURPOSE:" in diff_text or "+PURPOSE:" in diff_text:
                        purpose_added.append(change.path)
                    if "+REASON:" in diff_text:
                        reason_added.append(change.path)
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

        # PROOF.md の変化
        if change.path.name == "PROOF.md":
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8", errors="replace")
                if "PURPOSE:" in content:
                    purpose_added.append(change.path)
                if "REASON:" in content:
                    reason_added.append(change.path)

    return proof_added, proof_removed, proof_modified, purpose_added, reason_added


# PURPOSE: diff チェックのメインエントリポイント
def diff_check(root: Path, since: str = "HEAD~1") -> DiffResult:
    """Git diff に基づく EPT 変化検出"""
    result = DiffResult(since=since)

    # 1. Git diff からファイル変更を取得
    changes = get_git_diff_files(root, since)
    result.changed_files = changes

    # 変更ファイルから影響モジュールを特定
    for change in changes:
        parts = change.path.parts
        if len(parts) >= 2 and parts[0] == "mekhane":
            result.affected_modules.add(parts[1])

    # 2. PROOF/PURPOSE/REASON の変化を検出
    (
        result.proof_added,
        result.proof_removed,
        result.proof_modified,
        result.purpose_added,
        result.reason_added,
    ) = detect_proof_changes(root, changes)

    # 3. 現在の EPT スコアを計算 (変更されたモジュールのみ)
    if result.affected_modules:
        checker = DendronChecker(
            check_structure=True,
            check_function_nf=True,
            check_verification=True,
        )
        for module in result.affected_modules:
            module_path = root / "mekhane" / module
            if module_path.is_dir():
                try:
                    check_result = checker.check(module_path)
                    result.current_score += (
                        check_result.structure_ok
                        + check_result.function_nf_ok
                        + check_result.verification_ok
                    )
                    result.current_total += (
                        check_result.total_structure_checks
                        + check_result.total_function_nf_checks
                        + check_result.total_verification_checks
                    )
                except Exception:  # noqa: BLE001
                    pass

    return result


# PURPOSE: diff 結果をフォーマットして出力する
def format_diff_result(result: DiffResult) -> str:
    """diff 結果のテキスト表示"""
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append(f"Dendron Diff Report (since {result.since})")
    lines.append("=" * 60)
    lines.append("")

    # 概要
    py_files = [c for c in result.changed_files if c.path.suffix == ".py"]
    md_files = [c for c in result.changed_files if c.path.suffix == ".md"]
    lines.append(f"Changed files: {len(result.changed_files)} total ({len(py_files)} .py, {len(md_files)} .md)")
    if result.affected_modules:
        lines.append(f"Affected modules: {', '.join(sorted(result.affected_modules))}")
    lines.append("")

    # PROOF 変化
    if result.proof_added or result.proof_removed or result.proof_modified:
        lines.append("--- PROOF Changes ---")
        for p in result.proof_added:
            lines.append(f"  ✅ +PROOF  {p}")
        for p in result.proof_removed:
            lines.append(f"  ❌ -PROOF  {p}")
        for p in result.proof_modified:
            lines.append(f"  📝 ~PROOF  {p}")
        lines.append("")

    # PURPOSE/REASON 変化
    if result.purpose_added or result.reason_added:
        lines.append("--- PURPOSE/REASON Changes ---")
        for p in result.purpose_added:
            lines.append(f"  🎯 +PURPOSE  {p}")
        for p in result.reason_added:
            lines.append(f"  💡 +REASON   {p}")
        lines.append("")

    # EPT スコア
    if result.current_total > 0:
        pct = result.current_score / result.current_total * 100
        lines.append(f"EPT (affected modules): {result.current_score}/{result.current_total} ({pct:.0f}%)")
    else:
        lines.append("EPT: No Python changes in mekhane/")

    return "\n".join(lines)
