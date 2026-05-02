# Phase C Layer Sensitivity — B512 / D256, Mid-Deep 3-Fold Follow-up

> 実験日: 2026-04-23  
> 実行スクリプト: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity.py`  
> 生データ:
> - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity_b512_middeep_3fold_results.json`

## 1. 目的

前回までで、

- `B max_len=256` では truncation artifact が強い
- `B=512` に戻すと `B > D` が回復する
- それでも best window は `deep` ではなく `mid` に見える

ところまでは見えていた。  
今回の目的は、`B=512 / D=256` を固定した上で、

- `mid` が本当に安定最良か
- `deep-only locus` が残るか
- `λ=0.1 / 1.0` が `mid / deep` にどう効くか

を `3-fold` で切ること。

## 2. 設定

- model: `microsoft/codebert-base`
- windows: `mid / deep`
- conditions: `B / D`
- sample size: `320`
- fold: `3`
- epochs: `4`
- max_len: `B=512`, `D=256`
- λ: `0.0 / 0.1 / 1.0`

## 3. baseline 偏ρ_ccl

| cond | mid | deep | mid-deep |
|:--|--:|--:|--:|
| B | 0.2886 | 0.2440 | +0.0446 |
| D | 0.2589 | 0.2561 | +0.0028 |

## 4. λ 効果

### 4.1 B 条件

| window | baseline | λ=0.1 | Δ | λ=1.0 | Δ |
|:--|--:|--:|--:|--:|--:|
| mid | 0.2886 | 0.2896 | +0.0010 | 0.2887 | +0.0001 |
| deep | 0.2440 | 0.2440 | +0.0000 | 0.2440 | +0.0000 |

### 4.2 D 条件

| window | baseline | λ=0.1 | Δ | λ=1.0 | Δ |
|:--|--:|--:|--:|--:|--:|
| mid | 0.2589 | 0.2436 | -0.0153 | 0.2469 | -0.0120 |
| deep | 0.2561 | 0.2561 | +0.0000 | 0.2561 | +0.0000 |

## 5. 観察

### 5.1 `mid` は 3-fold でも残った

- `B` では `mid=0.2886 > deep=0.2440`
- `D` でも `mid=0.2589 > deep=0.2561`

差の大きさは `B` で明確、`D` で僅差だが、少なくとも `deep` 優位は出ていない。

### 5.2 `deep` は λ に完全フラット

- `B/deep`: `Δ偏ρ_ccl = 0.0 / 0.0`
- `D/deep`: `Δ偏ρ_ccl = 0.0 / 0.0`

この proxy では、`deep` は構造指標に対して反応していない。

### 5.3 `λ` は deep booster ではない

- `B/mid` は λ を入れてもほぼ不変
- `D/mid` はむしろ小幅悪化

したがって、少なくともこの実験線では、`λ` を「deep の構造回復装置」と呼ぶ根拠はない。

## 6. 結論

この follow-up で確定したのは 3 点。

1. **`mid locus` は 2-fold の偶然ではなく、3-fold でも残る。**
2. **`deep-only locus` はこの proxy では実質的に棄却。**
3. **`λ` は deep を押し上げない。deep は完全にフラット。**

したがって、次の問いはもう `mid vs deep` ではない。  
残る問いは、

- この `mid locus` が CodeBERT proxy 固有か
- それとも Phase C 本体の 7B 系にも移るか

の 1 点に絞られる。

## 7. 次の実験

次にやる価値があるのは 2 択。

1. 7B 本体で `mid / deep` だけに絞った小規模 ablation を打つ
2. proxy 側で `mid` 周辺をさらに細かく割って `layers 3-6 / 4-7 / 5-8` を比較する

いま優先度が高いのは `1`。  
理由は、proxy 内で `mid` が残ること自体はもう十分見えたから。
