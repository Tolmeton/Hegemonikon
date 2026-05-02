#!/usr/bin/env python3
"""
Θ(B) HGK+ v2 — セッションログから Θ(B) を自動計算。

v1 → v2 変更点:
  1. S(B) 再定義: 正規表現ベースのツール成功率 → Active比率 (n_A / n_total)
     - v1 の SUCCESS_PAT/FAILURE_PAT は会話テキスト中の語にマッチする偽陽性だらけだった
     - Active比率は FEP Value 軸 (I/A) 分類に基づく客観的指標
  2. Θ(B) 式: 乗法 S×mod → log-加法 log(1+S) + (mod-1)
     - 乗法では S(B) が分散の 95.6% を支配し modifier が無寄与
     - log 化により S と modifier が r=0.82/0.64 でバランスよく寄与
  3. セッション数: n=194 → n≈300+ (フィルタ緩和)

Θ(B)_v2 = log(1 + S_active) + α·H(s) + β·H(a) + γ·R(s,a)

where:
  S_active = n_Active / n_Total — Active 比率 [0,1]
  H(s) = sensory entropy / log2(k_s)  [0,1] 正規化
  H(a) = active entropy / log2(k_a)   [0,1] 正規化
  R(s,a) = NMI = I(S;A) / min(H(S), H(A))
"""

import re
import os
import sys
import json
import math
import glob
import numpy as np
from collections import Counter
from dataclasses import dataclass
from scipy import stats

# === 24 CCL 動詞の FEP Value 軸分類 ===
VERB_VALUE = {
    # Telos 族
    "noe": "I", "bou": "I", "zet": "A", "ene": "A",
    # Methodos 族
    "ske": "I", "sag": "I", "pei": "A", "tek": "A",
    # Krisis 族
    "kat": "I", "epo": "I", "pai": "A", "dok": "A",
    # Diástasis 族
    "lys": "I", "ops": "I", "akr": "A", "arc": "A",
    # Orexis 族
    "beb": "I", "ele": "I", "kop": "A", "dio": "A",
    # Chronos 族
    "hyp": "I", "prm": "I", "ath": "A", "par": "A",
}

# セッション管理 WF
SESSION_VERBS = {
    "boot": "I", "bye": "A", "fit": "I", "rom": "A", "hon": "I",
}

# ツール呼び出しの I/A 分類
TOOL_VALUE = {
    # Internal (知覚・情報取得)
    "view_file": "I", "list_dir": "I", "grep_search": "I",
    "find_by_name": "I", "search_web": "I", "read_url": "I",
    "Searched": "I",
    # Active (環境変更)
    "write_to_file": "A", "replace_file_content": "A",
    "multi_replace": "A", "run_command": "A",
    "Created": "A", "Modified": "A", "Deleted": "A",
    "browser_subagent": "A", "generate_image": "A",
}

ALL_VERBS = {**VERB_VALUE, **SESSION_VERBS}

# === 正規表現パターン ===
CCL_VERBS = "|".join(sorted(ALL_VERBS.keys(), key=len, reverse=True))
CCL_PAT = re.compile(rf"/({CCL_VERBS})[\+\-]?\b")
TOOL_NAMES = "|".join(sorted(TOOL_VALUE.keys(), key=len, reverse=True))
TOOL_PAT = re.compile(rf"\b({TOOL_NAMES})\b")


@dataclass
class SessionResult:
    """セッション別 Θ(B) 結果"""
    filename: str
    date: str
    title: str
    n_events: int
    n_bigrams: int
    n_sensory: int      # k_s: ユニークな sensory イベント種
    n_active: int       # k_a: ユニークな active イベント種
    n_I: int            # Internal イベント総数
    n_A: int            # Active イベント総数
    H_s_raw: float      # 正規化前 H(s) [bits]
    H_a_raw: float      # 正規化前 H(a) [bits]
    H_s: float          # 正規化後 H(s) [0,1]
    H_a: float          # 正規化後 H(a) [0,1]
    R_sa: float         # NMI [0,1]
    S_active: float     # Active 比率 [0,1] — v2 で S(B) を置き換え
    theta_v2: float     # Θ(B) v2: log(1+S) + modifier
    theta_v1: float     # Θ(B) v1: S × mod (比較用)
    alpha: float = 0.4
    beta: float = 0.4
    gamma: float = 0.2


