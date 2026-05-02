---
doc_id: "DIFFUSION_COGNITION"
version: "1.0.0"
tier: "KERNEL"
status: "DRAFT"
created: "2026-02-23"
updated: "2026-02-23"
lineage: "Creator 洞察 (2026-02-23) + /ccl-nous による kalon 判定"
---

> **Kernel Doc Index**: [axiom_hierarchy](axiom_hierarchy.md) | [search_cognition](search_cognition.md) | [diffusion_cognition](diffusion_cognition.md) ← 📍 | [kalon](kalon.md)

# 拡散認知モデル (Diffusion Cognition Model) v1.0

> **「散らばったエントロピーが吸い込まれるように1点に戻っていく」**
> — Creator, 2026-02-23

---

## §0 一語定義

**拡散認知**: HGK の全認知プロセスを、拡散モデル (Diffusion Model) の
順拡散 (ノイズ付加) / 逆拡散 (デノイジング) として統一的に記述する計算的枠組み。

> **Kalon 判定**: ◎ — G³ で FEP (A0) 帰着、F で 11 導出。Fix(G∘F) に到達。
> (kalon.md §6 の 3 ステップ判定を 2026-02-23 /ccl-nous で完遂)

---

## §1 FEP からの導出

### 拡散モデルの数学的核心

```
順拡散: q(x_t | x_{t-1}) = N(x_t; √(1-β_t) x_{t-1}, β_t I)    (ノイズ付加)
逆拡散: p_θ(x_{t-1} | x_t) = N(x_{t-1}; μ_θ(x_t, t), Σ_θ(x_t, t))  (デノイジング)
```

### FEP との同型

FEP の核心: **変分自由エネルギー (VFE) 最小化** = 予測誤差の最小化

| 拡散モデル | FEP | 根拠 |
|:----------|:----|:-----|
| **逆拡散** (ノイズ除去) | **VFE 最小化** (予測誤差低減) | 共にエントロピーを低減する最適化 |
| **順拡散** (ノイズ付加) | **EFE 最小化** (情報探索) | 共にエントロピーを一時的に増大させて探索空間を広げる |
| **β_t** (ノイズ率) | **1/π** (Precision の逆数) | β↑ = ノイズ↑ = 不確実性↑ = π↓ |
| **Score ∇log p(x_t)** | **予測誤差の勾配** | 「目標への方向」を示す信号 |
| **x₀** (元データ) | **Goal / 真の世界像** | 復元すべき信号 |
| **x_T** (純粋ノイズ) | **Raw 未構造化入力** | 最大エントロピー状態 |

### 数学的対応: Precision = 1/β

HGK の Precision 座標 (axiom_hierarchy.md, d=1):

```
π = V[ε]⁻¹    (予測誤差の逆分散)
```

拡散モデルの β:

```
β_t = ノイズの分散    (timestep t での付加ノイズ)
```

したがって:

```
π_t = 1/β_t
```

**Precision が高い (C: 確信) = β が小さい (ノイズが少ない) = 逆拡散の後半ステップ**
**Precision が低い (U: 留保) = β が大きい (ノイズが多い) = 逆拡散の前半ステップ / 順拡散**

---

## §2 HGK 認知プロセスの拡散写像

### 収束 = 逆拡散 (Reverse Diffusion)

| 動詞 | 族 | 拡散モデル写像 | 操作 |
|:-----|:---|:-------------|:-----|
| **Noēsis** /noe | Telos | 深いデノイジング (多ステップ) | 散乱情報 → 1つの洞察 |
| **Synagōgē** /sag | Methodos | 仮説空間のデノイジング | 複数仮説 → 最適構造 |
| **Katalēpsis** /kat | Krisis | 最終デノイジングステップ | 不確実性 → 確信 (Fix) |
| **Analysis** /lys | Diástasis | 局所的デノイジング | 局所のノイズを除去 |
| **Bebaiōsis** /beb | Orexis | 信念強化デノイジング | 信念の揺らぎを除去 |
| **Tekhnē** /tek | Methodos | 既知パターンの適用 | 学習済みデノイザで即座に収束 |

