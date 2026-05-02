# CAG 派生タスク引き継ぎ (Handoff)

> 📅 作成: 2026-03-15T08:50 | 元セッション: CAG Research (ca10ff22)
> 前提: [cag_research.md](file:///home/makaron8426/.gemini/antigravity/brain/ca10ff22-5832-459d-9f21-7061b6fbb796/cag_research.md) のリサーチレポートを参照のこと

---

## タスク概要

CAG (Cache-Augmented Generation) リサーチで抽出された 5 つの知的活動のうち、タスク 1 (PoC 実装) は元セッションで着手中。以下の 4 タスクを別セッションに引き継ぐ。

---

## タスク 2: CacheBlend PDF 精読

| 項目 | 詳細 |
|:-----|:-----|
| CCL | `/ccl-read` |
| 対象 | Yao et al. "CacheBlend: Fast Large Language Model Serving for RAG with Cached Knowledge Fusion" |
| DOI | [10.1145/3689031.3696098](https://doi.org/10.1145/3689031.3696098) |
| arXiv | [2405.16444](https://arxiv.org/abs/2405.16444) |
| 被引用 | 116 件 (2026-03-15) |
| 焦点 | **Selective KV Recompute アルゴリズム**の詳細。どのトークンを再計算し、どのトークンをスキップするかの判定基準。TTFT 2.2-3.3× 削減の具体的メカニズム |
| なぜ | Gnōsis (50,985 docs) は全載せ不可。部分キャッシュ合成が唯一の現実的なパス |
| 成果物 | `cag_cacheblend_analysis.md` — アルゴリズム図解 + HGK への適用可能性評価 |

---

## タスク 3: Context Rot と lost-in-the-middle の等価性検証

| 項目 | 詳細 |
|:-----|:-----|
| CCL | `/noe+` |
| 仮説 | HGK の Context Rot (N≥30 で品質劣化) と CAG 論文の "lost-in-the-middle" (Li et al., 2024b) は同一現象の異なる表現 |
| 根拠 | 両者とも「コンテキスト長増大 → 中間部分の注意力低下 → 精度劣化」のパターン |
| 参照論文 | Li et al. "Lost in the Middle: How Language Models Use Long Contexts" (2024) |
| 問い | Context Rot は lost-in-the-middle の特殊ケースか？独自の追加メカニズム (会話の蓄積 = コンテキスト汚染) があるか？ |
| 成果物 | `/noe+` 結果 + 理論的分析 |

---

## タスク 4: Hyphē DB と CAG 前処理の統合設計

| 項目 | 詳細 |
|:-----|:-----|
| CCL | `/ccl-plan` |
| 背景 | Hyphē DB の密度推定 (chunking + density estimation) は「何をキャッシュに載せるか」の選別そのもの |
| 参照 | `20_機構｜Mekhane/_src｜ソースコード/mekhane/hyphe/` (実装) + `linkage_hyphe.md` (理論) |
| 問い | Hyphē の G∘F ファンクターの密度推定関数を、CAG のコンテキスト事前選別に転用できるか？ |
| 成果物 | 統合設計ドキュメント + 実装計画 |

---

## タスク 5: SCBench で HGK 長コンテキスト手法のベンチマーク

| 項目 | 詳細 |
|:-----|:-----|
| CCL | `/pei+` |
| 対象 | Li et al. "SCBench: A KV-Cache-Centric Analysis of Long-Context Methods" (arXiv:2412.10319, 39 cited) |
| 目的 | 現在の Boot 方式 (user_rules 注入) の品質を定量測定する基準線を確立 |
| 問い | HGK の Boot Context サイズ (推定 15-20K tokens) は SCBench のどの区間に該当し、どの手法が最適か？ |
| 成果物 | ベンチマーク結果 + 推奨キャッシュ戦略 |

---

## 関連リソース

- リサーチレポート: `brain/ca10ff22.../cag_research.md`
- 原典論文: arXiv:2412.15605 (Chan et al., "Don't Do RAG")
- Semantic Scholar ID: S2 検索で各論文を取得可能
- Mneme: `mcp_mneme_search("Cache-Augmented Generation")` で関連 KI を検索
