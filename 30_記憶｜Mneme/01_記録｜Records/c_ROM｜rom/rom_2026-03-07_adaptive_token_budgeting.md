---
rom_id: rom_2026-03-07_adaptive_token_budgeting
session_id: 35171553-71ce-4c40-aede-9c1c8a002421
created_at: 2026-03-07 20:27
rom_type: rag_optimized
reliability: High
topics: [adaptive_budgeting, kalon, typos_migration, periskope, layered_prompt, compute_data_budget, phi3]
exec_summary: |
  Periskopē の Adaptive Token Budgeting を Kalon 飽和検知器 (P(new)) で駆動する仕組みを設計・実装・監査した。
  phi3 クエリ分類プロンプトを Týpos v8 DSL に移行し、Layered Prompt Architecture (L1 System + L2 Task + L3 Data) を確立。
  /ele+ 監査で5矛盾を検出し、/dio で全修正を完了。L2 深度でエラーなく動作確認済み。
search_expansion:
  synonyms: [token_budget, context_compression, dynamic_prompt_length, kalon_saturation]
  related_concepts: [FEP_precision, information_gain, P_new, bayesian_saturation, typos_dsl]
  abbreviations: [ATB, LPA]
---

# Adaptive Token Budgeting + Týpos 移行 {#sec_01_overview}

> **[DECISION]** Periskopē の LLM プロンプトを「固定部分」(Týpos) と「動的部分」(Kalon 駆動) に分離する **Layered Prompt Architecture** を採用した。

## 1. Layered Prompt Architecture (LPA) {#sec_02_lpa .architecture .core}

> **[DEF]** 3層構造でプロンプトのトークン効率と品質を両立する設計パターン。

| Layer | 管轄 | 圧縮 | コンテンツ |
|:------|:-----|:-----|:---------|
| **L1 System** | `.typos` DSL | ✅ コンパイル時最適化 | モデル固有の命令テンプレート |
| **L2 Task** | Python ハードコード | ❌ 固定 | タスク固有のコンテキスト |
| **L3 Data** | `compute_data_budget()` | ✅ Kalon P(new) 駆動 | 検索結果・合成テキスト |

> **[RULE]** L2 を削ると品質劣化する。圧縮対象は L1 と L3 のみ。

## 2. compute_data_budget() {#sec_03_budget_fn .implementation .core}

> **[FACT]** `kalon_detector.py` 内に実装。Kalon 飽和検知器の `SaturationState.p_new` を使って動的にキャラクタバジェットを計算する。

```python
def compute_data_budget(
    state: SaturationState,
    base_chars: int = 150_000,
    floor_ratio: float = 0.40,
) -> int:
    p_new = state.p_new  # 0.0–1.0
    ratio = floor_ratio + (1.0 - floor_ratio) * p_new
    return max(int(base_chars * floor_ratio), int(base_chars * ratio))
```

> **[DECISION]** `floor_ratio=0.40` は暫定値。経験的チューニング未実施。将来の `/pei+` で最適値を探索すべき。

**動作原理**:
- `P(new) = 1.0` → `ratio = 1.0` → バジェット = 150,000 chars (圧縮なし)
- `P(new) = 0.5` → `ratio = 0.70` → バジェット = 105,000 chars
- `P(new) = 0.0` → `ratio = 0.40` → バジェット = 60,000 chars (最大60%圧縮)

## 3. engine.py 統合 {#sec_04_engine .implementation}

> **[FACT]** `engine.py` の反復深化ループ (L1694付近) と Phase Inversion (L1764付近) の2箇所で `compute_data_budget()` を呼び出す。

> **[DECISION]** Phase Inversion の再合成時には、最新の `kalon_detector.state` で `_char_budget` を **再計算** する。初回計算のバジェットを使い回さない。

```python
# Phase Inversion 時の再計算 (修正後)
_char_budget_pi = compute_data_budget(kalon_detector.state)
logger.debug("Phase Inversion adaptive budget: %d chars (P(new)=%.3f)",
             _char_budget_pi, kalon_detector.state.p_new)
synthesis = await self.synthesizer.synthesize(
    query, search_results, char_budget=_char_budget_pi, ...
)
```

## 4. Týpos v8 DSL 移行 {#sec_05_typos .migration .typos}

> **[DISCOVERY]** Týpos v8 構文は旧 v2.1 (`@name`, `@instruction`, `@input`, `@output`) とは**非互換**。v8 では以下のブロック構文を使う:

```typos
#prompt phi3_classify_query
#syntax: v8
#depth: L1
<:role: Search Query Classifier :>
<:goal: Classify this search query into exactly ONE category. :>
<:constraints:
  - Reply with ONLY the category name (one word). Nothing else.
/constraints:>
<:context:
  - [knowledge] Categories: ...
  - [data] query: {query}
/context:>
```

