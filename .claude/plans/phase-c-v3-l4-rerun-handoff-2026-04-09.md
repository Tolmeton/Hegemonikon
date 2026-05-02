# Phase C v3 L4 Rerun Handoff

## Goal
- 再作成した L4 VM 上で修正済み `phase_c_v3.py` を再実行し、`phase_c_v3_results.json` を最後まで生成する。
- 今回の本線は TPU ではなく L4。TPU 版は side track とみなす。
- 主確認点は `B + λ>0` の guard が旧 OOM 点を越えられるかどうか。

## Infra Delta (2026-04-09)
- 無料クレジット使用のため、L4 は `Tolmeton` / `project-f2526536-3630-4df4-aff` 側で作り直す。
- `34.29.169.168` の旧 L4 は移行元としてのみ使い、状態回収後に削除する。
- ベストは旧 VM の状態を新 VM にできるだけそのまま移し、その上で patched `phase_c_v3.py` を `--all` で再実行すること。

## Host Convention

```bash
export OLD_L4_HOST=34.29.169.168
export NEW_L4_HOST=<fill-after-create>
```

- 以後の `NEW_L4_HOST` は新しく作る本番 rerun 先を指す。
- `OLD_L4_HOST` は移行・回収・削除対象の旧 VM を指す。
- 新 VM 作成後は、以下の実行・監視・回収コマンドの host 部分を `NEW_L4_HOST` に置き換えること。

## Why L4
- `phase_c_v3.py` の本来の実験実装は CUDA/QLoRA/Trainer 前提。
- TPU 版 `phase_c_v3_tpu.py` は `LoRA + bf16 + 手書き XLA ループ` への移植版で、既存結果との比較可能性が弱い。
- したがって、Phase C v3 の本番再実行は L4 を使うのが妥当。

## Legacy L4 (migration source before delete)
- last direct SSH target: `34.29.169.168`
- local metadata source:
  - `10_知性｜Nous/04_企画｜Boulēsis/00_舵｜Helm/pinakas/PINAKAS_COMPUTE.yaml`
- old machine shape recorded there:
  - project: `project-04762300-3537-489b-80b`
  - account: `rairaixoxoxo@gmail.com`
  - zone: `us-central1-a`
  - machine type: `g2-standard-4`
  - GPU: `NVIDIA L4 (24GB)`
  - disk: `200GB`
- 新 VM は、quota / credit 都合で変更が必要でない限り、この shape に寄せるのが無難。

## New L4 Target
- new account / project:
  - account key: `Tolmeton`
  - project: `project-f2526536-3630-4df4-aff`
- best effort parity target:
  - zone: `us-central1-a`
  - machine type: `g2-standard-4`
  - GPU: `NVIDIA L4 (24GB)`
  - disk: `200GB`
- 新 VM の instance name / external IP は作成後に `NEW_L4_HOST` に反映すること。

## Last Known Legacy L4 State
- `Phase C v3` は以前 `~/phase_c_v3_run.log` で停止。
- 停止原因は `B / lxi_0.01` 付近の CUDA OOM。
- 以前のログでは `512 MiB` の追加確保に失敗していた。
- 当時 GPU はその後 idle に戻っていたので、再実行自体は可能な状態だった。
- `save_strategy="no"` かつ最終 JSON 一括保存だったため、旧 run の途中結果は正式成果物として残っていない。

## Local Source of Truth
- rerun target:
  - `/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py`

