# 研究論文

> 最新の正本 / blocker / 次アクションは [現況台帳.md](現況台帳.md) を参照。

## 一覧

### FEP 分解型論文

FEP の操作的分解型を体系的に列挙し、HGK の7座標体系との整合性を検証する論文。

| バージョン | ファイル | 日付 | 主な変更 |
|:-----------|:---------|:-----|:---------|
| v0.5 | [FEPの操作的分解型_v05.md](FEPの操作的分解型_v05.md) | 2026-03-11 | Two-layer filter + 完全性証明 |
| v0.3 | [FEPの操作的分解型_v03.md](FEPの操作的分解型_v03.md) | 2026-03-08 | 「一貫性」への主張後退 + 先行研究統合 |

**致命的課題** (反証 [FEP分解型_系統的批判_反証.md](反証/FEP分解型_系統的批判_反証.md) より):
- F2: 循環論法 — HGK が分解の枠組みを決定している疑い
- F1: 「型」の数学的定義が不十分
- F7: HGK との対応が「アナロジー」止まり

**次アクション**: blind protocol の設計、または論文の射程縮小。本文の追記は保留。

---

### Coherence Invariance 論文

`G∘F` による adaptive chunking で、閾値 `τ` を変えても平均 coherence がほぼ不変に保たれることを示す論文。

| ファイル | 内容 |
|:---------|:-----|
| [コヒーレンス不変性定理_草稿.md](コヒーレンス不変性定理_草稿.md) | 現行正本 |
| [コヒーレンス不変性定理_構成案.md](コヒーレンス不変性定理_構成案.md) | 構成案 |

**現在地**:
- `ビジョン.md` では Phase 1 の速報候補
- 草稿には概要・理論・実験・議論・結論が通っている

**次アクション**: 投稿前の最終監査（ベニュー前提、再現情報、残論点の洗い出し）

---

### LLM Body 論文

「LLM に身体はあるか？」— Markov blanket の厚さを身体性の基質非依存的尺度として提案。
忘却論由来の衛星論文として、現行正本は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/drafts/standalone/llm_embodiment/` 配下に移した。

| ファイル | 内容 |
|:---------|:-----|
| [LLMに身体はあるか_統合草稿.md](../03_忘却論｜Oblivion/drafts/standalone/llm_embodiment/LLMに身体はあるか_統合草稿.md) | 現行正本 (統合草稿, Draft v0.5.3) |
| [LLMに身体はあるか_構成案.md](_archive/body_A_B_drafts/LLMに身体はあるか_構成案.md) | 構造アウトライン (archive) |
| [論文A_LLMに身体はあるか_草稿.md](_archive/body_A_B_drafts/論文A_LLMに身体はあるか_草稿.md) | 分割稿 (本文系, 従属) |
| [論文B_デジタル身体性の測定_草稿.md](_archive/body_A_B_drafts/論文B_デジタル身体性の測定_草稿.md) | 分割稿 (測定系, 従属) |

**残 blocker** (反証 [LLMに身体はあるか_反証.md](反証/LLMに身体はあるか_反証.md), 2026-03-21 更新):
- C3: `R(s,a)` の実測が未完了

**解決済み**:
- C1: vanilla LLM の `S(B) > 0` operational definition
- C5: 離散 Helmholtz の接地
- C2: body spectrum の scope 調整
- C4: affect 議論の qualification

**次アクション**: C3 (`R(s,a)` 実測) → 投稿パッケージ整備

---

### 境界は不動点である

Markov blanket を所与ではなく、状態と境界候補の相互決定から出る Galois fixed point として導く基幹論文。

| ファイル | 内容 |
|:---------|:-----|
| [境界は不動点である_v0.1_基幹草稿.md](境界は不動点である_v0.1_基幹草稿.md) | 現行本文正本 |
| [境界は不動点である_v0.1_基幹草稿.meta.md](境界は不動点である_v0.1_基幹草稿.meta.md) | 共同台帳・判定履歴・SOURCE 状態 |
| [_archive/boundary_fixedpoint_20260427/](_archive/boundary_fixedpoint_20260427/) | C4 再判定提案、M3 妥当性レビュー、M6 Batch3 narrative audit の退避先 |

**現在地**:
本体 `§1`-`§7` は初稿化済み。補助レポート 3 本は meta に統合し、トップレベル正本を本文 + meta の 2 本へ圧縮済み。

**次アクション**: page-precise citation 補強、A0 物理正当化 SOURCE 補強、Varela 1979 本文取得時の §6 補強。

---

## 反証ディレクトリ

自己反証は論文品質の核心。各論文に対する系統的批判を保管。

| ファイル | 対象 | 判定 |
|:---------|:-----|:-----|
| [FEP分解型_系統的批判_反証.md](反証/FEP分解型_系統的批判_反証.md) | FEP 分解型 v0.1 | 致命的3 + 重大4 |
| [LLMに身体はあるか_反証.md](反証/LLMに身体はあるか_反証.md) | LLM Body v0.5.0 追跡 | RESOLVED (C3 residual) |
