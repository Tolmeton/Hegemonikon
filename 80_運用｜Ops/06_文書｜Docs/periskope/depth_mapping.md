---
summary: "depth ↔ Periskopē パラメータ対応。旧 sop/modes.md から移植。"
parent: infrastructure/periskope
version: "1.0"
origin: "nous/workflow-modules/sop/modes.md v3.0"
---

# Depth Mapping — Periskopē パラメータ対応

> 各 depth は Periskopē engine.py のパラメータに直接対応する。
> 動詞の認知代数 (`+`/無印/`-`) に連動して自動選択される。

---

## depth ↔ パラメータ対応表

| depth | 認知代数 | sources | expand_query | multipass | max_results | 時間 |
|:------|:---------|:--------|:-------------|:----------|:------------|:-----|
| **1 (L1)** | `-` | searxng のみ | false | false | 10 | 10-30秒 |
| **2 (L2)** | 無印 | 全ソース | true | false | 10 | 30-90秒 |
| **3 (L3)** | `+` | 全ソース | true | true | 30 | 2-4分 |

---

## L1 Quick — 表層検索

> 「ざっくり」「概要」「さらっと」

| 項目 | 値 |
|:-----|:---|
| **depth** | 1 |
| **sources** | SearXNG のみ |
| **expand_query** | false |
| **multipass** | false |
| **Φ1 盲点分析** | off |
| **確信度** | LOW — 表層のみ |

---

## L2 Standard — 標準検索

> 「調べて」「どうやるか」

| 項目 | 値 |
|:-----|:---|
| **depth** | 2 |
| **sources** | 全ソース (SearXNG, Brave, Tavily, S2, Gnōsis, Sophia, Kairos) |
| **expand_query** | true (W3 バイリンガル展開) |
| **multipass** | false |
| **Φ1 盲点分析** | on |
| **W7 full-text** | max 5 URL |
| **Φ4 Decision Frame** | on |
| **確信度** | MEDIUM-HIGH |

---

## L3 Deep — 深層検索

> 「徹底的に」「詳しく」「深掘り」

| 項目 | 値 |
|:-----|:---|
| **depth** | 3 |
| **sources** | 全ソース |
| **expand_query** | true (W3 バイリンガル展開) |
| **multipass** | true (最大2イテレーション) |
| **Φ1 盲点分析** | on |
| **W7 full-text** | max 8 URL |
| **Φ4 Decision Frame** | on |
| **max_results** | 30/ソース |
| **確信度** | HIGH |

---

## Adaptive Depth (G2)

> Periskopē は品質スコア (NDCG/Entropy/Coverage) が閾値 (0.5) 未満の場合、
> 自動的に depth を1段階引き上げる。Creator の介入は不要。

```
quality < 0.5 → depth + 1 (L1→L2 or L2→L3)
```

---

## Periskopē パイプライン詳細

1. Phase 0: Φ1 盲点分析 (L2+)
2. Phase 0.5: クエリ展開 (W3 バイリンガル翻訳)
3. Phase 1: 多ソース並列検索
4. Phase 1.5-1.75: 重複排除 → W4 意味リランキング → 品質フィルタ
5. Phase 1.8: W7 選択的 full-text 精読 (L2+)
6. Phase 2: 多モデル合成 (depth 連動モデル選択)
7. Phase 2.5: W6 マルチパス精錬 (L3)
8. Phase 3: 引用検証 (BC-6 TAINT 自動分類)
9. Phase 3.5: Φ4 収束思考 (Decision Frame, L2+)
10. Quality: NDCG/Entropy/Coverage 計測 + JSONL 蓄積
11. G2: Adaptive Depth (quality < 0.5 → depth 自動昇格)

---

*v1.0 — 旧 sop/modes.md v3.0 から移植。infrastructure/periskope に独立 (2026-02-28)*