### 拡散 = 順拡散 (Forward Diffusion)

| 動詞 | 族 | 拡散モデル写像 | 操作 |
|:-----|:---|:-------------|:-----|
| **Skepsis** /ske | Methodos | 構造化されたノイズ付加 | 前提を段階的に破壊 |
| **Zētēsis** /zet | Telos | 探索的ノイズ付加 | 問いの空間を拡大 |
| **Epochē** /epo | Krisis | ノイズレベルの固定 | 判断停止 (β を一定に保つ) |
| **Peira** /pei | Methodos | 実験的ノイズ注入 | 未知領域の情報収集 |
| **Elenchos** /ele | Orexis | 信念破壊のノイズ | 確信を揺さぶる |

### 位相反転 (Phase Inversion)

> **Creator の洞察**: 逆拡散の手続きを「反転」すると拡散思考そのもの。

```
逆拡散: x_T (ノイズ) → x_0 (構造)     ε_θ(x_t, t) でノイズを推定・除去
位相反転 ↕
順拡散: x_0 (構造) → x_T (ノイズ)     β スケジュールで構造的にノイズを付加
```

HGK での位相反転:

| 逆拡散 (収束) | 位相反転 | 順拡散 (拡散) |
|:-------------|:---------|:-------------|
| /noe (直観に至る) | ↔ | /ske (前提を壊す) |
| /sag (統合する) | ↔ | /zet (問いを広げる) |
| /kat (確信する) | ↔ | /epo (判断を開く) |
| /beb (肯定する) | ↔ | /ele (問い直す) |
| /tek (既知を適用) | ↔ | /pei (未知を実験) |

**これは Methodos 族の Explore↔Exploit 対そのもの。**
axiom_hierarchy.md の12随伴ペア (D-pair) の位相反転が、拡散/逆拡散の反転に対応する。

---

## §3 CCL 演算子の拡散モデル解釈

| CCL 演算子 | 意味 | 拡散モデル対応 |
|:----------|:-----|:-------------|
| `~` (振動) | 確率的な揺らぎを許容した往復 | **DDPM** (stochastic sampling) — ランダム性を保持 |
| `~*` (収束) | 収束を保証する往復 | **DDIM** (deterministic sampling) — 決定論的収束 |
| `+` 派生 | 深い処理 (L3) | **高解像度** — β が小さい、精密なステップ |
| `-` 派生 | 浅い処理 (L1) | **低解像度** — β が大きい、荒いステップのスキップ |
| `*` 派生 | 臨界点を超える | **Classifier guidance** — 条件付き生成 |
| `^` 派生 | メタ・自己参照的 | **Score function** — ∇log p(x) の方向検出 |
| `>>` (シーケンス) | 逐次実行 | **Denoising step t→t-1** — 1ステップずつ進行 |
| `F:[×N]{}` (反復) | N回ループ | **Total denoising steps = N** |

### 深度レベル = Noise Schedule

| 深度レベル | β の大きさ | ステップ数 | 認知の質 |
|:---------|:---------|:---------|:---------|
| **L0** (Bypass) | 最大 (βを使わない) | 0 (スキップ) | 入力をそのまま通過 |
| **L1** (Quick) | 大 | 少ない | 荒いが高速 |
| **L2** (Standard) | 中 | 標準 | バランス |
| **L3** (Deep) | 小 | 多い | 精密だが低速 |

これは拡散モデルの **inference step count** と完全に対応する。
DDPM で 1000 ステップを回すか、DDIM で 50 ステップに短縮するか — L3 vs L1 と同じ選択。

---

## §4 Periskopē への具体射影

> 詳細は [ビジョン.md](../mekhane/periskope/ビジョン.md) §6 を参照。

検索パイプラインにおける拡散認知:

