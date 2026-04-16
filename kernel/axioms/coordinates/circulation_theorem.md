# 循環幾何定理 (Circulation Geometry Theorem)

> **体系的位置**: Problem E → Kernel 昇格 (v5.0)
> **依存**: axiom_hierarchy.md §定理⁴ (K₆ 完全性), L0.T Helmholtz (Γ⊣Q)
> **起源**: problem_E_m_connection.md §8.0-8.19
> **日付**: 2026-03-15 (v3.6 — §4.2.1 lax 2-functor [推定75%] + §4.2.2 F₂操作的構成 [推定78%] + 非線形検証: 二重井戸 ✓ (比15.6), Duffing ✓ (比16.8))

---

## §1 概要

非平衡定常系 (NESS) における確率密度 $p_{ss}$ と確率流 $j_{ss}$ の幾何を、
FEP のドリフト行列 $B = A + Q$ (対称＋反対称分解) に基づいて定式化する。

体系との接続:
- **L0.T**: Helmholtz (Γ⊣Q) の Q を幾何的に展開
- **定理⁴ (K₆ 完全性)**: X-series = G (対称) とは別に Q-series (反対称) が K₆ 上に乗る

---

## §2 基礎構造

### 2.1 ドリフト行列の分解

Fokker-Planck 方程式のドリフト行列 B を対称＋反対称に分解する:

```text
B = A + Q
A = (B + B^T)/2  (対称: ポテンシャル由来)
Q = (B - B^T)/2  (反対称: 循環由来)
```

定常分布: p_ss(x) ∝ exp(-V(x)/D)  (D = σ²/2)
定常確率流: j_ss = p_ss · Q∇V

### 2.2 循環空間 C_p

循環空間 C_p: j_ss をパラメトライズする。
循環メトリック g^(c): C_p 上の Fisher 的計量。

---

## §3 核心定理群 [全て数値検証済み]

### 定理 1: ω-不変性 (Circulation Invariance)

```text
div(p_ss · Q∇V) = 0
```

解析証明済み + 数値検証済み。
意味: 循環流は密度を変えない。循環は「仕事をしない力」。

### 定理 2: Wasserstein-循環分解 (W-C Decomposition)

```text
C_total = W₂² + d^(c)²
```

Helmholtz 分解 (j = j_irrot + j_sol) に基づく直交分解:
- W₂²: ポテンシャル (密度変化) 由来
- d^(c)²: 循環 (非平衡) 由来

### 定理 3: Q 双対性 (Q Duality)

```text
g^(c) = (σ⁴/4) Tr(Q^T Q · G^{sp}_F)
```

Fisher-Otto-循環の三角関係。
Fisher 情報行列の空間的成分と循環の幾何的測度を結ぶ。

### 定理 4: 動的 Q 双対性 (Dynamic Q Duality) — 定義的恒等式

```text
g^(c)(t) / I_F(t) = ω²σ⁴/4  (全時刻で成立)
```

**密度に依存しない恒等式** (kinematic identity)。
定常状態だけでなく過渡過程でも成立。数値検証精度: 10⁻⁸。

★ **性格**: これは「証明を要する定理」ではなく、g^(c) と I_F の定義から
代数的に従う恒等式 (→ §5.2 trade-off 恒等式):

```text
g^(c) = ω² ∫ p|∇V|² dx = ω²(σ⁴/4) I_F^{sp}   ← 定義の展開のみ
g^{(c,F)} = 1/ω²                                 ← ∂_ω log|j| = 1/ω (V 非依存)
積 = (σ⁴/4) I_F^{sp}                              ← ω が消える
```

前提: (a) |j_ss| = ω·p_ss·|∇V| (定義) + (b) T1 ω-不変性。
両方とも一般の閉じ込めポテンシャルで成立 → **OU 固有性なし**。

### 定理 5: n 次元一般化

```text
g^(c) = (σ⁴/4) Σ_k ω_k² I_F^(k)
```

n 次元の反対称行列 Q の Schur 分解:
- Q → Σ_{k=1}^{⌊n/2⌋} ω_k R_k  (R_k: k 番目の回転面)
- 各 ω_k: 独立な循環パターンの周波数
- n=2: ω₁ のみ (特殊ケース)
- n=6: ω₁, ω₂, ω₃ (HGK 体系に対応)

### 定理 10: Dually Flat ⟺ 等方回転 [確信 95%] (v3.0 追加)

```text
循環パラメータ空間 Ω が dually flat ⟺ ω_1 = ω_2 = ... = ω_{⌊n/2⌋}
```

**証明の骨子** (一般閉じ込めポテンシャル V(x)):
- (⇐) 等方 (ω_k = ω ∀k): |Q∇V|² = ω²|∇V|² → ∂_ω log|j| = 1/ω (x非依存) → g^{(c,F)} = 1/ω² は V 非依存。1D なので自動的に flat。 ■
- (⇒否定) 異方 (ω_k ≠ ω_l): U_k(x) = ω_k|∇V_k|²/Σ_l ω_l²|∇V_l|² が x 依存 → g^{(c,F)}_{kk} = E[U_k²]/ω_k² が V 依存 → dually flat にならない。 ■

数値検証: OU 4D (MC N=10⁶, 4つの A 設定で解析解一致 < 10⁻³) + 非 OU 3種 (Duffing 4D, DW 4D) × 2条件で等方 V 非依存性/異方 V 依存性を確認。

含意: 2D の結果 (§5.2) は n>2 等方の特殊ケース。**「認知スタイルと信念内容の独立性」は等方回転のみが保証する**。

[SOURCE: problem_E §8.18-8.18.1, verify_high_dim_c_alpha.py, test_non_ou_t10.py]

---

## §4 HGK 体系接続

### 4.1 K₆ 上の二重テンソル場 [確定]

axiom_hierarchy.md §定理⁴ との突合せ結果:

```text
K₆ グラフ (15 辺)
├ G_{ij} (対称): 辺の「平衡的結合強度」= X-series
│   |G_{ij}| = 座標間の統計的依存性 (Fisher 情報)
│   辺の有無 + 強度 → sloppy spectrum (G4)
│
└ Q_{ij} (反対称): 辺の「非平衡的循環強度」= Q-series
    Q_{ij} = -Q_{ji}: 座標間の **循環** ループ (★ /kat 確定: 因果ではない)
    Schur 分解 → 3 回転面 (ω₁, ω₂, ω₃)
    [確信 92% — Granger 因果実験: 面内 F >> 面間 F, 撤回条件: 面間 F>10 or TE>10%]
    → 15辺の個別定義: circulation_taxis.md *(not yet published)*
```

各辺は **2 つの独立なパラメータ** (G_{ij}, Q_{ij}) を持つ。
合計 30 のペア間パラメータが K₆ 上に乗る。

★ 旧仮説「X-series = Q の成分」は **棄却**。
  X-series は G (対称テンソル)、Q は別構造。

### 4.2 Helmholtz Γ⊣Q の展開

- axiom_hierarchy L28: L0.T 基底 = Helmholtz (Γ⊣Q)
- 循環幾何の Q = L0.T の Q そのもの
- → 循環幾何は L0.T (体系核外) の幾何的実現
- Helmholtz 関手 F: Phys → Geom は **Faithful but not Full** [推定 82%]
  - Faithful: d≤2 射の保存 (線形代数 + 圏論的構成で証明)
  - not Full: d=3 (Scale, Valence, Temporality) の Geom 射に Phys 対応物なし
  - 撤回条件: d=3 射の Phys 対応物発見 or 拡張関手構成
  - [SOURCE: axiom_hierarchy.md Lemma 6a, kat_Q_circulation_helmholtz_functor_2026-03-15.md]

#### 4.2.1 strict vs lax 判定 — **lax 2-functor** [推定 75%] (v3.4)

F: T → BiCat は **lax 2-functor**。strict ではない。

根拠: associator の時間発展 ∂α/∂t = -λ∇(Drift)(α) + J∇(Drift)(α) において:

```text
Γ_T (散逸的学習): 毎セッションで α を更新
  → F(η₂ ∘ η₁) ≅ F(η₂) ∘ F(η₁) (自然同型まで。厳密等号でない)

Q_T (保存的循環): J² = -Id により α を「回す」が「増やさない」
  → 合成の保存成分は strict

Γ_T ≠ 0 が一般的
  → 厳密等号 F(η₂ ∘ η₁) = F(η₂) ∘ F(η₁) は成立しない
  → laxitor φ: F(η₂) ∘ F(η₁) ⇒ F(η₂ ∘ η₁) の強度 ≈ ‖α(t)‖

α(t) → 0 の収束定理: 達人化 (expertise) で α が漸近的に 0 に収束
  → 「漸近的 strict 化」(asymptotic strictification)
  → lax 2-functor が学習の極限で strict に近づく
```

撤回条件: α(t) = 0 が有限時間で厳密に成立する構成の発見。

#### 4.2.2 F₂ 操作的構成 [推定 78%] (v3.4)

F₂: Sem → Geom の具体的計算手順 (全閉じ込めポテンシャル V で成立):

```text
Step 1. 定常共分散: Σ = solve_lyapunov(B, D·I)        [OU]
                     or MCMC 推定                      [non-OU]

Step 2. Fisher 行列: g^(F)_{ij} = (1/2) Tr(Σ⁻¹ ∂Σ/∂θ_i · Σ⁻¹ ∂Σ/∂θ_j)

Step 3. X-series 射影: G_{ij} = g^(F) の d=2 座標ペア成分 (対称)

Step 4. Q-series 射影: Q の Schur 分解 → 各回転面 ω_k
```

- OU では Step 1 に解析解が存在 (Lyapunov 方程式)
- non-OU では Step 1 が MCMC に依存。精度は N と V の滑らかさに依存
- Step 3-4 は K₆ 完全グラフの 15 辺への射影

[SOURCE: tek_helmholtz_functor_2026-03-15.md §3, kat_Q_circulation_helmholtz_functor_2026-03-15.md]

### 4.3 (s, π, ω) ブロック対角化との構造的同型 [仮説/条件付き成立]

Fisher 行列 G の (s, π, ω) ブロック対角化 (G5 φ分類定理) と
Q の Schur 分解による 3 回転面の関係:

```text
循環幾何                    HGK 体系
───────────────────────    ────────────────────
Q の Schur 分解 → 3面      G の (s,π,ω) → 3ブロック
各面: 2座標の回転           各ブロック: 2座標の直接結合
面間: 弱い (off-diagonal)   ブロック間: Valence 半直積で間接結合
ω_k: 回転周波数             ブロック内結合強度: |G_{ij}|
```

> [!WARNING]
> **H1 数値検証 (2026-03-15)**:
>
> G のブロック対角性 (mean-field) は Q を**直接拘束しない**。
> B = -(Γ+Q)Π で Γ, Π がブロック対角でも Q は自由。
>
> 数値実験 (`verify_h1_q_block.py`, N=500 trials × 28 ε値 × 4条件):
>
> | 条件 | 崩壊点 (alignment < 0.9) | 保護効果 |
> |:-----|:------------------------|:---------|
> | 等方 (ω₁=ω₂=ω₃) | **ε ≈ 0.01** (即座に崩壊) | なし |
> | 準縮退 (ω₁=ω₂≠ω₃) | ε ≈ 0.01 | なし (縮退面が脆弱) |
> | 弱異方 (ω₁>ω₂>ω₃, 比 ~1.5) | ε ≈ 0.07 | 7× |
> | 強異方 (ω₁>ω₂>ω₃, 比 ~10) | ε ≈ 0.09 | 9× |
>
> **結論**: 異方性 (ω₁≠ω₂≠ω₃) は固有値ギャップ効果により回転面の
> ブロック整列を保護するが、ブロック間結合が回転周波数の **~10% を超えると崩壊**する。
>
> **成立条件**: Q のブロック間成分 ≪ ブロック内成分 (≲ 10%)。
> これは mean-field 近似の精度が高いことと等価。

検証可能な予測:
G の最大非対角成分を持つ座標ペア = Q の最速回転面 ω₁ を形成するはず。
(**ただし H1 成立条件 (ε ≲ 0.1) 下でのみ有効**)

