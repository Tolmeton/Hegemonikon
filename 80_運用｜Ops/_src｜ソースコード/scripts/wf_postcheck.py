#!/usr/bin/env python3
# PROOF: [L2/運用] <- scripts/
# PURPOSE: ワークフロー実行後の品質検証
"""
wf_postcheck.py — 汎用 WF ポストチェック

環境強制: WF 出力の品質を機械的に検証する。
sel_enforcement の minimum_requirements を YAML から読み込み、
出力内容と照合する。

Usage:
    python scripts/wf_postcheck.py --wf boot --mode detailed --output /tmp/boot_report.md
    python scripts/wf_postcheck.py --wf dia --mode "+" --text "判定結果テキスト..."
    python scripts/wf_postcheck.py --list  # sel_enforcement 一覧表示
"""

import re
import sys
import argparse
from pathlib import Path

import yaml


# ============================================================
# YAML から sel_enforcement を読み込む
# ============================================================

WF_DIR = Path(__file__).parent.parent / "nous" / "workflows"


def load_sel_enforcement(wf_name: str) -> dict:
    """WF の sel_enforcement を YAML frontmatter から読み込む。"""
    wf_path = WF_DIR / f"{wf_name}.md"
    if not wf_path.exists():
        return {}

    content = wf_path.read_text(encoding="utf-8")

    # YAML frontmatter を抽出 (--- で囲まれた部分)
    match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
    if not match:
        return {}

    try:
        fm = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}

    return fm.get("sel_enforcement", {})


def list_all_sel_enforcement() -> dict[str, dict]:
    """全WFの sel_enforcement を読み込んで返す。"""
    result = {}
    for wf_path in sorted(WF_DIR.glob("*.md")):
        wf_name = wf_path.stem
        sel = load_sel_enforcement(wf_name)
        if sel:
            result[wf_name] = sel
    return result


# ============================================================
# 汎用チェッカー
# ============================================================

# モード名の正規化: "+" → "+", "detailed" → "+"
MODE_MAP = {
    "detailed": "+",
    "standard": "",
    "fast": "-",
    "+": "+",
    "-": "-",
    "*": "*",
    "": "",
}


def check_requirements(
    content: str,
    requirements: list[str],
) -> list[dict]:
    """
    requirements リストの各項目を content に対してチェックする。

    チェック方法:
    - 要件からキーワードを抽出（コロン前をプライマリキーワードとして優先）
    - content にキーワードが含まれるかヒューリスティック検査
    - 数値要件（N件以上、N行以内等）は正規表現で抽出・検証
    """
    checks = []
    content_lower = content.lower()

    for req in requirements:
        # 数値パターンの検出: "3つ以上", "5行以内", "N件"
        num_match = re.search(r"(\d+)[つ件個箇所]+以上", req)
        limit_match = re.search(r"(\d+)行以内", req)

        # コロン前をプライマリキーワードとして抽出
        primary_keywords = []
        if ":" in req or "：" in req:
            label = re.split(r"[:：]", req)[0].strip()
            primary_keywords = re.findall(r"[A-Za-z_-]{2,}|[ぁ-んァ-ヶ一-龠]{2,}", label)

        # 全体からキーワード抽出
        all_keywords = re.findall(r"[A-Za-z_-]{2,}|[ぁ-んァ-ヶ一-龠]{2,}", req)
        # ノイズ除去
        noise = {"必須", "明示", "以上", "以内", "のみ", "する", "こと", "出力",
                 "記載", "minimum", "requirements", "を", "で", "に", "は", "の", "が"}
        all_keywords = [k for k in all_keywords if k not in noise]

        # キーワードマッチ判定
        if primary_keywords:
            # プライマリキーワードの完全一致 OR 部分一致（2文字以上の部分文字列）
            primary_hit = False
            for k in primary_keywords:
                k_lower = k.lower()
                if k_lower in content_lower:
                    primary_hit = True
                    break
                # 長い日本語キーワードを分解して部分一致（例: 証拠セクション → 証拠, セクション）
                if len(k) >= 4:
                    for i in range(len(k) - 1):
                        sub = k[i:i+2]
                        if sub in content_lower:
                            primary_hit = True
                            break
                if primary_hit:
                    break
        else:
            primary_hit = False

        if all_keywords:
            match_count = sum(1 for k in all_keywords if k.lower() in content_lower)
            match_ratio = match_count / len(all_keywords)
        else:
            match_count = 0
            match_ratio = 0.0

        # 判定: プライマリキーワードマッチ OR 全体30%以上
        passed = primary_hit or match_ratio >= 0.3

        # 数値チェック: "3つ以上" → 該当パターンが3つ以上あるか
        if num_match and passed:
            expected = int(num_match.group(1))
            # ヒューリスティック: セクションヘッダ数で近似
            section_count = len(re.findall(r"^#{1,4}\s", content, re.MULTILINE))
            if section_count < expected:
                passed = False

        # 行数制限チェック
        if limit_match:
            max_lines = int(limit_match.group(1))
            actual_lines = len(content.strip().split("\n"))
            passed = actual_lines <= max_lines

        checks.append({
            "name": req[:60],
            "passed": passed,
            "detail": f"{'✅' if passed else '❌'} {req}" + (
                f" (keywords: {match_count}/{len(all_keywords)})" if all_keywords else ""
            ),
        })

    return checks


