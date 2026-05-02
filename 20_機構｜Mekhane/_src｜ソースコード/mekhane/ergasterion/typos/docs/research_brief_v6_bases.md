# Typos v6.0 基底モデル調査依頼書

> **目的**: 記述理論 Typos の基底構造の妥当性を外部検証する
> **依頼先**: Deep Research (Gemini / Claude)
> **作成日**: 2026-02-20
> **依頼者**: Hegemonikón Project

---

## 1. 背景

### Typos とは何か

Typos は「記述の物理学」— テキスト（記述）を射 (morphism) として形式化し、その構造を公理的に導出する理論体系。

### 唯一の公理 (A0)

> **記述は信念分布の不可逆圧縮である。**

```
f: M → L
```

- M = 書き手の信念多様体（頭の中の知識・信念の全体）
- L = 記号列（テキスト）
- f = 不可逆な圧縮写像

FEP (自由エネルギー原理) の記述版:

```
F[記述] = D_KL(q‖p) − E_q[log p(y|x)]
```

### 姉妹体系 HGK との構造的対応

Hegemonikón (HGK) は認知一般の理論体系で、以下の構造を持つ:

- **1公理** (FEP) → **6座標** (定理¹) → **24定理²** (認知機能)
- 6座標 = FEP からの導出距離 d で配置: d=0(1個), d=1(2個), d=2(3個) → 1+2+3=6
- 各座標は **Opposition** (相補的対立軸) を持つ:
  - d=1: Flow — I(推論) ↔ A(行為) … Basis + Markov blanket 仮定
  - d=1: Value — E(認識) ↔ P(実用) … EFE の分解
  - d=1: Function — Explore ↔ Exploit … EFE による行動選択
  - d=2: Scale — Micro ↔ Macro … 階層的生成モデル
  - d=2: Valence — + ↔ - … 内受容予測誤差の符号
  - d=2: Precision — C ↔ U … 予測誤差の逆分散
- 24定理² = 6 Series × 4 (2×2 マトリクス = 2座標のOppositionのテンソル積)

**Typos は HGK の「姉妹ではなく娘」** — 同じ FEP から派生するが、認知全般ではなく記述に限定された部分圏。

---

## 2. 現在の到達点 (v6.0 候補モデル)

A0 から導出距離 d で基底を配置:

| d | 基底名 | Opposition (相補的対立) | HGK 対応 | 導出根拠 |
|:--|:-------|:----------------------|:---------|:---------|
| 0 | **Image** (暗黙基底) | 信念 ↔ 記号 | Flow (I↔A) | A0 の定義 f: M→L に内在。M=信念, L=記号 |
| 1 | **Endpoint** | 始域 ↔ 終域 | Value (E↔P) | 射の定義に始域と終域が必要 (追加仮定1) |
| 1 | **Reason** | 志向 ↔ 経緯 | Function (Expl↔Expt) | 記述にはテロス(なぜ書くか)とアルケー(何に基づくか)が必要 (追加仮定1) |
| 2 | **Context** | 局所 ↔ 大域 | Scale (Mi↔Ma) | 記述の有効範囲 — スコープの粒度 (追加仮定2) |
| 2 | **???** | ??? ↔ ??? | ??? | **未確定 — 本調査の核心** |

### 成分導出の想定メカニズム

HGK と同じく、明示的基底のペアの Opposition のテンソル積 (2×2) で成分を生成:

- Image (d=0) を暗黙基底として除外
- 残りの明示基底からペアを選び、各ペアの 2×2 = 4成分

現在の明示基底が3つ (E, R, C) の場合: C(3,2)=3ペア × 4 = **12成分**
4つ見つかれば: C(4,2)=6ペア × 4 = **24成分** (HGK と完全同型)

---

## 3. 調査事項 (3つの問い)

### Q1: 4基底は妥当か？

現在の4基底 (Image, Endpoint, Reason, Context) が記述の射を完全に記述するために**必要かつ十分**か？

検証基準:

- **独立性**: 各基底は他の基底から導出できないか？
- **相補性**: 各基底の Opposition は「一方を定義すれば他方が自動的に定まる」関係か？
- **完全性**: この基底集合で記述の全ての本質的側面をカバーしているか？
- **最小性**: 冗長な基底はないか？

