---
rom_id: rom_2026-03-13_circulation_geometry
session_id: cf1bb5d8-1717-4721-b4a2-993715084c07
created_at: 2026-03-13 22:56
rom_type: distilled
reliability: Medium
topics: [circulation geometry, NESS, Pythagorean theorem, Christoffel symbols, Hatano-Sasa, problem E, m-connection]
exec_summary: |
  循環幾何 (Circulation Geometry) の定式化。C_p 空間の平坦性証明、
  NESS ダイバージェンス D_NESS = KL + d^(c)² の導出、
  Helmholtz 分解の幾何的実体同定。Problem E v4.3。
---

# 循環幾何の定式化 (Problem E v4.0→v4.3)

## 決定事項

> **[DECISION]** "current geometry" → **循環幾何** (Circulation Geometry) に改名
>
> 理由: j_ss は Q 成分 (保存的循環)、gauge 軌道 (Orb)、Flow (d=1) の保存的部分。
> 「電流」は物理からの借用語で FEP→圏論の血筋に乗らない。
> 以降: g^(j) → g^(c), ∇^(j) → ∇^(c), J_p → C_p

> **[DECISION]** C_p は平坦空間。Γ^(c) = 0 (Levi-Civita 接続)
>
> g^(c) が ω に依存しない定数計量であるため。循環パターンの空間は「曲がっていない」。
> 密度空間 P の曲がった幾何との対照的な構造。

> **[DECISION]** NESS ダイバージェンスの定義:
>
> D_NESS[(p₁,j₁):(p₂,j₂)] = KL[p₁:p₂] + ½ d^(c)(j₁,j₂)²
> = 非対称項(密度) + 対称項(循環)

## 発見

> **[DISCOVERY]** Hatano-Sasa EP 分解の幾何学的定式化
>
> σ = σ_ex + σ_hk ←→ D_NESS = KL + d^(c)²
> - σ_ex (excess EP) → KL[p₁:p₂] (密度幾何の距離)
> - σ_hk (housekeeping EP) → d^(c)(j₁,j₂)² (循環幾何の距離)
> EP の加法分解が幾何学の直交分解として自然に出現する。

> **[DISCOVERY]** Helmholtz 分解の幾何的実体同定 [推定 60%]
>
> Γ (学習/gradient) → KL → 密度幾何の距離
> Q (循環/solenoidal) → d^(c)² → 循環幾何の距離
> Γ + Q → D_NESS → NESS の完全な距離

> **[DISCOVERY]** ハイブリッド Pythagorean 定理
>
> 成立条件: (1) 密度方向の e-m 直交 AND (2) 循環方向の g^(c) 直交
> Case A (p固定): パターン学習 — d^(c)² のみ
> Case B (j固定): 知識学習 — KL のみ
> Case C (結合): 全体学習 (達人化)

> **[DISCOVERY]** 非分離ポテンシャルでの g^(c) 数値検証
>
> λx₁x₂ 結合で: 非対角成分 g₁₂ ≈ λ (線形依存)、
> 主軸回転 (π/4)、異方性増幅、Tr(g) は λ² に増加。
> 結合した信念は本来の座標軸とは異なる方向に思考を流す。

## §8.7 残穴状況

| # | 状態 | 問い |
|:--|:-----|:-----|
| 1 | ✅ solved | Christoffel 記号 → §8.8。C_p 内平坦 |
| 2 | ✅ solved | Pythagorean 定理 → §8.9。D_NESS 導出 |
| 3 | ✅ solved | 非分離 g^(c) → §8.6a。数値検証完了 |
| 4 | 🔴 未解決 | 過渡過程 (∂p/∂t ≠ 0) での密度-循環結合 |
| 5 | 🔴 未解決 | Wasserstein 距離との関係 |
| 6 | 🔴 未解決 | 非分離で p_ss の ω 不変性 |

## 関連情報

- 関連ファイル: `00_核心｜Kernel/A_公理｜Axioms/problem_E_m_connection.md` (v4.3)
- 関連問題: Problem B (Amari), C (Helmholtz), D (NESS)
- 前セッション: conv `eaeb134f` (current geometry 初期定式化)

<!-- ROM_GUIDE
primary_use: Problem E の循環幾何セクション (§8) の進捗追跡と次セッションへの引継ぎ
retrieval_keywords: circulation geometry, C_p, NESS divergence, Pythagorean, Christoffel, Hatano-Sasa, EP decomposition, housekeeping entropy
expiry: permanent
-->
