# Pythōsis Phase 4: Zen 抽出

> **CCL**: `/gno+{source=python.zen}`
> **Date**: 2026-02-01
> **Purpose**: Python Zen の 19 格言を Hegemonikón の認知原則として再解釈

---

## 📋 概要

Python Zen (`import this`) は 19 の設計格言から成る。
これを Hegemonikón の 1公理・7座標・24動詞体系と対応付け、CCL 設計原則として抽出する。

---

## 🎯 原則マッピング

| # | Python Zen | Hegemonikón 解釈 | 対応公理/定理 |
|:-:|:-----------|:-----------------|:--------------|
| 1 | Beautiful > ugly | **美的整合性**: 認知構造は美しくあるべき | Ax1 (Coherence) |
| 2 | Explicit > implicit | **明示性原則**: 暗黙の前提を避ける | A2 Krisis |
| 3 | Simple > complex | **縮約優先**: 可能な限り簡素に | S1 Metron |
| 4 | Complex > complicated | **秩序ある複雑さ**: 複雑は許容、混沌は不可 | S2 Mekhanē |
| 5 | Flat > nested | **ネスト制限**: 3レベル以下を推奨 | CPL §10.4 |
| 6 | Sparse > dense | **疎結合**: 密度より明瞭さ | P1 Khōra |
| 7 | Readability counts | **可読性**: 将来の自分にも読める | A4 Epistēmē |
| 8 | No special cases | **一貫性**: 例外は例外を生む | Ax6 (Boundaries) |
| 9 | Practicality > purity | **実用主義**: 純粋さより実用 | S4 Praxis |
| 10 | Errors not silent | **エラー顕在化**: 失敗を隠さない | H1 Propatheia |
| 11 | Unless explicit | **意図的抑制**: 明示的なら許容 | `@suppress` |
| 12 | Refuse to guess | **Zero Entropy**: 曖昧さを質問で解消 | O3 Zētēsis |
| 13 | One obvious way | **正規経路**: 答えは一つ、迷わない | P2 Hodos |
| 14 | Not obvious at first | **学習曲線**: 最初は非自明でも良い | K1 Eukairia |
| 15 | Now > never | **行動優先**: 完璧を待たない | O4 Energeia |
| 16 | Never > right now | **熟慮**: 拙速より待機 | O2 Boulēsis |
| 17 | Namespaces great | **スコープ分離**: 名前空間を活用 | P1 Khōra |

---

## 📐 CCL 設計原則への翻訳

### 原則 1: 美的整合性 (Coherence)

> **Python**: Beautiful is better than ugly.
> **CCL**: 認知構造全体の調和を優先せよ

**適用**:

- ワークフロー名は統一パターン (`/動詞` または `/名詞`)
- 演算子は直感的意味を持つ (`+` = 詳細化, `-` = 縮約)
- 派生名は一貫 (`sens`, `conc`, `form` — 3文字以下の形容詞的名詞)

---

### 原則 2: 明示性 (Explicitness)

> **Python**: Explicit is better than implicit.
> **CCL**: 暗黙の前提を避け、全てを宣言せよ

**適用**:

- パラメータはデフォルト値を明示: `{confidence: float (default: 0.5)}`
- 型制約を宣言: `/epi.typed{expect: string}`
- スコープを明示: `@scoped(setup:, teardown:)`

**違反例**:

```ccl
# 悪い: 何が起きるか不明
/noe

# 良い: 意図が明確
/noe+{target: "Pythōsis Phase 4", out: insight}
```

---

### 原則 3: 縮約優先 (Reduction First)

> **Python**: Simple is better than complex.
> **CCL**: 最小の複雑度で目的を達成せよ

**適用**:

- `-` 演算子を積極的に使用
- ポイント制の Warning 帯域 (60pt+) を避ける
- マクロで複雑さを隠蔽: `@think` = `(/noe~\noe)*dia ^ /u+`

**指標**:

| 帯域 | pt | 推奨度 |
|:-----|:---|:------:|
| Minimal | 5-15 | ★★★ |
| Standard | 15-30 | ★★ |
| Enhanced | 30-45 | ★ |
| Maximum | 45-60 | ⚠️ |
| Warning | 60+ | ❌ |

---

### 原則 4: 秩序ある複雑さ (Ordered Complexity)

> **Python**: Complex is better than complicated.
> **CCL**: 複雑さは構造化せよ

**適用**:

- Series `/a`, `/h`, `/k`, `/o`, `/p`, `/s` で複雑さを軸に分解
- X-series で結合規則を明示 (15結合規則)
- マクロで複雑さをカプセル化

---

### 原則 5: ネスト制限 (Nesting Limit)

