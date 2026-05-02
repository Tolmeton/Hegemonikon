#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/dendron/ A0→PURPOSE自動付与が必要→purpose_inferが担う
"""
PURPOSE Auto-Inferer — 関数/クラスの名前と文脈から PURPOSE コメントを自動推定して付与する。

Usage:
    python -m mekhane.dendron.purpose_infer mekhane/  [--dry-run]  [--limit 50]
"""

import ast
import re
from pathlib import Path
from typing import Optional


# PURPOSE: 関数/クラス名から日本語の PURPOSE コメントを推定する
def infer_purpose(name: str, node_type: str, docstring: Optional[str] = None) -> str:
    """名前と型から PURPOSE を推定する。

    アルゴリズム:
    1. docstring があればそこから抽出
    2. 名前のパターンマッチ (get_, set_, check_, run_, etc.)
    3. フォールバック: 名前をそのまま使用
    """
    # docstring から1行目を抽出
    if docstring:
        first_line = docstring.strip().split("\n")[0].strip()
        # 日本語があればそのまま使う
        if re.search(r'[\u3000-\u9fff]', first_line):
            return first_line[:80]
        # 英語の短い説明があればそれを使う
        if len(first_line) < 100 and first_line:
            return first_line[:80]

    # 名前パターンからの推定 (順序重要: dunder → single underscore)
    patterns = [
        (r'^__init__$', '初期化'),
        (r'^__str__|^__repr__', '文字列表現'),
        (r'^get_|^fetch_|^load_|^read_', '取得'),
        (r'^set_|^update_|^save_|^write_', '設定/保存'),
        (r'^check_|^validate_|^verify_|^is_|^has_', '検証'),
        (r'^run_|^execute_|^start_|^launch_', '実行'),
        (r'^create_|^make_|^build_|^generate_', '生成'),
        (r'^delete_|^remove_|^clear_|^cleanup_', '削除/クリーンアップ'),
        (r'^parse_|^extract_|^split_', 'パース/抽出'),
        (r'^format_|^render_|^display_|^print_', 'フォーマット/表示'),
        (r'^test_', 'テスト'),
        (r'^_', '内部処理'),
    ]

    for pattern, desc in patterns:
        if re.match(pattern, name):
            clean_name = re.sub(r'^_+', '', name)
            return f"{desc}: {clean_name}"

    # フォールバック
    prefix = "クラス" if node_type == "class" else "関数"
    return f"{prefix}: {name}"


# PURPOSE: ファイルに PURPOSE コメントを自動挿入する
def add_purpose_comments(filepath: Path, dry_run: bool = True) -> int:
    """ファイル中の PURPOSE なし関数/クラスに PURPOSE コメントを追加する。

    Returns:
        追加した PURPOSE の数
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.split("\n")

    try:
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        return 0

    insertions = []  # (line_number, purpose_comment)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue

        # 既に PURPOSE があるか確認
        start_line = node.lineno  # 1-indexed
        # 直前の2行に PURPOSE があるかチェック
        check_start = max(0, start_line - 3)
        preceding = "\n".join(lines[check_start:start_line - 1])
        if "PURPOSE:" in preceding:
            continue

        # docstring を取得
        docstring = ast.get_docstring(node)
        node_type = "class" if isinstance(node, ast.ClassDef) else "function"
        purpose = infer_purpose(node.name, node_type, docstring)

        # 挿入位置 = def/class の直前の行
        indent = ""
        if start_line - 1 < len(lines):
            def_line = lines[start_line - 1]
            indent = def_line[:len(def_line) - len(def_line.lstrip())]

        insertions.append((start_line - 1, f"{indent}# PURPOSE: [L2-auto] {purpose}"))

    if dry_run:
        for line_no, comment in insertions:
            print(f"  L{line_no + 1}: {comment.strip()}")
        return len(insertions)

    # 逆順で挿入 (行番号がずれないように)
    for line_no, comment in reversed(insertions):
        lines.insert(line_no, comment)

    filepath.write_text("\n".join(lines), encoding="utf-8")
    return len(insertions)


# PURPOSE: CLI エントリポイント
def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Auto-infer PURPOSE comments")
    parser.add_argument("path", help="Directory or file to process")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Show changes without writing")
    parser.add_argument("--apply", action="store_true", help="Actually write changes")
    parser.add_argument("--limit", type=int, default=50, help="Max files to process")
    args = parser.parse_args()

    target = Path(args.path)
    dry_run = not args.apply

    if dry_run:
        print("🔍 DRY RUN — showing proposed changes (use --apply to write)")
    else:
        print("✏️  APPLYING PURPOSE comments...")

    files = sorted(target.rglob("*.py")) if target.is_dir() else [target]
    total_added = 0
    files_modified = 0

    for i, f in enumerate(files[:args.limit]):
        if "__pycache__" in str(f) or "test" in f.name.lower():
            continue
        count = add_purpose_comments(f, dry_run=dry_run)
        if count > 0:
            print(f"📄 {f}: +{count} PURPOSE")
            total_added += count
            files_modified += 1

    print(f"\n{'Would add' if dry_run else 'Added'}: {total_added} PURPOSE comments in {files_modified} files")


if __name__ == "__main__":
    main()
