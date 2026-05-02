# P3 検証結果: CCL embedding vs Text embedding

> 実験日: 2026-03-18 21:49
> ベンチマーク: 正例 20 ペア / 負例 15 ペア

## ペアごとの結果

| ID | 種別 | パターン | Text Sim | CCL Sim | Δ | CCL一致 |
|:--|:--|:--|--:|--:|--:|:--|
| P01 | 正例 | filter → map → aggregate | 0.703 | 0.940 | +0.238 |  |
| P02 | 正例 | validate → transform → persist | 0.674 | 0.893 | +0.219 |  |
| P03 | 正例 | fetch → parse → cache | 0.609 | 0.863 | +0.255 |  |
| P04 | 正例 | iterate → check → accumulate | 0.645 | 1.000 | +0.355 | ≡ |
| P05 | 正例 | try → operation → except → fallback | 0.610 | 0.817 | +0.207 |  |
| P06 | 正例 | map → sort → slice | 0.746 | 1.000 | +0.254 | ≡ |
| P07 | 正例 | group_by → aggregate_each | 0.591 | 0.943 | +0.353 |  |
| P08 | 正例 | linear pipeline (3 transforms) | 0.620 | 1.000 | +0.380 | ≡ |
| P09 | 正例 | if-elif-else routing | 0.688 | 1.000 | +0.312 | ≡ |
| P10 | 正例 | recursive flatten | 0.655 | 1.000 | +0.345 | ≡ |
| P11 | 正例 | lookup → default → transform | 0.584 | 1.000 | +0.416 | ≡ |
| P12 | 正例 | comprehension: map + filter | 0.702 | 1.000 | +0.298 | ≡ |
| P13 | 正例 | wrap → execute → unwrap | 0.705 | 1.000 | +0.295 | ≡ |
| P14 | 正例 | reduce (left fold) | 0.745 | 1.000 | +0.255 | ≡ |
| P15 | 正例 | enumerate + conditional collect | 0.667 | 1.000 | +0.333 | ≡ |
| P16 | 正例 | nested loop → flat collect | 0.757 | 1.000 | +0.243 | ≡ |
| P17 | 正例 | factory dispatch | 0.641 | 1.000 | +0.359 | ≡ |
| P18 | 正例 | zip two lists → dict | 0.716 | 1.000 | +0.284 | ≡ |
| P19 | 正例 | while search → break on find | 0.693 | 1.000 | +0.307 | ≡ |
| P20 | 正例 | batch split → process each → collect | 0.647 | 1.000 | +0.353 | ≡ |
| N01 | 負例 | [NEGATIVE] linear vs recursive | 0.532 | 0.813 | +0.281 |  |
| N02 | 負例 | [NEGATIVE] simple vs complex branching | 0.550 | 0.696 | +0.146 |  |
| N03 | 負例 | [NEGATIVE] map vs try-except | 0.534 | 0.876 | +0.342 |  |
| N04 | 負例 | [NEGATIVE] filter vs nested loop | 0.431 | 0.724 | +0.293 |  |
| N05 | 負例 | [NEGATIVE] aggregate vs factory | 0.463 | 0.685 | +0.222 |  |
| N06 | 負例 | [HARD NEG] with-branch vs no-branch accumulate | 0.682 | 0.890 | +0.208 |  |
| N07 | 負例 | [HARD NEG] for-loop vs while-loop accumulate | 0.550 | 0.835 | +0.285 |  |
| N08 | 負例 | [HARD NEG] filter-then-map vs map-then-filter | 0.588 | 0.884 | +0.296 |  |
| N09 | 負例 | [HARD NEG] single-return vs early-return | 0.801 | 0.864 | +0.063 |  |
| N10 | 負例 | [HARD NEG] pure-map vs side-effecting map | 0.566 | 0.802 | +0.236 |  |
| N11 | 負例 | [EASY NEG] recursive-tree vs linear-pipeline | 0.406 | 0.694 | +0.288 |  |
| N12 | 負例 | [EASY NEG] generator vs dict-builder | 0.507 | 0.751 | +0.244 |  |
| N13 | 負例 | [EASY NEG] class-init vs function-composition | 0.505 | 0.819 | +0.314 |  |
| N14 | 負例 | [EASY NEG] error-chain vs math-computation | 0.426 | 0.796 | +0.370 |  |
| N15 | 負例 | [EASY NEG] state-machine vs comprehension | 0.426 | 0.725 | +0.299 |  |

## 集計

| 指標 | Text | CCL | Δ |
|:--|--:|--:|--:|
| 正例平均類似度 | 0.670 | 0.973 | +0.303 |
| 負例平均類似度 | 0.531 | 0.790 | +0.259 |
| 分離度 (正-負) | 0.139 | 0.183 | +0.044 |

## Recall@k

| k | Text | CCL | Δ |
|--:|--:|--:|--:|
| 1 | 70.0% | 90.0% | +20.0% |
| 3 | 100.0% | 100.0% | +0.0% |
| 5 | 100.0% | 100.0% | +0.0% |

## 統計的検定

| 検定 | 統計量 | p値 | 判定 |
|:--|--:|--:|:--|
| Wilcoxon 符号順位 | 210.0 | 0.0000 | 有意 (p < 0.05) |

| 手法 | AUC | 95% CI |
|:--|--:|:--|
| Text Embedding | 0.893 | [0.730, 1.000] |
| CCL Embedding | 0.967 | [0.903, 1.000] |

| 手法 | Cohen's d | 効果量 |
|:--|--:|:--|
| Text Embedding | 1.758 | 大 |
| CCL Embedding | 2.911 | 大 |

## CCL 構造式サンプル

### P01: filter → map → aggregate
- CCL A: `_ >> V:{_ >> .attr >> pred} >> F:[each]{_} >> _ >> F:[each]{_ >> fn} >> >> (_ >> sum / _ >> len)`
- CCL B: `_ >> V:{_ >> .attr} >> F:[each]{_} >> _ >> F:[each]{_ >> .attr} >> >> (_ >> sum / _ >> len)`
- 一致: 不一致

### P02: validate → transform → persist
- CCL A: `\str_ >> .get >> I:[ok]{...} >> _ >> fn >> _ >> fn >> >> _`
- CCL B: `\_ >> .strip >> I:[ok]{...} >> _ >> fn >> _ >> fn >> >> _`
- 一致: 不一致

### P03: fetch → parse → cache
- CCL A: `_ >> .get >> _ >> .attr >> .method >> _ >> >> _`
- CCL B: `_ >> .method >> _ >> fn >> _ >> >> _`
- 一致: 不一致

### P04: iterate → check → accumulate
- CCL A: `num_ >> _ >> F:[each]{_ >> .method >> I:[ok]{>> num_}} >> >> _`
- CCL B: `num_ >> _ >> F:[each]{_ >> .method >> I:[ok]{>> num_}} >> >> _`
- 一致: 完全一致

### P05: try → operation → except → fallback
- CCL A: `scope{>> _ >> .read} >> C:{>> _ >> fn}`
- CCL B: `_ >> .get >> >> _ >> .method >> C:{>> _ >> fn}`
- 一致: 不一致
