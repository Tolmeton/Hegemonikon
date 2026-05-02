#!/usr/bin/env python3
"""
矛盾1 対応: Theorem Log 重み α の感度分析

Tape (重み=1.0) + Theorem Log (重み=α) で状態ベクトルを構築し、
α={0, 0.1, 0.3, 0.5, 0.7, 1.0} の6条件で k, ω, EP, circ_ratio を比較。

α=0 は Tape のみ (v1 相当)、α=1 は均等重み (v2 相当)。

加えて矛盾2 対応: Bootstrap N=500 で EP の 95% CI を推定。
"""

import json
import re
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple

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
MICRO = {"lys","akr"}
MACRO = {"ops","arc"}
POSITIVE = {"beb","kop"}
NEGATIVE = {"ele","dio"}
PAST = {"hyp","ath"}
FUTURE = {"prm","par"}
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
    if isinstance(ts_val, (int, float)):
        return float(ts_val)
    if isinstance(ts_val, str):
        try:
            ts_clean = ts_val.replace("+00:00", "").replace("+09:00", "")
            dt = datetime.fromisoformat(ts_clean)
            return dt.timestamp()
        except:
            return 0.0
    return 0.0


def extract_verbs_from_ccl(wf: str) -> List[Tuple[str, str]]:
    results = []
    for match in VERB_RE.finditer(wf):
        verb, mod = match.group(1), match.group(2) or ""
        if verb in ALL_24:
            results.append((verb, mod))
    return results


def load_tape(traces_dir: Path) -> List[dict]:
    events = []
    for tape in sorted(traces_dir.glob("tape_*.jsonl")):
        with open(tape) as f:
            for line in f:
                l = line.strip()
                if not l: continue
                try:
                    ev = json.loads(l)
                except json.JSONDecodeError:
                    continue
                wf = ev.get("wf", "")
                ts = parse_ts(ev.get("ts", 0))
                verbs = extract_verbs_from_ccl(wf)
                if verbs:
                    events.append({"ts": ts, "source": "tape", "verbs": verbs})
    return events


def load_theorem(logs_dir: Path) -> List[dict]:
    events = []
    for logf in sorted(logs_dir.glob("theorem_log_*.jsonl")):
        with open(logf) as f:
            for line in f:
                l = line.strip()
                if not l: continue
                try:
                    ev = json.loads(l)
                except json.JSONDecodeError:
                    continue
                theorem = ev.get("theorem", "")
                series = THEOREM_TO_SERIES.get(theorem)
                if series is None: continue
                ts = parse_ts(ev.get("ts", 0))
                verb_pairs = [(v, "") for v in SERIES_TO_VERBS.get(series, [])]
                events.append({"ts": ts, "source": "theorem", "verbs": verb_pairs, "series": series})
    return events


def compute_ratio(a: float, b: float, smooth: float = 0.5) -> float:
    return (a + smooth) / (a + b + 2 * smooth)


def extract_state_weighted(verbs_weights: List[Tuple[str, str, float]]) -> np.ndarray:
    """重み付き動詞リストから6D状態ベクトルを計算。"""
    explore_w = exploit_w = 0.0
    internal_w = external_w = 0.0
    micro_w = macro_w = 0.0
    positive_w = negative_w = 0.0
    past_w = future_w = 0.0
    depth_sum = 0.0
    weight_sum = 0.0

    for verb, mod, w in verbs_weights:
        if verb in EXPLORE: explore_w += w
        if verb in EXPLOIT: exploit_w += w
        if verb in INTERNAL: internal_w += w
        if verb in EXTERNAL: external_w += w
        if verb in MICRO: micro_w += w
        if verb in MACRO: macro_w += w
        if verb in POSITIVE: positive_w += w
        if verb in NEGATIVE: negative_w += w
        if verb in PAST: past_w += w
        if verb in FUTURE: future_w += w
        depth_sum += DEPTH_MAP.get(mod, 0.5) * w
        weight_sum += w

    smooth = 0.5
    return np.array([
        (explore_w + smooth) / (explore_w + exploit_w + 2 * smooth),
        depth_sum / weight_sum if weight_sum > 0 else 0.5,
        (internal_w + smooth) / (internal_w + external_w + 2 * smooth),
        (micro_w + smooth) / (micro_w + macro_w + 2 * smooth),
        (positive_w + smooth) / (positive_w + negative_w + 2 * smooth),
        (past_w + smooth) / (past_w + future_w + 2 * smooth),
    ])