### 4.4 回転面のペアリング — **未決定** (v1.1)

> **⚠️ v1.1 前提精査 (2026-03-15)**: 候補 D は**レベル混同**により棄却。
> 全候補とも数学的に確定するには H1 (§4.3 仮説) の検証が必要。
> Q-series 15辺の定義は回転面ペアリングに依存しないため、
> circulation_taxis.md *(not yet published)* で独立に定義済み。
>
> H1 検証の引継ぎ: rom_Q_rotation_plane_verification.md

6 修飾座標を 3 ペアに分ける候補:

#### 候補 D: Γ⊣Q ペアリング — **棄却** (レベル混同)

axiom_hierarchy.md L2090-2118 の Γ/Q 写像テーブルから導出を試みたが、
**2つのレベルを混同**していた:

| レベル | 対象 | Q の codomain |
|:-------|:-----|:-------------|
| Helmholtz (L0) | 基底構造 Γ⊣Q | Coord_{all} (Flow を含む) |
| Stoicheia (L1) | Γ/Q の意味的連想 | Q(π)→Flow は**意味的連想** (L2095) |
| **K₆ (L2)** | **G_{ij}, Q_{ij}** | **Coord_{d≥2} (Flow を含まない)** |

棄却理由:
1. **Π₂ (Function ↔ Flow)**: Flow は K₆ の頂点ではない → K₆ 上の Q に適用不可
2. **Q(π) = Flow の地位**: axiom_hierarchy.md L2095 に「意味的連想」と明記されており演繹ではない
3. **Π₃ (Scale ↔ Temporality)**: Π₂ の残余として導出されたため、Π₂ 棄却に連動して根拠消失
4. **H1 の非自明性**: G のブロック対角性 (mean-field) が Q に転移する保証がない

#### 候補 A (次元ペアリング) — **棄却**

```text
  Π₁: Value(d=2) × Function(d=2)    — 学習の核心サイクル
  Π₂: Precision(d=2) × Scale(d=3)    — ズーム・確信ループ
  Π₃: Valence(d=3) × Temporality(d=3) — 情動-時間ループ
```

棄却理由: Γ/Q 写像構造と不整合。Value と Function は異なるブロック (s と π) の
Γ 像であり、同一回転面に属する根拠がない。d=2 という次元の一致は偶然。

#### 候補 B (族ペアリング) — 保留

```text
  Π₁: Value × Valence
  Π₂: Function × Temporality
  Π₃: Precision × Scale
```

Valence を回転面の軸とするが、φ分類定理では Valence は全ブロック横断の半直積修飾。
回転面の構成要素とするのは構造的に疑問。

#### 候補 C: Q の Schur 分解が決定 (事後的) — トートロジー

#### 現状要約 (v1.1)

| 候補 | 方法 | 状態 | 棄却/保留理由 |
|:-----|:-----|:-----|:-----------|
| A | 次元 (d=2/d=3) | **棄却** | Γ/Q 写像構造と不整合。d の一致は偶然 |
| B | 族 (Telos/Methodos/...) | **保留** | Valence は半直積修飾。回転面構成要素とするのは疑問 |
| C | Schur 分解 (事後的) | **トートロジー** | 「Q を対角化した結果が Q の構造」— 情報なし |
| D | Γ⊣Q ペアリング | **棄却** | Helmholtz (L0) と K₆ (L2) のレベル混同 |

**結論**: 回転面ペアリングは **H1 (§4.3) の検証** を待つ必要がある。
G のブロック対角性が Q に転移するかを実験的に確認し、転移パターンからペアリングを決定する。
Q-series 15辺の定義はペアリングに依存しないため、独立に進行可能。

### 4.5 /kat 統合: Q の因果的解釈の棄却 (2026-03-15)

> **起源**: /noe+ (理論) → /pei (Granger 因果実験) → /tek (関手構成) → /kat (確信固定)

Q_{ij} が「因果」(V2) ではなく「循環」(V1) であることを実験的に確定:

```text
実験: 6D 異方 OU, N=10000, T=30.0, 3回転面 (ω₁=2.0, ω₂=0.8, ω₃=0.3)

結果: Granger F-statistic
  面内ペア (0↔1, 2↔3, 4↔5): F = 128–203 (高い双方向 Granger 因果)
  面間ペア (0↔2, 0↔4, 2↔4 等): F ≈ 0.5–2.5 (有意でない)
  比率: 面内/面間 ≈ 50–400 倍

判定: V1 (循環) — 面内の強い双方向因果 + 面間の無因果 = 回転面内の循環構造
```

Q_{ij} の解釈:
- ✅ **循環**: Q の Schur 分解による回転面内の双方向ループ (実験で確認)
- ✗ **因果**: 面間因果関係は統計的に有意でない (Granger F < 基準値)

| 命題 | ラベル | 確信度 | 撤回条件 |
|:-----|:-------|:-------|:---------|
| Q_{ij} = 循環 ≠ 因果 | [確信 90%] | 92% | 面間 F>10 再現 or Transfer Entropy>10% |
| F: Phys→Geom = Faithful/¬Full | [推定 70%] | 82% | d=3 射の Phys 対応物発見 |

[SOURCE: sim_granger_causality_q.py, kat_Q_circulation_helmholtz_functor_2026-03-15.md, axiom_hierarchy.md v4.7.0]

---

## §5 双対接続理論 [確信 85%]

> problem_E_m_connection.md §8.15 の結果を Kernel 表現にまとめる。
> Amari の α-接続を current geometry に拡張し、循環空間の情報幾何的構造を確立する。

### 5.1 c-α 接続 (Current α-Connection)

密度幾何の α-接続 (Amari 1985) に倣い、循環空間上に c-α 接続を定義:

```text
Γ^{(c,α)}_{μν,ρ} = E_{p_ss}[
  ∂_μ ∂_ν log|j_ss| · ∂_ρ log|j_ss|
  + (1-α)/2 · ∂_μ log|j_ss| · ∂_ν log|j_ss| · ∂_ρ log|j_ss|
]
```

構造的類似:
- Amari: l = log p(x;θ) → 密度の対数
- Current: l^(c) = log|j_ss(x;ω)| → 電流の対数

特殊場合:
- α = 1: c-e 接続 (exponential-current)
- α = -1: c-m 接続 (mixture-current)
- α = 0: c-LC 接続 (Levi-Civita)

### 定理 6: c-双対性 (Current Duality)

```text
∇^{(c,α)} と ∇^{(c,-α)} は g^(c) に関して双対:
∂_ρ g^(c)(X, Y) = g^(c)(∇^{(c,α)}_ρ X, Y) + g^(c)(X, ∇^{(c,-α)}_ρ Y)
```

証明: Amari の証明と同型。l → l^(c) への置換。j_ss > 0 を仮定。

### 5.2 電流 Fisher 計量 (Current Fisher Metric)

パラメータ空間上の Fisher 的計量:

```text
g^{(c,F)}_{μν} = ∫ ∂_μ log|j_ss| · ∂_ν log|j_ss| · p_ss dx
```

一般の閉じ込めポテンシャルで成立 (OU 限定でない):

```text
|j_ss| = ω · p_ss · |∇V|  (定義)
log|j_ss| = log ω + log p_ss + log|∇V|
∂_ω log|j_ss| = 1/ω   (p_ss, ∇V は ω に依存しない: T1)
→ g^{(c,F)} = E[(1/ω)²] = 1/ω²   (ポアンカレ半直線 H¹の計量)
```

★ Trade-off 恒等式 (**定義的恒等式** — 全閉じ込めポテンシャルで成立):

```text
g^(c) = ∫|j_ss|²/p_ss dx = ω² ∫ p_ss|∇V|² dx = ω²(σ⁴/4) I_F^{sp}
g^{(c,F)} = 1/ω²

→ g^(c) · g^{(c,F)} = (σ⁴/4) I_F^{sp}  (ω が消える!)
```

物理的解釈 (不確定性関係):
- (循環コスト) × (循環感度) = (地形の急峻さ)
- ω 大 → 物理コスト大 but パラメータ感度小
- ω 小 → 物理コスト小 but パラメータ感度大
- trade-off は Fisher 情報 I_F^{sp}(V) のみで制約される

### 定理 7: Current-Density 双対性 (一般 — v2.1 修正)

```text
拡張パラメータ空間 M = M_density × M_circ 上:
G = g^(F) ⊕ g^{(c,F)}   (直和 = ブロック対角)
```

証明:
  (i) p_ss が ω に依存しない (T1) → g^(F) は ω の関数でない
  (ii) 交差項 G_{i,μ} = -(2/σ²ω_μ) E[∂_i V]
  (iii) 部分積分定理:
        E[∂_i V] = ∫ ∂_i V · p_ss dx = C ∫ ∂_i V · exp(-2V/σ²) dx
                 = -(Cσ²/2) [exp(-2V/σ²)]_{boundary} = 0
        (∵ V → ∞ at boundary → exp(-2V/σ²) → 0)
  → E[∂_i V] = 0 は **全ての閉じ込めポテンシャル**で成立。

★ v2.0 の「非 OU では E[∂_i V] ≠ 0」は誤り (7 種のポテンシャルで数値検証)。
★ 物理的意味: ∇V · p_ss = -(σ²/2) ∇p_ss → ∫ ∇V · p_ss dx = 0 (正規化の帰結)。

### 5.3 Dually Flat 構造と IS Divergence (一般 — v2.1)

循環空間は **一般の NESS** で dually flat:

```text
核心: ∂_ω log|j_ss| = 1/ω  (V 非依存)

証明:
  j_ss = p_ss · Q∇V = p_ss · ω J ∇V
  |j_ss| = ω · p_ss · |J∇V|  (ω > 0)
  log|j_ss| = log ω + log p_ss + log|J∇V|
  ∂_ω log|j_ss| = 1/ω  (p_ss, ∇V は ω に依存しない: T1)

→ g^{(c,F)} = E[(1/ω)²] = 1/ω²  (V の形に一切依存しない!)
```

座標構造:

```text
c-e 平坦: ω が e-座標 (j_ss は ω に線形 → mixture 的)
c-m 平坦: η = log ω が m-座標 (g_{ηη} = 1 → Christoffel = 0)

ポテンシャル関数 (V 非依存):
  ψ(η) = Σ_μ η_μ² / 2   → ∂²ψ/∂η² = 1 = g_{μμ}  ✓
  φ(ω) = -Σ_μ log ω_μ   → ∂²φ/∂ω² = 1/ω² = g_{μμ}  ✓

Legendre 関係: η_μ = log ω_μ ⟺ ω_μ = e^{η_μ}
```

自然なダイバージェンス:

```text
D^(c)(ω ∥ ω') = Σ_μ [ω_μ/ω'_μ - log(ω_μ/ω'_μ) - 1]
              = Itakura-Saito divergence  (V 非依存)
```

★ IS divergence が循環空間の自然な距離として出現。

**高次元条件 T10 (v2.5 追加)**:

```text
n ≥ 4 (複数回転面) のとき dually flat ⟺ 等方回転 (ω_k = ω, ∀k):
  等方: ∂_ω log|j| = 1/ω (x非依存) → g^{(c,F)} = 1/ω² (V非依存) → dually flat ✅
  異方: ∂_{ω_k} log|j| = U_k(x) (x依存) → g^{(c,F)} は V依存 → dually flat ✗

非 OU 検証: Duffing 4D、Double Well 4D で確認 (MCMC, N=50K):
  等方 scalar = 1/ω² (小数4桁一致、V非依存)
  異方 g_00 変動: 0.04 (Duffing) — 0.31 (DW)

→ T10 は任意ポテンシャルで成立 [確信 95%]
  (証明: problem_E_m_connection.md §8.18.1)
```

### 定理 8: c-Pythagoras (一般 — v2.1) [推定 65%]

```text
Dually flat 空間の射影定理:
ω_* = argmin_{ω' ∈ S} D^(c)(ω ∥ ω')  (S: e-flat 部分多様体)
⟹ D^(c)(ω ∥ ω'') = D^(c)(ω ∥ ω_*) + D^(c)(ω_* ∥ ω'')
    ∀ ω'' ∈ S
```

