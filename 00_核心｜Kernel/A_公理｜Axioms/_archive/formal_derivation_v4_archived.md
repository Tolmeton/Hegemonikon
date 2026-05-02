# L0 形式的導出: 最終結論 (V4)

> **水準**: A (Conditional Formal Derivation)
> **日時**: 2026-03-07
> **検証**: Gemini 3.1 Pro による4ラウンドの Adversarial Review で収束
> **判定**: Round 4 — "Conditionally Accepted / Minor Revisions"

---

## 1. 結論

**FEP + Active Inference (POMDP) + Scope Constraints (H, T, E) から、HGK の32実体 (1公理 + 7座標 + 24動詞) は一意に構成される。**

これは「合理的な選択 (Axiomatic Construction)」ではなく、「数学的帰結 (Formal Derivation)」である。

### 条件 (Conditional)
1. **FEP → Active Inference (POMDP)**: Friston (2019) の標準的主張
2. **SC-H (Hierarchy)**: 系はネストされたマルコフブランケットを持つ
3. **SC-T (Time)**: 系は時間発展する遷移ダイナミクスを持つ
4. **SC-E (Embodiment)**: 系は外受容感覚と内受容感覚を区別する

---

## 2. 構成の骨格

### 2.1 パラメータ空間: 積統計多様体
POMDP 生成モデルの独立パラメータは、それぞれ独自の統計多様体上に存在する。
全パラメータ空間: $\mathcal{M} = \mathcal{M}_A \times \mathcal{M}_B \times \mathcal{M}_C \times \mathcal{M}_\gamma \times \ldots$

### 2.2 7座標 = POMDP 因数分解の独立因子

| 座標 | POMDP 因子 | 明示的数学的対象 | Axiomatic Depth |
|:---|:---|:---|:---:|
| Flow (I↔A) | $s_t$ vs $a_t$ | MB 境界分割 | 0 |
| Value (E↔P) | C-matrix | $V_{prag} = \mathbb{E}_Q[\log P(o|C)]$ | 1 |
| Function (Explore↔Exploit) | Epistemic Value | $V_{epist} = \mathbb{E}_{Q(s)}[D_{KL}(P(o|s) \| P(o))]$ | 1 |
| Precision (C↔U) | $\gamma$ | $P(\pi|\gamma) = \sigma(-\gamma G(\pi))$ | 1 |
| Scale (Mi↔Ma) | Hierarchical coupling | $\omega \in \mathbb{R}^+$ (連続弛緩) | 2 (SC-H) |
| Temporality (Past↔Future) | Planning horizon | $\tau \in \mathbb{R}^+$ (連続弛緩) | 2 (SC-T) |
| Valence (+↔-) | Interoceptive PE | $\propto -dF/dt$ (スカラー) | 2 (SC-E) |

### 2.3 24動詞 = 過完備辞書 (Overcomplete Dictionary)
積多様体 $\mathcal{M}$ の接空間における方向微分作用素。
$|\text{Generators}| = 2(\text{Flow}) \times 6(\text{factors}) \times 2(\pm) = 24$

合成規則: 同一因子内は自然勾配降下法 (Amari)、I↔A 間は FEP ループによる動的結合。

### 2.4 近似的機能独立性
Mean-field 変分推論の仮定: $Q(s,\pi,\gamma) = Q(s)Q(\pi)Q(\gamma)$
→ 推論ダイナミクス上で FIM がブロック対角化 → 近似的幾何学的直交性
（注: P多様体の厳密な直交性ではなく、Q多様体上の推論の独立性）

---

## 3. 捨てたもの（4ラウンドの Elenchos で除去）

| 主張 | 除去された理由 |
|:---|:---|
| ZFC 公理との類比 | FEP は論理公理ではなく変分物理原理 (R1) |
| $\mathbb{R}^6$ ベクトル空間 | POMDP パラメータは異なる型を持つ (R2) |
| 厳密な幾何学的直交性 | 潜在変数モデルの FIM は密行列 (R3) |
| Lie 代数 $\mathfrak{g}$ | 閉包未証明 + I/A のドメイン不一致 (R3) |
| ガロア接続 $A \dashv I$ | 余単位が Active Inference と矛盾 (R2-R3) |
| 「同型的」対応 | 定義的命名であって同型写像ではない (R2) |

---

## 4. 残る Minor 修正 (5件)

1. Q多様体（推論）と P多様体（生成モデル）の区別の明示
2. Epistemic Value を相互情報量 $I(o;s)$ で正確に定式化
3. 状態推論（瞬間的認知）とパラメータ学習（メタ認知）の区別
4. 「frame」→「overcomplete dictionary」に用語修正
5. Valence を $-dF/dt$（スカラー）に統一

---

## 5. 参照文献

- Spisak & Friston (2025): Self-orthogonalizing attractor networks from FEP
- Smithe, Tull & Kleiner (2023): Compositional Active Inference, Theorem 46
- Friston (2019): Markov blanket partitioning
- Parr & Friston (2019): EFE decomposition
- Amari (2016): Information Geometry and Its Applications
- Pezzulo, Parr & Friston (2022): Temporal depth independence
- Seth & Critchley (2013): Interoceptive prediction error and valence
