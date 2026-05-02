# ROM: 異方回転 × AuDHD × Precision — 情報幾何的定式化

> **日付**: 2026-03-15
> **深度**: L3
> **確信度**: [推定 70%] (全体としての理論的整合性)
> **Source Session**: 59bd146b (Anisotropy AuDHD Cognitive Meaning)

---

## 核心成果

### §6.7 を circulation_theorem.md v3.1 に追加 (147行, 5節)

T10 (Dually flat ⟺ 等方回転, [確信 95%]) の認知科学的含意を定式化した。

#### 1. 信念-認知結合の定式化 (§6.7.1)

```text
等方: ∂_ω log|j| = 1/ω (x非依存) → g^{(c,F)} = 1/ω² (V非依存) → 独立
異方: ∂_{ω_k} log|j| = U_k(x) (x依存) → g^{(c,F)} は V依存 → 結合

U_k(x) = ω_k |(∇V)_{k-pair}|² / Σ_l ω_l² |(∇V)_{l-pair}|²
= 信念地形 V における方向 k の相対的勾配寄与率
```

**要点**: 等方回転だけが「どう考えるか」(ω) と「何を信じるか」(V) の独立性を保証する。
異方回転は precision の content-dependent bias を生む。

#### 2. precision の非一様性 (§6.7.2)

```text
π_k := 1 / g^{(c,F)}_{kk} = ω_k² / E[U_k²]

異方度: α_anis := max_k(π_k) / min_k(π_k)
  = 1 → 完全等方 (理想)
  >> 1 → 強異方 (認知の固着/過敏)
```

S-III Akribeia の理想 = α_anis = 1。異方性は S-III 違反の循環幾何的表現。

#### 3. 非ガウス増幅 (§6.7.3) — 数値検証済み

| 信念構造 | 増幅率 | 機構 |
|:---------|:------:|:-----|
| OU (ガウス: 単峰) | 1.00x | U_k は連続的 → V依存弱 |
| DW barrier=2 (双峰) | **4.40x** | U_k が双峰化 (0付近 + 1付近) |
| DW barrier=5 (強双峰) | **6.14x** | 二項対立信念で異方性が激化 |

**核心**: 双峰信念 (二項対立, all-or-nothing) が認知速度の非対称性を増幅する。
信念の「壁」(barrier) が高いほど ω-V 結合が強化される。

#### 4. AuDHD パラメータ化更新 (§6.7.4)

```text
ADHD = 動的異方性: dω_k/dt の分散が大 → precision が不安定に変動
ASD  = 静的異方性: ω_k 自体に永続的偏差 → precision のチャネル間不均衡
併存 = 動的 + 静的 → 精度の偏りが予測不能に変動
```

H7: [仮説] → **[仮説 45%]**
P5 (新規予測): AuDHD 群の Var_k(ω_k) × Var_t(ω_k(t)) が重症度と正相関

#### 5. Anti-Timidity 接続 (§6.7.5) [仮説 35%]

座標体系ベースで再分類 (候補A ペアリング: Π₁=Value×Function, Π₂=Precision×Scale, Π₃=Valence×Temporality):

**単一面パターン** (ω_k の直接的抑制/偏倚):
- T-1 /bye 提案禁止 → Π₃ 面 (Valence×Temporality) の ω 抑制
- T-4 保守的選択禁止 → Π₁ 面 (Value×Function) の ω 均一化
- T-6 尻込み禁止 → Π₂ 面 (Precision×Scale) の ω 抑制

**面間 coupling パターン** (§5.8 σ̇_cp ≠ 0 との接続):
- T-2 時間見積禁止 → Π₂→Π₃ coupling (Precision×Temporality 干渉)
- T-3 先延ばし禁止 → Π₁→Π₃ coupling (Function×Temporality 干渉)
- T-5 体調言及禁止 → Π₃→Π₁ coupling (Valence×Value 干渉)

**§5.8 接続**: 面間 coupling (σ̇_cp ≤ 0) = EP を減らす = 認知コスト削減 = 安易な道。
CCL 動詞対応: Π₁=/ene,/bou | Π₂=/ops,/lys | Π₃=/prm,/ath

---

## 確信度マップ

| 対象 | 確信度 | 根拠 |
|:-----|:------:|:-----|
| T10 (dually flat ⟺ 等方回転) | 95% | 解析証明 + 非OU 3種数値検証 |
| C2 (ω ↔ 認知スタイル) | 86% | 7文献 + P4 + kI + TUR |
| §6.7.1-2 信念-認知結合の定式化 | 90% | T10 の直接帰結 (数学的演繹) |
| §6.7.3 非ガウス増幅 | 85% | MCMC N=80K 数値検証済み |
| H7 AuDHD パラメータ化 | **45%** | T10帰結+増幅。fMRIデータなし |
| §6.7.5 Anti-Timidity 接続 | **30%** | 構造的類似のみ |

## 未解決

1. ω_k の面間差が AuDHD 特異か一般的個人差かの弁別
2. V→ω の因果方向 (信念→認知速度? 認知速度→信念固着?)
3. Anti-Timidity T-1〜T-6 の CCL 動詞 × 回転面の体系的対応 (24×K 空間)
4. fMRI time-series での ω_k 推定と P5 予測の検証

## 関連ファイル

- [circulation_theorem.md](../../../00_核心｜Kernel/A_公理｜Axioms/circulation_theorem.md) v3.1 §6.7
- [problem_E_m_connection.md](../../../00_核心｜Kernel/A_公理｜Axioms/problem_E_m_connection.md) §8.18.1-8.18.2
- [rom_2026-03-14_p4_dual_fim_omega.md](rom_2026-03-14_p4_dual_fim_omega.md)