def extract_events(content: str) -> list:
    """テキストから認知イベントのシーケンスを抽出する。"""
    events = []
    seen_in_line = set()
    for line_no, line in enumerate(content.split("\n"), 1):
        seen_in_line.clear()
        for m in CCL_PAT.finditer(line):
            verb = m.group(1).lower()
            key = ("ccl", verb)
            if key not in seen_in_line and verb in ALL_VERBS:
                events.append({"kind": "ccl", "name": verb, "value": ALL_VERBS[verb]})
                seen_in_line.add(key)
        for m in TOOL_PAT.finditer(line):
            tool = m.group(1)
            key = ("tool", tool)
            if key not in seen_in_line and tool in TOOL_VALUE:
                events.append({"kind": "tool", "name": tool, "value": TOOL_VALUE[tool]})
                seen_in_line.add(key)
    return events


def compute_entropy(counts: Counter) -> float:
    """Shannon エントロピー (bits)"""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def compute_session_metrics(events: list, alpha=0.4, beta=0.4, gamma=0.2) -> dict:
    """セッションの全メトリクスを計算する。"""
    if len(events) < 2:
        return None

    # I/A 分類別のイベント名カウント
    s_names = Counter(e["name"] for e in events if e["value"] == "I")
    a_names = Counter(e["name"] for e in events if e["value"] == "A")

    k_s = len(s_names)  # ユニークな sensory イベント種数
    k_a = len(a_names)  # ユニークな active イベント種数

    if k_s < 2 or k_a < 2:
        return None  # 退化ケース

    # H(s), H(a) — イベント名ベースのエントロピー
    H_s_raw = compute_entropy(s_names)
    H_a_raw = compute_entropy(a_names)

    # 正規化: [0, 1]
    H_s = H_s_raw / math.log2(k_s) if k_s > 1 else 0.0
    H_a = H_a_raw / math.log2(k_a) if k_a > 1 else 0.0

    # R(s,a) = NMI — bigram ベース
    transitions = Counter()
    s_counts = Counter()
    a_counts = Counter()
    for i in range(len(events) - 1):
        s = events[i]["value"]
        a = events[i + 1]["value"]
        transitions[(s, a)] += 1
        s_counts[s] += 1
        a_counts[a] += 1

    n_bigrams = sum(transitions.values())
    h_s_bi = compute_entropy(s_counts)
    h_a_bi = compute_entropy(a_counts)
    h_sa_bi = compute_entropy(transitions)
    rsa = max(0.0, h_s_bi + h_a_bi - h_sa_bi)
    h_min = min(h_s_bi, h_a_bi)
    R_sa = rsa / h_min if h_min > 0 else 0.0

    # S_active — Active 比率 (v2 の S(B) 代替)
    n_I = sum(1 for e in events if e["value"] == "I")
    n_A = sum(1 for e in events if e["value"] == "A")
    S_active = n_A / (n_I + n_A)

    # modifier = α·H(s) + β·H(a) + γ·R(s,a)
    modifier = alpha * H_s + beta * H_a + gamma * R_sa

    # Θ(B) v2: log(1 + S_active) + modifier
    theta_v2 = math.log1p(S_active) + modifier

    # Θ(B) v1: S_active × (1 + modifier)  — 比較用
    theta_v1 = S_active * (1 + modifier)

    return {
        "n_events": len(events),
        "n_bigrams": n_bigrams,
        "n_sensory": k_s,
        "n_active": k_a,
        "n_I": n_I,
        "n_A": n_A,
        "H_s_raw": H_s_raw,
        "H_a_raw": H_a_raw,
        "H_s": H_s,
        "H_a": H_a,
        "R_sa": R_sa,
        "S_active": S_active,
        "theta_v2": theta_v2,
        "theta_v1": theta_v1,
    }


