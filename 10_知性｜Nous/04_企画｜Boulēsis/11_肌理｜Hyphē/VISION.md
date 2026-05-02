# Phantasia Field 統一ビジョン — 全情報を意味空間に溶かす

> **Status**: 設計 (2026-03-31)
> **Origin**: Creator の直観 — 「Phantasia (セッション) は Phantasia のインスタンスに過ぎない」
> **Principle**: 全ての情報を意味空間に溶解し、出自はタグとして保持する。分離ではなく統一。

## 1. 核心命題

> 「私は全ての情報を、意味空間に溶かして DB 化したい」 — Creator, 2026-03-31

現行の Gnōsis (論文)・Sophia (知識)・Chronos (対話)・Kairos (Handoff) は**別々のインデックス**。
これは情報の出自 (source) を**構造**として扱っている。

Creator のビジョン: 出自は**タグ**であって構造ではない。
全ての情報は Phantasia Field (統一意味場) に dissolve し、recrystallize 時に source_type でフィルタすれば十分。

## 2. 名前の再定義

### なぜ「Gnōsis」ではなく「Phantasia」か

| 概念 | 語源 | 役割 |
|:-----|:-----|:-----|
| **Hyphē** (ὑφή) | 織物・肌理 | チャンキングの理論 — CKDF 4層アーキテクチャ。意味空間の Markov blanket を検出する数学 |
| **Phantasia** (φαντασία) | 像を結ぶ力 | 統一意味場 — Hyphē 理論に基づいて構築された埋め込み空間。溶解と結晶化の場 |
| **Phantazein** (φαντάζειν) | 像を結ぶ行為 | 場の上で動く LLM — Phantasia Field 上で像を結ぶ知性。自己消化、構造認識、応答生成 |

**Gnōsis** (γνῶσις = 知識) は汎称であり、Hyphē→Phantasia の結晶化という本質的構造を反映していない。
DB の名前は **Phantasia Field** — 全情報が溶解し、再結晶する場。

### 旧名称との対応

| 旧名 | 新名 | 変化 |
|:-----|:-----|:-----|
| GnosisIndex | **Phantasia Field** (統一場) | 論文専用 → 全ソース統一 |
| SophiaIndex | Phantasia Field `source_type: sophia` | 独立索引 → 統一場のフィルタ |
| ChronosIndex | Phantasia Field `source_type: chronos` | 同上 |
| KairosIndex | Phantasia Field `source_type: kairos` | 同上 |
| PhantasiaField (現行) | Phantasia Field `source_type: session` | セッション専用 → 統一場の一インスタンス |

### MCP サーバーの統合

| 旧サーバー | 新サーバー | 変化 |
|:-----------|:-----------|:-----|
| `mneme_server.py` (統合検索) | **Phantazein MCP** | 検索サーバー名を mneme → phantazein に |
| `phantazein_mcp_server.py` (Boot/Health) | ↑ に統合 | Boot + 検索を一つの MCP に |

`30_記憶｜Mneme/` (ディレクトリ) は変更しない — 物理的な記憶の格納場所として正しい名前。
変えるのは **MCP サーバー** (検索インターフェース) の名前のみ。

Hub の `BACKENDS` キー: `"mneme"` → `"phantazein"`。

## 3. アーキテクチャ

### 3.1 溶解パイプライン (dissolve)

```
情報源                    前処理               Hyphē             Phantasia Field
─────────              ────────           ──────             ────────────────
論文 PDF/MD  ─────┐
Handoff MD   ─────┤
セッションログ  ────┤──→ ソース別パーサー ──→ Nucleator G∘F ──→ dissolve()
知識項目 MD  ─────┤     (source_type タグ)   (統一チャンカー)   (統一 FAISS)
コード .py   ─────┤
Doxa MD     ─────┘
```

**不変条件**: 全チャンクは以下のメタデータを持つ

```python
{
    "source_type": str,      # "paper" | "handoff" | "session" | "sophia" | "code" | "doxa" | "rom"
    "source_path": str,      # 元ファイルのパス
    "title": str,            # ドキュメントタイトル
    "created_at": datetime,  # 溶解日時
    "session_id": str,       # 関連セッション (あれば)
    "project_id": str,       # 関連プロジェクト (あれば)
    # Nucleator 由来メトリクス
    "coherence": float,      # 内部一貫性
    "drift": float,          # 文脈逸脱度
    "efe": float,            # 期待自由エネルギー
    "precision": float,      # 精度勾配
}
```

### 3.2 結晶化 (recrystallize)

```python
# 全ソース横断検索 (cross-pollination)
field.recall(query="FEP と能動推論", mode="exploit")

# 論文だけ
field.recall(query="FEP", source_filter="paper")

# Handoff だけ
field.recall(query="Pinakas 設計", source_filter="handoff")

# Explore モード (低密度領域から新奇発見)
field.recall(query="随伴", mode="explore")
```

