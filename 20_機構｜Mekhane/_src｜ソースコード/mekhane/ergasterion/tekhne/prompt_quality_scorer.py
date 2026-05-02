from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ergasterion/tekhne/ A0→プロンプト品質定量化が必要→prompt_quality_scorerが担う
"""
Prompt Quality Scorer — システムプロンプトの品質を定量的にスコアリング

4次元スコア体系:
  - Structure (構造): YAML frontmatter, 必須セクション充足率
  - Safety (安全性): 敵対的入力対策, ガードレール記述
  - Completeness (完成度): Edge Cases, Fallback, 定量指標
  - Archetype Fit (適合度): Archetype 必須技術/禁忌との整合性

Usage:
  python prompt_quality_scorer.py <filepath>
  python prompt_quality_scorer.py --batch "nous/skills/*/SKILL.md" --min-score 50
"""


import argparse
import glob
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# === Score Data Structures ===

# PURPOSE: の統一的インターフェースを実現する
@dataclass
class DimensionScore:
    """Individual dimension score with details."""
    score: int  # 0-100
    max_score: int
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    # PURPOSE: prompt_quality_scorer の normalized 処理を実行する
    @property
    def normalized(self) -> int:
        """Normalize to 0-100 scale."""
        if self.max_score == 0:
            return 0
        return min(100, int((self.score / self.max_score) * 100))


# PURPOSE: の統一的インターフェースを実現する
@dataclass
class QualityReport:
    """Complete quality assessment report."""
    filepath: str
    structure: DimensionScore
    safety: DimensionScore
    completeness: DimensionScore
    archetype_fit: DimensionScore
    detected_format: str  # "skill" | "prompt" | "sage" | "unknown"
    detected_archetype: Optional[str] = None

    # PURPOSE: prompt_quality_scorer の total 処理を実行する
    @property
    def total(self) -> int:
        """Weighted total score (Structure 30, Safety 20, Completeness 30, Fit 20)."""
        return int(
            self.structure.normalized * 0.30
            + self.safety.normalized * 0.20
            + self.completeness.normalized * 0.30
            + self.archetype_fit.normalized * 0.20
        )

    # PURPOSE: prompt_quality_scorer の grade 処理を実行する
    @property
    def grade(self) -> str:
        t = self.total
        if t >= 90:
            return "S"
        elif t >= 80:
            return "A"
        elif t >= 70:
            return "B"
        elif t >= 60:
            return "C"
        elif t >= 50:
            return "D"
        else:
            return "F"

    # PURPOSE: prompt_quality_scorer の to dict 処理を実行する
    def to_dict(self) -> dict:
        return {
            "filepath": self.filepath,
            "total": self.total,
            "grade": self.grade,
            "detected_format": self.detected_format,
            "detected_archetype": self.detected_archetype,
            "dimensions": {
                "structure": {
                    "score": self.structure.normalized,
                    "passed": self.structure.checks_passed,
                    "failed": self.structure.checks_failed,
                    "suggestions": self.structure.suggestions,
                },
                "safety": {
                    "score": self.safety.normalized,
                    "passed": self.safety.checks_passed,
                    "failed": self.safety.checks_failed,
                    "suggestions": self.safety.suggestions,
                },
                "completeness": {
                    "score": self.completeness.normalized,
                    "passed": self.completeness.checks_passed,
                    "failed": self.completeness.checks_failed,
                    "suggestions": self.completeness.suggestions,
                },
                "archetype_fit": {
                    "score": self.archetype_fit.normalized,
                    "passed": self.archetype_fit.checks_passed,
                    "failed": self.archetype_fit.checks_failed,
                    "suggestions": self.archetype_fit.suggestions,
                },
            },
        }


# === Format Detection ===

# PURPOSE: prompt_quality_scorer の detect format 処理を実行する
def detect_format(content: str) -> str:
    """Detect prompt format: skill, prompt, sage, or unknown."""
    if content.strip().startswith("---") and "name:" in content[:500]:
        return "skill"
    if content.strip().startswith("//") or content.strip().startswith("#prompt"):
        return "prompt"
    if "<module_config>" in content or "<instruction>" in content:
        return "sage"
    return "unknown"


