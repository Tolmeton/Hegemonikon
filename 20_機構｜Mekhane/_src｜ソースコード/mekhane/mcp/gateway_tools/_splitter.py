#!/usr/bin/env python3
# PROOF: mekhane/mcp/gateway_tools/_splitter.py
# PURPOSE: mcp モジュールの _splitter
"""Gateway splitter v2 — 遅延 import パターンで domain files を生成。

このスクリプトは hgk_gateway.py を読み、各関数を正確に AST で解析して
domain files を生成する。sed ベースの前回とは異なり、Python AST を使い
関数の正確な範囲を取得する。
"""
import ast
import sys
import textwrap
from pathlib import Path

SRC = Path("mekhane/mcp/hgk_gateway.py")
DST = Path("mekhane/mcp/gateway_tools")

# ドメイン分類: 関数名 → ドメイン
DOMAIN_MAP = {
    # knowledge (7 tools)
    "hgk_sop_generate": "knowledge",
    "hgk_search": "knowledge",
    "hgk_doxa_read": "knowledge",
    "hgk_handoff_read": "knowledge",
    "hgk_idea_capture": "knowledge",
    "hgk_status": "knowledge",
    "hgk_gateway_health": "knowledge",
    # pks (3 tools → knowledge に含める)
    "hgk_pks_stats": "knowledge",
    "hgk_pks_health": "knowledge",
    "hgk_pks_search": "knowledge",
    # paper search (1 tool → search に含める)
    "hgk_paper_search": "search",
    # digestor (5 tools)
    "hgk_digest_check": "digestor",
    "hgk_digest_mark": "digestor",
    "hgk_digest_list": "digestor",
    "hgk_digest_topics": "digestor",
    "hgk_digest_run": "digestor",
    # ochema (9 tools)
    "hgk_sessions": "ochema",
    "hgk_session_read": "ochema",
    "hgk_ask": "ochema",
    "hgk_models": "ochema",
    "hgk_ochema_status": "ochema",
    "hgk_ask_with_tools": "ochema",
    "hgk_chat_start": "ochema",
    "hgk_chat_send": "ochema",
    "hgk_chat_close": "ochema",
    # sympatheia (9 tools)
    "hgk_health": "sympatheia",
    "hgk_notifications": "sympatheia",
    "hgk_proactive_push": "sympatheia",
    "hgk_sympatheia_wbc": "sympatheia",
    "hgk_sympatheia_attractor": "sympatheia",
    "hgk_sympatheia_digest": "sympatheia",
    "hgk_sympatheia_feedback": "sympatheia",
    "hgk_sympatheia_basanos_scan": "sympatheia",
    "hgk_sympatheia_peira_health": "sympatheia",
    "hgk_sympatheia_log_violation": "sympatheia",
    "hgk_sympatheia_violation_dashboard": "sympatheia",
    "hgk_sympatheia_escalate": "sympatheia",
    # jules (4 tools)
    "hgk_jules_create_task": "jules",
    "hgk_jules_get_status": "jules",
    "hgk_jules_list_repos": "jules",
    "hgk_jules_batch_execute": "jules",
    # periskope (5 tools)
    "hgk_research": "periskope",
    "hgk_research_search": "periskope",
    "hgk_research_sources": "periskope",
    "hgk_periskope_track": "periskope",
    "hgk_periskope_metrics": "periskope",
    "hgk_periskope_benchmark": "periskope",
    # typos (6 tools)
    "hgk_typos_generate": "typos",
    "hgk_typos_parse": "typos",
    "hgk_typos_validate": "typos",
    "hgk_typos_compile": "typos",
    "hgk_typos_expand": "typos",
    "hgk_typos_policy_check": "typos",
    # cowork (2 tools → knowledge に含める)
    "hgk_cowork_save": "knowledge",
    "hgk_cowork_resume": "knowledge",
}

# ヘルパー関数 → ドメイン
HELPER_MAP = {
    "_check_rate_limit": "ochema",
    "_sessions_from_handoffs": "ochema",
    "_get_pks_engine": "sympatheia",
    "_auto_extract_topics": "sympatheia",
    "_jules_init_pool": "jules",
    "_jules_get_key": "jules",
    "_jules_record": "jules",
    "_cowork_ensure_dirs": "knowledge",
    "_cowork_rotate": "knowledge",
    "_get_sympatheia": "sympatheia",
}

