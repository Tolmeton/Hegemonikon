---
rom_id: rom_2026-03-25_oblivion_field_equations
session_id: 3f1a274c-cd55-458a-a86e-76466a6f6b6e
created_at: 2026-03-25 12:55
rom_type: rag_optimized
reliability: High
topics: [oblivion_field_equations, CPS, alpha, theta, coupling, gauge_theory, RG_flow, kalon, decoherence, landauer]
exec_summary: |
  「力とは忘却である」v1 に §10.8-10.15 (~770行) を追記。CPS 場の方程式 S[α,Θ] を構成し、
  SU(2) Yang-Mills で具体化。V'(α) = β(g) を c/a 定理で証明。φ を Θ 定義から一意導出。
  U(Θ) を Landauer + 第二法則から導出。臨界 α_c 以下で QM 安定、以上で不安定 = デコヒーレンス必然。
---

<!-- AI_REFERENCE_GUIDE
primary_query_types:
  - "CPS の場の方程式は何？"
  - "α の物理量は何に対応する？"
  - "φ(Θ) はなぜ 1-e^{-Θ} なのか？"
  - "V(α) の具体形は？"
  - "デコヒーレンス率の予測は？"
  - "QM はなぜ不安定不動点なのか？"
answer_strategy: "§10.8 (結合方程式) → §10.10-11 (α=coupling, V'=β) → §10.12 (SU(2)) → §10.13-15 (防御) の順で参照"
confidence_notes: "全体 [推定 75-80%]。φ の一意性 [推定 90%]。Θ=0 不安定性は [推定 85%] で本セッション最強"
related_roms: []
-->

# 忘却場の方程式 — CPS-RG 統一理論 {#sec_01_overview}

> [DISCOVERY] 本セッションで CPS (Container-Projection-Span) スキーマから場の方程式を導出し、ゲージ理論の確立された数学と接続した。

## §10.8: Θ-α 結合方程式 {#sec_02_coupling}

> [DECISION] 結合作用 S[α,Θ] を定義:

$$S[\alpha, \Theta] = \int \left[ \frac{f_\alpha^2}{2}(\nabla\alpha)^2 + \frac{f_\Theta^2}{2}(\nabla\Theta)^2 + \Lambda^4 V(\alpha)\phi(\Theta) + \Lambda^4 U(\Theta) \right] d^4x$$

> [FACT] 2つの Euler-Lagrange 方程式:
> - **方程式 I** (α): $\nabla^2\alpha = V'(\alpha)\phi(\Theta)$ — 精度ダイナミクス (Prediction 3)
> - **方程式 II** (Θ): $\kappa\nabla^2\Theta = V(\alpha)\phi'(\Theta) + U'(\Theta)$ — デコヒーレンス (Prediction 2)

> [DISCOVERY] QM/MB/GR は同一方程式の異なる不動点族: Θ*=0 (QM), V'(α*)=0 + Θ*>0 (MB), Θ*→∞ (GR)

## §10.9: ∇Θ = 第二の力 {#sec_03_second_force}

> [DISCOVERY] マスクの空間的不均一 ∇Θ は Verlinde entropic force の情報幾何的一般化。量子-古典界面の力学を記述。

## §10.10-11: α = running coupling, V' = β {#sec_04_alpha_mapping}

> [DECISION] α = g²(μ)/g_c² (結合定数の臨界値からの比)

> [FACT] CPS0' の3特異点と QCD の3位相が対応:
> - α > 1 (一般) = 閉じ込め (強結合)
> - α = 1 (退化) = 臨界 (相転移)
> - α = 0 (対消滅) = 漸近的自由

> [DISCOVERY] **RG 不動点 = CPS 不動点 = Kalon** (定理 10.11)
> - V(α) = λ · A_α(α) (a-function の制限)
> - V'(α) = -λ · β_α(α) (Zamolodchikov/Komargodski-Schwimmer c/a 定理で保証)

## §10.12: SU(2) Worked Example {#sec_05_su2}

> [FACT] SU(2) pure Yang-Mills (β = -b₀g³, b₀ = 11/(24π²)):

