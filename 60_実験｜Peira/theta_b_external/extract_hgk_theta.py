#!/usr/bin/env python3
"""
HGK+ Θ(B) 自動計算 — セッションログからの MCP ツール使用抽出

PURPOSE: conv/ の対話ログから MCP/IDE ツール使用パターンを抽出し、
         セッション単位で Θ(B) コンポーネントを計算する。
         目標: n ≥ 300 (473 セッション中、ツール使用が十分なもの)

操作的定義:
- H(s): 利用可能ツールの分布エントロピー (MCP 構成固定 → ほぼ定数)
- H(a): セッション内で使用されたツールの頻度分布エントロピー
- R(s,a): (サーバ, ツール) 結合分布の相互情報量
- S(B): MCP ツール呼び出し成功率 (固定値 0.92 + セッション毎推定)

Θ(B) := S(B) · (1 + α·H(s) + β·H(a) + γ·R(s,a))
"""

import os
import sys
import re
import math
import json
import glob
from dataclasses import dataclass, field
from collections import Counter
from pathlib import Path

# === 定数 ===

# MCP サーバ → ツール名のマッピング (HGK+ 9 サーバ構成)
# ツール使用パターンの正規表現
MCP_TOOL_PATTERNS = {
    # MCP サーバツール (server: tool_name パターン)
    "hermeneus": [
        "hermeneus_run", "hermeneus_execute", "hermeneus_dispatch",
        "hermeneus_compile", "hermeneus_analyze",
        "hermeneus_admin",
    ],
    "periskope": [
        "periskope_research", "periskope_search", "periskope_admin",
        "periskope_track",
    ],
    "mneme": [
        "mneme_search", "mneme_check", "mneme_graph",
        "mneme_convert", "mneme_recommend_model",
    ],
    "ochema": [
        "ochema_ask", "ochema_chat", "ochema_context",
        "ochema_info", "ochema_plan_task",
    ],
    "sekisho": [
        "sekisho_audit", "sekisho_gate", "sekisho_history",
        "sekisho_ping",
    ],
    "sympatheia": [
        "sympatheia_attractor", "sympatheia_basanos_scan",
        "sympatheia_digest", "sympatheia_escalate",
        "sympatheia_feedback", "sympatheia_log_violation",
        "sympatheia_notifications", "sympatheia_peira_health",
        "sympatheia_ping", "sympatheia_status",
        "sympatheia_verify_on_edit", "sympatheia_violation_dashboard",
        "sympatheia_wbc",
    ],
    "digestor": [
        "digestor_paper", "digestor_pipeline",
    ],
    "phantazein": [
        "phantazein_boot", "phantazein_check",
        "phantazein_info", "phantazein_session",
    ],
    "typos": [
        "typos_compile", "typos_expand", "typos_generate",
        "typos_parse", "typos_ping", "typos_policy_check",
        "typos_validate",
    ],
    "hub": [
        "hub_execute", "hub_gate", "hub_recommend",
        "hub_shadow_status", "hub_stats",
    ],
    "jules": [
        "jules_batch_execute", "jules_create_task",
        "jules_get_status", "jules_list_repos",
    ],
    # IDE 標準ツール (server=ide)
    "ide": [
        "view_file", "write_to_file", "replace_file_content",
        "multi_replace_file_content",
        "run_command", "grep_search", "find_by_name", "list_dir",
        "read_url_content", "search_web", "generate_image",
        "browser_subagent", "notify_user", "send_command_input",
        "command_status",
    ],
}

# 逆マッピング: ツール名 → サーバ名
TOOL_TO_SERVER = {}
for server, tools in MCP_TOOL_PATTERNS.items():
    for tool in tools:
        TOOL_TO_SERVER[tool] = server

# 全ツール名のリスト (正規表現用)
ALL_TOOL_NAMES = sorted(TOOL_TO_SERVER.keys(), key=len, reverse=True)

# 偽陽性を除外するパターン
# (ツール名が言及されるが実際の呼び出しではないパターン)
FALSE_POSITIVE_SUFFIXES = [
    "_tools", "_server", "_mcp_server", "_description",
    "_schema", "_params", "_result", "_config",
]

# パラメータ (論文 §4.1)
ALPHA = 0.4
BETA = 0.4
GAMMA = 0.2