# ドメインが使用するコアのシンボル
DOMAIN_IMPORTS = {
    "knowledge": ["mcp", "_traced", "_get_policy", "_trace_tool_call",
                   "MNEME_DIR", "SESSIONS_DIR", "DOXA_DIR", "SOP_OUTPUT_DIR",
                   "IDEA_DIR", "PROJECT_ROOT", "POLICY", "GATEWAY_URL"],
    "digestor": ["mcp", "_traced"],
    "ochema": ["mcp", "_traced", "_get_policy", "_trace_tool_call", "GATEWAY_URL"],
    "search": ["mcp", "_traced", "_get_policy", "_trace_tool_call"],
    "sympatheia": ["mcp", "_traced", "_get_policy", "_trace_tool_call",
                    "MNEME_DIR", "PROJECT_ROOT", "GATEWAY_URL"],
    "jules": ["mcp", "_traced", "_get_policy", "_trace_tool_call", "GATEWAY_URL"],
    "periskope": ["mcp", "_traced", "_get_policy", "_trace_tool_call", "GATEWAY_URL"],
    "typos": ["mcp", "_traced", "_get_policy", "_trace_tool_call", "PROJECT_ROOT"],
}


def main():
    source = SRC.read_text(encoding="utf-8")
    lines = source.split("\n")
    
    # AST 解析
    tree = ast.parse(source)
    
    # 関数の行範囲を取得 (decorator 込み)
    functions = {}  # name -> (start_line, end_line, source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name
            if name in DOMAIN_MAP or name in HELPER_MAP:
                # decorator の開始行を考慮
                start = node.lineno
                if node.decorator_list:
                    start = min(d.lineno for d in node.decorator_list)
                end = node.end_lineno
                
                # セクションコメント (直前の # === 行) も含める
                scan = start - 2  # 1-indexed → 0-indexed, -1 for previous line
                while scan >= 0 and (lines[scan].strip().startswith("#") or lines[scan].strip() == ""):
                    if lines[scan].strip().startswith("# PURPOSE:") or lines[scan].strip().startswith("# ==="):
                        start = scan + 1  # 1-indexed
                    scan -= 1
                
                func_lines = lines[start-1:end]
                functions[name] = (start, end, "\n".join(func_lines))
    
    # ドメインごとにグループ化
    domains = {}
    for name, domain in {**DOMAIN_MAP, **HELPER_MAP}.items():
        if name in functions:
            domains.setdefault(domain, []).append((name, functions[name]))
    
    # 各ドメインファイルを生成
    for domain, funcs in domains.items():
        domain_imports = DOMAIN_IMPORTS.get(domain, ["mcp", "_traced"])
        import_str = ", ".join(domain_imports)
        
        # ソートして行番号順に
        funcs.sort(key=lambda x: x[1][0])
        
        func_bodies = []
        for name, (start, end, src) in funcs:
            # インデント1段追加 (register 関数のクロージャ内)
            indented = textwrap.indent(src, "    ")
            func_bodies.append(indented)
        
        register_name = f"register_{domain}_tools"
        func_names = [f[0] for f in funcs if f[0] in DOMAIN_MAP]
        
        content = f'''"""Gateway tools: {domain} domain."""
import time


def {register_name}():
    """Register {domain} domain tools ({len(func_names)} tools)."""
    from mekhane.mcp.hgk_gateway import {import_str}

{chr(10).join(func_bodies)}
'''
        
        outfile = DST / f"{domain}.py"
        outfile.write_text(content, encoding="utf-8")
        print(f"  ✅ {outfile}: {len(func_names)} tools, {len(funcs)} functions")
    
    # 統計
    total_tools = sum(
        len([f for f in funcs if f[0] in DOMAIN_MAP])
        for funcs in domains.values()
    )
    print(f"\n📊 Total: {total_tools} tools across {len(domains)} domains")
    
    # hgk_gateway.py から削除すべき行範囲を出力
    print("\n🗑️ Lines to remove from hgk_gateway.py:")
    all_ranges = []
    for name, (start, end, _) in sorted(functions.items(), key=lambda x: x[1][0]):
        all_ranges.append((start, end, name))
        print(f"  {name}: L{start}-L{end}")
    
    return all_ranges


if __name__ == "__main__":
    ranges = main()
