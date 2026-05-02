# Synteleia (συντέλεια) — 12法メタ認知監査システム

> **Etymology**: syn (共に) + telos (完成) = 「共に完成へ向かう」
> **Position**: Hegemonikón 認知アーキテクチャの L0 検出層
> **Status**: v2.0 — 12法 (Nomoi) ベースに再設計

---

## 本質

> **Synteleia は Hóros 12法の自動検出器である。**
> 3原理 × 4位相 = 12 Agent が、テキスト・コードの品質を並列監査する。

### FEP 的位置づけ

| 項目 | 12法 (Nomoi) | Synteleia |
|------|-------------|-----------|
| 役割 | 認知制約の定義 | 制約違反の L0 検出 |
| 構造 | 3 Stoicheia × 4 Phase | 3×4 = 12 Agent |
| 完全性 | FEP から演繹された完全集合 | 12法を網羅 |

---

## 3×4 テンソル積構造

```
            │ P1 Aisthēsis │ P2 Dianoia │ P3 Ekphrasis │ P4 Praxis  │
            │   (入力)     │   (処理)   │   (出力)     │   (行動)   │
────────────┼──────────────┼────────────┼──────────────┼────────────┤
S-I         │ N01Entity    │ N02Track   │ N03Confid    │ N04Guard   │
Tapeinoph.  │ 曖昧参照検出 │ ラベル欠如 │ 不可能断定   │ 破壊操作   │
────────────┼──────────────┼────────────┼──────────────┼────────────┤
S-II        │ N05Explore   │ N06Anomaly │ N07Express   │ N08Tool    │
Autonomia   │ 検索省略     │ 矛盾検出   │ 完了偽装     │ 先延ばし   │
────────────┼──────────────┼────────────┼──────────────┼────────────┤
S-III       │ N09Source    │ N10Taint   │ N11Action    │ N12Execute │
Akribeia    │ TAINT断言    │ 精度混同   │ 5W1H欠落     │ CCL手書き  │
────────────┴──────────────┴────────────┴──────────────┴────────────┘
```

### 12 Agent 一覧

| Agent | Nomos | 検出対象 |
|:------|:------|:---------|
| N01EntityAgent | N-1 実体を読め | 曖昧な参照・指示語 |
| N02UncertaintyAgent | N-2 不確実性を追跡 | 確信度ラベル欠如の断定 |
| N03ConfidenceAgent | N-3 確信度を明示 | 不可能断定・過剰確信 |
| N04IrreversibleAgent | N-4 不可逆前に確認 | スコープ逸脱・セキュリティ |
| N05ExplorationAgent | N-5 能動的に探せ | 早すぎる最適化 |
| N06AnomalyAgent | N-6 違和感を検知 | 論理矛盾・自己否定 |
| N07ExpressionAgent | N-7 主観を述べよ | 動機不明確・完了偽装 |
| N08ToolUseAgent | N-8 道具を使え | 先延ばし表現 |
| N09SourceAgent | N-9 原典に当たれ | TAINTによる断言 |
| N10TaintAgent | N-10 SOURCE/TAINT | 精度ラベルの混同 |
| N11ActionableAgent | N-11 行動可能に | 構造品質・未定義用語 |
| N12PrecisionAgent | N-12 正確に実行 | CCL誤用・未完了ブロック |

---

## 実行モデル

### 内積モード（@syn·）— デフォルト

12 Agent を**並列実行**し、結果を**統合**。

```
入力 → [N01..N12] → 統合 → AuditResult

CCL: @syn·
呼び出し: 12 回 (並列)
```

### 外積モード（@syn×）— 徹底検証

原理内の P1 (入力段階) の検出結果を P2-P4 に注入し**交差検証**。

```
           │ P2 Dianoia │ P3 Ekphrasis │ P4 Praxis  │
───────────┼────────────┼──────────────┼────────────┤
S-I  N01 → │ N01×N02    │ N01×N03      │ N01×N04    │
S-II N05 → │ N05×N06    │ N05×N07      │ N05×N08    │
S-III N09 →│ N09×N10    │ N09×N11      │ N09×N12    │

CCL: @syn×
呼び出し: 12 内積 + 9 交差 = 21 回 (並列)
```

### 深度連動 (with_depth)

| 深度 | 構成 | Agent 数 |
|:-----|:-----|:---------|
| L0 | N06AnomalyAgent のみ | 1 |
| L1 | 12法内積 | 12 |
| L2 | 12法内積 + SemanticAgent (L2) | 13 |
| L3 | 12法外積 + SemanticAgent (L2) | 13 + 9交差 |

---

## ディレクトリ構造

```
mekhane/synteleia/
├── base.py                    # AuditAgent 基底クラス
├── orchestrator.py            # 3×4 オーケストレーター
├── pattern_loader.py          # パターン辞書ローダー
├── nomoi/                     # 12法エージェント (v2.0)
│   ├── __init__.py            # 原理/位相グループ + エクスポート
│   ├── n01_entity.py          # S-I × P1
│   ├── ...                    # (12ファイル)
│   ├── n12_precision.py       # S-III × P4
│   └── patterns.yaml          # 全12法のパターン統合YAML
├── poiesis/                   # 旧・生成層 (後方互換)
├── kritai/                    # 旧・審査層 (後方互換 + L2/L3)
│   ├── semantic_agent.py      # L2 LLM 意味監査
│   ├── multi_semantic_agent.py # L2 Multi-LLM アンサンブル
│   └── consensus_agent.py     # L3 コンセンサス監査
└── tests/
```

---

## 旧体系との関係

| 旧 (v1) | → 新 (v2) |
|:---------|:----------|
| OusiaAgent O-001〜006 | → N01Entity |
| OusiaAgent O-010 | → N11Action |
| SchemaAgent S-* | → N11Action |
| HormeAgent H-* | → N07Express |
| LogicAgent LOG-* | → N06Anomaly |
| OperatorAgent OP-001〜005 | → N12Execute |
| OperatorAgent SEC-* | → N04Guard |
| PerigrapheAgent P-* | → N04Guard |
| KairosAgent K-001〜006 | → N08Tool |
| KairosAgent K-010〜012 | → N05Explore |
| CompletenessAgent COMP-001〜014 | → N12Execute |
| CompletenessAgent 必須要素 | → N11Action |

新規パターン (旧体系にない): N02, N03, N09, N10

---

*Design v1: 2026-02-01 / v2 Redesign: 2026-03-15*
*Basis: Hóros 12法 (3 Stoicheia × 4 Phase)*
