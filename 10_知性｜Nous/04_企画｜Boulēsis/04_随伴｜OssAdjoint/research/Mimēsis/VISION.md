# Mimēsis (μίμησις) — VISION

> **多体エージェントシミュレーションによる社会予測**。MiroFish × HGK 随伴PJ。
> 概念 (多体シミュレーション予測) と実装技術 (ReACT 制約, 漸進的出力, IPC) の両面を統合。
> 名の由来: μίμησις = 模倣・再現。シミュレーションの本質は模倣であり、模倣 (F) から創発 (G) が生まれる。

```typos
#prompt mimesis-vision
#syntax: v8
#depth: L2

<:role: Mimēsis (μίμησις = 模倣/再現) — MiroFish の HGK 随伴プロジェクト
  多体エージェントシミュレーションによる社会的未来予測を HGK 体系に統合する :>

<:goal: 
  1. MiroFish の概念 (多体シミュレーション予測) を HGK の認知ツールとして転用
  2. MiroFish の実装技術 (ReACT 制約, 漸進出力) を HGK インフラに移植
  3. HGK 固有の優位性 (FEP, Nomoi, 圏論的構造) で MiroFish にない厳密性を追加 :>

<:constraints:
  - MiroFish のコピーではない。概念の随伴射 (F⊣G) を構成する
  - 「予測」≠「シミュレーション」の区別を厳守 (ccl-read R1)
  - API コスト制約を設計の前提とする (40ラウンド天井)
  - 妥当性検証 (validation) なしの出力は「予測」と呼ばない
/constraints:>
```

---

## 起源: MiroFish から何を学んだか

### 概念レベル

