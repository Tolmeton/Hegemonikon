#!/usr/bin/env python3
"""
P3 α-遷移層力 検証実験 — Colab 自己完結版
CodeLlama-13B (40層, 4-bit) で実行

セットアップ (Colab セル):
  !pip install torch transformers bitsandbytes scipy matplotlib accelerate -q

Usage:
  python p3_colab.py                       # CodeLlama-13B (デフォルト)
  python p3_colab.py --model codellama-7b  # CodeLlama-7B
"""

import os
import sys
import json
import math
import argparse
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

import numpy as np

# 並列計算における OOM とハング/デッドロックを防止するためのスレッド数制限
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# ============================================================
# モデル設定
# ============================================================
MODEL_CONFIGS = {
    "codellama-13b": {
        "hf_name": "codellama/CodeLlama-13b-hf",
        "type": "decoder",
        "default_bits": 4,
        "n_layers": 40,
    },
    "codellama-7b": {
        "hf_name": "codellama/CodeLlama-7b-hf",
        "type": "decoder",
        "default_bits": 4,
        "n_layers": 32,
    },
    "codebert": {
        "hf_name": "microsoft/codebert-base",
        "type": "encoder",
        "default_bits": 32,
        "n_layers": 12,
    },
}

# ============================================================
# ベンチマークデータ — 構造同型関数ペア (P3検証用)
# ============================================================

