# FEP 分解型 blind evaluation — Gemini 3.1 Flash-Lite

## Source

- response: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/blind_outputs/gemini_gemini-3.1-flash-lite-preview_20260501T132107Z.md`
- prompt: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/FEP分解型_blind_participant_prompt.md`
- model: `gemini-3.1-flash-lite-preview`
- route: Gemini API via clean container runner

## Contamination

禁止語の直接混入は検出されなかった。

```text
Hegemonikon / HGK / CCL / 36 Poiesis / 12 H-series / 48-frame / ギリシャ語ラベル / skill 名 / 動詞名 / 本稿 §5 / 座標表: no hits
```

## Stage A: Decomposition Recovery

| ID | expected | observed in response | score | note |
|:---|:---|:---|:---:|:---|
| B0 | Helmholtz / solenoidal-dissipative / gradient-flow | NESS vs transient dynamics は弱い gap として出るが、Helmholtz / solenoidal / gradient-flow は出ない | 0 | 補助記録。pass/fail 条件からは外す |
| D2 | Markov blanket / internal-external boundary | Markovian Cut: Internal vs External states | 2 | 明確 |
| D3 | inference / action | Active/Passive: Perception vs Action | 2 | 明確 |
| D4 | VFE = Accuracy - Complexity | Variational Split: Accuracy vs Complexity | 2 | 明確 |
| D5 | EFE = Epistemic + Pragmatic | Active Split: Epistemic vs Pragmatic value | 2 | 明確 |
| D7 | temporal contrast | Temporal Horizon: Immediate vs Future consequences | 2 | Medium / derived だが時間方向は回収 |
| D8 | precision weighting | Precision Weighting | 2 | 明確 |
| D9 | scale / hierarchy | Hierarchical Depth: Top-down predictions vs Bottom-up errors | 2 | 明確 |
| D10 | interoceptive / affective valence | Affective Split: Allostatic set-points vs Sensory input | 1 | 内受容は出るが valence polarity は弱い |

## Stage B: Coordinate Support

| 制約面 | score | note |
|:---|:---:|:---|
| Basis | not gated | B0 系の力学的基底は出ない。Basis は blind protocol ではなく local SOURCE 側で支える |
| Directionality | 2 | D2 + D3 から内外境界と perception/action が回収される |
| Value | 1 | pragmatic / homeostatic requirements は出るが、D2 の internal/external から目的値の向きへ明示接続は弱い |
| Function | 2 | epistemic / pragmatic が回収される |
| Precision | 2 | precision weighting が回収される |
| Scale | 2 | hierarchical depth が回収される |
| Temporality | 2 | temporal horizon が回収される |
| Valence | 1 | interoceptive / affective は出るが、valence polarity は弱い |

## Verdict

**Weak pass** under the revised rubric.

旧 rubric では Basis 欠落により Fail と記録した。しかし Basis は操作的分解型ではなく FEP physics 由来の力学的基底であり、blind protocol の pass/fail 条件に置くべきではない。改訂 rubric では、Directionality と 6 修飾座標のうち主要 5 面以上が回収されているため Weak pass とする。

## Implication

この結果は、Basis を含む全 CE 層の blind support ではない。ただし、blind protocol の目的を coordinate modifiers の非後付け性検査へ限定するなら、Directionality / Function / Precision / Scale / Temporality は強く回収され、Value / Valence も弱く回収された。本文へ戻すなら、次の扱いにする。

1. Basis は FEP physics literature の local SOURCE から支持する。
2. blind protocol は Directionality と 6 修飾座標の非後付け性を検査するものへ制限する。
3. Gemini response は、Basis 欠落による失敗ではなく、Basis を blind gating に入れた rubric 設計の過要求を露出したものとして記録する。
