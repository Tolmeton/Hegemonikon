---
rom_id: rom_2026-03-14_p4_dual_fim_omega
session_id: e68b574b-b0cd-453c-8330-e01a6caf811a
created_at: 2026-03-14 14:27
rom_type: distilled
reliability: High
topics: [omega, FIM, stiff-sloppy, trade-off identity, PMEM, entropy production, Chen2025, OU model, circulation]
exec_summary: |
  P4 二重FIM分析: ω は分布FIMで最sloppy (rank M/M)、流FIMで最stiff (rank 1/M)。
  trade-off 恒等式 g^(c)·g^(c,F) = const の物理的意味を数値実証。
  C2 確信度 80%。Chen α=0.48 は「ω が丁度 stiff になる閾値」。
---

# P4: ω-Stiff 仮説の二重FIM分析 {#sec_01_dual_fim}

> **[DECISION]** 仮説の修正: ω は単純に stiff ではなく、「分布-sloppy / 流-stiff」の二重性を持つ

## §1 問題設定 {#sec_02_setup}

> **[CONTEXT]** multivariate OU モデル dX = -BXdt + σdW で B = S + ωA (S: 対称正定値, A: 反対称)

パラメータ空間: θ = (S の上三角成分, ω)。M = n(n+1)/2 + 1 次元。

**当初の仮説 (v1)**: ω は FIM で stiff (上位ランク)。つまり定常分布から ω を敏感に推定できる。

## §2 v1 結果: 仮説の棄却 {#sec_03_v1_rejection}

> **[DISCOVERY]** 分布FIM での ω のランクは全次元 (n=4,6,8) で M/M (最 sloppy)

**数学的根拠**: Lyapunov 方程式 BΣ + ΣB^T = D で定常共分散 Σ が決まる。対称部分と反対称部分を分離すると:

```
SΣ + ΣS = D  (主方程式: ω 非依存)
ωAΣ + ωΣA^T = ω[A, Σ]  (摂動: 交換子のみ)
```

Σ と A がほぼ交換する場合 [A, Σ] ≈ 0 → ω は Σ をほとんど変えない。

## §3 v2 結果: 核心的発見 — 二重FIM分析 {#sec_04_v2_discovery}

> **[DISCOVERY]** 2 種類の FIM を同時に計算すると、ω の「見え方」が完全に反転する

| FIM | 観測量 | ω ランク (n=4) | |⟨v_stiff, e_ω⟩| | 物理的意味 |
|---|---|---|---|---|
| **分布 FIM** | 定常分布 Σ | 11/11 (最sloppy) | < 0.01 | 定常分布は ω に鈍感 |
| **流 FIM** | EP + 循環指標 | **1/11 (最stiff)** | > 0.98 | EP・循環は ω に鋭敏 |
| **複合 FIM** (α=0.48) | 混合 | 1/11 | 0.61 | Chen 最適バランス |

**次元スケーリング**: n=4, 6, 8 で構造は不変。分布-sloppy / 流-stiff は次元非依存。

## §4 trade-off 恒等式の物理的解釈 {#sec_05_tradeoff}

> **[DISCOVERY]** trade-off 恒等式 g^(c) · g^(c,F) = const は「分布感度 × 流感度 = 一定」を意味する

```
g^(c)    = ω²     → 流ベース、stiff (EP ∝ ω²)
g^{(c,F)} = 1/ω²  → 分布ベース、sloppy
積        = 定数   → trade-off
```

EP に対する ω の相対感度 |∂EP/∂ω|/EP ≈ 2.0 (理論予測: EP ∝ ω² → 感度 = 2)。全次元で一致。

## §5 認知科学への翻訳 {#sec_06_cognitive}

> **[DECISION]** ω は「信念内容 (what) を変えずに認知プロセス (how) を変える」唯一のパラメータ方向

| 概念 | 分布ベース (PMEM) | 流ベース (EP) |
|---|---|---|
| 観測対象 | 「何を信じるか」 | 「どう考えるか」 |
| ω の可視性 | 不可視 (sloppy) | 最重要 (stiff) |
| Chen の対応 | J_ij = J_ji (対称制約) | α=0.48 閾値 |
| System 1/2 | 区別不能 | 明瞭に分離可能 |

**Chen α=0.48 の新解釈**: 分布と流のバランスで ω が丁度 stiff になる閾値。α < 0.48 では ω は sloppy (分布が支配)、α > 0.48 では ω が stiff (流が支配)。

## §6 C2 確信度推移 {#sec_07_confidence}

> **[DECISION]** C2 確信度: 75% → **80%** (P4 二重FIM分析 + trade-off 恒等式の物理的実証)

| バージョン | 確信度 | 主な根拠 |
|---|---|---|
| v5.3 | 60% | ω の操作定義 + System 1/2 方向性 |
| v5.4 | 70% | 7文献統合 + Chen 対応 |
| v5.5 | 75% | Chen 精読 + PMEM 制約発見 |
| **v5.7** | **80%** | **P4 二重FIM分析 + trade-off 実証** |

## §7 次ステップ {#sec_08_next}

1. **Chen 非対称 PMEM 拡張の深掘り**: J_ij ≠ J_ji を許す非対称モデルで ω がどう見えるか
2. **実データ (HCP/ADHD) への ω 推定**: 流ベース FIM からの推定パイプライン設計
3. **Kolchinsky excess/housekeeping EP 分解**: ω が housekeeping EP を支配する可能性

## 関連情報
- 実験スクリプト: `60_実験｜Peira/07_循環幾何実験｜CirculationGeometry/verify_omega_stiff.py`
- 更新文書: `00_核心｜Kernel/A_公理｜Axioms/problem_E_m_connection.md` (v5.7)
- 関連論文: Chen et al. (2025) "FIM of PMEM"
- 関連 Session: e68b574b-b0cd-453c-8330-e01a6caf811a

<!-- ROM_GUIDE
primary_use: P4 の数値検証結果と理論的洞察。ω の stiff-sloppy 二重性は全ての後続分析の基盤。
retrieval_keywords: omega stiff sloppy FIM distribution flow EP PMEM Chen tradeoff circulation OU Lyapunov
expiry: permanent
-->