def windowed_states_weighted(events: List[dict], alpha: float,
                              window_size: int, stride: int) -> np.ndarray:
    """重み α を適用してスライディングウィンドウ → 状態時系列。"""
    states = []
    for i in range(0, len(events) - window_size + 1, stride):
        window = events[i:i+window_size]
        all_vw = []
        for ev in window:
            w = 1.0 if ev["source"] == "tape" else alpha
            if w <= 0:
                continue
            for verb, mod in ev["verbs"]:
                all_vw.append((verb, mod, w))
        if all_vw:
            states.append(extract_state_weighted(all_vw))
    return np.array(states) if states else np.empty((0, 6))


def fit_var1(X: np.ndarray):
    Xt = X[:-1]
    Xt1 = X[1:]
    MT = np.linalg.lstsq(Xt, Xt1, rcond=None)[0]
    M = MT.T
    res = Xt1 - Xt @ MT
    Sigma = np.cov(res, rowvar=False)
    return M, Sigma


def analyze(X_active, active_labels, d):
    """B, S, Q, k, ω, EP, circ_ratio を計算して返す。"""
    M, Sigma_eps = fit_var1(X_active)
    B = M - np.eye(d)
    S = 0.5 * (B + B.T)
    Q = 0.5 * (B - B.T)

    # 復元力 k
    k_vals = {active_labels[i]: -S[i,i] for i in range(d)}

    # 循環比率
    Q_norm = np.linalg.norm(Q, 'fro')
    B_norm = np.linalg.norm(B, 'fro')
    circ_ratio = Q_norm / B_norm if B_norm > 0 else 0

    # 最大循環 ω
    max_omega = 0.0
    max_omega_pair = ""
    for i in range(d):
        for j in range(i+1, d):
            if abs(Q[i,j]) > max_omega:
                max_omega = abs(Q[i,j])
                max_omega_pair = f"{active_labels[i]}↔{active_labels[j]}"

    # 安定性
    eigs_B = np.linalg.eigvals(B)
    stable = np.all(np.real(eigs_B) < 0)
    min_re = np.min(np.real(eigs_B))

    # EP
    Sigma_state = np.cov(X_active, rowvar=False)
    try:
        Sigma_inv = np.linalg.inv(Sigma_state)
        EP = np.trace(Q @ Sigma_state @ Q.T @ Sigma_inv)
    except np.linalg.LinAlgError:
        EP = float('nan')

    return {
        "k": k_vals,
        "k_max_label": max(k_vals, key=k_vals.get),
        "k_max": max(k_vals.values()),
        "circ_ratio": circ_ratio,
        "max_omega": max_omega,
        "max_omega_pair": max_omega_pair,
        "stable": stable,
        "min_re": min_re,
        "EP": EP,
        "n_states": X_active.shape[0],
    }


def bootstrap_ep(X_active, n_boot=500, seed=42):
    """Bootstrap で EP の 95% CI を推定。"""
    rng = np.random.RandomState(seed)
    d = X_active.shape[1]
    eps_list = []
    for _ in range(n_boot):
        idx = rng.choice(X_active.shape[0], size=X_active.shape[0], replace=True)
        X_boot = X_active[idx]
        try:
            M_b, _ = fit_var1(X_boot)
            B_b = M_b - np.eye(d)
            Q_b = 0.5 * (B_b - B_b.T)
            Sigma_b = np.cov(X_boot, rowvar=False)
            Sigma_inv_b = np.linalg.inv(Sigma_b)
            ep_b = np.trace(Q_b @ Sigma_b @ Q_b.T @ Sigma_inv_b)
            eps_list.append(ep_b)
        except (np.linalg.LinAlgError, ValueError):
            continue
    eps = np.array(eps_list)
    return np.percentile(eps, 2.5), np.median(eps), np.percentile(eps, 97.5)