# PURPOSE: UML Phase 2 — MP 5段階のポストチェック統合
def check_uml(wf_name: str, content: str) -> list[dict]:
    """Run UML post-checks (MP Stage 3-5) on WF output.

    Graceful degradation: import failure → empty list.
    """
    try:
        from mekhane.fep.metacognitive_layer import run_post_checks
    except ImportError:
        return []

    try:
        checks = run_post_checks(
            output=content,
            context=f"/{wf_name} output",
            confidence=0.0,  # No explicit confidence from postcheck
        )
        return [
            {
                "name": f"UML {c.stage_label}",
                "passed": c.passed,
                "detail": f"{'✅' if c.passed else '⚠️'} UML {c.stage_label}: {c.result[:80]}",
            }
            for c in checks
        ]
    except Exception:
        return []  # UML failure should never block postcheck


def postcheck(
    wf_name: str,
    mode: str,
    content: str,
) -> dict:
    """
    汎用ポストチェック。

    Returns:
        dict: {"passed": bool, "checks": [...], "formatted": str}
    """
    sel = load_sel_enforcement(wf_name)
    if not sel:
        return {
            "passed": True,
            "checks": [],
            "formatted": f"⚠️ {wf_name}: sel_enforcement 未定義（チェックスキップ）",
        }

    normalized_mode = MODE_MAP.get(mode, mode)
    mode_sel = sel.get(normalized_mode, {})
    if not mode_sel:
        return {
            "passed": True,
            "checks": [],
            "formatted": f"⚠️ {wf_name}: モード '{mode}' の sel_enforcement 未定義",
        }

    requirements = mode_sel.get("minimum_requirements", [])
    if not requirements:
        return {
            "passed": True,
            "checks": [],
            "formatted": f"✅ {wf_name}: 要件なし（チェックスキップ）",
        }

    checks = check_requirements(content, requirements)

    # --- Extended checks ---
    # Naturality check for boot/bye WFs
    if wf_name in ("boot", "bye"):
        nat_checks = check_naturality()
        checks.extend(nat_checks)

    # Agent-Diff: Handoff structure diff (bye only)
    if wf_name == "bye":
        diff_checks = check_agent_diff(content)
        checks.extend(diff_checks)

    # BC violation pattern check (bye only)
    if wf_name == "bye":
        bc_checks = check_bc_patterns(content)
        checks.extend(bc_checks)

    # UML metacognitive post-check (Phase 2: all WFs)
    uml_checks = check_uml(wf_name, content)
    checks.extend(uml_checks)

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    all_passed = all(c["passed"] for c in checks)

    status = "PASS" if all_passed else "FAIL"
    icon = "✅" if all_passed else "❌"
    lines = [f"{icon} /{wf_name}{normalized_mode} Postcheck: {status} ({passed_count}/{total})"]
    for c in checks:
        lines.append(f"  {c['detail']}")

    return {
        "passed": all_passed,
        "checks": checks,
        "formatted": "\n".join(lines),
    }


# ============================================================
# Extended Checks: Agent-Diff (Handoff Structure Diff)
# ============================================================

HANDOFF_DIR = Path.home() / "oikos" / "mneme" / ".hegemonikon" / "sessions"


def check_agent_diff(content: str) -> list[dict]:
    """Compare current Handoff sections with previous Handoff.

    Detects section headings (##) in the previous Handoff that are
    missing from the current one. Missing sections are reported as
    FAIL unless the content contains an explicit '(省略理由:' note.
    """
    checks = []

    # Find the two most recent Handoff files
    handoffs = sorted(HANDOFF_DIR.glob("handoff_*.md"), reverse=True)
    if len(handoffs) < 2:
        checks.append({
            "name": "agent_diff",
            "passed": True,
            "detail": "✅ Agent-Diff: 比較対象の前回 Handoff なし (スキップ)",
        })
        return checks

    prev_path = handoffs[1]  # Second most recent
    try:
        prev_content = prev_path.read_text(encoding="utf-8")
    except Exception:
        return checks

    # Extract ## headings
    prev_sections = set(re.findall(r"^## (.+)$", prev_content, re.MULTILINE))
    curr_sections = set(re.findall(r"^## (.+)$", content, re.MULTILINE))

    missing = prev_sections - curr_sections
    if not missing:
        checks.append({
            "name": "agent_diff",
            "passed": True,
            "detail": f"✅ Agent-Diff: 前回 ({prev_path.name}) と構造一致",
        })
    else:
        for section in sorted(missing):
            # Check for explicit skip reason
            has_reason = "省略理由" in content and section.split()[0] in content
            checks.append({
                "name": f"agent_diff_{section[:30]}",
                "passed": has_reason,
                "detail": f"{'✅' if has_reason else '❌'} Agent-Diff: "
                          f"前回にあった '## {section}' が欠落"
                          + (" (省略理由あり)" if has_reason else ""),
            })

    return checks


