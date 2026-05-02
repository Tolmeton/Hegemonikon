#!/usr/bin/env python3
"""
階級別 Cosine 実コードベーステスト + 閾値チューニング
GIL 安全版: AST ノード数で事前フィルタ (CPU-bound なハング防止)
"""
import ast
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

# パス設定
MEKHANE_SRC = Path(r"c:\Users\makar\Sync\oikos\01_ヘゲモニコン｜Hegemonikon\20_機構｜Mekhane\_src｜ソースコード")
sys.path.insert(0, str(MEKHANE_SRC))

from mekhane.symploke.code_ingest import python_to_ccl, ccl_feature_vector
from mekhane.symphysis.fusion import (
    FusionEntry, analyze_freedom, analyze_freedom_hierarchical,
    TAXONOMIC_RANKS, _cosine_subvector, _cosine_similarity,
)

# 除外ディレクトリ
EXCLUDES = {"__pycache__", ".git", ".venv", "venv", "node_modules",
            "90_保管庫｜Archive", ".system_generated", "dist", "build"}

# AST ノード数の上限 — これ以上のノードを持つ関数は python_to_ccl がハングする可能性あり
MAX_AST_NODES = 200


def _count_ast_nodes(node: ast.AST) -> int:
    """AST ノードの総数をカウント (O(n))"""
    return sum(1 for _ in ast.walk(node))


def direct_scan(scan_dirs: list[Path], verbose: bool = False) -> list[FusionEntry]:
    """AST ノード数制限付き直接スキャン (GIL 安全)"""
    entries: list[FusionEntry] = []
    skipped = 0
    too_large = 0
    file_count = 0

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for py_file in sorted(scan_dir.rglob("*.py")):
            if set(py_file.parts) & EXCLUDES:
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=str(py_file))
            except (SyntaxError, UnicodeDecodeError):
                continue

            file_count += 1
            if verbose and file_count % 5 == 0:
                print(f"    ... {file_count} files, {len(entries)} entries, {skipped} skip, {too_large} too_large", flush=True)

            lines = source.splitlines()
            file_imports = []
            for n in ast.walk(tree):
                if isinstance(n, ast.Import):
                    for alias in n.names:
                        file_imports.append(alias.name)
                elif isinstance(n, ast.ImportFrom):
                    module = n.module or ""
                    for alias in n.names:
                        file_imports.append(f"{module}.{alias.name}")

            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                end = node.end_lineno or node.lineno
                if (end - node.lineno + 1) < 5:
                    continue
                if node.name.startswith("__") and node.name.endswith("__") and node.name != "__init__":
                    continue

                # AST ノード数チェック (GIL ハング防止)
                node_count = _count_ast_nodes(node)
                if node_count > MAX_AST_NODES:
                    too_large += 1
                    continue

                # CCL 変換
                try:
                    ccl_expr = python_to_ccl(node)
                except Exception:
                    skipped += 1
                    continue

                if not ccl_expr or ccl_expr == "_":
                    skipped += 1
                    continue

                # 51d 特徴量
                try:
                    features = ccl_feature_vector(node)
                except Exception:
                    features = []

                # PURPOSE 抽出
                purpose = ""
                if node.lineno >= 2:
                    prev = lines[node.lineno - 2].strip()
                    if prev.startswith("# PURPOSE:"):
                        purpose = prev[len("# PURPOSE:"):].strip()
                if not purpose:
                    doc = ast.get_docstring(node) or ""
                    purpose = doc[:100] if doc else node.name

                # クラス名
                class_name = ""
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        for child in ast.iter_child_nodes(parent):
                            if child is node:
                                class_name = parent.name
                                break

                entries.append(FusionEntry(
                    filepath=str(py_file),
                    name=node.name,
                    lineno=node.lineno,
                    class_name=class_name,
                    ccl_expr=" ".join(ccl_expr.split()),
                    ccl_features_43d=features,
                    purpose=purpose,
                    purpose_source="direct",
                    imports=file_imports,
                ))

    if verbose:
        print(f"  スキャン完了: {len(entries)} entries, {skipped} skip, {too_large} too_large, {file_count} files", flush=True)
    return entries


