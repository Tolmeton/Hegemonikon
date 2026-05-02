#!/usr/bin/env python3
"""
EP (エントロピー生成) 計算手法の診断

問題: 点推定 EP (0.18-0.89) と Bootstrap median EP (5.47-11.94) が桁違い。
仮説:
  H1: Bootstrap の iid 再サンプリングが時系列の自己相関を破壊 → VAR(1) が不安定化
  H2: Σ_state が特異に近く、Σ^{-1} が爆発
  H3: EP = tr(Q Σ Q^T Σ^{-1}) の定式化自体に問題 (次元依存性等)
  H4: ウィンドウ重複による見かけの自己相関

診断:
  1. Σ_state の条件数 (κ) を確認
  2. Block Bootstrap (自己相関保存) vs iid Bootstrap の比較
  3. EP の直接定義 EP = tr(Q D_ss Q^T D_ss^{-1}) vs 代替定式
  4. 合成データ (既知パラメータ) での EP 推定精度チェック
"""

import json
import re
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple

# ── sensitivity_alpha.py と同じデータロード関数群 (簡略化) ──

TRACES_DIR = Path(
    "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
    "/30_記憶｜Mneme/01_記録｜Records/g_実行痕跡｜traces"
)
LOGS_DIR = Path(
    "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
    "/30_記憶｜Mneme/01_記録｜Records/f_ログ｜logs"
)

ALL_24 = {'noe','bou','zet','ene','ske','sag','pei','tek',
          'kat','epo','pai','dok','lys','ops','akr','arc',
          'beb','ele','kop','dio','hyp','prm','ath','par'}
VERB_RE = re.compile(r'/([a-z]{2,4})([+\-])?')

EXPLORE = {"ske","zet","pei","dok","epo"}
EXPLOIT = {"sag","tek","ene","kat","pai"}
INTERNAL = {"noe","bou","kat","epo","beb","hyp"}
EXTERNAL = {"zet","pei","tek","ene","dio","par"}
MICRO = {"lys","akr"}; MACRO = {"ops","arc"}
POSITIVE = {"beb","kop"}; NEGATIVE = {"ele","dio"}
PAST = {"hyp","ath"}; FUTURE = {"prm","par"}
DEPTH_MAP = {"+": 1.0, "": 0.5, "-": 0.0}

THEOREM_TO_SERIES = {
    "O1": "Telos", "O2": "Telos", "O3": "Telos", "O4": "Telos",
    "A1": "Telos", "A2": "Telos", "A3": "Telos", "A4": "Telos",
    "P1": "Methodos", "P2": "Methodos", "P3": "Methodos", "P4": "Methodos",
    "K1": "Krisis", "K2": "Krisis", "K3": "Krisis", "K4": "Krisis",
    "S1": "Diastasis", "S2": "Diastasis", "S3": "Diastasis", "S4": "Diastasis",
    "H1": "Chronos", "H2": "Chronos", "H3": "Chronos", "H4": "Chronos",
}
SERIES_TO_VERBS = {
    "Telos": ["noe","bou","zet","ene"],
    "Methodos": ["ske","sag","pei","tek"],
    "Krisis": ["kat","epo","pai","dok"],
    "Diastasis": ["lys","ops","akr","arc"],
    "Orexis": ["beb","ele","kop","dio"],
    "Chronos": ["hyp","prm","ath","par"],
}


def parse_ts(ts_val) -> float:
    if isinstance(ts_val, (int, float)): return float(ts_val)
    if isinstance(ts_val, str):
        try:
            ts_clean = ts_val.replace("+00:00", "").replace("+09:00", "")
            return datetime.fromisoformat(ts_clean).timestamp()
        except: return 0.0
    return 0.0


def extract_verbs_from_ccl(wf: str) -> List[Tuple[str, str]]:
    return [(m.group(1), m.group(2) or "") for m in VERB_RE.finditer(wf) if m.group(1) in ALL_24]


def load_tape(traces_dir: Path) -> List[dict]:
    events = []
    for tape in sorted(traces_dir.glob("tape_*.jsonl")):
        with open(tape) as f:
            for line in f:
                l = line.strip()
                if not l: continue
                try: ev = json.loads(l)
                except: continue
                verbs = extract_verbs_from_ccl(ev.get("wf", ""))
                if verbs:
                    events.append({"ts": parse_ts(ev.get("ts", 0)), "source": "tape", "verbs": verbs})
    return events


