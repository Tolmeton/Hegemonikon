#!/usr/bin/env python3
"""Phase B2: Non-linear Probing — Attentive Pooling + Structural Head.

PROOF: Phase B (structural_probe.py) の構造的限界を解決する。
  mean-pooled cosine の 45% がコード長の交絡 (偏 ρ=0.474) であることを
  非線形プロービングで克服し、真の構造理解度を測定する。

PURPOSE: Code LLM の hidden state から CCL 類似度を予測する
  非線形 probe を学習し、Phase B の linear probe と比較する。

アーキテクチャ:
  Code → [Frozen LLM] → hidden_states (L×S×D)
       → [AttentivePooling] (learnable query × cross-attention)
       → weighted_repr (D)
       → [StructuralHead] (MLP: |a-b|, a*b → 64 → 1)
       → predicted_similarity → MSE vs CCL similarity
"""
from __future__ import annotations

import argparse
import json
import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# 遅延 import (GPU 環境依存)
torch = None  # type: ignore
nn = None  # type: ignore
F_torch = None  # type: ignore


def _ensure_torch():
    """PyTorch の遅延インポート。"""
    global torch, nn, F_torch
    if torch is None:
        import torch as _torch
        import torch.nn as _nn
        import torch.nn.functional as _F
        torch = _torch
        nn = _nn
        F_torch = _F


# ============================================================
# データ構造
# ============================================================

@dataclass
class ProbePair:
    """1つのペアのデータ。"""
    pair_id: str
    func_a_source: str
    func_b_source: str
    ccl_similarity: float
    length_ratio: float
    pair_type: str
    is_positive: bool


@dataclass
class HiddenCache:
    """1つの関数の全層 hidden state キャッシュ。"""
    func_key: str  # source の hash
    # 各層: (seq_len, hidden_dim) の token-level hidden state
    layer_hiddens: list[np.ndarray] = field(default_factory=list)


# ============================================================
# Hidden State 抽出 (token-level — mean-pool しない)
# ============================================================

# PURPOSE: 1つのコードスニペットの全層 hidden state を抽出 (token-level)
def extract_token_hidden_states(
    code: str, model, tokenizer, device, max_length: int = 512
) -> list[np.ndarray]:
    """各層の token-level hidden state (numpy array) を返す。

    Returns:
        list[np.ndarray] — (n_layers + 1) 個, 各 (seq_len, hidden_dim)
    """
    _ensure_torch()

    inputs = tokenizer(
        code, return_tensors="pt", truncation=True,
        max_length=max_length, padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True)

    hidden_states = outputs.hidden_states
    mask = inputs["attention_mask"][0]  # (seq_len,)
    seq_len = mask.sum().item()  # パディングを除く実トークン数

    # 各層: padding を除いた (seq_len, hidden_dim)
    result = []
    for layer_hs in hidden_states:
        hs = layer_hs[0, :seq_len, :].cpu().float().numpy()  # (seq_len, hidden_dim)
        result.append(hs)

    return result


# PURPOSE: ソースコードの hash を生成
def _source_hash(code: str) -> str:
    """ソースコードのハッシュ値 (キャッシュキー)。"""
    return hashlib.sha256(code.encode()).hexdigest()[:16]


# PURPOSE: hidden state をキャッシュから読むか新規抽出する
def get_or_extract_hiddens(
    code: str,
    model, tokenizer, device,
    cache_dir: Path,
    max_length: int = 512,
) -> list[np.ndarray]:
    """キャッシュがあればロード、なければ抽出して保存。"""
    import tempfile
    key = _source_hash(code)
    cache_file = cache_dir / f"{key}.npz"

    if cache_file.exists():
        try:
            data = np.load(cache_file)
            return [data[f"layer_{i}"] for i in range(len(data.files))]
        except Exception:
            # 破損ファイル → 削除して再抽出
            cache_file.unlink(missing_ok=True)

    hiddens = extract_token_hidden_states(code, model, tokenizer, device, max_length)

    # アトミック書き込み (temp → rename)
    save_dict = {f"layer_{i}": h for i, h in enumerate(hiddens)}
    fd, tmp_path = tempfile.mkstemp(dir=str(cache_dir), suffix=".npz")
    try:
        import os
        os.close(fd)
        np.savez_compressed(tmp_path, **save_dict)
        Path(tmp_path).rename(cache_file)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise

    return hiddens


