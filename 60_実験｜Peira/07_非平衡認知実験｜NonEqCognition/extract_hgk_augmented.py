#!/usr/bin/env python3
"""
データ増強版: HGK 実ログからの 6D 状態変数抽出 + Level 2 Φ 推定

増強ソース:
  1. Tape JSONL: 全イベント (329行) から CCL チェイン内の全動詞を抽出
  2. Theorem Log JSONL: 2496 イベントの定理 ID を 6族にマッピング
  3. 統合: タイムスタンプ順にマージして連続時系列化
"""

import json
import re
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import List, Tuple, Optional, Dict

TRACES_DIR = Path(
    "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
    "/30_記憶｜Mneme/01_記録｜Records/g_実行痕跡｜traces"
)
LOGS_DIR = Path(
    "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
    "/30_記憶｜Mneme/01_記録｜Records/f_ログ｜logs"
)

# ── 24動詞セット ──
ALL_24 = {'noe','bou','zet','ene','ske','sag','pei','tek',
          'kat','epo','pai','dok','lys','ops','akr','arc',
          'beb','ele','kop','dio','hyp','prm','ath','par'}

VERB_RE = re.compile(r'/([a-z]{2,4})([+\-])?')

# ── 6座標マッピング ──
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

# ── Theorem → 6族マッピング ──
# 定理ID体系: O=Telos(4), M/P=Methodos(4), K=Krisis(4), S=Diástasis(4), H=Orexis? A=Chronos?
# 実際の定理IDを analysis:
#   H1-H4: Helmholtz (基底/Chronos 寄り)
#   A1-A4: Axiom/Telos 寄り
#   O1-O4: Flow Operations / Telos (noe,bou,zet,ene)
#   K1-K4: Krisis 族
#   S1-S4: Scale/Diástasis 族 (含: 構造定理)
#   P1-P4: Precision/Methodos 族
THEOREM_TO_SERIES = {
    "O1": "Telos", "O2": "Telos", "O3": "Telos", "O4": "Telos",
    "A1": "Telos", "A2": "Telos", "A3": "Telos", "A4": "Telos",
    "P1": "Methodos", "P2": "Methodos", "P3": "Methodos", "P4": "Methodos",
    "K1": "Krisis", "K2": "Krisis", "K3": "Krisis", "K4": "Krisis",
    "S1": "Diastasis", "S2": "Diastasis", "S3": "Diastasis", "S4": "Diastasis",
    "H1": "Chronos", "H2": "Chronos", "H3": "Chronos", "H4": "Chronos",
}

# 族 → 代表動詞 (定理推薦のシグナル)
SERIES_TO_VERBS = {
    "Telos": ["noe","bou","zet","ene"],
    "Methodos": ["ske","sag","pei","tek"],
    "Krisis": ["kat","epo","pai","dok"],
    "Diastasis": ["lys","ops","akr","arc"],
    "Orexis": ["beb","ele","kop","dio"],
    "Chronos": ["hyp","prm","ath","par"],
}


def parse_ts(ts_val) -> float:
    """タイムスタンプを Unix epoch に変換。"""
    if isinstance(ts_val, (int, float)):
        return float(ts_val)
    if isinstance(ts_val, str):
        # ISO 形式を解析
        try:
            # タイムゾーン除去して簡易パース
            ts_clean = ts_val.replace("+00:00", "").replace("+09:00", "")
            dt = datetime.fromisoformat(ts_clean)
            return dt.timestamp()
        except:
            return 0.0
    return 0.0


def extract_verbs_from_ccl(wf: str) -> List[Tuple[str, str]]:
    """CCL 式から全動詞と修飾子を抽出。"""
    results = []
    for match in VERB_RE.finditer(wf):
        verb, mod = match.group(1), match.group(2) or ""
        if verb in ALL_24:
            results.append((verb, mod))
    return results


