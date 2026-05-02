---
rom_id: rom_2026-03-15_hyphe_v09_precision_ml
session_id: 46acb9cf-af60-4a5e-a628-376abcada7ce
created_at: 2026-03-15 14:03
rom_type: distilled
reliability: High
topics: [hyphe, precision_ml, multilayer_embedding, bge-m3, ml_weight, U字分布]
exec_summary: |
  Hyphē v0.9: bge-m3 浅↔深 cos sim ベースの precision_ml を hyphe_chunker.py に統合。
  ml_weight=0.4 が最適 (5セッション×11段階スイープ)。U字比率 40%→5%。
  67/67テスト PASSED + 実セッション E2E 検証 PASSED。
---

# Hyphē v0.9 Multilayer Precision 統合 {#sec_01_overview}

> **[DECISION]** ml_weight=0.4 をデフォルトに採用。U字分布の 87.5% 解消と k-NN の弁別力のバランスが最適。

## 設計と実装 {#sec_02_design}

> **[FACT]** precision_ml = bge-m3 Layer[1-4] (浅) ↔ Layer[21-24] (深) の cos sim → セッション内 min-max 正規化

統合 precision の式:
```
precision = ml_weight * precision_ml + (1 - ml_weight) * precision_knn
```

変更箇所:
- `Chunk` dataclass: `precision_ml: float = 0.0` 追加
- `compute_chunk_metrics`: Pass 3 (multilayer precision 計算 + 統合)
- `chunk_session`: `per_step_sims`, `ml_weight` パラメータ追加
- metrics: `mean_precision_ml`, `precision_ml_var` 追加

## ml_weight 最適値 {#sec_03_weight_sweep}

> **[DISCOVERY]** w=0.3-0.4 がスイートスポット。k-NN の弁別力 (高 var) と precision_ml のU字緩和が均衡。

| w | U-ratio | Score | 特徴 |
|---|---|---|---|
| 0.0 (knn) | 0.40 | 0.832 | U字: 40%が端に集中 |
| 0.3 | 0.10 | 0.938 | U字大幅緩和 |
| **0.4** | **0.05** | **0.940** | 🏆 ベスト |
| 0.5 | 0.05 | 0.909 | 分散やや低下 |
| 1.0 (ml) | 0.00 | 0.808 | 弁別力不足 |

品質メトリクス: 0.4×正規化エントロピー + 0.3×中央性 + 0.3×(1-U字比率)

## 実セッション検証 {#sec_04_e2e}

> **[FACT]** session_164ceafc (51 steps → 5 chunks) で全チャンク diff=0.000000

| chunk | p_knn | p_ml | 統合 p | 検証 |
|---|---|---|---|---|
| 0 | 0.00 | 0.39 | 0.20 | ✅ |
| 1 | 0.75 | 0.39 | 0.57 | ✅ |
| 3 | 1.00 | 0.58 | 0.79 | ✅ |

> **[DISCOVERY]** precision_ml は k-NN と異なるパターン: knn=0 でも ml≈0.39、knn=1.0 でも ml=0.58。統合が U字を緩和。

## 統計的基盤 (Phase 1 結果) {#sec_05_stats}

13セッション検証:
- H1 (分散 > 0.001): ✅ PASSED (p=0.006)
- H2 (k-NN と独立): ❌ FAILED (条件付き相関 mean|r|=0.54)
- H3 (range > 0.05): ✅ PASSED (p=0.0006)
- coherence 独立性: ✅ (r=-0.27, k-NN r≈0.81 より大幅改善)

## 関連情報
- 関連ファイル: `60_実験｜Peira/06_Hyphē実験｜HyphePoC/hyphe_chunker.py`
- 関連スクリプト: `run_multilayer_precision.py`
- 前提実験: whitening (ZCA), sloppy spectrum, Qwen3 比較

<!-- ROM_GUIDE
primary_use: Hyphē v0.9 の precision_ml 統合の設計根拠と検証結果の参照
retrieval_keywords: precision multilayer bge-m3 U字分布 ml_weight 最適化 浅層 深層
expiry: permanent
-->
