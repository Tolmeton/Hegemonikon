```typos
#prompt handoff-2026-03-26-oblivion-validation
#syntax: v8
#depth: L2

<:role: セッション引継ぎドキュメント — 選択的忘却定理の実験的検証 :>

<:goal: 次セッションが本セッションの成果と中立的結果を正確に把握し、Phase C に集中できる状態にする :>

<:context:
  - [knowledge] セッション日時: 2026-03-25 ~ 2026-03-26
  - [knowledge] Agent: Claude (Antigravity)
  - [knowledge] 主題: 選択的忘却定理 (Prediction 1) の JetBrains Complexity Trap データによる実験的検証
/context:>
```

---

# Handoff: 選択的忘却定理の実験的検証 (2026-03-26)

## セッション概要

JetBrains Complexity Trap データセット (SWE-bench Verified 500問 × 3条件) を用いて、選択的忘却定理 (Prediction 1: Ξ↑ → P↑) を Phase α/β'/γ'B の 3 フェーズで検証した。

**結果: 中立** — 支持も否定もできない。

## 実施した作業

### 1. データ取得と展開
- HuggingFace `JetBrains-Research/the-complexity-trap` から 3 条件の tar.gz をダウンロード・展開
  - `C:\tmp\complexity_trap\extracted_500\masking\` (558MB, N=500)
  - `C:\tmp\complexity_trap\extracted_500\raw\` (817MB, N=500)
  - `C:\tmp\ct\sum500\` (summary 500件をフラット展開, 670MB)
- P ラベル: `evaluation__*.json` の `resolved_ids` から取得

### 2. Phase β': 条件内 Ξ-P 相関
- **Ξ 操作化 v1** (入力サイズ分散): masking 条件で Entropy_ratio ρ=-0.10, p=0.025 → **符号が Prediction 1 と逆**
- **Ξ 操作化 v2** (raw-masking 差分 L1 距離): Ξ_L1 ρ=+0.157, p=0.0005 → **Prediction 1 と整合**
- **交絡の発見**: trajectory 長 (n_turns) が Ξ_L1 (ρ=-0.67) と P (ρ=-0.23) の両方を駆動する交絡変数。偏相関 ρ_partial|n_turns = +0.001, p=0.988 → **完全に消失**

### 3. Phase γ'B: 条件間介入分析
- Cochran Q (3条件) = 0.75, p=0.687 → **有意差なし**
- McNemar 対比較: 全て非有意 (p=0.43~0.91)
- 解決率: raw 54.0%, masking 55.8%, summary 55.0% → 差は ±2%

### 4. 論文記録
- `力とは忘却である_v1.md` に §11 を追記 (中立的結果の正直な記録)
- 忘却論 v1 を §11 で凍結する判断

## 重要な設計決定

1. **JetBrains データは Prediction 1 の検証に構造的に不適切** — 3条件は「忘却の質」ではなく「忘却の有無/方式」を変えているだけ
2. **忘却論 v1 は凍結** — Phase C (Structural Attention on TPU) に集中する方針を Creator と合意
3. **Prediction 1 の再定式化が必要** — testable な形: 「ランダム忘却 vs 構造的忘却で解決率に差があるか」

## 残タスク

| タスク | 優先度 | 状態 |
|:-------|:-------|:-----|
| Phase C: TPU 上の Structural Attention 実験 | **最高** | スクリプト SCP 済、実行待ち |
| Prediction 1 の testable 再定式化 | 中 | 未着手 |
| v2 構成 (§10.20) への §11 配置 | 低 | 未着手 |

## 生成物の場所

| ファイル | パス |
|:---------|:-----|
| Ξ-P 相関 (masking) | `C:\tmp\xi_phase_ab_results.json` |
| Ξ 差分分析 | `C:\tmp\xi_diff_results.json` |
| 偏相関結果 | `C:\tmp\xi_partial_results.json` |
| 条件間介入結果 | `C:\tmp\xi_intervention_results.json` |
| 分析スクリプト群 | `C:\tmp\xi_*.py` |
| 論文 §11 | `力とは忘却である_v1.md` 末尾 |
| Phase C スクリプト | `C:\tmp\lethe_scp\` |

## TPU 状態

- `oblivion-train-v6e` (v6e-4): SSH トンネル接続中。Phase C スクリプトが SCP 済
- Phase C の `train_structural_attention.py` / `structural_attention.py` / `eval_structural_attention.py` + `dataset_v3.json` が `C:\tmp\lethe_scp\` にコピー済

## 教訓

1. **操作化の乖離は致命的** — 理論の Ξ (忘却関手の不均一度) とテキスト長分散は全く異なる量
2. **交絡変数の確認は最初にすべき** — trajectory 長という自明な confound を最初に制御していれば、不要な分析を省けた
3. **中立的結果の正直な記録は資産** — §11 は「やったが出なかった」の記録。これ自体が次の理論修正の羅針盤になる