# ============================================================
# Probe モデル
# ============================================================

class AttentivePooling(object):
    """Learnable query × cross-attention で token-level hidden を集約。

    PyTorch nn.Module として動作する (遅延インポート対応)。
    """

    def __init__(self, hidden_dim: int, n_queries: int = 4):
        _ensure_torch()
        self.module = _AttentivePoolingModule(hidden_dim, n_queries)

    def __call__(self, hidden_states):
        return self.module(hidden_states)

    def parameters(self):
        return self.module.parameters()

    def to(self, device):
        self.module = self.module.to(device)
        return self

    def train(self):
        self.module.train()

    def eval(self):
        self.module.eval()


def _build_attentive_pooling_module():
    """nn.Module のクラスを動的に生成 (import 順序対応)。"""
    _ensure_torch()

    class _AttentivePoolingModule(nn.Module):
        """Cross-attention ベースの集約。"""

        def __init__(self, hidden_dim: int, n_queries: int = 4):
            super().__init__()
            self.queries = nn.Parameter(torch.randn(1, n_queries, hidden_dim) * 0.02)
            self.attn = nn.MultiheadAttention(hidden_dim, num_heads=4, batch_first=True)
            self.norm = nn.LayerNorm(hidden_dim)

        def forward(self, hidden_states):
            """
            Args:
                hidden_states: (batch, seq_len, hidden_dim)
            Returns:
                pooled: (batch, hidden_dim)
            """
            batch_size = hidden_states.size(0)
            queries = self.queries.expand(batch_size, -1, -1)
            attn_out, attn_weights = self.attn(queries, hidden_states, hidden_states)
            # n_queries 個の出力を mean して 1 つのベクトルに
            pooled = self.norm(attn_out.mean(dim=1))
            return pooled, attn_weights

    return _AttentivePoolingModule

# 遅延クラス定義
_AttentivePoolingModule = None


def _ensure_attentive_module():
    global _AttentivePoolingModule
    if _AttentivePoolingModule is None:
        _AttentivePoolingModule = _build_attentive_pooling_module()


class StructuralHead(object):
    """Probe head: |a-b|, a*b → MLP → similarity score."""

    def __init__(self, hidden_dim: int, intermediate_dim: int = 64):
        _ensure_torch()
        self.module = _build_structural_head(hidden_dim, intermediate_dim)

    def __call__(self, repr_a, repr_b):
        return self.module(repr_a, repr_b)

    def parameters(self):
        return self.module.parameters()

    def to(self, device):
        self.module = self.module.to(device)
        return self

    def train(self):
        self.module.train()

    def eval(self):
        self.module.eval()


def _build_structural_head(hidden_dim: int, intermediate_dim: int = 64):
    _ensure_torch()

    class _StructuralHeadModule(nn.Module):
        def __init__(self):
            super().__init__()
            # |a-b| と a*b を連結 → 2*hidden_dim 入力
            self.mlp = nn.Sequential(
                nn.Linear(hidden_dim * 2, intermediate_dim),
                nn.ReLU(),
                nn.Dropout(0.2),
                nn.Linear(intermediate_dim, 1),
                nn.Sigmoid(),  # 出力を [0, 1] に制約 (similarity)
            )

        def forward(self, repr_a, repr_b):
            diff = torch.abs(repr_a - repr_b)
            product = repr_a * repr_b
            combined = torch.cat([diff, product], dim=-1)
            return self.mlp(combined).squeeze(-1)

    return _StructuralHeadModule()


