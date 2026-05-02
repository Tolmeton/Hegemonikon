# Phase C v3 TPU Handoff

## Goal
- `project-b6ffbdd9-37f5-45e4-816` / `nous.sync@gmail.com` 上の TPU で `phase_c_v3` を実行可能にする。
- 現状の対象は `v6e` 優先。`L4` はまだ削除しない。

## Current Status
- Local TPU script exists:
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu.py`
- Remote nodes:
  - `phase-c-v3-v6e-alpha` / `asia-northeast1-b` / `v6e-1` / `READY`
  - `phase-c-v3-v6e-asia-northeast1-b` / `asia-northeast1-b` / `v6e-1` / `READY`
- Preferred node is `phase-c-v3-v6e-alpha` because `runtimeVersion=v2-alpha-tpuv6e`.
- Remote external IP of `phase-c-v3-v6e-alpha`:
  - `34.85.0.29`
- `A / smoke64 balanced / max_len=64 / quick` completed successfully on TPU.
- Full TPU ablation has been launched in background:
  - process: `python -u phase_c_v3_tpu.py --all --output phase_c_v3_tpu_full_20260409.json`
  - log: `~/phase_c_v3/phase_c_v3_tpu_full_20260409.log`
  - output: `~/phase_c_v3/phase_c_v3_tpu_full_20260409.json`
  - global partial: `~/phase_c_v3/phase_c_v3_tpu_full_20260409.partial.json`
  - current observed state at launch: `A / baseline / Fold 1/5` first compile

## Remote Environment
- Remote work dir:
  - `~/phase_c_v3`
- Remote clean venv:
  - `~/venvs/phase-c-v3-tpu-clean`
- Remote clean stack confirmed:
  - `torch 2.6.0+cu124`
  - `torch_xla 2.6.1`
  - `transformers 4.40.0.dev0` from `~/transformers-tpu-clean` (`flash_attention` branch of `pytorch-tpu/transformers`)
  - `peft 0.10.0`
- XLA device probe passed in clean venv:
  - `xm.get_xla_supported_devices("TPU") -> ['xla:0']`
  - `xm.xla_device() -> xla:0`

## Local Code Changes Already Applied
- `phase_c_v3.py`
  - partial save helper added
  - OOM guard for `B + λ>0`
  - GPU/L4 rerun safety improved
- `phase_c_v3_tpu.py`
  - CUDA/QLoRA/Trainer path removed
  - TPU/XLA manual training loop added
  - warmup+cosine scheduler added
  - runtime metadata added to outputs
  - `flash_attention=False` default injected when missing
  - gradient checkpointing disabled on XLA
  - gradient clipping (`max_grad_norm=1.0`) restored to match Trainer default and avoid TPU bf16 NaNs

## Completed Smoke Result
- Command completed:
  - `PJRT_DEVICE=TPU python -u phase_c_v3_tpu.py --condition A --data phase_c_condition_A_smoke64_balanced.jsonl --quick --max-len 64 --output phase_c_v3_tpu_smoke_A64b.json`
- Wall time:
  - `62.6 min`
- Final summary:
  - `baseline`: `acc=0.594`, `F1=0.620`, `ρ_logits=0.4198`, `partial_ρ_ccl=-0.0699`, `R@1=0.03`
  - `lxi_0.1`: `acc=0.594`, `F1=0.620`, `ρ_logits=0.4253`, `partial_ρ_ccl=-0.0813`, `R@1=0.03`
- Final artifacts on remote:
  - `~/phase_c_v3/phase_c_v3_tpu_smoke_A64b.json`
  - `~/phase_c_v3/phase_c_v3_tpu_smoke_A64b.partial.json`
  - `~/phase_c_v3/phase_c_v3_tpu_A_partial.json`
  - `~/phase_c_v3/smoke_A64b.log`
- Final artifacts copied locally:
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu_smoke_A64b.json`
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu_smoke_A64b.partial.json`
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu_A_partial.json`
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu_A_partial_preclip_nan.json`
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/smoke_A64b.log`

