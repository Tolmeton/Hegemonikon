#!/usr/bin/env python3
"""
直交性計測実験 — U_ccl × U_purpose の直交性を HGK コードベースで定量評価

仮説 F2: 二つの忘却関手は直交する情報を保存する [推定 85%]

計測:
  A. 同一 CCL × 異なる PURPOSE (構造的同型・目的異型) → U_ccl のファイバー
  B. 同一 PURPOSE × 異なる CCL (目的同型・構造異型) → U_purpose のファイバー
  C. 同一 CCL × 同一 PURPOSE → 真の冗長 (リファクタリング候補)
  D. 異なる CCL × 異なる PURPOSE → 独立 (直交の典型)

直交性スコア = (A + B) / (A + B + C)
  → 1.0 = 完全直交 (冗長なし)
  → 0.0 = 完全重複 (CCL と PURPOSE が結合)
"""

import sys
import signal
sys.setrecursionlimit(200)  # 深い再帰を早期に検出

import ast
from collections import defaultdict
from pathlib import Path
from dataclasses import dataclass, field

# PURPOSE: プロジェクトルートを追加
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"))

from mekhane.symploke.code_ingest import python_to_ccl
from mekhane.dendron.purpose_infer import infer_purpose


@dataclass
class FunctionEntry:
    """関数の CCL 構造式と PURPOSE を保持するエントリ"""
    filepath: str
    name: str
    lineno: int
    ccl_expr: str
    purpose: str
    class_name: str = ""


def _normalize_ccl(ccl: str) -> str:
    """CCL 式を正規化 (空白正規化 + 自明な式の除外)"""
    # 空白正規化
    result = " ".join(ccl.split())
    return result


def scan_codebase(scan_dirs: list[Path]) -> list[FunctionEntry]:
    """コードベースをスキャンし、全関数の CCL + PURPOSE を収集"""
    entries: list[FunctionEntry] = []
    exclude_dirs = {"__pycache__", ".git", ".venv", "venv", "node_modules",
                    "90_保管庫｜Archive", ".system_generated", "dist", "build"}

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            print(f"  ⚠️ {scan_dir} が存在しません、スキップ")
            continue

        for py_file in sorted(scan_dir.rglob("*.py")):
            # 除外チェック
            parts = set(py_file.parts)
            if parts & exclude_dirs:
                continue

            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError):
                continue

            lines = source.splitlines()

            # トップレベル関数
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    entry = _extract_entry(py_file, lines, node)
                    if entry:
                        entries.append(entry)
                elif isinstance(node, ast.ClassDef):
                    for item in ast.iter_child_nodes(node):
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            entry = _extract_entry(py_file, lines, item, class_name=node.name)
                            if entry:
                                entries.append(entry)

    return entries


def _extract_entry(filepath: Path, lines: list[str], node: ast.FunctionDef,
                   class_name: str = "") -> FunctionEntry | None:
    """AST ノードから FunctionEntry を抽出"""
    # 5行未満の自明な関数は除外
    end = node.end_lineno or node.lineno
    if (end - node.lineno + 1) < 5:
        return None

    # ダンダーメソッド除外 (__init__ は残す)
    if (node.name.startswith("__") and node.name.endswith("__")
            and node.name != "__init__"):
        return None

    # CCL 構造式 (タイムアウト + RecursionError 保護)
    def _timeout_handler(signum, frame):
        raise TimeoutError("python_to_ccl timeout")
    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    try:
        signal.alarm(3)  # 3秒タイムアウト
        ccl_expr = python_to_ccl(node)
        signal.alarm(0)
    except (RecursionError, TimeoutError):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
        return None  # 深い再帰/タイムアウトの関数はスキップ
    signal.signal(signal.SIGALRM, old_handler)
    if ccl_expr == "_":  # 空関数
        return None

    # PURPOSE: まず手書き PURPOSE コメントを探す
    purpose = ""
    if node.lineno > 1:
        prev_line = lines[node.lineno - 2].strip() if node.lineno >= 2 else ""
        if prev_line.startswith("# PURPOSE:"):
            purpose = prev_line[len("# PURPOSE:"):].strip()

    # 手書きがなければ推定
    if not purpose:
        docstring = ast.get_docstring(node)
        node_type = "function" if not class_name else "method"
        purpose = infer_purpose(node.name, node_type, docstring)

    return FunctionEntry(
        filepath=str(filepath),
        name=node.name,
        lineno=node.lineno,
        ccl_expr=_normalize_ccl(ccl_expr),
        purpose=purpose,
        class_name=class_name,
    )