class NonlinearProbe(object):
    """統合 Probe: AttentivePooling + StructuralHead。"""

    def __init__(self, hidden_dim: int, target_layer: int = -1,
                 n_queries: int = 4, intermediate_dim: int = 64):
        _ensure_torch()
        _ensure_attentive_module()
        self.target_layer = target_layer
        self.pooling = AttentivePooling(hidden_dim, n_queries)
        self.head = StructuralHead(hidden_dim, intermediate_dim)

    def parameters(self):
        return list(self.pooling.parameters()) + list(self.head.parameters())

    def to(self, device):
        self.pooling.to(device)
        self.head.to(device)
        return self

    def train(self):
        self.pooling.train()
        self.head.train()

    def eval(self):
        self.pooling.eval()
        self.head.eval()

    def forward(self, hs_a_np: np.ndarray, hs_b_np: np.ndarray):
        """
        Args:
            hs_a_np: np.ndarray (seq_len, hidden_dim) — target_layer のみ
            hs_b_np: np.ndarray (seq_len, hidden_dim) — target_layer のみ
        Returns:
            predicted_similarity: scalar tensor
        """
        hs_a = torch.from_numpy(hs_a_np).unsqueeze(0).float()
        hs_b = torch.from_numpy(hs_b_np).unsqueeze(0).float()

        # GPU に転送
        device = next(self.pooling.parameters()).device
        hs_a = hs_a.to(device)
        hs_b = hs_b.to(device)

        # Attentive Pooling
        repr_a, attn_a = self.pooling(hs_a)
        repr_b, attn_b = self.pooling(hs_b)

        # Structural Head
        similarity = self.head(repr_a, repr_b)

        return similarity, attn_a, attn_b


class MeanPoolBaseline(object):
    """ベースライン: mean-pool → MLP (attention なし)。"""

    def __init__(self, hidden_dim: int, target_layer: int = -1,
                 intermediate_dim: int = 64):
        _ensure_torch()
        self.target_layer = target_layer
        self.head = StructuralHead(hidden_dim, intermediate_dim)

    def parameters(self):
        return list(self.head.parameters())

    def to(self, device):
        self.head.to(device)
        return self

    def train(self):
        self.head.train()

    def eval(self):
        self.head.eval()

    def forward(self, hs_a_np: np.ndarray, hs_b_np: np.ndarray):
        """Mean-pool → StructuralHead。
        Args:
            hs_a_np: np.ndarray (seq_len, hidden_dim) — target_layer のみ
            hs_b_np: np.ndarray (seq_len, hidden_dim) — target_layer のみ
        """
        # mean pooling
        repr_a = torch.from_numpy(hs_a_np.mean(axis=0)).unsqueeze(0).float()
        repr_b = torch.from_numpy(hs_b_np.mean(axis=0)).unsqueeze(0).float()

        device = next(self.head.parameters()).device
        repr_a = repr_a.to(device)
        repr_b = repr_b.to(device)

        similarity = self.head(repr_a, repr_b)

        return similarity, None, None


# ============================================================
# 学習 + 5-fold CV
# ============================================================

# PURPOSE: 1 fold の学習を実行
def train_one_fold(
    probe, train_pairs, hiddens_map, n_epochs: int = 50, lr: float = 1e-3,
) -> float:
    """1 fold の学習。MSE loss で CCL similarity を予測する回帰タスク。"""
    _ensure_torch()

    optimizer = torch.optim.Adam(probe.parameters(), lr=lr, weight_decay=1e-4)
    loss_fn = nn.MSELoss()

    probe.train()
    best_loss = float("inf")

    for epoch in range(n_epochs):
        total_loss = 0.0
        np.random.shuffle(train_pairs)

        for pair in train_pairs:
            key_a = _source_hash(pair.func_a_source)
            key_b = _source_hash(pair.func_b_source)

            if key_a not in hiddens_map or key_b not in hiddens_map:
                continue

            optimizer.zero_grad()

            pred, _, _ = probe.forward(hiddens_map[key_a], hiddens_map[key_b])
            target = torch.tensor([pair.ccl_similarity], dtype=torch.float32)
            target = target.to(pred.device)

            loss = loss_fn(pred, target)
            loss.backward()
            # Gradient clipping で学習を安定化
            torch.nn.utils.clip_grad_norm_(probe.parameters(), max_norm=1.0)
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / max(len(train_pairs), 1)
        if avg_loss < best_loss:
            best_loss = avg_loss

    return best_loss


