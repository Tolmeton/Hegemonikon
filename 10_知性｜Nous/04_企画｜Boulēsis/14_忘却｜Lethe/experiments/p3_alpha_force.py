#!/usr/bin/env python3
# PROOF: [L2/実験] <- Paper I §6.3 P3検証 → α-遷移層力の事前コミット方式検証
"""
P3 α-遷移層力 検証実験 — 事前コミット方式 (道 1)

Paper I §6.3 予測:
  F₁₂ = (3/σ)(α·∂Φ + Φ·∂α)
  第2項 Φ·∂α = 「観測フレームワークの変動が曲率を生む」

実験設計:
  1. α(l) = tanh((l - l_c) / l_0) を事前固定 (l_c = n/2, l_0 = n/6)
  2. Φ(l) = 1 - CKA(h_0, h_l) で忘却場を測定
  3. F_pred(l) = Φ(l) · |∂_l α(l)| で理論予測を計算
  4. G(l) = 隠れ状態の層間幾何学的変化量を測定
  5. Spearman ρ(F_pred, G) + permutation test で検定
  6. ベースライン比較 (Φ単体, ∂α単体, 一様)

Usage:
  python p3_alpha_force.py --model codebert --dry-run   # パラメータ確認のみ
  python p3_alpha_force.py --model codebert              # CodeBERT (予備)
  python p3_alpha_force.py --model codellama --bits 4    # CodeLlama (本検証)
"""

# PURPOSE: P3 α-遷移層力の事前コミット方式検証実験

import sys
import os
import json
import argparse
import math
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

# パス設定
# experiments/ → 14_忘却｜Lethe/ → 04_企画｜Boulēsis/ → 10_知性｜Nous/ → 01_ヘゲモニコン｜Hegemonikon/
_SCRIPT_DIR = Path(__file__).parent
_HGK_ROOT = _SCRIPT_DIR.parent.parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
sys.path.insert(0, str(_MEKHANE_SRC))
sys.path.insert(0, str(_SCRIPT_DIR))

# 既存インフラ再利用
try:
    from structural_probe import (
        prepare_data, load_model, extract_hidden_states, cosine_similarity,
        MODEL_CONFIGS, ProbeDataPoint,
    )
except ImportError:
    # structural_probe / mekhane がロードできない場合のフォールバック (dry-run 用)
    print("  ⚠️ structural_probe のインポート失敗 — dry-run モードのみ利用可能")
    MODEL_CONFIGS = {
        "codebert": {"hf_name": "microsoft/codebert-base", "type": "encoder", "default_bits": 32},
        "codellama": {"hf_name": "codellama/CodeLlama-7b-hf", "type": "decoder", "default_bits": 4},
        "mistral": {"hf_name": "mistralai/Mistral-7B-v0.3", "type": "decoder", "default_bits": 4},
    }
    prepare_data = None
    load_model = None
    extract_hidden_states = None

    def cosine_similarity(a, b):
        """フォールバック用 cos 類似度。"""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a < 1e-12 or norm_b < 1e-12:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))



# ============================================================
# Phase 0: 事前コミット — α(l) の定義
# ============================================================

# PURPOSE: α-パラメータプロファイルを事前コミットして記録
@dataclass
class AlphaCommitment:
    """事前コミットされた α(l) パラメータ。変更禁止。"""
    n_layers: int
    l_c: float        # 遷移中心 = n/2
    l_0: float        # 遷移幅 = n/6
    committed_at: str  # ISO 8601 タイムスタンプ

    def alpha(self, l: int) -> float:
        """α(l) = tanh((l - l_c) / l_0)"""
        return math.tanh((l - self.l_c) / self.l_0)

    def dalpha(self, l: int) -> float:
        """∂_l α(l) = sech²((l - l_c) / l_0) / l_0"""
        a = self.alpha(l)
        return (1.0 - a**2) / self.l_0

    def to_dict(self) -> dict:
        return {
            "n_layers": self.n_layers,
            "l_c": self.l_c,
            "l_0": self.l_0,
            "committed_at": self.committed_at,
            "formula": "tanh((l - l_c) / l_0)",
            "source": "Paper I §6.3 具体例",
        }