認知的意味: 循環パターンの学習が情報幾何的に最適に分解される。

### 5.5 密度-循環双対性 (Density-Circulation Duality) — v2.3 追加

> **起源**: problem_E_m_connection.md §7.4 (旧称: 確率電流仮説)
> 用語改名 (v4.2): current geometry → **循環幾何** (Circulation Geometry)
> 仮説 → 双対性に昇格: 🟢 数値 + 解析で完全立証済み

#### 核心主張

NESS は **(p_ss, j_ss)** — 密度と循環の対で特徴づけられ:
- Γ → p_ss (密度): 系がどこにいるか (存在)
- Q → j_ss (循環): 系がどう動くか (動態)

この両者が **幾何的に独立** であることが、循環幾何の全構造の源泉。

#### 定理 9: 密度-循環独立性定理 (Density-Circulation Independence)

```text
定理: overdamped Langevin 系の NESS を
パラメータ θ = (密度パラメータ) × ω = (循環パラメータ) で特徴づけるとき、
拡張 Fisher 計量 G は

    G = g^(F)(θ) ⊕ g^{(c,F)}(ω)

と分解される (ブロック対角)。ここで:
(i)   g^{(c,F)}_μν = δ_μν / ω_μ²  (V 非依存, dually flat)
(ii)  交差項 G_{i,μ} = 0 は部分積分定理 E[∂_i V] = 0 から従う
(iii) g^(F)(θ) は Amari の標準 Fisher 計量
```

**証明**: T7 (Current-Density 双対性) に同じ。T1 (ω-不変性) + 部分積分定理で交差項が消える。
全閉じ込めポテンシャルで成立 (OU 限定でない)。

**系 (Corollary)**:

```text
C1: 密度パラメータ θ と循環パラメータ ω の推定は統計的に独立。
    → MaxLik 推定で θ̂ と ω̂ は互いの精度に影響しない。

C2: 循環空間 C_p 上の IS divergence は V 非依存:
    D^(c)(ω ∥ ω') = Σ_μ [ω_μ/ω'_μ - log(ω_μ/ω'_μ) - 1]
    → 循環パターンの「距離」はポテンシャル地形を知らなくても計算可能。

C3: trade-off 恒等式 (不確定性関係):
    g^(c) · g^{(c,F)} = (σ⁴/4) I_F^{sp}
    → (housekeeping EP) × (循環感度) = (密度の空間 Fisher 情報) × 定数
    → 物理コストと推定精度の積は地形のみで制約される。
```

**確信度**: [確信 90%] 90%。T7 の一般化証明 + 7 種ポテンシャル数値検証に基づく。

### 5.6 TUR との精密な対比 (v2.3 追加)

```text
■ 標準 TUR (Barato-Seifert 2015, Gingrich et al. 2016):

  Var[J] / ⟨J⟩² ≥ 2 / σ̇

  → EP σ̇ が小さいほど確率流のゆらぎが大きい (物理的制約)
  → 不等式。σ̇ の下界を与える。

■ Kolchinsky et al. の一般化 TUR (arXiv:2206.14599 §6):

  σ̇_hk ≥ 2⟨J⟩² / Var[J]    (housekeeping EP の下界)
  σ̇_ex ≥ 2⟨dπ/dt⟩² / Var[j]  (excess EP の下界 + speed limit)

  → EP を housekeeping/excess に分けた TUR
  → 不等式。far-from-equilibrium でも成立。

■ 我々の trade-off 恒等式:

  g^(c) · g^{(c,F)} = (σ⁴/4) I_F^{sp}

  → EP × Fisher 情報 = 定数 (等号! 不等式ではない)
  → 物理コストと推定精度の積が一定
  → パラメータ空間上の等式 (力空間の不等式ではない)
```

| 比較軸 | 標準 TUR | Kolchinsky TUR | 我々の trade-off |
| --- | --- | --- | --- |
| **対象** | 物理空間の流れ J | 力空間の EP 分解 | パラメータ空間の Fisher 計量 |
| **数学的形式** | 不等式 (下界) | 不等式 (下界) | **等式** (恒等式) |
| **分解** | σ̇ vs Var[J] | σ̇_hk vs σ̇_ex | g^(c) vs g^{(c,F)} |
| **適用範囲** | NESS 全般 | 線形・非線形離散系 | overdamped Langevin NESS |
| **幾何的構造** | なし | 力空間の射影 | パラメータ空間の dually flat |
| **V の役割** | 暗黙 | 暗黙 | **明示的** (I_F^{sp} として) |

[主観] TUR は「下界はいくらか」を問う。我々の trade-off は「正確にいくらか」を答える。等式である点が根本的な新規性。ただし overdamped Langevin に限定される点は TUR より狭い。

---

## §7 先行研究との対応 (v2.2 追加)

### 7.1 Kolchinsky, Dechant, Yoshimura, Ito (2022)

**"Information geometry of excess and housekeeping entropy production"** arXiv:2206.14599

力空間で EP を Pythagorean 分解: σ̇ = σ̇_hk + σ̇_ex
- σ̇_hk = min_ϕ D(f || -∇ϕ) — 非保存力の「残差」
- σ̇_ex — 時間変化による EP (定常では = 0)

**我々との対応**:

| Kolchinsky et al. | 本文書 | 関係 |
| --- | --- | --- |
| σ̇_hk (housekeeping EP) | g^(c) (物理コスト) | ∝ (定常で σ̇ = σ̇_hk) |
| 力空間の直交分解 | パラメータ空間のブロック対角性 (T7) | 相補的 |
| 一般化 KL divergence | IS divergence (H8) | 異なる空間で parallel |

**新規性の判定**:
- ✅ **g^{(c,F)} の V 非依存性**: 彼らの枠組みでは未議論
- ✅ **Fisher 計量のブロック対角性 (T7)**: パラメータ推定の独立性は彼らの問いにない
- ✅ **dually flat + IS divergence の普遍性 (H8)**: 循環パラメータ空間の幾何は未探索
- ✅ **trade-off 不確定性関係**: コスト × 精度 = 地形

**TUR 精密対比** (v2.3):

| 軸 | Kolchinsky et al. TUR | 本文書 trade-off 恒等式 |
| --- | --- | --- |
| 空間 | 力空間 (thermodynamic forces) | パラメータ空間 (θ = (k,σ,ω)) |
| 構造 | Pythagorean 不等式 (KL 射影) | 定義的恒等式 (部分積分) |
| 形式 | σ̇ ≥ σ̇_hk + σ̇_ex (分解) | g^(c)·g^{(c,F)} = (σ⁴/4)I_F (等式) |
| 成立条件 | 一般離散系 (線形/非線形) | OU 過程 (ただし H8 で一般化の兆し) |
| 主結果 | EP の下界 (TUR + 速度限界) | 循環コスト × 推定感度 = 地形定数 |
| 認知的解釈 | なし | System 1/2 + Explore/Exploit (§5.4) |
| Falasco et al. (2019) | 彼らの一般化の特殊ケース | 異なる空間での相補的結果 |

**深層対応** (/ccl-read 全文精読 2026-03-14):

1. **Pythagorean 分解 ↔ T7 ブロック対角性**:
   Kolchinsky の核心 Eq.(6): D(f‖0) = D(f‖-∇φ*) + D(-∇φ*‖0) は
   力空間における KL の直交分解。我々の T7 は Fisher 計量の
   パラメータ空間における直交分解 (G_{i,ω} = 0)。
   両者は **異なる空間で parallel な直交構造** を持つ。
   [確信 90%] 85% — 数学的対応は明確だが圏論的定式化は未完。

2. **SM7.2 Onsager-projective 分解 = 最近接先行研究**:
   [14] の分解 σ̇ = ‖f - (-∇φ*_ons)‖²_L + ‖∇φ*_ons‖²_L は
   **Euclidean 計量での射影**。Kolchinsky は KL divergence に拡張。
   我々の trade-off は **Fisher 計量での積** (射影ではなく積!)。
   → 階層: σ̇_ex ≤ σ̇_ex^hess ≤ σ̇_ex^ons (SM7.3 数値確認)
   我々の等式は不等式の飽和条件ではなく **別の量の等式**。

3. **φ* 最適ポテンシャル ↔ V(x)**:
   Kolchinsky の φ* は σ̇_hk を最小化する「有効自由エネルギー」。
   SM4 で勾配流 dt p = -K grad_p Φ(p) を導出。
   我々の V(x) は FEP のポテンシャルそのもの。
   → φ* は**システムの状態空間に存在**し、
     V は**パラメータで制御される外的ポテンシャル**。
   → [推定 70%] 定常で φ*_x ∝ V(x_i)/D の関係が成立する可能性。

4. **SM4 勾配流 ↔ FEP VFE 最小化** (定式化済み 2026-03-14):

   **数学的対応** (5つの射):

   | Kolchinsky SM4 (Eq.S42-S46) | FEP (Friston 2019 §4) | 備考 |
   |--------|--------|------|
   | K (正定値 Onsager 行列) | Γ (対称: 散逸成分) | 勾配流の「速度」 |
   | D(p‖π*) (一般化 KL) | F[q] (VFE) | 減少する Lyapunov 関数 |
   | dt p = -K grad D(p‖π*) | ẋ_μ = -Γ ∇F(x_μ) | 勾配流の構造的同型 |
   | σ̇_ex (excess EP) | -dF/dt (VFE 減少率) | 学習中に正、定常でゼロ |
   | σ̇_hk (housekeeping EP) | Q 成分のコスト (ω²) | F を変えない循環の維持コスト |

   **SM4 → FEP への拡張**: Kolchinsky の gradient flow は保存力系で厳密。
   FEP では Q ≠ 0 (solenoidal flow) が加わるが、ẋ_μ = -(Γ+Q)∇F において
   Qᵀ = -Q より -dF/dt = (∇F)ᵀΓ(∇F) ≥ 0 は Q に依存しない (Friston 2019 Eq.2.4)。
   → σ̇_ex は「Γ 経由の VFE 減少」に対応し、σ̇_hk は「Q による循環コスト」。

   **数値実験** (2D OU, CORTEX 解析解, k₁=k₂=1, σ²=1, μ₀=[1,0]):

   ```
   σ̇_hk = 2ω²,  σ̇_ex(t) = 2(1+ω²)e^{-2t}
   ratio(t) = (1+1/ω²)e^{-2t},  t* = (1/2)ln(1+1/ω²)
   ```

   | ω | σ̇_hk | ratio(0) | t* (切替時刻) |
   |---|-------|----------|--------------|
   | 0 | 0 | ∞ | ∞ (純学習) |
   | 0.5 | 0.5 | 5.0 | 0.81 |
   | 1.0 | 2.0 | 2.0 | 0.35 |
   | 2.0 | 8.0 | 1.25 | 0.11 |
   | 5.0 | 50 | 1.04 | 0.02 |
   | 10 | 200 | 1.01 | 0.005 |

   **認知的含意** (→ problem_E_m_connection.md §8.16 と接続):
   - ω 大 (System 2): t* が極端に短い → 学習相が瞬時に終わり維持コストが支配
   - ω 小 (System 1): t* が長い → 学習 (密度推定) に時間をかけられる
   - t* = S-I/S-II 切替のタイミング: ratio > 1 で学習優位、< 1 で維持優位
   - trade-off: ω 大は「多様な探索」(σ̇_hk 大) を可能にするが「密度学習」(t*→0) を犠牲にする
   [推定 70%] — 解析解は正確、認知的解釈の妥当性は ω-認知スタイル対応に依存

### 7.2 Dechant, Sasa, Ito (2021-2022)

**"Geometric decomposition of entropy production"** PRR 4, L012034 (48 citations)

状態空間での確率流の直交分解。excess/housekeeping/coupling の3成分。

- coupling 成分: time-dependent × nonconservative の相互作用 → **定常系ではゼロ**
- 我々の交差項ゼロ (G_{i,ω} = 0) は別の機構 (部分積分 E[∂_i V] = 0)

### 7.3 位置づけ

