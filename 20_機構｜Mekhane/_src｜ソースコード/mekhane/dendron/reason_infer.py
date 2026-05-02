#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/dendron/
# PURPOSE: コードの REASON (存在理由の経緯) を自動推定して付与し、R軸カバレッジを改善する
# REASON: REASON カバレッジ 1.3% (41/3089) を改善するため purpose_infer.py と同じアーキテクチャで構築
"""
REASON Auto-Inferer — ファイル/関数の文脈から REASON コメントを自動推定して付与する。

PURPOSE が「なぜ存在するか (未来)」なら、REASON は「なぜ作られたか (過去)」。
Git 履歴・docstring・名前パターンから REASON を推定する。

Usage:
    python -m mekhane.dendron.reason_infer mekhane/  [--dry-run]  [--limit 50]
"""

import ast
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


# PURPOSE: Git 履歴からファイルの初回コミット日を取得し、REASON の時間的根拠を確立する
def get_file_creation_date(filepath: Path) -> Optional[str]:
    """Git 履歴からファイル作成日を取得する。

    shallow clone 環境では git log が失敗する可能性があるため、
    失敗時はファイル mtime にフォールバックする。

    Returns:
        YYYY-MM-DD 形式の日付文字列、または None
    """
    # Git 履歴から取得を試行
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%ai", "--", str(filepath)],
            capture_output=True, text=True, timeout=5,
            cwd=filepath.parent,
        )
        if result.returncode == 0 and result.stdout.strip():
            # 最後の行 (= 最初のコミット) を取得
            lines = result.stdout.strip().split("\n")
            date_str = lines[-1].split()[0]  # "2026-01-20 12:34:56 +0900" → "2026-01-20"
            return date_str
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # フォールバック: ファイル mtime
    try:
        mtime = filepath.stat().st_mtime
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except OSError:
        return None


# PURPOSE: Git コミットメッセージからファイルの最初のコミットメッセージを取得する
def get_first_commit_message(filepath: Path) -> Optional[str]:
    """Git の最初のコミットメッセージを取得する。"""
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%s", "--", str(filepath)],
            capture_output=True, text=True, timeout=5,
            cwd=filepath.parent,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            return lines[-1].strip()[:80]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


# PURPOSE: 関数/クラスの文脈から REASON を推定し、存在理由の経緯を言語化する
def infer_reason(
    name: str,
    node_type: str,
    docstring: Optional[str] = None,
    purpose_text: Optional[str] = None,
) -> str:
    """名前・docstring・PURPOSE から REASON を推定する。

    アルゴリズム:
    1. docstring に「背景」「経緯」パターンがあればそこから抽出
    2. PURPOSE があれば「{PURPOSE} を実現するために作成」
    3. 名前パターンからの推定
    4. フォールバック: タイムスタンプベース
    """
    # docstring から背景・経緯パターンを抽出
    if docstring:
        for line in docstring.split("\n"):
            stripped = line.strip()
            # 日本語の背景パターン
            if re.search(r"(背景|経緯|動機|理由|きっかけ|〜のため|ために)", stripped):
                return stripped[:80]
            # 英語の背景パターン
            if re.search(r"(Background|Motivation|Context|History|Created because)", stripped, re.IGNORECASE):
                return stripped[:80]

    # PURPOSE テキストから推定
    if purpose_text:
        return f"{purpose_text} を実現するために作成"

    # 名前パターンからの推定
    patterns = [
        (r"^__init__$", "クラスの初期化処理が必要だったため"),
        (r"^migrate_|^upgrade_", "既存データの移行が必要だったため"),
        (r"^fix_|^patch_|^hotfix_", "バグ修正のため"),
        (r"^add_|^create_|^new_", "新機能追加のため"),
        (r"^refactor_|^restructure_", "コード品質改善のため"),
        (r"^test_", "品質保証のため"),
        (r"^_", "内部実装の需要があったため"),
    ]

    for pattern, reason in patterns:
        if re.match(pattern, name):
            return reason

    # フォールバック
    prefix = "クラス" if node_type == "class" else "関数"
    return f"{prefix} {name} の実装が必要だったため"


