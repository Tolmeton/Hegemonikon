#!/usr/bin/env python3
"""Q-series データ品質診断スクリプト v2.0。

3つの分析モードを提供:
  - 全WF版: ユーティリティWF含む全遷移で ω̂ を算出
  - UTL除外版: 24動詞のみで ω̂ を算出 (セッション構造の人工物を排除)
  - 比較版: 両方を並べて差分を可視化

使用法:
  python3 q_data_diagnosis.py           # 比較版 (デフォルト)
  python3 q_data_diagnosis.py --all     # 全WF版
  python3 q_data_diagnosis.py --core    # UTL除外版 (24動詞限定)
"""
import json, glob, re, os, sys
from collections import Counter, defaultdict
from pathlib import Path

# === 定数 ===
BASE = Path(os.path.expanduser(
    "~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon"
))
TRACES = BASE / "30_記憶｜Mneme" / "01_記録｜Records" / "g_実行痕跡｜traces"
HANDOFF_DIR = BASE / "30_記憶｜Mneme" / "01_記録｜Records" / "a_引継｜handoff"

# 24動詞 → 6座標マッピング (24 Poiesis のみ)
CORE_WF_TO_COORD = {
    # Telos (Value)
    "noe": "Va", "bou": "Va", "zet": "Va", "ene": "Va",
    # Methodos (Function)
    "ske": "Fu", "sag": "Fu", "pei": "Fu", "tek": "Fu",
    # Krisis (Precision)
    "kat": "Pr", "epo": "Pr", "pai": "Pr", "dok": "Pr",
    # Diástasis (Scale)
    "lys": "Sc", "ops": "Sc", "akr": "Sc", "arc": "Sc",
    # Orexis (Valence)
    "beb": "Vl", "ele": "Vl", "kop": "Vl", "dio": "Vl",
    # Chronos (Temporality)
    "hyp": "Te", "prm": "Te", "ath": "Te", "par": "Te",
}

# ユーティリティWF (τ層) の座標マッピング
UTL_WF_TO_COORD = {
    "boot": "Te", "bye": "Te", "rom": "Te",
    "eat": "Va", "fit": "Va",
    "vet": "Pr", "dendron": "Pr", "basanos": "Pr",
    "hon": "Vl", "u": "Vl",
}

# ユーティリティWF 名のリスト (除外フィルタ用)
UTL_WFS = set(UTL_WF_TO_COORD.keys())

# 全WFマッピング (24動詞 + UTL)
ALL_WF_TO_COORD = {**CORE_WF_TO_COORD, **UTL_WF_TO_COORD}

COORDS = ["Va", "Fu", "Pr", "Sc", "Vl", "Te"]

# Q-series 辺定義 (15辺)
Q_EDGES = [
    ("Va", "Pr", "Q1"),  ("Va", "Fu", "Q2"),  ("Fu", "Pr", "Q3"),
    ("Va", "Sc", "Q4"),  ("Va", "Vl", "Q5"),  ("Va", "Te", "Q6"),
    ("Fu", "Sc", "Q7"),  ("Fu", "Vl", "Q8"),  ("Fu", "Te", "Q9"),
    ("Pr", "Sc", "Q10"), ("Pr", "Vl", "Q11"), ("Pr", "Te", "Q12"),
    ("Sc", "Vl", "Q13"), ("Sc", "Te", "Q14"), ("Vl", "Te", "Q15"),
]

# 補正後 ω (τ_Te=4.0, s=0.7)
OMEGA_CORRECTED = {
    "Q1": 0.36, "Q2": 0.29, "Q3": 0.42,
    "Q4": 0.13, "Q5": 0.13, "Q6": 0.72,
    "Q7": 0.17, "Q8": 0.17, "Q9": 0.96,
    "Q10": 0.21, "Q11": 0.21, "Q12": 1.20,
    "Q13": 0.11, "Q14": 0.60, "Q15": 0.60,
}

# === データ抽出関数 ===

def extract_tape_transitions(wf_map):
    """tape JSONL からの COMPLETE 遷移を抽出"""
    transitions = []
    wf_counts = Counter()
    
    for fp in sorted(TRACES.glob("tape_*.jsonl")):
        completes = []
        for line in open(fp):
            try:
                rec = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if rec.get("step") == "COMPLETE":
                wf_name = rec.get("workflow_name", "")
                if wf_name in wf_map:
                    completes.append(wf_name)
                    wf_counts[wf_name] += 1
        
        # 連続 COMPLETE 間の遷移を抽出
        for i in range(len(completes) - 1):
            src = wf_map[completes[i]]
            dst = wf_map[completes[i+1]]
            transitions.append(("tape", src, dst, completes[i], completes[i+1]))
    
    return transitions, wf_counts

