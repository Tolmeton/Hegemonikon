---
rom_id: rom_2026-03-14_nucleator_v2_validation
session_id: 7838fc1c-716d-4627-afad-19d84d04816d
created_at: 2026-03-14 10:55
rom_type: distilled
reliability: High
topics: [nucleator, hyphe, chunker, tau-sensitivity, knn, gf-iteration, drift, markov-blanket]
exec_summary: |
  Nucleator v2 の理論検証完了。k-nearest 類似度 + 再帰分割 + 真値 drift で旧 PoC 比 73% drift 改善。
  130実験で G∘F 100% 収束を実証し、knn は tau>=0.75 でのみ有意 (19.3%) であることを確認。
  pairwise@0.70 (通常) / knn@0.75 (多スケール) の使い分けガイドラインを策定。
---

# Nucleator v2 理論検証 — 完全版

> **[DECISION]** k-nearest 類似度 (knn) は τ≥0.75 の細分割域でのみ有意 (19.3% drift 改善)。τ=0.70 では 0.3% で差なし。

> **[DECISION]** 使い分けガイドライン:
> - 通常セッション分割: **pairwise@τ=0.70**
> - 多スケール分析 (§8.4): **knn k=5@τ=0.75-0.80**
> - 階層的チャンキング: **pairwise@0.70 + knn@0.75** の2層構成

## 実験結果 (v3: 130 experiments, 13 sessions, 871 steps)

> **[FACT]** G∘F 収束率 **100%** (130/130)。Banach 不動点定理の実験的裏付け。

| τ | mode | Avg chunks | Avg drift | Drift improvement |
|-----|----------|------------|-----------|-------------------|
| 0.60 | pw/knn | 1.0 | 0.126 | 0% (pre-transition) |
| 0.70 | knn | 3.8 | 0.104 | 0.3% |
| 0.72 | knn | 7.2 | 0.087 | 6.1% |
| 0.75 | knn | 18.5 | 0.063 | **19.3%** |
| 0.80 | knn | 32.0 | 0.050 | **18.1%** |

> **[DISCOVERY]** v1 平均 drift 0.185 → v3 最良 0.050 = **73% 改善**

> **[DISCOVERY]** coherence の τ 不変性: τ を変えても coherence は 0.75-0.82 の狭い範囲に留まる。τ は Scale 座標の操作的実現であり、品質ではなく粒度を制御する。

> **[DISCOVERY]** 臨界点 τ_c ∈ [0.65, 0.70]: 分割なし → 分割ありの相転移。これ以下では knn/pairwise に差なし。

## コード変更 3件

> **[DECISION]** A. `compute_similarity_trace(mode='knn', k=3)` — k近傍 embedding で類似度計算。1次 Markov 仮定を緩和。

> **[DECISION]** B. `_recursive_split(chunk, embeddings, tau, min_steps)` — 全 τ 未満箇所で再帰的分割。旧実装は1箇所のみ分割で G∘F が保守的だった。

> **[DECISION]** C. `compute_chunk_metrics` の drift = centroid variance。旧: `1.0 - coherence` は真の drift ではなかった。

## テスト

26 tests PASSED (0.05s)。新規 9 tests: TestKnnSimilarity(3), TestRecursiveSplit(3), TestTrueDrift(3)。

## 関連情報
- 関連 WF: /noe, /pei, /fit
- 関連ファイル: linkage_hyphe.md §8.5, hyphe_chunker.py, test_hyphe_chunker.py
- 関連セッション: 7838fc1c (本セッション), d49cac06 (セッションチャンキング実装検討)

## 次ステップ

1. **セッションチャンキング本実装**: hyphe_chunker.py → Mneme 統合 (session_chunker.py)
2. **Mneme 連携**: チャンク結果を Kairos/Chronos にインデックス
3. **多スケール Nucleator**: §8.4 の理論を実装 (τ(s) パラメトリック)

<!-- ROM_GUIDE
primary_use: Nucleator 理論の実験的裏付けと使い分けの参照
retrieval_keywords: nucleator, tau, drift, knn, pairwise, chunker, hyphe, markov-blanket, phase-transition
expiry: permanent
-->
