# PROOF — 07_非平衡認知実験

## PURPOSE
HGK 実行ログから 6D 認知状態ベクトルを抽出し、VAR(1) モデルで B=Γ+Q 分解、
エントロピー生成 EP を推定する実験群。C3 (V ↔ Belief Potential) の経験的検証。

## 存在証明
- `extract_hgk_augmented.py`: データ増強版 6D 状態抽出 + Level 2 Φ 推定
- `sensitivity_alpha.py`: 矛盾1+2 対応 — Theorem Log 重み α 感度分析 + Bootstrap EP

## 実験結果 (2026-03-15)
- V1 (安定性): 全 α で PASS (頑健)
- k_max: α 依存 (Value@α=0 → Function@α=0.1-0.7 → Value@α=1.0)
- EP: α に単調増加 (0.18→0.89)、Bootstrap CI 幅が大きい
- Scale 軸: 全条件で不活性 (σ < 0.005)

## 依存
- 入力: `30_記憶｜Mneme/01_記録｜Records/g_実行痕跡｜traces/`
- 入力: `30_記憶｜Mneme/01_記録｜Records/f_ログ｜logs/`
- 理論: `00_核心｜Kernel/A_公理｜Axioms/problem_E_m_connection.md` §8.16
