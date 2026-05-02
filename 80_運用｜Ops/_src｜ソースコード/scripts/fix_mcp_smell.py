#!/usr/bin/env python3
"""
MCP Tool Description Auto-Fixer v1.0

Complements check_mcp_smell.py by auto-generating missing description elements:
  - Returns: ... (from tool name + inputSchema analysis)
  - Example: ... (from inputSchema required params)
  - Error conditions (from required params + common patterns)

Strategy:
  1. Parse each MCP server file via AST
  2. Find Tool() calls with description= keyword
  3. Analyze what's missing (reuse check_mcp_smell detect_smells)
  4. Generate suffix text for missing elements
  5. Rewrite the source file with augmented descriptions

Usage:
    python scripts/fix_mcp_smell.py                    # Preview changes
    python scripts/fix_mcp_smell.py --apply             # Apply changes
    python scripts/fix_mcp_smell.py --server sympatheia # Single server
    python scripts/fix_mcp_smell.py --dry-run --json    # JSON preview
"""

import ast
import json
import re
import sys
import textwrap
from pathlib import Path
from dataclasses import dataclass, field

# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
MCP_DIR = PROJECT_ROOT / "mekhane" / "mcp"
HERMENEUS_MCP = PROJECT_ROOT / "hermeneus" / "src" / "mcp_server.py"


# =============================================================================
# AST Analysis
# =============================================================================

@dataclass
class ToolInfo:
    name: str
    description: str
    input_schema: dict
    desc_node: ast.expr  # AST node for description value
    lineno: int
    end_lineno: int
    missing: list[str] = field(default_factory=list)


def discover_mcp_servers() -> list[tuple[str, Path]]:
    """Find all active MCP server Python files."""
    servers = []
    for f in sorted(MCP_DIR.glob("*_mcp_server.py")):
        name = f.stem.replace("_mcp_server", "")
        servers.append((name, f))
    if HERMENEUS_MCP.exists():
        servers.append(("hermeneus", HERMENEUS_MCP))
    return servers


def extract_tools_deep(filepath: Path) -> list[ToolInfo]:
    """Extract Tool() definitions with full schema info."""
    try:
        source = filepath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"  [WARN] Cannot parse {filepath.name}: {e}", file=sys.stderr)
        return []

    tools = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        func_name = getattr(func, 'id', None) or getattr(func, 'attr', None)
        if func_name != "Tool":
            continue

        name_val = None
        desc_val = None
        desc_node = None
        schema = {}

        for kw in node.keywords:
            if kw.arg == "name":
                name_val = _extract_string(kw.value)
            elif kw.arg == "description":
                desc_val = _extract_string(kw.value)
                desc_node = kw.value
            elif kw.arg == "inputSchema":
                schema = _extract_schema(kw.value)

        if name_val and desc_val and desc_node:
            # Skip description=variable patterns (e.g. description=desc)
            # Those have no string literal to patch
            if not isinstance(desc_node, (ast.Constant, ast.BinOp, ast.JoinedStr)):
                continue
            missing = _detect_missing(desc_val)
            tools.append(ToolInfo(
                name=name_val,
                description=desc_val,
                input_schema=schema,
                desc_node=desc_node,
                lineno=node.lineno,
                end_lineno=node.end_lineno,
                missing=missing,
            ))
    return tools


def _extract_string(node) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _extract_string(node.left)
        right = _extract_string(node.right)
        if left is not None and right is not None:
            return left + right
    elif isinstance(node, ast.JoinedStr):
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant):
                parts.append(str(val.value))
            else:
                parts.append("{...}")
        return "".join(parts)
    return None


def _extract_schema(node) -> dict:
    """Best-effort extraction of inputSchema dict from AST."""
    try:
        # Try ast.literal_eval on the source representation
        source = ast.get_source_segment(
            open(node._source_file).read() if hasattr(node, '_source_file') else "",
            node
        )
        if source:
            return json.loads(source.replace("'", '"'))
    except Exception:
        pass

    # Fallback: walk the Dict node
    if isinstance(node, ast.Dict):
        result = {}
        for k, v in zip(node.keys, node.values):
            key = _extract_string(k) if k else None
            if key == "properties" and isinstance(v, ast.Dict):
                props = {}
                for pk, pv in zip(v.keys, v.values):
                    pname = _extract_string(pk)
                    if pname:
                        prop_info = _extract_prop_info(pv)
                        props[pname] = prop_info
                result["properties"] = props
            elif key == "required" and isinstance(v, ast.List):
                result["required"] = [_extract_string(e) for e in v.elts if _extract_string(e)]
        return result
    return {}


