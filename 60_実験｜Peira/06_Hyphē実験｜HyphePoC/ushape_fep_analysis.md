# U字型精度分布の FEP 的解釈 — 実験結果と考察

## 結論

**U字型分布は「特徴」(feature) である** — 5/8 指標で U字型が優位。

## 実験概要

- **データ**: v0.7 precision (13セッション, 48チャンク, BC=0.6926)
- **3条件**: A.原U字型 / B.Quantile均一化 / C.Logit-squeeze中央集中
- **8指標**: λ弁別率 (3), Loss分散 (3), Coherence相関 (1), 情報エントロピー (1)

## 比較結果

| 指標 | A. U字型 | B. 均一 | C. 中央 | A優位? |
|:-----|:---------|:--------|:--------|:------:|
| δλ₁ range | **0.2000** | 0.1532 | 0.1138 | ✅ |
| λ₁ std | **0.0772** | 0.0580 | 0.0444 | ✅ |
| Loss std | **0.0403** | 0.0390 | 0.0381 | ✅ |
| Loss range | **0.1718** | 0.1625 | 0.1585 | ✅ |
| Loss CV | **6.5239** | 4.2910 | 4.1218 | ✅ |
| \|r(coh,prec)\| | 0.5106 | 0.5387 | **0.5027** | ❌ |
| H (entropy) | 2.8447 | 2.7773 | **2.4945** | ❌ |
| BC (bimodal) | 0.6926 | 0.6339 | **0.7085** | ❌ |

**A 優位: 5/8 指標**

## FEP レンズ分析

### F1: VFE を増やすか減らすか？

U字型分布は VFE を **減らす**:
- λ弁別率 +31% (A vs B): precision end のコントラストにより、λ schedule がチャンク品質差をより鋭く反映
- Loss CV +52% (A vs B): チャンク間の品質差がより検出可能 → Accuracy 項の改善

> ΔAccuracy > ΔComplexity → ΔVFE < 0

### F2: 精度の SOURCE は何か？

precision は `rho_eff` (kNN 密度推定) の min-max 正規化に由来:

```
rho_eff = d_w^{-1} * exp(-d_w * ΔS)   [SOURCE: hyphe_chunker.py L849-860]
```

- `d_w`: ウィンドウの意味的距離 → **embedding 空間の局所構造**
- `ΔS`: 前のウィンドウとのステップ差  → **テキストの長さ構造**
- U字型は `rho_eff` の分布そのものの帰結 → **構造的特性**

### F3: 均一化は探索か実行か？

- Quantile 均一化 = **exploitation** (既知の分布形状に強制)
- U字型保持 = **exploration** (データの自然な構造を尊重)

均一化は precision の弁別力を 23% (δλ₁), 34% (Loss CV) 低下させる → 実行品質を損なう。

### F4: 不確実性は解消可能か許容すべきか？

U字型の中間域の不在:
- epistemic uncertainty ではない (normalization を変えれば中間を作れる)
- **構造的帰結**: セッションログの意味境界は離散的であり、gradual な遷移は稀

→ 中間域の不在は **許容すべき** (aleatoric に近い)

### Proietti (2025) との接続

| precision 域 | Proietti のγ | 認知モード | チャンクの特徴 |
|:-------------|:-------------|:-----------|:---------------|
| 0.9-1.0 (25%) | γ=high | Deliberation | 明確な意味境界、高い一貫性 |
| 0.0-0.1 (27%) | γ=low | Habit | 曖昧な境界、機械的な分割 |
| 0.3-0.7 (21%) | γ=中間 | 高コスト遷移 | 中間はコスト高 → 不在は効率的 |

> precision の二極化は cognitive control の二極化と構造的に同型。
> 中間値が少ないことは「欠陥」ではなく「効率的な精度チャネル設計」。

## 設計への示唆

1. **v0.7 の min-max 正規化を維持すべき** — 均一化は弁別力を犠牲にする
2. **v0.8 quantile 正規化は弁別力 -8% の報告と整合** — quantile → 弁別力低下は U字型潰しが原因
3. **precision は 2値的に使用するのが最適** — 閾値 0.5 で high/low に分けるだけで十分
4. **AY (presheaf representability) は precision と直交な情報を持つ可能性** — 将来の実験候補

## 実験データ

- 入力: [precision_v07_results.json](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/60_実験｜Peira/06_Hyphē実験｜HyphePoC/precision_v07_results.json)
- スクリプト: [run_ushape_experiment.py](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/60_実験｜Peira/06_Hyphē実験｜HyphePoC/run_ushape_experiment.py)
- 結果: [ushape_experiment_results.json](file:///home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/60_実験｜Peira/06_Hyphē実験｜HyphePoC/ushape_experiment_results.json)