# PURPOSE: α パラメータの事前コミット + ログ出力
def commit_alpha(n_layers: int) -> AlphaCommitment:
    """事前コミット。データを見る前に呼ぶ。"""
    commitment = AlphaCommitment(
        n_layers=n_layers,
        l_c=n_layers / 2,
        l_0=n_layers / 6,
        committed_at=datetime.now().isoformat(),
    )
    print(f"\n{'='*70}")
    print(f"  Phase 0: α(l) 事前コミット")
    print(f"{'='*70}")
    print(f"  数式: α(l) = tanh((l - {commitment.l_c:.1f}) / {commitment.l_0:.1f})")
    print(f"  遷移中心 l_c = {commitment.l_c:.1f} (= n_layers/2)")
    print(f"  遷移幅   l_0 = {commitment.l_0:.1f} (= n_layers/6)")
    print(f"  コミット時刻: {commitment.committed_at}")
    print(f"  α プロファイル:")

    for l in range(n_layers + 1):
        a = commitment.alpha(l)
        da = commitment.dalpha(l)
        bar = "█" * int(abs(a) * 20)
        sign = "+" if a >= 0 else "-"
        print(f"    l={l:3d}: α={a:+.4f} |{sign}{bar:<20}| ∂α={da:.4f}")

    return commitment


# ============================================================
# Phase 2: Φ(l) 測定 — CKA (Centered Kernel Alignment)
# ============================================================

# PURPOSE: 線形 CKA を計算
def linear_cka(X: np.ndarray, Y: np.ndarray) -> float:
    """線形 CKA (Kornblith et al. 2019)。

    Args:
        X: (n, d_x) — n サンプル × d_x 次元
        Y: (n, d_y) — n サンプル × d_y 次元
    Returns:
        CKA ∈ [0, 1]
    """
    # 中心化
    X = X - X.mean(axis=0)
    Y = Y - Y.mean(axis=0)

    # HSIC 推定値
    XtX = X.T @ X  # (d_x, d_x)
    YtY = Y.T @ Y  # (d_y, d_y)
    XtY = X.T @ Y  # (d_x, d_y)

    hsic_xy = np.sum(XtY ** 2)
    hsic_xx = np.sum(XtX ** 2)
    hsic_yy = np.sum(YtY ** 2)

    denom = math.sqrt(hsic_xx * hsic_yy)
    if denom < 1e-12:
        return 0.0
    return float(hsic_xy / denom)


# PURPOSE: 全サンプルの hidden states を行列に結合
def stack_hidden_states(
    all_hidden: list[list[np.ndarray]], layer_idx: int
) -> np.ndarray:
    """全サンプルの指定層の hidden state を (n, d) に結合。

    Args:
        all_hidden: [sample_i][layer_j] = np.ndarray of shape (d,)
        layer_idx: 取得する層のインデックス
    Returns:
        (n_samples, d) の行列
    """
    return np.stack([h[layer_idx] for h in all_hidden])


# PURPOSE: Φ(l) = 1 - CKA(h_0, h_l) を全層で計算
def compute_phi(all_hidden: list[list[np.ndarray]], n_layers: int) -> np.ndarray:
    """忘却場 Φ(l) を CKA で計算。

    Returns:
        Φ: shape (n_layers + 1,) — Φ[0] = 0 (自己), Φ[l] = 1 - CKA(h_0, h_l)
    """
    H0 = stack_hidden_states(all_hidden, 0)  # (n, d)
    phi = np.zeros(n_layers + 1)

    for l in range(n_layers + 1):
        Hl = stack_hidden_states(all_hidden, l)
        cka_val = linear_cka(H0, Hl)
        phi[l] = 1.0 - cka_val

    return phi


# ============================================================
# Phase 3: G(l) 測定 — 幾何学的変化量
# ============================================================

