"""R1 同型群トリアージ: 車輪の再開発候補を抽出する。"""
import ast
import sys
import os
from pathlib import Path
from collections import defaultdict

# mekhane の code_ingest.py をインポート
MEKHANE_SRC = Path(r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード")
sys.path.insert(0, str(MEKHANE_SRC))

from mekhane.symploke.code_ingest import python_to_ccl


def extract_functions(filepath: Path) -> list:
    """ファイルから全関数/メソッドを抽出し、CCL に変換する。"""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return []

    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                ccl = python_to_ccl(node)
            except Exception:
                continue
            fstr = str(filepath)
            results.append({
                "name": node.name,
                "file": fstr,
                "line": node.lineno,
                "ccl": ccl,
                "is_test": node.name.startswith("test_") or "test_" in filepath.name or "tests" in fstr,
                "body_lines": (node.end_lineno - node.lineno + 1) if hasattr(node, "end_lineno") and node.end_lineno else 0,
            })
    return results


def main():
    mekhane_root = MEKHANE_SRC / "mekhane"
    print(f"走査: {mekhane_root}")

    all_funcs = []
    file_count = 0
    for py_file in mekhane_root.rglob("*.py"):
        funcs = extract_functions(py_file)
        all_funcs.extend(funcs)
        file_count += 1

    prod_funcs = [f for f in all_funcs if not f["is_test"]]
    test_funcs = [f for f in all_funcs if f["is_test"]]

    print(f"\n=== 基本統計 ===")
    print(f"ファイル数: {file_count}")
    print(f"全関数数: {len(all_funcs)}")
    print(f"プロダクション: {len(prod_funcs)}")
    print(f"テスト: {len(test_funcs)}")

    # CCL でグループ化
    ccl_groups = defaultdict(list)
    for func in all_funcs:
        ccl_groups[func["ccl"]].append(func)

    print(f"ユニーク CCL: {len(ccl_groups)}")

    # プロダクション関数のみの同型群
    prod_ccl = defaultdict(list)
    for func in prod_funcs:
        prod_ccl[func["ccl"]].append(func)

    # 同型群 (プロダクション関数 ≥2, CCL ≥5トークン)
    cross_file_groups = []
    same_file_groups = []

    for ccl, funcs in prod_ccl.items():
        if len(funcs) < 2:
            continue
        tokens = len(ccl.split())
        if tokens < 5:
            continue

        files = set(f["file"] for f in funcs)
        entry = {"ccl": ccl, "tokens": tokens, "funcs": funcs, "files": files, "count": len(funcs)}

        if len(files) >= 2:
            cross_file_groups.append(entry)
        else:
            same_file_groups.append(entry)

    # トークン数降順ソート
    cross_file_groups.sort(key=lambda x: (-x["tokens"], -x["count"]))
    same_file_groups.sort(key=lambda x: (-x["tokens"], -x["count"]))

    rel_root = MEKHANE_SRC

    print(f"\n=== プロダクション同型群 (CCL≥5トークン, 関数≥2) ===")
    print(f"複数ファイル横断: {len(cross_file_groups)}")
    print(f"同一ファイル内: {len(same_file_groups)}")

    print(f"\n{'='*80}")
    print(f"  カテゴリA: 複数ファイル横断 (車輪の再開発候補)")
    print(f"{'='*80}")

    for i, g in enumerate(cross_file_groups[:40], 1):
        print(f"\n--- A-{i} | {g['count']}関数 | {g['tokens']}トークン | {len(g['files'])}ファイル ---")
        print(f"CCL: {g['ccl']}")
        for func in g["funcs"]:
            rel = os.path.relpath(func["file"], rel_root)
            print(f"  {func['name']:<45} {rel}:{func['line']} ({func['body_lines']}行)")

    print(f"\n{'='*80}")
    print(f"  カテゴリB: 同一ファイル内 (内部リファクタ候補) 上位20")
    print(f"{'='*80}")

    for i, g in enumerate(same_file_groups[:20], 1):
        print(f"\n--- B-{i} | {g['count']}関数 | {g['tokens']}トークン ---")
        print(f"CCL: {g['ccl']}")
        for func in g["funcs"]:
            rel = os.path.relpath(func["file"], rel_root)
            print(f"  {func['name']:<45} {rel}:{func['line']} ({func['body_lines']}行)")


if __name__ == "__main__":
    main()
