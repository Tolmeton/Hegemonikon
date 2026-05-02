#!/usr/bin/env python3
"""
MCP Tool Description Smell Linter v2.0

Based on arXiv:2602.14878 (MCPCorpus) — extended with AST-based tool extraction.

Two-layer analysis:
  Layer 1: Server-level descriptions from mcp_config.json
  Layer 2: Tool-level descriptions extracted via AST from *_mcp_server.py files

Smell categories (12):
  1. too_brief      — Description < 20 chars
  2. too_long       — Description > 500 chars
  3. missing_return — No return value info
  4. missing_example— No usage example
  5. missing_error  — No error conditions
  6. jargon         — HGK-specific terms without explanation
  7. overloaded     — Too many responsibilities
  8. ambiguous      — Unclear scope
  9. missing_param  — Parameters not explained
  10. bilingual_mix — Mixed Japanese/English without consistency
  11. no_verb       — Description doesn't start with an action verb
  12. tool_count    — Server has too many tools (>15)

Usage:
    python scripts/check_mcp_smell.py                # Full analysis
    python scripts/check_mcp_smell.py --json          # JSON output
    python scripts/check_mcp_smell.py --server mneme  # Single server

Returns exit code 1 if average smells > 3.0 (CI gate).
"""

import ast
import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, field, asdict

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MCP_DIR = PROJECT_ROOT / "mekhane" / "mcp"
HERMENEUS_MCP = PROJECT_ROOT / "hermeneus" / "src" / "mcp_server.py"
CONFIG_PATH = PROJECT_ROOT.parent / ".gemini" / "antigravity" / "mcp_config.json"

# HGK Jargon patterns — terms that need explanation for external consumers
JARGON_PATTERNS = [
    (r"\bccl\b", "CCL (Cognitive Control Language)"),
    (r"\bfep\b", "FEP (Free Energy Principle)"),
    (r"\bhgk\b", "HGK (Hegemonikón)"),
    (r"\bhandoff\b", "Handoff (session transfer document)"),
    (r"\bsympatheia\b", "Sympatheia"),
    (r"\bperiskop[eē]\b", "Periskopē"),
    (r"\bmneme\b", "Mneme"),
    (r"\bochema\b", "Ochēma"),
    (r"\bherm[eē]neus\b", "Hermēneus"),
    (r"\bgn[oō]sis\b", "Gnōsis"),
    (r"\bsophia\b", "Sophia"),
    (r"\bkairos\b", "Kairos"),
    (r"\bchronos\b", "Chronos"),
    (r"\bkrisis\b", "Krisis"),
    (r"\bdokimasia\b", "Dokimasia"),
    (r"\bpeira\b", "Peira"),
    (r"\btaxis\b", "Taxis"),
    (r"\bdendron\b", "Dendron"),
    (r"(?:\bbc-\d+\b|\bn-\d+\b|θ\d+\.\d+)", "Hóros Constraint (BC/N/θ)"),
    (r"\bwbc\b", "WBC (White Blood Cell threat monitor)"),
]

# Action verbs that good descriptions start with
ACTION_VERBS = {
    "search", "get", "list", "create", "update", "delete", "run", "execute",
    "parse", "validate", "compile", "expand", "check", "send", "close",
    "start", "recommend", "generate", "set", "deploy", "health", "ping",
    "analyze", "adjust", "manage", "log", "display", "detect", "evaluate",
    "query", "export", "chat", "decompose", "compress",
}

# Internal HGK servers where jargon/bilingual are intentional design choices.
# These servers are consumed only by Claude/Gemini agents that already know HGK vocabulary.
# Smell suppression: jargon, bilingual_mix
INTERNAL_SERVERS = {
    "sympatheia", "hermeneus", "periskope", "ochema",
    "phantazein", "digestor", "gnosis", "sophia", "typos",
}


# =============================================================================
# Data Structures
# =============================================================================

@dataclass
class SmellResult:
    name: str
    description: str
    smells: list[str] = field(default_factory=list)
    level: str = "tool"  # "server" or "tool"


@dataclass
class ServerReport:
    server_name: str
    server_smell: SmellResult | None = None
    tool_smells: list[SmellResult] = field(default_factory=list)
    tool_count: int = 0


# =============================================================================
# Smell Detectors
# =============================================================================

