#!/usr/bin/env python3
"""Phase C-mini: Structural Attention 訓練パイプライン。

PROOF: structural_attention.py のモデルを dataset_v3.json で訓練し、
  構造検索 recall@1 +10pp を検証する。

PURPOSE: TinyLlama 1.1B (凍結) + Structural Attention 追加層を訓練。
  5-fold CV + 3条件アブレーション (C1/C2/C3) + Permutation Test。

実行例:
  # dry-run (疎通テスト)
  python train_structural_attention.py --dry-run --max-pairs 10

  # CodeBERT で本番実行 (TPU v6e)
  python train_structural_attention.py --model codebert --epochs 50

  # TinyLlama で本番実行
  python train_structural_attention.py --model TinyLlama/TinyLlama-1.1B-Chat-v1.0 --epochs 50

  # 3条件アブレーション
  python train_structural_attention.py --ablation --model codebert --epochs 30
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

# 遅延 import
torch = None
nn = None


def _ensure_torch():
    global torch, nn
    if torch is None:
        import torch as _torch
        import torch.nn as _nn
        torch = _torch
        nn = _nn


# ============================================================
# データ構造
# ============================================================

@dataclass
class TrainingPair:
    """訓練用ペアデータ。"""
    pair_id: str
    func_a_source: str
    func_b_source: str
    func_a_ccl: str
    func_b_ccl: str
    ccl_similarity: float
    length_ratio: float
    pair_type: str
    is_positive: bool


def load_dataset(path: Path) -> list[TrainingPair]:
    """dataset_v3.json を読み込む。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs = []
    for p in data["pairs"]:
        pairs.append(TrainingPair(
            pair_id=p["pair_id"],
            func_a_source=p["func_a_source"],
            func_b_source=p["func_b_source"],
            func_a_ccl=p.get("func_a_ccl", ""),
            func_b_ccl=p.get("func_b_ccl", ""),
            ccl_similarity=p["ccl_similarity"],
            length_ratio=p["length_ratio"],
            pair_type=p["pair_type"],
            is_positive=p["is_positive"],
        ))
    return pairs


# ============================================================
# Hidden State 抽出 (nonlinear_probe.py から流用)
# ============================================================

def _source_hash(code: str) -> str:
    """ソースコードのハッシュ値。"""
    return hashlib.sha256(code.encode()).hexdigest()[:16]


def extract_hidden_states(code: str, model, tokenizer, device, max_length=512):
    """全層の token-level hidden state を抽出。"""
    _ensure_torch()
    inputs = tokenizer(
        code, return_tensors="pt", truncation=True,
        max_length=max_length, padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)

    hidden_states = outputs.hidden_states
    mask = inputs["attention_mask"][0]
    seq_len = mask.sum().item()

    # 各層: (seq_len, hidden_dim)
    return [hs[0, :seq_len, :].cpu().float().numpy() for hs in hidden_states]


def get_or_cache_hiddens(
    code: str, model, tokenizer, device, cache_dir: Path, max_length=512
) -> list[np.ndarray]:
    """キャッシュ付き hidden state 抽出。"""
    import tempfile, os
    key = _source_hash(code)
    cache_file = cache_dir / f"{key}.npz"

    if cache_file.exists():
        try:
            data = np.load(cache_file)
            return [data[f"layer_{i}"] for i in range(len(data.files))]
        except Exception:
            cache_file.unlink(missing_ok=True)

    hiddens = extract_hidden_states(code, model, tokenizer, device, max_length)
    save_dict = {f"layer_{i}": h for i, h in enumerate(hiddens)}
    fd, tmp_path = tempfile.mkstemp(dir=str(cache_dir), suffix=".npz")
    try:
        os.close(fd)
        np.savez_compressed(tmp_path, **save_dict)
        Path(tmp_path).rename(cache_file)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    return hiddens


# ============================================================
# モデルロード
# ============================================================

def load_llm(model_name: str, bits: int = 0):
    """LLM をロード (凍結)。structural_probe.py 互換。"""
    _ensure_torch()
    from transformers import AutoModel, AutoTokenizer

    print(f"🔧 モデルロード: {model_name}")

    if "codebert" in model_name.lower():
        model_id = "microsoft/codebert-base"
    elif "tinyllama" in model_name.lower():
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    else:
        model_id = model_name

    tokenizer = AutoTokenizer.from_pretrained(model_id)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    kwargs = {"output_hidden_states": True}
    if bits == 4:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16
        )
    elif bits == 8:
        from transformers import BitsAndBytesConfig
        kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
    else:
        kwargs["torch_dtype"] = torch.bfloat16

    model = AutoModel.from_pretrained(model_id, **kwargs)

    device = "cpu"
    if torch.cuda.is_available():
        device = "cuda"
        if bits == 0:
            model = model.to(device)
    # TPU/XLA
    try:
        import torch_xla.core.xla_model as xm
        device = xm.xla_device()
        if bits == 0:
            model = model.to(device)
        print(f"  → TPU デバイス: {device}")
    except ImportError:
        pass

    model.eval()
    for param in model.parameters():
        param.requires_grad = False

    n_layers = model.config.num_hidden_layers
    hidden_dim = model.config.hidden_size
    print(f"  → {model_id} ({n_layers} 層, {hidden_dim}d, params={sum(p.numel() for p in model.parameters()):,})")

    return model, tokenizer, device, n_layers, hidden_dim


