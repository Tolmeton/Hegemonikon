# PROOF: [L2/インフラ] <- mekhane/ccl/sel_validator.py
"""
SEL Validator — Semantic Enforcement Layer 遵守検証

目的:
- WF 出力が sel_enforcement の minimum_requirements を満たすか検証
- 遵守率を測定し、非遵守時に警告を発行
- /vet との統合による事後検証

Usage:
    from mekhane.ccl.sel_validator import SELValidator

    validator = SELValidator()
    result = validator.validate(workflow="boot", operator="+", output=response)
    if not result.is_compliant:
        print(f"非遵守: {result.missing_requirements}")
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional
import yaml


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: SEL 要件
class SELRequirement:
    """SEL 要件"""

    description: str
    minimum_requirements: List[str]
    uml_requirements: Dict[str, str] = field(default_factory=dict)  # stage -> 要件テキスト


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: SEL 検証結果
class SELValidationResult:
    """SEL 検証結果"""

    workflow: str
    operator: str
    is_compliant: bool
    met_requirements: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    score: float = 0.0  # 遵守率 0.0-1.0
    uml_score: float = 0.0  # UML 遵守率 0.0-1.0
    uml_met: List[str] = field(default_factory=list)
    uml_missing: List[str] = field(default_factory=list)
    details: str = ""

    # PURPOSE: sel_validator の summary 処理を実行する
    @property
    # PURPOSE: SEL 遵守検証器
    def summary(self) -> str:
        status = "✅ 遵守" if self.is_compliant else "⚠️ 非遵守"
        total = len(self.met_requirements) + len(self.missing_requirements)
        uml_part = ""
        if self.uml_met or self.uml_missing:
            uml_total = len(self.uml_met) + len(self.uml_missing)
            uml_part = f" | UML: {len(self.uml_met)}/{uml_total}"
        return f"{status} {self.workflow}{self.operator}: {self.score:.0%} ({len(self.met_requirements)}/{total}){uml_part}"

# PURPOSE: SEL 遵守検証器

# PURPOSE: [L2-auto] SELValidator のクラス定義
class SELValidator:
    """SEL 遵守検証器"""

    # PURPOSE: SELValidator の構成と依存関係の初期化
    def __init__(self, workflows_dir: Optional[Path] = None):
        if workflows_dir is not None:
            self.workflows_dir = workflows_dir
        else:
            self.workflows_dir = (
                Path(__file__).resolve().parents[4] / ".agents" / "workflows"
            )
        self._cache: Dict[str, Dict] = {}

    # PURPOSE: ワークフローの sel_enforcement をロード
    def load_sel_enforcement(
        self, workflow: str
    ) -> Optional[Dict[str, SELRequirement]]:
        """ワークフローの sel_enforcement をロード"""
        if workflow in self._cache:
            return self._cache[workflow]

        wf_path = self.workflows_dir / f"{workflow}.md"
        ccl_wf_path = self.workflows_dir / f"ccl-{workflow}.md"
        if not wf_path.exists() and ccl_wf_path.exists():
            wf_path = ccl_wf_path
        if not wf_path.exists():
            return None

        content = wf_path.read_text(encoding="utf-8")

        # YAML frontmatter を抽出
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None

        sel = frontmatter.get("sel_enforcement")
        if not sel:
            return None

        result = {}
        for op, data in sel.items():
            if isinstance(data, dict):
                result[op] = SELRequirement(
                    description=data.get("description", ""),
                    minimum_requirements=data.get("minimum_requirements", []),
                    uml_requirements=data.get("uml_requirements", {}),
                )

        self._cache[workflow] = result
        return result

    # PURPOSE: 要件が出力に満たされているか確認
    def check_requirement(self, requirement: str, output: str) -> bool:
        """要件が出力に満たされているか確認"""
        # 日本語の要件を正規化してマッチング
        req_normalized = requirement.lower().replace(" ", "").replace("必須", "")

        # キーワードベースのチェック
        keywords = [k.strip() for k in req_normalized.split("/") if k.strip()]

        if not keywords:
            keywords = [req_normalized]

        output_lower = output.lower()
        output_normalized = output_lower.replace(" ", "")

        for kw in keywords:
            # 直接マッチ
            if kw in output_lower or kw in output_normalized:
                return True
            # 英語キーワードもチェック
            mapping = {
                "handoff": ["handoff", "引き継ぎ", "前回"],
                "ki": ["knowledge", "ki", "知識"],
                "identitystack": ["identity", "persona", "アイデンティティ"],
                "変化追跡": ["変化", "差分", "delta", "'"],
                "全層展開": ["o-series", "s-series", "h-series", "6層"],
                "根拠": ["理由", "因", "reason"],
                "構造化": ["#", "##", "###"],
                "問い返し": ["?", "？", "問い"],
            }
            for key, synonyms in mapping.items():
                if kw in key or key in kw:
                    if any(
                        s in output_lower or s.replace(" ", "") in output_normalized
                        for s in synonyms
                    ):
                        return True

        return False

    # PURPOSE: ワークフロー出力の SEL 遵守を検証
    def validate(
        self, workflow: str, operator: str, output: str
    ) -> SELValidationResult:
        """ワークフロー出力の SEL 遵守を検証"""
        sel = self.load_sel_enforcement(workflow)

        if not sel:
            return SELValidationResult(
                workflow=workflow,
                operator=operator,
                is_compliant=True,
                score=1.0,
                details="sel_enforcement なし（検証スキップ）",
            )

        requirement = sel.get(operator)
        if not requirement:
            return SELValidationResult(
                workflow=workflow,
                operator=operator,
                is_compliant=True,
                score=1.0,
                details=f"演算子 {operator} の要件なし（検証スキップ）",
            )

        met = []
        missing = []

        for req in requirement.minimum_requirements:
            if self.check_requirement(req, output):
                met.append(req)
            else:
                missing.append(req)

        # UML requirements check
        uml_met = []
        uml_missing = []
        for stage, uml_req in requirement.uml_requirements.items():
            if self.check_requirement(uml_req, output):
                uml_met.append(f"{stage}: {uml_req}")
            else:
                uml_missing.append(f"{stage}: {uml_req}")

        total = len(requirement.minimum_requirements)
        score = len(met) / total if total > 0 else 1.0

        uml_total = len(requirement.uml_requirements)
        uml_score = len(uml_met) / uml_total if uml_total > 0 else 1.0

        # Combined compliance: SEL must pass, UML is supplementary
        is_compliant = len(missing) == 0

        return SELValidationResult(
            workflow=workflow,
            operator=operator,
            is_compliant=is_compliant,
            met_requirements=met,
            missing_requirements=missing,
            score=score,
            uml_score=uml_score,
            uml_met=uml_met,
            uml_missing=uml_missing,
            details=requirement.description,
        )

    def validate_requirements(
        self,
        workflow: str,
        operator: str,
        output: str,
        minimum_requirements: List[str],
        description: str = "",
        uml_requirements: Optional[Dict[str, str]] = None,
    ) -> SELValidationResult:
        """外部で構築した requirement 群を SEL と同じ形式で検証する。"""
        met = []
        missing = []
        uml_met = []
        uml_missing = []

        for req in minimum_requirements:
            if self.check_requirement(req, output):
                met.append(req)
            else:
                missing.append(req)

        for stage, uml_req in (uml_requirements or {}).items():
            if self.check_requirement(uml_req, output):
                uml_met.append(f"{stage}: {uml_req}")
            else:
                uml_missing.append(f"{stage}: {uml_req}")

        total = len(minimum_requirements)
        uml_total = len(uml_requirements or {})

        return SELValidationResult(
            workflow=workflow,
            operator=operator,
            is_compliant=len(missing) == 0,
            met_requirements=met,
            missing_requirements=missing,
            score=(len(met) / total) if total > 0 else 1.0,
            uml_score=(len(uml_met) / uml_total) if uml_total > 0 else 1.0,
            uml_met=uml_met,
            uml_missing=uml_missing,
            details=description,
        )

    # PURPOSE: 複数出力を一括検証
    def validate_batch(
        self, outputs: Dict[str, Dict[str, str]]
    ) -> List[SELValidationResult]:
        """複数出力を一括検証

        Args:
            outputs: {workflow: {operator: output}}
        """
        results = []
        for workflow, ops in outputs.items():
            for operator, output in ops.items():
                results.append(self.validate(workflow, operator, output))
        return results

    # PURPOSE: 検証レポートを生成
    def generate_report(self, results: List[SELValidationResult]) -> str:
        """検証レポートを生成"""
        total = len(results)
        compliant = sum(1 for r in results if r.is_compliant)
        avg_score = sum(r.score for r in results) / total if total > 0 else 0.0

        lines = [
            "═" * 60,
            "[Hegemonikón] SEL 遵守レポート",
            "═" * 60,
            f"",
            f"📊 遵守率: {compliant}/{total} ({compliant/total:.0%})",
            f"📊 平均スコア: {avg_score:.0%}",
            f"",
        ]

        if any(not r.is_compliant for r in results):
            lines.append("⚠️ 非遵守項目:")
            for r in results:
                if not r.is_compliant:
                    lines.append(
                        f"  - {r.workflow}{r.operator}: {r.missing_requirements}"
                    )

        lines.append("═" * 60)
        return "\n".join(lines)


# テスト用
if __name__ == "__main__":
    validator = SELValidator()

    # boot+ のテスト
    test_output = """
    ## Handoff 読込
    前回セッションの引き継ぎを読み込みました。
    
    ## KI 参照
    5件の Knowledge Items を参照しました。
    
    ## Identity Stack
    Persona プロファイルを読み込みました。
    """

    result = validator.validate("boot", "+", test_output)
    print(result.summary)
    print(f"満たした要件: {result.met_requirements}")
    print(f"不足要件: {result.missing_requirements}")
