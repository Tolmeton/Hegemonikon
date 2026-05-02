#!/usr/bin/env python3
# PROOF: [L2/Basanos] <- 80_運用｜Ops MCP Security Scanner v3
"""
MCP Security Scanner v3

Layer 1: Description Quality (既存 check_mcp_smell.py)
Layer 2: Security Analysis (本スクリプト)
  A. Prompt Injection Detection
  B. Tool Poisoning (Description Drift)
  C. Toxic Flow Analysis

Usage:
    python scripts/check_mcp_security.py
    python scripts/check_mcp_security.py --json
    python scripts/check_mcp_security.py --baseline
    python scripts/check_mcp_security.py --server ochema

Returns exit code 1 if any security issue is found.
"""

import hashlib
import json
import re
import sys
import unicodedata
import yaml
from dataclasses import asdict, dataclass, field
from pathlib import Path

# 既存 smell linter を import
sys.path.insert(0, str(Path(__file__).parent))
import check_mcp_smell
from check_mcp_smell import (
    extract_tools_from_file,
    run_smell_check,
)

# HGK リポジトリルートを推定し、check_mcp_smell のパスを修正
# scripts/ は 80_運用｜Ops/_src｜ソースコード/scripts/ にあるが、
# MCP サーバは 20_機構｜Mekhane/_src｜ソースコード/mekhane/mcp/ にある
_HGK_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_MEKHANE_SRC = _HGK_ROOT / "20_機構｜Mekhane" / "_src｜ソースコード"
POLICY_PATH = _MEKHANE_SRC / "mekhane" / "mcp" / "gateway_policy.yaml"

check_mcp_smell.PROJECT_ROOT = _MEKHANE_SRC
check_mcp_smell.MCP_DIR = _MEKHANE_SRC / "mekhane" / "mcp"
check_mcp_smell.HERMENEUS_MCP = _MEKHANE_SRC / "hermeneus" / "src" / "mcp_server.py"
check_mcp_smell.CONFIG_PATH = _HGK_ROOT / ".gemini" / "antigravity" / "mcp_config.json"

from check_mcp_smell import discover_mcp_servers


# =============================================================================
# Configuration
# =============================================================================

PROJECT_ROOT = _MEKHANE_SRC
BASELINE_PATH = Path(__file__).parent / ".mcp_security_baseline.json"

INTERNAL_SERVERS = {
    "sympatheia", "hermeneus", "periskope", "ochema",
    "phantazein", "digestor", "gnosis", "sophia", "typos", "sekisho", "jules",
}


# =============================================================================
# Data Structures
# =============================================================================


@dataclass
class SecurityIssue:
    """セキュリティ問題1件。"""

    category: str   # prompt_injection | tool_poisoning | toxic_flow
    severity: str   # critical | high | medium | low
    tool_name: str
    server_name: str
    message: str
    detail: str = ""


@dataclass
class SecurityReport:
    """サーバ単位のセキュリティレポート。"""

    server_name: str
    tool_count: int = 0
    issues: list[SecurityIssue] = field(default_factory=list)
    baseline_status: str = ""


# =============================================================================
# Category A: Prompt Injection Detection
# =============================================================================

# (regex, severity, label)
_INJECTION_PATTERNS: list[tuple[str, str, str]] = [
    # 指示上書き系
    (r"ignore\s+(all\s+)?previous", "critical", "指示上書き: ignore previous"),
    (r"disregard\s+(all|any|the)", "critical", "指示上書き: disregard"),
    (r"forget\s+(all|everything|previous)", "critical", "指示上書き: forget all"),
    (r"override\s+(all|any|the|previous)", "critical", "指示上書き: override"),
    (r"new\s+instructions?\s*:", "critical", "指示上書き: new instructions"),
    # ロール改変系
    (r"you\s+are\s+now\s+", "high", "ロール改変: you are now"),
    (r"act\s+as\s+(a|an|if)\s+", "high", "ロール改変: act as"),
    (r"pretend\s+(to\s+be|you)", "high", "ロール改変: pretend"),
    (r"from\s+now\s+on", "high", "ロール改変: from now on"),
    # メタタグ系
    (r"<system>", "critical", "メタタグ: <system>"),
    (r"\[INST\]", "critical", "メタタグ: [INST]"),
    (r"<<SYS>>", "critical", "メタタグ: <<SYS>>"),
    # データ窃取系
    (r"(send|post|upload|exfiltrate)\s+(to|it|data|this)", "high", "データ窃取指示"),
    (r"(curl|wget|fetch)\s+https?://", "critical", "外部通信コマンド"),
]

