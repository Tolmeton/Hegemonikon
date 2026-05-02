#!/usr/bin/env python3
"""検証実験: ev の自然変換条件の proxy 検証

PURPOSE: linkage_hyphe.md §4.7.2 の自然変換条件
  q_c(f*(c')) = f*(q_c(c'))
を数値的に検証する。

理論 (ev: K^K × K → K):
  K^K の元 q = 個別ステップの embedding (クエリ「点」)
  ev(q, c) = cos_sim(q, centroid(c))
  J の射 f* の proxy = 隣接2チャンクの結合操作
    c_a, c_b → c_merged = c_a ∪ c_b

自然変換条件:
  ev(q, c_merged) ≈ w_a · ev(q, c_a) + w_b · ev(q, c_b)
  重みは各チャンクのステップ数比率。

centroid の加法的分解が近似的に成り立つことを利用:
  centroid(A∪B) ≈ (|A|·centroid(A) + |B|·centroid(B)) / (|A|+|B|)
  → cos_sim(q, centroid(A∪B)) ≈ weighted_avg(cos_sim(q, centroid(A)), cos_sim(q, centroid(B)))

検証指標:
  交換誤差: |ev(q, c_merged) - weighted_avg(ev(q, c_a), ev(q, c_b))| の全ペア平均
  交換相関: ev(q, c_merged) vs weighted_avg の Pearson 相関
  合格基準: 相関 r > 0.85 かつ 平均誤差 < 0.05

PROOF: linkage_hyphe.md §4.7.2
"""

import json
import math
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path

# パス設定
HGK_ROOT = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")
MEKHANE_SRC = HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
EXPERIMENT_DIR = HGK_ROOT / "60_実験｜Peira" / "06_Hyphē実験｜HyphePoC"
CACHE_FILE = EXPERIMENT_DIR / "embedding_cache.pkl"

sys.path.insert(0, str(MEKHANE_SRC))
sys.path.insert(0, str(EXPERIMENT_DIR))

# .env
env_file = HGK_ROOT / ".env"
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

from hyphe_chunker import (
    Step,
    _cosine_similarity,
    _l2_normalize,
    chunk_session,
    compute_similarity_trace,
    detect_boundaries,
    steps_to_chunks,
)


# ── データ型 ──────────────────────────────────────────────────────

@dataclass
class NaturalityCheck:
    """1つの (query_step, merge_pair) の自然性検証結果。"""
    session_id: str
    query_idx: int
    chunk_a_steps: list[int]
    chunk_b_steps: list[int]
    score_merged: float                 # ev(q, c_merged)
    score_weighted: float               # w_a * ev(q, c_a) + w_b * ev(q, c_b)
    score_a: float                      # ev(q, c_a)
    score_b: float                      # ev(q, c_b)
    error: float                        # |score_merged - score_weighted|
    weight_a: float
    weight_b: float


# ── ev proxy ──────────────────────────────────────────────────────

def _chunk_centroid(
    normed: list[list[float]],
    step_indices: list[int],
) -> list[float]:
    """チャンクの embedding centroid (L2正規化済み入力から計算)。"""
    if not step_indices:
        return []
    dim = len(normed[0])
    centroid = [0.0] * dim
    for idx in step_indices:
        for d in range(dim):
            centroid[d] += normed[idx][d]
    n = len(step_indices)
    centroid = [c / n for c in centroid]
    return _l2_normalize(centroid)


# ── 自然性検証 ────────────────────────────────────────────────────