def load_theorem(logs_dir: Path) -> List[dict]:
    events = []
    for logf in sorted(logs_dir.glob("theorem_log_*.jsonl")):
        with open(logf) as f:
            for line in f:
                l = line.strip()
                if not l: continue
                try: ev = json.loads(l)
                except: continue
                theorem = ev.get("theorem", "")
                series = THEOREM_TO_SERIES.get(theorem)
                if series is None: continue
                verb_pairs = [(v, "") for v in SERIES_TO_VERBS.get(series, [])]
                events.append({"ts": parse_ts(ev.get("ts", 0)), "source": "theorem", "verbs": verb_pairs})
    return events


def compute_ratio(a, b, smooth=0.5):
    return (a + smooth) / (a + b + 2 * smooth)


def extract_state(verbs_list):
    explore_n = exploit_n = internal_n = external_n = 0
    micro_n = macro_n = positive_n = negative_n = past_n = future_n = 0
    depths = []
    for verb, mod in verbs_list:
        if verb in EXPLORE: explore_n += 1
        if verb in EXPLOIT: exploit_n += 1
        if verb in INTERNAL: internal_n += 1
        if verb in EXTERNAL: external_n += 1
        if verb in MICRO: micro_n += 1
        if verb in MACRO: macro_n += 1
        if verb in POSITIVE: positive_n += 1
        if verb in NEGATIVE: negative_n += 1
        if verb in PAST: past_n += 1
        if verb in FUTURE: future_n += 1
        depths.append(DEPTH_MAP.get(mod, 0.5))
    return np.array([
        compute_ratio(explore_n, exploit_n),
        np.mean(depths) if depths else 0.5,
        compute_ratio(internal_n, external_n),
        compute_ratio(micro_n, macro_n),
        compute_ratio(positive_n, negative_n),
        compute_ratio(past_n, future_n),
    ])


def windowed_states(events, window_size, stride):
    states = []
    for i in range(0, len(events) - window_size + 1, stride):
        window = events[i:i+window_size]
        all_verbs = []
        for ev in window:
            all_verbs.extend(ev["verbs"])
        if all_verbs:
            states.append(extract_state(all_verbs))
    return np.array(states) if states else np.empty((0, 6))


def fit_var1(X):
    Xt = X[:-1]; Xt1 = X[1:]
    MT = np.linalg.lstsq(Xt, Xt1, rcond=None)[0]
    M = MT.T
    res = Xt1 - Xt @ MT
    return M, np.cov(res, rowvar=False)


# ─── 診断 ───