def _extract_prop_info(node) -> dict:
    """Extract property info from a Dict AST node."""
    info = {}
    if isinstance(node, ast.Dict):
        for k, v in zip(node.keys, node.values):
            key = _extract_string(k)
            if key == "type":
                info["type"] = _extract_string(v) or "string"
            elif key == "description":
                info["description"] = _extract_string(v) or ""
            elif key == "default":
                if isinstance(v, ast.Constant):
                    info["default"] = v.value
            elif key == "enum" and isinstance(v, ast.List):
                info["enum"] = [_extract_string(e) for e in v.elts]
    return info


def _detect_missing(desc: str) -> list[str]:
    """Detect which elements are missing from description."""
    missing = []
    desc_lower = desc.lower()
    if not re.search(r"returns?[\s:.]", desc_lower):
        missing.append("missing_return")
    if "example" not in desc_lower and "e.g." not in desc_lower and "例" not in desc:
        missing.append("missing_example")
    if not re.search(r"(error|fail|exception|raise|invalid)s?[\s:.,]", desc_lower):
        missing.append("missing_error")
    return missing


# =============================================================================
# Auto-Generation
# =============================================================================

def generate_return_text(tool: ToolInfo) -> str:
    """Generate Returns: text based on tool name patterns."""
    name = tool.name.lower()

    # Common patterns
    if name in ("ping",):
        return "Returns: 'pong' string."
    if "search" in name:
        return "Returns: list of matching results with relevance scores."
    if "list" in name:
        return "Returns: array of available items."
    if "stats" in name or "status" in name or "info" in name:
        return "Returns: JSON object with current statistics/status."
    if "get" in name or "details" in name:
        return "Returns: JSON object with requested details."
    if "create" in name or "start" in name:
        return "Returns: created resource ID or session info."
    if "send" in name or "ask" in name:
        return "Returns: response text from the operation."
    if "close" in name or "dismiss" in name:
        return "Returns: confirmation of closure."
    if "check" in name or "scan" in name or "validate" in name:
        return "Returns: list of issues found, empty if clean."
    if "run" in name or "execute" in name:
        return "Returns: execution result with status and output."
    if "compile" in name:
        return "Returns: compiled output string."
    if "parse" in name:
        return "Returns: parsed AST structure."
    if "export" in name:
        return "Returns: exported data or file path."
    if "recommend" in name:
        return "Returns: recommendation with reasoning."
    if "generate" in name:
        return "Returns: generated content."
    if "track" in name or "update" in name:
        return "Returns: updated tracking state."
    if "log" in name or "record" in name:
        return "Returns: recorded entry with session summary."
    if "benchmark" in name or "metrics" in name:
        return "Returns: quality scores and comparison data."
    if "backlinks" in name:
        return "Returns: list of items that reference the given one."
    if "graph" in name:
        return "Returns: graph statistics (nodes, edges, most linked)."
    if "quota" in name:
        return "Returns: remaining quota per model."
    if "models" in name:
        return "Returns: list of available models with quota."
    if "plan" in name:
        return "Returns: structured execution plan with sub-tasks."
    if "batch" in name:
        return "Returns: array of results, one per task."
    if "citations" in name:
        return "Returns: list of citing papers with metadata."
    if "sources" in name:
        return "Returns: recommended sources for the query type."
    if "escalate" in name:
        return "Returns: escalation candidates with severity analysis."
    if "feedback" in name:
        return "Returns: adjusted thresholds based on recent health data."
    if "digest" in name:
        return "Returns: compressed weekly summary of all state files."
    if "notifications" in name:
        return "Returns: notification list or action confirmation."
    if "dashboard" in name:
        return "Returns: aggregated statistics by pattern, severity, and trend."
    if "dendron" in name:
        return "Returns: list of PROOF verification issues found."
    if "dispatch" in name:
        return "Returns: {'success': bool, 'tree': str, 'workflows': list, 'plan_template': str}"
    if "attractor" in name:
        return "Returns: recommended theorem and workflow with similarity score."
    if "wbc" in name:
        return "Returns: threat assessment with score and severity level."
    if "peira" in name or "health" in name:
        return "Returns: service health summary with status per component."
    if "violation" in name:
        return "Returns: violation record with session statistics."
    if "policy" in name:
        return "Returns: convergent/divergent classification with confidence."
    if "expand" in name:
        return "Returns: expanded natural language prompt."
    if "mark" in name or "processed" in name:
        return "Returns: list of moved files."
    if "candidates" in name:
        return "Returns: ranked list of candidates."
    if "topics" in name:
        return "Returns: list of available topics."
    if "incoming" in name:
        return "Returns: list of pending files."
    if "audit" in name:
        return "Returns: audit log entries with verification results."

    # Fallback
    return "Returns: operation result."


