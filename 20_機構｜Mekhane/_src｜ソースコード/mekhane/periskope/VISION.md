# Periskopē 設計思想

> **「検索エンジンは情報を見つけるツールではなく、問いを生成する認知プロセスである。
> その認知プロセスには構造があり、その構造は FEP で記述でき、
> HGK のワークフロー体系で実行できる。」**
>
> **理論基盤**: [search_cognition.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/kernel/search_cognition.md)
> **実装**: [engine.py](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/engine.py) + [cognition/](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/__init__.py)

---

## 原則

### 1. 問い駆動 (Question-First)

> **計画 8 割、実行 2 割。**

良質な問いが良い検索を生む。問いの生成 = **予測誤差の文章化（外在化）**。
全体リソースの 8 割を問い生成プロセスに投じる。
実行中の創発的な問いの修正も含めての 8 割。

**実装**: `_phase_cognitive_expand()` — Φ1-Φ4 を検索前に実行
**計測**: `planning_ratio` として Phase 0 / total elapsed を metrics.jsonl に記録

### 2. 検索は Active Inference

検索クエリの生成 = **Expected Free Energy (EFE) の最小化**:

```
G(π) = -Epistemic Value (情報取得価値) - Pragmatic Value (目的達成価値)
```

- 良い検索クエリ = EFE を最大限に下げるアクション
- 検索結果 = 予測誤差の観測 → モデル更新 → 次の問い

**実装**: `_phase_iterative_deepen()` — 情報利得飽和で収束判定

### 3. 認知フロー (7 段階)

| 段階 | 認知活動 | FEP | HGK | 実装 | 比率 |
|:-----|:--------|:----|:----|:-----|:-----|
| ① 発見知覚 | 知識の欠落に気づく | 予測誤差検出 | O1 Noēsis | `phi1_blind_spot.py` | ████░ 80% |
| ② 拡散思考 | 問いの空間を探索 | Exploration | O3 Zētēsis | `phi2_divergent.py` | ████░ |
| ③ 収束思考 | 最良の問いに絞る | Exploitation | A2 Krisis | `phi4_convergent.py` | ████░ |
| ④ 行動準備 | 検索戦略の決定 | Policy Selection | S2 Mekhanē | `phi3_context.py` | ████░ |
| ⑤ 行動 | 検索の実行 | Active Inference | O4 Energeia | `engine._phase_search()` | █░░░ 20% |
| ⑥ 結果知覚 | 結果の評価 | PE Update | H2 Pistis | `engine._phase_cite()` | █░░░ |
| ⑦ モデル更新 | 次の問いの種 | Belief Update | H4 Doxa | `phi7_belief_update.py` | █░░░ |

⑦ → ① に戻る螺旋的深化。実行中にも ①-④ が再帰的に発火する。