# PURPOSE: ファイルレベルの REASON を推定し、ファイル全体の存在理由を言語化する
def infer_file_reason(filepath: Path) -> str:
    """ファイルレベルの REASON を推定する。

    優先順位:
    1. Git 初回コミットメッセージ
    2. ファイル作成日ベースのデフォルト
    """
    # Git コミットメッセージから推定
    commit_msg = get_first_commit_message(filepath)
    if commit_msg:
        return f"{commit_msg}"

    # 日付ベースのフォールバック
    date = get_file_creation_date(filepath)
    if date:
        return f"初回実装 ({date})"

    return "初回実装"


# PURPOSE: ファイルに REASON コメントを自動挿入する
def add_reason_comments(filepath: Path, dry_run: bool = True) -> Tuple[int, int]:
    """ファイル中の REASON なし関数/クラスに REASON コメントを追加する。

    Returns:
        (file_level_added, function_level_added) のタプル
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    file_added = 0
    func_added = 0

    # --- ファイルレベル REASON ---
    # PROOF ヘッダー行の近くに REASON がなければ追加
    has_file_reason = any("REASON:" in line for line in lines[:20])
    proof_line_idx = None
    for i, line in enumerate(lines[:20]):
        if "PROOF:" in line:
            proof_line_idx = i
            break

    if not has_file_reason and proof_line_idx is not None:
        file_reason = infer_file_reason(filepath)
        reason_comment = f"# REASON: [auto] {file_reason}"
        if dry_run:
            print(f"  L{proof_line_idx + 2}: {reason_comment}")
        else:
            lines.insert(proof_line_idx + 1, reason_comment)
        file_added = 1

    # --- 関数/クラスレベル REASON ---
    try:
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        if not dry_run and file_added:
            filepath.write_text("\n".join(lines), encoding="utf-8")
        return file_added, 0

    insertions = []  # (line_number, reason_comment)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        start_line = node.lineno  # 1-indexed
        # 直前の4行に REASON があるかチェック
        check_start = max(0, start_line - 5)
        preceding = "\n".join(lines[check_start:start_line - 1])
        if "REASON:" in preceding:
            continue

        # PURPOSE テキストを直前から取得
        purpose_text = None
        for pline in lines[check_start:start_line - 1]:
            match = re.search(r"#\s*PURPOSE:\s*(.+)", pline)
            if match:
                purpose_text = match.group(1).strip()
                break

        docstring = ast.get_docstring(node)
        node_type = "class" if isinstance(node, ast.ClassDef) else "function"
        reason = infer_reason(node.name, node_type, docstring, purpose_text)

        # 挿入位置 = PURPOSE 行の直後、なければ def/class の直前
        indent = ""
        if start_line - 1 < len(lines):
            def_line = lines[start_line - 1]
            indent = def_line[: len(def_line) - len(def_line.lstrip())]

        # PURPOSE 行があればその直後に挿入
        insert_at = start_line - 1  # def の直前
        for i in range(check_start, start_line - 1):
            if "PURPOSE:" in lines[i]:
                insert_at = i + 1
                break

        insertions.append((insert_at, f"{indent}# REASON: [auto] {reason}"))

    if dry_run:
        for line_no, comment in insertions:
            print(f"  L{line_no + 1}: {comment.strip()}")
        func_added = len(insertions)
    else:
        # 逆順で挿入 (行番号がずれないように)
        # file_added による行番号オフセットを考慮
        offset = file_added
        for line_no, comment in reversed(insertions):
            lines.insert(line_no + offset, comment)
        func_added = len(insertions)
        filepath.write_text("\n".join(lines), encoding="utf-8")

    return file_added, func_added


# PURPOSE: CLI エントリポイント
def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Auto-infer REASON comments")
    parser.add_argument("path", help="Directory or file to process")
    parser.add_argument(
        "--dry-run", action="store_true", default=True,
        help="Show changes without writing",
    )
    parser.add_argument("--apply", action="store_true", help="Actually write changes")
    parser.add_argument("--limit", type=int, default=50, help="Max files to process")
    args = parser.parse_args()

    target = Path(args.path)
    dry_run = not args.apply

    if dry_run:
        print("🔍 DRY RUN — showing proposed REASON additions (use --apply to write)")
    else:
        print("✏️  APPLYING REASON comments...")

    files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
    total_file = 0
    total_func = 0
    files_modified = 0

    for f in files[: args.limit]:
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


if __name__ == "__main__":
    sys.exit(main())
