# 00_信念｜Beliefs — Doxa スキーマ v1.0

> **FEP 演繹**: Doxa = P(s) — variational inference を経て安定化した prior。
> 「変わらない」のではなく「反証を経てなお残った信念」= Fix(G∘F) 近傍。
> confidence は precision weight (π_s)。高い = 安定。低い = 最近形成、要検証。

---

## POMDP 位置

| 変数 | 意味 | Doxa との関係 |
|:-----|:-----|:-------------|
| P(s) | prior 信念 | Doxa = 安定化した P(s) |
| Q(s\|o) | 事後信念 | ROM/Handoff = Q(s\|o)。Doxa に昇格する前段 |
| 区別 | Q(s\|o) → P(s) | 反復観測で安定 → Doxa 昇格 |

---

## ディレクトリ構造

```
00_信念｜Beliefs/
├── README.md          (本ファイル)
├── _global/           (scope: global — プロジェクト横断の普遍教訓)
│   └── doxa_*.typos
└── _project/          (scope: project — HGK 固有の教訓)
    └── doxa_*.typos
```

scope 分離の理由: ECC instinct v2.1 が発見した "cross-project contamination" 問題。
HGK 翻訳: MB 境界の明示化。local MB (project) の信念が nested MB (global) を汚染しない。

---

## Doxa ファイルスキーマ

### ファイル名規約

`doxa_{id}.typos` — id は kebab-case、64文字以内、`[a-z0-9-]` のみ。

### YAML Frontmatter

```yaml
---
id: prefer-source-over-memory        # 一意識別子 (kebab-case)
trigger: "記憶に基づく断定をしようとした時"  # いつ発動するか
confidence: 0.85                      # π_s precision weight [0.0, 1.0]
scope: global                         # global | project
domain: cognition                     # 分類 (下表参照)
source: cross-session-observation     # 信念の由来 (下表参照)
origin_session: "393a4a98-..."        # 最初に観測されたセッション ID
created_at: "2026-04-12"
updated_at: "2026-04-12"
evidence_count: 3                     # 裏付け観測の累計回数
---
```

### domain 分類

| domain | 内容 |
|:-------|:-----|
| cognition | 認知パターン・思考の癖 |
| architecture | 設計原則・構造判断 |
| process | 作業手順・ワークフロー |
| tool-usage | ツールの使い方・落とし穴 |
| philosophy | 哲学的原則・価値判断 |
| writing | 執筆・表現のパターン |

### source 分類

| source | 意味 | 信頼度 |
|:-------|:-----|:-------|
| explicit-teaching | Tolmetes が明示的に教えた | 高 |
| cross-session-observation | 複数セッションで同じパターン観測 (ROM マイニング結果含む) | 中-高 |
| single-session-observation | 1 セッションで観測 | 低-中 |
| violation-derived | 違反事例から抽出 | 高 (反証から学んだ) |

### Body (Typos v8.4)

```typos
#prompt doxa_{id}
#syntax: v8.4

<:content action:
  何をすべきか / 何を避けるべきか (1-3 行)
/content:>

<:content evidence:
  なぜこの信念を持つか。SOURCE ラベル付きの根拠。
  - [SOURCE: V-xxx] 違反事例からの教訓
  - [SOURCE: session-xxx] 観測された成功パターン
  - [SOURCE: Tolmetes] 明示的指示
/content:>

<:content exceptions:
  この信念が適用されない条件 (もしあれば)
/content:>
```

---

## Confidence (π_s) の運用

| 範囲 | 意味 | 運用 |
|:-----|:-----|:-----|
| 0.9-1.0 | 確立された信念 | 自動適用。疑う必要なし |
| 0.7-0.9 | 安定した信念 | 通常適用。例外があれば報告 |
| 0.5-0.7 | 形成中の信念 | 適用するが注意深く。反例を積極的に探す |
| 0.3-0.5 | 仮説的信念 | 適用しない。観察のみ |
| 0.0-0.3 | 棄却候補 | 反証が蓄積。削除を検討 |

### 更新規則

- 信念を支持する観測: confidence += 0.05, evidence_count += 1
- 信念に反する観測: confidence -= 0.1 (反証は支持より重い)
- confidence < 0.2 が 30 日続く: 棄却候補としてフラグ

---

## 昇格パイプライン (η: project → global)

```
ROM (Q(s|o), 一回性) 
  ↓ 反復観測 (evidence_count ≥ 2)
Doxa/_project (P(s), project-scoped)
  ↓ η 条件: 2+ project に出現 AND confidence ≥ 0.8
Doxa/_global (P(s), universal)
```

η (単位射) の条件:
1. **cross-project evidence**: 異なる 2+ プロジェクトで同じパターンを観測
2. **confidence threshold**: 平均 confidence ≥ 0.8
3. **no active counter-evidence**: 直近 30 日に反証なし

降格 (ε: global → project override):
- project 固有の例外が発見された場合、_project/ に override エントリを作成
- override は _global の同名 Doxa より優先

---

## ROM との関係

| 種別 | POMDP | 寿命 | 構造 |
|:-----|:------|:-----|:-----|
| ROM | Q(s\|o) | 一回性 (セッションの記録) | DECISION 列挙 |
| Doxa | P(s) | 安定的 (反復検証済み) | trigger + action + evidence |

ROM から Doxa を抽出する操作 = G (忘却関手): 具体的文脈を忘却し、普遍的パターンだけを保持する。

---

## 出典

- ECC instinct schema (affaan-m/everything-claude-code, MIT)
- HGK FEP framework (axiom_hierarchy.md)
- HGK 圏論基盤 (category-foundations)

*Doxa Schema v1.0 — 2026-04-12*