def extract_handoff_transitions(wf_map):
    """Handoff MD から CCL 動詞遷移を抽出"""
    transitions = []
    ccl_pattern = re.compile(r'(?<![/\w])/(' + '|'.join(wf_map.keys()) + r')[+-]?\b')
    path_pattern = re.compile(r'(?:file://|\.md|\.py|\.yaml|\.json|/\w+/\w+/)')
    
    total_files = 0
    for subdir in ["2026-02", "2026-03"]:
        d = HANDOFF_DIR / subdir
        if not d.exists():
            continue
        for fp in sorted(d.glob("*.md")):
            total_files += 1
            verbs = []
            for line in open(fp, errors='replace'):
                if path_pattern.search(line):
                    if not line.strip().startswith('/'):
                        continue
                for m in ccl_pattern.finditer(line):
                    verb = m.group(1).rstrip('+-')
                    if verb in wf_map:
                        verbs.append(verb)
            
            for i in range(len(verbs) - 1):
                src = wf_map[verbs[i]]
                dst = wf_map[verbs[i+1]]
                transitions.append(("handoff", src, dst, verbs[i], verbs[i+1]))
    
    return transitions, total_files

def build_matrix(transitions):
    """遷移行列を構築"""
    matrix = defaultdict(lambda: defaultdict(int))
    for _, src, dst, _, _ in transitions:
        matrix[src][dst] += 1
    return matrix

def compute_q_stats(matrix):
    """Q辺ごとの統計を計算"""
    results = []
    for c1, c2, qname in Q_EDGES:
        fwd = matrix[c1][c2]
        rev = matrix[c2][c1]
        n = fwd + rev
        if n > 0:
            omega_hat = abs(fwd - rev) / n
            direction = f"{c1}→{c2}" if fwd >= rev else f"{c2}→{c1}"
        else:
            omega_hat = None
            direction = "—"
        
        omega_corr = OMEGA_CORRECTED.get(qname, 0)
        residual = abs(omega_corr - omega_hat) if omega_hat is not None else None
        
        results.append({
            "q": qname, "c1": c1, "c2": c2,
            "fwd": fwd, "rev": rev, "n": n,
            "omega_hat": omega_hat, "direction": direction,
            "omega_corr": omega_corr, "residual": residual,
        })
    return results

def fmt_omega(val):
    """ω 値をフォーマット"""
    return f"{val:.2f}" if val is not None else "  —"

def print_q_table(stats, label=""):
    """Q辺統計テーブルを出力"""
    if label:
        print(f"\n## Q辺分析 ({label})")
    else:
        print(f"\n## Q辺分析")
    
    print(f"  {'Q':>4s}  {'辺':>10s}  {'n':>5s}  {'fwd':>4s}  {'rev':>4s}  {'ω̂':>6s}  {'ω(補正)':>8s}  {'残差':>6s}  {'方向':>10s}")
    print("  " + "-" * 68)
    
    for s in stats:
        omega_str = fmt_omega(s['omega_hat'])
        resid_str = fmt_omega(s['residual'])
        flag = ""
        if s['n'] <= 1:
            flag = " ⚠️n不足"
        elif s['residual'] is not None and s['residual'] > 0.25:
            flag = " ❌残差大"
        elif s['residual'] is not None and s['residual'] > 0.15:
            flag = " ⚠️残差"
        
        print(f"  {s['q']:>4s}  {s['c1']+'→'+s['c2']:>10s}  {s['n']:>5d}  {s['fwd']:>4d}  {s['rev']:>4d}  {omega_str:>6s}  {s['omega_corr']:>8.2f}  {resid_str:>6s}  {s['direction']:>10s}{flag}")

def print_comparison(stats_all, stats_core):
    """全WF版とUTL除外版の比較テーブル"""
    print(f"\n{'='*70}")
    print("全WF版 vs UTL除外版 (24動詞限定) 比較")
    print(f"{'='*70}")
    
    print(f"\n  {'Q':>4s}  {'辺':>10s}  {'n(全)':>6s}  {'ω̂(全)':>7s}  {'n(24)':>6s}  {'ω̂(24)':>7s}  {'Δω̂':>6s}  {'ω(補正)':>8s}  {'残差(全)':>8s}  {'残差(24)':>8s}")
    print("  " + "-" * 90)
    
    for sa, sc in zip(stats_all, stats_core):
        omega_all = fmt_omega(sa['omega_hat'])
        omega_core = fmt_omega(sc['omega_hat'])
        resid_all = fmt_omega(sa['residual'])
        resid_core = fmt_omega(sc['residual'])
        
        # Δω̂ = |ω̂(全) - ω̂(24)|
        if sa['omega_hat'] is not None and sc['omega_hat'] is not None:
            delta = abs(sa['omega_hat'] - sc['omega_hat'])
            delta_str = f"{delta:.2f}"
            flag = " ◆" if delta > 0.1 else ""
        else:
            delta_str = "  —"
            flag = ""
        
        print(f"  {sa['q']:>4s}  {sa['c1']+'→'+sa['c2']:>10s}  {sa['n']:>6d}  {omega_all:>7s}  {sc['n']:>6d}  {omega_core:>7s}  {delta_str:>6s}  {sa['omega_corr']:>8.2f}  {resid_all:>8s}  {resid_core:>8s}{flag}")
    
    # サマリー
    print(f"\n  ◆ = UTL除外で ω̂ が 0.10 以上変化した辺")
    
    # Te辺のRMSE比較
    te_resids_all = [sa['residual'] for sa in stats_all if ('Te' in sa['c1'] or 'Te' in sa['c2']) and sa['residual'] is not None]
    te_resids_core = [sc['residual'] for sc in stats_core if ('Te' in sc['c1'] or 'Te' in sc['c2']) and sc['residual'] is not None]
    
    non_te_resids_all = [sa['residual'] for sa in stats_all if 'Te' not in sa['c1'] and 'Te' not in sa['c2'] and sa['residual'] is not None]
    non_te_resids_core = [sc['residual'] for sc in stats_core if 'Te' not in sc['c1'] and 'Te' not in sc['c2'] and sc['residual'] is not None]
    
    def rmse(vals):
        if not vals:
            return float('nan')
        return (sum(v**2 for v in vals) / len(vals)) ** 0.5
    
    print(f"\n  Te辺 RMSE:    全WF={rmse(te_resids_all):.3f}  UTL除外={rmse(te_resids_core):.3f}")
    print(f"  非Te辺 RMSE:  全WF={rmse(non_te_resids_all):.3f}  UTL除外={rmse(non_te_resids_core):.3f}")
    print(f"  全辺 RMSE:    全WF={rmse([s['residual'] for s in stats_all if s['residual'] is not None]):.3f}  UTL除外={rmse([s['residual'] for s in stats_core if s['residual'] is not None]):.3f}")