# PURPOSE: 層間 CKA 変化率を計算
def compute_G_cka(all_hidden: list[list[np.ndarray]], n_layers: int) -> np.ndarray:
    """G1: 隣接層間の CKA 変化率。

    G1(l) = |CKA(h_{l-1}, h_l) - CKA(h_l, h_{l+1})|
    端点は隣接ペアの (1 - CKA) で代替。
    """
    # まず隣接 CKA を全部計算
    adj_cka = np.zeros(n_layers)  # adj_cka[l] = CKA(h_l, h_{l+1})
    for l in range(n_layers):
        Hl = stack_hidden_states(all_hidden, l)
        Hl1 = stack_hidden_states(all_hidden, l + 1)
        adj_cka[l] = linear_cka(Hl, Hl1)

    # G1(l) = 隣接 CKA の変化率
    G = np.zeros(n_layers + 1)
    G[0] = 1.0 - adj_cka[0]  # 端点: 入力層からの不連続性
    for l in range(1, n_layers):
        G[l] = abs(adj_cka[l] - adj_cka[l - 1])
    G[n_layers] = 1.0 - adj_cka[n_layers - 1]  # 端点

    return G


# PURPOSE: 固有値分散の変化率を計算
def compute_G_eigenvar(all_hidden: list[list[np.ndarray]], n_layers: int) -> np.ndarray:
    """G2: 共分散行列の固有値分散の層間変化。"""
    eigvars = np.zeros(n_layers + 1)
    for l in range(n_layers + 1):
        Hl = stack_hidden_states(all_hidden, l)
        Hl_c = Hl - Hl.mean(axis=0)
        # 特異値分解で固有値を効率的に計算 (d >> n の場合)
        _, s, _ = np.linalg.svd(Hl_c, full_matrices=False)
        eigvals = s ** 2 / (len(Hl_c) - 1)
        eigvars[l] = np.var(eigvals)

    # 層間変化
    G = np.zeros(n_layers + 1)
    for l in range(1, n_layers + 1):
        G[l] = abs(eigvars[l] - eigvars[l - 1])
    G[0] = G[1]  # 端点

    return G


# PURPOSE: cos 不連続性を計算
def compute_G_cos(all_hidden: list[list[np.ndarray]], n_layers: int) -> np.ndarray:
    """G3: 層間の平均ベクトルの cos 不連続性。"""
    means = []
    for l in range(n_layers + 1):
        Hl = stack_hidden_states(all_hidden, l)
        means.append(Hl.mean(axis=0))

    G = np.zeros(n_layers + 1)
    for l in range(1, n_layers + 1):
        G[l] = 1.0 - cosine_similarity(means[l - 1], means[l])
    G[0] = G[1]

    return G


# ============================================================
# Phase 4: F_pred(l) 計算 + Phase 5: 検定
# ============================================================

# PURPOSE: 理論予測 F_pred(l) = Φ(l) · |∂α(l)| を計算
def compute_F_pred(
    phi: np.ndarray, commitment: AlphaCommitment
) -> np.ndarray:
    """F_pred(l) = Φ(l) · |∂_l α(l)|"""
    F = np.zeros(len(phi))
    for l in range(len(phi)):
        F[l] = phi[l] * abs(commitment.dalpha(l))
    return F


# PURPOSE: permutation test で相関の有意性を検定
def permutation_test(
    x: np.ndarray, y: np.ndarray, n_perms: int = 10000, seed: int = 42
) -> tuple[float, float]:
    """Spearman ρ + permutation test。

    Returns:
        (rho, p_value)
    """
    from scipy.stats import spearmanr
    rng = np.random.RandomState(seed)

    rho_obs, _ = spearmanr(x, y)

    count = 0
    for _ in range(n_perms):
        perm_y = rng.permutation(y)
        rho_perm, _ = spearmanr(x, perm_y)
        if rho_perm >= rho_obs:
            count += 1

    p_value = (count + 1) / (n_perms + 1)
    return float(rho_obs), float(p_value)


# PURPOSE: R² を計算 (予測力の比較用)
def r_squared(x: np.ndarray, y: np.ndarray) -> float:
    """決定係数 R² (x で y を線形予測したとき)。"""
    if np.std(x) < 1e-12 or np.std(y) < 1e-12:
        return 0.0
    r = np.corrcoef(x, y)[0, 1]
    return float(r ** 2)