本文書の結果は Kolchinsky et al. と **相補的 (complementary)**:
- 彼ら: 固定システムの EP の力分解 (力空間の幾何)
- 我々: パラメータ変動に対する推定構造 (パラメータ空間の幾何)

---

## §5.7 過渡過程における trade-off 回復 [確信 85%] (v3.0 追加)

> problem_E §8.17 の結果を統合。

定常状態の trade-off 恒等式 g^(c)·g^{(c,F)} = (σ⁴/4)I_F^{sp} は ∂_ω p_ss = 0 に依拠する。
過渡状態では p(x,t) が ω に依存し (∂_ω p(x,t) ≠ 0)、恒等式は崩れる。

### 数値検証結果

Fokker-Planck 方程式を ω, ω±Δω で並列時間発展し、R_IF(t) = I_F(t)/I_F^{sp} の収束を追跡:

```text
パラメータ: σ=1.0, ω=1.0, grid 60², dt=0.0005
初期条件: N((1.5, 1.0), 0.6²I) — 定常から大きくずれたガウス分布

                   R_IF(t=0)    R_IF(最終)    KL(最終)     収束判定
  OU:              3.97         1.05 (t=2.0)  0.06         ✅
  Duffing:        44.26         1.01 (t=3.0)  0.01         ✅
  DoubleWell:     26.28         0.97 (t=3.0)  0.08         ✅
```

全3ポテンシャルで R_IF → 1, KL → 0 を確認。

### 発見と含意

1. **収束速度はポテンシャルに依存**: OU (線形) > Duffing (非線形) > DoubleWell (双峰)
2. **R_IF の回復 ⟺ p(t) → p_ss ⟺ σ̇_ex(t) → 0**: パラメータ空間と力空間で同じ物理
3. **認知的含意**: 認知状態遷移 (System 1→2) の過渡期で trade-off が崩れ、定常確立で回復

```text
[確信 90%] trade-off 恒等式は定常の定義的恒等式であり、過渡では崩れる
[確信 85%] I_F(t) → I_F^{sp} の収束が回復機構
[推定 75%] 収束速度は V の曲率に依存
```

[SOURCE: problem_E §8.17, verify_transient_tradeoff.py]

---

## §5.8 Kolchinsky-FEP 構造同型の拡充 (v3.0 追加)

> §7.1 の gradient flow↔VFE 対応 (5射) を過渡過程・3分解と接続。

### Non-autonomous gradient flow ↔ FEP learning

Kolchinsky SM4 の指摘: π* が p に依存しうる場合の non-autonomous gradient flow →
Lyapunov 安定性は保証されない。

```text
autonomous gradient flow   = 固定モデルでの推論 (perception)
  → F は単調減少 → σ̇_ex → 0 ... 学習の収束

non-autonomous gradient flow = モデル更新を伴う学習 (learning)
  → F の単調減少は保証されない → σ̇_ex は振動しうる
```

### Dechant-Sasa-Ito 3分解との接続

速度場の3直交分解: ν = ν* (excess) + ν^st (housekeeping) + ν^cp (coupling)

Helmholtz との対応:

| Helmholtz (FEP) | 3分解 | 力学的同定 |
|---|---|---|
| Γ∇F (散逸) | σ̇_excess | 勾配場: F を減少 |
| Q∇F (ソレノイダル) | σ̇_housekeeping | 循環場: F を変えない |
| — (2分解に存在しない) | σ̇_coupling | 干渉場: Γ と Q が同じ自由度で競合 |

### coupling の数値検証

```text
結果 1: 等方 OU → coupling = 0 (全時刻で厳密にゼロ)
  ★ T10 と整合: 等方性が C^st の ω 非依存性を保証し coupling を殺す

結果 2: 異方 OU + ω振動 → coupling ≠ 0
  |σ̇_cp|/σ̇_total ≈ 4-19% (有意だが支配的ではない)

結果 3: σ̇_cp ≤ 0 の普遍性 (全6実験で確認)
  → 緩和と循環が反対方向に作用 → 干渉は常に EP を減らす
```

```text
[確信 90%] 等方 OU で coupling = 0
[確信 85%] 異方 OU + ω変動で coupling ≠ 0
[推定 75%] σ̇_cp ≤ 0 は OU での普遍的性質
```

[SOURCE: problem_E §8.17.2, coupling_numerical_v3.py, ix_diagnostic_v2.py]

---

## §6 認知科学接続 (v3.0 全面再編)

> problem_E §8.16-8.16.2 + §8.19-8.19.2 の成果を統合。
> C2 確信度推移: 30% (初版) → 60% → 75% → 80% → 82% → 84% → **86%**

### 6.1 ω の認知的操作定義

**命題**: 「どう考えるか」(ω) は「何を信じるか」(V) の複雑さに影響されない

**操作定義 (3段階)**:

| Level | 手法 | 出力 | 制約 |
|---|---|---|---|
| L1 Model-free | 時間遅れ共分散の反対称成分 → TII | TII ∝ \|ω\| | ω の proxy のみ |
| L2 Model-based | OU fitting → B の反対称成分 Q → SVD | ω_k (各回転面) | 線形近似に限定 |
| L3 Info-geometric | 複数条件で p(x\|θ,ω) をフィット → g^{(c,F)} 推定 | g^{(c,F)} = 1/ω² の検証 | 十分なデータ量が必要 |

**ω ↔ System 1/2 対応** (v5.2 修正済み: ω大 = System 2):

| ω | 物理 | 認知的解釈 |
|---|---|---|
| ω ≈ 0 | 平衡 | 反復的・膠着 (反芻) |
| ω 小 | EP 小 | System 1: 直観的・自動的 |
| ω 大 | EP 大 | System 2: 熟慮的・意志的 |
| ω 不安定 | EP ゆらぎ | ADHD 的注意制御不安定性 |

根拠: EP ∝ ω² + ウィルパワー消費 + 実験データ (タスク中 EP > 安静時)

[SOURCE: problem_E §8.16.1, Nartallo-Kaluarachchi 2025]

### 6.2 実験的証拠体系 (P1-P4)

#### P1-P3: 検証可能な予測

| 予測 | 内容 | 測定法 |
|---|---|---|
| P1 | ブロック対角性: θ と ω の推定誤差相関 ≈ 0 | fMRI time series → OU fitting |
| P2 | V 非依存性: ω の推定精度がタスクに依存しない | 異なる V でのタスク間比較 |
| P3 | AuDHD 群 vs 定型群の ω 分布差 | 群間の ω_trait 比較 |

#### P4: 二重 FIM 数値検証 (核心的発見)

```text
| FIM の種類    | ω のランク (n=4) | ω のランク (n=6) | ω のランク (n=8) |
|---------------|-----------------|-----------------|------------------|
| 分布 FIM      | 11/11 (最 sloppy) | 22/22         | 37/37            |
| 流 FIM        | 1/11 (最 stiff)  | 1/22           | 1/37             |
| 複合 FIM (α=0.48) | 1/11          | 2/22           | 2/37             |
```

**核心**: ω は「分布では見えないが、流では最も重要」
- 分布 FIM で sloppy = 定常分布が ω に鈍感 = g^{(c,F)} = 1/ω²
- 流 FIM で stiff = EP が ω に鋭敏 = g^(c) = ω²
- 両者の積が一定 = trade-off 恒等式の物理的意味

**Chen (2025) との接続**: PMEM で ω が見えない理由の数学的説明 + α=0.48 の解釈

[SOURCE: problem_E §8.16.2, verify_omega_stiff.py]

### 6.3 PMEM → Kinetic Ising → OU の統一的接続 (v3.0 追加)

```text
   PMEM (対称)        kinetic Ising (非対称)        OU model (連続)
   J_ij = J_ji         J_ij ≠ J_ji                  B = S + ωA
   EP = 0               EP ∝ Σ(J_ij-J_ji)²          EP ∝ ω²
   ω 定義不能           ω = ||A||_F                  ω = スカラー
```

**3命題**:

1. **ω の不可視性** [確信 90%]: PMEM で ω は構造的に定義不能 (Boltzmann 分布の対称性)
2. **ω の可視化には時間方向が必要** [推定 80%]: 遷移確率 P(s(t)|s(t-1)) が反対称成分を可視化
3. **二重 FIM の一般化** [仮説 70%]: kI でも「分布-sloppy / 流-stiff」が成立

**Ishihara & Shimazaki (2025)** との接続:
- state-space kinetic Ising: マウス V1 で EP/spike → 成績の直接相関
- 非対称結合の entropy flow がタスク成績を予測 → ω ↔ 認知効率の独立した実験的支持
- coupling variability がタスク中に増大 + asymmetry 有意増大 (p=1.185e-5)

**Q1 (Kinetic Ising FIM ↔ OU 二重 FIM) の解答**:

```text
(a) 定常分布 FIM: kI では C = C(J^S) + O((J^A)²) → J^A は sloppy
                  OU では Σ = Σ(S), ∂Σ/∂ω = 0 → ω は厳密にゼロ感度

(b) 遷移確率 FIM: kI では G^(i) = E[p_i(1-p_i)·x_j·x_k] → J^S, J^A に等しく依存
                  OU では G^tr = (1/σ²)E[(Bx)(Bx)] → S, ωA に等しく依存
                  → 両者で反対称成分は stiff

(c) Mézard 接続: D^A ∝ J^A · C → 時間遅延相関の反対称部分が反対称結合を反映
```

[SOURCE: problem_E §8.19-8.19.1, Ishihara & Shimazaki 2025 (Nature Comm.), Mézard & Sakellariou 2011]

### 6.4 TUR + Cramér-Rao + Trade-off の情報幾何的三角形 (v3.0 追加)

> problem_E §8.19.2 の結果を統合。

**Q2 (Entropy Flow と Trade-off の TUR 接続) の解答**:

```text
trade-off 恒等式の EP 表現:
  g^(c) = ω² = (σ²/2) · EP_ss    (等方、S = aI)
  → EP_ss = 2/(σ² · g^{(c,F)})

情報幾何的 TUR:
  Var(J_τ) / ⟨J_τ⟩²  ≥  σ² · g^{(c,F)} / τ
  = (電流 Fisher 計量) × (拡散強度) / (観測時間)
```

**解釈**: g^{(c,F)} 大 (ω に脆い) → カレントの変動比下界が大きい → 精度が悪い
→ g^{(c,F)} を下げる = EP を増やす = コスト増 → **EP は精度の「資源」**

**Ishihara の「EP/spike → 成績」の TUR 的解釈**:
- EP 大 → TUR 下界が下がる → 低変動カレントが可能 → 高精度な信号伝送 → 高成績
- trade-off: EP は認知の「精度コスト」であり、循環 ω はその生成源

```text
[確信 85%] g^(c) = (σ²/2)·EP_ss は OU で厳密に成立
[推定 75%] 情報幾何的 TUR は trade-off の帰結として自然に導出される
[推定 70%] Ishihara の EP/spike は ω による EP 生成率の正規化と実質的に同等
```

[SOURCE: problem_E §8.19.2, Barato & Seifert 2015, Proesmans & Van den Broeck 2017]

### 6.5 応用仮説 (旧 §6, 最小変更)

#### Hyphē の τ-ω 対応 [仮説 45%]

Hyphē の chunk 分割パラメータ τ と循環 ω の理論的対応:
- τ → ∞: 全体が1 chunk → ω 大に対応 (遅い、全体的処理)
- τ → 0: 各要素が独立 → ω 小に対応 (速い、局所的処理)

#### 24定理との Kalon 条件 [仮説 45%]

24定理 (Poiesis) の動詞が c-α 接続上の測地線として定式化可能な条件を探索中。
候補: ωσ² = 2 (T4 恒等式から演繹的に導出される臨界点)

#### AuDHD パラメータ化 [仮説 45%]

AuDHD を (ω₁, ω₂, ω₃, σ) の4パラメータで特徴づける仮説。
- ADHD: ω_state の制御不安定性 (dω/dt の分散が大)
- ASD: ω_trait 自体の偏差 (特定 ω_k の固着)

### 6.6 確定/仮説の区分 (v3.0 統合)