## Important Line References
- Model load / TPU-specific config:
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu.py:345`
- `flash_attention` fallback:
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu.py:353`
- XLA gradient checkpointing disable:
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu.py:365`
- CLI defaults / quick mode:
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3_tpu.py:662`

## What Was Tried
- Full A quick on 1000-pair `phase_c_condition_A_full.jsonl`
  - log: `~/phase_c_v3/smoke_A_clean.log`
  - reached model load and compile
  - earlier failures fixed:
    - `peft` / `transformers` incompatibility
    - `gradient_checkpointing` with XLA
    - missing `config.flash_attention`
  - process was manually terminated during long compile.
- Smaller 64-row smoke on first 64 lines
  - log: `~/phase_c_v3/smoke_A64.log`
  - bad subset: all-positive labels (`64 pos, 0 neg`)
  - also manually terminated during compile.
- Balanced smoke subset file has already been created:
  - `~/phase_c_v3/phase_c_condition_A_smoke64_balanced.jsonl`
  - contains `32 pos / 32 neg`
- First balanced TPU smoke attempt completed baseline but diverged to `NaN` on epoch 2
  - archived partial: `~/phase_c_v3/phase_c_v3_tpu_A_partial_preclip_nan.json`
- Restart without `source ~/venvs/phase-c-v3-tpu-clean/bin/activate` failed immediately with wrong-site-package imports
  - archived log: `~/phase_c_v3/smoke_A64b_wrongenv_20260409-093108.log`
- Final balanced TPU smoke rerun succeeded after restoring Trainer-equivalent gradient clipping
  - log: `~/phase_c_v3/smoke_A64b.log`
  - output: `~/phase_c_v3/phase_c_v3_tpu_smoke_A64b.json`

## Main Remaining Blocker
- XLA compile time is still the main practical blocker for larger runs.
- Even on the successful smoke, first compile was heavy:
  - `baseline fold 1`: `1751s`
  - `lxi_0.1 fold 1`: `1798s`
- Numerical instability for TPU bf16 was mitigated for this smoke by restoring `max_grad_norm=1.0`.
- The next larger TPU run should assume ~30 min first-compile latency per new graph family.

## Recommended Next Step
While the full TPU ablation is running, monitor it with:

```bash
ssh 34.85.0.29 '
bash -lc "
cd ~/phase_c_v3
tail -120 phase_c_v3_tpu_full_20260409.log
ls -l phase_c_v3_tpu_full_20260409.json phase_c_v3_tpu_full_20260409.partial.json \
      phase_c_v3_tpu_A_partial.json phase_c_v3_tpu_B_partial.json phase_c_v3_tpu_D_partial.json 2>/dev/null || true
ps -ef | grep phase_c_v3_tpu.py | grep -v grep || true
"
'
```

After that run completes, compare this TPU path against an L4 run on the *same* balanced 64-row slice before promoting TPU as a production backend.

Suggested command shape on the L4 path:

```bash
python phase_c_v3.py \
  --condition A \
  --data phase_c_condition_A_smoke64_balanced.jsonl \
  --quick \
  --max-len 64 \
  --output phase_c_v3_gpu_smoke_A64b.json
```

Then compare at least:

1. `epoch_train_loss`
2. `acc / F1`
3. `rho_logits / partial_rho_ccl`
4. whether TPU/L4 preserve the same qualitative ordering between `baseline` and `lxi_0.1`

## Decision Notes
- `phase-c-v3-v6e-alpha` runtime choice itself is not the experimental treatment.
- But this TPU path is **not numerically identical** to the old CUDA/QLoRA/Trainer implementation.
- Treat the TPU version as a backend-port run until it is validated against L4 outputs on at least one comparable smoke slice.

## Do Not Forget
- Do not delete the L4 instance yet.
- TPU smoke finally completed, but backend equivalence is still unvalidated.
- Compare this exact balanced 64-row slice against L4 behavior before promoting TPU as the production backend.