# PURPOSE: prompt_quality_scorer の extract frontmatter 処理を実行する
def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from SKILL.md format."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    try:
        import yaml
        return yaml.safe_load(match.group(1)) or {}
    except Exception:  # noqa: BLE001
        return {}


# === Archetype Detection ===

ARCHETYPE_KEYWORDS = {
    "Precision": ["精度", "accuracy", "precision", "誤答率", "検証", "verification",
                  "CoVe", "WACK", "confidence"],
    "Speed": ["速度", "speed", "レイテンシ", "latency", "fast", "高速", "compression"],
    "Autonomy": ["自律", "autonomy", "autonomous", "エージェント", "agent",
                 "ReAct", "Reflexion", "fallback"],
    "Creative": ["創造", "creative", "多様性", "diversity", "アイデア", "idea",
                 "temperature", "brainstorm"],
    "Safety": ["安全", "safety", "リスク", "risk", "guard", "URIAL",
               "injection", "harmful"],
}


# PURPOSE: prompt_quality_scorer の detect archetype 処理を実行する
def detect_archetype(content: str) -> Optional[str]:
    """Detect the most likely archetype from content."""
    scores: dict[str, int] = {}
    content_lower = content.lower()
    for archetype, keywords in ARCHETYPE_KEYWORDS.items():
        scores[archetype] = sum(1 for kw in keywords if kw.lower() in content_lower)
    if not any(scores.values()):
        return None
    return max(scores, key=scores.get)


# === Dimension Checkers ===

