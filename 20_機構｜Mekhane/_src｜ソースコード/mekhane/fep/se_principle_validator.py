# PROOF: [L2/インフラ] <- mekhane/fep/se_principle_validator.py
"""
PROOF: [L2/インフラ]

A2 → 品質検証が必要
   → SE 5原則の構造的強制
   → se_principle_validator が担う

Q.E.D.

---

SE Principle Validator v1.0

SE 5原則の遵守を検証するスクリプト。
ワークフロー出力の必須フィールドを自動チェックし、違反時にブロック。

Usage:
    python se_principle_validator.py <filepath> --workflow <mek|s> [--scale <micro|meso|macro>]

Examples:
    python se_principle_validator.py output.md --workflow mek --scale meso
    python se_principle_validator.py output.md --workflow s
"""

from pathlib import Path
import re
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# PURPOSE: クラス: Scale
class Scale(Enum):
    MICRO = "micro"
    MESO = "meso"
    MACRO = "macro"


# PURPOSE: クラス: Severity
class Severity(Enum):
    ERROR = "error"  # ブロック
    WARNING = "warning"  # 警告のみ


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: クラス: Violation
class Violation:
    field: str
    principle: str
    severity: Severity
    message: str


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: クラス: ValidationResult
class ValidationResult:
    valid: bool
    violations: list[Violation]
    scale: Scale

    # PURPOSE: 検証結果のhuman-readable表示（PASS/FAIL+理由）
    def __str__(self) -> str:
        if self.valid:
            return f"✅ PASS (Scale: {self.scale.value})"

        lines = [f"❌ FAIL (Scale: {self.scale.value})"]
        for v in self.violations:
            icon = "⛔" if v.severity == Severity.ERROR else "⚠️"
            lines.append(f"  {icon} {v.field}: {v.message} [{v.principle}]")
        return "\n".join(lines)

# PURPOSE: SE 5原則の構造的強制を検証