| # | 内容 | 状態 | 根拠 |
| --- | --- | --- | --- |
| T1 | ω-不変性 | 確定 | 解析証明 + 数値検証 |
| T2 | W-C 分解 | 確定 | Helmholtz 分解 |
| T3 | Q 双対性 | 確定 | 数値検証 10⁻⁸ |
| T4 | 動的 Q 双対性 | 確定 | 定義的恒等式 (V 非依存) |
| T4' | trade-off 恒等式 | 確定 | g^(c)·g^{(c,F)} = (σ⁴/4)I_F — 定義的恒等式 |
| T5 | n 次元一般化 | 確定 | Schur 分解 |
| T6 | c-双対性 | 推定 55% | Amari と構造的同型 |
| T7 | Current-Density 双対性 | **確定 90%** | 部分積分証明 + 7ポテンシャル数値検証 |
| T8 | c-Pythagoras | **確信 75%** | dually flat 一般化 → 射影定理も一般 |
| T9 | 密度-循環独立性定理 | **確信 90%** | T7 + 部分積分証明 + 7ポテンシャル検証 |
| **T10** | **Dually flat ⟺ 等方回転** | **確信 95%** | **解析証明 + 非OU 3種×2条件 (v3.0)** |
| H1 | K₆ 二重テンソル場 | 確定 | axiom_hierarchy 突合せ |
| H2 | Helmholtz Γ⊣Q 接続 | 確定 | axiom_hierarchy L28 |
| **Q1** | **Q = 循環 ≠ 因果** | **確信 92%** | **Granger 実験 + /kat (2026-03-15)** |
| **Q2** | **Helmholtz 関手 Faithful/¬Full** | **推定 82%** | **F₁F₂ 構成 + /kat (2026-03-15)** |
| H3 | (s,π,ω) = 3回転面 | 仮説 | 構造的類似 |
| H4 | ペアリング | **仮説 (全候補未確定)** | A棄却/B保留/C循環/D棄却、H1検証待ち |
| H5 | Hyphē τ-ω | 仮説 | 理論的導出のみ |
| H6 | Kalon ωσ²=2 | 仮説 | 推定 |
| H7 | AuDHD (ω₁,...,ω_K,V,σ) | **仮説 70%** | T10帰結 + §6.7 + 非ガウス増幅 + §6.8.5 Q1-Q4 + §6.8.8 T12安定性 + §6.8.9 T13非線形安定性 |
| H8 | 循環空間 dually flat (一般) | **確定 85%** | ∂_ω log\|j\| = 1/ω の V 非依存性 |
| H9 | 密度-循環 統合 Pythagoras | **推定 65%** | T7一般化 + H8一般化で直積 × dually flat |
| **C2** | **ω ↔ 認知スタイル** | **推定 86%** | **7文献 + P4数値 + kI対応 + TUR (v3.0)** |

### 6.7 異方回転の precision 的意味 — AuDHD の情報幾何 (v3.1 追加)

> T10 (Dually flat ⟺ 等方回転) の認知科学的含意を定式化。
> §6.5 の H7 (AuDHD パラメータ化) を定量的に展開。

#### 6.7.1 T10 が壊すもの: 信念-認知結合

T10 の核心は**等方回転だけが信念と認知の独立性を保証する**こと:

```text
等方 (ω_k = ω ∀k):
  g^{(c,F)} = 1/ω²  (V 非依存)
  → 「どう考えるか」が「何を信じるか」に依存しない
  → 認知プロセスは信念内容から分離される
  → dually flat → IS divergence が成立 → 循環の最適射影 (T8) が使える

異方 (ω_k ≠ ω_l):
  g^{(c,F)}_{kk} = E[U_k(x)²] / ω_k²  (V 依存)
  → 「どう考えるか」が「何を信じるか」に依存してしまう
  → 認知プロセスと信念内容が結合する
  → dually flat でない → IS divergence も Pythagoras も崩壊
```

ここで **U_k(x)** は「信念地形 V における方向 k の相対的勾配寄与率」:

```text
  U_k(x) = ω_k |(∇V)_{k-pair}|² / Σ_l ω_l² |(∇V)_{l-pair}|²
```

U_k(x) の認知的意味: 位置 x (= 現在の信念状態) において、回転面 k がどれだけ
総循環に寄与しているかの**相対的重み**。等方なら全面で均等 (= x 非依存)。

#### 6.7.2 precision の非一様性の定式化

FEP の precision (精度加重) π は信号の信頼度を示すゲイン:

```text
  π_k := 1 / g^{(c,F)}_{kk} = ω_k² / E[U_k²]
```

**等方 (ωk = ω)**:
  - π = ω² (全方向で均一)
  - precision は信念内容 V に無関係
  - S-III Akribeia の理想: 精度が内容バイアスなく設定される

**異方 (ωk ≠ ωl)**:
  - π_k = ω_k² / E[U_k²] (方向ごとに異なる)
  - precision が信念地形 V に依存 → **精度の content-dependent bias**
  - S-III の違反: 精度設定が信念内容に汚染される

この非一様性の度合いを **異方度** (anisotropy index) α_anis で定量化:

```text
  α_anis := max_k(π_k) / min_k(π_k)

  α_anis = 1     → 完全等方 (理想)
  α_anis > 1     → 異方 (信念-認知結合あり)
  α_anis >> 1    → 強異方 (特定領域で認知が固着 or 過敏)
```

**経験的裏付け (Hyphē Exp-1/1b, 2026-03-15)**:

Gemini 3072d embedding (N=50K+) に対する PCA 診断 + ZCA whitening で直接検証:

| 条件 | cos_sim mean | D_eff | precision var |
|:-----|:-----------:|:-----:|:-------------:|
| 原空間 (異方) | 0.77 | 183 (6%) | 0.042 |
| ZCA whitening (等方化) | -0.001 | 893 (29%) | **0.021** (半減) |

→ whitening で α_anis ≈ 1 に近づけると precision variance が **半減**。
→ **異方性が precision の弁別力を水増ししていた** (H4: Anisotropy-Amplified Discrimination)。
→ T10 の逆面: 等方化 → ω-V 分離 → cos_sim ベースの precision carrier が消失。
→ 「偏り方に情報が反映される」= 異方性は noise ではなく signal。
→ 詳細: `rom_2026-03-15_embedding_anisotropy_diagnosis.md`

#### 6.7.3 非ガウス信念による増幅メカニズム

§8.18.2 の数値結果 (MCMC N=80K) は決定的な知見を与える:

| 信念構造 | 増幅率 (vs OU) | 認知的解釈 |
|:---------|:-------------:|:-----------|
| OU (ガウス: 単峰信念) | 1.00x | 信念は連続的グラデーション → 異方性の V 依存は弱い |
| Duffing (弱非線形) | 2.00-2.38x | 信念の歪み → 異方性が増幅 |
| DW barrier=2 (双峰) | **4.40x** | 二項対立信念 → V 依存性が急増 |
| DW barrier=5 (強双峰) | **6.14x** | 固い二項対立 → **認知の固着が激化** |

**増幅メカニズムの核心**: 双峰ポテンシャル (二項対立的信念) では U_k(x) が双峰化する。
- 「谷底」(∇V ≈ 0) → U_k ≈ 0: 認知方向 k が循環に寄与しない (「停滞」)
- 「壁」(|∇V| >> 0) → U_k ≈ 1: 方向 k が循環を支配 (「固着」)

→ U_k が 0 と 1 の間で大きく振動 → E[U_k²] >> E[U_k]² → g^{(c,F)} のばらつきが拡大
→ **信念の「壁」が高いほど、認知速度の非対称性が信念内容に結合する**

#### 6.7.4 AuDHD パラメータ化の更新

H7 を §6.7.1-6.7.3 の知見で更新:

```text
AuDHD を (ω₁, ..., ω_K, V, σ) で特徴づける (K = 回転面の数):

ADHD 成分 (動的異方性):
  dω_k/dt の分散が大 → ω_k が時刻ごとに不安定に変動
  → α_anis(t) が時間的に変動し予測不能な精度変化
  → S-III 違反: precision が安定して設定できない
  → §5.8 の coupling ≠ 0 が発動 (異方 + ω変動 → σ̇_cp = 4-19%)
  → housekeeping EP のゆらぎ = 「維持コストの不安定性」

ASD 成分 (静的異方性):
  ω_k 自体に永続的偏差 → 特定回転面で α_anis >> 1
  → 特定の信念領域 V_k で precision が異常に高い (特殊的関心) or 低い (無関心)
  → V 依存性 (§6.7.3) により、信念の壁 (barrier) が高い領域で効果が増幅
  → S-III 違反: 精度のチャネル間不均衡が恒常的

AuDHD の併存 = 動的 + 静的異方性:
  ω_k 自体が偏り (ASD) + さらに dω_k/dt が不安定 (ADHD)
  → 静的異方性を動的変動が攪乱 → α_anis(t) が大かつ不安定
  → 最も困難: 精度の偏りが予測不能に変動する
```

**予測 P5 (新規)**: AuDHD 群の fMRI time-series から推定された ω_k の
  (i) 面間分散 Var_k(ω_k) (静的異方度) と
  (ii) 時間的分散 Var_t(ω_k(t)) (動的不安定性) が、
  定型群より有意に大きい。
  両者の積 Var_k × Var_t が AuDHD の重症度スコアと正相関する。

**H7 確信度更新**: [仮説] → [仮説 55%]

微調整の理由:
- (+5%) T10 の数学的帰結 (等方 ⟺ dually flat) から異方=精度偏りの論理が厳密に導出された
- (+) 非ガウス増幅メカニズムにより、二項対立的信念での異方性激化が定量的に示された
- (-) fMRI データでの直接検証なし
- (-) ω_k の面間差が AuDHD 特異か一般的な個人差かの弁別ができていない
- (-) 信念構造 V(x) と ω_k の因果方向 → §6.8.5 Q1 で双方向フィードバックと判明 (+5%)
- (+) §6.8.5 Q2: 臨界 barrier なし (漸進的) → DW 非ガウス性自体が主因 (+5%)
- (+) §6.8.5 Q3: DW 増幅は次元にロバスト (α_DW≈100, 1/√d) (+)
- (+) §6.8.5 Q4: fMRI 検証プロトコル案 (Var_t(α) 群間比較) (+)

#### 6.7.5 Hóros Anti-Timidity / S-III との接続 [仮説 35%]

Hóros の Anti-Timidity パターン (T-1〜T-6) を 6修飾座標 × 回転面で再記述する仮説。

**座標レベルの同定** (episteme-entity-map の 6修飾座標):

> [!WARNING]
> 以下の分析は **候補 A (次元ペアリング)** に基づく。§4.4 で候補 A は棄却済み — 候補 D も「レベル混同」により棄却。
> **全候補が未確定** (v3.4 時点)。回転面のペアリングは H1 (§4.3 仮説) の検証待ち。
> **座標レベルの同定** (各 T パターンが関与する修飾座標の特定) は回転面ペアリングに依存しないため有効。
> 回転面の割当 (Π₁/Π₂/Π₃ への座標の帰属) のみが再分析対象。

> [!TIP]
> **有効な分析と無効な分析の区別**:
> - ✅ 有効: 各 T パターンが関与する **座標の特定** (例: T-1 は Temporality × Valence)。座標の特定は Q の Schur 分解の結果ではなく、Anti-Timidity パターンの認知的意味から導出されている。
> - ❌ 無効: 座標が **どの回転面 (Π₁/Π₂/Π₃) に属するか** の割当。これは §4.4 の回転面ペアリングに依存しており、全候補未確定のため仮置き。
> - 結論: 下表の「関与する座標」「認知的パターン」列は有効。「回転面 (候補A)」列は仮置き。