# PURPOSE: 自己完結型ベンチマークデータ (structural_probe.py/p3_benchmark.py 不要)
BENCHMARK_PAIRS = [
    # (func_a, func_b, is_positive) — is_positive = 構造的に同型
    # --- 正例: 構造同型 ---
    ("def add(a, b):\n    return a + b", "def mul(x, y):\n    return x * y", True),
    ("def square(x):\n    return x * x", "def cube(x):\n    return x * x * x", True),
    ("def greet(name):\n    return f'Hello, {name}'", "def farewell(name):\n    return f'Goodbye, {name}'", True),
    ("def max_val(a, b):\n    if a > b:\n        return a\n    return b",
     "def min_val(a, b):\n    if a < b:\n        return a\n    return b", True),
    ("def double(lst):\n    return [x * 2 for x in lst]",
     "def negate(lst):\n    return [-x for x in lst]", True),
    ("def count_pos(lst):\n    c = 0\n    for x in lst:\n        if x > 0:\n            c += 1\n    return c",
     "def count_neg(lst):\n    c = 0\n    for x in lst:\n        if x < 0:\n            c += 1\n    return c", True),
    ("def flatten(lst):\n    result = []\n    for sub in lst:\n        for item in sub:\n            result.append(item)\n    return result",
     "def chain(lst):\n    result = []\n    for sub in lst:\n        for item in sub:\n            result.append(item)\n    return result", True),
    ("def first(lst):\n    if lst:\n        return lst[0]\n    return None",
     "def last(lst):\n    if lst:\n        return lst[-1]\n    return None", True),
    ("def inc(x):\n    return x + 1", "def dec(x):\n    return x - 1", True),
    ("def is_even(n):\n    return n % 2 == 0", "def is_odd(n):\n    return n % 2 != 0", True),
    ("def to_upper(s):\n    return s.upper()", "def to_lower(s):\n    return s.lower()", True),
    ("def head(lst):\n    return lst[:1]", "def tail(lst):\n    return lst[1:]", True),
    ("def keys(d):\n    return list(d.keys())", "def values(d):\n    return list(d.values())", True),
    ("def sum_list(lst):\n    total = 0\n    for x in lst:\n        total += x\n    return total",
     "def prod_list(lst):\n    total = 1\n    for x in lst:\n        total *= x\n    return total", True),
    ("def rev(s):\n    return s[::-1]", "def dup(s):\n    return s + s", True),
    ("def abs_val(x):\n    if x < 0:\n        return -x\n    return x",
     "def sign(x):\n    if x < 0:\n        return -1\n    return 1", True),
    ("def pop_first(lst):\n    return lst[1:], lst[0]",
     "def pop_last(lst):\n    return lst[:-1], lst[-1]", True),
    ("def zip_add(a, b):\n    return [x + y for x, y in zip(a, b)]",
     "def zip_mul(a, b):\n    return [x * y for x, y in zip(a, b)]", True),
    ("def clamp_min(x, lo):\n    return max(x, lo)",
     "def clamp_max(x, hi):\n    return min(x, hi)", True),
    ("def prepend(lst, x):\n    return [x] + lst",
     "def append(lst, x):\n    return lst + [x]", True),
    # --- 負例: 構造非同型 ---
    ("def add(a, b):\n    return a + b",
     "def sort_list(lst):\n    return sorted(lst)", False),
    ("def square(x):\n    return x * x",
     "def flatten(lst):\n    result = []\n    for sub in lst:\n        for item in sub:\n            result.append(item)\n    return result", False),
    ("def greet(name):\n    return f'Hello, {name}'",
     "class Counter:\n    def __init__(self):\n        self.n = 0\n    def inc(self):\n        self.n += 1", False),
    ("def is_even(n):\n    return n % 2 == 0",
     "def fibonacci(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a", False),
    ("def max_val(a, b):\n    if a > b:\n        return a\n    return b",
     "def merge_sort(lst):\n    if len(lst) <= 1:\n        return lst\n    mid = len(lst) // 2\n    left = merge_sort(lst[:mid])\n    right = merge_sort(lst[mid:])\n    return merge(left, right)", False),
    ("def inc(x):\n    return x + 1",
     "import re\ndef extract_emails(text):\n    return re.findall(r'\\S+@\\S+', text)", False),
    ("def to_upper(s):\n    return s.upper()",
     "def binary_search(arr, target):\n    lo, hi = 0, len(arr)-1\n    while lo <= hi:\n        mid = (lo+hi)//2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            lo = mid+1\n        else:\n            hi = mid-1\n    return -1", False),
    ("def head(lst):\n    return lst[:1]",
     "def matrix_mul(A, B):\n    n = len(A)\n    C = [[0]*n for _ in range(n)]\n    for i in range(n):\n        for j in range(n):\n            for k in range(n):\n                C[i][j] += A[i][k]*B[k][j]\n    return C", False),
    ("def rev(s):\n    return s[::-1]",
     "def dijkstra(graph, start):\n    dist = {start: 0}\n    visited = set()\n    return dist", False),
    ("def keys(d):\n    return list(d.keys())",
     "async def fetch(url):\n    import aiohttp\n    async with aiohttp.ClientSession() as s:\n        async with s.get(url) as r:\n            return await r.text()", False),
    ("def abs_val(x):\n    if x < 0:\n        return -x\n    return x",
     "def quicksort(lst):\n    if len(lst) <= 1:\n        return lst\n    pivot = lst[0]\n    left = [x for x in lst[1:] if x <= pivot]\n    right = [x for x in lst[1:] if x > pivot]\n    return quicksort(left) + [pivot] + quicksort(right)", False),
    ("def double(lst):\n    return [x * 2 for x in lst]",
     "class Stack:\n    def __init__(self):\n        self._data = []\n    def push(self, x):\n        self._data.append(x)\n    def pop(self):\n        return self._data.pop()", False),
    ("def count_pos(lst):\n    c = 0\n    for x in lst:\n        if x > 0:\n            c += 1\n    return c",
     "def memoize(func):\n    cache = {}\n    def wrapper(*args):\n        if args not in cache:\n            cache[args] = func(*args)\n        return cache[args]\n    return wrapper", False),
    ("def clamp_min(x, lo):\n    return max(x, lo)",
     "def parse_json(s):\n    import json\n    return json.loads(s)", False),
    ("def sum_list(lst):\n    total = 0\n    for x in lst:\n        total += x\n    return total",
     "def levenshtein(s1, s2):\n    m, n = len(s1), len(s2)\n    dp = [[0]*(n+1) for _ in range(m+1)]\n    for i in range(m+1):\n        dp[i][0] = i\n    for j in range(n+1):\n        dp[0][j] = j\n    for i in range(1, m+1):\n        for j in range(1, n+1):\n            cost = 0 if s1[i-1]==s2[j-1] else 1\n            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)\n    return dp[m][n]", False),
]


# ============================================================
# Phase 0: 事前コミット — α(l) の定義
# ============================================================

@dataclass
class AlphaCommitment:
    """事前コミットされた α(l) パラメータ。変更禁止。"""
    n_layers: int
    l_c: float        # 遷移中心 = n/2
    l_0: float        # 遷移幅 = n/6
    committed_at: str  # ISO 8601

    def alpha(self, l: int) -> float:
        return math.tanh((l - self.l_c) / self.l_0)

    def dalpha(self, l: int) -> float:
        a = self.alpha(l)
        return (1.0 - a**2) / self.l_0

    def to_dict(self) -> dict:
        return {
            "n_layers": self.n_layers,
            "l_c": self.l_c, "l_0": self.l_0,
            "committed_at": self.committed_at,
            "formula": "tanh((l - l_c) / l_0)",
            "source": "Paper I §6.3",
        }