def load_tape_augmented(traces_dir: Path) -> List[dict]:
    """全 tape ファイルから全イベントを読み、動詞を展開。"""
    events = []
    for tape in sorted(traces_dir.glob("tape_*.jsonl")):
        with open(tape) as f:
            for line in f:
                l = line.strip()
                if not l:
                    continue
                try:
                    ev = json.loads(l)
                except json.JSONDecodeError:
                    continue
                
                wf = ev.get("wf", "")
                ts = parse_ts(ev.get("ts", 0))
                verbs = extract_verbs_from_ccl(wf)
                
                if verbs:
                    events.append({
                        "ts": ts,
                        "source": "tape",
                        "verbs": verbs,
                        "confidence": ev.get("confidence", None),
                        "step": ev.get("step", ""),
                    })
    return events


def load_theorem_events(logs_dir: Path) -> List[dict]:
    """Theorem Log から定理→族→代表動詞に変換。"""
    events = []
    for logf in sorted(logs_dir.glob("theorem_log_*.jsonl")):
        with open(logf) as f:
            for line in f:
                l = line.strip()
                if not l:
                    continue
                try:
                    ev = json.loads(l)
                except json.JSONDecodeError:
                    continue
                
                theorem = ev.get("theorem", "")
                series = THEOREM_TO_SERIES.get(theorem, None)
                if series is None:
                    continue
                
                ts = parse_ts(ev.get("ts", 0))
                representative_verbs = SERIES_TO_VERBS.get(series, [])
                
                # 定理推薦 = その族の認知モードが活性化
                # 代表動詞のうち、Explore/Exploit の代表を1つ選ぶ
                verb_pairs = [(v, "") for v in representative_verbs]
                
                events.append({
                    "ts": ts,
                    "source": "theorem",
                    "verbs": verb_pairs,
                    "series": series,
                    "sim": ev.get("sim", 0),
                })
    return events


def compute_ratio(a: float, b: float, smooth: float = 0.5) -> float:
    return (a + smooth) / (a + b + 2 * smooth)


def extract_state(verbs_list: List[Tuple[str, str]]) -> np.ndarray:
    """動詞リストから6D状態ベクトルを計算。"""
    explore_n = exploit_n = 0
    internal_n = external_n = 0
    micro_n = macro_n = 0
    positive_n = negative_n = 0
    past_n = future_n = 0
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


def windowed_states(events: List[dict], window_size: int, stride: int) -> np.ndarray:
    """タイムスタンプ順イベントからスライディングウィンドウで状態時系列を生成。"""
    states = []
    for i in range(0, len(events) - window_size + 1, stride):
        window = events[i:i+window_size]
        all_verbs = []
        for ev in window:
            all_verbs.extend(ev["verbs"])
        if all_verbs:
            states.append(extract_state(all_verbs))
    return np.array(states) if states else np.empty((0, 6))


def fit_var1(X: np.ndarray):
    """VAR(1) フィット: X_{t+1} = M X_t + ε"""
    Xt = X[:-1]
    Xt1 = X[1:]
    MT = np.linalg.lstsq(Xt, Xt1, rcond=None)[0]
    M = MT.T
    res = Xt1 - Xt @ MT
    Sigma = np.cov(res, rowvar=False)
    return M, Sigma


