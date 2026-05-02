---
rom_id: rom_2026-03-25_categorical_simplex_curvature
session_id: ead87b41-783a-4c76-908f-ce5665ce66f0
created_at: 2026-03-25 23:15
rom_type: distilled
reliability: High
topics: [categorical_simplex, Chebyshev_1_form, Fisher_metric, information_geometry, directionality_theorem, oblivion_curvature, Paper_I]
exec_summary: |
  カテゴリカルシンプレックスΔⁿ上の忘却場の曲率選択則を/noe+ L3で導出。
  T_i = 1-(n+1)p_i, dT=0 (指数型分布族の自然パラメータ系で普遍), K=+1/4。
  安定性は定性的議論のみ (Θ=0不安定は未証明, 推定60%)。
  Paper I 予測P4への支持は部分的。第2メカニズム(Chebyshevねじれ)は指数型では不活性。
  ⚠️ C_{ijk} 閉形式 (v1) は誤り → v2 (∂g_{jk}/∂θ_i) が正しい (2026-03-26 /dio 修正)。
---

# Δⁿ上の忘却場曲率選択則 {#sec_01_topic}

> **[DECISION]** 指数型分布族では dT=0 が普遍的に成立。Paper I §5.4 の「シンプレックスでは両メカニズムが同時に寄与する可能性」は修正が必要。力は第1メカニズム (dΦ∧T≠0) のみ。

> **[DISCOVERY]** カテゴリカル分布の Chebyshev 1-形式は T_i = 1-(n+1)p_i。ker(T) = {均等分布 p_i=1/(n+1)} = 最大エントロピー状態。

> **[DISCOVERY]** T_i = ∂_i log det g が指数型分布族で成立 → dT = d(d log det g) = 0 が自動的に従う。

## 主要結果テーブル {#sec_02_comparison}

| 項目 | ガウス族 (ℋ²) | カテゴリカル (Δⁿ) |
|:-----|:-------------|:----------------|
| 多様体 | ポアンカレ上半平面 | S^n 正象限 (半径2) |
| ガウス曲率 K | -1/2 | +1/4 |
| Fisher 計量 | g = (1/σ²)diag(1,2) | g_{ij} = p_i(δ_{ij}-p_j) |
| Chebyshev T_i | (0, 6/σ) | 1-(n+1)p_i |
| ker(T) | ∂/∂μ 方向 | 均等分布 p_i=1/(n+1) |
| dT | = 0 (閉) | = 0 (閉) |
| F_{ij} | (α/2)(∂_μΦ)(6/σ) | (α/2)[(∂_iΦ)T_j-(∂_jΦ)T_i] |
| **Θ=0 安定性** | **安定 (K<0)** | **不安定化傾向 (K>0)** — 厳密条件は λ < λ_c(K,T) |

## 核心数式 {#sec_03_formulas}

> **[FACT]** 自然パラメータ系 θ_i = log(p_i/p_{n+1}):

```
g_{ij} = p_i(δ_{ij} - p_j)
C_{ijk} = ∂g_{jk}/∂θ_i = (∂p_j/∂θ_i)(δ_{jk} - p_k) - p_j(∂p_k/∂θ_i)
  ⚠️ 旧式 C_{ijk} = p_i(δ_{ij}δ_{ik} - ...) は誤り (v3.py で検出)
T_i = 1 - (n+1)p_i
det g = p₁p₂...p_{n+1}
log det g = Σ log p_k
T_i = ∂_i log det g → dT = 0  (指数型分布族限定)
```

> **[FACT]** 忘却曲率 (dT=0 のため簡素化):

```
F_{ij} = (α/2)[(∂_iΦ)(1-(n+1)p_j) - (∂_jΦ)(1-(n+1)p_i)]
```

> **[FACT]** 球面変換 x_i = 2√p_i → Δⁿ ≅ S^n_+(R=2), K = 1/4

## 不確実領域 {#sec_04_uncertainty}

> **[CONTEXT]** 信頼度分布 (2026-03-26 /dio 更新):
- T_i = 1-(n+1)p_i の導出: [確信 98%] — v4.py 15/15 PASS
- dT = 0: [確信 97%] — 指数型分布族限定
- K=+1/4 → Θ=0 不安定: [推定 60%] — **厳密な変分導出が未完**。λ の閾値条件不明

## 次ステップ {#sec_05_next}

> **[RULE]** 数値検証 (/pei+):
1. T_i = 1-(n+1)p_i を SymPy で独立検証
2. F_{ij} の有限差分検証 (oblivion_field_gaussian.py のパターンに倣う)
3. Θ=0 安定性の摂動解析

## 関連情報
- 関連 WF: /noe+ (本分析の実行)
- 関連ファイル: 論文I_力としての忘却_草稿.md §4 (Worked Example 1 = ガウス族)
- Paper I 更新: v0.3→v0.5 (§3.4 λ注釈, §5.4 dT=0普遍性, §6.8 P4弱化, §9 P4現状更新)
- 関連 Session: ead87b41... (本セッション)

<!-- ROM_GUIDE
primary_use: Paper I §4b (Worked Example 2) の数学的基盤
retrieval_keywords: カテゴリカル分布, Fisher計量, Chebyshev形式, 正曲率, 球面, 安定性
expiry: permanent
-->