def main():
    print("=" * 72)
    print("矛盾1+2 対応: Theorem Log 重み α 感度分析 + Bootstrap EP")
    print("=" * 72)

    # データロード
    tape_events = load_tape(TRACES_DIR)
    theorem_events = load_theorem(LOGS_DIR)
    print(f"\nデータ: Tape {len(tape_events)} + Theorem {len(theorem_events)}")

    all_events_full = tape_events + theorem_events
    all_events_full.sort(key=lambda e: e["ts"])

    labels = ["Function", "Precision", "Value", "Scale", "Valence", "Temporality"]

    # α = 0 は theorem を除外 (Tape のみ)
    ALPHAS = [0.0, 0.1, 0.3, 0.5, 0.7, 1.0]
    WINDOW = 20
    STRIDE = 5

    results = []

    for alpha in ALPHAS:
        # α=0 の場合、Theorem イベントは重み 0 → 実質 Tape のみ
        if alpha == 0:
            events = tape_events.copy()
            events.sort(key=lambda e: e["ts"])
            # Tape のみだと少ないので window を小さくする
            win = 10
            stride = 3
        else:
            events = all_events_full
            win = WINDOW
            stride = STRIDE

        X = windowed_states_weighted(events, alpha, win, stride)
        if X.shape[0] < 10:
            print(f"\n  α={alpha}: ⚠️ データ不足 ({X.shape[0]} states)")
            continue

        stds = X.std(axis=0)
        active_mask = stds > 0.005
        active_labels = [l for l, m in zip(labels, active_mask) if m]
        X_active = X[:, active_mask]
        d = X_active.shape[1]

        res = analyze(X_active, active_labels, d)
        res["alpha"] = alpha
        res["dim"] = d
        res["active"] = ", ".join(active_labels)
        results.append(res)

    # 結果テーブル
    print(f"\n{'='*72}")
    print(f"感度分析結果")
    print(f"{'='*72}")

    print(f"\n{'α':>5s} {'dim':>3s} {'n':>5s} {'V1':>4s} {'k_max':>8s} {'k_max_label':>14s} "
          f"{'circ%':>7s} {'max_ω':>8s} {'ω_pair':>18s} {'EP':>8s}")
    print(f"{'─'*5} {'─'*3} {'─'*5} {'─'*4} {'─'*8} {'─'*14} {'─'*7} {'─'*8} {'─'*18} {'─'*8}")

    for r in results:
        v1 = "✅" if r["stable"] else "❌"
        print(f"{r['alpha']:5.1f} {r['dim']:3d} {r['n_states']:5d} {v1:>4s} "
              f"{r['k_max']:8.4f} {r['k_max_label']:>14s} "
              f"{100*r['circ_ratio']:6.1f}% {r['max_omega']:8.5f} {r['max_omega_pair']:>18s} "
              f"{r['EP']:8.4f}")

    # k の順位変化を詳細表示
    print(f"\n{'='*72}")
    print(f"k (復元力) の詳細比較")
    print(f"{'='*72}")

    # 全 α で共通のラベルを取得 (最低限 4D)
    common_labels = ["Function", "Precision", "Value", "Valence"]
    header = f"{'α':>5s} " + " ".join(f"{l:>10s}" for l in common_labels) + f" {'k_max':>12s}"
    print(f"\n{header}")
    print(f"{'─'*5} " + " ".join(f"{'─'*10}" for _ in common_labels) + f" {'─'*12}")

    for r in results:
        vals = []
        for l in common_labels:
            v = r["k"].get(l, float('nan'))
            vals.append(f"{v:10.4f}" if not np.isnan(v) else f"{'N/A':>10s}")
        k_max = r["k_max_label"]
        print(f"{r['alpha']:5.1f} " + " ".join(vals) + f" {k_max:>12s}")

    # Bootstrap EP (矛盾2)
    print(f"\n{'='*72}")
    print(f"矛盾2: Bootstrap EP 95% CI (N=500)")
    print(f"{'='*72}")

    for r in results:
        alpha = r["alpha"]
        if alpha == 0:
            events = tape_events.copy()
            events.sort(key=lambda e: e["ts"])
            win, stride = 10, 3
        else:
            events = all_events_full
            win, stride = WINDOW, STRIDE

        X = windowed_states_weighted(events, alpha, win, stride)
        stds = X.std(axis=0)
        active_mask = stds > 0.005
        X_active = X[:, active_mask]

        lo, med, hi = bootstrap_ep(X_active, n_boot=500)
        print(f"  α={alpha:.1f}: EP median={med:.4f}  95% CI=[{lo:.4f}, {hi:.4f}]")

    # 最終判定
    print(f"\n{'='*72}")
    print(f"感度分析の結論")
    print(f"{'='*72}")

    # k_max_label が α によって変わるか
    k_labels = [r["k_max_label"] for r in results]
    k_stable = len(set(k_labels)) == 1
    print(f"\n  k_max ラベル安定性: {k_labels}")
    if k_stable:
        print(f"    → ✅ 全 α で {k_labels[0]} が最強。結論は α に依存しない")
    else:
        print(f"    → ⚠️ k_max ラベルが α で変化。結論は α 依存")
        # 転換点を特定
        for i in range(1, len(results)):
            if results[i]["k_max_label"] != results[i-1]["k_max_label"]:
                print(f"      転換点: α={results[i-1]['alpha']}→{results[i]['alpha']} "
                      f"({results[i-1]['k_max_label']}→{results[i]['k_max_label']})")

    # V1 安定性
    v1_all = all(r["stable"] for r in results)
    print(f"\n  V1 安定性: {'✅ 全 α で PASS' if v1_all else '⚠️ 一部 FAIL'}")

    # circ_ratio の単調性
    circs = [r["circ_ratio"] for r in results]
    print(f"\n  circ_ratio 推移: {', '.join(f'{c:.3f}' for c in circs)}")

    # EP の推移
    eps = [r["EP"] for r in results]
    print(f"  EP 推移: {', '.join(f'{e:.4f}' for e in eps)}")


if __name__ == "__main__":
    main()
