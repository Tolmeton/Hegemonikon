# Euporia × Hyphē 融合 — 新規 AY タスク (2026-03-29)

> **起源**: Euporia ⇔ Hyphē 連携明示 (commit f1981e246) で地図が描けたことにより、
> 3本の未踏の道 (AY > 0) が構造的に現れた。
>
> **前提 SOURCE**:
> - [euporia.md §7.5](euporia.md) — 3ドメイン定義 + Hyphē 実験統合 (v0.8.0)
> - [THEORY.md](../../../60_実験｜Peira/06_Hyphē実験｜HyphePoC/THEORY.md) — 溶媒メタファー, ker(G), ZCA
> - [B_polynomial_linkage.md §6](B_polynomial_linkage.md) — Polynomial ↔ Hyphē 対応
> - [euporia_blindspots.md](euporia_blindspots.md) — C1'.2 射の不在 + ker(G) 進捗

---

## AY-1: ker(G) の突破 — 「溶かせない座標を溶かす」

**現状**: ker(G) = {Scale, Valence}。embedding は Scale と Valence を溶かせない (THEORY.md §3)。
**根拠**: FIM 分析 k_eff_90 = 33/3072、ZCA は等方性回復に有効だが ker(G) 解消には無力。

| タスク | 内容 | AY (新しい行為可能性) | コスト |
|:-------|:-----|:---------------------|:-------|
| **task_type 実験** | Gemini embedding の `task_type=CLASSIFICATION` を試す | 教師信号なしで ker(G) 次元が開くか検証 | **最低** (API 1行) |
| **Valence-aware fine-tuning** | Contrastive loss で肯定/否定チャンクを区別する embedding 学習 | Linkage×Valence 🕳️ 解消 → 反証情報の自動提示 | 中 (学習データ + GPU) |
| **階層的 embedding** | チャンク + セクション + 全体の3階層 embedding | Scale が溶ける → ディレクトリ体系の意味的整合性チェック | 中 (設計 + 実装) |

**理論的射程**: ker(G) 縮小 → Polynomial Functor の方向集合 B_i が豊かになる → 各チャンクから出る射の種類が増える (意味的類似だけでなく、対立・階層方向)。

**優先度**: ★★★ (即効性 高, 理論的射程 高)
**状態**: 未着手

---

## AY-2: Coherence Invariance の他ドメインへの転用

**現状**: G∘F の merge/split が Coherence を τ 非依存にする — Linkage で 130+ 実験で実証済み (range = 0.008)。
**問い**: これは Linkage 固有か、G∘F 随伴一般の性質か？

| タスク | 内容 | AY (新しい行為可能性) | コスト |
|:-------|:-----|:---------------------|:-------|
| **Cognition ドメインへの G∘F 転用** | WF 品質 (AY\|_{Cognition}) に G∘F 正規化が効くか | 深度 (L0-L3) に対し品質が深度非依存に | 高 (理論整備が先) |
| **Description ドメインへの G∘F 転用** | Týpos の merge/split でプロンプト品質を正規化 | プロンプト粒度非依存の品質保証 | 高 |
| **論文化**: Coherence Invariance 定理 | G∘F の普遍的性質として証明 | HGK の新定理。Kalon = Fix(G∘F) が「品質の粒度非依存性」を保証 | 高 (圏論的証明) |

**理論的射程**: **最高**。Coherence τ-invariance が G∘F 一般の性質なら、Euporía 全体が「AY は制御パラメータに対して堅牢」という強い主張を持てる。

**優先度**: ★★☆ (即効性 低, 理論的射程 最高)
**状態**: **着手中** (2026-03-29) — Paper VI 骨子 v0.1 完成。核心命題「忘却 (G) が行為可能性 (AY) を増大させる」。
**成果物**: [paper_VI_draft.md](../12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/paper_VI_draft.md), [linkage_crystallization.md](../11_統一索引｜UnifiedIndex/linkage_crystallization.md)

---

## AY-3: AY の定量的測定 — Polynomial Functor × Hyphē の合流

**現状**: Euporia は AY > 0 を定性的に要求。Hyphē は coherence / drift を定量的に測定。両者が定量的に接続されていない。
**橋脚**: `compute_ay.py` が HyphePoC に既存。euporia_sub.py が 6射影スコアリングを実装済み。

| タスク | 内容 | AY (新しい行為可能性) | コスト |
|:-------|:-----|:---------------------|:-------|
| **AY\|_{Linkage} の定量化** | `|Act_1(c)| - |Act_0(c)|` を Hyphē チャンク連動差として実際に計算 | AY が数値になる → 認知操作の価値を定量比較可能に | **低** (compute_ay.py 拡張) |
| **euporia_sub × phantasia 接続** | WF 実行のたびに AY\|_{Linkage} をリアルタイム計算 | 認知操作の価値が即座にフィードバック。N-7 の定量的基盤 | 中 (パイプライン接続) |
| **3ドメイン AY テンソル** | compute_ay を Cognition / Description にも適用 | 3D × 6座標 = 18次元の AY テンソル → EFE の実験的検証 | 高 (3ドメイン設計) |

**理論的射程**: AY が定量的になれば、Euporía は定性的公理 → AY 最適化問題に進化。EFE (epistemic + pragmatic) 分解の実験的検証が可能に。

**優先度**: ★★★ (即効性 最高, 理論的射程 中)
**状態**: **着手中** (2026-03-29)

---

## 実行順序

```
AY-3 (定量化) ──→ AY-1 (ker(G) 突破) ──→ AY-2 (他ドメイン転用)
  今日着手          次回                    論文候補
```

AY-3 の定量化基盤があれば、AY-1 の ker(G) 突破の効果を「AY が何ポイント増えたか」で測定できる。AY-2 は AY-3 + AY-1 の結果が他ドメインでも再現するかという問い。

---

*Created: 2026-03-29 | PJ Owner: Creator + Claude | Parent: PJ-07 Euporía*