def diagnose_ep():
    print("=" * 72)
    print("EP 計算手法の診断")
    print("=" * 72)

    # データロード
    tape = load_tape(TRACES_DIR)
    theorem = load_theorem(LOGS_DIR)
    all_events = tape + theorem
    all_events.sort(key=lambda e: e["ts"])

    X = windowed_states(all_events, 20, 5)
    labels = ["Function", "Precision", "Value", "Scale", "Valence", "Temporality"]
    stds = X.std(axis=0)
    active_mask = stds > 0.005
    active_labels = [l for l, m in zip(labels, active_mask) if m]
    X_active = X[:, active_mask]
    d = X_active.shape[1]
    N = X_active.shape[0]

    print(f"\nデータ: {N} states × {d}D ({', '.join(active_labels)})")

    # ── 診断 1: Σ_state の条件数 ──
    print(f"\n{'─'*72}")
    print("診断 1: Σ_state の条件数")
    print(f"{'─'*72}")

    Sigma_state = np.cov(X_active, rowvar=False)
    eigs_sigma = np.linalg.eigvalsh(Sigma_state)
    kappa = np.max(eigs_sigma) / np.min(eigs_sigma) if np.min(eigs_sigma) > 0 else float('inf')

    print(f"  Σ_state 固有値: {', '.join(f'{e:.6f}' for e in sorted(eigs_sigma))}")
    print(f"  条件数 κ(Σ): {kappa:.1f}")
    print(f"  最小固有値: {np.min(eigs_sigma):.8f}")

    if kappa > 100:
        print(f"  → ⚠️ 条件数が高い。Σ^{{-1}} が不安定。EP 計算が数値的に不安定な可能性")
    else:
        print(f"  → ✅ 条件数は許容範囲")

    # ── 診断 2: EP 計算の分解 ──
    print(f"\n{'─'*72}")
    print("診断 2: EP 計算の分解")
    print(f"{'─'*72}")

    M, Sigma_eps = fit_var1(X_active)
    B = M - np.eye(d)
    S = 0.5 * (B + B.T)
    Q = 0.5 * (B - B.T)

    # 点推定 EP
    Sigma_inv = np.linalg.inv(Sigma_state)
    EP_point = np.trace(Q @ Sigma_state @ Q.T @ Sigma_inv)

    # EP の各項分解
    QSQT = Q @ Sigma_state @ Q.T
    product = QSQT @ Sigma_inv
    print(f"  Q:")
    for i in range(d):
        print(f"    [{' '.join(f'{Q[i,j]:9.5f}' for j in range(d))}]")

    print(f"\n  ‖Q‖_F = {np.linalg.norm(Q, 'fro'):.6f}")
    print(f"  ‖Σ‖_F = {np.linalg.norm(Sigma_state, 'fro'):.6f}")
    print(f"  ‖Σ^(-1)‖_F = {np.linalg.norm(Sigma_inv, 'fro'):.6f}")

    print(f"\n  Q Σ Q^T:")
    for i in range(d):
        print(f"    [{' '.join(f'{QSQT[i,j]:12.8f}' for j in range(d))}]")

    print(f"\n  Q Σ Q^T Σ^(-1):")
    for i in range(d):
        print(f"    [{' '.join(f'{product[i,j]:12.8f}' for j in range(d))}]")

    print(f"\n  tr(Q Σ Q^T Σ^(-1)) = EP_point = {EP_point:.6f}")

    # EP の対角項分解
    diag_contributions = np.diag(product)
    print(f"\n  EP 対角項の寄与:")
    for i, l in enumerate(active_labels):
        print(f"    {l:14s}: {diag_contributions[i]:.6f} ({100*diag_contributions[i]/EP_point:.1f}%)")

    # ── 診断 3: 代替 EP 定式化 ──
    print(f"\n{'─'*72}")
    print("診断 3: 代替 EP 定式化")
    print(f"{'─'*72}")

    # EP_alt1: ep = sum_i sum_j Q_ij^2 (単純な循環量)
    EP_alt1 = np.sum(Q ** 2)
    print(f"  EP_alt1 = ΣQ²            = {EP_alt1:.6f}")

    # EP_alt2: ep = tr(Q^T Q) = ‖Q‖²_F
    EP_alt2 = np.trace(Q.T @ Q)
    print(f"  EP_alt2 = tr(Q^T Q)      = {EP_alt2:.6f}")

    # EP_alt3: 正規化 EP = EP / d
    EP_alt3 = EP_point / d
    print(f"  EP_alt3 = EP/d           = {EP_alt3:.6f}")

    # EP_alt4: Σ_eps ベース (残差の共分散を使う)
    try:
        Sigma_eps_inv = np.linalg.inv(Sigma_eps)
        EP_alt4 = np.trace(Q @ Sigma_eps @ Q.T @ Sigma_eps_inv)
        print(f"  EP_alt4 = tr(QΣ_εQ^TΣ_ε^-1)  = {EP_alt4:.6f}  (Σ_ε = 残差共分散)")
    except:
        print(f"  EP_alt4: 計算不可 (Σ_ε 特異)")

    # ── 診断 4: Bootstrap の問題 ──
    print(f"\n{'─'*72}")
    print("診断 4: iid vs Block Bootstrap")
    print(f"{'─'*72}")

    rng = np.random.RandomState(42)
    N_BOOT = 300

    # iid Bootstrap (元のコードと同じ)
    iid_eps = []
    for _ in range(N_BOOT):
        idx = rng.choice(N, size=N, replace=True)
        X_boot = X_active[idx]
        try:
            M_b, _ = fit_var1(X_boot)
            B_b = M_b - np.eye(d)
            Q_b = 0.5 * (B_b - B_b.T)
            Sig_b = np.cov(X_boot, rowvar=False)
            Sig_inv_b = np.linalg.inv(Sig_b)
            ep = np.trace(Q_b @ Sig_b @ Q_b.T @ Sig_inv_b)
            iid_eps.append(ep)
        except:
            continue

    # Block Bootstrap (ブロックサイズ = sqrt(N))
    block_size = max(3, int(np.sqrt(N)))
    block_eps = []
    for _ in range(N_BOOT):
        # ブロックランダムサンプリング
        n_blocks = (N + block_size - 1) // block_size
        starts = rng.choice(N - block_size + 1, size=n_blocks, replace=True)
        idx = np.concatenate([np.arange(s, min(s + block_size, N)) for s in starts])[:N]
        X_boot = X_active[idx]
        try:
            M_b, _ = fit_var1(X_boot)
            B_b = M_b - np.eye(d)
            Q_b = 0.5 * (B_b - B_b.T)
            Sig_b = np.cov(X_boot, rowvar=False)
            Sig_inv_b = np.linalg.inv(Sig_b)
            ep = np.trace(Q_b @ Sig_b @ Q_b.T @ Sig_inv_b)
            block_eps.append(ep)
        except:
            continue

    # Residual Bootstrap (VAR(1) 残差のリサンプリング → 時系列再構成)
    resid_eps = []
    # 原データで VAR(1) フィット
    Xt = X_active[:-1]; Xt1 = X_active[1:]
    MT_orig = np.linalg.lstsq(Xt, Xt1, rcond=None)[0]
    residuals = Xt1 - Xt @ MT_orig
    for _ in range(N_BOOT):
        # 残差をリサンプリング
        idx_r = rng.choice(residuals.shape[0], size=residuals.shape[0], replace=True)
        resid_boot = residuals[idx_r]
        # 時系列再構成
        X_syn = np.zeros_like(X_active)
        X_syn[0] = X_active[rng.randint(N)]  # ランダム初期値
        for t in range(residuals.shape[0]):
            X_syn[t+1] = X_syn[t] @ MT_orig + resid_boot[t]
        try:
            M_b, _ = fit_var1(X_syn)
            B_b = M_b - np.eye(d)
            Q_b = 0.5 * (B_b - B_b.T)
            Sig_b = np.cov(X_syn, rowvar=False)
            Sig_inv_b = np.linalg.inv(Sig_b)
            ep = np.trace(Q_b @ Sig_b @ Q_b.T @ Sig_inv_b)
            resid_eps.append(ep)
        except:
            continue

    iid_eps = np.array(iid_eps)
    block_eps = np.array(block_eps)
    resid_eps = np.array(resid_eps)

    def report_bootstrap(name, eps):
        if len(eps) == 0:
            print(f"  {name}: 計算失敗")
            return
        lo, med, hi = np.percentile(eps, [2.5, 50, 97.5])
        print(f"  {name:20s}: median={med:.4f}  95%CI=[{lo:.4f}, {hi:.4f}]  "
              f"mean={eps.mean():.4f}  std={eps.std():.4f}  N_valid={len(eps)}")

    report_bootstrap("iid Bootstrap", iid_eps)
    report_bootstrap("Block Bootstrap", block_eps)
    report_bootstrap("Residual Bootstrap", resid_eps)

    print(f"\n  点推定 EP: {EP_point:.4f}")
    print(f"\n  解釈:")
    if len(iid_eps) > 0 and len(resid_eps) > 0:
        ratio_iid = np.median(iid_eps) / EP_point if EP_point > 0 else float('inf')
        ratio_resid = np.median(resid_eps) / EP_point if EP_point > 0 else float('inf')
        print(f"    iid/点推定 = {ratio_iid:.1f}x")
        print(f"    Residual/点推定 = {ratio_resid:.1f}x")

        if ratio_iid > 3 and ratio_resid < 3:
            print(f"    → H1 支持: iid Bootstrap が時系列構造を破壊し EP を膨張")
            print(f"    → Residual Bootstrap が正しい推定法")
        elif ratio_resid > 3:
            print(f"    → H1 不支持: Residual でも膨張。EP 計算式自体の問題 (H2/H3)")
        else:
            print(f"    → 両手法で安定。点推定は過小評価の可能性")

    # ── 診断 5: 合成データでの検証 ──
    print(f"\n{'─'*72}")
    print("診断 5: 合成データでの EP 推定精度")
    print(f"{'─'*72}")

    # 既知のパラメータで OU 過程を生成
    d_syn = 5
    # 安定な B を構成
    B_true = np.diag([-0.2, -0.15, -0.25, -0.1, -0.3])
    # 適度な Q を追加
    Q_true = np.zeros((d_syn, d_syn))
    Q_true[0, 1] = 0.05; Q_true[1, 0] = -0.05
    Q_true[2, 3] = 0.08; Q_true[3, 2] = -0.08
    M_true = np.eye(d_syn) + B_true + Q_true

    # 真の EP を計算
    # OU 定常分布: Σ_ss = Lyapunov 方程式の解
    # 近似: 十分長い時系列で推定
    rng2 = np.random.RandomState(123)
    X_syn_long = np.zeros((10000, d_syn))
    X_syn_long[0] = rng2.randn(d_syn) * 0.1 + 0.5
    noise_cov = np.eye(d_syn) * 0.01
    L = np.linalg.cholesky(noise_cov)
    for t in range(9999):
        eps = L @ rng2.randn(d_syn)
        X_syn_long[t+1] = M_true @ X_syn_long[t] + eps

    # 真の EP (長い時系列から)
    M_est_long, _ = fit_var1(X_syn_long)
    B_est_long = M_est_long - np.eye(d_syn)
    Q_est_long = 0.5 * (B_est_long - B_est_long.T)
    Sig_long = np.cov(X_syn_long, rowvar=False)
    Sig_inv_long = np.linalg.inv(Sig_long)
    EP_true = np.trace(Q_est_long @ Sig_long @ Q_est_long.T @ Sig_inv_long)

    print(f"  合成データ: M_true の |λ| = {', '.join(f'{abs(e):.4f}' for e in np.linalg.eigvals(M_true))}")
    print(f"  EP_true (N=10000): {EP_true:.6f}")

    # N=539 (実データと同程度) でサブサンプル
    for N_sub in [100, 200, 539, 1000]:
        X_sub = X_syn_long[:N_sub]
        M_sub, _ = fit_var1(X_sub)
        B_sub = M_sub - np.eye(d_syn)
        Q_sub = 0.5 * (B_sub - B_sub.T)
        Sig_sub = np.cov(X_sub, rowvar=False)
        try:
            Sig_inv_sub = np.linalg.inv(Sig_sub)
            EP_sub = np.trace(Q_sub @ Sig_sub @ Q_sub.T @ Sig_inv_sub)
            ratio = EP_sub / EP_true if EP_true > 0 else float('inf')
            print(f"  N={N_sub:5d}: EP={EP_sub:.6f}  (ratio to true: {ratio:.2f}x)")
        except:
            print(f"  N={N_sub:5d}: 計算不可")

    # ── 診断 6: ウィンドウ重複効果 ──
    print(f"\n{'─'*72}")
    print("診断 6: ウィンドウ重複の影響")
    print(f"{'─'*72}")

    # 重複率を変えて EP を比較
    for win, stride in [(20, 5), (20, 10), (20, 15), (20, 20), (10, 5), (10, 10)]:
        X_w = windowed_states(all_events, win, stride)
        stds_w = X_w.std(axis=0)
        mask_w = stds_w > 0.005
        X_act_w = X_w[:, mask_w]
        if X_act_w.shape[0] < 10:
            print(f"  win={win:2d} stride={stride:2d}: データ不足 ({X_act_w.shape[0]})")
            continue
        M_w, _ = fit_var1(X_act_w)
        B_w = M_w - np.eye(X_act_w.shape[1])
        Q_w = 0.5 * (B_w - B_w.T)
        Sig_w = np.cov(X_act_w, rowvar=False)
        try:
            Sig_inv_w = np.linalg.inv(Sig_w)
            EP_w = np.trace(Q_w @ Sig_w @ Q_w.T @ Sig_inv_w)
            overlap = 1 - stride / win
            print(f"  win={win:2d} stride={stride:2d} (重複{100*overlap:.0f}%): "
                  f"N={X_act_w.shape[0]:4d} × {X_act_w.shape[1]}D  EP={EP_w:.6f}")
        except:
            print(f"  win={win:2d} stride={stride:2d}: 計算不可")

    # ── 最終判定 ──
    print(f"\n{'='*72}")
    print("最終判定")
    print(f"{'='*72}")


if __name__ == "__main__":
    diagnose_ep()