# PURPOSE: [L2-auto] SEPrincipleValidator のクラス定義
class SEPrincipleValidator:
    """SE 5原則の構造的強制を検証"""

    # 必須パターン定義
    MEK_PATTERNS = {
        "fail_fast": {
            "pattern": r"##\s*失敗シナリオ",
            "principle": "早期失敗",
            "min_scale": Scale.MESO,
        },
        "iteration": {
            "pattern": r"→\s*\*?\*?初版\*?\*?",
            "principle": "反復",
            "min_scale": Scale.MICRO,
        },
        "timebox": {
            "pattern": r"⏱️.*所要時間.*\d+",
            "principle": "タイムボックス",
            "min_scale": Scale.MESO,
        },
    }

    S_PATTERNS = {
        "stage_0": {
            "pattern": r"STAGE\s*0:",
            "principle": "可視化",
            "min_scale": Scale.MICRO,
        },
        "stage_1": {
            "pattern": r"STAGE\s*1:",
            "principle": "可視化",
            "min_scale": Scale.MICRO,
        },
        "stage_2": {
            "pattern": r"STAGE\s*2:",
            "principle": "可視化",
            "min_scale": Scale.MICRO,
        },
        "stage_3": {
            "pattern": r"STAGE\s*3:",
            "principle": "可視化",
            "min_scale": Scale.MICRO,
        },
        "stage_4": {
            "pattern": r"STAGE\s*4:",
            "principle": "可視化",
            "min_scale": Scale.MICRO,
        },
        "stage_5": {
            "pattern": r"STAGE\s*5:",
            "principle": "可視化",
            "min_scale": Scale.MICRO,
        },
        "keep": {
            "pattern": r"Keep\s*[:|：]",
            "principle": "継続改善",
            "min_scale": Scale.MICRO,
        },
        "problem": {
            "pattern": r"Problem\s*[:|：]",
            "principle": "継続改善",
            "min_scale": Scale.MICRO,
        },
        "try": {
            "pattern": r"Try\s*[:|：]",
            "principle": "継続改善",
            "min_scale": Scale.MICRO,
        },
        "timebox": {
            "pattern": r"⏱️.*合計.*\d+.*m.*45",
            "principle": "タイムボックス",
            "min_scale": Scale.MESO,
        },
    }

    SCALE_ORDER = {Scale.MICRO: 0, Scale.MESO: 1, Scale.MACRO: 2}

    # PURPOSE: コンテンツからスケールを自動検出
    def detect_scale(self, content: str) -> Scale:
        """コンテンツからスケールを自動検出"""
        scale_patterns = [
            (r"Scale\s*[:|：]\s*🔬\s*Micro", Scale.MICRO),
            (r"Scale\s*[:|：]\s*🔭\s*Meso", Scale.MESO),
            (r"Scale\s*[:|：]\s*🌍\s*Macro", Scale.MACRO),
            (r"Micro", Scale.MICRO),
            (r"Meso", Scale.MESO),
            (r"Macro", Scale.MACRO),
        ]

        for pattern, scale in scale_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return scale

        # デフォルトは Meso
        return Scale.MESO

    # PURPOSE: 現在のスケールでこのフィールドをチェックすべきか
    def should_check(self, field_min_scale: Scale, current_scale: Scale) -> bool:
        """現在のスケールでこのフィールドをチェックすべきか"""
        return self.SCALE_ORDER[current_scale] >= self.SCALE_ORDER[field_min_scale]

    # PURPOSE: ファイルを検証
    def validate(
        self, filepath: Path, workflow: str, scale: Optional[Scale] = None
    ) -> ValidationResult:
        """ファイルを検証"""
        content = filepath.read_text(encoding="utf-8")

        # スケール検出または指定
        detected_scale = scale or self.detect_scale(content)

        # パターン選択
        patterns = self.MEK_PATTERNS if workflow == "mek" else self.S_PATTERNS

        violations = []

        for field, config in patterns.items():
            if not self.should_check(config["min_scale"], detected_scale):
                continue

            if not re.search(config["pattern"], content, re.IGNORECASE):
                severity = (
                    Severity.ERROR
                    if detected_scale == Scale.MACRO
                    else Severity.WARNING
                )

                # Micro でも必須のものは ERROR
                if config["min_scale"] == Scale.MICRO:
                    severity = Severity.ERROR

                violations.append(
                    Violation(
                        field=field,
                        principle=config["principle"],
                        severity=severity,
                        message=f"パターン '{config['pattern']}' が見つかりません",
                    )
                )

        # ERROR があれば invalid
        has_errors = any(v.severity == Severity.ERROR for v in violations)

        return ValidationResult(
            valid=not has_errors,
            violations=violations,
# PURPOSE: CLI起動: 指定ディレクトリのSE原則検証を実行
            scale=detected_scale,
        )


# PURPOSE: se_principle_validator の main 処理を実行する
def main():
    if len(sys.argv) < 4:
        print(
            "Usage: python se_principle_validator.py <filepath> --workflow <mek|s> [--scale <micro|meso|macro>]"
        )
        sys.exit(1)

    filepath = Path(sys.argv[1])
    workflow = None
    scale = None

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--workflow":
            workflow = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--scale":
            scale = Scale(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    if not filepath.exists():
        print(f"❌ ファイルが見つかりません: {filepath}")
        sys.exit(1)

    if workflow not in ("mek", "s"):
        print(f"❌ workflow は 'mek' または 's' を指定してください")
        sys.exit(1)

    validator = SEPrincipleValidator()
    result = validator.validate(filepath, workflow, scale)

    print(result)

    if not result.valid:
        print("\n⛔ SE原則違反: ブロック")
        print("   修正後に再実行してください")
        sys.exit(1)
    else:
        print("\n✅ SE原則: 全パス")


if __name__ == "__main__":
    main()
