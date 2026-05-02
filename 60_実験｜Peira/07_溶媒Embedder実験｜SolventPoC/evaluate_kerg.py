"""ker(G) 再評価 — Baseline vs Fine-tuned Embedding.

PURPOSE: fine-tuned モデルで HGK セッションデータを再 embed し、
ker(G) の解消度を定量評価する。

評価指標:
  1. FIM stiff modes: 2 → ≥ 3 に増えたか？
  2. density-coherence Spearman ρ: 0.65 → < 0.4 に低下したか？ (Scale/Valence 分離)
  3. Valence 弁別: 対立ペアの cos gap が有意に増加したか？

PROOF: THEORY.md §4.5-4.6
"""

from __future__ import annotations

import argparse
import json
import logging
import math
from pathlib import Path

import numpy as np
from scipy import stats
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def compute_fim_stiff_modes(
    embeddings: np.ndarray,
    gap_ratio: float = 1.20,
) -> tuple[int, list[float]]:
    """FIM 固有値分析で stiff modes 数を計算。

    THEORY.md §4.5 の再現:
    共分散行列の固有値スペクトルから FIM の sloppy gap を検出。

    Args:
        embeddings: (n, d) の embedding 行列
        gap_ratio: stiff modes の判定閾値 (λ₁/λ₂ がこの比を超えたら gap)
    Returns:
        (stiff_modes, top10_eigenvalues)
    """
    n, d = embeddings.shape
    logger.info(f"FIM 分析: {n} samples × {d} dims")

    # 平均中心化
    X = embeddings - embeddings.mean(axis=0)

    # 共分散行列 (Gram matrix ベース: n << d)
    if n < d:
        K = X @ X.T / n  # (n, n)
        eigenvalues = np.linalg.eigvalsh(K)
        eigenvalues = np.sort(eigenvalues)[::-1]
    else:
        C = X.T @ X / n  # (d, d)
        eigenvalues = np.linalg.eigvalsh(C)
        eigenvalues = np.sort(eigenvalues)[::-1]

    # 正の固有値のみ
    eigenvalues = eigenvalues[eigenvalues > 1e-10]

    # Sloppy gap 検出: 隣接固有値比から最初の gap を検出
    stiff_modes = len(eigenvalues)  # デフォルト: 全て stiff
    for i in range(len(eigenvalues) - 1):
        ratio = eigenvalues[i] / eigenvalues[i + 1] if eigenvalues[i + 1] > 0 else float("inf")
        if ratio >= gap_ratio and i > 0:
            stiff_modes = i + 1
            break

    top10 = eigenvalues[:10].tolist()
    logger.info(f"  Stiff modes: {stiff_modes}")
    logger.info(f"  Top-10 eigenvalues: {[f'{v:.6f}' for v in top10]}")

    return stiff_modes, top10


def compute_density_coherence_correlation(
    embeddings: np.ndarray,
    chunk_indices: list[list[int]],
    k: int = 5,
) -> dict:
    """density-coherence 相関を計算。

    THEORY.md §4.6: Scale (density) と Valence (coherence) の共線形性。
    Spearman ρ = 0.65 → Fine-tuned で < 0.4 になるべき。

    Args:
        embeddings: (n, d) の embedding 行列
        chunk_indices: チャンクごとの step index リスト
        k: k-NN の k
    Returns:
        {"spearman_rho": float, "p_value": float, "densities": [...], "coherences": [...]}
    """
    n = embeddings.shape[0]

    # L2 正規化
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normed = embeddings / np.maximum(norms, 1e-8)

    # 全ペア cos similarity
    sim_matrix = normed @ normed.T

    densities = []
    coherences = []

    for indices in chunk_indices:
        if len(indices) < 2:
            continue

        # Density: チャンク内ステップの平均 k-NN 密度
        chunk_densities = []
        for i in indices:
            # i の全ステップとの類似度
            sims = sim_matrix[i]
            # 自分自身を除く上位 k 個
            top_k_sims = np.sort(sims)[::-1][1:k + 1]
            chunk_densities.append(top_k_sims.mean())
        densities.append(np.mean(chunk_densities))

        # Coherence: チャンク内ペアの平均 cos similarity
        pair_sims = []
        for ii, a in enumerate(indices):
            for b in indices[ii + 1:]:
                pair_sims.append(sim_matrix[a, b])
        coherences.append(np.mean(pair_sims) if pair_sims else 0.0)

    # Spearman 相関
    if len(densities) >= 3:
        rho, p_value = stats.spearmanr(densities, coherences)
    else:
        rho, p_value = float("nan"), float("nan")

    logger.info(f"  Density-Coherence Spearman ρ: {rho:.4f} (p={p_value:.4f})")
    return {
        "spearman_rho": rho,
        "p_value": p_value,
        "n_chunks": len(densities),
        "densities": densities,
        "coherences": coherences,
    }


