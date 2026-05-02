#!/usr/bin/env python3
# PROOF: mekhane/mcp/gateway_tools/_remover.py
# PURPOSE: mcp モジュールの _remover
"""hgk_gateway.py から移動済み関数を削除する。

_splitter.py で特定した関数の行範囲を使い、
各関数をコメント1行に置き換える。
"""
import ast
from pathlib import Path

SRC = Path("mekhane/mcp/hgk_gateway.py")

# 移動済みの関数 (CCL は既に手動で削除済み)
MOVED = {
    "hgk_sop_generate", "hgk_search", "hgk_doxa_read", "hgk_handoff_read",
    "hgk_idea_capture", "hgk_status", "hgk_gateway_health",
    "hgk_pks_stats", "hgk_pks_health", "hgk_pks_search",
    "hgk_paper_search",
    "hgk_digest_check", "hgk_digest_mark", "hgk_digest_list",
    "hgk_digest_topics", "hgk_digest_run",
    "_check_rate_limit", "hgk_sessions", "_sessions_from_handoffs",
    "hgk_session_read", "hgk_ask", "hgk_models", "hgk_ochema_status",
    "hgk_ask_with_tools", "hgk_chat_start", "hgk_chat_send", "hgk_chat_close",
    "hgk_health", "hgk_notifications",
    "_get_pks_engine", "hgk_proactive_push", "_auto_extract_topics",
    "_jules_init_pool", "_jules_get_key", "_jules_record",
    "hgk_jules_create_task", "hgk_jules_get_status",
    "hgk_jules_list_repos", "hgk_jules_batch_execute",
    "hgk_research", "hgk_research_search", "hgk_research_sources",
    "hgk_periskope_track", "hgk_periskope_metrics", "hgk_periskope_benchmark",
    "hgk_typos_generate", "hgk_typos_parse", "hgk_typos_validate",
    "hgk_typos_compile", "hgk_typos_expand", "hgk_typos_policy_check",
    "_cowork_ensure_dirs", "_cowork_rotate",
    "hgk_cowork_save", "hgk_cowork_resume",
    "_get_sympatheia",
    "hgk_sympatheia_wbc", "hgk_sympatheia_attractor",
    "hgk_sympatheia_digest", "hgk_sympatheia_feedback",
    "hgk_sympatheia_basanos_scan", "hgk_sympatheia_peira_health",
    "hgk_sympatheia_log_violation", "hgk_sympatheia_violation_dashboard",
    "hgk_sympatheia_escalate",
}

source = SRC.read_text(encoding="utf-8")
lines = source.split("\n")
tree = ast.parse(source)

# 削除する行範囲を収集
remove_ranges = []
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if node.name in MOVED:
            start = node.lineno
            if node.decorator_list:
                start = min(d.lineno for d in node.decorator_list)
            end = node.end_lineno
            
            # 直前のコメントも含める
            scan = start - 2  # 0-indexed
            while scan >= 0 and (lines[scan].strip().startswith("#") or lines[scan].strip() == ""):
                if lines[scan].strip().startswith("# PURPOSE:") or lines[scan].strip().startswith("# ==="):
                    start = scan + 1
                scan -= 1
            
            remove_ranges.append((start, end, node.name))

# 行番号でソート (降順で後ろから削除)
remove_ranges.sort(key=lambda x: x[0], reverse=True)

# 削除実行
for start, end, name in remove_ranges:
    # ドメイン判定
    domain = "gateway_tools"
    replacement = f"# {name} → {domain} に移動\n"
    lines[start-1:end] = [replacement.rstrip()]

new_source = "\n".join(lines)
SRC.write_text(new_source, encoding="utf-8")

total_removed = len(remove_ranges)
new_lines = len(new_source.split("\n"))
print(f"✅ {total_removed} functions removed. {len(source.split(chr(10)))} → {new_lines} lines")