# ============================================================
# 訓練ループ
# ============================================================

def train_one_fold(
    sa_model,
    train_pairs: list[TrainingPair],
    hiddens_map: dict,
    ccl_tokenize_fn,
    target_layer: int,
    n_epochs: int = 50,
    lr: float = 1e-4,
) -> float:
    """1 fold の訓練。"""
    _ensure_torch()
    from structural_attention import tokenize_ccl

    optimizer = torch.optim.AdamW(sa_model.parameters(), lr=lr, weight_decay=1e-2)
    loss_fn = nn.MSELoss()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs)

    sa_model.train()
    best_loss = float("inf")

    for epoch in range(n_epochs):
        total_loss = 0.0
        n_samples = 0
        np.random.shuffle(train_pairs)

        for pair in train_pairs:
            key_a = _source_hash(pair.func_a_source)
            key_b = _source_hash(pair.func_b_source)

            if key_a not in hiddens_map or key_b not in hiddens_map:
                continue

            optimizer.zero_grad()

            # hidden states → torch tensor (1, seq, hidden_dim)
            hs_a = torch.from_numpy(hiddens_map[key_a]).unsqueeze(0).float()
            hs_b = torch.from_numpy(hiddens_map[key_b]).unsqueeze(0).float()

            # CCL トークン (注入用)
            ccl_ids_a = torch.tensor([tokenize_ccl(pair.func_a_ccl)])
            ccl_ids_b = torch.tensor([tokenize_ccl(pair.func_b_ccl)])

            # デバイスに転送
            device = sa_model._device
            hs_a = hs_a.to(device)
            hs_b = hs_b.to(device)
            ccl_ids_a = ccl_ids_a.to(device)
            ccl_ids_b = ccl_ids_b.to(device)

            # フォワード
            pred = sa_model.forward(hs_a, hs_b, ccl_ids_a, ccl_ids_b)
            target = torch.tensor([pair.ccl_similarity], dtype=torch.float32, device=device)

            loss = loss_fn(pred, target)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(sa_model.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss += loss.item()
            n_samples += 1

        scheduler.step()
        avg_loss = total_loss / max(n_samples, 1)
        if avg_loss < best_loss:
            best_loss = avg_loss

        if (epoch + 1) % 10 == 0:
            print(f"    Epoch {epoch+1}/{n_epochs}: loss={avg_loss:.4f} (best={best_loss:.4f})")

    return best_loss


def evaluate_fold(
    sa_model,
    test_pairs: list[TrainingPair],
    hiddens_map: dict,
    target_layer: int,
) -> dict:
    """1 fold の評価。Spearman ρ + recall@k。"""
    _ensure_torch()
    from scipy import stats
    from structural_attention import tokenize_ccl

    sa_model.eval()
    predictions = []
    actuals = []
    lengths = []

    with torch.no_grad():
        for pair in test_pairs:
            key_a = _source_hash(pair.func_a_source)
            key_b = _source_hash(pair.func_b_source)
            if key_a not in hiddens_map or key_b not in hiddens_map:
                continue

            hs_a = torch.from_numpy(hiddens_map[key_a]).unsqueeze(0).float()
            hs_b = torch.from_numpy(hiddens_map[key_b]).unsqueeze(0).float()
            ccl_ids_a = torch.tensor([tokenize_ccl(pair.func_a_ccl)])
            ccl_ids_b = torch.tensor([tokenize_ccl(pair.func_b_ccl)])

            device = sa_model._device
            hs_a = hs_a.to(device)
            hs_b = hs_b.to(device)
            ccl_ids_a = ccl_ids_a.to(device)
            ccl_ids_b = ccl_ids_b.to(device)

            pred = sa_model.forward(hs_a, hs_b, ccl_ids_a, ccl_ids_b)
            predictions.append(pred.item())
            actuals.append(pair.ccl_similarity)
            lengths.append(pair.length_ratio)

    if len(predictions) < 5:
        return {"rho": 0.0, "partial_rho": 0.0, "n": len(predictions)}

    predictions = np.array(predictions)
    actuals = np.array(actuals)
    lengths = np.array(lengths)

    # 定数出力チェック
    if np.std(predictions) < 1e-8:
        return {"rho": 0.0, "partial_rho": 0.0, "n": len(predictions)}

    # Spearman ρ
    rho, rho_p = stats.spearmanr(predictions, actuals)
    if np.isnan(rho):
        rho, rho_p = 0.0, 1.0

    # 偏 ρ (コード長除去)
    rho_pl, _ = stats.spearmanr(predictions, lengths)
    rho_al, _ = stats.spearmanr(actuals, lengths)
    if np.isnan(rho_pl): rho_pl = 0.0
    if np.isnan(rho_al): rho_al = 0.0
    denom = np.sqrt((1 - rho_pl**2) * (1 - rho_al**2))
    partial_rho = (rho - rho_pl * rho_al) / denom if denom > 1e-10 else 0.0

    # recall@k (正例ペアが上位 k に入るか)
    positive_mask = np.array([p.is_positive for p in test_pairs
                              if _source_hash(p.func_a_source) in hiddens_map
                              and _source_hash(p.func_b_source) in hiddens_map])
    if len(positive_mask) > 0 and positive_mask.sum() > 0:
        sorted_idx = np.argsort(-predictions)  # 類似度降順
        recall_at_1 = float(positive_mask[sorted_idx[0]]) if len(sorted_idx) > 0 else 0.0
        top3 = sorted_idx[:3] if len(sorted_idx) >= 3 else sorted_idx
        recall_at_3 = float(positive_mask[top3].sum() / min(3, positive_mask.sum()))
    else:
        recall_at_1 = 0.0
        recall_at_3 = 0.0

    mse = float(np.mean((predictions - actuals) ** 2))

    return {
        "rho": float(rho), "rho_p": float(rho_p),
        "partial_rho": float(partial_rho),
        "mse": mse, "n": len(predictions),
        "recall_at_1": recall_at_1,
        "recall_at_3": recall_at_3,
    }


def run_cv(
    mode: str,
    pairs: list[TrainingPair],
    hiddens_map: dict,
    hidden_dim: int,
    target_layer: int,
    n_folds: int = 5,
    n_epochs: int = 50,
    seed: int = 42,
) -> dict:
    """5-fold CV を実行。"""
    _ensure_torch()
    from sklearn.model_selection import StratifiedKFold
    from structural_attention import StructuralAttentionModel, StructuralAttentionConfig

    config = StructuralAttentionConfig(hidden_dim=hidden_dim)
    labels = [1 if p.is_positive else 0 for p in pairs]
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

    fold_results = []

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(pairs, labels)):
        train_pairs = [pairs[i] for i in train_idx]
        test_pairs = [pairs[i] for i in test_idx]

        print(f"\n  Fold {fold_idx+1}/{n_folds} ({mode})")

        # 毎 fold 新規モデル
        model = StructuralAttentionModel(config, mode=mode)
        device = torch.device("cpu")
        if torch.cuda.is_available():
            device = torch.device("cuda")
        try:
            import torch_xla.core.xla_model as xm
            device = xm.xla_device()
        except ImportError:
            pass
        model.to(device)

        # 訓練
        train_loss = train_one_fold(
            model, train_pairs, hiddens_map, None, target_layer,
            n_epochs=n_epochs,
        )

        # 評価
        result = evaluate_fold(model, test_pairs, hiddens_map, target_layer)
        result["fold"] = fold_idx
        result["train_loss"] = train_loss
        fold_results.append(result)

        print(f"    ρ={result['rho']:.3f}, 偏ρ={result['partial_rho']:.3f}, "
              f"recall@1={result.get('recall_at_1', 0):.2f}")

        # メモリ解放
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # 集計
    mean_rho = float(np.nanmean([r["rho"] for r in fold_results]))
    mean_partial = float(np.nanmean([r["partial_rho"] for r in fold_results]))
    mean_recall1 = float(np.nanmean([r.get("recall_at_1", 0) for r in fold_results]))

    return {
        "mode": mode,
        "n_folds": n_folds,
        "mean_rho": mean_rho,
        "mean_partial_rho": mean_partial,
        "mean_recall_at_1": mean_recall1,
        "folds": fold_results,
    }


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Phase C-mini: Structural Attention 訓練")
    parser.add_argument("--dataset", default="dataset_v3.json", help="データセット JSON パス")
    parser.add_argument("--model", default="codebert", help="LLM モデル (codebert, tinyllama)")
    parser.add_argument("--bits", type=int, default=0, help="量子化 (0=デフォルト, 4, 8)")
    parser.add_argument("--layer", type=int, default=-1, help="ターゲット層 (-1=最終)")
    parser.add_argument("--epochs", type=int, default=50, help="訓練エポック数")
    parser.add_argument("--folds", type=int, default=5, help="CV fold 数")
    parser.add_argument("--max-pairs", type=int, default=0, help="最大ペア数 (0=全件)")
    parser.add_argument("--ablation", action="store_true", help="3条件アブレーション実行")
    parser.add_argument("--dry-run", action="store_true", help="疎通テスト (少数ペア)")
    parser.add_argument("--cache-dir", default=".hidden_cache", help="hidden state キャッシュ")
    parser.add_argument("--output", default="phase_c_mini_results.json", help="結果出力")
    args = parser.parse_args()

    if args.dry_run:
        args.max_pairs = args.max_pairs or 10
        args.epochs = min(args.epochs, 3)
        args.folds = min(args.folds, 2)
        print("🧪 DRY RUN モード (疎通テスト)")

    _ensure_torch()

    # --- データセット ---
    dataset_path = Path(args.dataset)
    print(f"\n📂 データセット: {dataset_path}")
    pairs = load_dataset(dataset_path)
    if args.max_pairs > 0:
        pairs = pairs[:args.max_pairs]
    print(f"  → {len(pairs)} ペア")

    # --- LLM ロード + hidden state 抽出 ---
    model, tokenizer, device, n_layers, hidden_dim = load_llm(args.model, args.bits)
    target_layer = args.layer if args.layer >= 0 else n_layers

    cache_dir = Path(args.cache_dir) / args.model.split("/")[-1].lower()
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📦 Hidden state 抽出 (L{target_layer}, キャッシュ: {cache_dir})...")
    all_sources = set()
    for p in pairs:
        all_sources.add(p.func_a_source)
        all_sources.add(p.func_b_source)

    hiddens_map = {}
    skipped = 0
    for i, source in enumerate(all_sources):
        key = _source_hash(source)
        if key not in hiddens_map:
            try:
                hiddens = get_or_cache_hiddens(source, model, tokenizer, device, cache_dir)
                hiddens_map[key] = hiddens[target_layer]
            except Exception as e:
                print(f"  ⚠️ {key}: {e}")
                skipped += 1
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(all_sources)} 処理済み")
    print(f"  → {len(hiddens_map)} 関数 (スキップ: {skipped})")

    # LLM 解放
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # --- 訓練 ---
    results = {}

    if args.ablation:
        # 3条件アブレーション
        modes = ["explicit_only", "injection_only", "hybrid"]
    else:
        modes = ["hybrid"]

    for mode in modes:
        print(f"\n{'='*60}")
        print(f"  Mode: {mode}")
        print(f"{'='*60}")

        result = run_cv(
            mode, pairs, hiddens_map,
            hidden_dim, target_layer,
            n_folds=args.folds, n_epochs=args.epochs,
        )
        results[mode] = result

        print(f"\n  📊 {mode}: ρ={result['mean_rho']:.3f}, "
              f"偏ρ={result['mean_partial_rho']:.3f}, "
              f"recall@1={result['mean_recall_at_1']:.2f}")

    # --- 結果まとめ ---
    print(f"\n{'='*60}")
    print(f"  結果まとめ")
    print(f"{'='*60}")
    print(f"  {'Mode':<20} | {'ρ':>6} | {'偏ρ':>6} | {'R@1':>5}")
    print(f"  {'-'*20}-+-{'-'*6}-+-{'-'*6}-+-{'-'*5}")

    # Phase B2 ベースライン
    print(f"  {'Phase B2 (attentive)':<20} | {'0.745':>6} | {'0.740':>6} | {'N/A':>5}")

    for mode, result in results.items():
        print(f"  {mode:<20} | {result['mean_rho']:6.3f} | "
              f"{result['mean_partial_rho']:6.3f} | "
              f"{result['mean_recall_at_1']:5.2f}")

    # 成功判定
    if "hybrid" in results:
        hr = results["hybrid"]
        recall_improvement = hr["mean_recall_at_1"] - 0.0  # ベースライン recall@1 不明なので仮
        rho_improvement = hr["mean_rho"] - 0.745  # Phase B2 比
        print(f"\n📋 仮説判定:")
        print(f"  P11 (ρ > Phase B2):     {'✅' if rho_improvement > 0 else '❌'} (Δρ={rho_improvement:+.3f})")
        if "explicit_only" in results and "injection_only" in results:
            hybrid_better = hr["mean_rho"] > max(
                results["explicit_only"]["mean_rho"],
                results["injection_only"]["mean_rho"]
            )
            print(f"  ハイブリッド優位:       {'✅' if hybrid_better else '❌'}")

    # --- 保存 ---
    output = {
        "model": args.model,
        "target_layer": target_layer,
        "hidden_dim": hidden_dim,
        "n_pairs": len(pairs),
        "ablation": args.ablation,
        "results": {k: {kk: vv for kk, vv in v.items() if kk != "folds"}
                    for k, v in results.items()},
        "detailed_results": results,
    }
    output_path = Path(args.output)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n💾 結果保存: {output_path}")


if __name__ == "__main__":
    main()