def detect_smells(desc: str, name: str = "", server_name: str = "") -> list[str]:
    """Detect smells in a single description string.

    Args:
        desc: Description text
        name: Tool name (for analysis)
        server_name: Server name (for INTERNAL_SERVERS allowlist)
    """
    smells = []
    desc_lower = desc.lower()

    # 1. Length checks
    if len(desc) < 20:
        smells.append("too_brief")
    if len(desc) > 500:
        smells.append("too_long")

    # 2. Missing return info
    if not re.search(r"returns?[\s:.]", desc_lower):
        smells.append("missing_return")

    # 3. Missing example
    if "example" not in desc_lower and "e.g." not in desc_lower and "例" not in desc:
        smells.append("missing_example")

    # 4. Missing error conditions
    if not re.search(r"(error|fail|exception|raise|invalid)s?[\s:.,]", desc_lower):
        smells.append("missing_error")

    # 5. Jargon without explanation
    for pattern, label in JARGON_PATTERNS:
        if re.search(pattern, desc_lower):
            # Check if the jargon is followed by an explanation in parens
            explained = re.search(
                pattern + r"\s*[\(（]", desc_lower
            )
            if not explained:
                smells.append(f"jargon:{label}")
                break  # Report only first jargon hit per description

    # 6. Overloaded (too many semicolons or conjunctions)
    conj_count = desc_lower.count(" and ") + desc_lower.count("、") + desc_lower.count("、")
    if conj_count >= 4:
        smells.append("overloaded")

    # 7. Bilingual mix (Japanese + English without consistency)
    has_jp = bool(re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", desc))
    has_en = bool(re.search(r"[a-zA-Z]{3,}", desc))
    if has_jp and has_en:
        jp_ratio = len(re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", desc))
        en_ratio = len(re.findall(r"[a-zA-Z]", desc))
        total = jp_ratio + en_ratio
        if total > 10:
            ratio = min(jp_ratio, en_ratio) / total
            if 0.2 < ratio < 0.8:
                smells.append("bilingual_mix")

    # 8. No action verb at start
    first_word_raw = desc.split()[0].lower() if desc.split() else ""
    # "compress" のような s 終わりの単語を破壊しないよう、removesuffix を使用
    first_word = first_word_raw.removesuffix("s") if first_word_raw.endswith("s") and not first_word_raw.endswith("ss") else first_word_raw
    if first_word and first_word not in ACTION_VERBS and not has_jp:
        smells.append("no_verb")

    # Filter: suppress jargon/bilingual_mix for internal HGK servers
    if server_name.lower() in INTERNAL_SERVERS:
        smells = [s for s in smells if not s.startswith("jargon:") and s != "bilingual_mix"]

    return smells


def suggest_fix(name: str, desc: str, smells: list[str]) -> str:
    """Propose a fixed description based on detected smells."""
    if not smells:
        return desc
        
    lines = desc.strip().split('\n')
    first_line = lines[0]
    
    if "no_verb" in smells:
        action = name.split('_')[0].capitalize() if '_' in name else "Execute"
        first_line = f"{action} {first_line}"
    
    fixed = [first_line] + lines[1:]
    
    if "missing_return" in smells:
        fixed.append("Returns: result data.")
    
    if "missing_example" in smells:
        fixed.append(f"Example: {name}()")
        
    return '\n'.join(fixed)


# =============================================================================
# AST-based Tool Extraction
# =============================================================================

def extract_tools_from_file(filepath: Path) -> list[tuple[str, str]]:
    """Extract (tool_name, description) pairs from a MCP server Python file.

    Parses the AST to find Tool() constructor calls and extracts
    name and description keyword arguments.
    """
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  [WARN] Cannot parse {filepath.name}: {e}", file=sys.stderr)
        return []

    tools = []

    for node in ast.walk(tree):
        # Look for Tool(...) calls
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        func_name = None
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr

        if func_name != "Tool":
            continue

        # Extract name and description from keyword arguments
        name_val = None
        desc_val = None

        for kw in node.keywords:
            if kw.arg == "name":
                name_val = _extract_string(kw.value)
            elif kw.arg == "description":
                desc_val = _extract_string(kw.value)

        if name_val and desc_val:
            tools.append((name_val, desc_val))

    return tools


def _extract_string(node: ast.expr) -> str | None:
    """Extract string value from an AST node (handles concatenation)."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    elif isinstance(node, ast.JoinedStr):
        # f-string — can't fully resolve, return template
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant):
                parts.append(str(val.value))
            else:
                parts.append("{...}")
        return "".join(parts)
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        # String concatenation: "a" + "b"
        left = _extract_string(node.left)
        right = _extract_string(node.right)
        if left is not None and right is not None:
            return left + right
    elif isinstance(node, ast.Call):
        # Might be str() or similar — skip
        return None
    return None


# =============================================================================
# Main Analysis
# =============================================================================

def discover_mcp_servers() -> list[tuple[str, Path]]:
    """Find all MCP server Python files."""
    servers = []

    # mekhane/mcp/*_mcp_server.py
    for f in sorted(MCP_DIR.glob("*_mcp_server.py")):
        name = f.stem.replace("_mcp_server", "")
        servers.append((name, f))

    # hermeneus/src/mcp_server.py
    if HERMENEUS_MCP.exists():
        servers.append(("hermeneus", HERMENEUS_MCP))

    return servers


def run_smell_check(target_server: str | None = None) -> dict:
    """Run the full two-layer smell analysis.

    Returns:
        dict with server_count, tool_count, total_smells,
        average_smells_per_tool, reports (list of ServerReport as dicts)
    """
    reports: list[ServerReport] = []

    # Layer 1: Server-level descriptions from config
    server_descs = {}
    if CONFIG_PATH.exists():
        try:
            config = json.loads(CONFIG_PATH.read_text())
            for name, srv in config.get("mcpServers", {}).items():
                if "description" in srv:
                    server_descs[name.lower()] = srv["description"]
        except Exception:
            pass

    # Layer 2: Tool-level descriptions via AST
    mcp_files = discover_mcp_servers()

    for server_name, filepath in mcp_files:
        if target_server and server_name != target_server:
            continue

        report = ServerReport(server_name=server_name)

        # Server-level smell
        if server_name in server_descs:
            desc = server_descs[server_name]
            smells = detect_smells(desc, server_name, server_name=server_name)
            report.server_smell = SmellResult(
                name=server_name, description=desc,
                smells=smells, level="server"
            )

        # Tool-level smells
        tools = extract_tools_from_file(filepath)
        report.tool_count = len(tools)

        for tool_name, tool_desc in tools:
            smells = detect_smells(tool_desc, tool_name, server_name=server_name)
            report.tool_smells.append(SmellResult(
                name=tool_name, description=tool_desc,
                smells=smells, level="tool"
            ))

        # Meta-smell: too many tools
        if report.tool_count > 15:
            if report.server_smell is None:
                report.server_smell = SmellResult(
                    name=server_name, description="(no server description)",
                    smells=[], level="server"
                )
            report.server_smell.smells.append(
                f"tool_count:{report.tool_count} (>15, LLM selection degrades)"
            )

        reports.append(report)

    # Aggregate stats
    all_smells = []
    total_tools = 0
    for r in reports:
        if r.server_smell:
            all_smells.extend(r.server_smell.smells)
        for ts in r.tool_smells:
            all_smells.extend(ts.smells)
            total_tools += 1

    total_smells = len(all_smells)
    avg = total_smells / max(total_tools, 1)

    return {
        "server_count": len(reports),
        "tool_count": total_tools,
        "total_smells": total_smells,
        "average_smells_per_tool": round(avg, 2),
        "reports": [asdict(r) for r in reports],
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MCP Tool Description Smell Linter")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--server", type=str, help="Check single server")
    parser.add_argument("--fix", action="store_true", help="Propose automatic fixes for smells")
    parser.add_argument("--report", action="store_true", help="Generate analysis report (tool distribution)")
    args = parser.parse_args()

    result = run_smell_check(target_server=args.server)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["average_smells_per_tool"] <= 3.0 else 1)

    if args.report:
        print("\n📊 MCP Tool Distribution Report (Candidate B: Modularization Analysis)")
        print("=" * 60)
        reports = sorted(result["reports"], key=lambda r: r["tool_count"], reverse=True)
        for r in reports:
            print(f"{r['server_name']:15} | {r['tool_count']:3} tools")
        print("-" * 60)
        overloaded = [r['server_name'] for r in reports if r['tool_count'] >= 15]
        if overloaded:
            print(f"⚠️  Servers needing modularization/Context division: {', '.join(overloaded)}")
        sys.exit(0)

    # Human-readable output
    print(f"🔍 MCP Smell Linter v2.0")
    print(f"   Servers: {result['server_count']}  |  Tools: {result['tool_count']}")
    print(f"   Total Smells: {result['total_smells']}")
    print(f"   Average Smells/Tool: {result['average_smells_per_tool']:.2f}")
    print()

    for report in result["reports"]:
        name = report["server_name"]
        tc = report["tool_count"]
        srv_smells = report["server_smell"]["smells"] if report["server_smell"] else []
        tool_smell_count = sum(len(t["smells"]) for t in report["tool_smells"])
        total = len(srv_smells) + tool_smell_count

        icon = "✅" if total == 0 else "⚠️" if total <= 3 else "🔴"
        print(f"{icon} {name} ({tc} tools, {total} smells)")

        if srv_smells:
            print(f"   [server] {', '.join(srv_smells)}")

        for ts in report["tool_smells"]:
            if ts["smells"]:
                print(f"   [{ts['name']}] {', '.join(ts['smells'])}")
                if args.fix:
                    fixed = suggest_fix(ts['name'], ts['description'], ts['smells'])
                    fixed_indented = fixed.replace('\n', '\n      ')
                    print(f"      [FIX SUGGESTION]\n      {fixed_indented}")
        print()

    if result["average_smells_per_tool"] > 3.0:
        print("❌ FAIL: Average smell count exceeds threshold (3.0)")
        sys.exit(1)
    else:
        print("✅ PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
