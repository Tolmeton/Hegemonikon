#!/usr/bin/env python3
"""conv パーサー PoC — HGK+ データ拡張

conv セッションログから MCP ツール使用パターンを自動抽出し、
H(s)/H(a)/R(s,a)/S(B) を計算する。

操作的定義 (compute_theta_b_v2.py L154-157 準拠):
  H(s): サーバ別ツール分布のエントロピー (正規化)
  H(a): 実際使用ツール名の頻度分布のエントロピー (正規化)
  R(s,a): I(s;a) = H(s) + H(a) - H(s,a)  相互情報量
  S(B): MCP 応答成功率 (conv テキストからの近似)

使い方:
  python conv_parser_poc.py                     # 全 conv ファイルを処理
  python conv_parser_poc.py --limit 5           # 先頭5ファイルのみ
  python conv_parser_poc.py --csv results.csv   # CSV 出力
"""
import re
import math
import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field

# === MCP ツール定義 ===
# サーバー → ツール のマッピング (HGK の MCP 体系)
SERVER_TOOLS = {
    "hermeneus": [
        "hermeneus_run", "hermeneus_analyze", "hermeneus_admin",
    ],
    "ochema": [
        "ochema_ask", "ochema_chat", "ochema_context", "ochema_info",
        "ochema_plan_task",
    ],
    "mneme": [
        "mneme_search", "mneme_check", "mneme_graph", "mneme_convert",
        "mneme_recommend_model",
    ],
    "periskope": [
        "periskope_research", "periskope_search", "periskope_track",
        "periskope_admin",
    ],
    "digestor": [
        "digestor_paper", "digestor_pipeline",
    ],
    "sekisho": [
        "sekisho_audit", "sekisho_admin",
    ],
    "sympatheia": [
        "sympatheia_monitor", "sympatheia_ops", "sympatheia_violations",
    ],
    "jules": [
        "jules_task",
    ],
    "typos": [
        "typos_compile", "typos_policy_check",
    ],
    "phantazein": [
        "phantazein_boot", "phantazein_check", "phantazein_info",
        "phantazein_session",
    ],
    "hub": [
        "hub_execute", "hub_recommend", "hub_gate",
        "hub_shadow_status", "hub_stats",
    ],
}

# IDE ビルトインツール (サーバー = "ide")
IDE_TOOLS = [
    "view_file", "write_to_file", "replace_file_content",
    "multi_replace_file_content", "run_command", "command_status",
    "send_command_input", "search_web", "read_url_content",
    "grep_search", "find_by_name", "list_dir", "generate_image",
    "browser_subagent",
]

# ツール → サーバーの逆引き辞書
TOOL_TO_SERVER = {}
for server, tools in SERVER_TOOLS.items():
    for tool in tools:
        TOOL_TO_SERVER[tool] = server
for tool in IDE_TOOLS:
    TOOL_TO_SERVER[tool] = "ide"

# 全ツール名のリスト (regex 用)
ALL_TOOL_NAMES = list(TOOL_TO_SERVER.keys())
# サーバー名のリスト (conv テキスト内のサーバー名マッチ用)
ALL_SERVER_NAMES = list(SERVER_TOOLS.keys())


@dataclass
class SessionMetrics:
    """1セッションの計測結果"""
    filename: str
    tool_counts: Counter = field(default_factory=Counter)   # ツール名 → 出現回数
    server_counts: Counter = field(default_factory=Counter)  # サーバー名 → 出現回数
    error_count: int = 0
    success_count: int = 0
    total_tool_uses: int = 0

    # 計算結果
    H_s: float = 0.0
    H_a: float = 0.0
    R_sa: float = 0.0
    S_B: float = 0.0
    k_s: int = 0   # 利用サーバー数
    k_a: int = 0   # 利用ツール数
    theta_B: float = 0.0


def shannon_entropy(counts: list[int]) -> float:
    """Shannon entropy H = -Σ p_i log2(p_i)"""
    total = sum(counts)
    if total == 0:
        return 0.0
    probs = [c / total for c in counts if c > 0]
    return -sum(p * math.log2(p) for p in probs)


def normalized_entropy(counts: list[int]) -> float:
    """正規化 Shannon entropy H_norm = H / log2(n)"""
    n = len([c for c in counts if c > 0])
    if n <= 1:
        return 0.0
    h = shannon_entropy(counts)
    return h / math.log2(n)


def mutual_information(joint_counts: dict[tuple, int]) -> float:
    """相互情報量 I(X;Y) = H(X) + H(Y) - H(X,Y)"""
    marginal_x: Counter = Counter()
    marginal_y: Counter = Counter()
    for (x, y), c in joint_counts.items():
        marginal_x[x] += c
        marginal_y[y] += c

    h_x = shannon_entropy(list(marginal_x.values()))
    h_y = shannon_entropy(list(marginal_y.values()))
    h_xy = shannon_entropy(list(joint_counts.values()))
    return max(0.0, h_x + h_y - h_xy)


