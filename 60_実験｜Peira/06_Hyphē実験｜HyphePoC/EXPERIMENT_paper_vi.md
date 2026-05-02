# Paper VI 実験設計書 — Coherence τ-Invariance の3ドメイン検証

**Created**: 2026-03-29
**Status**: 設計完了 → 実装中

---

## 概要

Paper VI §3 Coherence τ-Invariance 定理の3ドメイン検証。
2層構造: Layer 1 (Linkage 拡張) + Layer 2 (ドメイン固有)。

## Layer 1: Linkage 拡張 — 「G∘F の汎用性」

**目的**: Hyphē の G∘F を様々なテキスト種別に適用し、τ-invariance が
セッションログ以外でも成立するかを確認する。

**入力テキスト**:
- E1a: CoT 出力テキスト (10 タスク × 3 depth)
- E1b: SKILL.md ファイル (10 ファイル × 3 粒度版)

**手法**: `run_chunker.py --file {path} --tau {τ}` をそのまま使用。

**τ**: [0.60, 0.65, 0.70, 0.75, 0.80]
**G∘F**: ON/OFF
**N**: 30 テキスト × 5 τ × 2 (ON/OFF) = 300 データポイント

**測定**: C̄(Fix(G∘F; τ)) の range

**予測**: range < 0.02 (テキスト種別によらず τ-invariant)

**注意 (/exe W1)**: この実験は Linkage ドメインの拡張であり、
Cognition/Description ドメインの τ-invariance を主張するものではない。

---

## Layer 2: ドメイン固有 — 「Cognition / Description の τ-invariance」

### /exe で発見した構造的欠陥と修正

| 欠陥 | 修正 |
|:--|:--|
| W1: ドメイン混同 (Linkage の再測定) | ドメイン固有の ρ を使う |
| W2: τ のすり替え (similarity threshold) | ドメイン固有の τ (depth / granularity) |
| W3: depth 操作が離散3条件 | token budget で連続化 (5条件) |
| W4: granularity = 情報量変化 | 同一内容の分割数 N で操作 |
| W5: ker(G) が Linkage と同一 | LLM-as-judge ρ でドメイン固有の ker(G) |

### E2': Cognition — CoT の depth τ-invariance

**τ (制御パラメータ)**: token budget = [50, 200, 500, 1000, 2000]
- LLM に "Answer in at most {budget} tokens, showing your reasoning step by step" と指示
- 同一タスクを 5 budget で実行 → 5 つの CoT テキスト

**ρ (整合性測度)**: LLM-as-judge
- 隣接ステップペア (s_i, s_{i+1}) に対して:
  "Does step {i+1} follow logically from step {i}? Rate 0.0 (no connection) to 1.0 (tight logical chain)."
- Ochema/cortex API 経由で Gemini or Claude を judge として使用

**タスクセット** (10 タスク):
1. 数学: "Prove that √2 is irrational"
2. 論理: "All A are B, some B are C. What follows?"
3. コード: "Write a function to detect cycles in a linked list"
4. 分析: "Compare REST and GraphQL for a mobile app backend"
5. 要約: [Paper I abstract を要約]
6. 因果: "Why does increasing minimum wage have mixed effects?"
7. 創造: "Design a board game about climate change"
8. 批判: "Steel-man the argument against remote work"
9. 計画: "Plan a 3-day trip to Kyoto for a group of 4"
10. メタ: "Explain what makes a good explanation"

**F (merge)**: 隣接ステップの ρ > merge_threshold → 統合
**G (split)**: ステップ内の ρ < τ → 分割 (τ = ρ の閾値、5条件)
  G の τ は ρ (LLM-as-judge スコア) の閾値: [0.3, 0.4, 0.5, 0.6, 0.7]

**測定**:
- C̄(Fix(G∘F; τ_ρ)) の range (5 τ_ρ 条件間)
- C̄(Fix(G∘F; τ_ρ)) の depth (token budget) 依存性

**予測**:
- G∘F ON: C̄ の τ_ρ-range < 0.05 かつ depth-range < 0.05
- G∘F OFF: C̄ は τ_ρ と depth の両方に依存

**N**: 10 タスク × 5 depth × 5 τ_ρ × 2 (ON/OFF) = 500 データポイント
**LLM-as-judge calls**: ~5000 (10 タスク × 5 depth × ~20 ステップ × 5 τ_ρ)

### E3': Description — プロンプト granularity τ-invariance

**τ (制御パラメータ)**: 分割数 N = [3, 5, 10, 15, 20]
- 同一 SKILL の内容を N 個の指示文に分割
- 情報量は同一、粒度だけが変わる

**ρ (整合性測度)**: LLM-as-judge
- 隣接指示ペア (instr_i, instr_{i+1}) に対して:
  "Are these two instructions consistent and complementary? Rate 0.0 (contradictory) to 1.0 (perfectly coherent)."

**SKILL セット** (10 ファイル):
~/.claude/skills/ から以下を選定:
1. noe/SKILL.md (最大・複雑)
2. bou/SKILL.md
3. ene/SKILL.md
4. kat/SKILL.md
5. lys/SKILL.md
6. ske/SKILL.md
7. ele/SKILL.md
8. akr/SKILL.md
9. exe/SKILL.md
10. tek/SKILL.md

**F (merge)**: 隣接指示の ρ > merge_threshold → 統合
**G (split)**: 指示内の ρ < τ → 分割
  G の τ: [0.3, 0.4, 0.5, 0.6, 0.7]

**測定**:
- C̄(Fix(G∘F; τ_ρ)) の range (5 τ_ρ 条件間)
- C̄(Fix(G∘F; τ_ρ)) の granularity (N) 依存性

**予測**:
- G∘F ON: C̄ の τ_ρ-range < 0.05 かつ N-range < 0.05
- G∘F OFF: C̄ は τ_ρ と N の両方に依存

**N**: 10 SKILL × 5 N × 5 τ_ρ × 2 (ON/OFF) = 500 データポイント

---

## 実装ステップ

### Step 0: LLM-as-judge ρ モジュール (Layer 2 の核心)

`rho_judge.py` — hyphe_chunker.py の cosine similarity を差し替える抽象 ρ インターフェース

### Step 1: CoT データ生成 (E2')

`gen_cot_data.py` — 10 タスク × 5 depth の CoT テキストを生成

### Step 2: SKILL 粒度データ生成 (E3')

`gen_skill_granularity.py` — 10 SKILL × 5 N の粒度版を生成

### Step 3: Layer 1 実行

`run_layer1.py` — 既存 run_chunker.py のラッパー

### Step 4: Layer 2 実行

`run_layer2.py` — rho_judge.py + gf_iterate の統合ランナー

### Step 5: 分析

`analyze_paper_vi.py` — 全結果を集約し τ-invariance range を算出

---

## 成功基準

| 基準 | Layer 1 | Layer 2 E2' | Layer 2 E3' |
|:--|:--|:--|:--|
| C̄ τ-range (G∘F ON) | < 0.02 | < 0.05 | < 0.05 |
| C̄ τ-range (G∘F OFF) | > 0.05 | > 0.05 | > 0.05 |
| C̄ domain-param range (G∘F ON) | N/A | < 0.05 (depth) | < 0.05 (N) |
| Fix(G∘F) 収束率 | 100% | > 90% | > 90% |

---

*Paper VI Experiment Design v1.0 — 2026-03-29*