**統合**: [cognition/**init**.py](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/periskope/cognition/__init__.py) — 全 Φ のエントリポイント

### 4. 圏論的構造

> ⚠️ **操作的比喩 (operational metaphor)**: 以下は厳密な圏論的構造ではなく、
> 設計思考のための構造的メタファーとして使用している。
> 詳細な分析は [search_cognition.md §3](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/kernel/search_cognition.md) を参照。

- **検索** = 問い (Q) から答え (A) への関手 (Functor)
- **多言語検索** = 言語間の自然変換 (Natural Transformation)
- **結果統合** = 余極限 (Colimit)
- **検索精錬ループ** = 随伴関手ペア (Adjunction)

### 5. 差別化

| | Perplexity | Periskopē |
|:--|:----------|:----------|
| 目的 | 答えを返す | **問いを育てる** |
| 認知モデル | なし | **FEP + HGK** |
| ユーザー | 一般 | **研究者** |
| 言語 | 英語中心 | **日英中 3 言語** |
| ソース | 汎用 Web | **ニッチ + 学術** |

**「問いを育てる」の実装**: Φ7 Next Questions セクション — レポート末尾に次の探索の問いを提示

### 6. 逆拡散モデルとしての検索

> **理論基盤**: [diffusion_cognition.md](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/kernel/diffusion_cognition.md)

検索パイプラインは**拡散モデルの逆再生**である。
散らばった Web の情報 (高エントロピー) が、反復的に 1 つの回答 (低エントロピー) に収束していく。

```
Web 情報 (x_T = ノイズ)
  ↓ Phase 0: Φ1-Φ4 = 順拡散→逆拡散 (問いの空間を広げて絞る)
  ↓ Phase 1: 検索実行 = 観測 (新しいデータの取得)
  ↓ Phase 2: 合成 = デノイジングステップ
  ↓ Phase 2.5: CoT Chain = 反復デノイジング (各 iteration が 1 step)
  ↓ Phase 3: 引用検証 = Score function (方向検証)
  ↓ Phase 4: Φ7 = 最終デノイジング → Fix(G∘F) 候補
回答 (x_0 = 構造)
```

**対応表**:

| 拡散モデル | Periskopē | 実装 | config パラメータ |
|:----------|:----------|:-----|:----------------|
| β_t (ノイズ率) | Precision の逆数 (1/π) | `diversity_weight` 減衰 | `decay_type`: linear / exponential / cosine / logsnr |
| Score ∇log p | 予測誤差の勾配 | `embedder.similarity()` | — |
| α schedule | Explore→Exploit 遷移 | precision-weighted α | `alpha_schedule`: linear / cosine / sigmoid |
| Precision-weighting | 確信度×方向 | `score = α × rel × conf + (1-α) × gain` | — |
| Denoising steps | CoT Chain iterations | `_phase_iterative_deepen()` | `max_iterations` |
| 矛盾検出 | contradiction injection | `reasoning_step.contradictions` → 修正クエリ | L3 (depth≥3) で自動発動 |
| DDPM (確率的) | CCL `~` (振動) | 探索的反復 | — |
| DDIM (決定論的) | CCL `~*` (収束) | 収束的反復 | — |
| 収束判定 | info_gain < threshold | `saturation_threshold` | `saturation_threshold: 0.035` |

### 7. マルチスケール位相反転 (Phase Inversion)

> **「暫定的な答えが出るたびに、その情報を反証する情報を探すエージェントを並列実行する」**
> — Creator, 2026-02-24

検索パイプラインの全コンポーネントには暗黙の目的関数がある — 「クエリに対する支持証拠を見つける」。
**位相反転**とは、この目的関数を「クエリに対する**反証**を見つける」に反転させること。

```
通常:  f(query) = argmax P(evidence | supports query)
反転:  f̄(query) = argmax P(evidence | refutes query)
```

同じ装置、同じ能力、逆の目的。変えるのは「意図」だけ。

#### Scale 公理によるフラクタル構造

反転は特定のレイヤーの特権ではなく、**全レイヤーで同型に繰り返される**。

```
点 (L0):  query → anti_query                     # クエリの反転
線 (L1):  step(synthesis) → challenge(synthesis)  # ステップの反転
面 (L2):  pipeline(query) → anti_pipeline(query)  # パイプラインの反転
体 (L3):  model_A(result) → model_B(critique)     # セッションの反転
```

| 層 | 名前 | 何を反転するか | 粒度 | 実装 |
|:---|:-----|:-------------|:-----|:-----|
| **L0** | クエリ反転 | Φ1 で生成するクエリの方向 | 個々のクエリ | `phase_inversion.py: invert_queries()` |
| **L1** | ステップ反転 | CoT イテレーション内の中間合成 | 各イテレーション | `phase_inversion.py: advocatus_challenge()` |
| **L2** | パイプライン反転 | `research()` 全体の目的関数 | パイプライン全体 | `dialectic.py: DialecticEngine` |
| **L3** | セッション反転 | モデル間の検証 | セッション全体 | `/vet` (既存) |

#### L2 v2: 対称・並列・動的相互作用

> **「反証とは、異なる視点からの洞察の極限である」** — Creator, 2026-02-24
> **「並列はY、非対称はゴミ」** — Creator, 2026-02-24

反証側は支持側と**同格のフルパワー**で走る。弱い反証は反証ではない。
直列的な「ターン制」は妥協である — 真の弁証法は**相補的な動的相互作用**から生まれる。

```
┌─ Thesis Engine ──────┐                ┌── Anti Engine ────────┐
│ research() FULL power│                │ research() FULL power │
│ CoT iter 1 → publish │ ←── Shared ──→ │ CoT iter 1 → publish │
│ ← read opponent ←    │    Channel     │ ← read opponent ←    │
│ CoT iter 2 → publish │    (async)     │ CoT iter 2 → publish │
│ ...converge...       │                │ ...converge...        │
└──────────────────────┘                └───────────────────────┘
                         ↘     ↙
                   Dialectical Synthesis
```

**三原則**:

| 原則 | 意味 |
|:-----|:-----|
| **対称性** | Thesis と Antithesis は同じ `PeriskopeEngine`、同じ depth、同じ能力。変わるのは `system_instruction` のみ |
| **並列性** | `asyncio.gather` で同時実行。ターン制ではなく、両者が常に並走する |
| **動的相互作用** | Shared Channel (async queue) を通じて、各 CoT イテレーションの中間結果が即座に相手のコンテキストに流入する |

#### Context Rot 対策: 予測誤差の時間的減衰

長時間の弁証法ループでは **Context Rot** (対戦相手の発見が蓄積し、古い情報が新しい推論を汚染する) が発生する。

FEP 的には、古い情報は予測精度への寄与が時間とともに減衰するため、圧縮しても予測誤差の増大は最小限。
一方、直近の情報は予測に直結するため圧縮してはならない。

`DialecticContextBuffer` (`cognition/context_compressor.py`) がこれを実装する:

```
┌───────────────────────────────────────────────────┐
│  [Compressed Checkpoint]  ← 古い発見の LLM 要約   │
│  ─────────────────────                             │
│  [Verbatim iter N-1]      ← 直近の発見 (そのまま)  │
│  [Verbatim iter N]        ← 最新の発見 (そのまま)  │
└───────────────────────────────────────────────────┘
```

| パラメータ | L1 Quick | L2 Standard | L3 Deep |
|:-----------|:---------|:------------|:--------|
| バジェット (chars) | 5,000 | 20,000 | 40,000 |
| Verbatim window | 2 entries | 4 entries | 6 entries |
| 圧縮トリガー | バジェット超過時 | 同左 | 同左 |
| 圧縮方式 | Gemini Flash で要約 | 同左 | 同左 |
| フォールバック | 古い順切り捨て | 同左 | 同左 |

#### Shared Vector Index: 一時情報のシームレスな検索

Thesis/Anti 両エンジンが探索中に発見した情報（一時ファイル、暫定合成、推論トレース）は
**共有ベクトルインデックス**に即時登録される。

```
Thesis CoT iter 1 → [embed] → Shared Ephemeral Index ← [embed] ← Anti CoT iter 1
         ↑                            ↓                            ↑
         └────── vector search ───────┘────── vector search ───────┘
```

これにより、片方のエンジンが発見した反例や支持証拠を、もう片方が
キーワード一致ではなく**意味的類似度**で発見できる。 §1 の「検索は能動推論である」と同型。

#### HGK MCP 機構との統合ビジョン

Claude.ai 級の Deep Research では、検索パイプライン自体が HGK の認知インフラを利用する。

| MCP 機構 | Deep Research での役割 |
|:---------|:----------------------|
| **Dendron** | 中間合成の存在証明チェック — 引用された事実が実在するか検証 |
| **Synteleia** | 推論トレースの品質監査 — 各 CoT ステップの論理的健全性を静的解析 |
| **Anamnesis** | 過去の調査との接続 — 同じトピックの過去 Research Report を検索 |
| **Sympatheia WBC** | 異常検知 — 両エンジンの乖離が閾値を超えた場合にアラート |

検索がただの「情報取得」ではなく、**HGK の認知活動である** ことの実装。

#### FEP 的意味

確証バイアス (CD-3) の構造的解毒剤。予測誤差を最小化する最も楽な方法は
「確認的な証拠だけを集めること」— 位相反転はこれを構造的に不可能にする。

**N-2 (θ2.2) との関係**: N-2 (θ2.2) の C列 (Counter = 反証を挙げる) のシステムレベル外部化。
個人レベル (N-2 (θ2.2)) → 検索レベル (位相反転) → セッションレベル (/vet) の自己相似。

**操作的比喩**: §4 の圏論的構造と同様、ここでの「位相反転」はFEPからの厳密な導出ではなく、
設計原理としての操作的比喻である。

---

*Periskopē Vision v1.5 — 2026-02-24 §7 v2: 対称・並列・動的相互作用 + ベクトル共有 + HGK MCP統合*
*Periskopē Vision v1.4 — 2026-02-24 §7 マルチスケール位相反転追加 (Phase Inversion)*
*Periskopē Vision v1.3 — 2026-02-23 §6 逆拡散モデル追加 (diffusion_cognition.md)*
*Periskopē Vision v1.2 — 2026-02-23 行番号リンク→関数名テキスト、計測リンク追加*
*Periskopē Vision v1.1 — 2026-02-23 双方向リンク追加 + 圏論「操作的比喩」明記*
*Periskopē Vision v1.0 — 2026-02-19 Creator 承認*