def extract_tool_usage(text: str) -> tuple[Counter, Counter, int, int]:
    """conv テキストから MCP ツール使用パターンを抽出

    Returns:
        tool_counts: ツール名 → 出現回数
        server_counts: サーバー名 → 出現回数
        error_count: エラーパターンの出現回数
        success_count: 成功パターンの出現回数
    """
    tool_counts = Counter()
    server_counts = Counter()
    error_count = 0
    success_count = 0

    # ツール名の直接マッチ (長い名前から順にマッチさせる)
    sorted_tools = sorted(ALL_TOOL_NAMES, key=len, reverse=True)
    for tool_name in sorted_tools:
        # ワード境界を含むパターンで検索
        pattern = re.compile(r'\b' + re.escape(tool_name) + r'\b', re.IGNORECASE)
        matches = pattern.findall(text)
        if matches:
            count = len(matches)
            tool_counts[tool_name] += count
            server = TOOL_TO_SERVER.get(tool_name, "unknown")
            server_counts[server] += count

    # MCP プレフィックス付きツール名のマッチ
    mcp_pattern = re.compile(r'mcp_(\w+?)_(\w+)')
    for match in mcp_pattern.finditer(text):
        server_name = match.group(1)
        full_tool = f"{match.group(2)}"
        # すでにカウントされている場合はスキップ
        if full_tool not in tool_counts:
            tool_counts[full_tool] += 1
            server_counts[server_name] += 1

    # エラー/成功パターンの検出
    # エラーパターン
    error_patterns = [
        r'\berror\b', r'\bfailed\b', r'\bfailure\b',
        r'エラー', r'失敗', r'例外',
        r'\bException\b', r'\bTraceback\b',
    ]
    for pat in error_patterns:
        error_count += len(re.findall(pat, text, re.IGNORECASE))

    # 成功パターン
    success_patterns = [
        r'\bsuccess\b', r'\bcompleted?\b', r'\bpass(?:ed)?\b',
        r'成功', r'完了',
    ]
    for pat in success_patterns:
        success_count += len(re.findall(pat, text, re.IGNORECASE))

    return tool_counts, server_counts, error_count, success_count


def compute_session_metrics(filepath: Path) -> SessionMetrics | None:
    """1 conv ファイルから Θ(B) メトリクスを計算"""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  ⚠️ 読み込み失敗: {filepath.name}: {e}")
        return None

    tool_counts, server_counts, error_count, success_count = extract_tool_usage(text)

    # MCP ツールのみ (IDE ツールを除外)
    mcp_tool_counts = Counter({
        k: v for k, v in tool_counts.items()
        if TOOL_TO_SERVER.get(k, "ide") != "ide"
    })
    mcp_server_counts = Counter({
        k: v for k, v in server_counts.items()
        if k != "ide"
    })

    total_mcp = sum(mcp_tool_counts.values())

    # MCP ツール使用なし → HGK+ セッションでない可能性
    if total_mcp < 3:
        return None

    metrics = SessionMetrics(
        filename=filepath.name,
        tool_counts=mcp_tool_counts,
        server_counts=mcp_server_counts,
        error_count=error_count,
        success_count=success_count,
        total_tool_uses=total_mcp,
    )

    # H(s): サーバー分布の正規化エントロピー
    metrics.H_s = normalized_entropy(list(mcp_server_counts.values()))
    metrics.k_s = len(mcp_server_counts)

    # H(a): ツール使用頻度の正規化エントロピー
    metrics.H_a = normalized_entropy(list(mcp_tool_counts.values()))
    metrics.k_a = len(mcp_tool_counts)

    # R(s,a): 相互情報量
    # 同時分布: (server, tool) → count
    joint = {}
    for tool, count in mcp_tool_counts.items():
        server = TOOL_TO_SERVER.get(tool, "unknown")
        joint[(server, tool)] = count
    metrics.R_sa = mutual_information(joint)

    # S(B): 成功率の近似
    total_signals = error_count + success_count
    if total_signals > 0:
        metrics.S_B = success_count / total_signals
    else:
        metrics.S_B = 0.8  # デフォルト: 信号なしの場合は 0.8 と仮定

    # Θ(B) 計算 (v2 と同じ定義)
    alpha, beta, gamma = 1.0, 1.0, 1.0
    metrics.theta_B = metrics.S_B * (
        1 + alpha * metrics.H_s + beta * metrics.H_a + gamma * metrics.R_sa
    )

    return metrics


