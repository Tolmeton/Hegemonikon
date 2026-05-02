#!/usr/bin/env python3
"""
Search Quality Comparison: bge-m3 vs gemini-embedding-2-preview

2つの LanceDB テーブルを同一クエリで検索し、結果の違いを比較する。

方法:
  1. knowledge.lance (gemini-embedding-2) → Vertex AI embedder でクエリ
  2. knowledge_bge_backup.lance (bge-m3) → bge-m3 embedder でクエリ
  3. 同一クエリの top-K 結果を比較:
     - Jaccard 類似度 (結果の重複率)
     - 距離分布 (精度の指標)
     - ランク相関 (順序の一致度)

Usage:
  python compare_search_quality.py
"""

import sys
import json
import time
from pathlib import Path

# .env ロード
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "Sync" / "oikos" / "01_ヘゲモニコン｜Hegemonikon" / ".env")
except ImportError:
    pass

# プロジェクトルートを追加
HGK_ROOT = Path.home() / "Sync" / "oikos" / "01_ヘゲモニコン｜Hegemonikon"
SRC_ROOT = HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(SRC_ROOT))

import lancedb
import numpy as np

# ── パス設定 ──
GNOSIS_DIR = HGK_ROOT / "30_記憶｜Mneme" / "04_知識｜Gnosis" / "00_知識基盤｜KnowledgeBase" / "lancedb"
GEMINI_DB_PATH = GNOSIS_DIR / "knowledge.lance"
BGE_DB_PATH = GNOSIS_DIR / "knowledge_bge_backup.lance"

# ── テストクエリ ──
# HGK の研究テーマに関連するクエリ。多様性を確保。
TEST_QUERIES = [
    # FEP / Active Inference
    "free energy principle active inference",
    "variational Bayesian inference predictive coding",
    # Category Theory
    "category theory adjunction functor",
    "Yoneda lemma presheaf representable",
    # Neuroscience
    "prediction error N400 P600 ERP",
    "Markov blanket neural computation",
    # Embedding / NLP
    "representation degeneration anisotropy embedding",
    "transformer attention mechanism multilingual",
    # Cognitive Science
    "metacognition feeling of knowing monitoring",
    "AuDHD executive function cognitive flexibility",
]

K = 10  # 各クエリの取得件数

def load_gemini_embedder():
    """Vertex AI (gemini-embedding-2-preview) embedder をロード"""
    from mekhane.anamnesis.vertex_embedder import VertexEmbedder
    from mekhane.anamnesis.constants import EMBED_MODEL
    return VertexEmbedder(model_name=EMBED_MODEL, dimension=3072)

def load_bge_embedder():
    """bge-m3 embedder をロード (precision_router の機構を流用)"""
    try:
        from transformers import AutoTokenizer, AutoModel
        import torch

        model_name = "BAAI/bge-m3"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModel.from_pretrained(model_name)
        model.eval()

        def embed_fn(text: str) -> list[float]:
            with torch.no_grad():
                inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                outputs = model(**inputs)
                # [CLS] トークンの最終層を使用
                vec = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
                # L2 正規化
                vec = vec / np.linalg.norm(vec)
                return vec.tolist()

        return embed_fn
    except Exception as e:
        print(f"⚠️ bge-m3 ロード失敗: {e}")
        return None


