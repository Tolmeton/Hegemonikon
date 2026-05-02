# TPU セットアップ作業レポート

作成日: 2026-04-09
対象プロジェクト: `project-deb07447-0f70-4d65-a91`
対象アカウント: `h.raiki.biz@gmail.com`

## 1. 要約

Cloud TPU VM `sam-cka-run` の作成、PyTorch/XLA 環境構築、実験コード転送、TPU 上での smoke test 実行まで完了した。

最終的に稼働した構成:

- Zone: `us-central1-a`
- Accelerator type: `v5litepod-1`
- Runtime: `v2-alpha-tpuv5-lite`
- TPU VM status: `READY`

TPU 上で `torch_xla` が `xla:0` を認識し、`train_tpu.py` の 1 epoch smoke test (`sgd`, `sam`) が完走した。

## 2. 実施内容

### 2.1 スクリプト整備

`setup_tpu.sh` を以下の要件で更新した。

- project を `project-deb07447-0f70-4d65-a91` に固定
- account を `h.raiki.biz@gmail.com` に固定
- `access`, `inventory`, `create`, `init`, `verify`, `cleanup` のサブコマンド化
- TPU VM 初期化処理に PyTorch/XLA 導入と検証を実装
- `dpkg` ロック待ちを追加
- 実際に通った最小構成に合わせて既定 accelerator type を `v5litepod-1` / `v6e-1` に調整

### 2.2 在庫・作成試行

以下の試行を行った。

1. `v5litepod-8` in `us-central1-a`
   - 失敗
   - 理由: zone quota 超過 (`TPUV5sLitepodServingPerProjectPerZoneForTPUAPI`)
2. `v6e-8` in `us-east5-b`
   - 失敗
   - 理由: capacity 不足
3. `v6e-8` in `us-east5-a`
   - 失敗
   - 理由: capacity 不足
4. `v6e-8` in `us-central1-b`
   - 失敗
   - 理由: submit permission 不足
5. `v6e-8` in `us-east1-d`
   - 失敗
   - 理由: submit permission 不足
6. `v6e-8` in `asia-northeast1-b`
   - 失敗
   - 理由: capacity 不足
7. `v5litepod-1` in `us-central1-a`
   - 成功

### 2.3 VM 初期化

TPU VM 上で以下を実施した。

- `apt-get update`
- `libopenblas-dev` 導入
- `pip` 更新
- `numpy` 導入
- `torch==2.5.1`
- `torchvision==0.20.1`
- `torch_xla==2.5.1`
- `libtpu-nightly`

初回は `unattended-upgrade` が `dpkg` lock を保持して失敗したため、ロック待ちを追加し、最終的には自動更新プロセスを停止してセットアップを継続した。

### 2.4 実験コード転送

TPU VM `~/sam_comparison` に以下を転送した。

- `train_tpu.py`
- `configs.py`
- `optimizers.py`
- `oblivion_field.py`

## 3. 検証結果

### 3.1 XLA デバイス確認

TPU VM 上で以下を確認した。

- `supported_devices=['xla:0']`
- `xla_device=xla:0`
- `torch.randn(..., device=xla:0)` 成功

### 3.2 Smoke test

実行コマンド:

```bash
cd ~/sam_comparison
export PJRT_DEVICE=TPU
python3 train_tpu.py --methods sgd sam --seeds 42 --epochs 1 --out results_smoke_tpu --smoke
```

結果ファイル:

- `results_smoke_tpu/sgd_seed42.json`
- `results_smoke_tpu/sam_seed42.json`

主要指標:

| Method | Train Loss | Test Acc |
|---|---:|---:|
| SGD | 2.10085 | 36.43 |
| SAM | 2.26689 | 31.13 |

両条件とも epoch 1 の CKA / grad_phi / phi profile が保存されていることを確認した。

## 4. 現在の状態

現時点で以下が完了している。

- TPU VM 作成
- TPU VM 初期化
- PyTorch/XLA 動作確認
- 実験コード転送
- smoke test 完走

現時点での稼働リソース:

- TPU VM 名: `sam-cka-run`
- Zone: `us-central1-a`
- Accelerator: `v5litepod-1`
- Status: `READY`

## 5. 次アクション

本番実行に進む場合は、TPU VM 上で以下を実行すればよい。

```bash
cd ~/sam_comparison
export PJRT_DEVICE=TPU
nohup python3 train_tpu.py \
  --methods sgd sam \
  --seeds 42 43 44 45 46 \
  --out results_cka \
  > train_cka.log 2>&1 &
```

結果回収:

```bash
gcloud compute tpus tpu-vm scp \
  --project=project-deb07447-0f70-4d65-a91 \
  --zone=us-central1-a \
  --recurse \
  sam-cka-run:~/sam_comparison/results_cka \
  ./results_cka
```

不要になった場合の削除:

```bash
gcloud compute tpus tpu-vm delete sam-cka-run \
  --project=project-deb07447-0f70-4d65-a91 \
  --zone=us-central1-a
```
