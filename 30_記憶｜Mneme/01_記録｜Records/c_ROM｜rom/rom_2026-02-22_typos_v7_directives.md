---
rom_id: rom_2026-02-22_typos_v7_directives
session_id: bc313b35-7270-40a7-98b3-722ab374d490
created_at: 2026-02-22 11:41
rom_type: rag_optimized
reliability: High
topics: [typos, v7.0, description-acts, prompt-engineering, rate-distortion, speech-act-theory, HGK-homology]
exec_summary: |
  TYPOS v7.0: HGK v4.1 と完全相同な7基底 (1+3+3) 構造を確立し、
  24記述行為ディレクティブをパーサーに実装。Searle-Vanderveken の
  7構成要素との一致を発見。全27テスト PASS。
search_extensions:
  synonyms: [prompt language, directive, description act, illocutionary force]
  related_concepts: [Rate-Distortion theory, Searle speech acts, Peirce semiotics, FEP]
  abbreviations: [RD, RSA, FEP, HGK]
---

# TYPOS v7.0: 24 Description Act Directives {#sec_01_overview .typos .v7 .implementation}

> **[DECISION]** TYPOS の基底構造を 6基底 (v6.0) から 7基底 (v7.0) に改訂し、HGK v4.1 の 7座標と完全相同な 1+3+3 構造を採用
>
> - d=0: Endpoint (src ↔ tgt)
> - d=1: Reason, Resolution, Salience
> - d=2: Context, Order, Modality

## 理論的基盤 {#sec_02_theory .theory .foundations}

> **[DISCOVERY]** Searle-Vanderveken (1985) の発話内の力の7構成要素が、TYPOS 7基底と完全に一致する

| TYPOS 基底 | Searle-Vanderveken 構成要素 | 対応する Question |
|:-----------|:---------------------------|:-----------------|
| Endpoint | Direction of fit | Who |
| Reason | Illocutionary point | Why |
| Resolution | Degree of strength | How |
| Salience | Propositional content | How much |
| Context | Preparatory conditions | Where |
| Order | Mode of achievement | Which |
| Modality | Sincerity conditions | When |

> **[FACT]** Zaslavsky et al. (PNAS 2018) が色彩命名における Rate-Distortion 最適化を実証。TYPOS の A0 公理 (RD最適化) の経験的裏付け。

> **[FACT]** Zaslavsky, Hu, Levy (2020) が Rational Speech Act (RSA) フレームワークを Rate-Distortion 理論で基礎付けできることを証明。

> **[FACT]** Futrell & Hahn (2022, 2024) が言語の体系性が情報理論的ボトルネックから生じることを示した。

## 24ディレクティブの命名原理 {#sec_03_naming .naming .principle}

> **[RULE]** 生成規則: Endpoint × 6修飾基底 × 4極 = 24 description acts
> 4極 = source×arché, source×telos, target×arché, target×telos

> **[DECISION]** 命名の核心原理: **source** (情報提示) vs **target** (行動指示)
>
> - source: 書き手が情報を「差し出す」ディレクティブ (@data, @fact, @case)
> - target: 読み手に「行動させる」ディレクティブ (@spec, @assert, @step)

### 24ディレクティブ一覧

| 基底 | src×arché | src×telos | tgt×arché | tgt×telos |
|:-----|:----------|:----------|:----------|:----------|
| Reason | @context | @intent | @rationale | @goal |
| Resolution | @detail | @summary | @spec | @outline |
| Salience | @focus | @scope | @highlight | @expansion |
| Context | @case | @principle | @step | @policy |
| Order | @data | @schema | @content | @format |
| Modality | @fact | @assume | @assert | @option |

## 実装詳細 {#sec_04_impl .implementation .code}

> **[DECISION]** 24ディレクティブを個別 elif ではなく、`V7_DIRECTIVES` frozenset + 汎用 `blocks` dict で一括処理する設計を採用

| ファイル | 変更内容 |
|:---------|:---------|
| `typos.py` | V7_DIRECTIVES (24個), Prompt.blocks,_parse_block, compile/compile_async/expand, _merge |
| `test_typos.py` | TestV7Directives (7テスト) |

> **[FACT]** レガシー重複 (@goal, @format, @context) は既存パーサーの elif チェーンが先に処理するため、V7 分岐には到達しない。意図的設計。

> **[DECISION]** `_merge` 関数に `blocks` の dict マージを追加。tools/resources と同じ child-overrides-parent パターン。

## テスト結果 {#sec_05_test .verification}

> **[FACT]** 全27テスト PASS (既存20 + v7.0新規7)、退行なし。0.004秒で完了。

## フォローアップ候補 {#sec_06_followup .next}

| # | タスク | 優先度 | 理由 |
|:--|:-------|:-------|:-----|
| F1 | MCP validate で v7.0 ディレクティブを「有効」と認識する更新 | 🟡 中 | 現在 @role/@goal/@constraints のみを推奨チェック |
| F2 | PHILOSOPHY.md で v7.0 実装状態を canonical に反映 | 🟡 中 | ドキュメントとコードの整合性 |
| F3 | generate_typos() で v7.0 ディレクティブを活用した生成 | 🟢 低 | 現在のジェネレータはレガシーディレクティブのみ使用 |
| F4 | Depth Level 連動: L0-L3 で使用する基底を自動制限 | 🟡 中 | PHILOSOPHY.md §5 に記述済みだが未実装 |
| F5 | @expansion の命名に関するユーザビリティテスト | 🟢 低 | 採用率が低い場合は @breadth 等への変更を検討 |
| F6 | Gnōsis へのインデックス: v7.0 ディレクティブのドキュメントをベクトル検索可能にする | 🟢 低 | 将来の AI-assisted prompt writing |

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "TYPOS v7.0 のディレクティブは何があるか"
  - "TYPOS と HGK の対応関係は"
  - "Searle-Vanderveken との対応は"
  - "24ディレクティブの実装方法"
  - "blocks フィールドの使い方"
answer_strategy: "24ディレクティブの一覧表 (sec_03) を示し、実装は sec_04 を参照させる"
confidence_notes: "理論的基盤は複数の査読付き論文で裏付け。実装は全テスト PASS。命名は主観的判断を含む。"
related_roms: ["rom_2026-02-22_typos_bases"]
-->