# PURPOSE: テストセットで評価
def evaluate_fold(
    probe, test_pairs, hiddens_map,
) -> dict:
    """1 fold のテスト評価。Spearman ρ + 偏 ρ (長さ除去) を計算。"""
    _ensure_torch()
    from scipy import stats

    probe.eval()
    predictions = []
    actuals = []
    lengths = []

    with torch.no_grad():
        for pair in test_pairs:
            key_a = _source_hash(pair.func_a_source)
            key_b = _source_hash(pair.func_b_source)

            if key_a not in hiddens_map or key_b not in hiddens_map:
                continue

            pred, _, _ = probe.forward(hiddens_map[key_a], hiddens_map[key_b])
            predictions.append(pred.item())
            actuals.append(pair.ccl_similarity)
            lengths.append(pair.length_ratio)

    if len(predictions) < 5:
        return {"rho": 0.0, "rho_p": 1.0, "partial_rho": 0.0, "n": len(predictions)}

    predictions = np.array(predictions)
    actuals = np.array(actuals)
    lengths = np.array(lengths)

    # 定数出力チェック (全予測値が同一 → probe が退化)
    if np.std(predictions) < 1e-8:
        print(f"    ⚠️ 予測が定数 (std={np.std(predictions):.2e})。ρ=0.0 にフォールバック")
        mse = float(np.mean((predictions - actuals) ** 2))
        return {"rho": 0.0, "rho_p": 1.0, "partial_rho": 0.0, "mse": mse, "n": len(predictions)}

    # Spearman ρ
    rho, rho_p = stats.spearmanr(predictions, actuals)
    if np.isnan(rho):
        rho, rho_p = 0.0, 1.0

    # 偏 Spearman ρ (コード長除去)
    # ρ(pred, actual | length) = (ρ_pa - ρ_pl * ρ_al) / sqrt((1 - ρ_pl²)(1 - ρ_al²))
    rho_pl, _ = stats.spearmanr(predictions, lengths)
    rho_al, _ = stats.spearmanr(actuals, lengths)
    if np.isnan(rho_pl):
        rho_pl = 0.0
    if np.isnan(rho_al):
        rho_al = 0.0

    denom = np.sqrt((1 - rho_pl**2) * (1 - rho_al**2))
    if denom > 1e-10:
        partial_rho = (rho - rho_pl * rho_al) / denom
    else:
        partial_rho = 0.0

    # MSE
    mse = float(np.mean((predictions - actuals) ** 2))

    return {
        "rho": float(rho),
        "rho_p": float(rho_p),
        "partial_rho": float(partial_rho),
        "mse": mse,
        "n": len(predictions),
    }


# PURPOSE: 5-fold CV を実行
def run_cv(
    probe_class: str,
    pairs: list[ProbePair],
    hiddens_map: dict,
    hidden_dim: int,
    target_layer: int,
    n_folds: int = 5,
    n_epochs: int = 50,
    seed: int = 42,
) -> dict:
    """5-fold CV を実行し、平均 Spearman ρ を返す。"""
    _ensure_torch()
    from sklearn.model_selection import StratifiedKFold

    # ペアのラベル (positive/negative) で層化分割
    labels = [1 if p.is_positive else 0 for p in pairs]
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

    fold_results = []

    for fold_idx, (train_idx, test_idx) in enumerate(skf.split(pairs, labels)):
        train_pairs = [pairs[i] for i in train_idx]
        test_pairs = [pairs[i] for i in test_idx]

        # Probe を新規作成 (各 fold で独立)
        if probe_class == "attentive":
            probe = NonlinearProbe(hidden_dim, target_layer)
        else:
            probe = MeanPoolBaseline(hidden_dim, target_layer)

        device = torch.device("cpu")  # 小さいモデルなので CPU で十分
        probe.to(device)

        # 学習
        train_loss = train_one_fold(probe, train_pairs, hiddens_map, n_epochs)

        # 評価
        result = evaluate_fold(probe, test_pairs, hiddens_map)
        result["fold"] = fold_idx
        result["train_loss"] = train_loss
        fold_results.append(result)

        print(f"  Fold {fold_idx}: ρ={result['rho']:.3f}, "
              f"偏ρ={result['partial_rho']:.3f}, "
              f"MSE={result.get('mse', 0):.4f}, n={result['n']}")

    # 集計 (nan 安全)
    rhos = [r["rho"] for r in fold_results]
    partials = [r["partial_rho"] for r in fold_results]
    mses = [r.get("mse", 0) for r in fold_results]
    mean_rho = float(np.nanmean(rhos))
    mean_partial = float(np.nanmean(partials))
    mean_mse = float(np.nanmean(mses))

    return {
        "probe_class": probe_class,
        "target_layer": target_layer,
        "n_folds": n_folds,
        "n_epochs": n_epochs,
        "mean_rho": float(mean_rho),
        "mean_partial_rho": float(mean_partial),
        "mean_mse": float(mean_mse),
        "folds": fold_results,
    }


