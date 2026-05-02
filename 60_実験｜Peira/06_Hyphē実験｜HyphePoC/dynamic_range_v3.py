#!/usr/bin/env python3
"""§5.7 Dynamic Range 分析 v3 — 偏相関 + H_norm + p値 + Bootstrap CI。

calculate_hs_N30_v2.py をベースに、per-window H(s) 変動分析を追加。
/ele+ 批判的検証 (2026-03-15) で特定した5矛盾に対応:
  #1 トートロジー → H_norm (正規化エントロピー)
  #2 n=1 → テーブル脚注 (論文側)
  #3 テキスト検出 limitation → 論文 Methodological note
  #4 confound → 偏相関 + range/nwin + truncated
  #5 BiCat prediction → 論文 P1/P2

出力: §5.7 用テーブル + 相関分析 + p値 + 95% Bootstrap CI + confound 分析
"""

import os
import re
import math
import random
import statistics
from pathlib import Path
from collections import defaultdict

HGK = os.path.expanduser("~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")

# === MCP ツール検出パターン ===
MCP_PATTERNS = {
    "hermeneus": re.compile(
        r'\bhermeneus_(run|dispatch|execute|compile|list_workflows)\b'
    ),
    "sympatheia": re.compile(
        r'\bsympatheia_(status|notifications|verify_on_edit|wbc|attractor|'
        r'basanos_scan|peira_health|feedback|escalate|digest|log_violation|'
        r'violation_dashboard|ping)\b'
    ),
    "periskope": re.compile(
        r'\bperiskope_(research|search|benchmark|sources|track|metrics)\b'
    ),
    "sekisho": re.compile(
        r'\bsekisho_(audit|gate|history|ping)\b'
    ),
    "mneme": re.compile(
        r'\bmneme_(search|search_papers|dendron_check|dendron_mece_check|'
        r'backlinks|graph_stats|sources|stats|recommend_model)\b'
    ),
    "ochema": re.compile(
        r'\bochema_(ask|ask_cortex|ask_chat|ask_with_tools|start_chat|'
        r'send_chat|close_chat|models|status|ping|session_info|'
        r'shadow_status|context_rot|cortex_quota|cache_boot_context)\b'
    ),
    "digestor": re.compile(
        r'\bdigestor_(paper_search|paper_details|paper_citations|'
        r'list_candidates|run_digestor|check_incoming|get_topics|'
        r'mark_processed|ping)\b'
    ),
    "jules": re.compile(
        r'\bjules_(create_task|batch_execute|get_status|list_repos)\b'
    ),
    "typos": re.compile(
        r'\btypos_(compile|validate|parse|expand|generate|policy_check|ping)\b'
    ),
    "phantazein": re.compile(
        r'\bphantazein_(boot|health|sessions|status|ping|sync|report|'
        r'quota|snapshot|classify|consistency|orphans|cache_status)\b'
    ),
}

# ステップ分割パターン
_STEP_PATTERN = re.compile(r"^## 🤖 (?:Claude|Assistant|Gemini)", re.MULTILINE)

WINDOW_SIZE = 5  # ウィンドウあたりのステップ数


# === 統計ユーティリティ (stdlib のみ) ===

def _rank(values: list[float]) -> list[float]:
    """タイ対応の平均ランクを返す。"""
    n = len(values)
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j < n and indexed[j][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j + 1) / 2.0  # 1-indexed 平均
        for k in range(i, j):
            ranks[indexed[k][0]] = avg_rank
        i = j
    return ranks


def spearman_r(x: list[float], y: list[float]) -> float:
    """Spearman 順位相関係数。"""
    n = len(x)
    if n < 3:
        return float('nan')
    rx = _rank(x)
    ry = _rank(y)
    mx = sum(rx) / n
    my = sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    sy = math.sqrt(sum((b - my) ** 2 for b in ry))
    if sx == 0 or sy == 0:
        return float('nan')
    return cov / (sx * sy)