> **Python**: Flat is better than nested.
> **CCL**: ネストは 3 レベル以下

**適用**:

```ccl
# 推奨 (2レベル)
F:[×3]{
  I:[cond]{ /s+ }
}

# 深すぎる (4レベル) → マクロ化
let @inner = W:[loop]{ /s+ }
F:[×3]{ I:[cond]{ @inner } }
```

---

### 原則 6: 疎結合 (Sparse Coupling)

> **Python**: Sparse is better than dense.
> **CCL**: 1行に1概念

**適用**:

```ccl
# 悪い: 密度が高すぎる
(/noe~\noe)*(/dia^)*(/s~\s)_/kho*hod >> /ene+

# 良い: 段階的に展開
let @think = (/noe~\noe)*dia
let @design = (/s~\s)*hod
@think _@design >> /ene+
```

---

### 原則 7: 可読性 (Readability)

> **Python**: Readability counts.
> **CCL**: 将来の自分にも読めるか？

**適用**:

- ワークフローにはコメントを付与
- 複雑なマクロには `# 意図:` を記載
- 派生の選択理由を残す

---

### 原則 8: 一貫性 (Consistency)

> **Python**: Special cases aren't special enough to break the rules.
> **CCL**: 例外を作らない

**適用**:

- SEL (Semantic Enforcement Layer) による自動強制
- Anti-Skip Protocol の徹底
- 全ワークフローに同じ frontmatter 構造

---

### 原則 9: 実用主義 (Pragmatism)

> **Python**: Although practicality beats purity.
> **CCL**: 動くことが最優先

**適用**:

- `/ene- >> /dia` — まず動かし、後で検証
- 理論より実験: `/zet.poc`
- 完璧を待たない: `/euk+` で好機を逃さない

---

### 原則 10-11: エラー顕在化と意図的抑制

> **Python**: Errors should never pass silently. Unless explicitly silenced.
> **CCL**: 失敗は顕在化、抑制は明示

**適用**:

```ccl
# デフォルト: エラーは表示
/ene+  # 失敗時はエラーを報告

# 明示的抑制
@scoped(suppress: [timeout]) { /sop+ }
@suppress(NotFound) { /zet+ }
```

---

### 原則 12: Zero Entropy

> **Python**: In the face of ambiguity, refuse the temptation to guess.
> **CCL**: 曖昧さは質問で解消

**適用**:

- `/zet+` で問いを発見
- `/bou+` で意志を明確化
- `@u` で主観的判断を求める

**禁止**:

- 推測による Gap 埋め
- 「おそらく」「たぶん」での進行

---

### 原則 13: 正規経路

> **Python**: There should be one-- and preferably only one --obvious way to do it.
> **CCL**: Sacred Routes を定義

**適用**:

- `/boot >> /noe >> /s >> /ene >> /bye` — 標準思考フロー
- 同じ目的に複数の方法があれば、一つを正規化

---

### 原則 15-16: 行動と熟慮のバランス

> **Python**: Now is better than never. Although never is often better than right now.
> **CCL**: `/euk+` で好機を判定

**適用**:

```ccl
# 好機判定
/euk+{action: "リリース"}
# → 今か？ or 待つか？

# 結果に応じて
I:[/euk = now]{ /ene+ }
E:{ /bou.akra }  # Premortem で再検討
```

---

### 原則 17: スコープ分離

> **Python**: Namespaces are one honking great idea.
> **CCL**: `/kho` でスコープを分離

**適用**:

- プロジェクトごとにスコープ: `/kho{domain: "Pythōsis"}`
- `@scoped` でローカルコンテキスト
- Series でテーマ分離 (A=精度, H=動機, K=文脈...)

---

## 📊 原則遵守チェックリスト

| # | 原則 | CCL チェック |
|:-:|:-----|:-------------|
| 1 | 美的整合性 | 命名規則に従っているか |
| 2 | 明示性 | パラメータが明示されているか |
| 3 | 縮約優先 | 60pt 以下か |
| 4 | 秩序ある複雑さ | Series で分解されているか |
| 5 | ネスト制限 | 3レベル以下か |
| 6 | 疎結合 | 1行1概念か |
| 7 | 可読性 | コメントがあるか |
| 8 | 一貫性 | SEL に従っているか |
| 9 | 実用主義 | 動くか |
| 10-11 | エラー処理 | 失敗が顕在化するか |
| 12 | Zero Entropy | 曖昧さがないか |
| 13 | 正規経路 | Sacred Routes を使っているか |
| 15-16 | 行動/熟慮 | /euk で判定したか |
| 17 | スコープ分離 | /kho で分離されているか |

---

*Pythōsis Phase 4 | `/gno+{python.zen >> hegemonikon.principles}`*