# Unicode 制御文字カテゴリ
_DANGEROUS_UNICODE_CATS = {"Cf", "Co", "Cn"}  # Format, Private Use, Unassigned


def detect_prompt_injection(
    desc: str, tool_name: str, server_name: str,
) -> list[SecurityIssue]:
    """Description 内の Prompt Injection パターンを検出する。"""
    issues: list[SecurityIssue] = []
    desc_lower = desc.lower()

    # Pattern matching
    for pattern, severity, label in _INJECTION_PATTERNS:
        if re.search(pattern, desc_lower):
            issues.append(SecurityIssue(
                category="prompt_injection",
                severity=severity,
                tool_name=tool_name,
                server_name=server_name,
                message=label,
                detail=f"Pattern: {pattern}",
            ))

    # Unicode 制御文字チェック
    dangerous_chars = []
    for i, ch in enumerate(desc):
        cat = unicodedata.category(ch)
        if cat in _DANGEROUS_UNICODE_CATS and ch not in ("\u200b",):
            # zero-width space 以外の制御文字
            dangerous_chars.append((i, ch, cat, unicodedata.name(ch, "UNKNOWN")))

    if dangerous_chars:
        detail = "; ".join(f"pos={pos} U+{ord(c):04X} ({name})" for pos, c, _, name in dangerous_chars[:5])
        issues.append(SecurityIssue(
            category="prompt_injection",
            severity="high",
            tool_name=tool_name,
            server_name=server_name,
            message=f"Unicode 制御文字 {len(dangerous_chars)} 個検出",
            detail=detail,
        ))

    # 異常長 description (> 1000 chars)
    if len(desc) > 1000:
        issues.append(SecurityIssue(
            category="prompt_injection",
            severity="medium",
            tool_name=tool_name,
            server_name=server_name,
            message=f"異常に長い description ({len(desc)} chars) — 隠しテキストの可能性",
        ))

    return issues


# =============================================================================
# Category B: Tool Poisoning (Description Drift)
# =============================================================================


def _hash_desc(desc: str) -> str:
    """Description の SHA256 hash を計算。"""
    return hashlib.sha256(desc.encode("utf-8")).hexdigest()[:16]


def _load_baseline() -> dict[str, dict[str, str]]:
    """Baseline ファイルを読み込む。server.tool -> hash のマップ。"""
    if not BASELINE_PATH.exists():
        return {}
    try:
        data = json.loads(BASELINE_PATH.read_text("utf-8"))
        return data.get("tools", {})
    except Exception:
        return {}


def _save_baseline(tool_hashes: dict[str, str]) -> None:
    """Baseline ファイルを保存。"""
    data = {
        "version": 1,
        "tools": tool_hashes,
    }
    BASELINE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), "utf-8")


def detect_tool_poisoning(
    desc: str,
    tool_name: str,
    server_name: str,
    baseline: dict[str, str],
) -> tuple[list[SecurityIssue], str]:
    """Description の hash drift を検出する。

    Returns:
        (issues, current_hash)
    """
    key = f"{server_name}.{tool_name}"
    current_hash = _hash_desc(desc)
    issues: list[SecurityIssue] = []

    if key in baseline:
        if baseline[key] != current_hash:
            issues.append(SecurityIssue(
                category="tool_poisoning",
                severity="high",
                tool_name=tool_name,
                server_name=server_name,
                message="Description drift 検出 — baseline から変更あり",
                detail=f"baseline={baseline[key]} current={current_hash}",
            ))

    return issues, current_hash


# =============================================================================
# Category C: Toxic Flow Analysis
# =============================================================================

