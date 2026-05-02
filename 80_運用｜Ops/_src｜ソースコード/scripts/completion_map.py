#!/usr/bin/env python3
# PROOF: [L2/ツール] <- scripts/
# PURPOSE: 32実体体系 (v4.1) の実装状況を自動スキャンし、完成度マップを生成する
"""
96-Element Completion Map Scanner

Scans:
  - WF: nous/workflows/{code}.md
  - Skill: nous/skills/{series}/{id}-{name}/SKILL.md
  - Tests: mekhane/ (grep for test functions referencing theorems)
  - FEP: mekhane/fep/ (encoding, agent references)
  - Boot: mekhane/symploke/boot_integration.py

Outputs:
  - Markdown table
  - JSON for image generation
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
AGENT = ROOT / "nous"
MEKHANE = ROOT / "mekhane"

# ── 24 Theorems ──────────────────────────────────
THEOREMS = {
    # O-series (Telos): L0, Pure cognition
    "O1": {"name": "Noēsis", "series": "O", "wf": "noe", "skill_dir": "telos/v01-noesis"},
    "O2": {"name": "Boulēsis", "series": "O", "wf": "bou", "skill_dir": "telos/v02-boulesis"},
    "O3": {"name": "Zētēsis", "series": "O", "wf": "zet", "skill_dir": "telos/v03-zetesis"},
    "O4": {"name": "Energeia", "series": "O", "wf": "ene", "skill_dir": "telos/v04-energeia"},
    # S-series (Methodos): L1, Strategic design
    "S1": {"name": "Metron", "series": "S", "wf": "met", "skill_dir": "schema/s1-metron"},
    "S2": {"name": "Mekhanē", "series": "S", "wf": "mek", "skill_dir": "schema/s2-mekhane"},
    "S3": {"name": "Stathmos", "series": "S", "wf": "sta", "skill_dir": "schema/s3-stathmos"},
    "S4": {"name": "Praxis", "series": "S", "wf": "pra", "skill_dir": "schema/s4-praxis"},
    # H-series (Krisis): L2a, Motivation
    "H1": {"name": "Propatheia", "series": "H", "wf": "pro", "skill_dir": "horme/h1-propatheia"},
    "H2": {"name": "Pistis", "series": "H", "wf": "pis", "skill_dir": "horme/h2-pistis"},
    "H3": {"name": "Orexis", "series": "H", "wf": "ore", "skill_dir": "horme/h3-orexis"},
    "H4": {"name": "Doxa", "series": "H", "wf": "dox", "skill_dir": "horme/h4-doxa"},
    # P-series (Diástasis): L2b, Context placement
    "P1": {"name": "Khōra", "series": "P", "wf": "kho", "skill_dir": "perigraphe/p1-khora"},
    "P2": {"name": "Hodos", "series": "P", "wf": "hod", "skill_dir": "perigraphe/p2-hodos"},
    "P3": {"name": "Trokhia", "series": "P", "wf": "tro", "skill_dir": "perigraphe/p3-trokhia"},
    "P4": {"name": "Tekhnē", "series": "P", "wf": "tek", "skill_dir": "perigraphe/p4-tekhne"},
    # K-series (Chronos): L3, Temporal judgment
    "K1": {"name": "Eukairia", "series": "K", "wf": "euk", "skill_dir": "kairos/k1-eukairia"},
    "K2": {"name": "Chronos", "series": "K", "wf": "chr", "skill_dir": "kairos/k2-chronos"},
    "K3": {"name": "Telos", "series": "K", "wf": "tel", "skill_dir": "kairos/k3-telos"},
    "K4": {"name": "Sophia", "series": "K", "wf": "sop", "skill_dir": "kairos/k4-sophia"},
    # A-series (Orexis): L4, Precision judgment
    "A1": {"name": "Pathos", "series": "A", "wf": "pat", "skill_dir": "akribeia/a1-pathos"},
    "A2": {"name": "Krisis", "series": "A", "wf": "dia", "skill_dir": "akribeia/a2-krisis"},
    "A3": {"name": "Gnōmē", "series": "A", "wf": "gno", "skill_dir": "akribeia/a3-gnome"},
    "A4": {"name": "Epistēmē", "series": "A", "wf": "epi", "skill_dir": "akribeia/a4-episteme"},
}

# ── 7 Axioms ─────────────────────────────────────
AXIOMS = {
    "FEP": {"level": "L0", "desc": "Free Energy Principle"},
    "Flow": {"level": "L1", "desc": "I ↔ A (推論 ↔ 行為)"},
    "Value": {"level": "L1", "desc": "E ↔ P (認識 ↔ 実用)"},
    "Scale": {"level": "L1.5", "desc": "Micro ↔ Macro"},
    "Function": {"level": "L1.5", "desc": "Explore ↔ Exploit"},
    "Valence": {"level": "L1.75", "desc": "+ ↔ -"},
    "Precision": {"level": "L1.75", "desc": "C ↔ U"},
}

# ── 9 X-series groups ────────────────────────────
XSERIES_GROUPS = [
    ("X-OS", "O→S", 8),
    ("X-OH", "O→H", 8),
    ("X-SH", "S→H", 8),
    ("X-SP", "S→P", 8),
    ("X-SK", "S→K", 8),
    ("X-PK", "P→K", 8),
    ("X-HA", "H→A", 8),
    ("X-HK", "H→K", 8),
    ("X-KA", "K→A", 8),
]


def check_wf(wf_code: str) -> bool:
    """Check if workflow file exists."""
    wf_path = AGENT / "workflows" / f"{wf_code}.md"
    return wf_path.exists()


def check_skill(skill_dir: str) -> bool:
    """Check if SKILL.md exists."""
    skill_path = AGENT / "skills" / skill_dir / "SKILL.md"
    return skill_path.exists()


def check_tests(theorem_id: str, theorem_name: str) -> int:
    """Count test files referencing this theorem."""
    count = 0
    patterns = [theorem_id.lower(), theorem_name.lower().replace("ē", "e").replace("ō", "o")]

    for test_file in MEKHANE.rglob("test_*.py"):
        try:
            content = test_file.read_text(encoding="utf-8", errors="ignore").lower()
            for pat in patterns:
                if pat in content:
                    count += 1
                    break
        except Exception:
            pass
    return count


def check_fep(theorem_id: str) -> bool:
    """Check if theorem is referenced in FEP encoding/agent."""
    fep_dir = MEKHANE / "fep"
    if not fep_dir.exists():
        return False

    patterns = [theorem_id, theorem_id.lower()]
    for py_file in fep_dir.glob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            for pat in patterns:
                if pat in content:
                    return True
        except Exception:
            pass
    return False


def check_boot(theorem_id: str) -> bool:
    """Check if theorem is referenced in boot integration."""
    boot_file = MEKHANE / "symploke" / "boot_integration.py"
    if not boot_file.exists():
        return False
    try:
        content = boot_file.read_text(encoding="utf-8")
        return theorem_id in content
    except Exception:
        return False


def check_xseries_impl() -> dict:
    """Check X-series implementation in morphism_proposer, taxis, and WF YAML.

    X-series connections are encoded as:
      - WF YAML morphisms: '>>S': [/met, /mek] means O→S connection
      - morphism_proposer.py: orchestrates >>S/>>H dispatch
      - kernel docs: x_*.md formal definitions
    """
    results = {}

    # Collect all relevant content
    all_content = ""

    # 1. Taxis code
    taxis_dir = MEKHANE / "taxis"
    if taxis_dir.exists():
        for f in taxis_dir.glob("*.py"):
            try:
                all_content += f.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass

    # 2. Kernel x-series docs
    kernel_dir = ROOT / "kernel"
    for f in kernel_dir.glob("*.md"):
        try:
            all_content += f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass

    # 3. WF YAML morphisms (>>S, >>H patterns)
    wf_dir = AGENT / "workflows"
    wf_morphisms = set()  # Series letters with morphism connections
    if wf_dir.exists():
        for wf_file in wf_dir.glob("*.md"):
            try:
                content = wf_file.read_text(encoding="utf-8", errors="ignore")
                # Find >>X patterns in morphisms sections
                for m in re.finditer(r'">>([OSHPKA])"', content):
                    target_series = m.group(1)
                    # Determine source series from WF's theorem
                    for tid, tinfo in THEOREMS.items():
                        if tinfo["wf"] == wf_file.stem:
                            source_series = tinfo["series"]
                            wf_morphisms.add((source_series, target_series))
                            break
            except Exception:
                pass

    # Map (source, target) pairs to X-series groups
    pair_to_group = {}
    for group_name, conn, _count in XSERIES_GROUPS:
        src, tgt = conn.split("→")
        pair_to_group[(src, tgt)] = group_name

    for group_name, _conn, _count in XSERIES_GROUPS:
        # Check in code/docs
        in_code = (group_name.replace("-", "_").lower() in all_content.lower() or
                   group_name.lower() in all_content.lower() or
                   group_name in all_content)
        # Check in WF morphisms
        src, tgt = _conn.split("→")
        in_wf = (src, tgt) in wf_morphisms

        results[group_name] = in_code or in_wf

    return results


def status_icon(val):
    """Convert value to status icon."""
    if isinstance(val, bool):
        return "✅" if val else "—"
    if isinstance(val, int):
        if val >= 3:
            return f"✅({val})"
        elif val >= 1:
            return f"⚠️({val})"
        else:
            return "—"
    return str(val)


def overall_status(wf, skill, tests, fep, boot):
    """Calculate overall status."""
    score = 0
    if wf: score += 1
    if skill: score += 1
    if tests > 0: score += 1
    if fep: score += 1
    if boot: score += 1

    if score >= 5:
        return "◎"  # 完璧
    elif score >= 4:
        return "○"  # 良好
    elif score >= 3:
        return "△"  # 部分的
    elif score >= 1:
        return "▽"  # 不足
    else:
        return "✗"  # 未実装


def main():
    print("# 32実体完成度マップ\n")
    print(f"Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # ── Axioms ──
    print("## 公理 (7)\n")
    print("| Axiom | Level | Description | FEP Code | Status |")
    print("|:------|:-----:|:------------|:--------:|:------:|")
    for name, info in AXIOMS.items():
        fep = check_fep(name)
        status = "✅" if fep else "△"
        print(f"| {name} | {info['level']} | {info['desc']} | {status_icon(fep)} | {status} |")

    # ── Theorems ──
    print("\n## 定理 (24)\n")
    print("| ID | Name | WF | Skill | Tests | FEP | Boot | Status |")
    print("|:---|:-----|:--:|:-----:|:-----:|:---:|:----:|:------:|")

    theorem_data = []
    for tid, info in THEOREMS.items():
        wf = check_wf(info["wf"])
        skill = check_skill(info["skill_dir"])
        tests = check_tests(tid, info["name"])
        fep = check_fep(tid)
        boot = check_boot(tid)
        status = overall_status(wf, skill, tests, fep, boot)

        print(f"| {tid} | {info['name']} | {status_icon(wf)} | {status_icon(skill)} | {status_icon(tests)} | {status_icon(fep)} | {status_icon(boot)} | {status} |")

        theorem_data.append({
            "id": tid, "name": info["name"], "series": info["series"],
            "wf": wf, "skill": skill, "tests": tests, "fep": fep, "boot": boot,
            "status": status,
        })

    # ── Series Summary ──
    print("\n## Series サマリ\n")
    print("| Series | ◎ | ○ | △ | ▽ | ✗ | Coverage |")
    print("|:-------|:-:|:-:|:-:|:-:|:-:|:--------:|")

    for series_code in ["O", "S", "H", "P", "K", "A"]:
        series_theorems = [t for t in theorem_data if t["series"] == series_code]
        counts = {}
        for s in ["◎", "○", "△", "▽", "✗"]:
            counts[s] = sum(1 for t in series_theorems if t["status"] == s)

        good = counts.get("◎", 0) + counts.get("○", 0)
        total = len(series_theorems)
        cov = f"{good/total*100:.0f}%" if total else "N/A"
        series_names = {"O": "Telos", "S": "Methodos", "H": "Krisis", "P": "Diástasis", "K": "Chronos", "A": "Orexis"}

        print(f"| {series_code} ({series_names[series_code]}) | {counts.get('◎',0)} | {counts.get('○',0)} | {counts.get('△',0)} | {counts.get('▽',0)} | {counts.get('✗',0)} | {cov} |")

    # ── X-series ──
    print("\n## X-series 関係 (72)\n")
    xresults = check_xseries_impl()
    print("| Group | Connection | Count | Code Ref | Status |")
    print("|:------|:-----------|:-----:|:--------:|:------:|")
    for group_name, conn, count in XSERIES_GROUPS:
        has_impl = xresults.get(group_name, False)
        print(f"| {group_name} | {conn} | {count} | {status_icon(has_impl)} | {'△' if has_impl else '▽'} |")

    # ── Totals ──
    total_good = sum(1 for t in theorem_data if t["status"] in ("◎", "○"))
    total_partial = sum(1 for t in theorem_data if t["status"] == "△")
    total_weak = sum(1 for t in theorem_data if t["status"] in ("▽", "✗"))
    x_impl = sum(1 for v in xresults.values() if v)

    print(f"\n## 全体サマリ\n")
    print(f"| Component | Total | Good | Partial | Weak |")
    print(f"|:----------|:-----:|:----:|:-------:|:----:|")
    print(f"| Axioms | 7 | — | — | — |")
    print(f"| Theorems | 24 | {total_good} | {total_partial} | {total_weak} |")
    print(f"| X-series groups | 9 | {x_impl} | — | {9-x_impl} |")
    print(f"| **Total elements** | **96** | — | — | — |")

    # Save JSON for image generation
    json_data = {
        "axioms": list(AXIOMS.keys()),
        "theorems": theorem_data,
        "xseries": {k: v for k, v in xresults.items()},
        "summary": {
            "total_good": total_good,
            "total_partial": total_partial,
            "total_weak": total_weak,
            "x_impl": x_impl,
        }
    }
    json_path = ROOT / "docs" / "completion_map.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False))
    print(f"\n📄 JSON saved: {json_path}")


if __name__ == "__main__":
    main()
