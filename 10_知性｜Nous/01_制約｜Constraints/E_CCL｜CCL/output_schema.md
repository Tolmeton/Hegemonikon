# CCL Output Schema — スキル出力積の型宣言仕様 v1.0

> **正本**: operators.md §16 (変数と射影) の補助仕様
> **目的**: スキルが返す積 (product) の成分を宣言し、`$result.field` 射影の静的検証を可能にする
> **Origin**: 2026-04-04 — CCL 変数設計 A+B ハイブリッド

---

## 1. 概要

各スキルは実行後に WM 変数を設定する。この WM 変数は**スキル出力の積の成分名**でもある (operators.md §16.4.3)。

`<:output:>` ブロックは、その積の型を Typos 構文で宣言する。

```
スキル実行 → 積 (A × B × C × ...) を出力
<:output:> = その積の成分名と型の宣言
$result.field = 積の射影 (π₁, π₂, ...)
hermeneus = <:output:> に基づく静的検証
```

---

## 2. 型システム

### 2.1 基本型

| 型 | 意味 | 由来 |
|:---|:-----|:-----|
| `String` | テキスト (自由形式) | 汎用 |
| `O` | Ousia (本質的洞察) | Telos 定理型 |
| `S` | Schema (構造・計画) | Methodos 定理型 |
| `K` | Krisis (判断・確信度) | Krisis 定理型 |
| `H` | Hormē (衝動・動機) | Orexis 定理型 |
| `Ω` | Sēmeion (信号・差分) | Diástasis/Chronos 定理型 |

### 2.2 修飾型

| 記法 | 意味 | 例 |
|:-----|:-----|:---|
| `[T]` | T の配列 | `[String]` = テキストのリスト |
| `T?` | T またはなし (オプショナル) | `String?` = あるかもしれないテキスト |
| `[T]?` | オプショナルな配列 | `[String]?` = リストがあるかもしれない |

### 2.3 型推論ルール

- フィールドに型注釈がない場合 → `String` (デフォルト)
- 動詞の出力は定理型から自動推論 (operators.md §16.7)
- 配列型は明示が必要 (`[String]` は推論されない)

---

## 3. Base パターン (mixin)

66スキルの WM 全数調査から導出された3つのアーキタイプ。

### 3.1 wm-L: 知覚型 (Sensory)

> **適用**: S極スキル (Telos-S, Krisis-S, Methodos-S, Diástasis-S, Orexis-S, Chronos-S)
> **認知座標**: Flow=S (知覚)。外部/内部の信号を受け取り、構造化する
> **FEP**: sensory precision ↑, prior precision ↓ — 入力を最大化し推論を抑制

```typos
<:output mixin="wm-L":
  goal: String             # この実行の目的
  gaps: [String]?          # 知覚で検出した欠落・盲点
  next: String             # 次のアクション (→/verb 形式)
/output:>
```

**専用フィールドの典型例** (スキルごとに追加):

| スキル | 専用フィールド | 型 |
|:-------|:---------------|:---|
| /the (V25 観照) | `perceived`, `suspended` | `[String]`, `[String]?` |
| /ant (V26 検知) | `baseline`, `deltas` | `String`, `[Ω]` |
| /ere (V27 探知) | `scope`, `discoveries`, `absences`, `surprises` | `String`, `[String]`, `[String]?`, `[String]?` |
| /agn (V28 参照) | `pattern`, `matches`, `mismatches`, `coverage` | `String`, `[String]`, `[String]?`, `K` |
| /sap (V29 精読) | `facts`, `priors`, `gaps` | `[String]`, `[String]`, `[String]` |
| /ski (V30 走査) | `map`, `hotspots`, `gaps` | `String`, `[String]`, `[String]` |
| /prs (V31 注視) | `details`, `deviations` | `[String]`, `[Ω]?` |
| /per (V32 一覧) | `structure`, `statistics` | `String`, `String` |
| /apo (V33 傾聴) | `strengths`, `balance` | `[String]`, `String` |
| /exe (V34 吟味) | `issues`, `balance` | `[String]`, `String` |
| /his (V35 回顧) | `records`, `deviations` | `[String]`, `[Ω]?` |
| /prg (V36 前進) | `signals`, `suspended`, `separation` | `[Ω]`, `[String]?`, `String` |

### 3.2 wm-M: 判断型 (Decision)

> **適用**: Peras 全族、Krisis-T1/T2、Chronos-T1/T2、一部の判断系スキル
> **認知座標**: Flow=I (推論)。入力を統合し、判断を導出する
> **FEP**: model precision ↑ — 内部モデルの確度を最大化

```typos
<:output mixin="wm-M":
  goal: String             # この実行の目的
  constraints: String      # 制約・前提条件
  decision: String         # 判断の結論
  next: String             # 次のアクション (→/verb 形式)
/output:>
```

**専用フィールドの典型例**:

