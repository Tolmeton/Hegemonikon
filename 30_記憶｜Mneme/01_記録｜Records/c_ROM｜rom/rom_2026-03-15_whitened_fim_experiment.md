# ROM: Whitened Embedding FIM 実験 (E6)

**日時**: 2026-03-15 14:00
**実験ID**: e6_whitened_fim
**目的**: 仮説 1B (Cone Effect / Anisotropy) の検証 — PCA whitening が FIM の k_signal を変えるか

## 結論

**仮説 1B は棄却**。ただし理由は「異方性が無関係」ではなく、**FIM の計算手法が本質的にアフィン変換不変**であるため。

## 実験設計

| 項目 | 値 |
|------|-----|
| モデル | gemini-embedding-001 |
| 次元数 | 3072 |
| サンプル数 | 200 |
| k-NN | 10 |
| Whitening | PCA (ZCA) → 有効次元 199 |

## 結果

| 指標 | Raw | Whitened | 差分 |
|------|-----|----------|------|
| k_signal | 1 | 1 | 0 |
| max_gap (log) | 0.0442 | 0.0442 | 0 |
| sloppy_ratio | 0.1951 | 0.1951 | 0 |
| FIM trace | 0.3003 | 0.3003 | 0 |
| 有効次元数 | 3072 | 199 | -2873 |

**固有値上位5**: Raw と Whitened で小数点以下13桁まで一致。

## 分析

### なぜ FIM が不変なのか

k-NN ベースの FIM 計算:
```
FIM ≈ (1/N) Σᵢ (1/k) Σⱼ∈kNN(i) (xⱼ - xᵢ)(xⱼ - xᵢ)ᵀ
```

PCA whitening は x → W·x (アフィン変換) を適用する。
- Whitened FIM = W · Raw FIM · Wᵀ
- 固有値は **類似変換** の下で不変
- したがって FIM の固有値スペクトルは whitening に影響されない

これは数学的に当然であり、実験はこの不変性を確認した。

### 仮説への影響

| 仮説 | 判定 | 根拠 |
|------|------|------|
| 1A: 本質的低次元性 (Osgood) | △ 排除されず | k_signal=1 は低次元性を示唆するが、実験設計の限界もある |
| 1B: Cone Effect (Anisotropy) | ✗ 検証不能 | FIM がアフィン不変なので、この手法では検証不可能 |
| 2A: K₆ シンプレクティック | △ 排除されず | 別の実験が必要 |
| 3A: FEP 高速-低速分離 | △ 排除されず | 動的実験が必要 |

### k_signal = 1 について (前回 2-3 との差)

- 前回の Sloppy Spectrum 実験 (E3) では k_signal = 2-3
- 今回は k_signal = 1
- 差の原因: [仮説] サンプル数 (200 vs E3 のサンプル数)、テキストの多様性、k-NN パラメータの違い
- k_signal の不安定性自体が、低次元性の頑健な証拠とは言えないことを示唆

### 正しい異方性検証への提案

Cone Effect を検証するなら、FIM ではなく以下が有効:
1. **cosine similarity の分布分析**: 全ペアのコサイン類似度ヒストグラム → 狭い分布 = 異方性大
2. **IsoScore / Isotropy Score**: Mu et al. (2018) の手法
3. **事後処理 (post-hoc) 後の下流タスク性能比較**: whitening → タスク精度の変化

## タグ

```yaml
topics: [k_signal, FIM, whitening, anisotropy, cone_effect, PCA]
related_experiments: [e3_sloppy_spectrum, e5_anisotropy_diagnosis]
related_roms: [rom_2026-03-15_k_signal_analysis.md]
confidence: 確信 (実験結果自体) / 推定 (分析・解釈)
```
