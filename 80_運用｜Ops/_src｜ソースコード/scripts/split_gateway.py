#!/usr/bin/env python3
"""hgk_gateway.py を core + gateway_tools/ に分割するスクリプト。

戦略:
1. L1-577 をコアとして hgk_gateway.py に残す
2. L578 以降を解析し、ドメイン別にファイルを生成
3. gateway_tools/__init__.py で全モジュールを import
"""
import os
import re
from pathlib import Path

SRC = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/mcp/hgk_gateway.py")
TOOLS_DIR = Path("/home/makaron8426/Sync/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane/mcp/gateway_tools")

# ドメイン→関数名マッピング
DOMAINS = {
    "knowledge": [
        "hgk_sop_generate", "hgk_search", "hgk_doxa_read", "hgk_handoff_read",
        "hgk_idea_capture", "hgk_status", "hgk_sessions", "hgk_session_read",
        "hgk_gateway_health",
    ],
    "ccl": ["hgk_ccl_dispatch", "hgk_ccl_execute", "hgk_ccl_run"],
    "digestor": [
        "hgk_digest_check", "hgk_digest_mark", "hgk_digest_list",
        "hgk_digest_topics", "hgk_digest_run",
    ],
    "ochema": [
        "hgk_ask", "hgk_ask_with_tools", "hgk_models", "hgk_ochema_status",
        "hgk_chat_start", "hgk_chat_send", "hgk_chat_close",
        "hgk_cowork_save", "hgk_cowork_resume",
    ],
    "search": ["hgk_pks_stats", "hgk_pks_health", "hgk_pks_search", "hgk_paper_search"],
    "sympatheia": [
        "hgk_sympatheia_wbc", "hgk_sympatheia_attractor", "hgk_sympatheia_basanos_scan",
        "hgk_sympatheia_digest", "hgk_sympatheia_escalate", "hgk_sympatheia_feedback",
        "hgk_sympatheia_log_violation", "hgk_sympatheia_peira_health",
        "hgk_sympatheia_violation_dashboard", "hgk_health", "hgk_notifications",
        "hgk_proactive_push",
    ],
    "periskope": [
        "hgk_research", "hgk_research_search", "hgk_research_sources",
        "hgk_periskope_benchmark", "hgk_periskope_metrics", "hgk_periskope_track",
    ],
    "typos": [
        "hgk_typos_compile", "hgk_typos_expand", "hgk_typos_generate",
        "hgk_typos_parse", "hgk_typos_policy_check", "hgk_typos_validate",
    ],
    "jules": [
        "hgk_jules_create_task", "hgk_jules_get_status",
        "hgk_jules_list_repos", "hgk_jules_batch_execute",
    ],
}

# Build reverse map: function_name → domain
func_to_domain = {}
for domain, funcs in DOMAINS.items():
    for f in funcs:
        func_to_domain[f] = domain

# Read entire file
lines = SRC.read_text().splitlines(keepends=True)
print(f"Total lines: {len(lines)}")

# Core ends at line 577 (0-indexed: 576)
CORE_END = 577  # inclusive, 1-indexed

# Parse tool blocks: find @mcp.tool() → def → end of function
# Also capture section comments and helper functions that precede @mcp.tool()
tool_blocks = []  # (start_line_0idx, end_line_0idx, func_name)

i = CORE_END  # Start after core (0-indexed)
while i < len(lines):
    line = lines[i]
    if '@mcp.tool()' in line:
        # Walk back to include preceding comments/section headers/PURPOSE/helper functions
        block_start = i
        # Look back for section comments and PURPOSE lines
        j = i - 1
        while j >= CORE_END:
            stripped = lines[j].strip()
            if stripped == '' or stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                j -= 1
            else:
                break
        # The block starts at j+1
        block_start = j + 1
        
        # Find the def line
        k = i + 1
        while k < len(lines) and not lines[k].strip().startswith('def '):
            k += 1
        
        if k < len(lines):
            m = re.match(r'\s*def\s+(\w+)', lines[k])
            func_name = m.group(1) if m else "unknown"
        else:
            func_name = "unknown"
        
        # Find end of function: next @mcp.tool() or section comment at same indent or EOF
        # or next non-decorated def at top level
        end = k + 1
        while end < len(lines):
            stripped = lines[end].strip()
            if '@mcp.tool()' in lines[end]:
                break
            # Check for `if __name__` block
            if lines[end].startswith('if __name__'):
                break
            # New section at top level (non-indented def/class that is NOT a helper)
            end += 1
        
        tool_blocks.append((block_start, end, func_name))
        i = end
    else:
        i += 1

print(f"Tool blocks found: {len(tool_blocks)}")
for start, end, name in tool_blocks[:5]:
    print(f"  L{start+1}-L{end}: {name}")
print(f"  ...")
for start, end, name in tool_blocks[-3:]:
    print(f"  L{start+1}-L{end}: {name}")

# Group blocks by domain
domain_blocks = {d: [] for d in DOMAINS}
unclassified_blocks = []

for start, end, name in tool_blocks:
    domain = func_to_domain.get(name)
    if domain:
        domain_blocks[domain].append((start, end, name))
    else:
        unclassified_blocks.append((start, end, name))

if unclassified_blocks:
    print(f"\nWARNING: Unclassified blocks:")
    for s, e, n in unclassified_blocks:
        print(f"  L{s+1}-L{e}: {n}")

# Also find non-tool helper functions/variables between blocks
# These need to go to the domain that uses them or stay in core

# Collect inter-block content (helpers, constants used by tools)
# For now, include them in the nearest following tool's domain

# Create gateway_tools/ directory
TOOLS_DIR.mkdir(exist_ok=True)

# Generate each domain file
for domain, blocks in domain_blocks.items():
    if not blocks:
        continue
    
    out_lines = []
    out_lines.append(f'"""Gateway tools: {domain} domain."""\n')
    out_lines.append("from mekhane.mcp.hgk_gateway import (\n")
    out_lines.append("    mcp, _traced, MNEME_DIR, PROJECT_ROOT, POLICY, _get_policy,\n")
    out_lines.append(")\n")
    out_lines.append("from pathlib import Path\n")
    out_lines.append("import os\n")
    out_lines.append("import json\n")
    out_lines.append("import time\n")
    out_lines.append("\n\n")
    
    for start, end, name in blocks:
        # Include the actual lines
        block = lines[start:end]
        out_lines.extend(block)
    
    filepath = TOOLS_DIR / f"{domain}.py"
    filepath.write_text("".join(out_lines))
    func_count = len(blocks)
    line_count = len(out_lines)
    print(f"Written {filepath.name}: {func_count} tools, {line_count} lines")

# Generate __init__.py
init_lines = ['"""Gateway tools package — registers all @mcp.tool() handlers."""\n\n']
init_lines.append("def register_all():\n")
init_lines.append('    """Import all domain modules to trigger @mcp.tool() registration."""\n')
for domain in sorted(DOMAINS.keys()):
    if domain_blocks.get(domain):
        init_lines.append(f"    from mekhane.mcp.gateway_tools import {domain}  # noqa: F401\n")

init_path = TOOLS_DIR / "__init__.py"
init_path.write_text("".join(init_lines))
print(f"Written __init__.py")

# Report
total_tools = sum(len(b) for b in domain_blocks.values())
print(f"\nTotal tools extracted: {total_tools}")
print(f"Unclassified: {len(unclassified_blocks)}")