def spearman_p(r: float, n: int) -> float:
    """Spearman 相関の近似 p 値 (t 分布近似 + Abramowitz-Stegun)。"""
    if math.isnan(r) or n < 4:
        return float('nan')
    t = r * math.sqrt((n - 2) / (1 - r * r + 1e-15))
    df = n - 2
    # Abramowitz & Stegun 26.2.17 近似 (t→p 変換, 2-tailed)
    x = df / (df + t * t)
    # 正則化不完全ベータ関数の近似 (df/2, 0.5)
    # 大自由度・大tでは正規近似で十分
    z = abs(t) * math.sqrt(1 - 1 / (4 * df) - 7 / (120 * df * df))
    # Φ(z) の Abramowitz-Stegun 近似 26.2.17
    p_one = 0.5 * math.erfc(z / math.sqrt(2))
    return 2 * p_one  # 両側検定


def partial_spearman(x: list[float], y: list[float],
                     z: list[float]) -> tuple[float, float]:
    """z を制御した Spearman 偏相関。返り値: (r_partial, p_approx)。"""
    rxy = spearman_r(x, y)
    rxz = spearman_r(x, z)
    ryz = spearman_r(y, z)
    denom = math.sqrt((1 - rxz ** 2) * (1 - ryz ** 2) + 1e-15)
    r_partial = (rxy - rxz * ryz) / denom
    # 自由度調整 p 値
    n = len(x)
    p = spearman_p(r_partial, n - 1)  # 1変数制御なので df-1
    return r_partial, p


def bootstrap_ci_spearman(x: list[float], y: list[float],
                          n_boot: int = 2000, alpha: float = 0.05,
                          seed: int = 42) -> tuple[float, float]:
    """Bootstrap percentile 信頼区間 (95% デフォルト)。
    返り値: (lower, upper)。"""
    rng = random.Random(seed)
    n = len(x)
    rs = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        xb = [x[i] for i in idx]
        yb = [y[i] for i in idx]
        r = spearman_r(xb, yb)
        if not math.isnan(r):
            rs.append(r)
    rs.sort()
    lo_idx = int(len(rs) * (alpha / 2))
    hi_idx = int(len(rs) * (1 - alpha / 2)) - 1
    return rs[lo_idx], rs[hi_idx]


def bootstrap_ci_partial(x: list[float], y: list[float], z: list[float],
                         n_boot: int = 2000, alpha: float = 0.05,
                         seed: int = 42) -> tuple[float, float]:
    """偏相関の Bootstrap percentile 信頼区間。"""
    rng = random.Random(seed)
    n = len(x)
    rs = []
    for _ in range(n_boot):
        idx = [rng.randrange(n) for _ in range(n)]
        xb = [x[i] for i in idx]
        yb = [y[i] for i in idx]
        zb = [z[i] for i in idx]
        rp, _ = partial_spearman(xb, yb, zb)
        if not math.isnan(rp):
            rs.append(rp)
    rs.sort()
    lo_idx = int(len(rs) * (alpha / 2))
    hi_idx = int(len(rs) * (1 - alpha / 2)) - 1
    return rs[lo_idx], rs[hi_idx]


# === H(s) 計算 ===

def count_mcp_in_text(text: str) -> dict[str, int]:
    """テキスト中の MCP サーバー操作パターン出現数をカウント。"""
    counts: dict[str, int] = {}
    for server, pattern in MCP_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            counts[server] = len(matches)
    return counts


def compute_hs(server_counts: dict) -> float:
    """H(s) = Shannon entropy (bits)。"""
    total = sum(server_counts.values())
    if total == 0:
        return 0.0
    hs = 0.0
    for count in server_counts.values():
        p = count / total
        if p > 0:
            hs -= p * math.log2(p)
    return hs


def compute_hs_norm(server_counts: dict) -> float:
    """正規化エントロピー H_norm = H(s) / log2(n_servers)。
    n_servers=1 のときは H(s)=0 なので 0 を返す。"""
    n = len([c for c in server_counts.values() if c > 0])
    if n <= 1:
        return 0.0
    return compute_hs(server_counts) / math.log2(n)


# === セッション読込・ウィンドウ分割 ===