# PURPOSE: 全検定を実行
def run_tests(
    phi: np.ndarray,
    G_dict: dict[str, np.ndarray],
    F_pred: np.ndarray,
    commitment: AlphaCommitment,
) -> dict:
    """全検定 + ベースライン比較を実行。"""
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

        # 主検定: F_pred vs G
        rho_main, p_main = permutation_test(F_pred, G)
        r2_main = r_squared(F_pred, G)

        # ベースライン 1: Φ のみ
        rho_phi, p_phi = permutation_test(phi, G)
        r2_phi = r_squared(phi, G)

        # ベースライン 2: ∂α のみ
        rho_da, p_da = permutation_test(dalpha, G)
        r2_da = r_squared(dalpha, G)

        # ベースライン 3: 一様
        rho_uni, p_uni = permutation_test(uniform, G)
        r2_uni = r_squared(uniform, G)

        # ピーク検定
        peak_F = int(np.argmax(F_pred))
        peak_G = int(np.argmax(G))
        peak_diff = abs(peak_F - peak_G)

        print(f"    主検定 (F_pred vs G):  ρ={rho_main:+.4f}  p={p_main:.4f}  R²={r2_main:.4f}")
        print(f"    BL1 (Φ vs G):          ρ={rho_phi:+.4f}  p={p_phi:.4f}  R²={r2_phi:.4f}")
        print(f"    BL2 (∂α vs G):         ρ={rho_da:+.4f}  p={p_da:.4f}  R²={r2_da:.4f}")
        print(f"    BL3 (一様 vs G):       ρ={rho_uni:+.4f}  p={p_uni:.4f}  R²={r2_uni:.4f}")
        print(f"    ΔR² (F_pred - Φ):      {r2_main - r2_phi:+.4f}")
        print(f"    ΔR² (F_pred - ∂α):     {r2_main - r2_da:+.4f}")
        print(f"    ピーク: F_pred@l={peak_F}, G@l={peak_G}, 差={peak_diff}")

        # 判定
        sig = "✅ 有意" if p_main < 0.05 else "  (有意でない)"
        adds = "✅ 付加価値" if r2_main > r2_phi and r2_main > r2_da else "  (付加価値なし)"
        print(f"    判定: {sig}, {adds}")

        results["tests"][g_name] = {
            "rho_main": rho_main, "p_main": p_main, "r2_main": r2_main,
            "rho_phi": rho_phi, "p_phi": p_phi, "r2_phi": r2_phi,
            "rho_dalpha": rho_da, "p_dalpha": p_da, "r2_dalpha": r2_da,
            "rho_uniform": rho_uni, "r2_uniform": r2_uni,
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

# PURPOSE: 結果を PNG に出力
def plot_results(
    phi: np.ndarray,
    G_dict: dict[str, np.ndarray],
    F_pred: np.ndarray,
    commitment: AlphaCommitment,
    model_key: str,
    output_dir: Path,
):
    """4パネル図を生成。"""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("  ⚠️ matplotlib がないため可視化をスキップ")
        return

    n = len(phi)
    layers = np.arange(n)
    alpha_vals = np.array([commitment.alpha(l) for l in range(n)])
    dalpha_vals = np.array([abs(commitment.dalpha(l)) for l in range(n)])

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"P3 α-遷移層力検証 — {model_key} ({n-1} layers)", fontsize=14)

    # Panel 1: α(l) と ∂α(l)
    ax1 = axes[0, 0]
    ax1.plot(layers, alpha_vals, "b-", linewidth=2, label="α(l)")
    ax1_twin = ax1.twinx()
    ax1_twin.plot(layers, dalpha_vals, "r--", linewidth=1.5, label="|∂α(l)|")
    ax1.set_xlabel("Layer l")
    ax1.set_ylabel("α(l)", color="b")
    ax1_twin.set_ylabel("|∂α(l)|", color="r")
    ax1.set_title("事前コミット: α プロファイル")
    ax1.legend(loc="upper left")
    ax1_twin.legend(loc="upper right")
    ax1.axhline(0, color="gray", linestyle=":", alpha=0.5)

    # Panel 2: Φ(l)
    ax2 = axes[0, 1]
    ax2.plot(layers, phi, "g-", linewidth=2, label="Φ(l) = 1 - CKA")
    ax2.fill_between(layers, 0, phi, alpha=0.2, color="green")
    ax2.set_xlabel("Layer l")
    ax2.set_ylabel("Φ(l)")
    ax2.set_title("忘却場 Φ(l)")
    ax2.legend()

    # Panel 3: F_pred(l) vs G(l)
    ax3 = axes[1, 0]
    # F_pred を正規化
    F_norm = F_pred / (F_pred.max() + 1e-12)
    ax3.plot(layers, F_norm, "k-", linewidth=2.5, label="F_pred(l) [正規化]")
    colors = ["#e74c3c", "#3498db", "#2ecc71"]
    for (g_name, G), color in zip(G_dict.items(), colors):
        G_norm = G / (G.max() + 1e-12)
        ax3.plot(layers, G_norm, "--", color=color, linewidth=1.5, label=f"G: {g_name}")
    ax3.set_xlabel("Layer l")
    ax3.set_ylabel("正規化値")
    ax3.set_title("理論予測 F_pred vs 実測 G")
    ax3.legend(fontsize=8)

    # Panel 4: 散布図 (F_pred vs 最良 G)
    ax4 = axes[1, 1]
    # 最も相関の高い G を選択
    from scipy.stats import spearmanr
    best_g_name = None
    best_rho = -1
    for g_name, G in G_dict.items():
        rho, _ = spearmanr(F_pred, G)
        if rho > best_rho:
            best_rho = rho
            best_g_name = g_name

    G_best = G_dict[best_g_name]
    ax4.scatter(F_pred, G_best, alpha=0.7, c=layers, cmap="viridis", s=50)
    ax4.set_xlabel("F_pred(l)")
    ax4.set_ylabel(f"G: {best_g_name}")
    ax4.set_title(f"散布図 (Spearman ρ = {best_rho:.3f})")
    cbar = plt.colorbar(ax4.collections[0], ax=ax4)
    cbar.set_label("Layer l")

    plt.tight_layout()
    output_path = output_dir / f"p3_alpha_force_{model_key}.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  📊 図を保存: {output_path}")


