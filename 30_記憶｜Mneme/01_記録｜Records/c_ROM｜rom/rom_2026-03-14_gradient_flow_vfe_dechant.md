---
rom_id: rom_2026-03-14_gradient_flow_vfe_dechant
session_id: 4dc334a2-fce0-4071-b52c-85fe9e960d22
created_at: 2026-03-14 16:10
rom_type: distilled
reliability: High
topics: [gradient_flow, VFE, entropy_production, Kolchinsky, Dechant-Sasa-Ito, coupling, non-autonomous, FEP, trade-off_identity, cognitive_interpretation]
exec_summary: |
  Kolchinsky SM4 の gradient flow ↔ FEP VFE 最小化の5射対応を定式化し、
  Dechant-Sasa-Ito の3分解 (excess+housekeeping+coupling) を精読。
  Non-autonomous gradient flow の数値実験で σ̇_ex 振動を実証。
---

# Gradient Flow ↔ VFE 対応 + Dechant-Sasa-Ito 3分解

> **[DECISION]** Kolchinsky SM4 の gradient flow ↔ FEP VFE の5射対応を
> problem_E_m_connection.md §8.17.1 に正式記載。

## 1. Kolchinsky Gradient Flow ↔ FEP VFE 5射対応

> **[DISCOVERY]** 5つの構造的対応

| Kolchinsky (SM4) | FEP (Friston 2019 §4) | 物理的意味 |
|-----------------|----------------------|-----------|
| Onsager matrix K | 散逸成分 Γ | 対称正定値 → 勾配流の「摩擦」 |
| D(p‖π*) | F[q] = VFE | Lyapunov 関数 (autonomous時) |
| dt p = -K grad D | ẋ_μ = -Γ∇F | 勾配流方程式 |
| σ̇_ex | -dF/dt | 学習の速度 (VFE減少率) |
| σ̇_hk | Q-cost | 循環維持コスト |

## 2. CORTEX 解析解 (2D OU)

> **[FACT]** 解析的に導出された遷移時刻

```
σ̇_hk = 2ω²
σ̇_ex(t) = 2(1+ω²) e^{-2t}
t* = (1/2) ln(1 + 1/ω²)   ← 学習→維持の切替時刻
```

- ω大 (System 2): t* ≈ 0 → housekeeping 即支配
- ω小 (System 1): t* 大 → 学習優位期間が長い

## 3. Non-autonomous Gradient Flow 数値実験

> **[DISCOVERY]** 3パターンで σ̇_ex の振動/非単調性を実証

| パターン | 結果 |
|---------|------|
| Step (ω=1→3, t=2) | t=2 で σ̇_ex 再上昇 → ピーク (t=3.55) → 減衰 |
| Sinusoidal | σ̇_ex 支配的周波数 0.252 ≈ ω の 0.250 Hz (追従振動) |
| Random walk | tail CV=1.25、定常に到達しない |

- Autonomous (ω固定) = perception → σ̇_ex 単調減少
- Non-autonomous (ω変動) = learning → σ̇_ex 振動 → VFE は Lyapunov でない

## 4. Dechant-Sasa-Ito 3分解 (arXiv:2202.04331, PRE 106, 024125)

> **[DISCOVERY]** EP の3分解と coupling 項の発見

```
σ̇ = σ̇_excess + σ̇_housekeeping + σ̇_coupling   (Eq.25)
```

- **Hatano-Sasa 分解**: σ̇ = σ̇_ex^HS + σ̇_hk^HS
- **Maes-Netočný 分解**: σ̇ = σ̇_ex^MN + σ̇_hk^MN
- **統一 (Dechant-Sasa-Ito)**: σ̇_ex^MN = σ̇_ex^HS + σ̇_coupling

> **[FACT]** 3項は相互直交 (内積 ⟨a,b⟩_p = ∫ a·b/p dx)

> **[FACT]** coupling=0 の条件:
> (a) 保存力のみ (ω=0)、(b) 定常 (p=p^st)、(c) 両駆動が独立な自由度に作用

> **[DECISION]** 我々の OU で coupling=0 の理由: ω 時間独立 → 唯一の非平衡源は非保存力 → 定常到達後は excess=0 → coupling の発動条件 (時間依存+非保存力の同時存在) を満たさない

## 5. §IX: σ̇_ex^HS = -d D_KL(p‖p^st)/dt

> **[DISCOVERY]** excess EP が KL divergence の減少率を特徴づける
> = 我々の R_IF → 1 (trade-off 恒等式の回復度) と同一物理

## 6. 未解決の問い

> **[CONTEXT]** 次のステップ候補

1. coupling の FEP 認知的解釈: coupling = 知覚更新 × 循環思考の相互作用コスト？
2. ω(t) 時間変動時の coupling の Appendix A 明示式による定量計算
3. 変分表現 (§VI): MN 分解 = 勾配場成分最大化 → 我々の等式は最適性条件？
4. TUR (§VII): excess/housekeeping/coupling 各項の不確定性関係

## 関連情報
- 関連 WF: /ccl-read, /ccl-dig
- 関連 KI: circulation_theorem.md, problem_E_m_connection.md
- 関連 Session: 4dc334a2-fce0-4071-b52c-85fe9e960d22

<!-- ROM_GUIDE
primary_use: gradient flow ↔ VFE 対応の参照、EP 3分解の FEP 解釈
retrieval_keywords: gradient flow, VFE, entropy production, coupling, Kolchinsky, Dechant, excess, housekeeping, non-autonomous, learning, perception
expiry: permanent
-->