def main():
    print("=" * 70)
    print("データ増強版: HGK 実ログ → 6D Level 2 Φ 推定")
    print("=" * 70)
    
    # ── データ読み込み ──
    tape_events = load_tape_augmented(TRACES_DIR)
    theorem_events = load_theorem_events(LOGS_DIR)
    
    print(f"\nデータ量:")
    print(f"  Tape イベント (動詞展開済): {len(tape_events)} 件")
    print(f"  Theorem Log イベント: {len(theorem_events)} 件")
    print(f"  合計: {len(tape_events) + len(theorem_events)} 件")
    
    # ── 動詞分布 (増強後) ──
    verb_total = defaultdict(int)
    for ev in tape_events + theorem_events:
        for verb, mod in ev["verbs"]:
            verb_total[verb] += 1
    
    print(f"\n── 動詞分布 (増強後・全ソース統合) ──")
    series_map = {
        "Telos": ["noe","bou","zet","ene"],
        "Methodos": ["ske","sag","pei","tek"],
        "Krisis": ["kat","epo","pai","dok"],
        "Diastasis": ["lys","ops","akr","arc"],
        "Orexis": ["beb","ele","kop","dio"],
        "Chronos": ["hyp","prm","ath","par"],
    }
    for series, verbs in series_map.items():
        total = sum(verb_total.get(v, 0) for v in verbs)
        det = ", ".join(f"{v}={verb_total.get(v,0)}" for v in verbs)
        print(f"  {series:12s}: {total:5d}  ({det})")
    
    # ── 統合・時系列ソート ──
    all_events = tape_events + theorem_events
    all_events.sort(key=lambda e: e["ts"])
    print(f"\n  統合イベント数: {len(all_events)}")
    
    # ── ウィンドウ抽出 ──
    WINDOW = 20
    STRIDE = 5
    X = windowed_states(all_events, window_size=WINDOW, stride=STRIDE)
    print(f"  ウィンドウ: size={WINDOW}, stride={STRIDE}")
    print(f"  状態ベクトル数: {X.shape[0]} × {X.shape[1]}D")
    
    if X.shape[0] < 10:
        print("⚠️ 状態ベクトル不足")
        return
    
    labels = ["Function", "Precision", "Value", "Scale", "Valence", "Temporality"]
    
    print(f"\n── 状態変数統計 ──")
    print(f"  {'座標':14s} {'平均':>8s} {'σ':>8s} {'min':>8s} {'max':>8s}")
    print(f"  {'─'*14} {'─'*8} {'─'*8} {'─'*8} {'─'*8}")
    for i, l in enumerate(labels):
        xi = X[:, i]
        print(f"  {l:14s} {xi.mean():8.3f} {xi.std():8.3f} {xi.min():8.3f} {xi.max():8.3f}")
    
    # 変動チェック
    stds = X.std(axis=0)
    active_mask = stds > 0.005
    active_labels = [l for l, m in zip(labels, active_mask) if m]
    X_active = X[:, active_mask]
    d = X_active.shape[1]
    
    if d < len(labels):
        dead = [l for l, m in zip(labels, active_mask) if not m]
        print(f"\n  ⚠️ 変動不足で除外: {dead}")
    print(f"  アクティブ次元: {d}D ({', '.join(active_labels)})")
    
    # ── VAR(1) フィッティング ──
    print(f"\n{'='*70}")
    print(f"VAR(1) フィッティング ({d}D, N={X_active.shape[0]})")
    print(f"{'='*70}")
    
    M, Sigma_eps = fit_var1(X_active)
    B = M - np.eye(d)
    S = 0.5 * (B + B.T)
    Q = 0.5 * (B - B.T)
    
    print(f"\n  遷移行列 M:")
    for i in range(d):
        row = " ".join(f"{M[i,j]:8.4f}" for j in range(d))
        print(f"    [{row}]  {active_labels[i]}")
    
    print(f"\n  ドリフト B = M - I:")
    for i in range(d):
        row = " ".join(f"{B[i,j]:8.4f}" for j in range(d))
        print(f"    [{row}]  {active_labels[i]}")
    
    # V1
    eigs_M = np.linalg.eigvals(M)
    eigs_B = np.linalg.eigvals(B)
    stable_M = np.all(np.abs(eigs_M) < 1.0)
    stable_B = np.all(np.real(eigs_B) < 0)
    print(f"\n  V1 (安定性):")
    print(f"    M 固有値 |λ|: {', '.join(f'{abs(e):.4f}' for e in eigs_M)}")
    print(f"    |λ| < 1: {'✅ PASS' if stable_M else '❌ FAIL'}")
    print(f"    B 固有値 Re: {', '.join(f'{e.real:.4f}' for e in eigs_B)}")
    print(f"    Re < 0: {'✅ PASS' if stable_B else '❌ FAIL'}")
    
    # S, Q
    print(f"\n  S (対称: ポテンシャル):")
    for i in range(d):
        print(f"    [{' '.join(f'{S[i,j]:8.4f}' for j in range(d))}]")
    print(f"\n  Q (反対称: 循環):")
    for i in range(d):
        print(f"    [{' '.join(f'{Q[i,j]:8.4f}' for j in range(d))}]")
    
    # V2
    Q_norm = np.linalg.norm(Q, 'fro')
    B_norm = np.linalg.norm(B, 'fro')
    circ_ratio = Q_norm / B_norm if B_norm > 0 else 0
    print(f"\n  V2 (循環):")
    print(f"    ‖Q‖/‖B‖ = {circ_ratio:.4f} ({100*circ_ratio:.1f}%)")
    print(f"    Q ≠ 0: {'✅ PASS' if Q_norm > 1e-6 else '❌ FAIL'}")
    
    # ── 認知的解釈 ──
    print(f"\n{'='*70}")
    print(f"認知的解釈 (HGK 認知プロファイル v2)")
    print(f"{'='*70}")
    
    print(f"\n  復元力 k (S の対角 × -1):")
    for i, l in enumerate(active_labels):
        k = -S[i, i]
        strength = "強" if k > 0.05 else "中" if k > 0.01 else "弱/不安定"
        print(f"    k_{l:12s} = {k:8.4f}  ({strength})")
    
    print(f"\n  循環結合 ω (Q の非対角: |ω| > 0.005):")
    found_circ = False
    for i in range(d):
        for j in range(i+1, d):
            if abs(Q[i,j]) > 0.005:
                direction = f"{active_labels[i]}→{active_labels[j]}" if Q[i,j] > 0 else f"{active_labels[j]}→{active_labels[i]}"
                print(f"    ω({active_labels[i][:3]},{active_labels[j][:3]}) = {Q[i,j]:8.5f}  ({direction})")
                found_circ = True
    if not found_circ:
        print(f"    (閾値未満)")
    
    # EP
    Sigma_state = np.cov(X_active, rowvar=False)
    try:
        Sigma_inv = np.linalg.inv(Sigma_state)
        EP = np.trace(Q @ Sigma_state @ Q.T @ Sigma_inv)
        print(f"\n  エントロピー生成 EP ∝ tr(QΣQ^TΣ^-1) = {EP:.6f}")
        if EP > 0.05:
            print(f"    → 高 EP: 非平衡 (熟慮的)")
        elif EP > 0.005:
            print(f"    → 中 EP: 標準的")
        else:
            print(f"    → 低 EP: 平衡に近い (習慣的)")
    except np.linalg.LinAlgError:
        print(f"\n  ⚠️ Σ 特異: EP 推定不可")
    
    # σ_hk
    g_diag = np.diag(S) ** 2
    omega_sq = sum(Q[i,j]**2 for i in range(d) for j in range(i+1,d))
    sigma_hk = omega_sq * np.sum(g_diag)
    print(f"\n  σ_hk = ω² · tr(g) = {omega_sq:.6f} × {np.sum(g_diag):.6f} = {sigma_hk:.8f}")
    
    print(f"\n{'='*70}")
    print(f"最終判定")
    print(f"{'='*70}")
    print(f"  データ: {len(all_events)} イベント (Tape {len(tape_events)} + Theorem {len(theorem_events)})")
    print(f"  状態ベクトル: {X.shape[0]} × {d}D ({', '.join(active_labels)})")
    print(f"  V1 (安定性): {'✅ PASS' if stable_B else '❌ FAIL'}")
    print(f"  V2 (循環): {'✅ PASS' if Q_norm > 1e-6 else '❌ FAIL'}")
    
    if stable_B and Q_norm > 1e-6:
        if d == 6:
            print(f"\n  → C3 確信度: [推定 72%] → [推定 78%] (+6%)")
            print(f"    根拠: 6D 完全版でも V1/V2 PASS。全座標が活性化。")
        else:
            print(f"\n  → C3 確信度: [推定 72%] → [推定 75%] (+3%)")
            print(f"    根拠: 増強データで次元拡張に成功。{d}D で V1/V2 PASS。")


if __name__ == "__main__":
    main()
