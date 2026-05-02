```typos
#prompt sop-ccl-embedding-structural-correlation
#syntax: v8
#depth: L2

<:role: KI — CCL Embedding の構造的相関に関する実験的知見 :>

<:goal: CCL 構造式の embedding が Python コードの構造的類似度と
  統計的に有意な相関を持つことの実験的証拠を集約する :>

<:context:
  - [knowledge] 実験系列: P3a (合成ベンチマーク) + P3b v1/v2 (実世界, 2コードベース)
  - [file] 60_実験｜Peira/07_CCL-PL｜CCL-PL/p3b_benchmark.py
  - [file] 60_実験｜Peira/07_CCL-PL｜CCL-PL/p3_results.md
  - [file] 60_実験｜Peira/07_CCL-PL｜CCL-PL/p3b_results.md
/context:>
```

# CCL Embedding は Python コードの構造を捕捉する

> **日付**: 2026-03-20
> **実験者**: Claude (Antigravity) + Creator
> **ステータス**: P3b 検証完了 (2コードベース)

## 核心発見

| 発見 | 確信度 | 根拠 |
|:-----|:-------|:-----|
| CCL embedding は Text embedding より構造的相関が統計的有意に高い | **確信 95%** | 2コードベース × 2距離基準、全て p < 0.01 |
| CCL embedding の構造相関 ρ ≈ 0.25-0.30 | **確信 85%** | HGK: 0.303, deer-flow: 0.245 |
| 相関の大きさはコードベースに依存するが優位性は不変 | **確信 90%** | Δρ = +0.18〜+0.28、全条件で CCL > Text |
| Ground truth (AST/CF) の解像度が結果を左右する | **確信 90%** | v1 (shallow) → v2 (deep) で ρ が 6.4x 向上 |

## 実験設計

### P3a: 合成ベンチマーク

- **方法**: 20 正例 + 15 負例の構造的ペアを手動作成
- **embedding**: gemini-embedding-2-preview (3072d)
- **結果**: AUC_CCL = 0.967 > AUC_Text = 0.893, Wilcoxon p < 0.0001
- **Cohen's d**: CCL = 2.911 (大), Text = 1.758 (大)

### P3b: 実世界コードベース (構造距離相関法)

CCL 非依存の構造距離 (AST, CF) を ground truth とし、embedding cosine との Spearman ρ を比較。

**v2 改良**: Deep AST (全ノード走査, 情報量 23x 増) + multiset CF (弁別力 32%→90%+)

| コードベース | n_func | n_pairs | ρ(AST,CCL) | ρ(AST,Text) | Δρ | Fisher p |
|:--|--:|--:|--:|--:|--:|--:|
| HGK (mekhane) | 196 | 500 | **0.303** | 0.020 | +0.283 | **<0.0001** |
| deer-flow (外部) | 191 | 500 | 0.245 | 0.066 | +0.179 | **0.004** |

| コードベース | ρ(CF,CCL) | ρ(CF,Text) | Δρ | Fisher p |
|:--|--:|--:|--:|--:|
| HGK | **0.330** | 0.176 | +0.154 | **0.009** |
| deer-flow | **0.295** | 0.055 | +0.240 | **<0.001** |

### P3b 仮説判定

| 仮説 | HGK | deer-flow | 総合 |
|:--|:--|:--|:--|
| H1: ρ_CCL > 0.3 | ✅ (0.303) | ❌ (0.245) | 部分支持 |
| H2: CCL > Text | ✅ (Δ=+0.283) | ✅ (Δ=+0.179) | **全面支持** |
| H3: p < 0.05 | ✅ (p<0.0001) | ✅ (p=0.004) | **全面支持** |

## 解釈と示唆

### なぜ CCL > Text か

1. **構造の明示化**: `python_to_ccl()` が制御フロー・データフロー・分岐を記号列に変換
2. **表面的変動の除去**: 変数名・コメント・docstring が CCL 変換で消える → 構造のみが残る
3. **embedding の構造感受性**: gemini-embedding は CCL の記号パターンから構造的類似度を捕捉

### 制限事項

| 制限 | 影響 | 対策 |
|:--|:--|:--|
| CCL パーサーが HGK 最適化 | deer-flow で ρ 低下 | パーサー汎用性改善 |
| ρ ≈ 0.25-0.30 は「弱〜中程度の相関」| 単独では構造決定に不十分 | 他の特徴量と組合せ |
| embedding モデル依存 | gemini-embedding 以外は未検証 | マルチモデル検証 |
| medium 関数のみ (4-10 stmts) | 大関数での挙動は未知 | 範囲拡大実験 |

### 体系的接続

- **Lēthē 研究への示唆**: CCL が「構造の明示的表現」として使えるなら、LLM の暗黙的構造理解 (U_ccl) の ground truth として利用可能
- **Helmholtz Γ⊣Q との対応**: CCL embedding = Γ (均衡的・構造的)、Text embedding = Q (非均衡的・表面的) と解釈可能 [仮説]
- **Kalon 判定**: [主観] CCL の構造相関が ρ > 0 で Text に勝つことは、CCL が「コードの構造を見る」正しい抽象化であることを示す。Fix(G∘F) に近い — 発散 (python_to_ccl) と収束 (embedding) のサイクルが安定している

## 次のステップ

1. **3つ目のコードベース**: stdlib 等の大規模 OSS で再現性を確認
2. **パーサー汎用性**: `code_ingest.py` の HGK バイアスを定量化・削減
3. **Lēthē Phase B 統合**: P3b の CCL embedding を structural probe の ground truth として活用
4. **embedding モデル比較**: text-embedding-3-large 等での追試

---

*P3b 検証完了 2026-03-20 — 2コードベース × 2距離基準、全条件で CCL > Text (p < 0.01)*