| スキル | 専用フィールド | 型 |
|:-------|:---------------|:---|
| /noe (V01 認識) | `insight`, `anomaly`, `limit` | `O`, `String?`, `String?` |
| /bou (V02 意志) | `desire`, `feasibility`, `will` | `String`, `K`, `String` |
| /kat (V09 確定) | (base のみ) | — |
| /epo (V10 留保) | `current_state` | `String` |
| /sag (V06 収束) | (base のみ) | — |
| /beb (V17 肯定) | `belief`, `condition` | `String`, `String` |
| /pai (V11 決断) | (base のみ) | — |
| /dok (V12 打診) | (base のみ) | — |
| /akr (V15 精密) | (base のみ) | — |
| Peras 全族 (/t /m /k /d /o /c /ax) | (base のみ) | — |
| Hub 全族 (/Ia /Ib /Sa /Sb /Aa /Ab) | 族固有の1フィールド | varies |

### 3.3 wm-H: 行動型 (Action)

> **適用**: T3/T4 スキルのうち、実際の WM が `current_state` + `next_step` を使うもの。
> 認知座標が A-pole (行為型) でも、WM が `$goal / $constraints / $decision / $next` なら wm-M を使う。
> **判定基準**: 認知座標ではなく**実際の WM 出力**が優先。
> **例外 (A-pole だが wm-M)**: /akr (精密修正 → 判断が主), /pai (決断 → 確信固定が主), /dok (打診 → 判断が主)
> **認知座標**: Flow=A (行為)。判断を実行に移す
> **FEP**: action precision ↑ — 行為の精度を最大化し、prediction error を環境に押し返す

```typos
<:output mixin="wm-H":
  goal: String             # この実行の目的
  current_state: String    # 現在の状態
  constraints: String      # 制約・前提条件
  next_step: String        # 次の具体的ステップ
/output:>
```

**専用フィールドの典型例**:

| スキル | 専用フィールド | 型 |
|:-------|:---------------|:---|
| /tek (V08 適用) | `artifacts` | `[String]?` |
| /arh (V16 展開) | (base のみ) | — |
| /kop (V19 推進) | `direction`, `terrain`, `anchor`, `discovery` | `String`, `String`, `String`, `String?` |
| /dio (V20 是正) | (base のみ) | — |
| /par (V24 先制) | (base のみ) | — |

> **注意**: /kop は `$goal` の代わりに `$direction` を使う唯一の例外。
> `use="wm-H"` を使わず、独自スキーマで宣言する。

### 3.4 例外: H-series

H-series スキル (h-telos, h-methodos, h-krisis, h-diastasis, h-orexis, h-chronos) は
標準 WM フォーマットに従わない。中動態 (being) の状態検知を出力する。

```typos
# H-series は独自スキーマ (base mixin を使わない)
<:output:
  state: String            # 検知された being 状態
  intensity: K?            # 強度 (あれば)
  trigger: String?         # トリガーとなった信号
/output:>
```

---

## 4. SKILL.md での使用方法

### 4.1 基本形

```typos
<:output use="wm-M":
  # wm-M から継承: goal, constraints, decision, next
  insight: O               # 専用: 構造的洞察
  confidence: K            # 専用: 確信度
  assumptions: [String]?   # 専用: 前提リスト
/output:>
```

### 4.2 継承なし (独自スキーマ)

```typos
<:output:
  direction: String        # /kop: goal の代わり
  terrain: String
  anchor: String
  discovery: String?
  next: String
/output:>
```

### 4.3 配置場所

SKILL.md 内の `<:highlight:>` ブロックの直後、`<:intent:>` の直前に配置:

```
<:highlight:>
  ...
/highlight:>

<:output use="wm-M":         ← ここ
  ...
/output:>

<:intent:>
  ...
/intent:>
```

---

## 5. hermeneus 連携

### 5.1 静的検証

hermeneus は `<:output:>` 宣言に基づき、CCL 式の射影を検証する:

```ccl
/noe+ >> $result
$result.insight >> /ele       # ✅ insight: O はスキーマに存在
$result.foobar >> /kat        # ❌ foobar は /noe の output に未宣言
```

### 5.2 型チェック

```ccl
/noe+ >> $result
$result.confidence >> /pai    # ⚠️ /pai の入力は K 型を期待。confidence: K なので ✅
$result.insight >> /pai       # ⚠️ /pai の入力に O 型は不適切。型不一致の警告
```

### 5.3 後方互換

`<:output:>` がないスキルは従来通り動作する:
- 全体キャプチャ (`$result = /verb`) → ✅ 常に可能
- `.field` 射影 → ⚠️ hermeneus は検証不能。警告を出すが実行は妨げない
- 分解束縛 → ⚠️ 同上

---

## 6. operators.md §16 との対応

| operators.md | output_schema.md |
|:-------------|:-----------------|
| §16.1 精度パラメトリック | — (変数の概念。スキーマの概念ではない) |
| §16.2 束縛 | §4 配置場所 (束縛先の型がスキーマで宣言される) |
| §16.4 積の射影 | §5.1 静的検証 (射影先の検証根拠) |
| §16.4.3 WM=積の成分 | §3 Base パターン (WM の型宣言) |
| §16.7 型推論 | §2 型システム + §5.2 型チェック |

---

*v1.0 — 2026-04-04 CCL 変数設計セッション*