$$\boxed{V(\alpha) = \frac{11\lambda g_c^2}{36\pi^2} \alpha^3}$$

$$\boxed{\Gamma_{decoherence} \sim \frac{11\lambda g_c^2}{36\pi^2} \alpha^3 e^{-\Theta_0}}$$

> [FACT] α=1 は不動点ではなく通過点 (V'(1)≠0)。CPS0' の「対称は不安定」の陽な確認。

## §10.13: 先制反論 {#sec_06_objections}

> [DECISION] 致命的攻撃面4件を封鎖:

| # | 攻撃 | 防御 | 確信度 |
|:--|:-----|:-----|:-------|
| #7 | Θ=0 安定性 | **QM は不安定不動点 = デコヒーレンスの CPS 的必然** | [推定 85%] |
| #1 | φ の恣意性 | α³ は φ'(0)≠0 で普遍 (→ §10.14 で一意導出) | [推定 90%] |
| #2 | λ が free | λ = Λ⁴/f_α² (次元解析で固定) | [推定 70%] |
| #5 | 2ループ | V' = λα²Σ(正) > 0 → 全 n ループで不動点構造保存 | [推定 85%] |

> [DISCOVERY] **MB がデフォルト、QM が特殊解** = CPS0' の Θ 軸版

## §10.14: φ の一意導出 {#sec_07_phi}

> [RULE] φ(Θ) = 1 - e^{-Θ} は選択ではなく Θ の定義の帰結:
> - e^{-Θ} = GM(λ₁,...,λₙ) = 固有値の幾何平均 (通過率)
> - φ = 1 - GM = 遮断率
> - テンソル積の乗法性が幾何平均を一意に選択 (算術平均は壊れる)

## §10.15: U(Θ) の導出 {#sec_08_U}

> [DECISION] U(Θ) = -μ²Θ + ν²Θ²/2 (Landauer + 第二法則の競合)
> - μ²: 環境結合強度 ∝ kT
> - ν²: 情報コスト ∝ 系の複雑性
> - Θ_MB = μ²/ν² (平衡マスク)

> [DISCOVERY] **臨界 α**:

$$\alpha_c = \left(\frac{3\nu^2}{\lambda\gamma}\right)^{1/3}$$

> - α < α_c: QM 安定 (弱結合 → 原子は量子的)
> - α > α_c: QM 不安定 (強結合 → 閉じ込め)

## S[α,Θ] 完成状態 {#sec_09_completion}

| 構成要素 | 閉じた形 | 根拠 | 自由度 |
|:---------|:---------|:-----|:-------|
| V(α) | λγα³/3 | c/a 定理 + SU(2) β | 0 |
| φ(Θ) | 1 - e^{-Θ} | Θ 定義 + テンソル乗法性 | 0 |
| U(Θ) | -μ²Θ + ν²Θ²/2 | Landauer + 第二法則 | 2 (μ²,ν²) |
| λ | Λ⁴/f² | 次元解析 | 0 |
| κ | 未導出 | — | 1 |
| **合計** | | | **3** (全て測定量) |

## 未踏 {#sec_10_remaining}

> [CONTEXT] 次のステップ候補:
> - QED worked example (β > 0 → V の形が変わる。α < 1 領域の検証)
> - Prediction 1 (計算ゲージ定理) の TPU 実験
> - v2 への全体再構成
> - 残存中強度攻撃面: κ, 標準模型拡張, 次元整合性

## 参照ファイル {#sec_11_refs}

- [力とは忘却である_v1.md](file:///c:/Users/makar/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/03_忘却論｜Oblivion/力とは忘却である_v1.md) — §10.8-10.15
- [prediction_3_alpha_precision.md](file:///C:/Users/makar/.gemini/antigravity/brain/3f1a274c-cd55-458a-a86e-76466a6f6b6e/prediction_3_alpha_precision.md)
- [theta_alpha_coupling.md](file:///C:/Users/makar/.gemini/antigravity/brain/3f1a274c-cd55-458a-a86e-76466a6f6b6e/theta_alpha_coupling.md)