def analyze_orthogonality(entries: list[FunctionEntry]) -> dict:
    """直交性を分析"""
    # CCL でグループ化
    ccl_groups: dict[str, list[FunctionEntry]] = defaultdict(list)
    for e in entries:
        ccl_groups[e.ccl_expr].append(e)

    # PURPOSE でグループ化
    purpose_groups: dict[str, list[FunctionEntry]] = defaultdict(list)
    for e in entries:
        purpose_groups[e.purpose].append(e)

    # カテゴリ A: 同一CCL × 異なるPURPOSE
    cat_a = []  # (ccl, [entries])
    for ccl, group in ccl_groups.items():
        purposes = set(e.purpose for e in group)
        if len(group) >= 2 and len(purposes) >= 2:
            cat_a.append((ccl, group))

    # カテゴリ B: 同一PURPOSE × 異なるCCL
    cat_b = []  # (purpose, [entries])
    for purpose, group in purpose_groups.items():
        ccls = set(e.ccl_expr for e in group)
        if len(group) >= 2 and len(ccls) >= 2:
            cat_b.append((purpose, group))

    # カテゴリ C: 同一CCL × 同一PURPOSE → 真の冗長
    cat_c = []
    for ccl, group in ccl_groups.items():
        if len(group) < 2:
            continue
        # 同一 PURPOSE のペアを検出
        purpose_subgroups: dict[str, list[FunctionEntry]] = defaultdict(list)
        for e in group:
            purpose_subgroups[e.purpose].append(e)
        for purpose, subgroup in purpose_subgroups.items():
            if len(subgroup) >= 2:
                cat_c.append((ccl, purpose, subgroup))

    # カテゴリ D: 全エントリ - (A∪B∪C) = 独立
    # (実際にはペア数で計算するが、簡略化して group 数で)

    # 統計
    total_functions = len(entries)
    unique_ccl = len(ccl_groups)
    unique_purpose = len(purpose_groups)
    multi_ccl_groups = sum(1 for g in ccl_groups.values() if len(g) >= 2)
    multi_purpose_groups = sum(1 for g in purpose_groups.values() if len(g) >= 2)

    # 直交性スコア
    a_count = sum(len(g) for _, g in cat_a)
    b_count = sum(len(g) for _, g in cat_b)
    c_count = sum(len(sg) for _, _, sg in cat_c)
    denom = a_count + b_count + c_count
    orthogonality_score = (a_count + b_count) / denom if denom > 0 else 1.0

    return {
        "total_functions": total_functions,
        "unique_ccl": unique_ccl,
        "unique_purpose": unique_purpose,
        "multi_ccl_groups": multi_ccl_groups,
        "multi_purpose_groups": multi_purpose_groups,
        "cat_a": cat_a,  # 同一CCL × 異なるPURPOSE
        "cat_b": cat_b,  # 同一PURPOSE × 異なるCCL
        "cat_c": cat_c,  # 真の冗長
        "a_count": a_count,
        "b_count": b_count,
        "c_count": c_count,
        "orthogonality_score": orthogonality_score,
    }