# S(B) 固定値 (手動計測2セッションの平均)
S_B_FIXED = 0.925  # (0.94 + 0.91) / 2

# === データ構造 ===

@dataclass
class SessionTheta:
    """1セッションの Θ(B) コンポーネント"""
    session_file: str
    session_date: str
    session_title: str
    
    # ツール使用統計
    tool_counts: dict  # {tool_name: count}
    server_counts: dict  # {server: count}
    total_tool_calls: int
    unique_tools: int
    unique_servers: int
    
    # Θ(B) コンポーネント
    H_s: float  # 感覚エントロピー (固定値)
    H_a: float  # 行動エントロピー
    R_sa: float  # 相互情報量
    S_B_fixed: float  # 固定 S(B)
    S_B_estimated: float  # 推定 S(B)
    
    # メタデータ
    error_count: int = 0  # エラー言及数
    file_size: int = 0  # ファイルサイズ
    line_count: int = 0  # 行数
    
    @property
    def theta_fixed(self) -> float:
        """Θ(B) with 固定 S(B)"""
        return self.S_B_fixed * (1 + ALPHA * self.H_s
                                  + BETA * self.H_a
                                  + GAMMA * self.R_sa)
    
    @property
    def theta_estimated(self) -> float:
        """Θ(B) with 推定 S(B)"""
        return self.S_B_estimated * (1 + ALPHA * self.H_s
                                      + BETA * self.H_a
                                      + GAMMA * self.R_sa)


# === エントロピー計算 ===

def shannon_entropy(counts: list[int]) -> float:
    """Shannon entropy H = -Σ p_i log2(p_i)"""
    total = sum(counts)
    if total == 0:
        return 0.0
    h = 0.0
    for c in counts:
        if c > 0:
            p = c / total
            h -= p * math.log2(p)
    return h


def normalized_entropy(counts: list[int]) -> float:
    """正規化エントロピー [0, 1]"""
    n = len([c for c in counts if c > 0])
    if n <= 1:
        return 0.0
    return shannon_entropy(counts) / math.log2(n)


def mutual_information(joint_counts: dict, marginal_x: dict, 
                       marginal_y: dict) -> float:
    """I(X;Y) = H(X) + H(Y) - H(X,Y)"""
    h_x = shannon_entropy(list(marginal_x.values()))
    h_y = shannon_entropy(list(marginal_y.values()))
    h_xy = shannon_entropy(list(joint_counts.values()))
    return max(0.0, h_x + h_y - h_xy)


# === セッションログ解析 ===

def extract_tool_calls(text: str) -> Counter:
    """テキストから MCP/IDE ツール呼び出しを抽出する。
    
    戦略: 全ツール名を1つの alternation パターンにまとめて
    1パスで検索 (高速化)。偽陽性は後処理で除外。
    """
    tool_counts = Counter()
    
    # 全ツール名を1つの alternation パターンに結合
    # 長い名前を先にマッチさせる (longest match)
    pattern = r'\b(' + '|'.join(re.escape(t) for t in ALL_TOOL_NAMES) + r')\b'
    
    for m in re.finditer(pattern, text):
        tool_name = m.group(1)
        # 偽陽性チェック: 直後に除外接尾辞が続くか
        end_pos = m.end()
        remaining = text[end_pos:end_pos + 20]
        is_false = False
        for suffix in FALSE_POSITIVE_SUFFIXES:
            if remaining.startswith(suffix):
                is_false = True
                break
        if not is_false:
            tool_counts[tool_name] += 1
    
    return tool_counts


def count_errors(text: str) -> int:
    """テキスト中のエラー言及数を推定する。
    
    S(B) 推定用: エラーパターンの出現回数。
    """
    error_patterns = [
        r'\bError\b', r'\bエラー',
        r'\bfailed\b', r'\b失敗',
        r'\bException\b',
        r'\btraceback\b',
        r'\bTimeoutError\b',
        r'\bConnectionError\b',
    ]
    count = 0
    for pat in error_patterns:
        count += len(re.findall(pat, text, re.IGNORECASE))
    return count


