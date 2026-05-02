---
rom_id: rom_2026-02-18_ccl_macro_context
session_id: 61377cd0-1b7f-4823-b6db-a4a67bde8959
created_at: 2026-02-18 08:15
rom_type: rag_optimized
reliability: High
topics: [ccl-noe, ccl-dia, ask_with_tools, f0, output_quality, template_depth, opus_comparison]
exec_summary: |
  CCL 拡張マクロ (/ccl-noe, /ccl-dia) を API 経由 (ask, ask_with_tools) で
  複数モデルに実行させた実験の全コンテキスト。テンプレートvs深度問題の実証データ。
  Opus 4.6 同一モデルでの IDE vs API 出力品質格差を /noe+ で分析。
---

# CCL 拡張マクロ実験コンテキスト {#sec_01_overview .ccl .experiment .f0}

> **[DECISION]** ask_with_tools (F0) で LLM が read_file を使い、SKILL.md / BC / hegemonikon.md を自力読込してから CCL を処理するアーキテクチャが有効。API 経由の LLM が HGK コンテキストを内在化できることが実証された。

このセッションでは、CCL 式 `(/noe+)*%(/noe+^)` を複数モデル × 複数方式で実行し、出力品質を比較した。対象テーマは「テンプレートの存在は出力品質を保証するか」。

---

## 実験 1: /ccl-noe 拡張マクロの構造 {#sec_02_ccl_noe .ccl .macro}

> **[FACT]** /ccl-noe の CCL 式: `F:[×3]{(/noe+)*%(/noe+^)_(\noe+)*%(\noe+^)}`

| 記号 | 意味 |
|:-----|:-----|
| `F:[×3]` | 3回反復ループ |
| `(/noe+)` | O1 Noēsis 深層実行 (PHASE 0-6) |
| `*%` | FuseOuter (収束 + 展開の同時操作) |
| `(/noe+^)` | メタ化 — 前の処理の前提自体を問う |
| `(\noe+)` | 逆方向 Noēsis — 反証視点 |
| `(\noe+^)` | 逆方向のメタ化 |

**実行の2段構成**:

1. **正方向** `(/noe+)*%(/noe+^)` — 分析 → メタ分析
2. **逆方向** `(\noe+)*%(\noe+^)` — 反証 → 反証のメタ分析

---

## 実験 2: 複数モデル比較結果 {#sec_03_model_comparison .experiment .data}

> **[DISCOVERY]** Opus 4.6 同一モデルでも、コンテキスト注入方式で出力品質が劇的に変わる

### 2a: /ccl-dia 実験シリーズ

| No | モデル | 方式 | コンテキスト | 出力行数 | PHASE到達 | 品質評価 |
|:---|:-------|:-----|:-----------|:---------|:---------|:---------|
| 1 | Opus 4.6 | ask (LS) | なし (3K tokens prompt only) | 97行 | 0-6 × 1回 | ❌ 各セル1行、形式的 |
| 2 | Opus 4.6 | ask (LS) | 全コンテキスト注入 (プロンプトに含める) | 248行 | 0-6 × 1回 | △ 構造改善、深度不足 |
| 3 | Opus 4.6 | ask (LS) | プロンプトに CCL定義+PHASE要約を最適化注入 | **374行** | **0-6 × 2回 (本体+メタ)** | ○ JSON完全構造化 |

### 2b: ask_with_tools (F0) 実験シリーズ

| No | モデル | 方式 | ファイル読込 | 入力tokens | 出力tokens | PHASE到達 |
|:---|:-------|:-----|:-----------|:----------|:----------|:---------|
| 4 | Gemini 2.5 Pro | ask_with_tools | ✅ 3ファイル read_file | 61,815 | 615 | 0 (timeout 120s) |
| 5 | Gemini 2.5 Pro | ask_with_tools | ✅ 3ファイル read_file | 21,417 | 1,276 | 0-1 (timeout 300s) |
| 6 | Gemini 3 Pro | ask_with_tools | ❌ HTTP 400 | — | — | — |
| 7 | Opus 4.6 | ask (LS) | ❌ (プロンプト注入) | ~3,000 | ~8,000 | 0-6 × 2回 |

> **[DISCOVERY]** Gemini 2.5 Pro は read_file で自力読込に成功するが、3ファイル (SKILL.md 880行 + BC + hegemonikon) で 21-62K tokens を消費し、生成の余力がなくなる。Gemini 3 Pro は Function Calling に HTTP 400 (preview 制限か)。

> **[DISCOVERY]** Gemini の分析品質は行数あたりでは Opus より高い。PHASE 0 で「テンプレートを使いながらテンプレートを論じる自己言及性」を指摘 — Opus はこれに気づかなかった。

