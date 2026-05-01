# Style Guide — Predictions Descend / 理解関手の普遍的限界

## 親原理

本稿は「予測も理解も重要である」という穏当な整理ではない。核は、予測を理解の証拠として読む評価軸を反転し、理解を `L ⊣ R` の操作として、予測1を下降関手 `R` の痕跡として再配置する点にある。

改稿・英訳・要約では、この反転を弱い比喩へ落とさない。強度を落とす必要がある場合は、主張そのものを縮めるのではなく、主張水準ラベル、SOURCE 強度、未解決条件を明示する。

## 読者

| 読者層 | 配慮 |
|:---|:---|
| 科学哲学 | Popper / Bogen-Woodward / van Fraassen / Cartwright の接続を、標準語で示す |
| 圏論に慣れていない読者 | `L`, `R`, `η_unit`, `Ker` の前に、操作の向きと直感を置く |
| FEP / active inference 読者 | FEP は実例であり、論旨は FEP 非依存で立つことを保つ |
| AI / benchmark culture 読者 | 予測精度批判を「予測は無意味」へ誤読させない |

## 書き換え規律

| 面 | 方針 |
|:---|:---|
| L / R の向き | `L` = 還元・上昇、`R` = 回復・下降を全章で固定する |
| 真理0 / 真理1 | `真理0 = 構造`、`真理1 = 有限理論としての経験的真` を混ぜない |
| 予測0 / 予測1 | `予測1` 批判を `予測0` 批判へ広げない |
| C1-C5 | meta §M2 の主張水準と確信度を維持し、後退させる場合は Gauntlet に戻す |
| NRFT | formal proof attempt と theorem surface を分け、honest calibration を消さない |
| Bogen-Woodward | 単なる再記述ではなく、4 型 + 随伴構造 + NRFT 骨格への延長として扱う |

## 禁止

| 禁止 | 理由 |
|:---|:---|
| 「一つの見方」として弱める | C4/C5 の反転 claim が μ に縮退する |
| 予測批判を「予測は不要」と書く | 本稿は予測1の存在価値ではなく、真理0指標としての誤読を批判している |
| 圏論語を装飾として使う | `L ⊣ R` は load-bearing な操作定義 |
| FEP 依存稿として扱う | meta と本文は FEP 非依存性を射程条件として明示している |
| theorem / hypothesis / structural analogy を混ぜる | 本稿内の claim calibration が壊れる |

## 英訳時の register

強い結論には `we argue`, `we establish`, `this entails` を使う。未解決条件がある箇所では `under this restriction`, `as a constructive claim`, `at the level of structural analogy` のように、弱めるのではなく型注記で精密化する。

数学語は削らず、式の直前に「何を見ればよいか」を自然言語で置く。`L ⊣ R` は式だけで済ませず、対象を別表現へ還元し、そこから回復する二つの操作として説明する。
