#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/dendron/
"""
Dendron 親参照移行スクリプト

ORPHAN ファイルに親参照を自動追加する。
親は「ファイルが属するディレクトリ」を基本とする。
"""

import re
from pathlib import Path
from typing import Optional

# 親参照パターン
PROOF_PATTERN = re.compile(r"(#\s*PROOF:\s*\[[^\]]+\])")


# PURPOSE: ファイルが属するディレクトリから親パスを決定する
def get_parent_path(file_path: Path, root: Path) -> str:
    """ファイルの親パスを決定"""
    rel_path = file_path.relative_to(root)
    parent = rel_path.parent
    
    # 親ディレクトリがルートなら、パッケージ名を使用
    if str(parent) == ".":
        return str(rel_path.stem)
    
    return str(parent) + "/"


# PURPOSE: ORPHAN ファイルの PROOF ヘッダーに親参照を追加する
def add_parent_reference(file_path: Path, root: Path, dry_run: bool = True) -> Optional[str]:
    """ファイルに親参照を追加"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return f"読み込みエラー: {e}"
    
    # PROOF ヘッダーを検索
    match = PROOF_PATTERN.search(content)
    if not match:
        return "PROOF ヘッダーなし"
    
    old_proof = match.group(1)
    
    # 既に親参照がある場合はスキップ
    if "<-" in content.split("\n")[0]:
        return "既に親参照あり"
    
    # 親パスを決定
    parent_path = get_parent_path(file_path, root)
    
    # 新しい PROOF ヘッダー
    new_proof = f"{old_proof} <- {parent_path}"
    
    # 置換
    new_content = content.replace(old_proof, new_proof, 1)
    
    if dry_run:
        return f"DRY-RUN: {old_proof} → {new_proof}"
    
    # 書き込み
    file_path.write_text(new_content, encoding="utf-8")
    return f"UPDATED: {old_proof} → {new_proof}"


# PURPOSE: CLI 引数をパースして移行処理を実行する
def main() -> None:
    import argparse
    
    parser = argparse.ArgumentParser(description="Dendron 親参照移行")
    parser.add_argument("target", help="対象ディレクトリ")
    parser.add_argument("--dry-run", action="store_true", help="実際には変更しない")
    parser.add_argument("--root", default=".", help="ルートディレクトリ")
    
    args = parser.parse_args()
    
    root = Path(args.root).resolve()
    target = Path(args.target).resolve()
    
    updated = 0
    skipped = 0
    errors = 0
    
    for py_file in target.rglob("*.py"):
        result = add_parent_reference(py_file, root, dry_run=args.dry_run)
        
        if result:
            if "UPDATED" in result or "DRY-RUN" in result:
                print(f"  {py_file.relative_to(root)}: {result}")
                updated += 1
            elif "既に" in result:
                skipped += 1
            else:
                print(f"  ⚠️ {py_file.relative_to(root)}: {result}")
                errors += 1
    
    print()
    print(f"📊 結果: {updated} 更新, {skipped} スキップ, {errors} エラー")
    
    if args.dry_run and updated > 0:
        print()
        print("💡 実行するには --dry-run を外してください")


if __name__ == "__main__":
    main()