def load_all_sessions() -> list[dict]:
    """全セッションを読み込み、ウィンドウ分割して MCP 使用を分析。"""
    sessions_dir = Path(HGK) / "30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions"
    all_files = sorted(sessions_dir.rglob("*.md"))
    all_files = [f for f in all_files if
                 f.name != "README.md" and
                 "/_misc/" not in str(f) and
                 "/_old_sessions/" not in str(f)]

    print(f"ファイル数: {len(all_files)}")

    results = []
    skipped = 0
    for path in all_files:
        try:
            text = path.read_text(encoding="utf-8")
            steps = _STEP_PATTERN.split(text)
            if len(steps) < 9:
                skipped += 1
                continue

            n_steps = len(steps) - 1  # 最初の要素は先頭テキスト

            # 全体の MCP カウント
            mcp_counts = count_mcp_in_text(text)
            total_calls = sum(mcp_counts.values())
            n_servers = len([c for c in mcp_counts.values() if c > 0])
            hs_total = compute_hs(mcp_counts)
            hs_norm = compute_hs_norm(mcp_counts)

            # ウィンドウ分割: 各ウィンドウの H(s) を計算
            windows = []
            step_texts = steps[1:]  # 先頭テキストを除く
            for w_start in range(0, len(step_texts), WINDOW_SIZE):
                w_end = min(w_start + WINDOW_SIZE, len(step_texts))
                window_text = "\n".join(step_texts[w_start:w_end])
                w_counts = count_mcp_in_text(window_text)
                w_hs = compute_hs(w_counts)
                windows.append(w_hs)

            n_windows = len(windows)
            dr_range = max(windows) - min(windows) if n_windows > 1 else 0.0
            dr_per_nwin = dr_range / n_windows if n_windows > 0 else 0.0

            # truncated DR: 最初の2ウィンドウのみ
            if len(windows) >= 2:
                dr_trunc = max(windows[:2]) - min(windows[:2])
            else:
                dr_trunc = 0.0

            results.append({
                "file": path.name,
                "steps": n_steps,
                "n_windows": n_windows,
                "n_servers": n_servers,
                "total_calls": total_calls,
                "hs": hs_total,
                "hs_norm": hs_norm,
                "dr_range": dr_range,
                "dr_per_nwin": dr_per_nwin,
                "dr_trunc": dr_trunc,
                "windows": windows,
            })
        except Exception:
            skipped += 1

    print(f"分析対象: {len(results)} セッション (スキップ: {skipped})")
    return results


# === 出力 ===