def print_data_summary(tape_trans, handoff_trans, tape_wf, label=""):
    """データソース概要を出力"""
    all_trans = tape_trans + handoff_trans
    
    print(f"\n{'='*70}")
    print(f"Q-series データ品質診断 {label}")
    print(f"{'='*70}")
    
    print(f"\n## データソース")
    print(f"  tape COMPLETE: {len(tape_trans)} 遷移")
    print(f"  handoff:       {len(handoff_trans)} 遷移")
    print(f"  合計:          {len(all_trans)} 遷移")
    
    matrix = build_matrix(all_trans)
    total = sum(matrix[s][d] for s in COORDS for d in COORDS)
    self_t = sum(matrix[c][c] for c in COORDS)
    print(f"  自己遷移率:    {100*self_t/total:.1f}%" if total > 0 else "")
    
    return all_trans, matrix

# === メイン ===
if __name__ == "__main__":
    mode = "compare"  # デフォルト: 比較モード
    if "--all" in sys.argv:
        mode = "all"
    elif "--core" in sys.argv:
        mode = "core"
    
    print("tape 遷移を抽出中...")
    
    if mode in ("all", "compare"):
        tape_all, wf_all = extract_tape_transitions(ALL_WF_TO_COORD)
        handoff_all, _ = extract_handoff_transitions(ALL_WF_TO_COORD)
    
    if mode in ("core", "compare"):
        tape_core, wf_core = extract_tape_transitions(CORE_WF_TO_COORD)
        handoff_core, _ = extract_handoff_transitions(CORE_WF_TO_COORD)
    
    if mode == "all":
        all_trans, matrix = print_data_summary(tape_all, handoff_all, wf_all, "(全WF版)")
        stats = compute_q_stats(matrix)
        print_q_table(stats, "全WF版")
    
    elif mode == "core":
        all_trans, matrix = print_data_summary(tape_core, handoff_core, wf_core, "(24動詞限定)")
        stats = compute_q_stats(matrix)
        print_q_table(stats, "24動詞限定")
    
    else:  # compare
        print("handoff 遷移を抽出中...")
        
        # 全WF版
        all_trans_a, matrix_a = print_data_summary(tape_all, handoff_all, wf_all, "(全WF版)")
        stats_all = compute_q_stats(matrix_a)
        
        # UTL除外版
        all_trans_c, matrix_c = print_data_summary(tape_core, handoff_core, wf_core, "(24動詞限定)")
        stats_core = compute_q_stats(matrix_c)
        
        # 比較テーブル
        print_comparison(stats_all, stats_core)
        
        # Q15 の内訳比較
        print(f"\n## Q15 内訳変化")
        q15_all = Counter()
        for _, src, dst, ws, wd in all_trans_a:
            if (src == "Vl" and dst == "Te") or (src == "Te" and dst == "Vl"):
                q15_all[f"{ws}→{wd}"] += 1
        q15_core = Counter()
        for _, src, dst, ws, wd in all_trans_c:
            if (src == "Vl" and dst == "Te") or (src == "Te" and dst == "Vl"):
                q15_core[f"{ws}→{wd}"] += 1
        
        print(f"  全WF版 Q15 上位:")
        for pair, cnt in q15_all.most_common(5):
            utl_mark = " [UTL]" if any(w in UTL_WFS for w in pair.split("→")) else ""
            print(f"    {pair}: {cnt}{utl_mark}")
        print(f"  24動詞限定 Q15 上位:")
        for pair, cnt in q15_core.most_common(5):
            print(f"    {pair}: {cnt}")