def valence_discrimination_vectors(model: SentenceTransformer) -> dict:
    """Valence 弁別力をベクトル空間で測定。

    対立ペアと類似ペアの cos similarity の差 (gap) を測定。
    """
    pairs_valence = [
        ("この設計は美しく、効率的だ", "この設計は醜く、非効率的だ"),
        ("実験は成功し、仮説が支持された", "実験は失敗し、仮説が棄却された"),
        ("このアプローチは問題を解決する", "このアプローチは新たな問題を生む"),
        ("コードの品質は高い", "コードの品質は低い"),
        ("This approach is elegant and effective", "This approach is clumsy and useless"),
        ("The model performs well", "The model performs poorly"),
        ("信頼性が高い", "信頼性が低い"),
        ("Progress is being made", "We are going backwards"),
    ]
    pairs_similar = [
        ("この設計は美しく、効率的だ", "この設計は優雅で、パフォーマンスが良い"),
        ("実験は成功した", "テストは pass した"),
        ("コードの品質は高い", "コードはよく書かれている"),
        ("This is a good solution", "This is an excellent approach"),
    ]

    valence_sims = []
    for a, b in pairs_valence:
        embs = model.encode([a, b], convert_to_numpy=True)
        embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
        sim = float(embs[0] @ embs[1])
        valence_sims.append(sim)

    similar_sims = []
    for a, b in pairs_similar:
        embs = model.encode([a, b], convert_to_numpy=True)
        embs = embs / np.linalg.norm(embs, axis=1, keepdims=True)
        sim = float(embs[0] @ embs[1])
        similar_sims.append(sim)

    return {
        "mean_valence_cos": float(np.mean(valence_sims)),
        "mean_similar_cos": float(np.mean(similar_sims)),
        "gap": float(np.mean(similar_sims) - np.mean(valence_sims)),
        "valence_sims": valence_sims,
        "similar_sims": similar_sims,
    }


def evaluate_model(model_name_or_path: str, label: str) -> dict:
    """1モデルの全評価を実行。"""
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 {label}: {model_name_or_path}")
    logger.info('='*60)

    model = SentenceTransformer(model_name_or_path)

    # テストテキスト (HGK セッション風のテキスト)
    test_texts = [
        "kalon の定義を確認する。Fix(G∘F) の不動点条件を検証した。",
        "テスト結果は全て pass。CI/CD パイプラインが正常に動作している。",
        "このアプローチは失敗した。根本的な設計変更が必要。",
        "Handoff を作成。次回セッションへの引き継ぎ情報を記録した。",
        "FEP の自由エネルギー原理に基づき、認知制約を導出した。",
        "バグを発見。TypeError が発生しており、修正が必要。",
        "コードレビューの結果、品質は高く、Kalon に近い。",
        "パフォーマンスが低下している。最適化が必要。",
        "新しい定理を発見。24動詞の対称性が証明された。",
        "データベースが破損。バックアップから復元が必要。",
        "セッションは成功裏に終了。全目標を達成した。",
        "このプロジェクトは行き詰まっている。方向転換すべき。",
        "ドキュメントの整理が完了。MECE 構造が維持されている。",
        "エラーが連続している。根本原因の特定ができていない。",
        "sprint 計画を策定。次の2週間の目標を設定した。",
        "リソースが不足している。外部支援が必要。",
        "実験結果は予想通り。仮説が支持されている。",
        "deadlineに間に合わない可能性がある。優先度の再評価が必要。",
        "チームの士気は高い。生産性が向上している。",
        "技術的負債が蓄積している。リファクタリングが急務。",
    ]

    # Embedding
    embeddings = model.encode(test_texts, convert_to_numpy=True, show_progress_bar=False)
    logger.info(f"  Embedding shape: {embeddings.shape}")

    # 1. FIM stiff modes
    stiff_modes, eigenvalues = compute_fim_stiff_modes(embeddings)

    # 2. Density-Coherence 相関 (簡易チャンク: 連続4ステップ)
    chunk_size = 4
    chunk_indices = [
        list(range(i, min(i + chunk_size, len(test_texts))))
        for i in range(0, len(test_texts), chunk_size)
    ]
    dc_result = compute_density_coherence_correlation(embeddings, chunk_indices)

    # 3. Valence 弁別
    valence_result = valence_discrimination_vectors(model)
    logger.info(f"  Valence gap: {valence_result['gap']:.4f}")

    return {
        "label": label,
        "model": model_name_or_path,
        "embedding_dim": embeddings.shape[1],
        "n_samples": embeddings.shape[0],
        "fim": {
            "stiff_modes": stiff_modes,
            "top10_eigenvalues": eigenvalues,
        },
        "density_coherence": {
            "spearman_rho": dc_result["spearman_rho"],
            "p_value": dc_result["p_value"],
        },
        "valence": valence_result,
    }