def threshold_sweep(entries: list[FusionEntry]):
    """各階級の cosine 分布を測定し推奨閾値を算出"""
    import statistics, random
    random.seed(42)

    valid = [e for e in entries if e.ccl_features_43d and len(e.ccl_features_43d) >= 51]
    n = len(valid)
    print(f"\n=== 閾値チューニング ({n} entries) ===", flush=True)

    max_pairs = min(5000, n * (n - 1) // 2)
    if n * (n - 1) // 2 <= max_pairs:
        pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    else:
        pairs = set()
        while len(pairs) < max_pairs:
            i = random.randint(0, n - 1)
            j = random.randint(0, n - 1)
            if i != j:
                pairs.add((min(i, j), max(i, j)))
        pairs = list(pairs)
    print(f"  サンプルペア数: {len(pairs)}", flush=True)

    rank_cosines: dict[str, list[float]] = {r: [] for r in TAXONOMIC_RANKS}
    full_cosines: list[float] = []
    for i, j in pairs:
        full = _cosine_similarity(valid[i].ccl_features_43d, valid[j].ccl_features_43d)
        full_cosines.append(full)
        for rank, (start, end) in TAXONOMIC_RANKS.items():
            cos = _cosine_subvector(valid[i].ccl_features_43d, valid[j].ccl_features_43d, start, end)
            rank_cosines[rank].append(cos)

    print(f"\n{'階級':12s} {'dim':>4s} {'mean':>7s} {'std':>7s} {'p50':>7s} {'p90':>7s} {'p95':>7s} {'p99':>7s}", flush=True)
    print("-" * 65, flush=True)
    recommended = {}
    for rank, (start, end) in TAXONOMIC_RANKS.items():
        vals = sorted(rank_cosines[rank])
        nv = len(vals)
        mean = statistics.mean(vals)
        std = statistics.stdev(vals) if nv > 1 else 0
        p50 = vals[int(nv * 0.5)]
        p90 = vals[int(nv * 0.9)]
        p95 = vals[int(nv * 0.95)]
        p99 = vals[int(nv * 0.99)]
        recommended[rank] = round(p95, 3)
        print(f"  {rank:10s} {end-start:3d}d  {mean:7.4f} {std:7.4f} {p50:7.4f} {p90:7.4f} {p95:7.4f} {p99:7.4f}", flush=True)

    vals = sorted(full_cosines)
    nv = len(vals)
    mean = statistics.mean(vals)
    std = statistics.stdev(vals) if nv > 1 else 0
    p50 = vals[int(nv * 0.5)]
    p90 = vals[int(nv * 0.9)]
    p95 = vals[int(nv * 0.95)]
    p99 = vals[int(nv * 0.99)]
    print(f"  {'all':10s} {51:3d}d  {mean:7.4f} {std:7.4f} {p50:7.4f} {p90:7.4f} {p95:7.4f} {p99:7.4f}", flush=True)

    print(f"\n推奨閾値 (p95):", flush=True)
    for rank, t in recommended.items():
        print(f"  {rank:10s}: {t}", flush=True)
    return recommended


def main():
    print("=" * 70, flush=True)
    print("  階級別 Cosine — 実コードベース全スキャンテスト", flush=True)
    print("=" * 70, flush=True)

    from mekhane.paths import MEKHANE_DIR, OPS_DIR
    scan_dirs = [MEKHANE_DIR / "_src｜ソースコード", OPS_DIR / "_src｜ソースコード"]

    print(f"\nスキャン対象:", flush=True)
    for d in scan_dirs:
        x = "✅" if d.exists() else "❌"
        print(f"  {x} {d}", flush=True)

    t0 = time.time()
    entries = direct_scan(scan_dirs, verbose=True)
    t1 = time.time()
    print(f"  スキャン時間: {t1-t0:.1f}秒", flush=True)

    vec_lengths = [len(e.ccl_features_43d) for e in entries if e.ccl_features_43d]
    if vec_lengths:
        print(f"  ベクトル長: min={min(vec_lengths)}, max={max(vec_lengths)}", flush=True)
        print(f"  51d entries: {sum(1 for v in vec_lengths if v >= 51)}/{len(vec_lengths)}", flush=True)

    # 旧方式
    print(f"\n{'='*70}", flush=True)
    print("  旧方式: 全体 cosine", flush=True)
    t0 = time.time()
    old = analyze_freedom(entries, cosine_threshold=0.9)
    t1 = time.time()
    print(f"  ペア数: {old.total_pairs_checked:,}, 同型: {old.structural_similar}, 接続: {old.connected}, 独立: {old.independent}, 自由率: {old.freedom_ratio:.2%}, {t1-t0:.1f}s", flush=True)

    # 新方式
    print(f"\n{'='*70}", flush=True)
    print("  新方式: 階級別 cosine", flush=True)
    t0 = time.time()
    hier = analyze_freedom_hierarchical(entries)
    t1 = time.time()
    print(f"  ペア数: {hier.total_pairs_checked:,}, 全階級独立: {hier.full_independent}, {t1-t0:.1f}s", flush=True)
    print(f"\n  階級別:", flush=True)
    for rank, count in hier.rank_similar.items():
        s, e = TAXONOMIC_RANKS[rank]
        ind = hier.rank_independent.get(rank, 0)
        print(f"    {rank:10s} ({e-s:2d}d): 同型={count:4d}, 独立={ind:4d}", flush=True)

    # 比較
    print(f"\n{'='*70}", flush=True)
    diff = old.independent - hier.full_independent
    print(f"  旧: 独立={old.independent}, 新: 全階級独立={hier.full_independent}, 差分: {diff}", flush=True)
    if old.independent > 0:
        print(f"  除外率: {diff/old.independent:.1%}", flush=True)

    # 上位ペア
    if hier.independent_pairs:
        print(f"\n  --- 独立同型ペア (上位 {min(10, len(hier.independent_pairs))}) ---", flush=True)
        for p in hier.independent_pairs[:10]:
            print(f"    {p['a']} ↔ {p['b']} (全階級: {p['全階級一致']})", flush=True)

    # 閾値チューニング
    rec = threshold_sweep(entries)

    # p95 で再分析
    print(f"\n{'='*70}", flush=True)
    print("  p95 閾値で再分析", flush=True)
    hier2 = analyze_freedom_hierarchical(entries, rank_thresholds=rec)
    print(f"  全階級独立: {hier2.full_independent}", flush=True)

    # 保存
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "entries_count": len(entries),
        "old": {"similar": old.structural_similar, "connected": old.connected, "independent": old.independent, "freedom_ratio": round(old.freedom_ratio, 4)},
        "new_default": {"full_independent": hier.full_independent, "rank_similar": hier.rank_similar, "rank_independent": hier.rank_independent},
        "new_p95": {"thresholds": rec, "full_independent": hier2.full_independent, "rank_independent": hier2.rank_independent},
        "independent_pairs": hier.independent_pairs[:20],
    }
    out = Path(__file__).parent / "results" / "hierarchical_cosine_results.json"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n結果保存: {out}", flush=True)


if __name__ == "__main__":
    main()