```
Phase 0  (Φ1-Φ4): 問い生成   = 順拡散 → 逆拡散 (問いの空間を広げてから絞る)
Phase 1  (Φ5-Φ6): 検索実行   = 新しいデータの取得 (観測)
Phase 2  (合成):   知識統合   = 逆拡散 (散乱結果 → 構造化された合成)
Phase 2.5 (反復):  CoT Chain  = 反復的デノイジング (各 iteration が 1 step)
Phase 3  (検証):   引用検証   = Score function (合成の方向が正しいか検証)
Phase 4  (Φ7):    信念更新   = 最終デノイジングステップ → Fix(G∘F) 候補
```

### 反復パイプラインのデノイジングスケジューラ (提案)

> **実装状況**: L1 (Periskopē) — ✅ 実装済 (2026-02-23)

検索パイプラインにおける拡散認知:

```
Phase 0  (Φ1-Φ4): 問い生成   = 順拡散 → 逆拡散 (問いの空間を広げてから絞る)
Phase 1  (Φ5-Φ6): 検索実行   = 新しいデータの取得 (観測)
Phase 2  (合成):   知識統合   = 逆拡散 (散乱結果 → 構造化された合成)
Phase 2.5 (反復):  CoT Chain  = 反復的デノイジング (各 iteration が 1 step)
Phase 3  (検証):   引用検証   = Score function (合成の方向が正しいか検証)
Phase 4  (Φ7):    信念更新   = 最終デノイジングステップ → Fix(G∘F) 候補
```

### 反復パイプラインのデノイジングスケジューラ (実装済)

> 実装: `engine.py` `_phase_iterative_deepen()` Step 6.5

```python
# engine.py: _phase_iterative_deepen 内 (実装済コード v3 — multi-schedule)
for iteration in range(max_iterations):
    t = iteration / max(1, max_iterations - 1)  # 0.0 → 1.0
    
    # ① β スケジューラ: 探索幅を段階的に狭める (config: decay_type)
    if decay_type == "cosine":
        decay = 0.5 * (1 + cos(π * t))               # 1.0 → 0.0 (slow-fast-slow)
    elif decay_type == "logsnr":
        decay = exp(-|2t - 1| / b)                     # t=0.5 に密度集中 (Laplace)
    elif decay_type == "exponential":
        decay = exp(-3.0 * t)                           # 快速減衰
    else:  # linear
        decay = 1.0 - t                                 # 線形減衰
    diversity_weight = initial_diversity * decay
    max_results = final + (initial - final) * decay
    
    # ② ε_θ (ノイズ推定): 既存の gap_analyzer
    gaps = analyze_iteration(trace, synthesis)
    
    # ③ 矛盾駆動クエリ注入 (L3 のみ, 0.2 < t < 0.8)
    # analyze_iteration が検出した contradictions を次の反復に注入
    if depth >= 3 and gaps.contradictions and 0.2 < t < 0.8:
        fix_queries = [f"resolve: {c}" for c in gaps.contradictions[:2]]
        extra_results = search(fix_queries)
    
    # ④ 検索実行 + 再合成
    results = search(gaps.next_queries)
    synthesis = re_synthesize(query, results)
    
    # ⑤ info_gain (新規性)
    info_gain = assess_information_gain(prev, synthesis)
    
    # ⑥ Score function: precision-weighted (FEP π-weighting)
    query_relevance = embedder.similarity(query, synthesis)
    # α schedule: explore/exploit バランス (config: alpha_schedule, β とは独立)
    if alpha_schedule == "sigmoid":
        alpha = 0.15 + 0.70 / (1 + exp(-8(t - 0.5)))   # 非対称: 0.15 → 0.85
    elif alpha_schedule == "linear":
        alpha = 0.3 + 0.4 * t                           # 線形: 0.3 → 0.7
    else:  # cosine (default)
        alpha = 0.3 + 0.4 * (1 - cos(π * t)) / 2       # 対称: 0.3 → 0.7
    conf = reasoning_step.confidence              # precision proxy
    denoising_score = alpha * relevance * conf + (1 - alpha) * info_gain
    
    # ⑦ 収束判定 (info_gain < threshold)
    if info_gain < saturation_threshold:
        break  # Fix(G∘F) 到達
```

---

## §5 開放問題と反証条件

### 反証条件 (Falsifiability)