def commit_alpha(n_layers: int) -> AlphaCommitment:
    commitment = AlphaCommitment(
        n_layers=n_layers,
        l_c=n_layers / 2,
        l_0=n_layers / 6,
        committed_at=datetime.now().isoformat(),
    )
    print(f"\n{'='*70}")
    print(f"  Phase 0: α(l) 事前コミット")
    print(f"{'='*70}")
    print(f"  α(l) = tanh((l - {commitment.l_c:.1f}) / {commitment.l_0:.1f})")
    print(f"  l_c = {commitment.l_c:.1f}, l_0 = {commitment.l_0:.1f}")
    print(f"  コミット時刻: {commitment.committed_at}")
    for l in range(n_layers + 1):
        a = commitment.alpha(l)
        da = commitment.dalpha(l)
        bar = "█" * int(abs(a) * 20)
        sign = "+" if a >= 0 else "-"
        print(f"    l={l:3d}: α={a:+.4f} |{sign}{bar:<20}| ∂α={da:.4f}")
    return commitment


# ============================================================
# モデル ロード + Hidden State 抽出
# ============================================================

def load_model(model_key: str, bits: int = 0):
    """モデルとトークナイザーをロード (量子化対応)"""
    import torch
    from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM, BitsAndBytesConfig

    config = MODEL_CONFIGS[model_key]
    hf_name = config["hf_name"]
    model_type = config["type"]
    if bits == 0:
        bits = config["default_bits"]

    print(f"📦 モデルロード: {hf_name} ({bits}bit)")
    tokenizer = AutoTokenizer.from_pretrained(hf_name, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    kwargs = {"trust_remote_code": True, "output_hidden_states": True}
    if bits == 4:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )
        kwargs["quantization_config"] = bnb_config
        kwargs["device_map"] = "auto"
    elif bits == 16:
        kwargs["torch_dtype"] = torch.float16
        kwargs["device_map"] = "auto"

    ModelClass = AutoModelForCausalLM if model_type == "decoder" else AutoModel
    model = ModelClass.from_pretrained(hf_name, **kwargs)
    model.eval()

    # 層数取得
    if hasattr(model.config, "num_hidden_layers"):
        n_layers = model.config.num_hidden_layers
    else:
        n_layers = config["n_layers"]

    device = next(model.parameters()).device
    print(f"  ✅ ロード完了: {n_layers} 層, device={device}")
    return model, tokenizer, device, n_layers


def extract_hidden_states(code: str, model, tokenizer, device) -> list:
    """コードスニペットから全層の hidden state を抽出。CLS/最終トークンの平均を使用。"""
    import torch

    inputs = tokenizer(
        code, return_tensors="pt", truncation=True, max_length=256, padding=True
    ).to(device)

    with torch.no_grad():
        outputs = model(**inputs)

    hidden_states = outputs.hidden_states  # (n_layers + 1,) のタプル

    result = []
    for hs in hidden_states:
        # attention_mask を使って有効トークンのみ平均
        mask = inputs["attention_mask"].unsqueeze(-1).float()
        masked_hs = hs * mask
        pooled = masked_hs.sum(dim=1) / mask.sum(dim=1)
        result.append(pooled.squeeze(0).cpu().float().numpy())

    return result


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom < 1e-12:
        return 0.0
    return float(np.dot(a, b) / denom)


# ============================================================
# Phase 2: Φ(l) / Phase 3: G(l) / Phase 4: F_pred
# ============================================================

def stack_hidden_states(all_hidden, layer_idx):
    return np.stack([h[layer_idx] for h in all_hidden])


def linear_cka(X, Y):
    X = X - X.mean(axis=0)
    Y = Y - Y.mean(axis=0)
    XtY = X.T @ Y
    hsic_xy = np.sum(XtY ** 2)
    hsic_xx = np.sum((X.T @ X) ** 2)
    hsic_yy = np.sum((Y.T @ Y) ** 2)
    denom = math.sqrt(hsic_xx * hsic_yy)
    if denom < 1e-12:
        return 0.0
    return float(hsic_xy / denom)


