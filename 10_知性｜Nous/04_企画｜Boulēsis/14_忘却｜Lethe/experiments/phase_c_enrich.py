#!/usr/bin/env python3
"""Phase C データエンリッチ: 既存ペアにソースコードを注入し、A/B/D 3条件用 JSONL を生成。

既存の phase_c_training.jsonl (1000ペア) のメタデータから元ファイルを特定し、
AST 解析でソースコードを抽出。3条件の入力形式を JSONL で出力する。

条件:
  A: CCL テキストのみ (raw CCL) — 既存 _ccl.jsonl と同等だが統一形式
  B: Code + CCL 並置 (両方の情報)
  D: Code のみ (ソースコード)

Usage:
  python phase_c_enrich.py
  python phase_c_enrich.py --dry-run   # 抽出テストのみ
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).parent
_HGK_ROOT = _SCRIPT_DIR.parent.parent.parent.parent

# Windows → Linux パス変換
WIN_PREFIX = "C:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/"
LINUX_PREFIX = str(_HGK_ROOT) + "/"


def win_to_linux(win_path: str) -> str:
    return win_path.replace("\\", "/").replace(WIN_PREFIX, LINUX_PREFIX)


def extract_function_source(file_path: str, func_name: str, line_hint: int = 0) -> str | None:
    """AST で関数ソースを抽出。line_hint があれば位置ヒントとして使う。"""
    try:
        source = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return None

    candidates = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == func_name:
                candidates.append(node)

    if not candidates:
        return None

    # line_hint に最も近いものを選択
    if line_hint > 0 and len(candidates) > 1:
        candidates.sort(key=lambda n: abs(n.lineno - line_hint))

    node = candidates[0]
    lines = source.splitlines()
    end = node.end_lineno or (node.lineno + 20)
    return "\n".join(lines[node.lineno - 1 : end])


def parse_func_ref(func_ref: str) -> tuple[str, str]:
    """'file_path::func_name' を分解。"""
    parts = func_ref.rsplit("::", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return func_ref, ""


def enrich_pairs(input_jsonl: Path, dry_run: bool = False) -> tuple[list[dict], int, int]:
    """既存 JSONL を読み、ソースコードを注入。"""
    records = []
    with open(input_jsonl, encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))

    enriched = []
    ok = 0
    fail = 0

    for i, rec in enumerate(records):
        meta = rec.get("metadata", {})
        func_a_ref = meta.get("func_a", "")
        func_b_ref = meta.get("func_b", "")

        file_a, name_a = parse_func_ref(func_a_ref)
        file_b, name_b = parse_func_ref(func_b_ref)

        path_a = win_to_linux(file_a)
        path_b = win_to_linux(file_b)

        src_a = extract_function_source(path_a, name_a)
        src_b = extract_function_source(path_b, name_b)

        if src_a and src_b:
            ok += 1
        else:
            fail += 1
            if fail <= 5:
                print(f"  WARN [{i}]: src_a={'OK' if src_a else 'FAIL'} src_b={'OK' if src_b else 'FAIL'} "
                      f"— {name_a} / {name_b}")

        # CCL は既存 _ccl.jsonl から取るか、metadata から復元
        ccl_a = meta.get("anchor_ccl", "")
        ccl_b = meta.get("candidate_ccl", "")

        enriched.append({
            "source_a": src_a or "",
            "source_b": src_b or "",
            "ccl_a": ccl_a,
            "ccl_b": ccl_b,
            "label": rec["label"],
            "cosine_49d": rec["cosine_49d"],
            "pair_type": rec["pair_type"],
            "pair_id": meta.get("pair_id", f"PC_{i:05d}"),
            "has_source": bool(src_a and src_b),
        })

    return enriched, ok, fail


def write_condition_jsonl(enriched: list[dict], output_dir: Path) -> None:
    """A/B/D 3条件の JSONL を出力。"""
    # ソースコードがあるペアのみ使用 (B/D 条件用)
    with_source = [e for e in enriched if e["has_source"]]

    # 条件 A: CCL のみ (全ペア使用)
    path_a = output_dir / "phase_c_condition_A.jsonl"
    with open(path_a, "w", encoding="utf-8") as f:
        for e in enriched:
            rec = {
                "text_a": e["ccl_a"],
                "text_b": e["ccl_b"],
                "label": e["label"],
                "cosine_49d": e["cosine_49d"],
                "pair_type": e["pair_type"],
                "condition": "A_ccl",
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  A (raw CCL):     {path_a.name} — {len(enriched)} pairs")

    # 条件 B: Code + CCL 並置 (ソースありのみ)
    path_b = output_dir / "phase_c_condition_B.jsonl"
    with open(path_b, "w", encoding="utf-8") as f:
        for e in with_source:
            rec = {
                "text_a": f"### Code\n{e['source_a']}\n\n### CCL\n{e['ccl_a']}",
                "text_b": f"### Code\n{e['source_b']}\n\n### CCL\n{e['ccl_b']}",
                "label": e["label"],
                "cosine_49d": e["cosine_49d"],
                "pair_type": e["pair_type"],
                "condition": "B_code_ccl",
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  B (Code+CCL):    {path_b.name} — {len(with_source)} pairs")

    # 条件 D: Code のみ (ソースありのみ)
    path_d = output_dir / "phase_c_condition_D.jsonl"
    with open(path_d, "w", encoding="utf-8") as f:
        for e in with_source:
            rec = {
                "text_a": e["source_a"],
                "text_b": e["source_b"],
                "label": e["label"],
                "cosine_49d": e["cosine_49d"],
                "pair_type": e["pair_type"],
                "condition": "D_code",
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  D (Code only):   {path_d.name} — {len(with_source)} pairs")


def write_full_ccl_jsonl(enriched: list[dict], ccl_jsonl: Path, output_dir: Path) -> None:
    """条件 A 用: 既存 _ccl.jsonl のフル CCL を使った JSONL (metadata の truncated CCL ではなく)。"""
    ccl_records = []
    with open(ccl_jsonl, encoding="utf-8") as f:
        for line in f:
            ccl_records.append(json.loads(line))

    if len(ccl_records) != len(enriched):
        print(f"  WARN: ccl_jsonl ({len(ccl_records)}) != enriched ({len(enriched)}), using metadata CCL")
        return

    path_a_full = output_dir / "phase_c_condition_A_full.jsonl"
    with open(path_a_full, "w", encoding="utf-8") as f:
        for ccl_rec, e in zip(ccl_records, enriched):
            rec = {
                "text_a": ccl_rec["anchor_ccl"],
                "text_b": ccl_rec["candidate_ccl"],
                "label": e["label"],
                "cosine_49d": e["cosine_49d"],
                "pair_type": e["pair_type"],
                "condition": "A_ccl_full",
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  A-full (raw CCL): {path_a_full.name} — {len(ccl_records)} pairs (untruncated)")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase C data enrichment")
    parser.add_argument("--dry-run", action="store_true", help="抽出テストのみ")
    args = parser.parse_args()

    input_jsonl = _SCRIPT_DIR / "phase_c_training.jsonl"
    ccl_jsonl = _SCRIPT_DIR / "phase_c_training_ccl.jsonl"

    if not input_jsonl.exists():
        print(f"❌ {input_jsonl} not found")
        sys.exit(1)

    print(f"📂 入力: {input_jsonl}")
    enriched, ok, fail = enrich_pairs(input_jsonl)
    print(f"📊 ソースコード抽出: {ok}/{ok+fail} ({ok/(ok+fail)*100:.1f}%)")
    print(f"   (失敗 {fail} 件は B/D 条件から除外)")

    if args.dry_run:
        print("\n🔍 Dry run — JSONL 出力スキップ")
        return

    print(f"\n💾 3条件 JSONL 生成:")
    write_condition_jsonl(enriched, _SCRIPT_DIR)
    write_full_ccl_jsonl(enriched, ccl_jsonl, _SCRIPT_DIR)

    print(f"\n✅ 生成完了 — 次のステップ:")
    print(f"  phase_c_v3.py --condition A --data phase_c_condition_A_full.jsonl")
    print(f"  phase_c_v3.py --condition B --data phase_c_condition_B.jsonl")
    print(f"  phase_c_v3.py --condition D --data phase_c_condition_D.jsonl")


if __name__ == "__main__":
    main()