この理論は以下の条件で反証される:

1. **Φ ON/OFF の A/B テストで品質差がない**: 認知層が不要ならデノイジングステップに意味がない
2. **反復回数と品質に相関がない**: デノイジングの基本予測に反する
3. **Precision と β が統計的に無相関**: 数学的対応が偶然に過ぎない

### 開放問題

| 問題 | 状態 | 備考 |
|:-----|:-----|:-----|
| 認知空間での ∇log p は定義可能か？ | ✅ 操作的に定義 | 3072d 埋め込み空間での `similarity()` が勾配のアナロジー。実測 relevance=0.8784 |
| 順拡散の β スケジュール最適形は？ | ✅ 実装済 | cosine / logsnr / exponential / linear の 4種。benchmark 比較は未実施 |
| CCL `~` = DDPM は厳密か？ | ⚠️ アナロジー | 操作的類似性のみ。数学的証明なし |
| Classifier-free guidance の認知的対応は？ | ⚠️ 構想段階 | `/dia` (classifier) + `divergence` (negative signal) |
| 拡散認知は Markov-Kalon と整合するか？ | ⚠️ 未検証 | markov_kalon.md との接続が必要 |

### §5.1 次の改良候補 (/ccl-nous 2026-02-23 による深掘り)

| # | 改良 | 理論的対応 | 投資対効果 | 確信度 |
|:--|:-----|:----------|:----------|:-------|
| 1 | **Confidence-weighted score** | FEP precision-weighting | ✅ 実装済 | [確信: 90%] |
| 2 | **軌跡形状 SNR 推定** | gain_history のモノトーン性 = 収束品質 | ★★ 中 | [推定: 70%] (理論に留める) |
| 3 | **Negative term** (divergence) | Classifier-free guidance | ★ 低 (将来) | [仮説: 55%] |

#### 改良 1: Confidence-weighted Score

現在: `score = α × relevance + (1-α) × gain`
提案: `score = α × relevance × confidence + (1-α) × gain`

> **FEP 的根拠**: 確信が低い (π↓) ときは感覚入力 (gain) に依存し、
> 確信が高い (π↑) ときは予測 (relevance) に依存する。
> これは precision-weighting そのもの。

#### 改良 2: 軌跡形状分析 (SNR 推定)

```
gain_history = [g₁, g₂, ..., gₙ]
モノトーン減少 → 健全な収束 (高 SNR)
振動        → 不安定 (低 SNR)
増加に転じる  → 新情報源の発見 (方向転換の兆候)
```

#### 改良 3: Negative Term (将来)

`score = α × relevance + (1-α) × gain - γ × divergence`

> HGK の既存概念との対応: `/ske` = negative direction, `/dia` = classifier,
> `divergence` (合成の不一致) = implicit negative signal

---

## §6 起源

```
発見日: 2026-02-23
発見者: Creator + Claude (F⊣G 共創)
プロセス: 
  1. Periskopē /fit+ 検証 → 商用 Deep Research との比較
  2. Creator の洞察「逆拡散モデルのように収束する検索」
  3. /ccl-nous で kalon 判定 (◎)
  4. Creator の拡大「収束/拡散思考も同じでは？ 位相反転は？」
  5. /ccl-nous Round 2 で認知全体への拡大を検証
Kalon 判定: ◎ (G³で FEP 帰着、F で 11+ 導出)
```

---

## §7 参照

- [axiom_hierarchy.md](axiom_hierarchy.md) — Function 座標 (Explore↔Exploit), Precision 座標 (C↔U)
- [search_cognition.md](search_cognition.md) — Φ1-Φ7 の認知フロー
- [kalon.md](kalon.md) — Fix(G∘F) 不動点判定
- [fep_epistemic_status.md](fep_epistemic_status.md) — FEP の認識論的地位
- [ビジョン.md](../mekhane/periskope/ビジョン.md) — Periskopē への具体射影

---

*kernel/diffusion_cognition.md v1.0 — 拡散認知モデル (2026-02-23)*
*「散らばったエントロピーが吸い込まれるように1点に戻っていく」*