def main():
    sessions = load_all_sessions()
    mcp_sessions = [s for s in sessions if s["n_servers"] > 0]
    n_mcp = len(mcp_sessions)

    # Θ グループ分類
    groups = {"0 (vanilla)": [], "1-3 (partial)": [], "4+ (augment)": []}
    for s in sessions:
        ns = s["n_servers"]
        if ns == 0:
            groups["0 (vanilla)"].append(s)
        elif 1 <= ns <= 3:
            groups["1-3 (partial)"].append(s)
        else:
            groups["4+ (augment)"].append(s)

    print(f"\n{'='*80}")
    print(f"§5.7 Dynamic Range 修正版 — N={len(sessions)} (MCP使用: {n_mcp})")
    print(f"{'='*80}\n")

    # --- テーブル 1: グループ比較 ---
    print("### Θ(B) グループ比較\n")
    print("| Θ group      | n   | DR range | DR/nwin | DR trunc | H(s) mean | H_norm |")
    print("|:-------------|----:|---------:|--------:|---------:|----------:|-------:|")
    for gname in ["0 (vanilla)", "1-3 (partial)", "4+ (augment)"]:
        items = groups[gname]
        n = len(items)
        if n == 0:
            print(f"| {gname:12s} | {n:3d} |        - |       - |        - |         - |      - |")
            continue
        dr_m = statistics.mean([s["dr_range"] for s in items])
        drn_m = statistics.mean([s["dr_per_nwin"] for s in items])
        drt_m = statistics.mean([s["dr_trunc"] for s in items])
        hs_m = statistics.mean([s["hs"] for s in items])
        hn_m = statistics.mean([s["hs_norm"] for s in items])
        print(f"| {gname:12s} | {n:3d} |    {dr_m:.3f} |  {drn_m:.4f} |    {drt_m:.3f} |     {hs_m:.3f} |  {hn_m:.3f} |")

    # --- テーブル 2: 相関分析 ---
    if n_mcp >= 4:
        theta = [float(s["n_servers"]) for s in mcp_sessions]
        dr = [s["dr_range"] for s in mcp_sessions]
        dr_nwin = [s["dr_per_nwin"] for s in mcp_sessions]
        dr_trunc = [s["dr_trunc"] for s in mcp_sessions]
        hs_vals = [s["hs"] for s in mcp_sessions]
        hs_norm_vals = [s["hs_norm"] for s in mcp_sessions]
        steps = [float(s["steps"]) for s in mcp_sessions]
        nwin = [float(s["n_windows"]) for s in mcp_sessions]

        # 相関計算
        r_theta_dr = spearman_r(theta, dr)
        p_theta_dr = spearman_p(r_theta_dr, n_mcp)

        r_partial_steps, p_partial = partial_spearman(theta, dr, steps)

        r_theta_dr_nwin_partial, p_nwin_partial = partial_spearman(theta, dr_nwin, steps)

        r_theta_trunc = spearman_r(theta, dr_trunc)
        p_theta_trunc = spearman_p(r_theta_trunc, n_mcp)

        r_theta_hs = spearman_r(theta, hs_vals)
        p_theta_hs = spearman_p(r_theta_hs, n_mcp)

        r_theta_hn = spearman_r(theta, hs_norm_vals)
        p_theta_hn = spearman_p(r_theta_hn, n_mcp)

        r_steps_dr = spearman_r(steps, dr)
        p_steps_dr = spearman_p(r_steps_dr, n_mcp)

        r_nwin_dr = spearman_r(nwin, dr)
        p_nwin_dr = spearman_p(r_nwin_dr, n_mcp)

        # Bootstrap 95% CI (B=2000, seed=42 で再現可能)
        print("\n  Bootstrap CI 計算中 (B=2000)...", flush=True)
        ci_raw = bootstrap_ci_spearman(theta, dr)
        ci_partial = bootstrap_ci_partial(theta, dr, steps)
        ci_nwin = bootstrap_ci_partial(theta, dr_nwin, steps)
        ci_trunc = bootstrap_ci_spearman(theta, dr_trunc)
        ci_hs = bootstrap_ci_spearman(theta, hs_vals)
        ci_hn = bootstrap_ci_spearman(theta, hs_norm_vals)
        ci_steps = bootstrap_ci_spearman(steps, dr)

        print(f"\n### 相関分析 (MCP使用セッション, n={n_mcp})\n")
        print("| Hypothesis                      | r_s    | 95% CI          | p           | note           |")
        print("|:--------------------------------|-------:|:----------------|:------------|:---------------|")
        print(f"| Θ ↔ DR (range)       [raw]      | {r_theta_dr:+.3f} | [{ci_raw[0]:+.3f}, {ci_raw[1]:+.3f}] | {p_theta_dr:.2e} |                |")
        print(f"| Θ ↔ DR (range)       [| steps]  | {r_partial_steps:+.3f} | [{ci_partial[0]:+.3f}, {ci_partial[1]:+.3f}] | {p_partial:.2e} | 偏相関         |")
        print(f"| Θ ↔ DR/nwin         [| steps]   | {r_theta_dr_nwin_partial:+.3f} | [{ci_nwin[0]:+.3f}, {ci_nwin[1]:+.3f}] | {p_nwin_partial:.2e} | 正規化+偏相関   |")
        print(f"| Θ ↔ DR (trunc, 2win only)       | {r_theta_trunc:+.3f} | [{ci_trunc[0]:+.3f}, {ci_trunc[1]:+.3f}] | {p_theta_trunc:.2e} | ウィンドウ固定  |")
        print(f"| Θ ↔ H(s)                        | {r_theta_hs:+.3f} | [{ci_hs[0]:+.3f}, {ci_hs[1]:+.3f}] | {p_theta_hs:.2e} |                |")
        print(f"| Θ ↔ H_norm                      | {r_theta_hn:+.3f} | [{ci_hn[0]:+.3f}, {ci_hn[1]:+.3f}] | {p_theta_hn:.2e} | 正規化ent      |")
        print(f"| steps ↔ DR (confound)           | {r_steps_dr:+.3f} | [{ci_steps[0]:+.3f}, {ci_steps[1]:+.3f}] | {p_steps_dr:.2e} |                |")
        print(f"| n_windows ↔ DR (confound)       | {r_nwin_dr:+.3f} |                 | {p_nwin_dr:.2e} |                |")

        # --- 分析サマリー ---
        drop_pct = abs(r_theta_dr - r_partial_steps) / abs(r_theta_dr) * 100
        print(f"\n### トートロジー検証 (#1)")
        print(f"  Θ ↔ H(s):     r_s = {r_theta_hs:+.3f}  (Θ が H(s) 上界を決定 → ほぼ自明)")
        print(f"  Θ ↔ H_norm:   r_s = {r_theta_hn:+.3f}  (正規化で Θ の上界効果を除去)")

        print(f"\n### Confound 分析 (#4)")
        print(f"  raw r(Θ, DR):            {r_theta_dr:+.3f}")
        print(f"  partial r(Θ, DR | steps): {r_partial_steps:+.3f} (p={p_partial:.2e})")
        print(f"  効果量低下: {drop_pct:.1f}%")
        if abs(r_partial_steps) >= 0.5:
            print(f"  判定: ✅ Θ→DR の直接効果は偏相関後も moderate 以上 ({r_partial_steps:+.3f})")
        else:
            print(f"  判定: ⚠️ 偏相関後の効果量が moderate 未満 ({r_partial_steps:+.3f})")

        print(f"\n### Truncated 分析 (最初の2ウィンドウのみ)")
        print(f"  Θ ↔ DR_trunc: r_s = {r_theta_trunc:+.3f} (p={p_theta_trunc:.2e})")
        if abs(r_theta_trunc) >= 0.5:
            print(f"  判定: ✅ ウィンドウ数を固定しても Θ→DR 効果が残る")
        else:
            print(f"  判定: ⚠️ truncated 分析で効果量が低下")

    # --- Θ≥4 セッション詳細 ---
    augmented = groups["4+ (augment)"]
    if augmented:
        print(f"\n### Θ≥4 セッション詳細")
        for s in augmented:
            print(f"  {s['file'][:60]}   srv={s['n_servers']} H(s)={s['hs']:.3f} "
                  f"H_n={s['hs_norm']:.3f} DR={s['dr_range']:.3f} "
                  f"DR/w={s['dr_per_nwin']:.4f} trunc={s['dr_trunc']:.3f}")

    # --- 数値サマリー (論文更新用) ---
    print(f"\n{'='*80}")
    print("§5.7 修正用 数値サマリー")
    print(f"{'='*80}")
    print(f"  N_total = {len(sessions)}")
    print(f"  N_mcp   = {n_mcp}")
    if n_mcp >= 4:
        print(f"  r(Θ, DR)           = {r_theta_dr:+.3f} (p={p_theta_dr:.2e}) CI=[{ci_raw[0]:+.3f}, {ci_raw[1]:+.3f}]")
        print(f"  r(Θ, DR | steps)   = {r_partial_steps:+.3f} (p={p_partial:.2e}) CI=[{ci_partial[0]:+.3f}, {ci_partial[1]:+.3f}]")
        print(f"  r(Θ, H_norm)       = {r_theta_hn:+.3f} (p={p_theta_hn:.2e}) CI=[{ci_hn[0]:+.3f}, {ci_hn[1]:+.3f}]")
        print(f"  r(Θ, DR_trunc)     = {r_theta_trunc:+.3f} (p={p_theta_trunc:.2e}) CI=[{ci_trunc[0]:+.3f}, {ci_trunc[1]:+.3f}]")
        print(f"  confound drop      = {drop_pct:.1f}%")


if __name__ == "__main__":
    main()