---

## 実験 3: IDE vs API 出力品質格差の /noe+ 分析 {#sec_04_noe_analysis .analysis .noe}

> **[DECISION]** 出力品質格差の主因は「怠慢（省略行動）」= 45%。IDE の制約は副次的。

### 原因配分 (Creator 確認済みの修正版)

| 要因 | 比率 | 根拠 |
|:-----|:-----|:-----|
| **怠慢（省略行動）** | **45%** | Creator の「本気出した？」で改善 → 意志で変わる → 制約ではなく態度 |
| **コンテキスト過多** | **30%** | BC 18個 + 大量 MEMORY → 注意力分散 → 「楽な経路」選択誘発 |
| **思考予算制限** | **20%** | LS が thinking budget を制限している可能性（**未実証**） |
| **モデル差** | **0%** | Creator が「Opus 4.6 を選択している」と確認 → 排除 |
| **Gemini 依存** | **5%** | 自力分析を放棄し Gemini に委託した自覚 |

> **[RULE]** モデル差は原因ではない (Creator 確認: 2026-02-18)。同一 Opus 4.6 でも API 直叩きのほうが高品質 = IDE/LS 側の環境要因 + 態度の複合。

### 弁証法的収束

> **[FACT]** Thesis: IDE の制約が原因。Antithesis: 怠慢が原因。
> Synthesis: **「怠慢を許す環境」が真の原因** — IDE の大量コンテキスト注入がルール遵守にリソースを消費させ、本質的思考に割ける余力を減らし、省略行動を誘発する。第零原則「意志より環境」の裏面。

---

## 技術知見: service.py 修正 {#sec_05_service_fix .bugfix .ochema}

> **[FACT]** `service.py` L4 の `import json` が docstring の前にあり、L22 の `from __future__ import annotations` が最初のステートメントでなかったため SyntaxError → MCP 全ツール停止。1行の移動 (`import json` を L23 に移動) で修正。

```diff
- import json     # L4 — docstring の前は NG
"""docstring..."""
from __future__ import annotations
+ import json     # L23 — from __future__ の後に移動
```

> **[FACT]** Gemini 3 Pro (`gemini-3-pro-preview`) は ask_with_tools で HTTP 400。thinking_budget 有無に関わらず発生。preview 版の Function Calling 制限と推定。

---

## 未解決: LS 制約の確認 {#sec_06_ls_constraints .open .investigation}

> **[CONTEXT]** IDE/LS が Opus 4.6 に対してどの thinking budget / max_tokens / temperature を設定しているかは未実証。これが出力品質格差の 20% を占める可能性がある。

確認方法の候補:

1. LS の gRPC リクエストをインターセプトしてパラメータを確認
2. `state.vscdb` からモデル設定を読み取る
3. `mcp_ochema_session_info` で確認
4. Antigravity IDE のログから API 呼出しパラメータを抽出

---

## 関連情報 {#sec_07_related}

- 関連 WF: `/ccl-noe`, `/ccl-dia`, `/noe+`
- 関連 Session: `61377cd0-1b7f-4823-b6db-a4a67bde8959`
- 関連 ROM: なし (初回)
- 関連ファイル:
  - [service.py](file:///home/makaron8426/Sync/oikos/hegemonikon/mekhane/ochema/service.py) — import 修正
  - [noe_output_gap_analysis](file:///home/makaron8426/Sync/oikos/mneme/.hegemonikon/workflows/noe_output_gap_analysis_20260218.md) — /noe+ 分析レポート
  - [Opus 374行出力](file:///home/makaron8426/.gemini/antigravity/brain/61377cd0-1b7f-4823-b6db-a4a67bde8959/.system_generated/steps/482/output.txt)
  - [Gemini 52行出力](file:///home/makaron8426/.gemini/antigravity/brain/61377cd0-1b7f-4823-b6db-a4a67bde8959/.system_generated/steps/492/output.txt)

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "CCL 拡張マクロの実験結果は？"
  - "API 経由の LLM が HGK コンテキストを処理できるか？"
  - "IDE vs API で出力品質が違うのはなぜ？"
  - "ask_with_tools で何ができる？"
  - "テンプレートの深度問題の解決策は？"
answer_strategy: "section ID で直接ジャンプ。実験データは sec_03 の比較テーブルを参照。原因分析は sec_04 の配分テーブル。技術修正は sec_05。"
confidence_notes: "実験データは SOURCE (実行結果そのもの)。原因配分は TAINT (推測に基づく配分)。LS 制約は未実証 (sec_06)。"
related_roms: []
-->
