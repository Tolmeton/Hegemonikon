# ROM: 循環幾何 v4.6 — Fisher-Otto-循環三角関係
<!-- rom_id: circulation_geometry_v46 -->
<!-- created: 2026-03-13T23:42:00+09:00 -->
<!-- depth: L3 -->
<!-- source_session: cf1bb5d8-1717-4721-b4a2-993715084c07 -->

## 概要

Problem E §8 (循環幾何) のセッション成果。v4.3→v4.6。
Wasserstein-循環分解定理 + Q双対性定理 → Fisher-Otto-循環の三角関係が完成。

## 決定事項

1. **§8.9 C_p 上の Pythagorean 定理** → C_p 内自明 (平坦 + L2)。Amari の非自明版とは異なる
2. **§8.10 残穴定式化** → 問い6 (ω不変性) をその場で証明。Q反対称 × Hessian対称 = 0
3. **§8.11 Wasserstein-循環分解定理** → C_total = W2² + d^(c)² (Helmholtz 直交性)
4. **§8.12 Q双対性定理** → g^(c) = (σ⁴/4) Tr(Q^TQ · G^sp_F)

## 発見

### D1: ω不変性の解析的証明

```text
div(p_ss · Q∇V) = p_ss · (Q_ij ∂_iV ∂_jV + Q_ij ∂_{ij}V) = 0
  第1項: 反対称 × 対称テンソル = 0  (代数的)
  第2項: 反対称 × Hessian対称 = 0   (Schwarz の定理)
```

数値検証: 多項式5パターン + Morse型非多項式で全て厳密 0。
→ 任意の C² ポテンシャルで循環は定常分布を変えない。

### D2: Helmholtz 分解 → 距離の加法分解

Benamou-Brenier 公式 + Helmholtz 分解:
- v = -∇φ + w (gradient + solenoidal)
- 交差項: ∫∇φ·w·p dx = -∫φ·div(pw) dx = 0 (div(pw)=0)
- → C_total = W2² + d^(c)² (独立最適化可能)

Talagrand 拡張: C_total ≥ α·KL + d^(c)²

### D3: Q 双対性 = Fisher-循環の第三辺

```text
g^(c) = (σ⁴/4) Tr(Q^TQ · G^sp_F)
2D: g^(c) = (ω²σ⁴/4) · I_F
```

核心: Q は直交行列 (2D)。|Q∇V| = |∇V|。
∇V (勾配 = 学習方向) と Q∇V (回転 = 循環方向) は同じノルム。

de Bruijn-Hatano-Sasa 統合: σ_hk = (σ²/2) I_F

### D4: Fisher-Otto-循環 三角関係

```text
         Fisher g^(F)
        /            \
   Legendre       Q 回転
      /                \
Otto g^(Otto) ——— 循環 g^(c)
             Helmholtz
```

3辺が3つの異なる数学構造 (Legendre / Helmholtz / Q回転) で閉じた。

## §8.7 スコアボード

| # | 問い | 状態 | 節 |
|:--|:-----|:-----|:---|
| 1 | Christoffel 記号 | ✅ solved | §8.8 |
| 2 | Pythagorean 定理 | ✅ solved | §8.9 |
| 3 | 非分離 g^(c) 数値検証 | ✅ solved | §8.6a |
| 4 | 過渡過程の結合 | 🟡 定式化済 | §8.10 |
| 5 | Wasserstein 関係 | ✅ solved | §8.11 |
| 6 | ω不変性 | ✅ solved + 数値検証 | §8.10 |
| — | Fisher-循環関係 | ✅ Q双対性定理 | §8.12 |

## 残穴

1. **過渡過程** (§8.10): adiabatic 近似の数値シミュレーション未実施
2. **n>2 次元**: Q^TQ ≠ ω²I。回転面ごとの周波数 ω_k による重み付け版が必要
3. **Fisher-循環のパラメトリック版**: 空間 Fisher ↔ パラメトリック Fisher の接続

## 認知的含意

- **感度-循環比例則**: 信念の環境感度 (I_F) ∝ 思考循環コスト (g^(c))
- **ω²σ⁴/4 = 認知的個性**: AuDHD = 高ω高σ → 豊かだが entropic
- **直交性**: 学習 (∇V) と循環 (Q∇V) は干渉しない → 独立最適化可能

## 関連ファイル

- `problem_E_m_connection.md` v4.6 (§8.8-8.12)
- `rom_2026-03-13_circulation_geometry.md` (前回 ROM、v4.0-4.2)