特に検証してほしい点:

- **Endpoint の Opposition「始域↔終域」**: 圏論の射の定義としては自然だが、「書き手↔読み手」と同義か、それとも微妙に異なるか？
- **Reason の Opposition「志向↔経緯」(テロス↔アルケー)**: アリストテレスの四原因の目的因↔始動因に対応。これは記述の「なぜ」の二面性として妥当か？
- **Context の Opposition「局所↔大域」**: HGK の Scale (Micro↔Macro) の記述版。記述の有効範囲の粒度として独立軸をなすか？

### Q2: d=2 に第2の基底は存在するか？

HGK では d=2 に3つの座標 (Scale, Valence, Precision) がある。Typos で d=2 に Context 以外の基底があるべきか？

棄却済みの候補:

- **Quality (精度↔基準)**: Opposition が相補的でない（カテゴリ錯誤）
- **Resolution (精確↔概略)**: Context (局所↔大域) と共変する（独立でない）。また、「信念↔記号」(Rate-Distortion) の測度に過ぎない
- **Valence 相当 (肯定↔否定)**: 記述には身体的な情動方向がなく、内容の属性に吸収される

**調査依頼**: 上記以外に、A0 + 追加仮定2 (d=2) で導出可能な、記述に固有の相補的対立軸はあるか？

d=2 基底が存在するための条件:

1. A0 + 1つ以上の追加仮定を必要とする（d=0, d=1 ではない）
2. 既存の3基底 (Endpoint, Reason, Context) から導出できない
3. 相補的対立 (Opposition) を持つ
4. 記述の本質的側面に対応する

### Q3: 成分数は何が正しいか？

以下の候補モデルのうち、どれが最も妥当か？

| モデル | 明示基底 | ペア数 | ×4 | 成分数 | 特徴 |
|:-------|:--------|:------|:---|:-------|:-----|
| A | 3 (E,R,C) | 3 | 4 | **12** | 最小。HGK の半分 |
| B | 4 (E,R,C,?) | 6 | 4 | **24** | HGK と完全同型 |
| C | 3 (E,R,C) | 3 | ? | **?** | 関数が4でない可能性 |

---

## 4. 検証に役立つ理論的参照

以下の学術領域が参考になる可能性がある:

1. **Rate-Distortion Theory** (Shannon) — A0 の数学的基盤
2. **RSA (Rational Speech Acts)** framework (Goodman & Frank, 2016) — 語用論のベイズモデル。記述を「話者→聴者」の推論問題として形式化
3. **Relevance Theory** (Sperber & Wilson, 1986/1995) — 発話の関連性を認知的コスト/利益で分析
4. **Speech Act Theory** (Austin, Searle) — 発語行為の分類: locutionary / illocutionary / perlocutionary
5. **Systemic Functional Linguistics** (Halliday) — テキストの3つの metafunction: ideational / interpersonal / textual
6. **Category Theory for Communication** — Fong & Spivak の applied category theory
7. **Information Theory and Linguistics** — テキストの情報論的分析

特に **Halliday の3つの metafunction** は Typos の基底と比較する価値がある:

- Ideational (概念的) ≈ Image?
- Interpersonal (対人的) ≈ Endpoint?
- Textual (テキスト的) ≈ Context?

---

## 5. 期待する成果物

1. **4基底の妥当性評価** — 各基底の独立性・相補性・完全性・最小性の評価
2. **d=2 の第2基底の候補リスト** — 見つかった場合は Opposition とその根拠
3. **代替モデルの提案** — もし4基底モデル自体に問題があれば、別のアプローチの提案
4. **学術的根拠** — 上記の評価を支持する論文・理論の引用

---

## 6. 制約

- 10成分を前提としないこと。成分数は基底×関数の**結果**として出るべき
- HGK との構造的対応は参考にするが、強制しないこと。Typos は独自の構造を持ちうる
- 「答えがない」は妥当な結論。無理に基底を見つける必要はない

---

*Typos v6.0 Research Brief — 2026-02-20*
*Hegemonikón Project — mekhane/ergasterion/typos/docs/*