> **[RULE]** `.typos` ファイルは `#prompt` + `#syntax: v8` ヘッダが必須。`@name` は v2.1 構文であり v8 では無視される。

**移行済みプロンプト**: `phi3_classify_query.typos` (1/16)

**未移行** (残り 15):
- `engine.py` 内: phi1 blind spot, phi4 convergent(旧インライン版), W6/W7 refinement
- `cognition/phi0_*.py`: intent decompose, query planner
- `cognition/phi1_blind_spot.py`: blind spot analysis, query synthesis
- `cognition/phi2_divergent.py`: divergent thinking
- `cognition/phi4_convergent.py`: convergent framing, decision frame
- `cognition/phi7_belief_update.py`: belief update
- `cognition/reasoning_trace.py`: iteration analysis
- `cognition/phase_inversion.py`: phase inversion

## 5. /ele+ 監査結果 {#sec_06_elenchos .audit .quality}

> **[FACT]** Elenchos 監査で5つの矛盾を検出し、/dio で全て修正完了。

| # | 矛盾 | 根本原因 | 修正 |
|:--|:-----|:--------|:-----|
| 1 | L1 depth ではφ7ループ未発動→圧縮未観測 | テスト depth が浅すぎた | depth=2 で再テスト |
| 2 | Phase Inversion で `_char_budget` が古い値 | ローカル変数スコープの欠落 | PI 内で再計算を追加 |
| 3 | `compute_data_budget` がループ内 import | 最適化不良 | ファイル上部に移動 |
| 4 | Týpos プロンプトがコンパイル空文字列 | v2.1 構文を v8 に混用 | v8 ブロック構文に書き直し |
| 5 | `floor_ratio=0.40` の根拠なし | 経験的チューニング未実施 | 暫定値として明記、将来の `/pei+` 課題に指定 |

## 6. ベンチマーク結果 {#sec_07_benchmark .metrics}

> **[FACT]** L1/L2 双方でテスト完了。

| 指標 | L1 結果 | L2 結果 |
|:-----|:--------|:--------|
| NDCG@10 | 0.97 | 0.76 |
| Entropy (normalized) | 1.00 | 1.00 |
| Overall Score | 0.94 | 0.66 |
| Search Results数 | — | 131 |
| 合成文字数 (Gemini) | — | 13,289 |
| 合成文字数 (Claude) | — | 11,761 |

> **[OPINION]** L2 の NDCG 低下 (0.97→0.76) は depth 増加による検索結果の多様性拡大が原因であり、Adaptive Budgeting 自体の劣化ではない [推定]。

## 7. 次のアクション {#sec_08_next}

| 優先度 | アクション | 関連 WF |
|:-------|:---------|:--------|
| 🔴 | phi1_blind_spot, phi4_convergent を Týpos v8 に移行 | `/kop+` |
| 🟡 | `floor_ratio` の最適値を `/pei+` で探索 | `/pei+` |
| 🟡 | 全 16 プロンプトの A/B テスト体制構築 | `/tek` |
| 🟢 | synthesizer.py の Týpos 連携修正 (periskope_synthesizer.prompt の不在) | `/dio` |

## 関連情報 {#sec_09_refs}

- **関連 WF**: `/ele+`, `/dio`, `/kop+`, `/pei+`
- **関連ファイル**:
  - `mekhane/periskope/engine.py` (L1694, L1764)
  - `mekhane/periskope/kalon_detector.py` (`compute_data_budget`)
  - `mekhane/periskope/prompts/phi3_classify_query.typos`
  - `mekhane/periskope/cognition/phi3_context.py` (`_load_prompt_file`, `_classify_query_llm`)
  - `mekhane/periskope/synthesizer.py` (`char_budget` パラメータ)
- **関連セッション**: 35171553-71ce-4c40-aede-9c1c8a002421
- **関連 Artifact**: `ele_adaptive_token_budgeting.md`

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "Periskopē のトークン管理はどうなっている？"
  - "Kalon と Adaptive Budgeting の関係は？"
  - "Týpos v8 構文の正しい書き方は？"
  - "phi3 のプロンプト移行方法は？"
  - "Layered Prompt Architecture とは？"
answer_strategy: "LPA の3層構造から説明し、compute_data_budget() の数式、engine.py の統合箇所を示す。Týpos 関連は sec_05 を参照。"
confidence_notes: "実装は動作確認済みだが floor_ratio の最適化は未実施。L2 での NDCG 低下の原因分析は [推定] レベル。"
related_roms: []
-->

<!-- ROM_GUIDE
primary_use: Periskopē の Adaptive Token Budgeting 実装の全コンテキスト復元
retrieval_keywords: adaptive budgeting, kalon, P(new), compute_data_budget, typos, phi3, layered prompt, engine.py, periskope, token compression
expiry: permanent
-->