def search_lancedb(db_path: Path, table_name: str, query_vec: list[float], k: int) -> list[dict]:
    """LanceDB テーブルをベクトル検索"""
    db = lancedb.connect(str(db_path.parent))
    try:
        table = db.open_table(db_path.stem)
    except Exception:
        # テーブル名が異なる場合
        tables = db.table_names()
        if not tables:
            return []
        table = db.open_table(tables[0])

    results = table.search(query_vec).limit(k).to_list()
    return results


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard 類似度"""
    if not set_a and not set_b:
        return 1.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union) if union else 0.0


def rank_correlation(list_a: list, list_b: list) -> float:
    """簡易ランク相関: 共通要素の順位距離"""
    if not list_a or not list_b:
        return 0.0
    common = set(list_a) & set(list_b)
    if not common:
        return 0.0

    rank_a = {item: i for i, item in enumerate(list_a)}
    rank_b = {item: i for i, item in enumerate(list_b)}

    diffs = [abs(rank_a[item] - rank_b[item]) for item in common]
    max_possible = len(list_a) - 1
    if max_possible == 0:
        return 1.0
    normalized = 1.0 - (sum(diffs) / (len(diffs) * max_possible))
    return max(0.0, normalized)


def main():
    print("=" * 70)
    print("🔬 Search Quality Comparison: bge-m3 vs gemini-embedding-2-preview")
    print("=" * 70)

    # ── DB 存在確認 ──
    gemini_lance = GNOSIS_DIR
    bge_lance = GNOSIS_DIR

    print(f"\n📂 Gemini DB: {GEMINI_DB_PATH}")
    print(f"📂 BGE DB:    {BGE_DB_PATH}")

    if not GEMINI_DB_PATH.exists():
        print("❌ Gemini DB が見つかりません")
        return
    if not BGE_DB_PATH.exists():
        print("❌ BGE backup DB が見つかりません")
        return

    # ── DB の基本情報 ──
    db = lancedb.connect(str(GNOSIS_DIR))
    tables = db.table_names()
    print(f"\n📊 利用可能テーブル: {tables}")

    for tname in tables:
        t = db.open_table(tname)
        dim = None
        for field in t.schema:
            if field.name == "vector":
                import re
                m = re.search(r'\[(\d+)\]', str(field.type))
                if m:
                    dim = int(m.group(1))
        count = t.count_rows()
        print(f"  {tname}: {count:,} rows, {dim}d vectors")

    # ── Embedder ロード ──
    print("\n🔧 Embedder ロード中...")

    gemini_emb = load_gemini_embedder()
    print(f"  ✅ Gemini: {gemini_emb}")

    bge_embed_fn = load_bge_embedder()
    if bge_embed_fn:
        print(f"  ✅ BGE-M3: loaded")
    else:
        print("  ⚠️ BGE-M3 をロードできません。Gemini DB のみテスト。")

    # ── 検索テスト ──
    print(f"\n🔍 テスト実行: {len(TEST_QUERIES)} クエリ × K={K}")
    print("-" * 70)

    results_summary = []

    for i, query in enumerate(TEST_QUERIES):
        print(f"\n[{i+1}/{len(TEST_QUERIES)}] Query: \"{query}\"")

        # Gemini 検索
        t0 = time.time()
        gemini_vec = gemini_emb.embed(query)
        gemini_results = search_lancedb(GEMINI_DB_PATH, "knowledge", gemini_vec, K)
        gemini_time = time.time() - t0

        gemini_titles = [r.get("title", "?")[:60] for r in gemini_results]
        gemini_pks = [r.get("primary_key", "") for r in gemini_results]
        gemini_distances = [r.get("_distance", 0.0) for r in gemini_results]

        print(f"  Gemini ({gemini_time:.2f}s): {len(gemini_results)} results")
        for j, (title, dist) in enumerate(zip(gemini_titles[:5], gemini_distances[:5])):
            print(f"    {j+1}. [{dist:.4f}] {title}")

        # BGE 検索 (利用可能な場合)
        bge_titles = []
        bge_pks = []
        bge_distances = []
        bge_time = 0.0

        if bge_embed_fn:
            t0 = time.time()
            bge_vec = bge_embed_fn(query)
            try:
                bge_results = search_lancedb(BGE_DB_PATH, "knowledge_bge_backup", bge_vec, K)
                bge_time = time.time() - t0

                bge_titles = [r.get("title", "?")[:60] for r in bge_results]
                bge_pks = [r.get("primary_key", "") for r in bge_results]
                bge_distances = [r.get("_distance", 0.0) for r in bge_results]

                print(f"  BGE-M3 ({bge_time:.2f}s): {len(bge_results)} results")
                for j, (title, dist) in enumerate(zip(bge_titles[:5], bge_distances[:5])):
                    print(f"    {j+1}. [{dist:.4f}] {title}")
            except Exception as e:
                print(f"  ⚠️ BGE 検索失敗: {e}")

        # 比較メトリクス
        if bge_pks and gemini_pks:
            jaccard = jaccard_similarity(set(gemini_pks), set(bge_pks))
            rank_corr = rank_correlation(gemini_pks, bge_pks)
            common = set(gemini_pks) & set(bge_pks)

            print(f"  📊 Jaccard: {jaccard:.3f} | Rank Corr: {rank_corr:.3f} | Common: {len(common)}/{K}")

            results_summary.append({
                "query": query,
                "gemini_count": len(gemini_results),
                "bge_count": len(bge_pks),
                "jaccard": jaccard,
                "rank_corr": rank_corr,
                "common_count": len(common),
                "gemini_avg_dist": np.mean(gemini_distances) if gemini_distances else 0.0,
                "bge_avg_dist": np.mean(bge_distances) if bge_distances else 0.0,
                "gemini_time": gemini_time,
                "bge_time": bge_time,
            })
        else:
            results_summary.append({
                "query": query,
                "gemini_count": len(gemini_results),
                "bge_count": 0,
                "jaccard": None,
                "rank_corr": None,
                "common_count": 0,
                "gemini_avg_dist": np.mean(gemini_distances) if gemini_distances else 0.0,
                "bge_avg_dist": 0.0,
                "gemini_time": gemini_time,
                "bge_time": bge_time,
            })

    # ── 総合レポート ──
    print("\n" + "=" * 70)
    print("📋 総合レポート")
    print("=" * 70)

    has_bge = any(r["bge_count"] > 0 for r in results_summary)

    if has_bge:
        avg_jaccard = np.mean([r["jaccard"] for r in results_summary if r["jaccard"] is not None])
        avg_rank_corr = np.mean([r["rank_corr"] for r in results_summary if r["rank_corr"] is not None])
        avg_common = np.mean([r["common_count"] for r in results_summary])

        print(f"\n  平均 Jaccard 類似度:  {avg_jaccard:.3f}")
        print(f"  平均 Rank 相関:      {avg_rank_corr:.3f}")
        print(f"  平均 共通結果数:     {avg_common:.1f} / {K}")

    avg_gemini_dist = np.mean([r["gemini_avg_dist"] for r in results_summary])
    avg_bge_dist = np.mean([r["bge_avg_dist"] for r in results_summary if r["bge_avg_dist"] > 0]) if has_bge else 0.0
    avg_gemini_time = np.mean([r["gemini_time"] for r in results_summary])
    avg_bge_time = np.mean([r["bge_time"] for r in results_summary if r["bge_time"] > 0]) if has_bge else 0.0

    print(f"\n  Gemini 平均距離:     {avg_gemini_dist:.4f}")
    if has_bge:
        print(f"  BGE-M3 平均距離:     {avg_bge_dist:.4f}")
    print(f"\n  Gemini 平均速度:     {avg_gemini_time:.2f}s")
    if has_bge:
        print(f"  BGE-M3 平均速度:     {avg_bge_time:.2f}s")

    # JSON 出力
    output_path = Path(__file__).parent / "search_quality_results.json"
    with open(output_path, "w") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n📄 結果出力: {output_path}")

    print("\n✅ テスト完了")


if __name__ == "__main__":
    main()