def compute_phi(all_hidden, n_layers):
    H0 = stack_hidden_states(all_hidden, 0)
    phi = np.zeros(n_layers + 1)
    for l in range(n_layers + 1):
        Hl = stack_hidden_states(all_hidden, l)
        phi[l] = 1.0 - linear_cka(H0, Hl)
    return phi


def compute_G_cka(all_hidden, n_layers):
    adj_cka = np.zeros(n_layers)
    for l in range(n_layers):
        Hl = stack_hidden_states(all_hidden, l)
        Hl1 = stack_hidden_states(all_hidden, l + 1)
        adj_cka[l] = linear_cka(Hl, Hl1)
    G = np.zeros(n_layers + 1)
    G[0] = 1.0 - adj_cka[0]
    for l in range(1, n_layers):
        G[l] = abs(adj_cka[l] - adj_cka[l - 1])
    G[n_layers] = 1.0 - adj_cka[n_layers - 1]
    return G


def compute_G_eigenvar(all_hidden, n_layers):
    eigvars = np.zeros(n_layers + 1)
    for l in range(n_layers + 1):
        Hl = stack_hidden_states(all_hidden, l)
        Hl_c = Hl - Hl.mean(axis=0)
        _, s, _ = np.linalg.svd(Hl_c, full_matrices=False)
        eigvals = s ** 2 / (len(Hl_c) - 1)
        eigvars[l] = np.var(eigvals)
    G = np.zeros(n_layers + 1)
    for l in range(1, n_layers + 1):
        G[l] = abs(eigvars[l] - eigvars[l - 1])
    G[0] = G[1]
    return G


def compute_G_cos(all_hidden, n_layers):
    means = [stack_hidden_states(all_hidden, l).mean(axis=0) for l in range(n_layers + 1)]
    G = np.zeros(n_layers + 1)
    for l in range(1, n_layers + 1):
        G[l] = 1.0 - cosine_similarity(means[l - 1], means[l])
    G[0] = G[1]
    return G


def compute_F_pred(phi, commitment):
    F = np.zeros(len(phi))
    for l in range(len(phi)):
        F[l] = phi[l] * abs(commitment.dalpha(l))
    return F


# ============================================================
# Phase 5: 検定
# ============================================================

def permutation_test(x, y, n_perms=10000, seed=42):
    from scipy.stats import spearmanr
    rng = np.random.RandomState(seed)
    rho_obs, _ = spearmanr(x, y)
    count = 0
    for _ in range(n_perms):
        perm_y = rng.permutation(y)
        rho_perm, _ = spearmanr(x, perm_y)
        if rho_perm >= rho_obs:
            count += 1
    return float(rho_obs), float((count + 1) / (n_perms + 1))


def r_squared(x, y):
    if np.std(x) < 1e-12 or np.std(y) < 1e-12:
        return 0.0
    r = np.corrcoef(x, y)[0, 1]
    return float(r ** 2)


def run_tests(phi, G_dict, F_pred, commitment):
    from scipy.stats import spearmanr
    n = len(phi)
    dalpha = np.array([abs(commitment.dalpha(l)) for l in range(n)])
    uniform = np.ones(n) / n

    results = {"tests": {}}
    print(f"\n{'='*70}")
    print(f"  Phase 5: 検定結果")
    print(f"{'='*70}")

    for g_name, G in G_dict.items():
        print(f"\n  --- G プロキシ: {g_name} ---")
        rho_main, p_main = permutation_test(F_pred, G)
        r2_main = r_squared(F_pred, G)
        rho_phi, p_phi = permutation_test(phi, G)
        r2_phi = r_squared(phi, G)
        rho_da, p_da = permutation_test(dalpha, G)
        r2_da = r_squared(dalpha, G)
        rho_uni, p_uni = permutation_test(uniform, G)
        r2_uni = r_squared(uniform, G)
        peak_F = int(np.argmax(F_pred))
        peak_G = int(np.argmax(G))
        peak_diff = abs(peak_F - peak_G)

        print(f"    主: ρ={rho_main:+.4f} p={p_main:.4f} R²={r2_main:.4f}")
        print(f"    Φ:  ρ={rho_phi:+.4f} p={p_phi:.4f} R²={r2_phi:.4f}")
        print(f"    ∂α: ρ={rho_da:+.4f} p={p_da:.4f} R²={r2_da:.4f}")
        print(f"    ΔR²(F-Φ)={r2_main-r2_phi:+.4f} ΔR²(F-∂α)={r2_main-r2_da:+.4f}")
        print(f"    ピーク: F@{peak_F} G@{peak_G} 差={peak_diff}")

        sig = "✅" if p_main < 0.05 else "❌"
        adds = "✅" if r2_main > r2_phi and r2_main > r2_da else "❌"
        print(f"    判定: 有意={sig} 付加={adds}")

        results["tests"][g_name] = {
            "rho_main": rho_main, "p_main": p_main, "r2_main": r2_main,
            "rho_phi": rho_phi, "r2_phi": r2_phi,
            "rho_dalpha": rho_da, "r2_dalpha": r2_da,
            "delta_r2_phi": r2_main - r2_phi,
            "delta_r2_dalpha": r2_main - r2_da,
            "peak_F": peak_F, "peak_G": peak_G, "peak_diff": peak_diff,
            "significant": p_main < 0.05,
            "additive": r2_main > r2_phi and r2_main > r2_da,
        }
    return results


