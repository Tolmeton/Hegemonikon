# 05_スペクトル解析｜SloppySpectrum — Fisher 情報量・VFE 理論検証

FEP の理論的基盤を数値的に検証する解析的導出実験群。「Sloppy Model」概念に基づく情報幾何的分析。

## 内容

| ファイル | 概要 |
|:---------|:-----|
| `fisher_analytical_derivation.py` | Fisher 情報量の解析的導出 |
| `fisher_d_eff.py` | 有効次元 d_eff の計算 |
| `fisher_d_eff_extended.py` | d_eff 拡張版 |
| `fisher_d_eff_theory.py` | d_eff の理論的分析 |
| `fisher_maxent_bic.py` | 最大エントロピー + BIC 解析 |
| `fisher_pr_analysis.py` | 精度 (Precision) 分析 |
| `fisher_self_reference_fast.py` | 自己参照の高速計算 |
| `fisher_self_reference_vfe.py` | 自己参照 × VFE 統合 |

## 理論的背景

- **Sloppy Model**: Transtrum et al. — パラメータ空間の固有値スペクトルが「sloppy」(指数的減衰) する現象
- **Fisher 情報幾何**: 統計多様体上の曲率 = 情報量
- **d_eff (有効次元)**: 実質的に推定可能なパラメータ数 ≪ 名目次元
- **VFE 接続**: Kalon の Fix(G∘F) 不動点が Fisher 情報量の極大にあるか？