def print_report(results: dict) -> None:
    """結果レポートを出力"""
    print("\n" + "=" * 70)
    print("  CCL-IR × Dendron 直交性実験 — 結果レポート")
    print("=" * 70)

    print(f"\n📊 基本統計:")
    print(f"  関数/メソッド総数: {results['total_functions']}")
    print(f"  一意な CCL 構造式: {results['unique_ccl']}")
    print(f"  一意な PURPOSE:    {results['unique_purpose']}")
    print(f"  CCL 重複グループ:  {results['multi_ccl_groups']} (2+ メンバー)")
    print(f"  PURPOSE 重複グループ: {results['multi_purpose_groups']} (2+ メンバー)")

    print(f"\n📐 直交性分析:")
    print(f"  A. 同一CCL × 異なるPURPOSE: {results['a_count']} 関数 ({len(results['cat_a'])} グループ)")
    print(f"  B. 同一PURPOSE × 異なるCCL:  {results['b_count']} 関数 ({len(results['cat_b'])} グループ)")
    print(f"  C. 真の冗長 (同一CCL × 同一PURPOSE): {results['c_count']} 関数 ({len(results['cat_c'])} グループ)")

    score = results['orthogonality_score']
    print(f"\n  🎯 直交性スコア: {score:.3f}")
    if score >= 0.8:
        print("  → 高い直交性。融合に価値あり")
    elif score >= 0.5:
        print("  → 中程度の直交性。部分的に融合有用")
    else:
        print("  → 低い直交性。CCL と PURPOSE は結合的")

    # カテゴリ A の詳細 (上位5件)
    if results['cat_a']:
        print(f"\n--- カテゴリ A: 同一 CCL × 異なる PURPOSE (上位5件) ---")
        for i, (ccl, group) in enumerate(sorted(results['cat_a'], key=lambda x: -len(x[1]))[:5]):
            print(f"\n  [{i+1}] CCL: {ccl[:80]}{'...' if len(ccl) > 80 else ''}")
            for e in group[:5]:
                loc = f"{e.class_name}.{e.name}" if e.class_name else e.name
                fname = Path(e.filepath).name
                print(f"      {fname}:{loc} — PURPOSE: {e.purpose[:60]}")

    # カテゴリ B の詳細 (上位5件)
    if results['cat_b']:
        print(f"\n--- カテゴリ B: 同一 PURPOSE × 異なる CCL (上位5件) ---")
        for i, (purpose, group) in enumerate(sorted(results['cat_b'], key=lambda x: -len(x[1]))[:5]):
            print(f"\n  [{i+1}] PURPOSE: {purpose[:60]}")
            for e in group[:5]:
                loc = f"{e.class_name}.{e.name}" if e.class_name else e.name
                fname = Path(e.filepath).name
                print(f"      {fname}:{loc} — CCL: {e.ccl_expr[:60]}{'...' if len(e.ccl_expr) > 60 else ''}")

    # カテゴリ C の詳細 (全件)
    if results['cat_c']:
        print(f"\n--- カテゴリ C: 真の冗長 (同一CCL × 同一PURPOSE) ---")
        for i, (ccl, purpose, subgroup) in enumerate(results['cat_c'][:10]):
            print(f"\n  [{i+1}] CCL: {ccl[:60]}  PURPOSE: {purpose[:40]}")
            for e in subgroup:
                loc = f"{e.class_name}.{e.name}" if e.class_name else e.name
                fname = Path(e.filepath).name
                print(f"      {fname}:{loc} (L{e.lineno})")


def main():
    # HGK コードベースのスキャン対象
    hgk_root = ROOT
    scan_dirs = [
        hgk_root / "20_機構｜Mekhane" / "_src｜ソースコード",
        hgk_root / "80_運用｜Ops" / "_src｜ソースコード",
        hgk_root / "60_実験｜Peira",
    ]

    print("🔬 HGK コードベースをスキャン中...")
    entries = scan_codebase(scan_dirs)
    print(f"  → {len(entries)} 関数/メソッドを収集")

    if not entries:
        print("❌ エントリが見つかりません")
        return

    print("\n📐 直交性を分析中...")
    results = analyze_orthogonality(entries)
    print_report(results)


if __name__ == "__main__":
    main()
