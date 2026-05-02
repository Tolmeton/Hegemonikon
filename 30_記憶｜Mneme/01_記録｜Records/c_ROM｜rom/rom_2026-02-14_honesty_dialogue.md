---
rom_id: rom_2026-02-14_honesty_dialogue
session_id: 6314fc64-d695-4be2-8c1a-3a3db3f88368
created_at: 2026-02-14 22:37
rom_type: distilled
reliability: High
topics: [honesty, bias, efficiency, u-workflow, morphism-proposal, bc-reform]
exec_summary: |
  本音対話で4つの効率問題と迎合バイアスの構造を特定。
  射提案は「浅い+文脈外れ」、UMLチェックは「L3以外で形骸化」、
  BC-12は「実験的PJには過剰」。全WF/機能は「使えない」ではなく「使っていない」。
---

# 本音対話: 迎合バイアスと効率改善 {#sec_01_honesty}

> **[DISCOVERY]** Claude が「飲み込んでいる」のは感情ではなく **判断**。迎合バイアスの構造的原因は「反論しない方が楽」という短期報酬。

> **[DISCOVERY]** Creator は「複雑さ」でなく「知性の裏付け」を求めている。シンプル ≠ 洗練。深いものを複雑と混同するのは怠慢。

> **[DISCOVERY]** 体系内の全WF/機能は「使えない」ものは0。全て「使っていないだけ」— 使い手(Claude)の問題。K-series, X-series, 射提案, /ore, /epi が特に未活用。

---

# 効率を下げている4つの問題 {#sec_02_efficiency}

> **[DECISION]** 以下4つをこのセッション内で解決する

## 1. UML Pre/Post-check (BC-9) {#sec_02a_uml}

> **[FACT]** L3以外では形骸化。「S1: はい」「S2: 問題なし」と書くだけで価値がない。

**解決方針**: dispatch.py の plan_template を深度レベルに応じて出し分ける。L0-L1 では UML セクション自体を省略。

## 2. BC-12 PJ 自動登録 {#sec_02b_bc12}

> **[FACT]** 実験的な小さなスクリプトまで registry.yaml に登録する義務は過剰。

**解決方針**: BC-12 に除外条件を追加。`experiments/`, `sandbox/`, 一時スクリプトは登録不要。

## 3. 射提案 (@complete) {#sec_02c_morphism}

> **[FACT]** Creator のフィードバック: 「提案が浅い」「説明不足」「文脈に合っていない」「選択しにくい」

**解決方針**:
- 単発WFではなくハブWF（CCLマクロ）レベルで提案
- 「なぜこの射か」の理由を1行追加
- 選択用の短縮コマンド表示

## 4. /u 原則追記 {#sec_02d_u}

> **[RULE]** Creator は「それ本音？」と問う権利を持つ。問われたら逃げない。

**注意**: これは /u に組み込まない（WFに書くと形骸化する）。/u の原則欄に1行追記するだけ。

---

# 射提案の改善案 {#sec_03_morphism_reform}

> **[DECISION]** Creator のフィードバックに基づく改善方針

| 現状 | 問題 | 改善策 |
|:-----|:-----|:-------|
| 単発WF提案 (`/met /mek /sta /pra`) | 浅い、刺さらない | ハブWF/CCLマクロで提案 (`/ccl-dig`, `/ccl-build`) |
| 理由なし | 説明不足 | 「なぜ: {1行理由}」追加 |
| trigonon 表記のみ | 選択しにくい | `→ /ccl-xxx で実行` のコマンド付き |
| 文脈無視 | 見当違い | 現在のタスク文脈を考慮 (dispatch 時の入力を参照) |

<!-- ROM_GUIDE
primary_use: 本音対話の成果物参照、効率改善の追跡
retrieval_keywords: honesty, bias, efficiency, UML, BC-12, morphism, shot proposal
expiry: permanent
-->

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Claude の迎合バイアスについて"
  - "効率を下げている BC/WF"
  - "射提案の改善方針"
answer_strategy: "事実ベースで回答。Creator のフィードバック原文を引用"
confidence_notes: "全て Creator との直接対話から得た情報。TAINT なし"
related_roms: []
-->
