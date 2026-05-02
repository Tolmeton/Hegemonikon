from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/fep/ A0→WFフロントマターのcategory_theoryを消費する必要→wf_category_parserが担う
"""
WF Category Theory Frontmatter Parser

WF (.md) の YAML フロントマターに書かれた category_theory: ブロックを
パースし、category.py の型に変換する **最初の消費者コード**。

Origin: /zet+ Q2 (2026-02-08)
Problem: フロントマターに category_theory: があるが、読むコードがなかった。
         これは宣言と実装の乖離 (Q16 Layer C) であり、バグと同等。

Supported frontmatter patterns:
    Pattern A — Peras WF (o.md, s.md, h.md, p.md, k.md, a.md):
        category_theory:
          yoneda: "Hom(-, Tn) ≅ F(Tn)"
          limit: "Cone の頂点"
          converge_as_cone: "C0=PW, C1=射, C2=融合, C3=検証"
          cone_builder: "mekhane/fep/cone_builder.py"

    Pattern B — Monad WF (zet.md):
        category_theory:
          core: "モナド T: Cog → Cog"
          unit: "η: X → T(X)"
          join: "μ: T(T(X)) → T(X)"
          kleisli: "anom >==> hypo >==> eval"
          laws: {left_unit, right_unit, associativity}

Usage:
    from mekhane.fep.wf_category_parser import parse_wf_category, scan_all_wfs
    info = parse_wf_category(Path("nous/workflows/o.md"))
    report = scan_all_wfs()
"""


import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


# PURPOSE: category_theory フロントマターのパース結果
@dataclass
class WFCategoryInfo:
    """Parsed category_theory block from a WF frontmatter."""

    wf_path: Path                          # WF ファイルパス
    wf_name: str = ""                      # WF 名 (/o, /zet, etc.)
    pattern: str = ""                      # "peras" | "monad" | "adjunction" | "unknown"
    raw: Dict = field(default_factory=dict) # 生の YAML dict

    # Peras pattern fields
    yoneda: str = ""
    limit: str = ""
    converge_as_cone: str = ""
    cone_builder_path: str = ""

    # Monad pattern fields
    core: str = ""
    unit: str = ""
    join: str = ""
    kleisli: str = ""
    laws: Dict[str, str] = field(default_factory=dict)

    # Common
    description: str = ""                   # 1行要約

    # PURPOSE: wf_category_parser の is valid 処理を実行する
    @property
    def is_valid(self) -> bool:
        """最低限のフィールドが埋まっているか。"""
        if self.pattern == "peras":
            return bool(self.converge_as_cone)
        elif self.pattern == "monad":
            return bool(self.core)
        return bool(self.raw)

    # PURPOSE: wf_category_parser の coverage score 処理を実行する
    @property
    def coverage_score(self) -> float:
        """フロントマターの充実度 (0.0-1.0)。"""
        if self.pattern == "peras":
            fields = [self.yoneda, self.limit, self.converge_as_cone, self.cone_builder_path]
            return sum(1.0 for f in fields if f) / len(fields)
        elif self.pattern == "monad":
            fields = [self.core, self.unit, self.join, self.kleisli]
            law_score = min(len(self.laws) / 3, 1.0) if self.laws else 0.0
            base = sum(1.0 for f in fields if f) / len(fields)
            return (base + law_score) / 2
        return 0.0


# PURPOSE: YAML フロントマターを抽出
def _extract_frontmatter(wf_path: Path) -> Optional[Dict]:
    """Extract YAML frontmatter from a WF markdown file."""
    text = wf_path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


# PURPOSE: category_theory パターンを判定
def _detect_pattern(ct: Dict) -> str:
    """Detect which category_theory pattern this is."""
    if "core" in ct or "unit" in ct or "join" in ct:
        return "monad"
    if "yoneda" in ct or "limit" in ct or "converge_as_cone" in ct:
        return "peras"
    if "left" in ct or "right" in ct or "adjunction" in ct:
        return "adjunction"
    return "unknown"


