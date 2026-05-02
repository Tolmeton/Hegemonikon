# Wave 9 CCL 距離改善実験 — 結果

- 関数数: 200
- ペア数: 500
- ベースライン ρ: 0.5917
- 最良 ρ: 0.6991

## 個別距離の直接 ρ

| 指標 | ρ |
|:---|---:|
| ρ(ast_lev, ccl_edit) | 0.5917 |
| ρ(ast_bigram, ccl_edit) | 0.1635 |
| ρ(ast_trigram, ccl_edit) | 0.0949 |
| ρ(cf, ccl_edit) | 0.4021 |
| ρ(ast_lev, ccl_extra) | 0.3170 |

## Grid Search 結果

### grid_search_ccl
- best ρ = 0.6086
- weights: ccl_edit=0.95, ccl_extra=0.05

### grid_search_gt
- best ρ = 0.6734
- weights: ast_lev=0.80, ast_bigram=0.00, cf=0.20

### grid_search_both
- best ρ = 0.6991
- GT(0.80lev+0.00bi+0.20cf) vs CCL(0.95edit+0.05extra)

## 診断

| 指標ペア | ρ |
|:---|---:|
| ρ(ast_lev, ast_bigram) | 0.2244 |
| ρ(ast_lev, ast_trigram) | 0.1601 |
| ρ(ast_lev, cf) | 0.1791 |
| ρ(ccl_edit, ccl_extra) | 0.2646 |
| ρ(ast_bigram, cf) | 0.1759 |

Fisher z-test: p = 0.0035 (**)