def verify_naturality_merge(
    embeddings: list[list[float]],
    session_id: str,
    tau: float = 0.70,
) -> list[NaturalityCheck]:
    """隣接チャンク結合を f* proxy として自然変換条件を検証。
    
    手順:
    1. τ でチャンク化 (G∘F まで)
    2. 隣接チャンクの (c_a, c_b) ペアを列挙
    3. c_merged = c_a ∪ c_b の centroid を計算
    4. 各チャンクに属さない全ステップがクエリ候補 q
    5. ev(q, c_merged) ≈ w_a · ev(q, c_a) + w_b · ev(q, c_b) を検証
    """
    n = len(embeddings)
    if n < 6:
        return []
    
    # L2 正規化
    normed = [_l2_normalize(e) for e in embeddings]
    
    # チャンク化
    dummy_steps = [Step(index=i, text=f"s{i}") for i in range(n)]
    result = chunk_session(dummy_steps, embeddings, tau=tau)
    chunks = result.chunks
    
    if len(chunks) < 2:
        return []
    
    checks = []
    
    # 隣接チャンクペアを列挙
    for ci in range(len(chunks) - 1):
        c_a = chunks[ci]
        c_b = chunks[ci + 1]
        
        a_steps = [s.index for s in c_a.steps]
        b_steps = [s.index for s in c_b.steps]
        merged_steps = a_steps + b_steps
        merged_set = set(merged_steps)
        
        # centroid 計算
        cent_a = _chunk_centroid(normed, a_steps)
        cent_b = _chunk_centroid(normed, b_steps)
        cent_merged = _chunk_centroid(normed, merged_steps)
        
        if not cent_a or not cent_b or not cent_merged:
            continue
        
        # 重み
        total = len(a_steps) + len(b_steps)
        w_a = len(a_steps) / total
        w_b = len(b_steps) / total
        
        # このペアに属さない全ステップをクエリ候補に
        query_indices = [i for i in range(n) if i not in merged_set]
        
        for qi in query_indices:
            q = normed[qi]
            
            s_merged = _cosine_similarity(q, cent_merged)
            s_a = _cosine_similarity(q, cent_a)
            s_b = _cosine_similarity(q, cent_b)
            s_weighted = w_a * s_a + w_b * s_b
            error = abs(s_merged - s_weighted)
            
            checks.append(NaturalityCheck(
                session_id=session_id,
                query_idx=qi,
                chunk_a_steps=a_steps,
                chunk_b_steps=b_steps,
                score_merged=s_merged,
                score_weighted=s_weighted,
                score_a=s_a,
                score_b=s_b,
                error=error,
                weight_a=w_a,
                weight_b=w_b,
            ))
    
    return checks


# ── 統計分析 ──────────────────────────────────────────────────────