| MiroFish の概念 | HGK 随伴射 | 変換の本質 |
|:---------------|:----------|:----------|
| 種子情報 → 世界構築 | Gnōsis → Markov Blanket 生成 | 知識グラフからシミュレーション空間を構成 |
| Agent の人格生成 | FEP ペルソナ = (prior, likelihood, precision) | パラメータ注入ではなく生成モデルとしてペルソナを定義 |
| 双平台並行シミュレーション | Multi-MB 同時推論 | 複数の Markov Blanket を並行実行し創発を観測 |
| ReportAgent (ReACT) | Poiema + Hermēneus 統合 | CCL ワークフローとしてレポート生成を制御 |
| 「上帝視角」(God's-eye view) | Observer functor | シミュレーション外部からの変数注入を圏論的に定式化 |

### 実装レベル

| MiroFish の技術 | HGK 移植先 | 優先度 |
|:---------------|:----------|:------|
| **ReACT ツール呼出制約** (最低N回義務, 連続禁止) | Hermēneus WF 実行エンジン (θ12.1 強化) | **高** |
| **漸進的セクション別保存** (.md ファイル単位) | Poiema レポート生成 | **中** |
| **chat() でレポートと対話** | Handoff 対話インターフェース | **中** |
| **ファイルベース IPC** (command.json ↔ response.json) | Motherbrain 軽量プロトコル参考 | 低 |
| **content 後処理** (重複標題除去, 見出しレベル変換) | Poiema 出力品質パイプライン | 低 |

---

## VISION: 3層アーキテクチャ

### V1. Multi-Agent Prediction Engine (多体予測エンジン)

**問題**: HGK には「もし X が起きたら社会/市場はどう動くか」を構造的に推論する手段がない。

**解決**: FEP ベースのペルソナを持つ Agent 群を並行推論させ、創発的パターンを観測する。

```
入力: 種子テキスト (ニュース, 政策, 仮説)
  ↓
Gnōsis: 知識グラフ構築 (GraphRAG 相当)
  ↓
ペルソナ生成: FEP (prior, likelihood, precision) × 人口統計パラメータ
  ↓
シミュレーション: Multi-MB 並行推論 (N ラウンド)
  ↓
Observer: 創発パターン抽出
  ↓
出力: 構造化レポート + 確信度ラベル + 妥当性限界の明示
```

**MiroFish との差異**:

| 次元 | MiroFish | Mimēsis |
|:----|:---------|:--------|
| ペルソナ | prompt テンプレート + パラメータ注入 | FEP 生成モデル (prior + precision) |
| 妥当性 | 検証なし | N-3 確信度ラベル + 予測 ≠ シミュレーション明示 |
| 制約 | OASIS エンジン依存 | HGK CCL で実行制御 |
| 記憶 | Zep Cloud (外部SaaS) | Mneme + Gnōsis (自律管理) |
| 出力 | Markdown レポート | CCL-controlled Poiema 出力 |

---

### V2. ReACT 環境強制 (θ12.1 拡張)

**問題**: HGK の θ12.1 (CCL 実行義務) は「手書き偽装禁止」だが、**ツール呼出の最低回数義務**がない。

**MiroFish の教訓**: `report_agent.py` L850-1000 のツール制約設計:
- セクションあたり最低2回のツール呼出
- 同一ツールの連続使用禁止
- ツール呼出と最終回答の競合時はツール呼出優先

**解決**: Hermēneus の WF 実行エンジンに以下を追加:

```typos
#prompt react-constraint
#syntax: v8
#depth: L1

<:constraints:
  - θ12.4 ツール呼出最低義務: L2+ WF のステップには最低 N 回のツール呼出を義務付け
  - θ12.5 連続ツール禁止: 同一ツールの連続使用を禁止 (多角化義務)
  - θ12.6 ツール優先: LLM がツール呼出と最終回答を同時出力した場合、ツール呼出を優先
/constraints:>
```

---

### V3. 漸進的出力パイプライン (Poiema 拡張)

**問題**: 現在の Poiema (構造化出力) は全体を一度に生成。長時間生成でプレビュー不可。

**MiroFish の教訓**: `ReportManager` のセクション別保存パターン:
```
reports/{report_id}/
  meta.json → outline.json → progress.json → section_XX.md → full_report.md
```

**解決**: Poiema / Handoff 出力に同パターンを適用。セクション単位保存 + リアルタイムプレビュー。

---

## HGK 動詞マッピング

| Mimēsis 機能 | HGK 動詞 | CCL |
|:------------|:---------|:----|
| 種子情報投入 | /zet (探求) | `/zet+` |
| ペルソナ生成 | /ske (発散) | `/ske+` |
| シミュレーション実行 | /pei (実験) | `/pei+` |
| 創発パターン抽出 | /sag (収束) | `/sag+` |
| レポート生成 | /kat (確定) | `/kat+` |
| 妥当性評価 | /ele (批判) | `/ele+` |

**CCL マクロ**: `@mimesis = /zet+_/ske+_F:[×N]{/pei+>>/sag+>>/ele+}_/kat+`

---

## 設計上の制約 (Anti-Hype)

| MiroFish の弱点 | Mimēsis での解決 |
|:---------------|:---------------|
| 「予測」と「シミュレーション」の混同 | 出力に `[シミュレーション結果]` ラベル必須 |
| 妥当性検証なし | バックテスト or 専門家レビューを必須ステップ化 |
| API コスト天井 (40ラウンド) | コスト上限を設計パラメータとして明示 |
| ペルソナの行動収束 | FEP precision パラメータで多様性を強制 |
| エラーリカバリなし | セクション別保存 + チェックポイント再開 |

---

## Kalon 判定

- F (発散) = 多体エージェントの並行推論 = 模倣 (mimēsis)
- G (収束) = Observer functor による構造抽出 = 創発の捕捉
- 不動点候補 = 模倣から創発が生まれ、創発が次の模倣を導く螺旋の収束点

[推定 60%] Kalon に至るにはまだ G∘F サイクルが足りない。基盤整備後に再評価。

---

## 実装ロードマップ (Phase 別)

> 旧 mirofish/ビジョン.md の6領域マップを統合。推奨順: 0 → 2 → 1 → 3 → 4 → 5

| Phase | 領域 | HGK 吸収先 | 依存 | 状態 |
|:------|:-----|:----------|:-----|:-----|
| **0** | OASIS 仿真エンジン | Mekhane (`mekhane/oasis/`) + CCL `@simulate` | なし | 未着手 |
| **1** | GraphRAG 知識構築 | Gnōsis + Anamnesis LanceDB | なし | 未着手 |
| **2** | ペルソナ動的生成 | Basanos (固定6体→動的N体), Synteleia | Phase 0 | 未着手 |
| **3** | ReportAgent + 深度対話 | Poiema + Handoff chat() | Phase 0 | **D1-D3 着手可能** |
| **4** | 双平台並行模拟 | Hermēneus CCL `*` 並行演算子統合 | Phase 0 | 未着手 |
| **5** | UX フロントエンド | Organon (参考のみ, AGPL-3.0 制約) | なし | 低優先 |

> [!CAUTION]
> MiroFish は AGPL-3.0。コード直接再利用は HGK 全体を AGPL 汚染する可能性あり。
> 戦略: パターンと技術を学び、HGK ネイティブで再実装。OASIS (Apache-2.0) は直接依存可能。

---

## 着想元

- [MiroFish](https://github.com/666ghj/MiroFish) — 14.2k Stars, AGPL-3.0
  - 精読: simulation_runner.py, report_agent.py, oasis_profile_generator.py, simulation_ipc.py (計4332行)
- [Generative Agents](https://arxiv.org/abs/2304.03442) (Park et al. 2023, cited 3395)
- [AgentSociety](https://arxiv.org/abs/2502.17378) (Piao et al. 2025, cited 109)
- [OASIS](https://github.com/camel-ai/oasis) — CAMEL-AI Multi-Agent Simulation Engine

---

*VISION v0.1 — 2026-03-11*
