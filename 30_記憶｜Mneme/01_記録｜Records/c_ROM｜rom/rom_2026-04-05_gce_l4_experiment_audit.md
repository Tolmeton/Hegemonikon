# ROM: GCE L4 実験回収・監査・v3 投入 (2026-04-05)

## DECISION: LoRA 初期化バグ (E1) の発見と修正

- **バグ**: v2/v3 の fold 間 LoRA リセットで `lora_B` にも `kaiming_uniform_` を適用
- **正**: lora_A = kaiming, lora_B = zeros (初期 LoRA 出力 = 0 を保証)
- **v1 はバグなし**: clone/copy 方式で peft の初期化を保存・復元していた
- **v2 で混入**: fold ループ導入時に kaiming 直接呼び出しに変更し lora_B を壊した
- **影響**: v2 の全結果 (ρ=0.459) はバグあり。P14 (λ最適値) は TAINT

## DECISION: v2 結果の信頼度判定

- P11' 棄却 (vs C-mini ρ=0.963): **維持** — 方向は変わらない
- P14 支持 (lxi_0.01 最良): **TAINT** — λ条件間相対順位が汚染
- v1 (13B, ρ=0.857): **信頼可** — バグなし

## DECISION: Phase C v3 修正版を GCE L4 に投入

- E1: LoRA 初期化修正 (lora_A/lora_B 分離)
- E2: logits (sigmoid 前) でも ρ を記録 — 飽和前の信号
- E4: 条件間 paired t-test (fold 対応) をサマリーに追加
- PID 30886, 推定完了 4/8 朝
- Pinakas T-060, T-061 に登録済み

## DISCOVERY: Phase B2 ゼロ結果の原因

- Gemma4 ロード → CUDA OOM (他プロセスと VRAM 競合)
- キャッシュ 34/369 関数のみ → それも NoneType エラーで全滅
- 全 fold で n<5 → 即 ρ=0.0 return
- **probe のバグではない。データパイプラインの物理的断裂**

## FILES: GCE 回収先

- ローカル: `60_実験｜Peira/theta_b_external/gce_l4_results/` (21ファイル)
- GCE: 34.29.169.168 (NVIDIA L4, 23GB VRAM)
- 大ファイル: b2_gemma4_extracted.npz (527MB) は `60_実験｜Peira/` 直下

## PLAN: 次のステップ

1. v3 結果回収 (4/8 以降)
2. P14 再検証 (v3 結果で)
3. B2 再実行 (v3 完了後、GPU 単独占有で)
4. VISION.md 更新
