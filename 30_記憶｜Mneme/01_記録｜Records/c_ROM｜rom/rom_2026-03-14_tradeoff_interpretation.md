---
created: 2026-03-14T10:58:55+09:00
topic: Trade-off 恒等式の一般解釈 — 物理計量 vs 情報計量の非対称性
depth: L3
source_session: e68b574b
tags: [circulation_geometry, fisher_information, trade-off, autonomia, NESS]
---

# ROM: Trade-off 恒等式の一般解釈

## 1. 核心構造

```
g^(c)     = ω² · (σ⁴/4) · I_F^{sp}(V)   ← V 依存 (物理コスト)
g^{(c,F)} = 1/ω²                          ← V 独立 (情報感度)
product   = (σ⁴/4) · I_F^{sp}(V)          ← ω 独立、V 依存
```

**不確定性関係**:
```
(循環コスト) × (循環感度) = (地形の急峻さ)
```

## 2. 非対称性の根源

### g^{(c,F)} が V 非依存な理由
- j_ss = ω · p_ss · J∇V → ∂_ω log|j| = 1/ω
- j は ω に線形 → log j は log ω + (V依存項)
- ω で微分すると V 依存項が消える
- **これは j_ss の定義レベルで成立** — ポテンシャルの形状に一切依存しない

### g^(c) が V 依存な理由
- g^(c) = ∫ |j_ss|²/p_ss dx = ω² ∫ p_ss |Q∇V|² dx
- ∫ p_ss |∇V|² dx は V の形状に依存
- **循環の物理的コスト (housekeeping EP) は ∇V の大きさで決まる**

## 3.「認知スタイル推定の信念非依存性」の真偽分析

### 数学的に真な部分
- [確信] Fisher 情報 g^{(c,F)} = 1/ω² は V 非依存 → ω の Cramér-Rao 下界は V に依存しない
- [確信] 密度-循環の直積構造 (T7) → ω と θ の推定は独立
- [確信] dually flat 構造の V 非依存性 → IS divergence でのω推定効率は普遍的

### 解釈上の注意 (過剰般化のリスク)
- [仮説] 「ω = 認知スタイル」は比喩。ω は回転角速度であり、認知スタイルの全てではない
- [推定] 実際の認知系は単一の ω ではなく多次元パラメータ空間
- [仮説] V = 信念ポテンシャルの同定自体が大きな未解決問題

### 結論
数学的構造としては真。ω の推定効率が V に依存しないのは定義レベルで成立。
認知科学への適用は analogical — 直接的同一視は過剰主張。
ただし「スタイルと内容の独立性」という構造が情報幾何から自然に出る点は非自明。

## 4. 関連論文調査

### 最も近い先行研究群
1. **Dechant, Sasa, Ito (2021)** "Geometric decomposition of entropy production" (48 citations)
   - excess/housekeeping EP の幾何的分解
   - 我々の trade-off 恒等式と深く関連するが、循環 Fisher 計量の V 非依存性は未言及
2. **Kolchinsky, Dechant, Yoshimura, Ito (2022)** "Information geometry of excess and housekeeping EP" (15 citations)
   - EP の力と流れの情報幾何的構造
   - 最も我々の構造に近い — しかし dually flat 構造の V 非依存性は議論されていない
3. **Dechant, Sasa, Ito (2022)** "Geometric decomposition into excess, housekeeping, and coupling" (27 citations)
   - 3成分分解 (coupling 成分を新規導入)
   - 我々の交差項ゼロ (coupling ゼロ) は彼らの coupling 成分の特殊ケースか？
4. **Lacerda, Bettmann, Goold (2025)** "Information geometry of transitions between quantum NESS"
   - NESS 間遷移の Fisher 計量。量子系への拡張。

### 車輪の再発明？
- **部分的に重複**: EP の情報幾何的分解は Dechant-Sasa-Ito が確立済み
- **新規部分**: 循環 Fisher 計量 g^{(c,F)} = 1/ω² の V 非依存性、
  dually flat 構造の普遍性、IS divergence の出現は明示的に論じられていない
- **完全に新規**: 認知科学 (S-II Autonomia) との接続、HGK への応用

### 認知科学側
- 認知スタイル研究 (Witkin: field dependence/independence) は統計的に独立な因子として確立
- 信念内容と認知スタイルの分離は dual process theory でも前提されるが情報幾何的基盤はない
- **「ω推定のV非依存性」を認知スタイル-信念分離の数学的基盤として提示した研究は未発見**

## 5. 数値結果

| ポテンシャル | I_F^{sp} | g^(c)·g^{(c,F)} | 解釈 |
|---|---|---|---|
| OU | 4.0 | 1.0 | 基準 |
| Duffing (ε=0.3) | 4.86 | 1.21 | 4次 barrier で急峻 |
| ダブルウェル | 5.36 | 1.34 | 二重井戸で最急峻 |
| 三次+安定化 | 5.49 | 1.37 | 非対称で最大 |

## 6. 変更ファイル
- problem_E_m_connection.md §trade-off 恒等式の一般解釈 (新規追加)

## 7. 次の方向
- Dechant-Sasa-Ito の coupling 成分と我々の交差項ゼロの関係を精査
- Kolchinsky et al. の力-流れ分解と trade-off 恒等式の対応を確認
- 認知科学的解釈を rigorous にするための条件整理
