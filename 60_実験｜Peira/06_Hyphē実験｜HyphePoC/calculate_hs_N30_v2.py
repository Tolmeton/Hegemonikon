#!/usr/bin/env python3
"""H(s) メトリクス計算 v2 — テキストベース heuristic。

エクスポートされた Markdown にはツール呼び出しの構造化データがないため、
MCP サーバーの **操作パターン** をテキスト中から検出し、H(s) を近似する。

検出パターン:
  - hermeneus: hermeneus_run, hermeneus_dispatch, hermeneus_execute, hermeneus_compile
  - sympatheia: sympatheia_status, sympatheia_notifications, sympatheia_verify, sympatheia_wbc, etc.
  - periskope: periskope_research, periskope_search, periskope_benchmark
  - sekisho: sekisho_audit, sekisho_gate
  - mneme: mneme_search, mneme_dendron, mneme_sources
  - ochema: ochema_ask, ochema_ask_cortex, ochema_start_chat
  - digestor: digestor_paper_search, digestor_paper_details
  - jules: jules_create_task, jules_batch_execute
  - typos: typos_compile, typos_validate
  - phantazein: phantazein_boot, phantazein_health, phantazein_sessions
"""

import os
import re
import math
import random
import statistics
from pathlib import Path
from collections import defaultdict

HGK = os.path.expanduser("~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon")

# MCP ツール操作パターン (正規表現)
# 形式: server_tool_name として出現するもの
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


def count_mcp_in_text(text: str) -> dict[str, int]:
    """テキスト中の MCP サーバー操作パターン出現数をカウント。"""
    counts = defaultdict(int)
    for server, pattern in MCP_PATTERNS.items():
        matches = pattern.findall(text)
        counts[server] += len(matches)
    return dict(counts)


def compute_hs(server_counts: dict) -> float:
    """H(s) = Shannon entropy を計算。"""
    total = sum(server_counts.values())
    if total == 0:
        return 0.0
    hs = 0.0
    for count in server_counts.values():
        p = count / total
        if p > 0:
            hs -= p * math.log2(p)
    return hs


def classify_session(total_calls: int, n_servers: int) -> str:
    """3条件分類。"""
    if total_calls == 0:
        return "VANILLA"
    elif n_servers <= 3 and total_calls <= 10:
        return "PARTIAL"
    else:
        return "HGK+"


def load_sessions(n_target: int) -> list[dict]:
    """セッションログを読み込み、MCP 使用を分析。"""
    sessions_dir = Path(HGK) / "30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions"
    all_files = sorted(list(sessions_dir.rglob("*.md")))

    # README, _misc 内の重複を除外
    all_files = [f for f in all_files if
                 f.name != "README.md" and
                 "/_misc/" not in str(f) and
                 "/_old_sessions/" not in str(f)]

    random.seed(42)
    random.shuffle(all_files)

    results = []
    for path in all_files:
        try:
            text = path.read_text(encoding="utf-8")
            # 最低 8 ステップのセッションのみ
            steps = _STEP_PATTERN.split(text)
            if len(steps) < 9:  # 8 steps + 初期テキスト
                continue

            n_steps = len(steps) - 1
            mcp_counts = count_mcp_in_text(text)
            total_calls = sum(mcp_counts.values())
            n_servers = len([s for s, c in mcp_counts.items() if c > 0])
            hs = compute_hs(mcp_counts)
            category = classify_session(total_calls, n_servers)

            results.append({
                "file": path.name,
                "steps": n_steps,
                "mcp_counts": mcp_counts,
                "total_calls": total_calls,
                "n_servers": n_servers,
                "hs": hs,
                "category": category,
            })

            if len(results) >= n_target:
                break
        except Exception:
            pass

    return results


def main():
    N_TARGET = 30
    sessions = load_sessions(N_TARGET)

    print(f"=== H(s) Measurement Results (N={len(sessions)}) ===\n")

    # カテゴリ別集計
    cats = {"VANILLA": [], "PARTIAL": [], "HGK+": []}
    for s in sessions:
        cats[s["category"]].append(s)

    # テーブル出力
    print("### §5.2 H(s) Measurement: MCP Server Entropy\n")
    print("| Condition | n | H(s) mean | H(s) std | Calls mean | Servers mean |")
    print("|:----------|---:|----------:|---------:|-----------:|-------------:|")

    for cat_name in ["VANILLA", "PARTIAL", "HGK+"]:
        items = cats[cat_name]
        n = len(items)
        if n == 0:
            print(f"| {cat_name} | 0 | - | - | - | - |")
            continue

        hs_vals = [s["hs"] for s in items]
        call_vals = [s["total_calls"] for s in items]
        srv_vals = [s["n_servers"] for s in items]

        mean_hs = statistics.mean(hs_vals)
        std_hs = statistics.pstdev(hs_vals)
        mean_calls = statistics.mean(call_vals)
        mean_srvs = statistics.mean(srv_vals)

        print(f"| {cat_name} | {n} | {mean_hs:.3f} | {std_hs:.3f} | {mean_calls:.1f} | {mean_srvs:.1f} |")

    # 全セッション詳細
    print("\n### 全セッション詳細\n")
    print("| # | File | Steps | Category | Calls | Servers | H(s) | Top servers |")
    print("|--:|:-----|------:|:---------|------:|--------:|-----:|:------------|")
    for i, s in enumerate(sessions, 1):
        top = sorted(s["mcp_counts"].items(), key=lambda x: -x[1])[:3]
        top_str = ", ".join(f"{k}:{v}" for k, v in top if v > 0) or "-"
        print(f"| {i} | {s['file'][:45]} | {s['steps']} | {s['category']} | "
              f"{s['total_calls']} | {s['n_servers']} | {s['hs']:.3f} | {top_str} |")

    # 統計検定用のサマリー
    print("\n### 統計サマリー")
    all_hs = [s["hs"] for s in sessions]
    print(f"全体 H(s): mean={statistics.mean(all_hs):.3f}, "
          f"std={statistics.pstdev(all_hs):.3f}, "
          f"min={min(all_hs):.3f}, max={max(all_hs):.3f}")
    print(f"分類: VANILLA={len(cats['VANILLA'])}, "
          f"PARTIAL={len(cats['PARTIAL'])}, "
          f"HGK+={len(cats['HGK+'])}")


if __name__ == "__main__":
    main()