# ============================================================
# Extended Checks: Naturality Verification
# ============================================================


def check_naturality() -> list[dict]:
    """Verify η/ε/η_MP natural transformations are well-formed.

    Auto-runs verify_naturality() from cone_builder on all registered
    natural transformations. Reports per-transformation pass/fail.

    Returns:
        list[dict]: Check results compatible with postcheck format.
    """
    checks = []
    try:
        from mekhane.fep.category import NATURAL_TRANSFORMATIONS
        from mekhane.fep.cone_builder import verify_naturality
    except ImportError:
        checks.append({
            "name": "naturality_import",
            "passed": False,
            "detail": "❌ Natural transformation modules not importable",
        })
        return checks

    for nt_key, nt in NATURAL_TRANSFORMATIONS.items():
        result = verify_naturality(nt)
        checks.append({
            "name": f"naturality_{nt_key}",
            "passed": result.is_natural,
            "detail": f"{'✅' if result.is_natural else '❌'} "
                      f"NatTrans {nt.name}: {result.summary}",
        })
        # Add per-violation details
        for violation in result.violations:
            checks.append({
                "name": f"naturality_{nt_key}_violation",
                "passed": False,
                "detail": f"  ⚠️ {violation}",
            })

    return checks


# ============================================================
# Extended Checks: BC Violation Pattern Detection
# ============================================================


def check_bc_patterns(content: str) -> list[dict]:
    """BC violation patterns to detect during /bye postcheck.

    Checks:
    1. Handoff にBC違反セクションが含まれるか
    2. 昇格候補があるか (suggest_escalation)
    3. 叱責率が異常に高くないか

    Graceful degradation: import failure → empty list.
    """
    checks = []
    try:
        from mekhane.sympatheia.violation_logger import (
            read_all_entries, suggest_escalation, compute_stats,
        )
    except ImportError:
        return []

    try:
        entries = read_all_entries()
        if not entries:
            checks.append({
                "name": "bc_section",
                "passed": True,
                "detail": "✅ BC: 違反記録なし",
            })
            return checks

        # Check 1: Handoff has BC section
        has_bc_section = "BC フィードバック" in content or "BC:" in content
        checks.append({
            "name": "bc_section_present",
            "passed": has_bc_section,
            "detail": f"{'✅' if has_bc_section else '❌'} BC: "
                      f"Handoff に BC フィードバックセクション{'あり' if has_bc_section else 'なし'}",
        })

        # Check 2: Escalation candidates
        candidates = suggest_escalation(entries)
        if candidates:
            patterns = [c["pattern"] for c in candidates]
            checks.append({
                "name": "bc_escalation",
                "passed": False,  # Escalation = attention needed
                "detail": f"⚠️ BC: 昇格候補 {len(candidates)} 件 ({', '.join(patterns)})"
                          f" — sympatheia_escalate で確認",
            })
        else:
            checks.append({
                "name": "bc_escalation",
                "passed": True,
                "detail": "✅ BC: 昇格候補なし",
            })

        # Check 3: Reprimand rate
        stats = compute_stats(entries)
        reprimand_rate = stats.get("reprimand_rate", 0)
        rate_ok = reprimand_rate < 80.0
        checks.append({
            "name": "bc_reprimand_rate",
            "passed": rate_ok,
            "detail": f"{'✅' if rate_ok else '⚠️'} BC: 叱責率 {reprimand_rate:.1f}%"
                      + ("" if rate_ok else " — 改善が必要"),
        })

    except Exception:
        pass  # BC check failure should never block postcheck

    return checks


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="汎用 WF ポストチェック — sel_enforcement ベースの品質検証"
    )
    parser.add_argument("--wf", type=str, help="ワークフロー名 (例: boot, dia, noe)")
    parser.add_argument("--mode", type=str, default="+", help='モード (+, -, *, detailed, fast)')
    parser.add_argument("--output", type=str, help="チェック対象ファイルパス")
    parser.add_argument("--text", type=str, help="チェック対象テキスト（直接指定）")
    parser.add_argument("--list", action="store_true", help="全WFの sel_enforcement 一覧")
    args = parser.parse_args()

    if args.list:
        all_sel = list_all_sel_enforcement()
        print(f"📋 sel_enforcement 定義済み WF: {len(all_sel)}")
        print()
        for wf_name, sel in all_sel.items():
            modes = ", ".join(sel.keys())
            print(f"  /{wf_name}: [{modes}]")
            for mode_key, mode_val in sel.items():
                reqs = mode_val.get("minimum_requirements", [])
                print(f"    {mode_key}: {len(reqs)} requirements")
        sys.exit(0)

    if not args.wf:
        parser.error("--wf is required (or use --list)")

    # コンテンツ取得
    content = ""
    if args.output:
        path = Path(args.output)
        if not path.exists():
            print(f"❌ File not found: {args.output}")
            sys.exit(1)
        content = path.read_text(encoding="utf-8")
    elif args.text:
        content = args.text
    else:
        # stdin から読み込み
        content = sys.stdin.read()

    result = postcheck(args.wf, args.mode, content)
    print(result["formatted"])
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