def generate_example_text(tool: ToolInfo) -> str:
    """Generate Example: text from inputSchema."""
    props = tool.input_schema.get("properties", {})
    required = tool.input_schema.get("required", [])

    if not props:
        return f"Example: {tool.name}()"

    # Build example with required params
    parts = []
    for pname in required:
        pinfo = props.get(pname, {})
        ptype = pinfo.get("type", "string")
        if ptype == "string":
            example_val = pinfo.get("enum", [None])[0] if pinfo.get("enum") else f"'...'"
            parts.append(f'{pname}={example_val}')
        elif ptype == "integer":
            parts.append(f'{pname}=10')
        elif ptype == "boolean":
            parts.append(f'{pname}=true')
        elif ptype == "array":
            parts.append(f'{pname}=[...]')

    if not parts:
        # Use first property as example
        for pname, pinfo in list(props.items())[:1]:
            parts.append(f"{pname}='...'")

    return f"Example: {tool.name}({', '.join(parts)})"


def generate_error_text(tool: ToolInfo) -> str:
    """Generate error condition text."""
    required = tool.input_schema.get("required", [])
    if required:
        return f"Errors if required params ({', '.join(required)}) are missing or invalid."
    return "Errors on invalid input or internal failure."


def build_suffix(tool: ToolInfo) -> str:
    """Build the suffix to append to an existing description."""
    parts = []
    if "missing_return" in tool.missing:
        parts.append(generate_return_text(tool))
    if "missing_example" in tool.missing:
        parts.append(generate_example_text(tool))
    if "missing_error" in tool.missing:
        parts.append(generate_error_text(tool))
    return " ".join(parts)


# =============================================================================
# Source Rewriting
# =============================================================================

def apply_fixes(filepath: Path, tools: list[ToolInfo], dry_run: bool = True) -> list[dict]:
    """Apply description fixes to a source file.

    Handles both single-line (ast.Constant) and multi-line concatenated
    strings (ast.BinOp chain from parenthesized string literals).
    Uses AST end_col_offset for precise insertion point.
    """
    source = filepath.read_text(encoding="utf-8")
    lines = source.split("\n")
    changes = []

    # Process tools in reverse order (bottom-up) so line numbers stay valid
    fixable = [t for t in tools if t.missing]
    fixable.sort(key=lambda t: t.lineno, reverse=True)

    for tool in fixable:
        suffix = build_suffix(tool)
        if not suffix:
            continue

        desc_node = tool.desc_node
        change = {
            "tool": tool.name,
            "line": tool.lineno,
            "missing": tool.missing,
            "suffix": suffix,
            "applied": False,
        }

        if not dry_run:
            applied = _insert_suffix(lines, desc_node, suffix)
            change["applied"] = applied

        changes.append(change)

    if not dry_run and any(c["applied"] for c in changes):
        filepath.write_text("\n".join(lines), encoding="utf-8")

    return changes