| Anti-Timidity | 認知的パターン | 関与する座標 | 回転面 (候補A) | 機構 |
|:-------------|:-------------|:-----------|:-------------|:-----|
| T-1 /bye 提案禁止 | 終了への恐怖 | **Temporality** (未来) × **Valence** (負) | Π₃ | 「終了」面の ω → 0 (負の未来の回避) |
| T-2 時間見積禁止 | 制御の錯覚 | **Temporality** (未来) × **Precision** (不確実) | Π₃→Π₂ coupling | 不確実な未来を精度なく予測 = 面間干渉 |
| T-3 先延ばし禁止 | 開始回避 | **Function** (Exploit固着) × **Temporality** (未来回避) | Π₁→Π₃ coupling | 行動面と時間面の干渉 → barrier で U_k ≈ 0 |
| T-4 保守的選択禁止 | 探索の抑制 | **Function** (Explore→Exploit) × **Value** (内部固着) | **Π₁** | 探索面の ω 均一化 = Exploit 一辺倒 |
| T-5 体調言及禁止 | 誤帰属 | **Valence** (負: 心配) × **Value** (外部: Creator) | Π₃→Π₁ coupling | 社交的 ω を認知的 ω と混同 |
| T-6 尻込み禁止 | 規模の恐怖 | **Scale** (Macro) × **Valence** (負) | **Π₂** or Π₃ | Scale 面で barrier が高く ω → 0 |

**構造的発見**: 候補 A ペアリング (Π₁=Value×Function, Π₂=Precision×Scale, Π₃=Valence×Temporality) で分析すると:

```text
単一面パターン (ω_k の抑制/偏倚):
  T-1: Π₃ 面の ω 抑制 (Valence×Temporality — 負の未来回避)
  T-4: Π₁ 面の ω 均一化 (Value×Function — 探索抑制)
  T-6: Π₂ 面の ω 抑制 (Precision×Scale — 規模恐怖)

面間 coupling パターン (σ̇_cp ≠ 0 の発現):
  T-2: Π₂→Π₃ coupling (Precision と Temporality の干渉)
  T-3: Π₁→Π₃ coupling (Function と Temporality の干渉)
  T-5: Π₃→Π₁ coupling (Valence と Value の干渉)
```

**§5.8 coupling 数値との接続**:

```text
§5.8 結果: 等方 OU → coupling = 0 / 異方 OU + ω変動 → coupling = 4-19%
    σ̇_cp ≤ 0 (全実験で確認) = 干渉は常に EP を減らす

Anti-Timidity 解釈:
  単一面パターン (T-1,4,6) → ω_k の抑制 → α_anis 増大 → 精度偏り
  面間 coupling パターン (T-2,3,5) → 異方性 + ω変動 → σ̇_cp < 0
    → 「干渉は EP を減らす」= 認知コストを下げてしまう
    → 省エネだが低品質 — 安易な道を選ぶ認知メカニズム
```

**CCL 動詞との萌芽的対応**:

| 回転面 | 座標ペア | 候補 CCL 動詞 | Anti-Timidity |
|:------|:--------|:------------|:-------------|
| Π₁ | Value × Function | /ene (実行), /bou (意志) | T-4 (探索抑制) |
| Π₂ | Precision × Scale | /ops (全体俯瞰), /lys (局所分析) | T-6 (規模恐怖) |
| Π₃ | Valence × Temporality | /prm (予測), /ath (回顧) | T-1 (終了恐怖) |

[仮説 35%] — v3.0 の [30%] から +5%。座標レベルでの同定により「単一面 vs 面間 coupling」の
構造的区別が見え、§5.8 の coupling 数値結果と接続できたため。
ただし回転面ペアリングは **全候補が未確定** (§4.4 v1.1) であり、上表の「回転面 (候補A)」列と
「構造的発見」の Π₁/Π₂/Π₃ 割当は **仮置き**。座標レベル (各 T パターンが関与する修飾座標) のみ有効。
H1 (§4.3) 検証後に回転面の再割当が必要。

[SOURCE: circulation_theorem.md T10, §4.3, §4.4 v1.1, §5.8, episteme-entity-map, horos-N07/N08]

---

## §8 参照

- [problem_E_m_connection.md](../category/problem_E_m_connection.md) §8.0-8.19 — 全導出過程
- [problem_E_m_connection.md](../category/problem_E_m_connection.md) §8.16-8.19.2 — 認知科学接続 (ω↔認知スタイル, C2: 86%) + 実験的証拠体系 + PMEM→kI→OU統一 + TUR接続
- [axiom_hierarchy.md](../axiom_hierarchy.md) §定理⁴ — X-series, K₆ 完全性
- Amari (1985): α-接続と双対構造の基本理論
- Amari & Nagaoka (2000): Methods of Information Geometry
- Kolchinsky, Dechant, Yoshimura, Ito (2022): arXiv:2206.14599 — EP の情報幾何
- Dechant, Sasa, Ito (2021): arXiv:2109.12817 — EP の幾何的分解
- Dechant, Sasa, Ito (2022): PRE 106, 024125 — 3成分分解
- Lacerda, Bettmann, Goold (2025): arXiv:2501.08858 — 量子 NESS の情報幾何
- Ishihara & Shimazaki (2025): Nature Comm. (arXiv:2502.15440) — state-space kinetic Ising, entropy flow
- Mézard & Sakellariou (2011): J. Stat. Mech. (arXiv:1103.3433) — exact mean-field inference for asymmetric kinetic Ising
- Chen et al. (2025): arXiv:2501.19106 — FIM stiff/sloppy と認知個人差
- Nartallo-Kaluarachchi et al. (2025): Physics Reports — 脳の time-irreversibility レビュー
- Cruzat et al. (2023): J. Neurosci. — Alzheimer と irreversibility
- Friston (2019): A free energy principle for a particular physics
- Barato & Seifert (2015): TUR の基本定理
- rom_2026-03-13_circulation_complete_v47.md — v4.7 ROM
- rom_2026-03-14_xseries_dual_tensor.md — v4.9 ROM
- rom_2026-03-14_kolchinsky_correspondence.md — Kolchinsky 対応 ROM

---

### §6.8 数値検証 — 異方性の定量的構造

**4D (2回転面) + 6D (3回転面) Euler-Maruyama シミュレーション**による定量的検証。
ソース: `sim_anisotropic_ou_4d.py` (v2), `sim_anisotropic_ou_6d.py`

#### §6.8.1 4D 実験結果

| 実験 | 条件 | α_anis | EP_total | EP面間相関 |
|:-----|:-----|:------:|:--------:|:---------:|
| Exp1 | 等方 (ω₁=ω₂=1.0) | 1.024 | 1.966 | +0.18 |
| Exp2 | Π₁抑制 (ω₁=0.2) | 1.171 | 1.035 | +0.24 |
| Exp3 | 強抑制 (ω₁=0.05) | 1.285 | — | +0.24 |
| Exp4 | 面間干渉 (ω反相関振動) | 1.036 | 2.241 | **-0.25** |
| Exp5 | AuDHD (静的+動的) | 1.008 | 1.086 | +0.23 |
| Exp6 | **DW+異方** (ω₁=0.5,ω₂=1.5) | **8.246** | 5.079 | +0.08 |
| Exp7 | DW+等方 | 6.422 | 12.505 | +0.14 |

#### §6.8.2 6D 実験結果

6D = HGK 3回転面体系 (§4.4 候補A — **仮置き**、全候補未確定):
- Π₁: Value × Function (ω₁)
- Π₂: Precision × Scale (ω₂)
- Π₃: Valence × Temporality (ω₃)

| 実験 | 条件 | α_static | α_mean±std | EP_total | Π₁-Π₃相関 |
|:-----|:-----|:--------:|:----------:|:--------:|:---------:|
| E1 | 等方 | 1.12 | 6.3±39 | 3.20 | +0.30 |
| E2 | Π₁抑制 T-4 (ω₁=0.2) | **5.50** | 47±293 | 2.17 | +0.13 |
| E3 | Π₃抑制 T-1 (ω₃=0.2) | **4.79** | 41±287 | 2.15 | +0.25 |
| E4 | Π₁→Π₃ coupling T-3 | 1.78 | 6.7±39 | 2.69 | **+0.36** |
| E5 | AuDHD 3面動的 | 4.30 | 50±**1220** | 3.63 | +0.10 |
| E6 | **DW(Π₃)+異方** | **11.75** | 99±1012 | 27.41 | -0.01 |
| E7 | DW(Π₃)+等方 | 9.25 | 21±217 | 13.82 | +0.04 |

#### §6.8.3 核心的発見

**発見 1: 信念構造 V(x) が異方性の主因** [確信 85%]

$$\text{DW 増幅率} = \frac{\alpha_{\text{DW+異方}}}{\alpha_{\text{OU+異方}}} = \begin{cases} 7.04\times & (4D) \\ 2.13\times & (6D) \end{cases}$$

- OU (ガウス信念) では ω比 5:1 でも α ≈ 1.2–5.5 にとどまる
- DW (双峰信念) は等方ωでも α = 6.4–9.3 を生成
- **V(x) の非ガウス性が ω の異方性を増幅する**
- 認知的意味: 二項対立的信念 (all-or-nothing) が認知速度の偏りを劇的に拡大
- 4D→6D で増幅率が低下 (7x→2x) → 局所的に「希釈効果」が見える
- ★ しかし §6.8.5 Q3 (d=4-16 スキャン) で **α_DW ≈ 100 は次元にほぼ不変**。増幅率の低下は α_OU 基準の変動が主因
- 希釈効果の修正: DW 増幅自体はロバスト、増幅「率」のみ ∝ 1/√d で緩やかに減衰 (R²=0.48)

**発見 2: 面間 coupling は EP 正相関として顕在化** [推定 70%]

- T-3 パターン (Function↓→Temporality↓): Π₁-Π₃ EP 相関 = **+0.36** (E4)
- 等方基準 (E1): Π₁-Π₃ EP 相関 = +0.30
- DW+異方 (E6): Π₁-Π₃ EP 相関 = **−0.01** (coupling 消失)
- 4D 面間干渉 (Exp4): EP 相関 = **−0.25** (唯一の負値)
- 解釈: ω反相関振動は面間 EP を負に結合させる = **省エネ認知経路** (§5.8 σ̇_cp ≤ 0 と整合)
- DW ポテンシャルが coupling を破壊する → 硬い信念は面間相互作用を遮断

**発見 3: AuDHD は「瞬時変動」で特徴づけられる** [仮説 40%]

- E5 AuDHD: α_static = 4.30 (中程度) だが α_std = **1220** (巨大)
- 4D AuDHD (Exp5): α_anis = 1.008 (等方より低い = 時間平均で打消し)
- **修正 P5**: AuDHD の指標は平均 α ではなく **分散** Var_t(α_anis(t))
  - ADHD: 高 Var_t → 瞬間的な precision 変動
  - ASD: 高 α_static → 持続的な precision 偏り
  - AuDHD: 両方 → 静的偏差 + 巨大変動

$$\text{AuDHD severity} \propto \alpha_{\text{static}} \cdot \text{Var}_t(\alpha(t))$$

#### §6.8.4 H7 仮説の修正

旧 H7 (v3.1): ω_k の偏り → precision 偏り → AuDHD

**新 H7 (v3.2)**: V(x) の非ガウス性が ω_k の微小な偏りを増幅する

- ω の偏りだけでは α ≈ 1–5 (弱い異方性)
- V(x) がガウスから乖離すると α が 2–7 倍に増幅
- **AuDHD の本質は「硬い信念 × 偏った認知速度」の相乗効果**
- 確信度: 45% → 50% (ω単独説は棄却。V×ω 相互作用説が数値的に支持)

| パラメータ | 認知的意味 | 旧仮説 | 新仮説 (v3.2) |
|:----------|:----------|:------|:-------------|
| ω_k | 認知速度 | 主因 | 種 (seed) |
| V(x) | 信念構造 | 背景 | **増幅器 (amplifier)** |
| α_anis | precision 偏り | ω由来 | V×ω 相互作用 |
| Var_t(α) | 瞬時変動 | 未定義 | **AuDHD 指標** |

#### §6.8.5 開問題への回答

ソース: `sim_vw_causality.py`, `sim_dw_barrier_sweep.py`, `sim_dimension_scaling.py`

**Q1: V→ω の因果方向** [推定 65%: 双方向]

6D DW で3つの因果モデルを Granger 検定:

| モデル | F(曲率→ω) | F(ω→曲率) | 判定 |
|:-------|:---------:|:---------:|:-----|
| A: V→ω (曲率がωを変調) | **9.96** | **25.43** | 双方向 |
| B: ω→V (ωがbarrierを変調) | — | **8.86** | ω→V |
| C: 独立基準 | ≈0 | ≈0 | 因果なし ✓ |

- **結論**: V と ω は **フィードバックループ** を形成する
- V→ω 方向でも逆因果 (ω→曲率) が強く出る → 信念と認知速度は相互制約
- 認知的意味: 硬い信念 (高曲率) が認知速度を上げ、速い認知が信念を硬化させる正のフィードバック

**Q2: DW barrier の臨界値** [確信 80%: 臨界点なし]

barrier b = 0.1–8.0 スイープ (6D, ω=(0.5, 1.0, 1.5)):

| b | α_static (異方) | α_static (等方) | 増幅率 |
|:-:|:--------------:|:--------------:|:-----:|
| 0.1 | 7.6 | 1.2 | 6.1x |
| 0.5 | 15.7 | 2.2 | 7.3x |
| 0.8 | 26.4 | 2.9 | **8.9x** |
| 3.0 | 105 | 12.1 | 8.7x |
| 8.0 | 300 | 34.7 | 8.7x |

- **結論**: 急激な臨界遷移は**存在しない**。α は b に対して漸進的に増加
- 最大ステップ増加率 = 1.68x (b=0.5→0.8) — 「相転移」的な急変なし
- **DW 増幅率** (異方/等方) は b ≈ 0.8 で ≈ 8.7–8.9 に収束し、b > 1 では一定
- 認知的意味: 信念の非ガウス性自体が増幅の原因であり、barrier の「高さ」は二次的

**Q3: 6D→∞D のスケーリング** [確信 90%: **解析的に次元不変を証明**]

d = 4, 6, 8, 10, 12, 16 で DW 増幅率を測定:

| d | 面数 | α_OU | α_DW | 増幅率 |
|:-:|:---:|:----:|:----:|:-----:|
| 4 | 2 | 7.9 | 104 | **13.2x** |
| 6 | 3 | 8.2 | 105 | **12.8x** |
| 8 | 4 | 7.0 | 104 | **14.8x** |
| 10 | 5 | 9.2 | 100 | **10.8x** |
| 12 | 6 | 9.0 | 97 | **10.7x** |
| 16 | 8 | 12.1 | 113 | **9.3x** |

旧解釈: 増幅率 ∝ 1/√d (R²=0.48, 弱いフィット)

**新解釈 (解析的証明)**: α_DW 自体が d に依存しない（→ §6.8.7 T11）。「増幅率の見かけの次元依存性」は α_OU 基準の有限サンプリング変動が原因:

$$\alpha_{\text{DW}} = \frac{\omega_{\text{DW}}^2}{\omega_{\min}^2} \cdot \frac{\langle|\nabla V_{\text{DW}}|^2\rangle_{\text{st}}}{\langle|\nabla V_{\text{OU}}|^2\rangle_{\text{st}}} = \frac{(1.5)^2}{(0.5)^2} \cdot \frac{11.59}{1.00} = \mathbf{104.3}$$

- 解析予測 **104.3** vs シミュレーション平均 **103.7** (6次元値) → **一致度 99.4%**
- **d は式に一切現れない** → 次元不変性は解析的に証明された
- α_OU の解析予測 = (ω_max/ω_min)² = 9.0、シミュレーション 7.0–12.1 (平均 8.9)
- **真の増幅率** = 104.3/9.0 = **11.6x** (次元に依存しない)

**Q4: fMRI 検証可能性** [仮説 35%]

以下の検証プロトコル案を提案:

1. **α_anis の検証**: resting-state fMRI で BOLD 時系列の回転面分解を行い、面間 EP 比率を測定。AuDHD 群 vs 定型群で Var_t(α) を比較。
2. **検出可能性**: Nartallo-Kaluarachchi et al. (2025) の time-irreversibility 手法が直接適用可能。Cruzat et al. (2023) の Alzheimer 研究で EP の神経相関が確認済み。
3. **予測**: AuDHD 群で Var_t(α) が有意に高い (静的偏差 + 高変動)。ASD のみの群は α_static が高いが Var_t は低い。
4. **限界**: EP の面分解が脳の ROI にどう対応するかは未定 (理論的対応が必要)。

#### §6.8.6 H7 仮説の最終更新

旧 H7 (v3.2): V(x) の非ガウス性が ω の微小偏りを増幅する

**新 H7 (v3.4)**: V(x) と ω は正のフィードバックループを形成し、非ガウス性が増幅のドライバー

| 要素 | 旧仮説 (v3.2) | 新仮説 (v3.4) | 根拠 |
|:-----|:-------------|:-------------|:-----|
| V→ω 因果 | 未定義 | **双方向フィードバック** | Q1: Granger F 双方向有意 |
| 臨界 barrier | 未定義 | **存在しない** (漸進的) | Q2: 最大ステップ 1.68x |
| 次元スケーリング | 「希釈効果」 | **次元不変** (T11 解析証明) | Q3: α_pred=104.3 vs sim=103.7 |
| fMRI 検証 | 未定義 | **Var_t(α) compare** | Q4: Nartallo-K. 手法 |

確信度: 50% → **60%** (4開問題のうち3つに実験的回答 + Q3 解析証明)

#### §6.8.7 T11: DW 異方性の次元不変性定理

**定理 T11** (DW 次元不変性). d次元系 (d ∈ 2ℕ) で d/2 個の回転面のうち1面が双峰ポテンシャル V_DW(x₁) = b(x₁²-1)²、残りが OU ポテンシャル V_OU(x) = (a/2)|x|² を持つとき、異方性比 α_static は次元 d に依存しない:

$$\alpha_{\text{static}} = \frac{\omega_{\text{DW}}^2 \cdot \langle|\nabla V_{\text{DW}}|^2\rangle_{p^*}}{\omega_{\min}^2 \cdot \langle|\nabla V_{\text{OU}}|^2\rangle_{p^*}}$$

ここで p* は各面の定常分布。

*証明*.

各面は独立な2D サブシステムなので定常分布は因子化する: p*(x₁,...,x_d) = ∏_k p*_k(x_{2k-1}, x_{2k})。

EP_k = ω_k² · ⟨|∇V_k|²⟩_{p*_k} は面 k の EP。α = max_k(EP_k)/min_k(EP_k)。

**OU 面** (ポテンシャル (a/2)(x₁²+x₂²)):
- ∇V = a(x₁, x₂), |∇V|² = a²(x₁²+x₂²)
- 定常分布 p* ∝ exp(-a|x|²/σ²) → ⟨x_i²⟩ = σ²/(2a)
- ⟨|∇V|²⟩ = a² · 2σ²/(2a) = **a·σ²**

**DW 面** (x₁: DW b(x₁²-1)², x₂: OU (a/2)x₂²):
- ∂V/∂x₁ = 4b·x₁(x₁²-1), ∂V/∂x₂ = a·x₂
- p*₁(x₁) ∝ exp(-2b(x₁²-1)²/σ²)
- ⟨|∂V/∂x₁|²⟩ = 16b² ⟨x₁²(x₁²-1)²⟩_{p*₁} =: **G(b,σ)** (定数、d に依存しない)
- ⟨|∂V/∂x₂|²⟩ = a·σ²/2
- ⟨|∇V_DW|²⟩ = **G(b,σ) + a·σ²/2**

したがって:

$$\alpha = \frac{\omega_{\text{DW}}^2 \cdot (G(b,\sigma) + a\sigma^2/2)}{\omega_{\min}^2 \cdot a\sigma^2}$$

右辺に d は現れない。■

**数値検証** (b=3, σ=1, a=1, ω_DW=1.5, ω_min=0.5):
- G(3,1) = 11.09 (数値積分)
- α_pred = 9.0 × (11.09+0.50)/1.00 = **104.3**
- α_sim 平均 (d=4–16): **103.7** → 一致度 **99.4%**

**系 C4** (増幅率の次元不変性). 真の DW 増幅率 α_DW/α_OU も次元に依存しない:

$$\text{増幅率} = \frac{G(b,\sigma) + a\sigma^2/2}{a\sigma^2} = \frac{11.59}{1.00} = \mathbf{11.6\times}$$

**系 C5** (barrier 依存性). G(b,σ) の barrier 依存性は以下の通り:

| b | G(b,1) | α_pred |
|:-:|:------:|:------:|
| 0.1 | 0.47 | 8.7 |
| 0.5 | 1.50 | 18.0 |
| 1.0 | 3.11 | 32.5 |
| 3.0 | 11.09 | 104.3 |
| 5.0 | 19.18 | 177.1 |
| 8.0 | 31.21 | 285.4 |

認知的意味: α は b に対して (近似的に) 線形に増加する。barrier が高くなるほど信念の分極が precision 偏りを強める。次元に無関係 — これは HGK の座標数が増えても信念構造の影響力が希釈されないことを保証する。

#### §6.8.8 T12: V↔ω フィードバック安定性定理

ソース: `sim_vw_stability_v2.py`

**動機**: Q1 で V↔ω の双方向フィードバックを確認したが、この正のフィードバックが安定か不安定か (ロックインするか) は未解明だった。

**モデル**: barrier b と angular velocity ω の線形結合力学系:

$$\dot{b} = \gamma_b \cdot (b_0 + \beta(\omega - \omega_0) - b)$$
$$\dot{\omega} = \gamma_\omega \cdot (\omega_0 + \alpha(b - b_0) - \omega)$$

ここで:
- α = V→ω 結合: barrier 1単位↑ → ω が α 増加 (硬い信念 → 速い認知)
- β = ω→V 結合: ω 1単位↑ → barrier が β 増加 (速い認知 → 硬い信念)

**定理 T12** (V↔ω フィードバック安定性). αβ ≠ 1 のとき唯一の固定点 (b₀, ω₀) が存在し:

$$\alpha\beta < 1 \implies \text{大域的漸近安定 (stable node)}$$
$$\alpha\beta > 1 \implies \text{鞍点不安定 (saddle)}$$

*証明*.

ヤコビアン:

$$J = \begin{pmatrix} -\gamma_b & \gamma_b \beta \\ \gamma_\omega \alpha & -\gamma_\omega \end{pmatrix}$$

- tr(J) = −(γ_b + γ_ω) < 0 (常に成立)
- det(J) = γ_b·γ_ω·(1 − αβ)
- αβ < 1 ⟹ det > 0 かつ tr < 0 ⟹ 安定
- αβ > 1 ⟹ det < 0 ⟹ 鞍点

γ_b = γ_ω = γ のとき固有値: λ± = −γ ± γ√(αβ)。緩和時定数: τ = 1/(γ(1−√(αβ)))。■

**数値検証** (認知プロファイル):

| プロファイル | α | β | αβ | 安定性 | τ | 認知的特徴 |
|:------------|:--:|:--:|:---:|:------:|:---:|:----------|
| 定型発達 | 0.1 | 0.1 | 0.01 | stable | 1.1 | 弱い結合。摂動は即減衰 |
| 軽度 ASD | 0.5 | 0.2 | 0.10 | stable | 1.5 | V→ω 優位。信念が認知を支配 |
| 軽度 ADHD | 0.2 | 0.5 | 0.10 | stable | 1.5 | ω→V 優位。認知が信念を変形 |
| AuDHD | 0.7 | 0.7 | 0.49 | stable | 3.3 | 双方向中程度 |
| 重度 AuDHD | 0.9 | 0.9 | 0.81 | stable | **10.0** | 臨界近傍。揺らぎ大 |
| ロックイン | 1.2 | 1.0 | 1.20 | saddle | ∞ | 正フィードバック発散 |

**系 C6** (AuDHD の位相空間特性). 重度 AuDHD (αβ ≈ 0.81) では τ ≈ 10 (定型の9倍)。
- 摂動の減衰が遅い → 外因で容易に状態がシフトする
- Var_t(α) ∝ αβ/(1−αβ) → Q1 の「瞬時変動が大きい」(α_std=1220) と整合
- 「良い日と悪い日」= 臨界近傍での大きな揺らぎの反映