def compute_session_theta(filepath: str, 
                          min_tools: int = 3,
                          min_calls: int = 5) -> SessionTheta | None:
    """1セッションログファイルから Θ(B) を計算する。"""
    
    path = Path(filepath)
    filename = path.name
    
    # ファイル名からメタデータ抽出
    # パターン: 2026-MM-DD_conv_NN_Title.md or 2026-MM-DD_NNN_Title.md
    # or live_YYYY-MM-DD_Title.md or session_xxx_YYYY-MM-DD.md
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    session_date = date_match.group(1) if date_match else "unknown"
    
    # タイトル抽出
    title_match = re.match(r'\d{4}-\d{2}-\d{2}_(?:conv_)?\d+_(.+)\.md$', filename)
    if not title_match:
        title_match = re.match(r'live_\d{4}-\d{2}-\d{2}_(.+)\.md$', filename)
    session_title = title_match.group(1) if title_match else filename.replace('.md', '')
    
    # ファイル読み込み
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception:
        return None
    
    line_count = text.count('\n')
    file_size = len(text.encode('utf-8'))
    
    # ツール呼び出し抽出
    tool_counts = extract_tool_calls(text)
    
    # 閾値チェック
    if len(tool_counts) < min_tools:
        return None
    
    total_calls = sum(tool_counts.values())
    if total_calls < min_calls:
        return None
    
    # サーバ別カウント
    server_counts = Counter()
    joint_counts = Counter()  # (server, tool) ペア
    
    for tool, count in tool_counts.items():
        server = TOOL_TO_SERVER.get(tool, "unknown")
        server_counts[server] += count
        joint_counts[(server, tool)] += count
    
    # --- H(s): 感覚チャネルエントロピー ---
    # HGK+ の MCP 構成は固定 (9 MCPサーバ + IDE)
    # 全サーバは常に利用可能。均等分布に近い → H(s) ≈ 0.85-0.90
    # 正規化: log2(10 servers) = 3.32
    # 実測: Session 1 = 0.887, Session 2 = 0.836 → 平均 0.862
    # ただし、セッションごとに実際に「到達可能な」サーバ数が異なる
    # → 使用されたサーバ数に基づいて計算
    available_servers = len(MCP_TOOL_PATTERNS)  # 全11サーバ
    # 均等な利用可能性を仮定: 各サーバに同じ重み
    h_s_counts = [1] * available_servers  # 全サーバ利用可能
    h_s = normalized_entropy(h_s_counts)  # = 1.0 (均等)
    # より現実的: 実際に使用されたサーバの分布でエントロピー
    if len(server_counts) >= 2:
        h_s = normalized_entropy(list(server_counts.values()))
    else:
        h_s = 0.0
    
    # --- H(a): 行動チャネルエントロピー ---
    if len(tool_counts) >= 2:
        h_a = normalized_entropy(list(tool_counts.values()))
    else:
        h_a = 0.0
    
    # --- R(s,a): 相互情報量 ---
    if len(joint_counts) >= 2 and len(server_counts) >= 2:
        r_sa_raw = mutual_information(
            joint_counts, server_counts, dict(tool_counts)
        )
        # 正規化
        h_server = shannon_entropy(list(server_counts.values()))
        h_tool = shannon_entropy(list(tool_counts.values()))
        denom = min(h_server, h_tool)
        r_sa = r_sa_raw / denom if denom > 0 else 0.0
        r_sa = min(r_sa, 1.0)  # クリップ
    else:
        r_sa = 0.0
    
    # --- S(B): MB 強度 ---
    error_count = count_errors(text)
    # 推定: (total_calls - error_mentions) / total_calls
    # ただしエラー言及 ≠ ツール呼び出しエラー (過大推定の可能性)
    # → エラーの 1/3 がツール関連と仮定 (保守的)
    tool_related_errors = error_count // 3
    s_b_estimated = max(0.5, 
                        (total_calls - tool_related_errors) / total_calls
                        if total_calls > 0 else S_B_FIXED)
    
    return SessionTheta(
        session_file=filename,
        session_date=session_date,
        session_title=session_title,
        tool_counts=dict(tool_counts),
        server_counts=dict(server_counts),
        total_tool_calls=total_calls,
        unique_tools=len(tool_counts),
        unique_servers=len(server_counts),
        H_s=h_s,
        H_a=h_a,
        R_sa=r_sa,
        S_B_fixed=S_B_FIXED,
        S_B_estimated=s_b_estimated,
        error_count=error_count,
        file_size=file_size,
        line_count=line_count,
    )


