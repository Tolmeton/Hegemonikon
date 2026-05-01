# Structural Attention Phase C-mini Reproducibility Bundle

作成日: 2026-04-26

この bundle は `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/構造的アテンション_草稿.md` の Phase C-mini 主結果を固定するための paper-local 再現束である。

## 1. 内容

| path | 役割 | provenance |
|:---|:---|:---|
| `source/phase_c_mini_results.json` | Phase C-mini の元結果 JSON | `/home/makaron8426/Sync/oikos/02_作業場｜Workspace/B_個人｜Personal/tpu-experiments/phase_c_mini_results.json` |
| `source/dataset_v3.json` | 246 pair dataset | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/dataset_v3.json` |
| `scripts/structural_attention.py` | Structural Attention model | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/structural_attention.py` |
| `scripts/train_structural_attention.py` | training / CV runner | `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/train_structural_attention.py` |
| `reports/phase_c_mini_report_HEAD.md` | report snapshot | git `HEAD:10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/phase_c_mini_report.md` と同一 hash |

## 2. 固定された主結果

| condition | mean rho | mean partial rho | R@1 | folds |
|:---|---:|---:|---:|---:|
| `hybrid_lxi_0.0` | `0.9579709922110187` | `0.9545035086578906` | `1.0` | `5` |
| `hybrid_lxi_0.01` | `0.961737033313337` | `0.959502381415489` | `1.0` | `5` |
| `hybrid_lxi_0.1` | `0.9622048975859432` | `0.9591531356063546` | `1.0` | `5` |
| `hybrid_lxi_1.0` | `0.9631681246445829` | `0.9597954360852059` | `1.0` | `5` |

## 3. 再実行コマンド

```bash
cd '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/reproducibility/structural_attention_phase_c_mini_20260324'
python scripts/train_structural_attention.py \
  --dataset source/dataset_v3.json \
  --model codebert \
  --layer 12 \
  --folds 5 \
  --epochs 50 \
  --p14 \
  --cache-dir .hidden_cache \
  --output source/phase_c_mini_results_rerun.json
```

## 4. 検証

```bash
cd '/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/12_遊学｜Yugaku/01_研究論文｜Papers/reproducibility/structural_attention_phase_c_mini_20260324'
sha256sum -c MANIFEST.sha256
jq '{n_pairs, target_layer, hidden_dim, results: .results}' source/phase_c_mini_results.json
```

## 5. 注意

- `source/phase_c_mini_results.json` は本実験結果であり、`n_pairs=246`, `n_folds=5`。
- `/home/makaron8426/Sync/oikos/02_作業場｜Workspace/B_個人｜Personal/tpu-experiments/tpu-experiments/phase_c_mini_results.json` は `n_pairs=10`, `n_folds=2` の dry-run なので本 bundle には採用しない。
- `reports/phase_c_mini_report_HEAD.md` は現ワークツリーでは削除扱いの報告書を、HEAD と同一 hash の snapshot として固定したもの。
