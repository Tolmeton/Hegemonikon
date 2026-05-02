# ROM+: 循環幾何 v4.7 全体蒸留 — Fisher-Otto-循環三角関係 + HGK体系接続
<!-- rom_id: circulation_geometry_complete_v47 -->
<!-- created: 2026-03-13T23:56:00+09:00 -->
<!-- depth: L3 -->
<!-- source_session: cf1bb5d8-1717-4721-b4a2-993715084c07 -->

## 概要

Problem E §8 (循環幾何) のセッション全体を L3 深度で蒸留。
v4.0 (前回 ROM) → v4.7。8問全て solved。
核心発見: Fisher-Otto-循環の三角関係 + Q双対性が運動学的恒等式 + HGK 6座標が 3 回転面を持つ。

## セッション経路

```
§8.8 Christoffel → §8.9 Pythagorean → §8.10 残穴定式化 (問い6証明)
→ §8.11 Wasserstein-循環分解 → §8.12 Q双対性 → §8.13 n>2一般化
→ §8.14 HGK体系接続 [仮説]
```

## 決定事項 (確信度付き)

### D1: 循環空間 C_p は平坦 [確信]
- Christoffel 記号 Γ^(c) = 0 (p_ss 固定時)
- Pythagorean 定理は C_p 内で自明成立 (L2 計量)
- Amari の非自明版とは対照的

### D2: ω不変性の証明 [確信]
```text
div(p_ss · Q∇V) = 0  ∀ V ∈ C²
  第1項: Q反対称 × ∂V⊗∂V 対称 = 0
  第2項: Q反対称 × Hessian 対称 = 0
```
- 6つのポテンシャル (多項式5 + Morse型) で数値的に厳密 0 を確認
- 含意: どんな V でも循環は定常分布に影響しない (非対称双対性)

### D3: Wasserstein-循環分解定理 [確信]
```text
C_total = W2² + d^(c)²  (Helmholtz 直交性)
交差項: ∫∇φ·w·p dx = -∫φ·div(pw) dx = 0
Talagrand 拡張: C_total ≥ α·KL + d^(c)²
```

### D4: Q 双対性定理 [確信]
```text
g^(c) = (σ⁴/4) Tr(Q^TQ · G^sp_F)
2D: g^(c) = (ω²σ⁴/4) · I_F
```
- **運動学的恒等式**: p に依存しない。過渡過程でも厳密成立
- 数値検証: g^(c)/I_F = ω²σ⁴/4 が全時刻で誤差 < 10⁻⁶

### D5: Fisher-Otto-循環 三角関係 [確信]
```text
Fisher ——Legendre—— Otto
  \                  /
 Q回転            Helmholtz
    \              /
      循環 g^(c)
```
- 3辺が3つの異なる数学構造で閉じた

### D6: n>2 次元一般化 [推定 65%]
- Q の Schur 分解 → ⌊n/2⌋ 回転面
- g^(c) = (σ⁴/4) Σ_k ω_k² I_F^(k) (スペクトル分解)
- 奇数次元は Q-不変方向を持つ (「真理の軸」)

### D7: HGK 6座標 = 3 回転面 [仮説 40%]
- HGK の 6 修飾座標 → 6D 状態空間 → 3 回転面
- X-series (15 関係) = C(6,2) = Q 行列の独立成分数
- 回転面ペアリング候補: Value×Function, Precision×Scale, Valence×Temporality

## 核心定理の一覧

| ID | 名前 | 式 | 確信度 |
|:---|:-----|:---|:-------|
| CT-1 | ω不変性 | div(p·Q∇V) = 0 | 確信 |
| CT-2 | Helmholtz 分解 | C = W2² + d^(c)² | 確信 |
| CT-3 | Q 双対性 | g^(c) = (σ⁴/4) Tr(Q^TQ G^sp) | 確信 |
| CT-4 | スペクトル分解 | g^(c) = Σ_k ω_k² I_F^(k) | 推定 |
| CT-5 | de Bruijn-HS | σ_hk = (σ²/2) I_F | 確信 |

## 過渡過程シミュレーション結果

```
ω=0.5: g^(c) 1.30→0.37 (ss:0.38), ratio=0.0625=theory ✓
ω=1.0: g^(c) 5.19→1.51 (ss:1.50), ratio=0.2500=theory ✓
ω=2.0: g^(c) 20.8→6.01 (ss:6.00), ratio=1.0000=theory ✓
```
→ Q双対 ratio が全時刻で厳密一致 = 運動学的恒等式

## 残穴

1. **X-series 整合性**: 既存 X-series 定義と Q 行列解釈の突合せ → axiom_hierarchy.md 参照要
2. **Hyphē 転用**: 回転面の軸通過 → チャンク境界の定量化
3. **Kalon 定量化**: Fix(G∘F) = Fisher-循環不動点としての定義
4. **パラメトリック Fisher**: 空間 Fisher ↔ パラメトリック Fisher の橋渡し
5. **Kernel 昇格**: §8.14 の仮説検証後、circulation_theorem.md として Kernel に配置

## 次セッションへの指示

1. axiom_hierarchy.md を view_file → X-series 定義と Q 行列の対応を検証
2. Hyphē の PoC 結果と循環周波数 ω の対応を調査
3. 検証通過後、Kernel に独立ファイルとして昇格

## 関連ファイル

- `problem_E_m_connection.md` v4.7 (§8.8-8.14)
- `rom_2026-03-13_circulation_geometry.md` (v4.0-4.2)
- `rom_2026-03-13_fisher_circulation_triangle.md` (v4.3-4.6)
- `axiom_hierarchy.md` (← 次セッションで検証対象)