**系 C7** (治療戦略). αβ を 1 未満に保つことが治療目標:
- **α の低減 (CBT)**: 信念の硬さ → 認知速度の結合を弱める (信念の柔軟化)
- **β の低減 (薬物療法)**: 認知速度 → 信念硬化の結合を弱める (例: methylphenidate による ω の安定化)
- **両方の低減**: AuDHD 最適戦略。αβ の乗算構造により、両方を少しずつ下げることが最も効率的

認知的意味: V↔ω フィードバックの安定性は **結合積 αβ** という単一の無次元量で完全に決定される。これは AuDHD の重症度の自然な尺度であり、αβ = 1 が「代償可能」と「ロックイン」の臨界境界を定める。

#### §6.8.9 T13: 非線形 V↔ω 安定性定理 (大域的安定性 + ピッチフォーク分岐)

ソース: `sim_nonlinear_stability.py`

**動機**: T12 は線形モデルだった。現実の認知結合は飽和する (信念が無限に硬くなることはない、認知速度にも上限がある)。非線形結合を導入し、大域的安定性と分岐構造を厳密に解析する。

**モデル**: T12 の線形結合を tanh 飽和に置換 (u = b − b₀, v = ω − ω₀ に中心化):

$$\dot{u} = \gamma(-u + \beta \cdot \tanh(v))$$
$$\dot{v} = \gamma(-v + \alpha \cdot \tanh(u))$$

飽和の認知的意味: |tanh(x)| < |x| (x ≠ 0) より、非線形結合は線形結合より常に弱い。信念の硬さにも認知速度にも天井がある。

**定理 T13** (非線形 V↔ω 安定性 + ピッチフォーク分岐).

**(a) 閉軌道の不存在**: 全ての αβ ≥ 0 に対して、系は閉軌道 (リミットサイクル) を持たない。

**(b) 大域的漸近安定性**: αβ < 1 のとき、(0,0) は唯一の固定点であり、大域的漸近安定。

**(c) 超臨界ピッチフォーク分岐**: αβ = 1 で分岐。αβ > 1 のとき (0,0) は鞍点化し、2つの新しい安定ノード ±(u\*, v\*) が出現する。

*証明*.

**(a)** Bendixson の否定判定法。ベクトル場 f = (f₁, f₂) の発散:

$$\text{div}(f) = \frac{\partial f_1}{\partial u} + \frac{\partial f_2}{\partial v} = -\gamma + (-\gamma) = -2\gamma < 0$$

単連結領域 ℝ² 上で div(f) が常に負 → 閉軌道は存在しない。■

**(b)** 3段階:

(i) **縮小写像**: 固定点は u = β·tanh(α·tanh(u)) の解。φ(u) ≡ β·tanh(α·tanh(u)) とおく。

$$\phi'(u) = \alpha\beta \cdot \text{sech}^2(\alpha \cdot \tanh(u)) \cdot \text{sech}^2(u)$$

sech²(x) ≤ 1 かつ sech²(x) < 1 (x ≠ 0) より、αβ < 1 のとき sup|φ'| ≤ αβ < 1。Banach の縮小写像定理により唯一の固定点 u = 0。

(ii) **有界性**: |tanh(x)| ≤ 1 より |du/dt| ≤ γ(|u| + β), |dv/dt| ≤ γ(|v| + α)。全軌道は有界。

(iii) **大域的安定性**: (0,0) は唯一の平衡点、局所安定 (T12 より)、閉軌道なし (a)、軌道は有界。Poincaré-Bendixson 定理により、全軌道は (0,0) に収束する。■

**(c)** φ'(0) = αβ。αβ > 1 のとき φ'(0) > 1 だが φ(u) → β (u → ∞) より φ(u) < u が大きな u で成立。中間値の定理から ±u\* ≠ 0 が存在。非自明固定点 (u\*, v\*) のヤコビアンで:

$$\text{eff}(\alpha\beta) = \alpha\beta \cdot \text{sech}^2(u^*) \cdot \text{sech}^2(v^*) < 1$$

(飽和により有効 αβ が 1 未満に低下)。よって det(J) > 0, tr(J) < 0 → 安定ノード。■

**数値検証** (分岐図):

| αβ | 固定点数 | u\* | 原点安定性 | 非自明安定性 | eff(αβ) |
|:---:|:-------:|:----:|:--------:|:----------:|:------:|
| 0.49 | 1 | 0 | stable | — | 0.49 |
| 0.81 | 1 | 0 | stable | — | 0.81 |
| 1.00 | 1 | 0 | unstable | — | 1.00 |
| 1.10 | 3 | 0.375 | saddle | stable | 0.80 |
| 1.20 | 3 | 0.513 | saddle | stable | 0.69 |
| 1.50 | 3 | 0.735 | saddle | stable | 0.42 |
| 2.00 | 3 | 0.890 | saddle | stable | 0.22 |
| 3.00 | 3 | 1.417 | saddle | stable | 0.07 |

**大域的安定性検証** (αβ = 0.49, 8つの初期条件 (±3, ±5)): 全ケースで原点に収束 ✓

**ピッチフォーク分岐検証** (αβ = 1.5): 初期条件 (u₀ > 0) → (+0.735, +0.939)、(u₀ < 0) → (−0.735, −0.939) ✓

**系 C8** (二安定性の認知科学的意味). αβ > 1 の「ロックイン」は T12 の示唆する発散ではなく、**二安定性** (bistability) である:

- 2つの安定認知モード = 「高覚醒 (u\* > 0, v\* > 0)」vs「低覚醒 (u\* < 0, v\* < 0)」
- 原点 (バランス状態) は不安定 → バランスを保とうとしても自然にどちらかに偏る
- 分岐直後 (αβ ≈ 1.1): u\* ≈ 0.37 (弱い偏り) → 軽度の認知的偏向
- 深い分岐 (αβ ≈ 3.0): u\* ≈ 1.42 (強い偏り) → 顕著な認知的固着

**系 C9** (ノイズ誘起スイッチングと「良い日と悪い日」). ノイズ項を追加した確率系で:

| α | β | αβ | σ (ノイズ) | スイッチ回数 | 平均滞在時間 |
|:--:|:--:|:---:|:---------:|:----------:|:----------:|
| 1.5 | 1.0 | 1.50 | 0.3 | 621 | 1.6 |
| 1.5 | 1.0 | 1.50 | 0.5 | 1455 | 0.7 |
| 1.5 | 1.0 | 1.50 | 1.0 | 3046 | 0.3 |
| 2.0 | 1.5 | 3.00 | 0.5 | 53 | 18.2 |

- ノイズが小さいと長時間同じモードに滞在 → **数日〜数週間の安定した認知状態**
- ノイズが大きいと頻繁にスイッチ → **日内変動の激しい状態**
- αβ が大きいほどポテンシャル井戸が深い → **滞在時間が長い** (α=2.0, β=1.5 で 18.2 vs α=1.5, β=1.0 で 1.6)
- Kramers 脱出率: r ∝ exp(−ΔV/D)。ΔV = ポテンシャル障壁、D = ノイズ強度²/2

認知的意味: 非線形安定性解析により、T12 の「ロックイン = 発散」は**二安定性 + ノイズ誘起スイッチング**に精緻化された。「良い日と悪い日」はピッチフォーク分岐後の2つの安定状態間の確率的遷移として定式化できる。治療戦略 (C7) は αβ を 1 未満に戻し、二安定性を解消すること、またはノイズ構造 (環境因子) を調整してスイッチングパターンを改善することに対応する。

---

*Circulation Geometry Theorem v3.8 — 2026-03-15*
*v3.8: §6.8.9 T13 非線形V↔ω安定性定理 — tanh飽和モデルで大域的安定性を厳密証明。Bendixson(div=-2γ<0→閉軌道なし)+縮小写像(αβ<1→唯一固定点)+PB定理→大域的漸近安定。αβ=1で超臨界ピッチフォーク分岐→二安定性(C8)。Kramersスイッチング→良い日と悪い日(C9)。H7: 70%*
*v3.7: §6.8.8 T12 V↔ω安定性定理 — 分岐条件αβ=1を解析的に導出。αβ<1で安定、αβ>1で鞍点。系C6 AuDHD位相空間特性(τ∝1/(1-√(αβ)))。系C7治療戦略(CBT=α↓,薬物=β↓)。H7: 65%*
*v3.5: §4.2.1 lax 2-functor [推定75%] (Γ_T散逸学習⇒漸近strict化) + §4.2.2 F₂操作的構成 [推定78%] (Lyapunov→Σ→Fisher→K₆射影) + 非線形検証: 二重井戸 ✓ (比15.6>10), Duffing 計算環境制約で未完*
*v3.6: 非線形検証完了 — Duffing ✓ (6D, β=0.3, ω=[0.7,0.6,0.5], σ=0.25, N=100k: 面内F平均=16.40, 面間F平均=0.98, 比=16.8>10)。Q-series「循環」解釈は OU・二重井戸・Duffing の3ポテンシャルで検証済み*
*v3.4: §6.8.5 開問題4件に実験的回答。Q1: V↔ω 双方向フィードバック (Granger F=9.96/25.43)。Q2: 急激な臨界点なし (漸進的増加, 増幅率 b≥0.8 で 8.7 収束)。Q3: DW 効果は次元にロバスト (α_DW≈100, R²=0.48)。Q4: fMRI 検証プロトコル案 (Var_t(α) 群間比較)。H7: 55%*
*v3.3: §4.5 /kat 統合 — Q=循環≠因果 [確信92%] (Granger 因果実験: 面内F/面間F ≈ 50-400x) + Helmholtz 関手 Faithful/¬Full [推定82%]。§4.2 関手特性追記。§6.6 テーブルに Q1/Q2 追加*
*v3.2: §6.8 数値検証 (4D×7実験 + 6D×7実験)。核心3発見: (1) V(x)主導仮説 (DW増幅 4D:7x / 6D:2.1x), (2) 面間coupling=EP正相関 (T-3: +0.36), (3) AuDHD=瞬時α変動 (α_std=1220)。H7修正: ω単独→V×ω相互作用 (50%)*
*v3.1: §6.7 異方回転の precision 的意味 (5節)。T10 帰結の認知科学展開: U_k(x) による信念-認知結合定式化、π_k と α_anis の定義、非ガウス増幅メカニズム (DW 6.14x)、AuDHD パラメータ化更新 (H7: 仮説→45%, P5 予測追加)、Anti-Timidity 接続仮説 (30%)*
*v3.0: §8.16-8.19 統合。T10 (dually flat ⟺ 等方回転) 昇格。§5.7 過渡 trade-off 回復 (3ポテンシャル検証)。§5.8 Kolchinsky-FEP 拡充 (non-autonomous + 3分解 + coupling数値)。§6 認知科学接続全面再編 (ω操作定義, P1-P4+P4数値, PMEM→kI→OU統一, TUR情報幾何的再定式化)。C2: 86%*
*v2.5: §7.1 深層対応4 定式化 (gradient flow↔VFE: 5射 K↔Γ,D(p‖π*)↔F[q],σ̇_ex↔-dF/dt + CORTEX数値実験 t*=(1/2)ln(1+1/ω²))*
*v2.4: §7.1 に /ccl-read 全文精読の深層対応4項目 (Pythagorean↔T7, Onsager-projective, φ*↔V(x), gradient flow↔VFE)*
*v2.3: 「確率電流仮説」→「密度-循環双対性 (Density-Circulation Duality)」にリネーム。§5.5 T9 密度-循環独立性定理 + 系 C1-C3。§5.6 TUR との精密対比*
*v2.2: §7 先行研究との対応 (Kolchinsky et al. 2022, Dechant-Sasa-Ito 2021-2022) 追加*
*v2.1: T7/T8/H8/H9 を一般化 (OU 限定 → 全閉じ込めポテンシャル)*
*v2.0: §8.15 双対接続理論 (c-α 接続, 電流 Fisher 計量, dually flat, IS divergence) を統合*