# ============================================================
# メインパイプライン
# ============================================================

# PURPOSE: メイン実行
def main():
    parser = argparse.ArgumentParser(description="P3 α-遷移層力 検証実験")
    parser.add_argument("--model", default="codebert", choices=list(MODEL_CONFIGS.keys()))
    parser.add_argument("--bits", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true", help="パラメータ確認のみ")
    parser.add_argument("--output", default="", help="出力ディレクトリ")
    args = parser.parse_args()

    output_dir = Path(args.output) if args.output else _SCRIPT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Phase 0: モデル情報取得 + α 事前コミット ---
    config = MODEL_CONFIGS[args.model]
    # 層数を取得 (ロード不要で確認)
    n_layers_map = {"codebert": 12, "codellama": 32, "mistral": 32}
    n_layers = n_layers_map.get(args.model, 12)

    commitment = commit_alpha(n_layers)

    if args.dry_run:
        print(f"\n  🏃 Dry run 完了。上記 α プロファイルでコミット。")
        # コミットメントを JSON で保存
        commit_path = output_dir / f"p3_commitment_{args.model}.json"
        with open(commit_path, "w") as f:
            json.dump(commitment.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"  💾 コミット保存: {commit_path}")
        return

    # --- Phase 1: データ準備 + Hidden State 抽出 ---
    print(f"\n{'='*70}")
    print(f"  Phase 1: データ準備 + Hidden State 抽出")
    print(f"{'='*70}")

    data = prepare_data()
    print(f"  データ: {len(data)} ペア ({sum(1 for d in data if d.is_positive)} 正例)")

    model, tokenizer, device, actual_n_layers = load_model(args.model, args.bits)

    # 層数が事前コミットと合うか確認
    if actual_n_layers != n_layers:
        print(f"  ⚠️ 層数不一致: コミット={n_layers}, 実際={actual_n_layers}")
        print(f"  コミットを実際の層数で再作成...")
        commitment = commit_alpha(actual_n_layers)
        n_layers = actual_n_layers

    # 全スニペットの hidden state を抽出
    all_codes = []
    for d in data:
        all_codes.append(d.ccl_a if d.ccl_a else "_")
        all_codes.append(d.ccl_b if d.ccl_b else "_")

    # 代わりに: ソースコードを直接使う (CCL ではなくコード自体の隠れ表現)
    all_codes_src = []
    from p3_benchmark import create_benchmark_pairs
    raw_pairs = create_benchmark_pairs()
    for pair in raw_pairs:
        all_codes_src.append(pair.func_a_source)
        all_codes_src.append(pair.func_b_source)

    print(f"  {len(all_codes_src)} スニペットの hidden state を抽出中...")

    all_hidden = []
    for i, code in enumerate(all_codes_src):
        if (i + 1) % 10 == 0:
            print(f"    [{i+1}/{len(all_codes_src)}]")
        hs = extract_hidden_states(code, model, tokenizer, device)
        all_hidden.append(hs)

    print(f"  ✅ 抽出完了: {len(all_hidden)} サンプル × {len(all_hidden[0])} 層")

    # --- Phase 2: Φ(l) 測定 ---
    print(f"\n{'='*70}")
    print(f"  Phase 2: Φ(l) 測定 (CKA)")
    print(f"{'='*70}")

    phi = compute_phi(all_hidden, n_layers)
    for l in range(n_layers + 1):
        bar = "█" * int(phi[l] * 30)
        print(f"    l={l:3d}: Φ={phi[l]:.4f} |{bar}")

    # --- Phase 3: G(l) 測定 ---
    print(f"\n{'='*70}")
    print(f"  Phase 3: G(l) 測定 (幾何学的変化量)")
    print(f"{'='*70}")

    G_dict = {
        "CKA変化": compute_G_cka(all_hidden, n_layers),
        "固有値分散": compute_G_eigenvar(all_hidden, n_layers),
        "cos不連続": compute_G_cos(all_hidden, n_layers),
    }

    for g_name, G in G_dict.items():
        print(f"\n  {g_name}:")
        for l in range(n_layers + 1):
            bar = "█" * int(G[l] / (G.max() + 1e-12) * 20)
            print(f"    l={l:3d}: G={G[l]:.6f} |{bar}")

    # --- Phase 4: F_pred(l) 計算 ---
    print(f"\n{'='*70}")
    print(f"  Phase 4: F_pred(l) = Φ(l) · |∂α(l)|")
    print(f"{'='*70}")

    F_pred = compute_F_pred(phi, commitment)
    for l in range(n_layers + 1):
        bar = "█" * int(F_pred[l] / (F_pred.max() + 1e-12) * 20)
        print(f"    l={l:3d}: F={F_pred[l]:.6f} |{bar}")

    # --- Phase 5: 検定 ---
    test_results = run_tests(phi, G_dict, F_pred, commitment)

    # --- 可視化 ---
    plot_results(phi, G_dict, F_pred, commitment, args.model, output_dir)

    # --- 結果保存 ---
    result_data = {
        "model": args.model,
        "n_layers": n_layers,
        "commitment": commitment.to_dict(),
        "phi": phi.tolist(),
        "F_pred": F_pred.tolist(),
        "G": {name: G.tolist() for name, G in G_dict.items()},
        "alpha": [commitment.alpha(l) for l in range(n_layers + 1)],
        "dalpha": [commitment.dalpha(l) for l in range(n_layers + 1)],
        **test_results,
    }

    result_path = output_dir / f"p3_alpha_force_{args.model}.json"
    with open(result_path, "w") as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    print(f"\n  💾 結果保存: {result_path}")

    # --- 総合判定 ---
    print(f"\n{'='*70}")
    print(f"  総合判定")
    print(f"{'='*70}")

    any_sig = any(
        t["significant"] for t in test_results["tests"].values()
    )
    any_add = any(
        t["additive"] for t in test_results["tests"].values()
    )

    if any_sig and any_add:
        print(f"  ✅ P3 α-遷移層力の証拠あり (有意 + 付加価値)")
        print(f"     → F_pred = Φ·∂α は Φ 単体より優れた予測力を持つ")
    elif any_sig:
        print(f"  🟡 F_pred と G に有意な相関はあるが、Φ 単体を超えない")
        print(f"     → ∂α 項の付加価値は不明確")
    else:
        print(f"  ❌ F_pred と G に有意な相関なし")
        print(f"     → α(l)=tanh の事前コミットでは P3 効果は検出されない")
        print(f"     → 解釈: α の操作化に問題があるか、効果が小さすぎる")


if __name__ == "__main__":
    main()