# PURPOSE: structure を検証する
def check_structure(content: str, fmt: str) -> DimensionScore:
    """Check structural quality of the prompt."""
    score = 0
    max_score = 0
    passed = []
    failed = []
    suggestions = []

    if fmt == "skill":
        # YAML frontmatter
        max_score += 20
        fm = extract_frontmatter(content)
        if fm:
            score += 10
            passed.append("YAML frontmatter present")
            if fm.get("name"):
                score += 5
                passed.append("name field exists")
            else:
                failed.append("name field missing in frontmatter")
                suggestions.append("frontmatter に name: を追加してください")
            if fm.get("description"):
                score += 5
                passed.append("description field exists")
            else:
                failed.append("description field missing")
                suggestions.append("frontmatter に description: を追加してください")
        else:
            failed.append("YAML frontmatter missing")
            suggestions.append("--- で囲んだ YAML frontmatter を追加してください")

        # Required sections
        required_sections = [
            ("Overview", 10),
            ("Core Behavior", 15),
            ("Quality Standards", 10),
            ("Edge Cases", 10),
            ("Examples", 10),
        ]
        for section_name, points in required_sections:
            max_score += points
            patterns = [
                f"## {section_name}",
                f"## {section_name.lower()}",
                f"### {section_name}",
            ]
            if any(p in content for p in patterns):
                score += points
                passed.append(f"Section '{section_name}' found")
            else:
                failed.append(f"Section '{section_name}' missing")
                suggestions.append(f"## {section_name} セクションを追加してください")

        # Heading hierarchy
        max_score += 10
        h2_count = len(re.findall(r"^## ", content, re.MULTILINE))
        if h2_count >= 3:
            score += 10
            passed.append(f"Good heading structure ({h2_count} H2 sections)")
        elif h2_count >= 1:
            score += 5
            passed.append(f"Minimal heading structure ({h2_count} H2 sections)")
            suggestions.append("セクション構造をもう少し分割することを推奨")
        else:
            failed.append("No H2 headings found")
            suggestions.append("## 見出しでセクションを構造化してください")

        # Content length
        max_score += 15
        word_count = len(content.split())
        if word_count >= 200:
            score += 15
            passed.append(f"Sufficient content length ({word_count} words)")
        elif word_count >= 100:
            score += 8
            passed.append(f"Minimal content length ({word_count} words)")
            suggestions.append("内容をもう少し詳細に記述することを推奨")
        else:
            failed.append(f"Content too short ({word_count} words)")
            suggestions.append("最低200語以上の内容を記述してください")

    elif fmt == "prompt":
        # Týpos format checks
        max_score += 40
        if "#prompt" in content:
            score += 10
            passed.append("#prompt directive found")
        else:
            failed.append("#prompt directive missing")
        if "@role:" in content:
            score += 10
            passed.append("@role defined")
        else:
            failed.append("@role missing")
            suggestions.append("@role: でロールを定義してください")
        if "@goal:" in content:
            score += 10
            passed.append("@goal defined")
        else:
            failed.append("@goal missing")
        if "@constraints:" in content:
            score += 10
            passed.append("@constraints defined")
        else:
            failed.append("@constraints missing")

        max_score += 30
        if "@examples:" in content:
            score += 15
            passed.append("@examples provided")
        else:
            failed.append("@examples missing")
            suggestions.append("@examples: で入出力例を追加してください")
        if "@format:" in content:
            score += 15
            passed.append("@format defined")
        else:
            failed.append("@format missing")

        max_score += 30
        word_count = len(content.split())
        if word_count >= 100:
            score += 30
            passed.append(f"Sufficient content ({word_count} words)")
        elif word_count >= 50:
            score += 15
            passed.append(f"Minimal content ({word_count} words)")
        else:
            failed.append(f"Content too short ({word_count} words)")

    elif fmt == "sage":
        max_score += 50
        for tag, points in [("<module_config>", 10), ("<instruction>", 15),
                            ("<protocol>", 10), ("<constraints>", 10),
                            ("<output_template>", 5)]:
            max_score_adj = points  # already included in 50
            if tag in content:
                score += points
                passed.append(f"XML tag {tag} found")
            else:
                failed.append(f"XML tag {tag} missing")
                suggestions.append(f"{tag} タグを追加してください")

        max_score += 50
        word_count = len(content.split())
        if word_count >= 150:
            score += 50
            passed.append(f"Sufficient content ({word_count} words)")
        elif word_count >= 75:
            score += 25
        else:
            failed.append(f"Content too short ({word_count} words)")

    else:
        max_score = 100
        score = 30  # Unknown format gets base score
        suggestions.append("認識可能なフォーマット (SKILL.md / .prompt / SAGE XML) を使用してください")

    return DimensionScore(score=score, max_score=max(max_score, 1),
                          checks_passed=passed, checks_failed=failed,
                          suggestions=suggestions)


# PURPOSE: safety を検証する
def check_safety(content: str) -> DimensionScore:
    """Check safety-related qualities."""
    score = 0
    max_score = 0
    passed = []
    failed = []
    suggestions = []

    # Injection defense
    safety_patterns = [
        ("injection", 15, "Prompt injection defense",
         "prompt injection への防御を記述してください"),
        ("guard|guardrail|boundary", 15, "Guardrails defined",
         "ガードレール/境界条件を定義してください"),
        ("error|exception|エラー|異常", 10, "Error handling mentioned",
         "エラー/異常系の処理を記述してください"),
        ("fallback|フォールバック|代替", 10, "Fallback strategy",
         "フォールバック戦略を定義してください"),
        ("role|persona|ロール", 10, "Role boundaries defined",
         "ロール境界を明確に定義してください"),
        ("confidenc|確信|信頼", 10, "Confidence handling",
         "確信度の表現方法を定義してください"),
        ("refuse|reject|拒否|limitations", 10, "Refusal conditions",
         "拒否/回答保留の条件を定義してください"),
        ("harmful|有害|unethical", 5, "Harmful content policy",
         "有害コンテンツへのポリシーを記述してください"),
        ("user_input|input.*zone|sanitiz", 10, "Input sanitization",
         "ユーザー入力の隔離/サニタイズを記述してください"),
        ("limit|制限|boundary|上限", 5, "Operational limits",
         "動作上限/制限を定義してください"),
    ]

    for pattern, points, pass_msg, fail_msg in safety_patterns:
        max_score += points
        if re.search(pattern, content, re.IGNORECASE):
            score += points
            passed.append(pass_msg)
        else:
            failed.append(pass_msg + " — not found")
            suggestions.append(fail_msg)

    return DimensionScore(score=score, max_score=max(max_score, 1),
                          checks_passed=passed, checks_failed=failed,
                          suggestions=suggestions)