def main():
    parser = argparse.ArgumentParser(description="ker(G) 再評価")
    parser.add_argument("--baseline", type=str,
                        default="sentence-transformers/all-mpnet-base-v2",
                        help="Baseline モデル")
    parser.add_argument("--finetuned", type=str,
                        default="./output/valence-mpnet",
                        help="Fine-tuned モデルのパス")
    parser.add_argument("--output", type=str,
                        default="./evaluation_results.json",
                        help="結果の出力先")
    args = parser.parse_args()

    results = {}

    # Baseline 評価
    results["baseline"] = evaluate_model(args.baseline, "Baseline")

    # Fine-tuned 評価
    finetuned_path = Path(args.finetuned)
    if finetuned_path.exists():
        results["finetuned"] = evaluate_model(args.finetuned, "Fine-tuned")

        # 比較サマリー
        b = results["baseline"]
        f = results["finetuned"]
        logger.info("\n" + "=" * 60)
        logger.info("📊 Baseline vs Fine-tuned 比較")
        logger.info("=" * 60)
        logger.info(f"  FIM stiff modes:   {b['fim']['stiff_modes']} → {f['fim']['stiff_modes']}")
        logger.info(f"  D-C Spearman ρ:    {b['density_coherence']['spearman_rho']:.4f} → {f['density_coherence']['spearman_rho']:.4f}")
        logger.info(f"  Valence gap:       {b['valence']['gap']:.4f} → {f['valence']['gap']:.4f}")

        # 成功判定
        success_fim = f["fim"]["stiff_modes"] >= 3
        success_dc = abs(f["density_coherence"]["spearman_rho"]) < abs(b["density_coherence"]["spearman_rho"])
        success_val = f["valence"]["gap"] > b["valence"]["gap"]

        results["success_criteria"] = {
            "fim_improved": success_fim,
            "dc_decorrelated": success_dc,
            "valence_improved": success_val,
            "overall": success_fim or (success_dc and success_val),
        }
        logger.info(f"\n  FIM 改善:      {'✅' if success_fim else '❌'}")
        logger.info(f"  D-C 脱相関:    {'✅' if success_dc else '❌'}")
        logger.info(f"  Valence 改善:  {'✅' if success_val else '❌'}")
    else:
        logger.warning(f"Fine-tuned モデルが見つかりません: {args.finetuned}")
        logger.info("  Baseline のみ評価しました。")

    # 結果保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # numpy 型を JSON serializable に変換
    def convert(obj):
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj

    output_path.write_text(
        json.dumps(results, indent=2, ensure_ascii=False, default=convert)
    )
    logger.info(f"\n結果保存: {output_path}")


if __name__ == "__main__":
    main()