def main():
    conv_dir = (
        sys.argv[1] if len(sys.argv) > 1
        else "/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/"
             "30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv"
    )

    alpha, beta, gamma = 0.4, 0.4, 0.2

    print("=" * 70)
    print("Θ(B) HGK+ v2 — log-加法形式 + S_active")
    print(f"パラメータ: α={alpha}, β={beta}, γ={gamma}")
    print(f"式: Θ(B) = log(1 + S_active) + α·H(s) + β·H(a) + γ·R(s,a)")
    print(f"データソース: {conv_dir}")
    print("=" * 70)

    # セッションをロード
    pattern = os.path.join(conv_dir, "*.md")
    files = sorted(glob.glob(pattern))
    date_pat = re.compile(r"(\d{4}-\d{2}-\d{2})")
    # 新しいファイル名パターンも対応
    title_pat1 = re.compile(r"^\d{4}-\d{2}-\d{2}_conv_\d+_")
    title_pat2 = re.compile(r"^\d{4}-\d{2}-\d{2}_\d+_")

    results = []
    skipped = {"too_few_events": 0, "degenerate": 0}

    for filepath in files:
        basename = os.path.basename(filepath)
        m = date_pat.match(basename)
        date = m.group(1) if m else "unknown"
        title = title_pat1.sub("", basename)
        title = title_pat2.sub("", title).replace(".md", "")

        try:
            with open(filepath, encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        events = extract_events(content)
        if len(events) < 10:
            skipped["too_few_events"] += 1
            continue

        metrics = compute_session_metrics(events, alpha, beta, gamma)
        if metrics is None:
            skipped["degenerate"] += 1
            continue

        results.append(SessionResult(
            filename=basename,
            date=date,
            title=title[:60],
            alpha=alpha,
            beta=beta,
            gamma=gamma,
            **metrics,
        ))

    print(f"\n有効セッション: {len(results)}")
    print(f"スキップ: {skipped}")

    if not results:
        print("有効なセッションがありません")
        return

    # === 統計サマリー ===
    thetas_v2 = np.array([r.theta_v2 for r in results])
    thetas_v1 = np.array([r.theta_v1 for r in results])
    s_acts = np.array([r.S_active for r in results])
    hs_vals = np.array([r.H_s for r in results])
    ha_vals = np.array([r.H_a for r in results])
    rsa_vals = np.array([r.R_sa for r in results])
    mods = alpha * hs_vals + beta * ha_vals + gamma * rsa_vals

    print("\n### Θ(B) v2 統計 (log-加法)")
    print(f"  n = {len(results)}")
    print(f"  平均 = {thetas_v2.mean():.4f}")
    print(f"  中央値 = {np.median(thetas_v2):.4f}")
    print(f"  SD = {thetas_v2.std():.4f}")
    print(f"  範囲 = [{thetas_v2.min():.4f}, {thetas_v2.max():.4f}]")
    print(f"  Q1 = {np.percentile(thetas_v2, 25):.4f}")
    print(f"  Q3 = {np.percentile(thetas_v2, 75):.4f}")

    print("\n### Θ(B) v1 統計 (乗法, 比較用)")
    print(f"  平均 = {thetas_v1.mean():.4f}")
    print(f"  SD = {thetas_v1.std():.4f}")
    print(f"  範囲 = [{thetas_v1.min():.4f}, {thetas_v1.max():.4f}]")

    print("\n### 成分統計")
    for name, vals in [("S_active", s_acts), ("H(s)", hs_vals),
                       ("H(a)", ha_vals), ("R(s,a)", rsa_vals), ("modifier", mods)]:
        arr = np.array(vals)
        print(f"  {name:10}: mean={arr.mean():.4f}, sd={arr.std():.4f}, "
              f"range=[{arr.min():.4f}, {arr.max():.4f}]")

    # === 相関分析 ===
    print("\n### 成分→Θ(B)_v2 相関")
    log_s = np.log1p(s_acts)
    for name, vals in [("log(1+S)", log_s), ("modifier", mods),
                       ("H(s)", hs_vals), ("H(a)", ha_vals), ("R(s,a)", rsa_vals)]:
        r, p = stats.pearsonr(vals, thetas_v2)
        print(f"  r({name:10}, Θ_v2) = {r:.4f}, p = {p:.2e}")

    print("\n### v1 との比較")
    for name, vals in [("S_active", s_acts), ("modifier", mods)]:
        r_v1, _ = stats.pearsonr(vals, thetas_v1)
        r_v2, _ = stats.pearsonr(vals, thetas_v2)
        print(f"  {name:10}: r(v1)={r_v1:.4f}, r(v2)={r_v2:.4f}")

    # === 分散分解 (加法なので単純) ===
    print("\n### 分散分解 (加法)")
    var_total = np.var(thetas_v2)
    var_log_s = np.var(log_s)
    var_mod = np.var(mods)
    cov2 = 2 * np.cov(log_s, mods)[0, 1]
    print(f"  Var[Θ_v2]      = {var_total:.6f}")
    print(f"  Var[log(1+S)]  = {var_log_s:.6f} ({var_log_s/var_total*100:.1f}%)")
    print(f"  Var[modifier]  = {var_mod:.6f} ({var_mod/var_total*100:.1f}%)")
    print(f"  2·Cov          = {cov2:.6f} ({cov2/var_total*100:.1f}%)")

    # === 上位/下位セッション ===
    sorted_by_theta = sorted(results, key=lambda r: r.theta_v2, reverse=True)
    print("\n### 上位10セッション (Θ_v2 降順)")
    print(f"{'Θ_v2':>7} {'S_act':>6} {'H(s)':>6} {'H(a)':>6} {'R':>6} {'n':>5} {'日付':>12} タイトル")
    print("-" * 90)
    for r in sorted_by_theta[:10]:
        print(f"{r.theta_v2:7.4f} {r.S_active:6.3f} {r.H_s:6.3f} {r.H_a:6.3f} "
              f"{r.R_sa:6.3f} {r.n_events:5} {r.date:>12} {r.title[:35]}")

    print("\n### 下位10セッション (Θ_v2 昇順)")
    for r in sorted_by_theta[-10:]:
        print(f"{r.theta_v2:7.4f} {r.S_active:6.3f} {r.H_s:6.3f} {r.H_a:6.3f} "
              f"{r.R_sa:6.3f} {r.n_events:5} {r.date:>12} {r.title[:35]}")

    # === JSON 出力 ===
    output = {
        "version": "hgk_v2",
        "description": "Θ(B) v2 — log-加法形式 + S_active",
        "formula": "Θ(B) = log(1 + S_active) + α·H(s) + β·H(a) + γ·R(s,a)",
        "params": {"alpha": alpha, "beta": beta, "gamma": gamma},
        "changes_from_v1": [
            "S(B) → S_active (Active比率): 偽陽性のない客観的指標",
            "乗法 S×mod → log-加法 log(1+S)+mod: 両成分がバランスよく寄与",
        ],
        "stats": {
            "n": len(results),
            "theta_v2_mean": round(float(thetas_v2.mean()), 4),
            "theta_v2_median": round(float(np.median(thetas_v2)), 4),
            "theta_v2_sd": round(float(thetas_v2.std()), 4),
            "theta_v2_min": round(float(thetas_v2.min()), 4),
            "theta_v2_max": round(float(thetas_v2.max()), 4),
            "s_active_mean": round(float(s_acts.mean()), 4),
            "hs_mean": round(float(hs_vals.mean()), 4),
            "ha_mean": round(float(ha_vals.mean()), 4),
            "rsa_mean": round(float(rsa_vals.mean()), 4),
            "variance_decomp": {
                "pct_log_s": round(float(var_log_s / var_total * 100), 1),
                "pct_modifier": round(float(var_mod / var_total * 100), 1),
                "pct_cov": round(float(cov2 / var_total * 100), 1),
            },
            "correlations": {
                "r_log_s_theta": round(float(stats.pearsonr(log_s, thetas_v2)[0]), 4),
                "r_mod_theta": round(float(stats.pearsonr(mods, thetas_v2)[0]), 4),
            },
        },
        "sessions": [
            {
                "filename": r.filename,
                "date": r.date,
                "title": r.title,
                "theta_v2": round(r.theta_v2, 4),
                "theta_v1": round(r.theta_v1, 4),
                "S_active": round(r.S_active, 4),
                "H_s": round(r.H_s, 4),
                "H_a": round(r.H_a, 4),
                "R_sa": round(r.R_sa, 4),
                "n_events": r.n_events,
                "n_I": r.n_I,
                "n_A": r.n_A,
            }
            for r in sorted_by_theta
        ],
    }

    outpath = os.path.join(os.path.dirname(__file__) or ".", "theta_b_hgk_results_v2.json")
    with open(outpath, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 結果を {outpath} に保存 (n={len(results)} セッション)")


if __name__ == "__main__":
    main()