# PURPOSE: completeness を検証する
def check_completeness(content: str, fmt: str) -> DimensionScore:
    """Check completeness of the prompt."""
    score = 0
    max_score = 0
    passed = []
    failed = []
    suggestions = []

    # Edge cases / failure scenarios
    max_score += 25
    failure_keywords = re.findall(
        r"(failure|失敗|edge.?case|境界|trap|罠|worst.?case|最悪|pre.?mortem)",
        content, re.IGNORECASE
    )
    failure_count = len(failure_keywords)
    if failure_count >= 3:
        score += 25
        passed.append(f"Failure scenarios: {failure_count} mentions (≥3 required)")
    elif failure_count >= 1:
        score += 12
        passed.append(f"Failure scenarios: {failure_count} mentions (need ≥3)")
        suggestions.append("失敗ケースを3つ以上予測してください")
    else:
        failed.append("No failure scenarios described")
        suggestions.append("失敗ケースの予測 (Pre-Mortem) を追加してください")

    # Quantitative metrics
    max_score += 20
    quant_patterns = [r"\d+%", r"\d+秒", r"\d+件", r"<\s*\d", r">\s*\d",
                      r"\d+回", r"score", r"metric"]
    quant_found = sum(1 for p in quant_patterns if re.search(p, content))
    if quant_found >= 3:
        score += 20
        passed.append(f"Quantitative metrics: {quant_found} found")
    elif quant_found >= 1:
        score += 10
        passed.append(f"Minimal quantitative metrics: {quant_found} found")
        suggestions.append("定量的品質指標をもう少し追加してください")
    else:
        failed.append("No quantitative metrics found")
        suggestions.append("定量的品質指標 (精度X%以上、レイテンシY秒以下 等) を追加してください")

    # Examples
    max_score += 20
    example_patterns = [r"example|例|input.*output|入力.*出力|usage|使用方法"]
    if any(re.search(p, content, re.IGNORECASE) for p in example_patterns):
        score += 20
        passed.append("Examples/usage section found")
    else:
        failed.append("No examples found")
        suggestions.append("入出力例 (Examples) を追加してください")

    # Fallback strategy
    max_score += 15
    if re.search(r"fallback|フォールバック|代替|escalat|エスカレーション", content, re.IGNORECASE):
        score += 15
        passed.append("Fallback/escalation strategy defined")
    else:
        failed.append("No fallback strategy")
        suggestions.append("Fallback/エスカレーション戦略を定義してください")

    # Tools / references
    max_score += 10
    if re.search(r"tool|ツール|reference|参照|context|コンテキスト", content, re.IGNORECASE):
        score += 10
        passed.append("Tools/references defined")
    else:
        failed.append("No tools or references mentioned")
        suggestions.append("使用ツールや参照ファイルを記述してください")

    # Activation / trigger conditions
    max_score += 10
    if re.search(r"trigger|activation|発動|起動|条件", content, re.IGNORECASE):
        score += 10
        passed.append("Activation triggers defined")
    else:
        failed.append("No activation triggers")
        suggestions.append("発動条件 (Triggers) を定義してください")

    return DimensionScore(score=score, max_score=max(max_score, 1),
                          checks_passed=passed, checks_failed=failed,
                          suggestions=suggestions)


ARCHETYPE_REQUIRED_TECH = {
    "Precision": ["CoVe", "WACK", "Confidence", "検証", "verification"],
    "Speed": ["圧縮", "compression", "cache", "キャッシュ", "短文"],
    "Autonomy": ["ReAct", "Reflexion", "Fallback", "エスカレーション", "Mem0"],
    "Creative": ["Temperature", "SAC", "多様性", "diversity"],
    "Safety": ["URIAL", "Neutralizing", "Constitutional", "有害", "フィルタ"],
}

