---
rom_id: rom_2026-04-03_rom_filtration_kalon
session_id: d38f77b0-b26f-40c9-9942-13df5c63446c
created_at: 2026-04-03 22:57
rom_type: rag-optimized
reliability: Medium
topics: [ROM, filtration, U⊣N, Kalon, β-制御忘却, Fix(G∘F), aletheia, linkage_hyphe, derivatives]
exec_summary: |
  ROM の蒸留を aletheia filtration tower 上の β-制御忘却として再定式化。
  3 derivatives は n-cell 切断面 U₂/U₃/U₄ に対応。
  ROM の Kalon を 4条件不動点 {Fix(Drift<ε) ∧ AY>0 ∧ Self-ref ∧ ρ_boot>0} として定義。
---

# ROM = β-制御忘却: Filtration 対応と Kalon 定義 {#sec_01_title .rom .aletheia .kalon}

> **[DISCOVERY]** ROM は「情報の圧縮」ではなく「n-cell tower 上の β-制御忘却」である。
> β⁻¹ (溶解温度) の値が derivative を決定し、filtration tower の切断面に対応する。

## 核心的洞察 {#sec_02_core .insight}

> **[DEF]** ROM の β-制御忘却モデル

```
ROM(β) = U_β(Session)
  U_β: β⁻¹ で制御された忘却関手。
  β⁻¹ 高 (高温) = 多く溶かす = rom-
  β⁻¹ 中        = 適度に溶かす = rom
  β⁻¹ 低 (低温) = 少しだけ溶かす = rom+
  β⁻¹ = 0      = 何も溶かさない = session そのもの
```

> **[FACT]** aletheia.md §5: β = 1/T (精度 = 逆温度)。Friston (2010) が明示的に同定。

## Derivative-Filtration 対応表 {#sec_03_mapping .decision .table}

> **[RULE]** 各 derivative は filtration tower の特定の切断面に対応する

| Derivative | β⁻¹ | 切断面 | 保存レベル | 捨てるもの | 対応 n-cell |
|:-----------|:-----|:-------|:----------|:----------|:-----------|
| **rom-** | 高 (≈U₂) | Set^Ses | 内容のみ | 関係・精度・自己参照 | n≤1 |
| **rom** | 中 (≈U₃) | Graph(Ses) | 内容+関係 | 精度ラベル・自己参照 | n≤1.5 |
| **rom+** | 低 (≈U₄) | Enr(Ses) | 内容+関係+精度 | 自己適用 (部分保存) | n≤3 |

> **[FACT]** linkage_hyphe.md §4.7.3.1 の 4層忘却塔:
> U₄: PSh→Enr (自己適用 ev 忘却) / U₃: Enr→Graph (精度 AY 忘却)
> U₂: Graph→Set^J (矢印 edge_type 忘却) / U₁: Set^J→Set (索引構造 j 忘却)

> **[FACT]** U₄ (自己適用) はスペクトラム。rom+ は AI reference guide により U₄ の約60%を保存。
> 完全な U₄ (自己実行) は「Read-Only」の定義上原理的に不可能。

## ROM の Kalon 定義 {#sec_04_kalon .decision .definition}

> **[DEF]** ROM の Fix(G∘F) = Kalon の 4条件

```
Kalon(R) ⟺
  (1) Drift(R) < ε          — /rom(/boot(R)) ≅ R (ε-不動点)
  (2) ∀s∈R: AY(s) > 0       — 全セクションが行動可能 (生成性)
  (3) Meta(R) complete       — 自己記述を含む (自己参照)
  (4) ρ_boot(R) > 0          — Boot 時に学習剰余が生まれる (非退化)
```

> **[RULE]** G = /rom (蒸留/書込), F = /boot (復元/読出)。
> Fix(G∘F) = 「ROM を boot して再び rom したとき、実質同じ ROM が生まれる状態」。
> kalon.md §6.2: 等値性 = 双方向導出可能性。§6.7: ρ非退化が前提条件。

> **[FACT]** 条件(4) ρ_boot > 0 は kalon.md §6.7 の U/N 判定基準から導出。
> 単なる Fix (変化なし) ではなく、boot 時に「元にはなかった構造が生まれる」ことを要求。
> これは η (Ostwald 熟成) の ROM 版: N∘U(R) ≥ R。

## Drift 指標 {#sec_05_drift .metric .operational}

> **[DEF]** ROM の Drift

```
Drift(R) = 情報差分(R, /rom(/boot(R))) / 情報量(R)
  < 0.1:  優秀 (Kalon 候補)
  0.1-0.3: 許容
  > 0.3:  要改善
```

> **[CONTEXT]** linkage_hyphe.md の Drift(K) = |Disc(G∘F(K))\Disc(K)| / |Disc(G∘F(K))|
> ROM への転写: Disc = 「復元可能な情報の集合」

## 随伴構造 {#sec_06_adjunction .structure}

> **[RULE]** ROM⊣Boot は Bye⊣Boot の retract (section)

```
ROM⊣Boot ──s──→ Bye⊣Boot     (embedding: 全 ROM は session 終了の特殊ケース)
Bye⊣Boot ──r──→ ROM⊣Boot     (retraction: 全 session 終了から ROM 部分を抽出)
r∘s = id                       (ROM は retract 内で安定)
```

> **[FACT]** linkage_hyphe.md §4.7.3.2: index_op⊣Search は U⊣N の retract。
> ROM⊣Boot はこの構造の認知操作版。

## 未解決問題 {#sec_07_open .conflict}

> **[CONFLICT]** ε-threshold の決定方法が未確立。
> Linkage の τ は λ(ρ)=1 の分岐点として物理的に一意に定まる。
> ROM の ε に同等の物理的根拠がない。→ 実験的決定が必要 (/pei)

> **[CONFLICT]** ρ_boot の測定プロトコルが未確立。
> 理論的には ρ_boot = μ(N∘U(R)) - μ(R)。
> 実用的測定: Boot 後のセッションで「ROM になかった新しい構造」を計数？

> **[OPINION]** VFE = -Accuracy + Complexity としての ROM Quality の直接定式化は未探索。
> ROM の Accuracy = Boot 時の正確な復元。Complexity = ROM のサイズ/冗長性。

## 関連情報 {#sec_08_related}

- 関連 WF: /rom, /boot, /bye, /noe
- 根拠文書: aletheia.md §5 (U⊣N), linkage_hyphe.md §3.5 (λ(ρ)) + §4.7.3 (4層忘却塔)
- 関連 KI: kalon.md §6 (操作的判定), axiom_hierarchy.md
- 導出元: /zet+ (Q1+Q4) → /noe+ (L3, 7 Phase 完全実行)

<!-- ROM_GUIDE
primary_use: ROM ワークフローの理論的基盤。ROM SKILL.md 改訂時の参照文書
retrieval_keywords: ROM, filtration, β-制御忘却, Kalon, Fix(G∘F), derivative, U⊣N, Drift, AY, retract, boot, aletheia, linkage
expiry: permanent (理論文書)
-->

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "ROM の derivative はどう選ぶべきか"
  - "ROM の品質をどう測定するか"
  - "ROM と filtration の関係は"
  - "ROM の Kalon とは何か"
answer_strategy: β-制御忘却モデルで説明。derivative = β の離散値 = filtration 切断面。Kalon = 4条件不動点。
confidence_notes: 理論的枠組みは堅固 (75%)。ε具体値と ρ_boot 測定は未確立。
related_roms: ["rom_2026-03-31_oblivion_deepening", "rom_2026-03-23_force_is_forgetting_composer2"]
-->