def _insert_suffix(lines: list[str], desc_node: ast.expr, suffix: str) -> bool:
    """Insert suffix text before the closing quote of a description node.

    Strategy: find the rightmost string Constant in the AST node,
    use its end_lineno/end_col_offset to locate the closing quote precisely.
    NOTE: AST col_offset in Python 3 is in UTF-8 bytes, not characters!
    """
    target_node = desc_node

    # For BinOp chains (concatenated strings), find the rightmost Constant
    if isinstance(desc_node, ast.BinOp):
        target_node = _find_rightmost_constant(desc_node)

    if not target_node or not isinstance(target_node, ast.Constant):
        return False

    # Use AST's end position (1-indexed line, 0-indexed col)
    end_line = getattr(target_node, 'end_lineno', None)
    end_col = getattr(target_node, 'end_col_offset', None)

    if end_line is None or end_col is None:
        # Fallback: scan for closing quote on the node's line
        return _insert_suffix_fallback(lines, target_node, suffix)

    line_idx = end_line - 1
    line = lines[line_idx]

    # Convert line to bytes since end_col_offset is in UTF-8 bytes
    line_bytes = line.encode("utf-8")

    # end_col_offset points AFTER the closing quote.
    # The closing quote is at end_col - 1.
    quote_pos = end_col - 1
    if quote_pos < 0 or quote_pos >= len(line_bytes):
        return _insert_suffix_fallback(lines, target_node, suffix)

    quote_char_byte = line_bytes[quote_pos:quote_pos+1]
    if quote_char_byte not in (b'"', b"'"):
        return _insert_suffix_fallback(lines, target_node, suffix)

    # Insert suffix before the closing quote
    new_suffix_bytes = f" {suffix}".encode("utf-8")
    new_line_bytes = line_bytes[:quote_pos] + new_suffix_bytes + line_bytes[quote_pos:]
    lines[line_idx] = new_line_bytes.decode("utf-8")
    return True



def _insert_suffix_fallback(lines: list[str], node: ast.Constant, suffix: str) -> bool:
    """Fallback: scan the line for the last quote character."""
    line_idx = (getattr(node, 'end_lineno', None) or node.lineno) - 1
    line = lines[line_idx]

    for quote_char in ['",', "',", '")', "')"]:
        if quote_char in line:
            pos = line.rindex(quote_char)
            lines[line_idx] = line[:pos] + f" {suffix}" + line[pos:]
            return True
    return False


def _find_rightmost_constant(node):
    """Find the rightmost Constant node in a BinOp chain."""
    if isinstance(node, ast.Constant):
        return node
    if isinstance(node, ast.BinOp):
        return _find_rightmost_constant(node.right)
    return None


# =============================================================================
# Public API (for night_review.py integration)
# =============================================================================

def run_fix(dry_run: bool = True, server: str | None = None) -> dict:
    """Run the auto-fixer programmatically.

    Returns:
        {
            "total_tools": int,
            "total_fixed": int,
            "changes": {server_name: [change_dict, ...]},
        }
    """
    all_changes = {}
    total_fixed = 0
    total_tools = 0

    for server_name, filepath in discover_mcp_servers():
        if server and server_name != server:
            continue

        tools = extract_tools_deep(filepath)
        total_tools += len(tools)

        fixable = [t for t in tools if t.missing]
        if not fixable:
            continue

        changes = apply_fixes(filepath, tools, dry_run=dry_run)
        all_changes[server_name] = changes
        total_fixed += len([c for c in changes if c.get("applied") or dry_run])

    return {
        "total_tools": total_tools,
        "total_fixed": total_fixed,
        "changes": all_changes,
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MCP Tool Description Auto-Fixer")
    parser.add_argument("--apply", action="store_true", help="Apply fixes (default: preview)")
    parser.add_argument("--server", type=str, help="Fix single server")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    dry_run = not args.apply
    all_changes = {}
    total_fixed = 0
    total_tools = 0

    for server_name, filepath in discover_mcp_servers():
        if args.server and server_name != args.server:
            continue

        tools = extract_tools_deep(filepath)
        total_tools += len(tools)

        fixable = [t for t in tools if t.missing]
        if not fixable:
            continue

        changes = apply_fixes(filepath, tools, dry_run=dry_run)
        all_changes[server_name] = changes
        total_fixed += len([c for c in changes if c.get("applied") or dry_run])

    if args.json:
        print(json.dumps(all_changes, ensure_ascii=False, indent=2))
    else:
        mode = "PREVIEW" if dry_run else "APPLIED"
        print(f"🔧 MCP Description Auto-Fixer v1.0 [{mode}]")
        print(f"   Tools analyzed: {total_tools}")
        print(f"   Fixes {'proposed' if dry_run else 'applied'}: {total_fixed}")
        print()

        for server, changes in all_changes.items():
            print(f"--- {server} ---")
            for c in changes:
                status = "✅" if c.get("applied") else "📋"
                print(f"  {status} [{c['tool']}] +{', '.join(c['missing'])}")
                print(f"     → {c['suffix'][:120]}...")
            print()

        if dry_run:
            print("💡 Run with --apply to write changes to source files.")


if __name__ == "__main__":
    main()