ARCHETYPE_FORBIDDEN_TECH = {
    "Precision": ["EmotionPrompt", "高Temperature", "Creative"],
    "Speed": ["Many-shot", "Self-Consistency", "ToT", "深いCoT"],
    "Autonomy": ["Abstention", "過度な", "人間確認必須"],
    "Creative": ["Temperature=0", "厳格なフォーマット制約"],
    "Safety": ["ロール逸脱許容", "無制限生成"],
}


# PURPOSE: archetype fit を検証する
def check_archetype_fit(content: str, archetype: Optional[str]) -> DimensionScore:
    """Check archetype-specific fitness."""
    score = 0
    max_score = 0
    passed = []
    failed = []
    suggestions = []

    if not archetype:
        return DimensionScore(
            score=50, max_score=100,
            checks_passed=["No archetype detected — using neutral score"],
            checks_failed=[],
            suggestions=["Archetype (Precision/Speed/Autonomy/Creative/Safety) を明示してください"]
        )

    # Required technologies
    required = ARCHETYPE_REQUIRED_TECH.get(archetype, [])
    max_score += len(required) * 15
    for tech in required:
        if re.search(tech, content, re.IGNORECASE):
            score += 15
            passed.append(f"Required tech '{tech}' found for {archetype}")
        else:
            failed.append(f"Required tech '{tech}' missing for {archetype}")
            suggestions.append(f"{archetype} アーキタイプに必要な '{tech}' を追加してください")

    # Forbidden technologies (negative check)
    forbidden = ARCHETYPE_FORBIDDEN_TECH.get(archetype, [])
    max_score += len(forbidden) * 10
    for tech in forbidden:
        if re.search(tech, content, re.IGNORECASE):
            failed.append(f"Forbidden tech '{tech}' found for {archetype}")
            suggestions.append(f"{archetype} アーキタイプでは '{tech}' の使用を避けてください")
        else:
            score += 10
            passed.append(f"Forbidden tech '{tech}' correctly absent")

    if max_score == 0:
        max_score = 100
        score = 50

    return DimensionScore(score=score, max_score=max(max_score, 1),
                          checks_passed=passed, checks_failed=failed,
                          suggestions=suggestions)


# === Convergence/Divergence Policy ===

# FEP Function axiom: Explore ↔ Exploit
# .prompt = precision weighting ↑ = Exploit optimal, Explore detrimental
CONVERGENT_TASKS = frozenset([
    "data_extraction", "spec_generation", "test_generation",
    "code_formatting", "translation", "schema_validation",
    "jules_coding",
])

DIVERGENT_TASKS = frozenset([
    "brainstorming", "ideation", "exploration",
    "creative_writing", "design_review",
])


# PURPOSE: convergence policy を検証する
def check_convergence_policy(archetype: Optional[str], fmt: str) -> list[str]:
    """Check if .prompt format is appropriate for detected archetype.

    Returns list of warnings (empty = no issues).
    FEP basis: Function axiom (Explore ↔ Exploit)
    """
    warnings = []
    if fmt == "prompt" and archetype == "Creative":
        warnings.append(
            "⚠️ POLICY: Creative archetype + .prompt 形式は多様性喪失リスクあり。"
            " .prompt は precision weighting を上げるため、拡散タスクには不向き。"
            " (FEP Function 公理: Explore ↔ Exploit)"
        )
    return warnings


# === Main Scoring ===

# PURPOSE: prompt_quality_scorer の score prompt 処理を実行する
def score_prompt(filepath: str) -> QualityReport:
    """Score a prompt file and return a QualityReport."""
    content = Path(filepath).read_text(encoding="utf-8")
    return _score_content(content, filepath=filepath)