# PURPOSE: 単一の WF からcategory_theory 情報をパース
def parse_wf_category(wf_path: Path) -> Optional[WFCategoryInfo]:
    """Parse category_theory block from a single WF file.

    Returns None if the WF has no category_theory frontmatter.
    """
    fm = _extract_frontmatter(wf_path)
    if not fm or "category_theory" not in fm:
        return None

    ct = fm["category_theory"]
    if not isinstance(ct, dict):
        return None

    pattern = _detect_pattern(ct)
    wf_name = "/" + wf_path.stem

    info = WFCategoryInfo(
        wf_path=wf_path,
        wf_name=wf_name,
        pattern=pattern,
        raw=ct,
    )

    if pattern == "peras":
        info.yoneda = ct.get("yoneda", "")
        info.limit = ct.get("limit", "")
        info.converge_as_cone = ct.get("converge_as_cone", "")
        info.cone_builder_path = ct.get("cone_builder", "")
        info.description = f"Peras WF: {info.converge_as_cone[:60]}"

    elif pattern == "monad":
        info.core = ct.get("core", "")
        info.unit = ct.get("unit", "")
        info.join = ct.get("join", "")
        info.kleisli = ct.get("kleisli", "")
        info.laws = ct.get("laws", {})
        info.description = f"Monad WF: {info.core[:60]}"

    return info


# PURPOSE: 全 WF をスキャンして category_theory 情報を集約
def scan_all_wfs(wf_dir: Optional[Path] = None) -> Dict[str, WFCategoryInfo]:
    """Scan all WF files and extract category_theory info.

    Returns:
        Dict mapping WF name → WFCategoryInfo
    """
    if wf_dir is None:
        wf_dir = Path(__file__).parent.parent.parent / "nous" / "workflows"

    results = {}
    if not wf_dir.exists():
        return results

    for wf_path in sorted(wf_dir.glob("*.md")):
        info = parse_wf_category(wf_path)
        if info is not None:
            results[info.wf_name] = info

    return results


# PURPOSE: category_theory coverage レポートを生成
def coverage_report(wf_dir: Optional[Path] = None) -> str:
    """Generate a coverage report of category_theory frontmatter.

    Shows which WFs have category_theory, their pattern, and coverage score.
    """
    if wf_dir is None:
        wf_dir = Path(__file__).parent.parent.parent / "nous" / "workflows"

    all_wfs = sorted(wf_dir.glob("*.md")) if wf_dir.exists() else []
    parsed = scan_all_wfs(wf_dir)

    lines = [
        "Category Theory Frontmatter Coverage Report",
        "=" * 50,
        f"Total WFs: {len(all_wfs)} | With category_theory: {len(parsed)}",
        "",
    ]

    # By pattern
    patterns: Dict[str, List[str]] = {}
    for name, info in parsed.items():
        patterns.setdefault(info.pattern, []).append(name)

    for pat, names in sorted(patterns.items()):
        lines.append(f"\n📐 Pattern: {pat} ({len(names)} WFs)")
        for name in names:
            info = parsed[name]
            score = info.coverage_score
            icon = "✅" if score >= 0.75 else "🟡" if score >= 0.5 else "🔴"
            lines.append(f"  {icon} {name:8s} coverage={score:.0%} — {info.description}")

    # Missing
    missing = [
        "/" + wf.stem for wf in all_wfs
        if "/" + wf.stem not in parsed
    ]
    if missing:
        lines.append(f"\n⚪ No category_theory ({len(missing)} WFs):")
        # Show first 10
        for name in missing[:10]:
            lines.append(f"  · {name}")
        if len(missing) > 10:
            lines.append(f"  ... and {len(missing) - 10} more")

    return "\n".join(lines)


if __name__ == "__main__":
    print(coverage_report())