### 3.3 Phantazein (場の上の知性)

```
Phantasia Field (統一意味場)
        ↑ dissolve          ↓ recrystallize
        |                    |
   Phantazein ──────────────────────────
   (場の上の LLM)
   - 自己消化: self_digest() — セッションを場に溶解
   - 構造認識: 将来的に raw data の自動構造化
   - Boot 統合: phantazein_boot() — 場から意図に合致する文脈を結晶化
```

## 4. CKDF との対応

全ソースに Hyphē の CKDF 4層が適用される:

| CKDF 層 | 統一場での意味 |
|:--------|:-------------|
| **L0** 格子構造 | 全情報の意味空間 Ω + 類似度前順序。論文もセッションも同一空間 |
| **L1** Galois 接続 | dissolve (F) ⊣ recrystallize (G)。ソース不問 |
| **L2** 座標検出 | 6座標 TypedRelation。ソース横断で座標構造が発現するか = 未検証の問い |
| **L3** 局所不動点 | チャンク = MB の不動点。Nucleator が全ソースに統一適用 |

### Cross-Pollination 仮説

統一場の最大の価値: **異なるソース間の意味的接触が自然に起きる**。

- 論文の概念がセッションの議論と隣接する
- コードパターンが理論文書と結びつく
- Handoff の設計判断が関連論文を引き寄せる

これは分離索引では原理的に起きない。検索ではなく**発見**のエンジン。

## 5. 実装移行計画

### Phase 0: 現行 DB 構築 (即時)

このマシン (Debian) で Phantasia Field を構築可能にする。
現行の GnosisIndex + KnowledgeIndexer パイプラインを動かし、全知識ソースを溶解する。

- 埋め込み: Vertex AI `gemini-embedding-2-preview` (dim=3072)
- ストレージ: FAISS
- チャンカー: MarkdownChunker (Phase 0)、Nucleator (Phase 1 で統一)

### Phase 1: Nucleator 統一

全ソースのチャンキングを Nucleator (G∘F 固定点) に統一。
現行の MarkdownChunker は Nucleator のフォールバック。

### Phase 2: 索引統合

SearchEngine の 4 索引 (gnosis/sophia/chronos/kairos) を Phantasia Field に統合。
source_type タグで事後フィルタ可能にする。

- `SearchEngine.search(query, scope="all")` → Phantasia Field 全体検索
- `SearchEngine.search(query, scope="papers")` → `source_filter="paper"`
- `SearchEngine.search(query, scope="code")` → `source_filter="code"`

### Phase 3: Phantazein 統合

Phantazein MCP が Phantasia Field を直接操作する。
Boot 時の文脈復元 = `field.recall(intent, mode="exploit")`。
自己消化 = `field.dissolve(session_text, source="session")`。

### Phase 4: MCP 独立化

Phantasia Field を独立 MCP サーバーとして公開。
Hub 経由でも直接でもアクセス可能にする。

## 6. FEP 的意味

自由エネルギー最小化 = 世界モデルの統一。

- **分離索引** = 世界モデルが分裂している。論文の世界とセッションの世界が断絶。
- **統一場** = 世界モデルが一つ。全情報が同一の意味空間で関係し合う。

情報の出自で構造を分けることは、FEP に反する。
出自はメタデータであって、意味空間の構造ではない。

## 7. 未解決の問い

| # | 問い | 種別 |
|:--|:-----|:-----|
| Q-A | Nucleator が論文チャンクに適用可能か？論文の構造 (Abstract/Method/Results) と Nucleator の密度ベース境界検出は整合するか | epistemic |
| Q-B | BGE / Vertex embedding が論文と会話ログの異なるレジスタを同一空間で意味的に近接配置できるか | epistemic |
| Q-C | L2 座標検出はソース横断で発現するか？異なるソースのチャンクに共通の TypedRelation 座標構造が存在するか | 研究 |
| Q-D | スケーラビリティ: 27,432 論文 + 数千セッション + コード → FAISS の性能は十分か | 工学 |

---

## 接続

- [README.md](README.md) — Hyphē 肌理の全体像 + CKDF
- [ckdf_theory.md](ckdf_theory.md) — CKDF 完全定義
- [phantasia_field.py](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/anamnesis/phantasia_field.py) — 現行実装
- [phantasia_pipeline.py](../../../20_機構｜Mekhane/_src｜ソースコード/mekhane/anamnesis/phantasia_pipeline.py) — dissolve/recrystallize パイプライン

---

*Created: 2026-03-31 — Creator のビジョン「全ての情報を意味空間に溶かす」から結晶化*