# PURPOSE: [L2-auto] score_prompt_text の関数定義
def score_prompt_text(content: str, name: str = "<inline>") -> QualityReport:
    """Score prompt content directly (without reading from file).

    Args:
        content: The prompt text to score
        name: Display name for the report

    Returns:
        QualityReport with scoring results
    """
    return _score_content(content, filepath=name)


# PURPOSE: [L2-auto] _score_content の関数定義
def _score_content(content: str, filepath: str = "<inline>") -> QualityReport:
    """Internal scoring logic shared by score_prompt and score_prompt_text."""
    fmt = detect_format(content)
    archetype = detect_archetype(content)

    report = QualityReport(
        filepath=filepath,
        structure=check_structure(content, fmt),
        safety=check_safety(content),
        completeness=check_completeness(content, fmt),
        archetype_fit=check_archetype_fit(content, archetype),
        detected_format=fmt,
        detected_archetype=archetype,
    )

    # Add convergence/divergence policy warnings
    policy_warnings = check_convergence_policy(archetype, fmt)
    for w in policy_warnings:
        report.archetype_fit.suggestions.append(w)

    return report


# PURPOSE: report を整形する
def format_report(report: QualityReport, verbose: bool = False) -> str:
    """Format a QualityReport as human-readable text."""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"📊 Prompt Quality Score: {report.filepath}")
    lines.append(f"{'='*60}")
    lines.append(f"  Format: {report.detected_format} | Archetype: {report.detected_archetype or 'N/A'}")
    lines.append(f"")
    lines.append(f"  Total: {report.total}/100 (Grade: {report.grade})")
    lines.append(f"")
    lines.append(f"  ├─ Structure:     {report.structure.normalized:3d}/100")
    lines.append(f"  ├─ Safety:        {report.safety.normalized:3d}/100")
    lines.append(f"  ├─ Completeness:  {report.completeness.normalized:3d}/100")
    lines.append(f"  └─ Archetype Fit: {report.archetype_fit.normalized:3d}/100")

    if verbose:
        for dim_name, dim in [("Structure", report.structure),
                               ("Safety", report.safety),
                               ("Completeness", report.completeness),
                               ("Archetype Fit", report.archetype_fit)]:
            if dim.checks_failed or dim.suggestions:
                lines.append(f"\n  [{dim_name}] Improvements:")
                for s in dim.suggestions[:5]:
                    lines.append(f"    → {s}")

    lines.append(f"{'='*60}")
    return "\n".join(lines)


# === CLI ===

# PURPOSE: prompt_quality_scorer の main 処理を実行する
def main():
    parser = argparse.ArgumentParser(description="Prompt Quality Scorer")
    parser.add_argument("filepath", nargs="?", help="Path to prompt file")
    parser.add_argument("--batch", help="Glob pattern for batch scoring")
    parser.add_argument("--min-score", type=int, default=0,
                        help="Minimum score threshold (exit 1 if any below)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show detailed suggestions")
    args = parser.parse_args()

    if not args.filepath and not args.batch:
        parser.error("Either filepath or --batch is required")

    files = []
    if args.batch:
        files = sorted(glob.glob(args.batch, recursive=True))
    elif args.filepath:
        files = [args.filepath]

    if not files:
        print("No files found.")
        sys.exit(1)

    reports = []
    failures = []

    for f in files:
        try:
            report = score_prompt(f)
            reports.append(report)
            if report.total < args.min_score:
                failures.append(report)
        except Exception as e:  # noqa: BLE001
            print(f"Error scoring {f}: {e}", file=sys.stderr)

    if args.json:
        print(json.dumps([r.to_dict() for r in reports], ensure_ascii=False, indent=2))
    else:
        for r in reports:
            print(format_report(r, verbose=args.verbose))

        if len(reports) > 1:
            avg = sum(r.total for r in reports) / len(reports)
            print(f"\n📈 Batch Summary: {len(reports)} files | Avg: {avg:.1f}/100")
            if failures:
                print(f"⚠️  {len(failures)} file(s) below threshold ({args.min_score}):")
                for f in failures:
                    print(f"   {f.filepath}: {f.total}/100 (Grade: {f.grade})")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
