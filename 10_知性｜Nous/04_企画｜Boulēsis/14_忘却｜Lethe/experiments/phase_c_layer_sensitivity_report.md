# Phase C Layer Sensitivity Report

> 実験日: 2026-04-21  
> 実行スクリプト: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity.py`  
> 生データ: `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_layer_sensitivity_results.json`

## 1. 目的

`D-only` 効果の locus が浅層ではなく深層統合にあるかを、最小コストで感度分析する。

元の仮説:

- D 条件では deep 側の適応が shallow より `partial_rho_ccl` を強く押し上げる
- B 条件ではその利得が弱い、または出ない

## 2. MVP 設計

これは **CodeLlama-7B の厳密再現ではない**。環境制約のため、base model を `microsoft/codebert-base` に落とした proxy 実験である。

- データ: realistic Phase C 条件 `B / D`
- サンプル: 320 pairs, B/D で同一 index を共有
- CV: 2-fold
- 学習: 4 epoch
- max_len: 256
- LoRA windows:
  - shallow = layers 0-3
  - mid = layers 4-7
  - deep = layers 8-11
- λ 条件:
  - baseline = 0.0
  - lxi_1.0 = 1.0
- 指標:
  - `partial_rho_ccl` を主指標
  - `acc` を副指標

## 3. 結果サマリ

| cond | window | baseline 偏ρ_ccl | λ=1.0 偏ρ_ccl | Δ偏ρ_ccl | baseline acc | λ=1.0 acc | Δacc |
|:--|:--|--:|--:|--:|--:|--:|--:|
| D | shallow | 0.2042 | 0.2134 | +0.0092 | 0.5125 | 0.5469 | +0.0344 |
| D | mid | 0.2327 | 0.2303 | -0.0024 | 0.5625 | 0.5625 | +0.0000 |
| D | deep | 0.2175 | 0.2175 | +0.0000 | 0.5312 | 0.5312 | +0.0000 |
| B | shallow | 0.1425 | 0.0863 | -0.0562 | 0.5312 | 0.5531 | +0.0219 |
| B | mid | 0.1307 | 0.1441 | +0.0134 | 0.5531 | 0.5406 | -0.0125 |
| B | deep | 0.1408 | 0.1408 | +0.0000 | 0.5500 | 0.5500 | +0.0000 |

## 4. 一次観察

### 4.1 D の best baseline は deep ではなく mid

- D baseline の `partial_rho_ccl` は `mid=0.2327` が最良
- deep baseline は `0.2175`
- shallow baseline は `0.2042`

したがって、この proxy では **「深層ほど構造理解が強い」単純図式は支持されない**。

### 4.2 λ の利得は D/shallow にしか弱く出ていない

- D/shallow だけが `Δ偏ρ_ccl=+0.0092`, `Δacc=+0.0344`
- D/mid は微減
- D/deep は完全にフラット

したがって、この proxy では **deep-only LXI gain 仮説は不支持**。

### 4.3 B では shallow がむしろ悪化

- B/shallow は `Δ偏ρ_ccl=-0.0562`
- B/mid は小幅改善 `+0.0134`
- B/deep はフラット

これは「浅層 LoRA + λ は B の構造指標を壊しうる」可能性を示す。

## 5. 重要な汚染要因

この実験で一番大きい汚染は **B truncation** である。

同じ sample indices でも文字数は:

| 条件 | mean chars | p50 | p90 |
|:--|--:|--:|--:|
| B | 1622.6 | 1123 | 3053 |
| D | 1345.5 | 859 | 2636 |

`max_len=256` 固定なので、B は D より切り捨て圧が強い。  
その結果、この proxy では baseline でも D が B を全 window で上回っており、元の 7B 結果とは並びが逆転している。

したがって:

- **window 内比較** はまだ読む価値がある
- **B vs D の絶対値比較** は truncation TAINT が強い

## 6. 現時点の結論

この MVP が支持したのは、

- deep-only locus ではない
- D の最良 baseline は mid
- LXI gain は大きくなく、窓ごとに非単調

である。

この MVP が **支持しなかった** のは、

- 「D では deep にだけ λ 効果が集まる」

である。

## 7. 次の実験

次の 1 本はこれ。

1. `B max_len` を 384 or 512 に上げ、D は 256 のまま据え置く  
2. 同じ layer windows で再測定する  
3. `window 内の λ 差` と `B/D の順位逆転` が保たれるかを見る

これで `mid locus` が本物か、単に `B truncation` が景色を歪めているだけかが分かる。