# PURPOSE: Permutation test
def permutation_test(
    probe_class: str,
    pairs: list[ProbePair],
    hiddens_map: dict,
    hidden_dim: int,
    target_layer: int,
    observed_rho: float,
    n_permutations: int = 100,
    seed: int = 42,
) -> float:
    """ρ の有意性を permutation test で検証。"""
    rng = np.random.RandomState(seed)
    count_above = 0

    for i in range(n_permutations):
        # CCL similarity をシャッフル
        shuffled = [ProbePair(
            pair_id=p.pair_id,
            func_a_source=p.func_a_source,
            func_b_source=p.func_b_source,
            ccl_similarity=pairs[rng.randint(len(pairs))].ccl_similarity,  # ランダム入替
            length_ratio=p.length_ratio,
            pair_type=p.pair_type,
            is_positive=p.is_positive,
        ) for p in pairs]

        result = run_cv(
            probe_class, shuffled, hiddens_map,
            hidden_dim, target_layer,
            n_folds=3, n_epochs=20, seed=seed + i,
        )

        if result["mean_rho"] >= observed_rho:
            count_above += 1

        if (i + 1) % 20 == 0:
            print(f"  Permutation {i+1}/{n_permutations}: "
                  f"p ≈ {count_above / (i + 1):.3f}")

    return count_above / n_permutations


# ============================================================
# Main
# ============================================================

def load_dataset(path: Path) -> list[ProbePair]:
    """データセット JSON を読み込む。"""
    data = json.loads(path.read_text(encoding="utf-8"))
    pairs = []
    for p in data["pairs"]:
        pairs.append(ProbePair(
            pair_id=p["pair_id"],
            func_a_source=p["func_a_source"],
            func_b_source=p["func_b_source"],
            ccl_similarity=p["ccl_similarity"],
            length_ratio=p["length_ratio"],
            pair_type=p["pair_type"],
            is_positive=p["is_positive"],
        ))
    return pairs