## Key Fixes Already Applied
- atomic partial save helper added
  - [phase_c_v3.py](/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py#L52)
- per-condition snapshot payload helper added
  - [phase_c_v3.py](/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py#L60)
- `B + λ>0` の OOM guard added
  - `max_len` shrink
  - train/eval batch shrink
  - [phase_c_v3.py](/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py#L295)
- fold 完了ごとの partial save added
  - [phase_c_v3.py](/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py#L450)
- 例外時 partial save added
  - [phase_c_v3.py](/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py#L462)
- global partial save added
  - [phase_c_v3.py](/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py#L693)
- gradient checkpointing enabled in HF `TrainingArguments`
  - [phase_c_v3.py](/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py#L353)

## Behavioral Notes of the Fix
- `B` 条件の `λ=0` は従来どおり `max_len=1024`, `train_bs=batch_size`, `eval_bs=batch_size*2`
- `B` 条件の `λ>0` だけ guard が入る:
  - `effective_max_len = min(max_len, b_lxi_max_len)`
  - `train_batch_size = min(batch_size, b_lxi_train_batch_size)`
  - `eval_batch_size = min(batch_size * 2, b_lxi_eval_batch_size)`
- 既定値:
  - `--b-lxi-max-len 768`
  - `--b-lxi-train-batch-size 1`
  - `--b-lxi-eval-batch-size 1`

## Recommended L4 Rerun Procedure

### 1. Recreate the new L4 target
- Create the rerun VM under `Tolmeton` / `project-f2526536-3630-4df4-aff`.
- Mirror the old L4 shape as closely as possible: `g2-standard-4`, `NVIDIA L4 (24GB)`, `200GB disk`, `us-central1-a`.
- Once created, fill `NEW_L4_HOST`.

### 2. Recover old VM state before deletion
- Before deleting `OLD_L4_HOST`, inspect and copy over whatever can be preserved.
- Minimum items worth preserving:
  - `~/phase_c_v3.py`
  - `~/phase_c_v3_run.log`
  - `~/phase_c_v3_results.json`
  - `~/phase_c_v3_results.partial.json`
  - `~/phase_c_v3_*_partial.json`
  - repo checkout if present
  - Python env / requirements snapshot if present
  - `~/.cache/huggingface` if present

Inspection command:

```bash
ssh "$OLD_L4_HOST" '
bash -lc "
pwd
python3 --version
nvidia-smi
ls -ld ~/.cache ~/.cache/huggingface 2>/dev/null || true
ls -l ~/phase_c_v3.py ~/phase_c_v3_run.log ~/phase_c_v3_results.json ~/phase_c_v3_results.partial.json ~/phase_c_v3_*_partial.json 2>/dev/null || true
tail -40 ~/phase_c_v3_run.log 2>/dev/null || true
"
'
```

If local relay is needed, use a temp dir and preserve at least the script, logs, partials, and HF cache:

```bash
mkdir -p /tmp/phase-c-v3-rerun
scp "$OLD_L4_HOST:~/phase_c_v3.py" /tmp/phase-c-v3-rerun/ 2>/dev/null || true
scp "$OLD_L4_HOST:~/phase_c_v3_run.log" /tmp/phase-c-v3-rerun/ 2>/dev/null || true
scp "$OLD_L4_HOST:~/phase_c_v3_results.json" /tmp/phase-c-v3-rerun/ 2>/dev/null || true
scp "$OLD_L4_HOST:~/phase_c_v3_results.partial.json" /tmp/phase-c-v3-rerun/ 2>/dev/null || true
scp "$OLD_L4_HOST:~/phase_c_v3_A_partial.json" /tmp/phase-c-v3-rerun/ 2>/dev/null || true
scp "$OLD_L4_HOST:~/phase_c_v3_B_partial.json" /tmp/phase-c-v3-rerun/ 2>/dev/null || true
scp "$OLD_L4_HOST:~/phase_c_v3_D_partial.json" /tmp/phase-c-v3-rerun/ 2>/dev/null || true
scp -r "$OLD_L4_HOST:~/.cache/huggingface" /tmp/phase-c-v3-rerun/huggingface 2>/dev/null || true
```

### 3. Sync the patched file to the new L4
From local, overwrite any migrated copy with the local source of truth:

```bash
scp "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/phase_c_v3.py" \
  "$NEW_L4_HOST:~/phase_c_v3.py"
```

If you used local relay and want to restore preserved state to the new VM as well:

```bash
scp /tmp/phase-c-v3-rerun/phase_c_v3_run.log "$NEW_L4_HOST:~/" 2>/dev/null || true
scp /tmp/phase-c-v3-rerun/phase_c_v3_results.json "$NEW_L4_HOST:~/" 2>/dev/null || true
scp /tmp/phase-c-v3-rerun/phase_c_v3_results.partial.json "$NEW_L4_HOST:~/" 2>/dev/null || true
scp /tmp/phase-c-v3-rerun/phase_c_v3_A_partial.json "$NEW_L4_HOST:~/" 2>/dev/null || true
scp /tmp/phase-c-v3-rerun/phase_c_v3_B_partial.json "$NEW_L4_HOST:~/" 2>/dev/null || true
scp /tmp/phase-c-v3-rerun/phase_c_v3_D_partial.json "$NEW_L4_HOST:~/" 2>/dev/null || true
scp -r /tmp/phase-c-v3-rerun/huggingface "$NEW_L4_HOST:~/.cache/" 2>/dev/null || true
```

If the working directory on the VM is repo-root style, instead sync to the exact experiments dir after checking with `pwd`.

### 4. Verify remote state before launch

```bash
ssh "$NEW_L4_HOST" '
bash -lc "
nvidia-smi
ls -l ~/phase_c_v3.py ~/phase_c_v3_run.log ~/phase_c_v3_results.json ~/phase_c_v3_results.partial.json 2>/dev/null || true
tail -40 ~/phase_c_v3_run.log 2>/dev/null || true
"
'
```

### 5. Optional quick smoke first
- This is only to verify the new guards and partial-save path.
- Use a low-cost run before the full rerun if you want to catch config errors fast.

```bash
ssh "$NEW_L4_HOST" '
bash -lc "
cd ~
nohup python3 phase_c_v3.py --all --quick > phase_c_v3_quick.log 2>&1 &
echo \$!
"
'
```

Quick-run acceptance:
- `phase_c_v3_A_partial.json`, `phase_c_v3_B_partial.json`, `phase_c_v3_D_partial.json` appear as work progresses
- no immediate OOM at `B / lxi_0.1`

### 6. Full rerun

```bash
ssh "$NEW_L4_HOST" '
bash -lc "
cd ~
nohup python3 phase_c_v3.py --all > phase_c_v3_run.log 2>&1 &
echo \$!
"
'
```

If the file lives in another directory, replace `cd ~` with the actual location and run the script there.

## Monitoring Commands

```bash
ssh "$NEW_L4_HOST" '
bash -lc "
tail -80 ~/phase_c_v3_run.log
"
'
```

```bash
ssh "$NEW_L4_HOST" '
bash -lc "
ls -l ~/phase_c_v3_*partial.json ~/phase_c_v3_results.json 2>/dev/null || true
"
'
```

```bash
ssh "$NEW_L4_HOST" '
bash -lc "
ps -ef | grep phase_c_v3.py | grep -v grep || true
nvidia-smi
"
'
```

## Expected Output Files
- final:
  - `~/phase_c_v3_results.json`
- global partial:
  - `~/phase_c_v3_results.partial.json`
- per-condition partials:
  - `~/phase_c_v3_A_partial.json`
  - `~/phase_c_v3_B_partial.json`
  - `~/phase_c_v3_D_partial.json`

## What To Check During Rerun
- `A` and `D` should behave roughly like before.
- `B / baseline` may still be heavy, but should not fail immediately.
- `B / lxi_*` is the main regression target:
  - confirm the log prints the OOM guard line
  - confirm execution proceeds past the previous failure point
- if a later fold still fails, the partial JSON should contain:
  - `error`
  - `failed_condition`
  - `failed_fold`

## If It OOMs Again
Retry with stricter B guard only:

```bash
ssh "$NEW_L4_HOST" '
bash -lc "
cd ~
nohup python3 phase_c_v3.py --all \
  --b-lxi-max-len 640 \
  --b-lxi-train-batch-size 1 \
  --b-lxi-eval-batch-size 1 \
  > phase_c_v3_run.log 2>&1 &
echo \$!
"
'
```

If that still fails, the next lever is reducing global `--batch-size` from `4` to `2`, but only after preserving the first rerun logs.

## Result Recovery
After completion:

```bash
scp "$NEW_L4_HOST:~/phase_c_v3_results.json" \
  "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/"
```

Also recover partials and the run log:

```bash
scp "$NEW_L4_HOST:~/phase_c_v3_run.log" \
    "$NEW_L4_HOST:~/phase_c_v3_results.partial.json" \
    "$NEW_L4_HOST:~/phase_c_v3_A_partial.json" \
    "$NEW_L4_HOST:~/phase_c_v3_B_partial.json" \
    "$NEW_L4_HOST:~/phase_c_v3_D_partial.json" \
  "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/10_知性｜Nous/04_企画｜Boulēsis/14_忘却｜Lethe/experiments/"
```

## Old L4 Cleanup
- After confirming required state has been copied and the new rerun has started cleanly, delete the old L4.
- The old VM metadata/source of truth is the `lethe-phase-c` record in `PINAKAS_COMPUTE.yaml`.
- Do not delete the old VM before confirming that the new VM can launch `phase_c_v3.py` and that any needed cache / logs / partials have been preserved.

## Decision Rule
- If the L4 rerun completes with the patched script, use that as the authoritative Phase C v3 result.
- Do not replace it with TPU results unless TPU and L4 agree on a controlled smoke slice first.
