---
rom_id: rom_2026-02-27_pistis_absorption
session_id: 1d92db44-ee7d-476b-8618-0e33853b21ea
created_at: 2026-02-27 10:48
rom_type: rag_optimized
reliability: High
topics: [pistis, H-series, dokimasia, absorption, v4.1, precision, certainty]
exec_summary: |
  旧 H2 Pistis (確信度評価) を v4.1 体系に解体・吸収した。
  「確信」という状態は Dokimasia [Pr:C/U] へ、確信度を評価・計算する操作(各派生)は
  /dia, /noe, /tek などの適切な Poiesis 動詞へ完全分離された。
---

# H2 Pistis 完全吸収と解体 {#sec_01_pistis_absorption}

> **[DECISION]** 旧体系の Pistis は「状態=(パラメータ)」と「操作=(動詞)」が混同された複合概念であったため解体された。
> 状態面は Dokimasia `[Precision: C/U]` 修飾子に吸収し、操作面 (派生WF群) はそれぞれの機能に基づき既存の Poiesis 動詞に再マッピングした。

## 消化の経緯 {#sec_02_process}

> **[FACT]** /ske で 5次元仮説を展開。H5 (盲点: Pisis には状態と操作が混同してパッケージ化されている) の EIG が 0.9 と最大であった。(SOURCE: ske_pistis_20260227.md)

> **[FACT]** /noe+ で深層分析を実行。「確信する」という単一の動詞は存在せず、客観的証拠調べ(/dia)・主観内省(/noe)・ベイズ計算(/tek) といった異なる操作が、単に「確信度を出すため」という目的基準で /pis に詰め込まれていたことを発見。(SOURCE: noe_pistis_20260227.md)

## 核心的発見: 操作の解体 {#sec_03_core_discoveries}

> **[DISCOVERY]** Pistis の派生モードは以下のように各 24動詞に解体される:

| 旧派生 (目的分類) | v4.1 分解先 (操作と精密さの分離) |
|:----------------|:---------------------------------|
| `/pis` (全体) | `[Precision: C/U]` 修飾子 (単独では実行不可) |
| `/pis.obje` (客観) | **A2 Krisis (/dia)** (証拠を厳密に判定して `[Pr:C/U]` を得る) |
| `/pis.subj` (主観) | **O1 Noēsis (/noe)** (己の不確かさを内省して `[Pr:U]` を得る) |
| `/pis.inte` (合意) | **V14 Synopsis (/ops)** (周囲の合意状況を俯瞰して `[Pr:C/U]` を得る) |
| `/pis.bayes` (確率) | **V08 Tekhnē (/tek)** (事後確率を数学的に計算して `[Pr:C/U]` を得・更新する) |
| `/pis.cali` (校正) | **V23 Anatheōrēsis (/ath)** (過去の予測と実績から教訓を抽出し尺度を直す) |
| `/pis.unc` (不確実性) | **V13 Analysis (/lys)** (不確実性の構造を Aleatoric/Epistemic に分解する) |

## 実装の記録 {#sec_04_implementation}

> **[RULE]** 旧 WF `/pis` は `lcm_state: deprecated` に変更済み。主観・客観のギャップや過信バイアス (X-HK5) などの実践知恵は Dokimasia 知識ベースに移植した。

| 変更ファイル | 変更内容 |
|:------------|:---------|
| `kernel/axiom_hierarchy.md` | H2 の吸収記録 + 状態と操作の分離の記述 + 解体マッピングの追記 |
| `nous/skills/dokimasia/SKILL.md` | H2 Pistis 用セクションを開放。実践知恵と解体マッピングを記録 |
| `nous/workflows/pis.md` | frontmatter deprecated + 本文に DEPRECATION NOTICE |

## 関連情報 {#sec_05_references}

- 関連 WF: `/ske`, `/noe+`, `/rom+`, `/dox`
- 関連 Skill: `dokimasia/SKILL.md`
- 出力ファイル: `mneme/.hegemonikon/workflows/ske_pistis_20260227.md`, `noe_pistis_20260227.md`
- 次ステップ: H3 Orexis の深い消化

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Pistis は v4.1 でどうなったか"
  - "確信度評価 (/pis) は今後どう行うか"
  - "/pis.bayes の代わりは何か"
answer_strategy: "Pistis は状態[Precision:C/U]と操作(/dia, /tek等)に分解されたことを説明し、適切な動詞を案内する"
confidence_notes: "Kalon 0.98。非常に自然な分解と統合。"
related_roms: ["rom_2026-02-27_propatheia_absorption"]
-->

---
*ROM burned: 2026-02-27 /rom+ by Claude*
