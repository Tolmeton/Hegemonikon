# 6 ⋊ 1 構造の正式記述

**結論**: 座標空間 = (6座標直積) ⋊_φ (Valence)。φ は v 依存で基質ごとに異なる。
**日付**: 2026-03-09

---

## 1. 定義

**Def 1** (HGK 座標空間). HGK の認知座標空間 $\mathcal{C}$ は半直積:

$$\mathcal{C} = H \rtimes_\phi K$$

ここで:
- $H = (\mathbb{R}^{\text{Value}} \times \mathbb{R}^{\text{Function}} \times \mathbb{R}^{\text{Precision}} \times \mathbb{R}^{\text{Scale}} \times \mathbb{R}^{\text{Temporality}} \times \mathbb{R}^{\text{Flow}})$ — 6座標の直積
- $K = \mathbb{R}^{\text{Valence}}$ — Valence 空間
- $\phi: K \to \operatorname{Aut}(H)$ — Valence による 6座標への修飾写像

**Def 2** (直積と半直積の区別).
- 直積 $H \times K$: $\forall (h, k), (h', k') \in H \times K$, $(h,k) \cdot (h', k') = (hh', kk')$
- 半直積 $H \rtimes_\phi K$: $(h,k) \cdot (h', k') = (h \cdot \phi(k)(h'), kk')$

直積では $K$ は $H$ に影響を与えない。半直積では $K$ (Valence) が $\phi$ を通じて $H$ (6座標) を変換する。

## 2. Fisher 情報行列による実証

### Smithe Theorem 46 (対偶)

> **Thm 46** (Smithe): M = M₁ ⊗ M₂ ⟹ F(M) = F(M₁) + F(M₂)
> **対偶**: F(M) ≠ F(M₁) + F(M₂) ⟹ M ≠ M₁ ⊗ M₂

### 実験結果 (2026-03-09)

v=0 でテスト: F_base = F_state + F_policy (**加法成立** ✅ → H 内は直積)
v≠0 でテスト: F_total ≠ F_base + F_v (**加法崩壊** ❌ → H×K は直積不成立)
→ 従って $\mathcal{C} \neq H \times K$

### 4定義比較 Fisher 実験

**条件**: n_states=3, n_obs=2, n_actions=2, v=0.5, ω=1.0

| 定義 | Ratio | s (状態) | π (方策) | ω (精度) | 主結合先 |
|:--|--:|--:|--:|--:|:--|
| **Joffily (2013)** | **1.91** | **1.91** | 0.00 | 0.00 | s (状態信念) |
| Seth (2013) | 1.04 | 1.11 | 0.01 | **2.08** | ω (精度) |
| Hesp (2021) | 1.23 | 0.18 | **1.13** | 0.00 | π (方策) |
| Pattisapu (2024) | 0.41 | 0.41 | 0.00 | 0.00 | s (状態信念) |

**Smithe ΔF_base** (v=0 → v≠0 でベースブロックがどれだけ変わるか):

| 定義 | ΔF_base | 意味 |
|:--|--:|:--|
| **Pattisapu** | 0.00 | ベースブロック不変 → 最も独立的 |
| Joffily | 0.17 | 弱い干渉 |
| Seth | 0.31 | 中程度の干渉 |
| **Hesp** | 1.38 | 最も強い干渉 (v が π を通じて全体に波及) |

### v 依存性の発見

| 定義 | Ratio (v≈0) | Ratio (v=0.5) |
|:--|--:|--:|
| Hesp | **0.22** | **1.23** |

Hesp 定義は v=0 近傍で弱結合 (lax)、v から離れると強結合化。

**解釈**: 半直積の $\phi(v)$ は $v$ の値に依存する。$\phi(0) \approx \text{id}$ (恒等)、$\phi(v \neq 0)$ は非自明。これは半直積の本質的特徴。

## 3. 圏論的定式化

### 3.1 随伴対 (F ⊣ G) としての Valence

Kalon の定義: $\text{Kalon}(x) \iff x = \text{Fix}(G \circ F)$

Valence の半直積構造は、この随伴対の**作用が座標空間に及ぶ**ことを意味する:
- $F$ (左随伴 = Explore): Valence が正 (v > 0) → 座標空間を「拡張」(行動の確信度↑)
- $G$ (右随伴 = Exploit): Valence が負 (v < 0) → 座標空間を「収縮」(行動の確信度↓)

### 3.2 φ の分類

$\phi$ はファイバー束 (fiber bundle) の構造群として解釈できる:
- 底空間: $K$ (Valence 空間)
- ファイバー: $H$ (6座標空間)
- 構造群: $\operatorname{Aut}(H)$

各定義は異なる接続 (connection) に対応:

```
φ_Seth:  v → Aut(H) を Precision 軸に沿って作用させる (乗法的)
φ_Hesp:  v → Aut(H) を Policy 軸に沿って作用させる (温度的)
φ_Patt:  v → Aut(H) を State 軸への射影で作用させる (加法的)
φ_Joff:  v → Aut(H) を VFE 勾配に沿って作用させる (微分的)
```

### 3.3 情報幾何学的記述

Fisher 行列 $F_{ij}$ のブロック構造:

直積の場合:
```
F = [ F_H   0  ]
    [  0   F_K ]
```

半直積の場合 (実際):
```
F = [ F_H        Φ(v)  ]
    [ Φ(v)^T     F_K   ]
```

ここで $\Phi(v)$ は off-diagonal ブロック (交差項)。$\Phi(0) \approx 0$、$\Phi(v \neq 0) \neq 0$。

$\operatorname{ratio} = \|\Phi(v)\|_1 / |F_{vv}|$ が半直積の「作用の強さ」を定量する。

## 4. 構造的まとめ

```
全座標空間 𝒞 = H ⋊_φ K

H = Flow × Value × Function × Precision × Scale × Temporality
    (d=1)  (d=2)   (d=2)      (d=2)      (d=3)   (d=2)

    H 内部は直積 (Fisher 加法成立)
    6座標間の交差項は v=0 でゼロ

K = Valence (d=3)

    K は H を修飾する (半直積)
    修飾の方法 (φ) は基質に依存
    φ(0) ≈ id (中立状態)
    φ(v≠0) ≠ id (非中立 → H が変形)

d 値一覧:
  d=1: Flow (MB 存在から直接)
  d=2: Value, Function, Precision, Temporality (FEP の帰結)
  d=3: Scale, Valence (構成的可能性 / 基質依存)
```

## 5. 確信度

| 判定 | 確信度 |
|:-----|:-------|
| H 内 6座標間は直積 (Fisher 加法) | [確信 90%] 90% |
| H×K は半直積 (Smithe 対偶) | [確信 90%] 85% |
| Joffily は最強結合 (ratio=1.91) | [確信 90%] 95% (実験の数値) |
| メタ枠組み (φ は基質依存) | [推定 70%] 80% |
| Hesp の v 依存性 (v=0 で 0.22, v=0.5 で 1.23) | [確信 90%] 95% (実験の数値) |

## 6. Open Problems

1. Joffily の高結合は排他的か？ → v = −dF/dt は dF/ds を通じて s と恒等的に結合する (構造的)
2. Pattisapu の ΔF_base=0 は意味深い — C·E[o] は s を通じて結合するが、ベースブロックを変えない。なぜか？
3. 適切な φ の分類定理は存在するか？ → [仮説 45%] φ は「結合先 × 結合型 (乗法/加法/温度/微分)」で 4×2 に分類可能？

---
*Analysis completed: 2026-03-09 21:15 JST*
*Experiment: valence_4def_fisher.py (source preserved)*