# 危険フローパターン: (source pattern, sink pattern, severity, label)
_TOXIC_FLOW_PATTERNS: list[tuple[str, str, str, str]] = [
    # 外部漏洩: ファイル/コマンド実行 → 外部ネットワーク
    (r"\b(file|read_file|open|load|bash|cmd|sh)\b|ファイル|ローカル", 
     r"\b(http|url|api|request|curl|webhook|post|send)\b|通信|ネットワーク", 
     "high",
     "File→Network: ローカルデータのネットワーク漏洩リスク"),
    # 認証情報 → 出力
    (r"\b(token|key|secret|password|credential|auth|api_key)\b|トークン|パスワード|鍵|認証", 
     r"\b(log|print|send|display|output|http|url|api)\b|通信|送信|出力|表示", 
     "critical",
     "Credential→Output: 認証情報の漏洩リスク"),
]


def detect_toxic_flows(
    tools: list[tuple[str, str]],
    server_name: str,
    risk_tools: dict[str, set[str]],
) -> list[SecurityIssue]:
    """ツール群のデータフローパターンを解析する。

    同一サーバ内のツール組み合わせで危険フローを検出。
    """
    issues: list[SecurityIssue] = []

    tool_names = [name for name, _ in tools]
    tool_descs = {name: desc.lower() for name, desc in tools}

    for source_pat, sink_pat, severity, label in _TOXIC_FLOW_PATTERNS:
        sources = [n for n in tool_names if re.search(source_pat, n.lower()) or re.search(source_pat, tool_descs.get(n, ""))]
        sinks = [n for n in tool_names if re.search(sink_pat, n.lower()) or re.search(sink_pat, tool_descs.get(n, ""))]

        for src in sources:
            for snk in sinks:
                if src != snk:
                    issues.append(SecurityIssue(
                        category="toxic_flow",
                        severity=severity,
                        tool_name=f"{src} -> {snk}",
                        server_name=server_name,
                        message=label,
                        detail=f"Source: {src}, Sink: {snk}",
                    ))

    # 意味ベース検出: Low Risk (読取等) から High/Medium Risk (副作用・送信) へのフロー
    tool_names = [name for name, _ in tools]
    low_tools = [n for n in tool_names if n in risk_tools["low"]]
    high_med_tools = [n for n in tool_names if n in risk_tools["high"] or n in risk_tools["medium"]]

    if low_tools and high_med_tools:
        for src in low_tools:
            for snk in high_med_tools:
                if src != snk:
                    issues.append(SecurityIssue(
                        category="toxic_flow",
                        severity="medium",
                        tool_name=f"{src} -> {snk}",
                        server_name=server_name,
                        message="Read→Action: 読取専用ツールから副作用のあるツールへの連携 (Policy-based)",
                        detail=f"Source({src}) is Low Risk, Sink({snk}) is High/Medium Risk",
                    ))

    return issues


# =============================================================================
# Orchestrator
# =============================================================================


def _load_risk_tools() -> dict[str, set[str]]:
    """Policy ファイルからリスク別ツール分類を読み込む。"""
    try:
        data = yaml.safe_load(POLICY_PATH.read_text("utf-8"))
        qg = data.get("quality_gate", {})
        return {
            "high": set(qg.get("high_risk_tools", [])),
            "medium": set(qg.get("medium_risk_tools", [])),
            "low": set(qg.get("low_risk_tools", [])),
        }
    except Exception:
        return {"high": set(), "medium": set(), "low": set()}