# === メイン ===

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="HGK+ Θ(B) 自動計算 — セッションログ抽出"
    )
    base_dir = ("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/"
                "30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions")
    parser.add_argument(
        "--conv-dir",
        default=f"{base_dir}/conv",
        help="conv/ ディレクトリ"
    )
    parser.add_argument("--json", action="store_true",
                        help="JSON 出力")
    parser.add_argument("--min-tools", type=int, default=2,
                        help="最小ユニークツール数 (デフォルト: 2)")
    parser.add_argument("--min-calls", type=int, default=3,
                        help="最小ツール呼び出し数 (デフォルト: 3)")
    parser.add_argument("--all-dirs", action="store_true",
                        help="conv/ に加えて live/, sessions/, chat_export/ も含める")
    args = parser.parse_args()
    
    conv_dir = Path(args.conv_dir)
    if not conv_dir.is_dir():
        print(f"エラー: {conv_dir} が見つかりません")
        sys.exit(1)
    
    # 全セッションファイルを収集
    md_files = sorted(conv_dir.glob("*.md"))
    
    if args.all_dirs:
        # 追加ディレクトリもスキャン
        extra_dirs = ["live", "conv/sessions", "chat_export"]
        for subdir in extra_dirs:
            extra_path = Path(base_dir) / subdir
            if extra_path.is_dir():
                extra_md = sorted(extra_path.glob("*.md"))
                md_files.extend(extra_md)
    
    # 重複除去 (同じファイルパスは1回だけ)
    seen = set()
    unique_files = []
    for f in md_files:
        if str(f) not in seen:
            seen.add(str(f))
            unique_files.append(f)
    md_files = unique_files
    
    print(f"\n{'='*70}")
    print(f"HGK+ Θ(B) 自動計算 — セッションログ抽出")
    print(f"{'='*70}")
    print(f"対象: {len(md_files)} セッションファイル")
    if args.all_dirs:
        print(f"(conv/ + live/ + sessions/ + chat_export/)")
    
    results: list[SessionTheta] = []
    skipped = 0
    errors = 0
    
    for filepath in md_files:
        result = compute_session_theta(
            str(filepath),
            min_tools=args.min_tools,
            min_calls=args.min_calls,
        )
        if result is None:
            skipped += 1
            continue
        results.append(result)
    
    n = len(results)
    print(f"\n--- 結果サマリー ---")
    print(f"有効セッション: {n} / {len(md_files)} "
          f"(スキップ: {skipped}, エラー: {errors})")
    
    if n == 0:
        print("有効なセッションがありません")
        sys.exit(1)
    
    # --- 統計 ---
    thetas_fixed = [r.theta_fixed for r in results]
    thetas_estimated = [r.theta_estimated for r in results]
    h_a_values = [r.H_a for r in results]
    h_s_values = [r.H_s for r in results]
    r_sa_values = [r.R_sa for r in results]
    s_b_est_values = [r.S_B_estimated for r in results]
    
    import numpy as np
    
    print(f"\n--- Θ(B) 分布 (n={n}) ---")
    print(f"{'指標':<20} {'平均':>8} {'SD':>8} {'min':>8} {'max':>8} {'中央値':>8}")
    print("-" * 65)
    for name, vals in [
        ("Θ(B) 固定S(B)", thetas_fixed),
        ("Θ(B) 推定S(B)", thetas_estimated),
        ("H(s)", h_s_values),
        ("H(a)", h_a_values),
        ("R(s,a)", r_sa_values),
        ("S(B) 推定", s_b_est_values),
    ]:
        arr = np.array(vals)
        print(f"{name:<20} {arr.mean():>8.4f} {arr.std():>8.4f} "
              f"{arr.min():>8.4f} {arr.max():>8.4f} {np.median(arr):>8.4f}")
    
    # --- S(B) 固定 vs 推定の比較 ---
    print(f"\n--- S(B) 比較 ---")
    s_b_diff = np.array(s_b_est_values) - S_B_FIXED
    print(f"固定 S(B) = {S_B_FIXED}")
    print(f"推定 S(B) 平均 = {np.mean(s_b_est_values):.4f}")
    print(f"差の平均 = {np.mean(s_b_diff):.4f}")
    print(f"差の SD = {np.std(s_b_diff):.4f}")
    print(f"Θ(B) 差の平均 = {np.mean(np.array(thetas_estimated) - np.array(thetas_fixed)):.4f}")
    
    # --- 日付別分布 ---
    from collections import defaultdict
    date_counts = defaultdict(int)
    for r in results:
        month = r.session_date[:7]  # YYYY-MM
        date_counts[month] += 1
    
    print(f"\n--- 月別セッション数 ---")
    for month in sorted(date_counts.keys()):
        print(f"  {month}: {date_counts[month]:>4} セッション")
    
    # --- ツール使用頻度 ---
    all_tool_counts = Counter()
    all_server_counts = Counter()
    for r in results:
        for tool, count in r.tool_counts.items():
            all_tool_counts[tool] += count
        for server, count in r.server_counts.items():
            all_server_counts[server] += count
    
    print(f"\n--- ツール使用頻度 (全セッション集計) ---")
    for tool, count in all_tool_counts.most_common(20):
        server = TOOL_TO_SERVER.get(tool, "?")
        print(f"  {tool:<35} {count:>6} ({server})")
    
    print(f"\n--- サーバ別使用頻度 ---")
    for server, count in all_server_counts.most_common():
        print(f"  {server:<15} {count:>6}")
    
    # --- 上位/下位セッション ---
    results_sorted = sorted(results, key=lambda r: r.theta_fixed, reverse=True)
    print(f"\n--- Θ(B) 上位10 ---")
    for r in results_sorted[:10]:
        print(f"  {r.theta_fixed:.4f} | {r.session_date} | "
              f"{r.session_title[:40]} | tools={r.unique_tools}, "
              f"calls={r.total_tool_calls}")
    
    print(f"\n--- Θ(B) 下位10 ---")
    for r in results_sorted[-10:]:
        print(f"  {r.theta_fixed:.4f} | {r.session_date} | "
              f"{r.session_title[:40]} | tools={r.unique_tools}, "
              f"calls={r.total_tool_calls}")
    
    # --- JSON 出力 ---
    if args.json:
        output = {
            "version": "auto_extract_v1",
            "source": "HGK+ session logs",
            "n": n,
            "total_files": len(md_files),
            "parameters": {
                "alpha": ALPHA, "beta": BETA, "gamma": GAMMA,
                "S_B_fixed": S_B_FIXED,
            },
            "summary": {
                "theta_fixed_mean": float(np.mean(thetas_fixed)),
                "theta_fixed_std": float(np.std(thetas_fixed)),
                "theta_fixed_median": float(np.median(thetas_fixed)),
                "theta_estimated_mean": float(np.mean(thetas_estimated)),
                "H_s_mean": float(np.mean(h_s_values)),
                "H_a_mean": float(np.mean(h_a_values)),
                "R_sa_mean": float(np.mean(r_sa_values)),
                "S_B_estimated_mean": float(np.mean(s_b_est_values)),
            },
            "sessions": [{
                "file": r.session_file,
                "date": r.session_date,
                "title": r.session_title,
                "theta_fixed": round(r.theta_fixed, 4),
                "theta_estimated": round(r.theta_estimated, 4),
                "H_s": round(r.H_s, 4),
                "H_a": round(r.H_a, 4),
                "R_sa": round(r.R_sa, 4),
                "S_B_fixed": r.S_B_fixed,
                "S_B_estimated": round(r.S_B_estimated, 4),
                "total_calls": r.total_tool_calls,
                "unique_tools": r.unique_tools,
                "unique_servers": r.unique_servers,
                "error_count": r.error_count,
            } for r in results],
        }
        json_path = Path(__file__).parent / "hgk_theta_auto_results.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n✅ JSON 出力: {json_path}")
    
    # --- 目標達成判定 ---
    print(f"\n{'='*70}")
    if n >= 300:
        print(f"🎯 目標達成: n={n} ≥ 300")
    elif n >= 100:
        print(f"⚠️ 部分達成: n={n} (目標: 300)")
    else:
        print(f"❌ 不足: n={n} (目標: 300)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
