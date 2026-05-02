# Wave 9/10 Siamese CCL 距離学習 — 結果

- 関数数: 200
- ペア数: 5000
- 特徴量: 43d (CCL 27d + AST 16d)
- GT: AST Levenshtein 正規化距離
- エポック数: 600, 学習率: 0.001

## 結果

| モデル | test_ρ mean | test_ρ std | best_ρ max |
|:---|---:|---:|---:|
| V2_Residual | 0.9135 | 0.0007 | 0.9163 |