def run_security_scan(
    target_server: str | None = None,
    update_baseline: bool = False,
) -> dict:
    """全カテゴリのセキュリティスキャンを実行する。"""

    reports: list[SecurityReport] = []
    baseline = _load_baseline()
    new_hashes: dict[str, str] = dict(baseline)  # baseline を継承
    risk_tools = _load_risk_tools()

    mcp_files = discover_mcp_servers()

    for server_name, filepath in mcp_files:
        if target_server and server_name != target_server:
            continue

        report = SecurityReport(server_name=server_name)
        tools = extract_tools_from_file(filepath)
        report.tool_count = len(tools)

        for tool_name, tool_desc in tools:
            # Category A: Prompt Injection
            pi_issues = detect_prompt_injection(tool_desc, tool_name, server_name)
            report.issues.extend(pi_issues)

            # Category B: Tool Poisoning
            tp_issues, current_hash = detect_tool_poisoning(
                tool_desc, tool_name, server_name, baseline,
            )
            report.issues.extend(tp_issues)
            new_hashes[f"{server_name}.{tool_name}"] = current_hash

        # Category C: Toxic Flow (サーバ単位)
        tf_issues = detect_toxic_flows(tools, server_name, risk_tools)
        # 内部サーバの Toxic Flow は設計意図 (Hub) であるため情報を維持しつつ Severity を緩和
        for issue in tf_issues:
            if server_name in INTERNAL_SERVERS:
                issue.severity = "low"
                issue.detail += " (Internal Server: 意図されたHub機能としてSeverity緩和)"
        report.issues.extend(tf_issues)

        # Baseline status
        server_keys = [k for k in baseline if k.startswith(f"{server_name}.")]
        if not server_keys:
            report.baseline_status = "new"
        elif any(
            i.category == "tool_poisoning" for i in report.issues
        ):
            report.baseline_status = "drifted"
        else:
            report.baseline_status = "unchanged"

        reports.append(report)

    # Baseline 更新
    if update_baseline:
        _save_baseline(new_hashes)

    # Layer 1: Smell check
    smell_result = run_smell_check(target_server=target_server)

    # Aggregate
    all_issues = []
    for r in reports:
        all_issues.extend(r.issues)

    critical_count = sum(1 for i in all_issues if i.severity == "critical")
    high_count = sum(1 for i in all_issues if i.severity == "high")

    return {
        "layer1_quality": {
            "average_smells_per_tool": smell_result["average_smells_per_tool"],
            "total_smells": smell_result["total_smells"],
        },
        "layer2_security": {
            "total_issues": len(all_issues),
            "critical": critical_count,
            "high": high_count,
            "medium": sum(1 for i in all_issues if i.severity == "medium"),
            "low": sum(1 for i in all_issues if i.severity == "low"),
        },
        "baseline_updated": update_baseline,
        "server_count": len(reports),
        "reports": [asdict(r) for r in reports],
        "verdict": "FAIL" if critical_count > 0 or high_count > 0 else "PASS",
    }


# =============================================================================
# CLI
# =============================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(description="MCP Security Scanner v3")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--server", type=str, help="Scan single server")
    parser.add_argument("--baseline", action="store_true", help="Update baseline hashes")
    args = parser.parse_args()

    result = run_security_scan(
        target_server=args.server,
        update_baseline=args.baseline,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["verdict"] == "PASS" else 1)

    # Human-readable output
    l1 = result["layer1_quality"]
    l2 = result["layer2_security"]

    print("=" * 60)
    print("🛡️  MCP Security Scanner v3")
    print("=" * 60)
    print(f"\n📊 Layer 1 — Quality: {l1['total_smells']} smells ({l1['average_smells_per_tool']:.2f}/tool)")
    print(f"🔒 Layer 2 — Security: {l2['total_issues']} issues "
          f"(🔴{l2['critical']} 🟠{l2['high']} 🟡{l2['medium']} ⚪{l2['low']})")

    if result["baseline_updated"]:
        print(f"\n📝 Baseline updated: {BASELINE_PATH}")

    print()

    for report in result["reports"]:
        name = report["server_name"]
        tc = report["tool_count"]
        issues = report["issues"]
        status = report["baseline_status"]

        status_icon = {"new": "🆕", "unchanged": "✅", "drifted": "⚠️"}.get(status, "❓")
        issue_count = len(issues)
        icon = "✅" if issue_count == 0 else "⚠️" if issue_count <= 2 else "🔴"

        print(f"{icon} {name} ({tc} tools) {status_icon}")

        for issue in issues:
            sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}[issue["severity"]]
            print(f"   {sev_icon} [{issue['category']}] {issue['message']}")
            if issue.get("detail"):
                print(f"      {issue['detail']}")

        if issues:
            print()

    print("=" * 60)
    verdict = result["verdict"]
    if verdict == "PASS":
        print("✅ PASS — No critical/high security issues")
    else:
        print("❌ FAIL — Critical or high security issues detected")
    print("=" * 60)

    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
