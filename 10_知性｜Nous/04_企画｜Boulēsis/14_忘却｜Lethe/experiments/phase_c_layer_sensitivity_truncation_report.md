# Phase C Layer Sensitivity — Truncation Follow-up

> 実験日: 2026-04-23  
> 実行スクリプト: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity.py`  
> 生データ:
> - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity_results.json`
> - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity_b384_results.json`
> - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity_b512_results.json`

## 1. 目的

前回の `B max_len=256` 実験では、`B` の構造指標が過度に低く、`D > B` に逆転していた。  
今回の目的は、その逆転が `B truncation artifact` かどうかを切ること。

固定したもの:

- sample indices
- seed
- D 側 max_len = 256
- model / epochs / folds / layer windows

動かしたもの:

- B 側 max_len = `256 / 384 / 512`

## 2. B 側の baseline 偏ρ_ccl 推移

| B max_len | shallow | mid | deep |
|:--|--:|--:|--:|
| 256 | 0.1425 | 0.1307 | 0.1408 |
| 384 | 0.1238 | 0.2153 | 0.1732 |
| 512 | 0.1738 | 0.2519 | 0.2273 |

## 3. 観察

### 3.1 `mid` は消えず、むしろ強化された

- `B/mid` baseline 偏ρ_ccl は `0.1307 → 0.2153 → 0.2519`
- 256 で見えていた「B は弱い」は、かなりの部分が truncation 汚染だった

### 3.2 `deep` も戻るが、best は `mid`

- `B/deep` baseline 偏ρ_ccl は `0.1408 → 0.1732 → 0.2273`
- ただし 512 でも `mid=0.2519 > deep=0.2273`

したがって、「十分な長さを渡すと deep が主座になる」は支持されない。  
この proxy では **best window は mid** のまま。

### 3.3 D/B の逆転は解消した

baseline 偏ρ_ccl の `D - B`:

| window | B=256 | B=384 | B=512 |
|:--|--:|--:|--:|
| shallow | +0.0617 | +0.0803 | +0.0304 |
| mid | +0.1021 | +0.0174 | **-0.0192** |
| deep | +0.0767 | +0.0443 | **-0.0099** |

`B=512` で `mid/deep` は `B > D` に戻る。  
よって、前回の `D > B` はかなり強く **truncation artifact** だった。

## 4. λ 効果の推移

`Δ偏ρ_ccl = λ1.0 - baseline`

| B max_len | shallow | mid | deep |
|:--|--:|--:|--:|
| 256 | -0.0562 | +0.0134 | +0.0000 |
| 384 | +0.0248 | +0.0055 | +0.0000 |
| 512 | +0.0210 | -0.0129 | +0.0000 |

これが示すもの:

- λ 効果は **窓と長さに対して非単調**
- deep は一貫してフラット
- shallow は 256 では壊れ、384/512 ではむしろ少し効く
- mid は baseline が上がるほど λ 利得が消える

## 5. 結論

この follow-up で確定したのは 2 点。

1. **前回の B 低下は主に truncation artifact だった。**
2. **それでも best window は deep ではなく mid のまま。**

したがって、現時点の最有力読みは:

- `deep-only locus` は棄却
- `mid locus` は surviving hypothesis
- λ は深層専用ブースタではなく、長さと窓に依存する補完項

## 6. 次の実験

次の 1 本はこれ。

1. `B=512, D=256` を維持
2. `λ` を `0.0 / 0.1 / 1.0` に戻す
3. `mid` と `deep` のみで fold 数を 3 以上に増やす

これで、

- `mid` が本当に安定最良か
- `λ` の非単調性が偶然か
- deep が flat なままか

を切れる。