# ============================================================
# 可視化
# ============================================================

def plot_results(phi, G_dict, F_pred, commitment, model_key, output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    n = len(phi)
    layers = np.arange(n)
    alpha_vals = np.array([commitment.alpha(l) for l in range(n)])
    dalpha_vals = np.array([abs(commitment.dalpha(l)) for l in range(n)])

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"P3 alpha-transition force — {model_key} ({n-1} layers)", fontsize=14)

    # α プロファイル
    ax1 = axes[0, 0]
    ax1.plot(layers, alpha_vals, "b-", lw=2, label="α(l)")
    ax1t = ax1.twinx()
    ax1t.plot(layers, dalpha_vals, "r--", lw=1.5, label="|∂α(l)|")
    ax1.set_xlabel("Layer l"); ax1.set_ylabel("α(l)", color="b")
    ax1t.set_ylabel("|∂α(l)|", color="r")
    ax1.set_title("Pre-committed α profile")
    ax1.legend(loc="upper left"); ax1t.legend(loc="upper right")
    ax1.axhline(0, color="gray", ls=":", alpha=0.5)

    # Φ(l)
    ax2 = axes[0, 1]
    ax2.plot(layers, phi, "g-", lw=2, label="Φ(l) = 1 - CKA")
    ax2.fill_between(layers, 0, phi, alpha=0.2, color="green")
    ax2.set_xlabel("Layer l"); ax2.set_ylabel("Φ(l)")
    ax2.set_title("Oblivion field Φ(l)"); ax2.legend()

    # F_pred vs G
    ax3 = axes[1, 0]
    F_norm = F_pred / (F_pred.max() + 1e-12)
    ax3.plot(layers, F_norm, "k-", lw=2.5, label="F_pred [norm]")
    colors = ["#e74c3c", "#3498db", "#2ecc71"]
    for (g_name, G), color in zip(G_dict.items(), colors):
        G_norm = G / (G.max() + 1e-12)
        ax3.plot(layers, G_norm, "--", color=color, lw=1.5, label=f"G: {g_name}")
    ax3.set_xlabel("Layer l"); ax3.set_ylabel("Normalized")
    ax3.set_title("F_pred vs G"); ax3.legend(fontsize=8)

    # 散布図
    ax4 = axes[1, 1]
    from scipy.stats import spearmanr
    best_name, best_rho = None, -1
    for g_name, G in G_dict.items():
        rho, _ = spearmanr(F_pred, G)
        if rho > best_rho:
            best_rho = rho; best_name = g_name
    ax4.scatter(F_pred, G_dict[best_name], alpha=0.7, c=layers, cmap="viridis", s=50)
    ax4.set_xlabel("F_pred(l)"); ax4.set_ylabel(f"G: {best_name}")
    ax4.set_title(f"Scatter (Spearman ρ = {best_rho:.3f})")
    plt.colorbar(ax4.collections[0], ax=ax4, label="Layer l")

    plt.tight_layout()
    out = Path(output_dir) / f"p3_alpha_force_{model_key}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 Figure saved: {out}")


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="P3 α-transition force (Colab)")
    parser.add_argument("--model", default="codellama-13b", choices=list(MODEL_CONFIGS.keys()))
    parser.add_argument("--bits", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default=".")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    config = MODEL_CONFIGS[args.model]
    n_layers = config["n_layers"]
    commitment = commit_alpha(n_layers)

    if args.dry_run:
        print(f"\n  🏃 Dry run 完了。")
        commit_path = output_dir / f"p3_commitment_{args.model}.json"
        with open(commit_path, "w") as f:
            json.dump(commitment.to_dict(), f, indent=2)
        print(f"  💾 Saved: {commit_path}")
        return

    # Phase 1: データ + Hidden States
    print(f"\n{'='*70}")
    print(f"  Phase 1: データ準備 + Hidden State 抽出")
    print(f"{'='*70}")

    all_codes = []
    for (fa, fb, _) in BENCHMARK_PAIRS:
        all_codes.append(fa)
        all_codes.append(fb)
    print(f"  データ: {len(BENCHMARK_PAIRS)} ペア, {len(all_codes)} スニペット")

    model, tokenizer, device, actual_n_layers = load_model(args.model, args.bits)
    if actual_n_layers != n_layers:
        print(f"  ⚠️ 層数補正: {n_layers} → {actual_n_layers}")
        commitment = commit_alpha(actual_n_layers)
        n_layers = actual_n_layers

    print(f"  {len(all_codes)} スニペットの hidden state を抽出中...")
    all_hidden = []
    for i, code in enumerate(all_codes):
        if (i + 1) % 10 == 0:
            print(f"    [{i+1}/{len(all_codes)}]")
        hs = extract_hidden_states(code, model, tokenizer, device)
        all_hidden.append(hs)
    print(f"  ✅ 完了: {len(all_hidden)} サンプル × {len(all_hidden[0])} 層")

    # Phase 2-4
    print(f"\n{'='*70}")
    print(f"  Phase 2: Φ(l)")
    print(f"{'='*70}")
    phi = compute_phi(all_hidden, n_layers)
    for l in range(n_layers + 1):
        bar = "█" * int(phi[l] * 30)
        print(f"    l={l:3d}: Φ={phi[l]:.4f} |{bar}")

    print(f"\n{'='*70}")
    print(f"  Phase 3: G(l)")
    print(f"{'='*70}")
    G_dict = {
        "CKA_change": compute_G_cka(all_hidden, n_layers),
        "eigenvar": compute_G_eigenvar(all_hidden, n_layers),
        "cos_disc": compute_G_cos(all_hidden, n_layers),
    }
    for g_name, G in G_dict.items():
        print(f"\n  {g_name}:")
        for l in range(n_layers + 1):
            bar = "█" * int(G[l] / (G.max() + 1e-12) * 20)
            print(f"    l={l:3d}: G={G[l]:.6f} |{bar}")

    print(f"\n{'='*70}")
    print(f"  Phase 4: F_pred(l) = Φ(l) · |∂α(l)|")
    print(f"{'='*70}")
    F_pred = compute_F_pred(phi, commitment)
    for l in range(n_layers + 1):
        bar = "█" * int(F_pred[l] / (F_pred.max() + 1e-12) * 20)
        print(f"    l={l:3d}: F={F_pred[l]:.6f} |{bar}")

    # Phase 5
    test_results = run_tests(phi, G_dict, F_pred, commitment)

    # 可視化
    plot_results(phi, G_dict, F_pred, commitment, args.model, output_dir)

    # 結果保存
    result_data = {
        "model": args.model, "n_layers": n_layers,
        "commitment": commitment.to_dict(),
        "phi": phi.tolist(), "F_pred": F_pred.tolist(),
        "G": {name: G.tolist() for name, G in G_dict.items()},
        "alpha": [commitment.alpha(l) for l in range(n_layers + 1)],
        "dalpha": [commitment.dalpha(l) for l in range(n_layers + 1)],
        **test_results,
    }
    result_path = output_dir / f"p3_alpha_force_{args.model}.json"
    with open(result_path, "w") as f:
        json.dump(result_data, f, indent=2)
    print(f"\n  💾 Results saved: {result_path}")

    # 総合判定
    print(f"\n{'='*70}")
    print(f"  総合判定")
    print(f"{'='*70}")
    any_sig = any(t["significant"] for t in test_results["tests"].values())
    any_add = any(t["additive"] for t in test_results["tests"].values())
    if any_sig and any_add:
        print("  ✅ P3 α-遷移層力の証拠あり")
    elif any_sig:
        print("  🟡 有意だが Φ 単体を超えない")
    else:
        print("  ❌ F_pred と G に有意な相関なし")


if __name__ == "__main__":
    main()