def main():
    parser = argparse.ArgumentParser(description="Phase B2: Non-linear Probing")
    parser.add_argument(
        "--dataset", type=str, default="dataset_v3.json",
        help="データセット JSON パス",
    )
    parser.add_argument(
        "--model", type=str, default="codebert",
        help="モデルキー (codebert, codellama, mistral)",
    )
    parser.add_argument(
        "--bits", type=int, default=0,
        help="量子化ビット数 (0=デフォルト, 4, 8)",
    )
    parser.add_argument(
        "--layer", type=int, default=-1,
        help="ターゲット層 (-1 = 最終層)",
    )
    parser.add_argument(
        "--epochs", type=int, default=50,
        help="学習エポック数",
    )
    parser.add_argument(
        "--folds", type=int, default=5,
        help="CV fold 数",
    )
    parser.add_argument(
        "--permutations", type=int, default=100,
        help="Permutation test の回数 (0 = スキップ)",
    )
    parser.add_argument(
        "--output", type=str, default="phase_b2_results.json",
        help="結果出力 JSON パス",
    )
    parser.add_argument(
        "--cache-dir", type=str, default=".hidden_cache",
        help="Hidden state キャッシュディレクトリ",
    )
    args = parser.parse_args()

    _ensure_torch()

    # --- データセット読み込み ---
    dataset_path = Path(args.dataset)
    print(f"📂 データセット: {dataset_path}")
    pairs = load_dataset(dataset_path)
    print(f"  → {len(pairs)} ペア")

    # --- モデルロード (キャッシュ全件時はスキップ可能) ---
    import sys
    sys.path.insert(0, str(Path(__file__).parent))

    model_key = args.model.split("/")[-1]
    target_layer = args.layer  # 暫定値 (モデルロード後に再解決)

    # キャッシュディレクトリ
    cache_dir = Path(args.cache_dir) / model_key
    cache_dir.mkdir(parents=True, exist_ok=True)

    # 全ソース関数のキーを収集
    all_sources = set()
    for p in pairs:
        all_sources.add(p.func_a_source)
        all_sources.add(p.func_b_source)

    # キャッシュ充足率を確認 (モデルロードが必要かどうか判定)
    cached_keys = set()
    for source in all_sources:
        key = _source_hash(source)
        cache_path = cache_dir / f"{key}.npz"
        if cache_path.exists():
            cached_keys.add(key)

    all_keys = {_source_hash(s) for s in all_sources}
    missing_keys = all_keys - cached_keys
    print(f"\n📦 キャッシュ状況: {len(cached_keys)}/{len(all_keys)} 関数 (不足: {len(missing_keys)})")

    model = None
    tokenizer = None
    device = "cpu"

    if missing_keys:
        # 不足分があるのでモデルロードを試みる
        try:
            from structural_probe import load_model
            print(f"\n🔧 モデルロード: {args.model} ({len(missing_keys)} 関数の抽出が必要)")
            model, tokenizer, device, n_layers = load_model(args.model, bits=args.bits)
            hidden_dim = model.config.hidden_size
            if target_layer < 0:
                target_layer = n_layers
            print(f"  対象層: L{target_layer} (hidden_dim={hidden_dim})")
        except Exception as e:
            print(f"\n⚠️ モデルロード失敗: {e}")
            print(f"  → キャッシュ済み {len(cached_keys)} 関数のみで続行 (不足 {len(missing_keys)} 関数はスキップ)")
            model = None
            if not cached_keys:
                print("  ❌ キャッシュも空。モデルが必要です。")
                sys.exit(1)
            # hidden_dim をキャッシュファイルから推定
            sample_key = next(iter(cached_keys))
            sample_path = cache_dir / f"{sample_key}.npz"
            sample_data = np.load(sample_path)
            # npz のキーは layer_0, layer_1, ... 形式
            layer_keys = sorted([k for k in sample_data.files if k.startswith("layer_")])
            n_layers = len(layer_keys) - 1  # layer_0 は embedding 層
            hidden_dim = sample_data[layer_keys[0]].shape[-1]
            if target_layer < 0:
                target_layer = n_layers
            print(f"  対象層: L{target_layer} (hidden_dim={hidden_dim}, n_layers={n_layers})")
            del sample_data
    else:
        # 全キャッシュ済み — モデルロードをスキップ
        print(f"  ✅ 全関数キャッシュ済み — モデルロード不要")
        # hidden_dim をキャッシュファイルから推定
        sample_key = next(iter(cached_keys))
        sample_path = cache_dir / f"{sample_key}.npz"
        sample_data = np.load(sample_path)
        # npz のキーは layer_0, layer_1, ... 形式
        layer_keys = sorted([k for k in sample_data.files if k.startswith("layer_")])
        n_layers = len(layer_keys) - 1  # layer_0 は embedding 層
        hidden_dim = sample_data[layer_keys[0]].shape[-1]
        if target_layer < 0:
            target_layer = n_layers
        print(f"  対象層: L{target_layer} (hidden_dim={hidden_dim}, n_layers={n_layers})")
        del sample_data

    print(f"\n📦 Hidden state ロード (キャッシュ: {cache_dir})...")

    # メモリ最適化: target_layer の hidden state のみ保持 (全層保持は RAM OOM の原因)
    hiddens_map = {}  # key → np.ndarray (seq_len, hidden_dim) — target_layer のみ
    skipped = 0
    for i, source in enumerate(all_sources):
        key = _source_hash(source)
        if key not in hiddens_map:
            try:
                hiddens = get_or_extract_hiddens(source, model, tokenizer, device, cache_dir)
                # target_layer のみ保持してメモリ節約
                hiddens_map[key] = hiddens[target_layer]
            except Exception as e:
                print(f"  ⚠️ {key}: 抽出失敗 ({e})。スキップ")
                skipped += 1
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(all_sources)} 関数処理済み")
    print(f"  → {len(hiddens_map)} 関数の hidden state を取得 (スキップ: {skipped})")

    # --- LLM を解放 (GPU メモリ節約) ---
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # --- 5-fold CV: Attentive Probe ---
    print(f"\n{'='*60}")
    print(f"  Attentive Probe (L{target_layer})")
    print(f"{'='*60}")
    attentive_result = run_cv(
        "attentive", pairs, hiddens_map,
        hidden_dim, target_layer,
        n_folds=args.folds, n_epochs=args.epochs,
    )
    print(f"\n  📊 平均 ρ = {attentive_result['mean_rho']:.3f}")
    print(f"  📊 平均 偏ρ = {attentive_result['mean_partial_rho']:.3f}")
    print(f"  📊 平均 MSE = {attentive_result['mean_mse']:.4f}")

    # --- 5-fold CV: MLP-only Baseline ---
    print(f"\n{'='*60}")
    print(f"  MLP-only Baseline (L{target_layer})")
    print(f"{'='*60}")
    baseline_result = run_cv(
        "meanpool_mlp", pairs, hiddens_map,
        hidden_dim, target_layer,
        n_folds=args.folds, n_epochs=args.epochs,
    )
    print(f"\n  📊 平均 ρ = {baseline_result['mean_rho']:.3f}")
    print(f"  📊 平均 偏ρ = {baseline_result['mean_partial_rho']:.3f}")
    print(f"  📊 平均 MSE = {baseline_result['mean_mse']:.4f}")

    # --- Permutation Test ---
    perm_p = None
    if args.permutations > 0:
        print(f"\n🔀 Permutation Test ({args.permutations} 回)...")
        perm_p = permutation_test(
            "attentive", pairs, hiddens_map,
            hidden_dim, target_layer,
            observed_rho=attentive_result["mean_rho"],
            n_permutations=args.permutations,
        )
        print(f"  → p = {perm_p:.4f}")

    # --- 結果まとめ ---
    print(f"\n{'='*60}")
    print(f"  結果まとめ")
    print(f"{'='*60}")
    print(f"  {'Probe':<20} | {'ρ':>6} | {'偏ρ':>6} | {'MSE':>8}")
    print(f"  {'-'*20}-+-{'-'*6}-+-{'-'*6}-+-{'-'*8}")
    print(f"  {'Phase B (linear)':<20} | {'0.871':>6} | {'0.474':>6} | {'N/A':>8}")
    print(f"  {'MLP-only':<20} | {baseline_result['mean_rho']:6.3f} | {baseline_result['mean_partial_rho']:6.3f} | {baseline_result['mean_mse']:8.4f}")
    print(f"  {'Attentive':<20} | {attentive_result['mean_rho']:6.3f} | {attentive_result['mean_partial_rho']:6.3f} | {attentive_result['mean_mse']:8.4f}")
    if perm_p is not None:
        print(f"  Permutation p = {perm_p:.4f} {'✅' if perm_p < 0.05 else '❌'}")

    # 仮説判定
    print(f"\n📋 仮説判定:")
    h1 = attentive_result["mean_rho"] > 0.474
    h2 = attentive_result["mean_partial_rho"] > 0.3
    h3 = perm_p is not None and perm_p < 0.05
    h4 = attentive_result["mean_rho"] > baseline_result["mean_rho"]
    print(f"  H_B2_1 (ρ > 0.474):           {'✅ PASS' if h1 else '❌ FAIL'}")
    print(f"  H_B2_2 (偏ρ > 0.3):           {'✅ PASS' if h2 else '❌ FAIL'}")
    print(f"  H_B2_3 (perm p < 0.05):       {'✅ PASS' if h3 else '⏭️ SKIP' if perm_p is None else '❌ FAIL'}")
    print(f"  H_B2_4 (Attentive > MLP):     {'✅ PASS' if h4 else '❌ FAIL'}")

    # --- 保存 ---
    output = {
        "model": args.model,
        "target_layer": target_layer,
        "hidden_dim": hidden_dim,
        "n_pairs": len(pairs),
        "attentive": attentive_result,
        "baseline": baseline_result,
        "permutation_p": perm_p,
        "hypotheses": {
            "H_B2_1": h1,
            "H_B2_2": h2,
            "H_B2_3": h3,
            "H_B2_4": h4,
        },
    }
    output_path = Path(args.output)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n💾 結果保存: {output_path}")


if __name__ == "__main__":
    main()
