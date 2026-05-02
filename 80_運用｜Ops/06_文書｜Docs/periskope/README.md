---
doc_id: "INFRA_PERISKOPE"
version: "1.0"
tier: "INFRASTRUCTURE"
status: "CANONICAL"
created: "2026-02-28"
role: "入力インフラ — 外部世界の知識を WF に取り込む"
dual: "Mneme (出力インフラ — WF の結果を外部記憶に永続化する)"
---

# Periskopē — 入力インフラ層

> **Mneme (出力) ⊣ Periskopē (入力)**: FEP の Action / Inference サイクルの対称的インフラ。
>
> - **Mneme**: 内部 → 外部 (認知結果の永続化) = Action 側
> - **Periskopē**: 外部 → 内部 (外部知識の取り込み) = Inference 側

---

## MCP ツール一覧

| ツール | 用途 | 時間 |
|:-------|:-----|:-----|
| `periskope_search` | 多ソース並列検索 (軽量) | 10-15秒 |
| `periskope_research` | フルパイプライン (検索→合成→引用検証→レポート) | 30秒-4分 |
| `periskope_sources` | クエリに最適なソース推薦 | 即時 |
| `periskope_track` | 調査テーマの進捗管理 | 即時 |
| `periskope_benchmark` | 検索品質ベンチマーク | 数分 |
| `periskope_metrics` | 品質メトリクス照会 | 即時 |

---

## 利用可能動詞

> すべての動詞が Periskopē を「呼べる」が、座標的に推奨される動詞がある。

| 推奨度 | 動詞 | 座標 | Periskopē での用途 |
|:-------|:-----|:-----|:------------------|
| ★★★ | **V03 /zet** (探求) | A×E | 認識のために環境に働きかける = 検索そのもの |
| ★★★ | **V07 /pei** (実験) | A×Explore | 未知領域の探索的情報収集 |
| ★★☆ | V01 /noe (理解) | I×E | 検索結果を入力とした深い理解 |
| ★★☆ | V05 /ske (発散) | I×Explore | 仮説空間拡張のための外部情報注入 |
| ★★☆ | V14 /ops (俯瞰) | I×Ma | 俯瞰に必要な広域情報収集 |

### 推奨度の座標根拠

- **★★★ (一級)**: Flow=A (行為) を含む動詞。外部環境に能動的に働きかける
- **★★☆ (二級)**: Flow=I (推論) の動詞。検索結果を入力として使う
- **★☆☆ (補助的)**: 上記以外。必要に応じて利用可能だが主用途ではない

---

## 利用規約

1. **WF Phase 内で呼ぶ**: Periskopē MCP は各動詞の WF Phase 内で呼び出す
2. **CCL マクロから直接呼ばない**: マクロは純粋 CCL。Periskopē 連携は WF 粒度で組み込む
3. **depth は動詞の認知代数 (+/-) に連動**: `+` = L3 (Deep), 無印 = L2 (Standard), `-` = L1 (Quick)
4. **結果は Mneme に保存**: Periskopē の出力は `mneme/.hegemonikon/workflows/` に保存する

---

## 旧 /sop からの移行

| 旧 /sop の要素 | 移行先 |
|:---------------|:------|
| Periskopē パラメータ | [depth_mapping.md](depth_mapping.md) |
| 外部調査依頼書 | [templates.md](templates.md) |
| depth ↔ mode 対応 | [depth_mapping.md](depth_mapping.md) |
| 知恵の充足度チェック | `/lys[Pr:U] >> /epo[Pr:U] >> /dok[Pr:U]` |
| X-series バイアス知識 | Dokimasia SKILL.md に移植済み |
| @search マクロ | `ccl-search.md` v3.0 |
| @gap マクロ | `ccl-gap.md` |

---

*v1.0 — 旧 K4 Sophia (/sop) の完全吸収に伴い新設。Mneme と双対の入力インフラ層 (2026-02-28)*