def main():
    parser = argparse.ArgumentParser(description="conv パーサー PoC — HGK+ データ拡張")
    parser.add_argument("--conv-dir", type=Path,
                        default=Path(__file__).parent.parent.parent /
                        "30_記憶｜Mneme/01_記録｜Records/b_対話｜sessions/conv",
                        help="conv ディレクトリのパス")
    parser.add_argument("--limit", type=int, default=0,
                        help="処理するファイル数の上限 (0=全部)")
    parser.add_argument("--min-mcp", type=int, default=3,
                        help="HGK+ 判定の最小 MCP ツール使用回数")
    parser.add_argument("--csv", type=str, default="",
                        help="CSV 出力ファイルパス")
    parser.add_argument("--verbose", action="store_true",
                        help="各セッションの詳細を表示")
    args = parser.parse_args()

    conv_dir = args.conv_dir
    if not conv_dir.exists():
        print(f"❌ ディレクトリが見つかりません: {conv_dir}")
        return

    # conv ファイルの一覧
    conv_files = sorted(conv_dir.glob("*.md"))
    total_files = len(conv_files)
    print(f"📂 conv ディレクトリ: {conv_dir}")
    print(f"📄 ファイル数: {total_files}")

    if args.limit > 0:
        conv_files = conv_files[:args.limit]
        print(f"📎 上限: {args.limit} ファイル")

    print(f"\n{'='*70}")
    print(f"  conv パーサー PoC — HGK+ メトリクス自動抽出")
    print(f"{'='*70}\n")

    results: list[SessionMetrics] = []
    skipped = 0

    for i, filepath in enumerate(conv_files, 1):
        if i % 50 == 0 or i == len(conv_files):
            print(f"  処理中: {i}/{len(conv_files)}...")

        metrics = compute_session_metrics(filepath)
        if metrics is None:
            skipped += 1
            continue
        results.append(metrics)

        if args.verbose:
            print(f"\n  [{i}] {filepath.name}")
            print(f"    MCP: {metrics.total_tool_uses} calls | "
                  f"k_s={metrics.k_s} | k_a={metrics.k_a}")
            print(f"    H(s)={metrics.H_s:.3f} | H(a)={metrics.H_a:.3f} | "
                  f"R(s,a)={metrics.R_sa:.3f} | S(B)={metrics.S_B:.3f}")
            print(f"    Θ(B)={metrics.theta_B:.3f}")
            top_tools = metrics.tool_counts.most_common(5)
            print(f"    Top tools: {', '.join(f'{t}={c}' for t,c in top_tools)}")

    # === サマリー ===
    print(f"\n{'='*70}")
    print(f"  サマリー")
    print(f"{'='*70}")
    print(f"  全ファイル: {total_files}")
    print(f"  処理対象 : {len(conv_files)}")
    print(f"  HGK+ 判定: {len(results)} セッション (MCP≥{args.min_mcp})")
    print(f"  スキップ : {skipped} (MCP使用 < {args.min_mcp})")

    if results:
        h_s_vals = [r.H_s for r in results]
        h_a_vals = [r.H_a for r in results]
        r_sa_vals = [r.R_sa for r in results]
        s_b_vals = [r.S_B for r in results]
        theta_vals = [r.theta_B for r in results]
        k_s_vals = [r.k_s for r in results]
        k_a_vals = [r.k_a for r in results]

        print(f"\n  n = {len(results)} セッション")
        print(f"\n  {'指標':>10s} {'平均':>8s} {'標準偏差':>8s} {'最小':>8s} {'最大':>8s}")
        print(f"  {'-'*50}")
        for name, vals in [
            ("H(s)", h_s_vals), ("H(a)", h_a_vals),
            ("R(s,a)", r_sa_vals), ("S(B)", s_b_vals),
            ("Θ(B)", theta_vals), ("k_s", k_s_vals), ("k_a", k_a_vals),
        ]:
            mean = sum(vals) / len(vals)
            std = (sum((v - mean)**2 for v in vals) / len(vals)) ** 0.5
            print(f"  {name:>10s} {mean:8.3f} {std:8.3f} {min(vals):8.3f} {max(vals):8.3f}")

        # v2 の手動値との比較
        print(f"\n  📊 v2 手動計測値との比較:")
        print(f"  v2 Session 1: H(s)=2.81, H(a)=2.32, R(s,a)=0.67, S(B)=0.94")
        print(f"  v2 Session 2: H(s)=2.65, H(a)=2.18, R(s,a)=0.71, S(B)=0.91")
        print(f"  conv 自動平均: H(s)={sum(h_s_vals)/len(h_s_vals):.2f}, "
              f"H(a)={sum(h_a_vals)/len(h_a_vals):.2f}, "
              f"R(s,a)={sum(r_sa_vals)/len(r_sa_vals):.2f}, "
              f"S(B)={sum(s_b_vals)/len(s_b_vals):.2f}")

    # CSV 出力
    if args.csv and results:
        import csv
        with open(args.csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'filename', 'H_s', 'H_a', 'R_sa', 'S_B', 'theta_B',
                'k_s', 'k_a', 'total_mcp', 'error_count', 'success_count',
            ])
            for r in results:
                writer.writerow([
                    r.filename, f"{r.H_s:.4f}", f"{r.H_a:.4f}",
                    f"{r.R_sa:.4f}", f"{r.S_B:.4f}", f"{r.theta_B:.4f}",
                    r.k_s, r.k_a, r.total_tool_uses,
                    r.error_count, r.success_count,
                ])
        print(f"\n  📁 CSV 出力: {args.csv}")


if __name__ == "__main__":
    main()
