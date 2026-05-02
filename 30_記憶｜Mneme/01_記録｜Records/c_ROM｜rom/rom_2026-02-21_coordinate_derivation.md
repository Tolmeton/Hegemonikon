# ROM: HGK 座標導出距離の確定 (2026-02-21)

> **ステータス**: 確定 (全会一致)
> **セッション**: 73d29a63

## 確定事項: d 配分 = 1+3+2

| d | 座標 | Opposition | 根拠 |
|:--|:-----|:-----------|:-----|
| **0** | Flow | I↔A | MB partition に定義的に内在 |
| **1** | Value | E↔P | EFE の分解で初めて分離 |
| **1** | Function | Expl↔Expt | EFE に基づく行動選択のトレードオフ |
| **1** | **Precision** | C↔U | VFE の生成モデル (MB + 分布仮定) に固有。MB の構造ではない |
| **2** | Scale | Mi↔Ma | 階層的生成モデルの追加仮定が必要 |
| **2** | Valence | +↔− | 内受容モデル (Seth 2013) の追加仮定が必要 |

## 判定根拠

### Precision = d=1 の決定的証拠

| 調査者 | 判定 | 核心根拠 |
|:-------|:-----|:---------|
| Gemini 2.5 Pro | d=1 | パラメータ化が追加仮定 |
| Gemini Deep Research | d=0.5→整数化 d=1 | MB < Precision < EFE |
| Gemini 3.1 Pro | d=1 | VFE gradient descent で動作、EFE は強化のみ |
| **Claude.ai Research** | **d=1 (決定的)** | 統計的精度 Π ≠ 認知的精度 π (同音異義解消) |
| Parr & Friston (2018) | VFE 段階 | DOI: 10.3389/fnint.2018.00039 |
| Claude 敵対的分析 | d=1 | MB の構造ではなく動的性質 |

### Claude.ai の決定打: 同音異義の解消

- **統計的精度 (Π)**: NESS 密度の逆共分散行列 → MB トポロジーを定義 → d=0
- **認知的精度 (π)**: 予測誤差の逆分散 → エージェントが推論 → **d=1**
- Da Costa (2021) の「MB = precision matrix sparsity」は統計的 Π の話。座標 C↔U は認知的 π の話。**別物。**

### 部分順序 (FEP から必然)

```
Flow (d=0) ≤ {Value, Function, Precision} (d=1) ≤ {Scale, Valence} (d=2)
```

## 未確定事項

- H(3,2) = 6 Series の必然性 → 次の検証対象
- 25 定理体系の具体的な定理名・Opposition の割り当て

## 参照文献

- Parr, Benrimoh, Vincent, Friston (2018) "Precision and False Perceptual Inference" DOI: 10.3389/fnint.2018.00039
- Feldman & Friston (2010) "Attention, Uncertainty, and Free-Energy" Front. Hum. Neurosci. 4:215
- Da Costa et al. (2021) Proc. R. Soc. A 477:20210518
- Clark (2013) "The Many Faces of Precision" Front. Psychol. 4:270
- Friston (2019) arXiv:1906.10184