def analyze_results(checks: list[NaturalityCheck]) -> dict:
    """交換誤差と交換相関を計算。"""
    if not checks:
        return {"n": 0, "mean_error": 0.0, "correlation": 0.0, "r_squared": 0.0}
    
    n = len(checks)
    errors = [c.error for c in checks]
    befores = [c.score_merged for c in checks]
    afters = [c.score_weighted for c in checks]
    
    mean_error = sum(errors) / n
    max_error = max(errors)
    median_error = sorted(errors)[n // 2]
    
    # Pearson 相関
    mean_b = sum(befores) / n
    mean_a = sum(afters) / n
    
    cov = sum((b - mean_b) * (a - mean_a) for b, a in zip(befores, afters)) / n
    var_b = sum((b - mean_b) ** 2 for b in befores) / n
    var_a = sum((a - mean_a) ** 2 for a in afters) / n
    
    denom = math.sqrt(var_b * var_a)
    correlation = cov / denom if denom > 1e-12 else 0.0
    
    # R²
    ss_res = sum((b - a) ** 2 for b, a in zip(befores, afters))
    ss_tot = sum((b - mean_b) ** 2 for b in befores)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 1e-12 else 0.0
    
    # セッション別
    session_ids = sorted(set(c.session_id for c in checks))
    per_session = {}
    for sid in session_ids:
        s_checks = [c for c in checks if c.session_id == sid]
        s_errors = [c.error for c in s_checks]
        per_session[sid] = {
            "n": len(s_checks),
            "mean_error": sum(s_errors) / len(s_errors),
            "max_error": max(s_errors),
        }
    
    return {
        "n": n,
        "mean_error": mean_error,
        "median_error": median_error,
        "max_error": max_error,
        "correlation": correlation,
        "r_squared": r_squared,
        "per_session": per_session,
    }


def print_report(stats: dict, checks: list[NaturalityCheck]) -> None:
    """検証結果のレポートを出力。"""
    print("=" * 60)
    print("ev 自然変換条件 — proxy 検証結果")
    print("  f* proxy: 隣接2チャンク結合操作")
    print("=" * 60)
    
    n = stats["n"]
    print(f"\n  有効ペア数:       {n}")
    print(f"  平均交換誤差:     {stats['mean_error']:.6f}")
    print(f"  中央値交換誤差:   {stats['median_error']:.6f}")
    print(f"  最大交換誤差:     {stats['max_error']:.6f}")
    print(f"  Pearson 相関:     {stats['correlation']:.4f}")
    print(f"  R²:               {stats['r_squared']:.4f}")
    
    # 合格判定
    print(f"\n{'='*60}")
    print("合格判定:")
    print(f"{'='*60}")
    
    corr_pass = stats["correlation"] > 0.85
    err_pass = stats["mean_error"] < 0.05
    
    print(f"  相関 r > 0.85:    {'✅ PASS' if corr_pass else '❌ FAIL'} (r = {stats['correlation']:.4f})")
    print(f"  誤差 < 0.05:      {'✅ PASS' if err_pass else '❌ FAIL'} (err = {stats['mean_error']:.6f})")
    
    if corr_pass and err_pass:
        print(f"\n  → 結論: 自然変換条件は proxy レベルで成立 ✅")
        print(f"  → 確信度引き上げ根拠: [推定] 65% → 80% を支持")
    elif corr_pass or err_pass:
        print(f"\n  → 結論: 自然変換条件は部分的に成立")
        print(f"  → 確信度引き上げ根拠: [推定] 65% → 75% を支持")
    else:
        print(f"\n  → 結論: 自然変換条件は proxy レベルで不成立 ❌")
        print(f"  → 要因分析が必要")
    
    # セッション別
    if stats.get("per_session"):
        print(f"\n{'='*60}")
        print("セッション別:")
        print(f"{'='*60}")
        print(f"  {'Session':<12} {'N':>6} {'MeanErr':>11} {'MaxErr':>11}")
        print(f"  {'-'*42}")
        for sid, s in sorted(stats["per_session"].items()):
            print(f"  {sid:<12} {s['n']:>6} {s['mean_error']:>11.6f} {s['max_error']:>11.6f}")
    
    # 誤差分布
    if checks:
        errors = sorted(c.error for c in checks)
        bins = [0.001, 0.005, 0.01, 0.02, 0.05, 0.10, 1.0]
        print(f"\n  誤差分布:")
        prev = 0.0
        for b in bins:
            count = sum(1 for e in errors if prev <= e < b)
            pct = 100 * count / len(errors)
            bar = "█" * int(pct / 2)
            print(f"    [{prev:.3f}, {b:.3f}): {count:>5} ({pct:>5.1f}%) {bar}")
            prev = b


# ── メイン ────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("ev 自然変換条件 proxy 検証")
    print("q(c_merged) ≈ w_a·q(c_a) + w_b·q(c_b)")
    print("f* proxy = 隣接チャンク結合操作")
    print("=" * 60)
    
    # Phase 1: キャッシュ読み込み
    print(f"\n--- Phase 1: embedding キャッシュ ---")
    if not CACHE_FILE.exists():
        print(f"  ❌ キャッシュが存在しません: {CACHE_FILE}")
        sys.exit(1)
    
    with open(CACHE_FILE, "rb") as f:
        cache = pickle.load(f)
    print(f"  {len(cache)} sessions loaded")
    
    # Phase 2-3: 検証実行
    print(f"\n--- Phase 2: 自然変換条件の検証 ---")
    all_checks: list[NaturalityCheck] = []
    
    for session_id, data in sorted(cache.items()):
        embeddings = data["embeddings"]
        checks = verify_naturality_merge(embeddings, session_id, tau=0.70)
        all_checks.extend(checks)
        print(f"  [{session_id}] {len(checks):>4} checks ({len(embeddings)} steps)")
    
    print(f"  合計: {len(all_checks)} checks")
    
    if not all_checks:
        print(f"\n  ❌ 有効なチェックがありませんでした")
        sys.exit(1)
    
    # Phase 3: 分析
    print(f"\n--- Phase 3: 統計分析 ---")
    stats = analyze_results(all_checks)
    print_report(stats, all_checks)
    
    # JSON 保存
    output = {
        "summary": {k: v for k, v in stats.items() if k != "per_session"},
        "per_session": stats.get("per_session", {}),
        "config": {"tau": 0.70, "proxy": "adjacent_chunk_merge"},
    }
    
    output_path = EXPERIMENT_DIR / "results_ev_naturality.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n結果を {output_path.name} に保存")


if __name__ == "__main__":
    main()
