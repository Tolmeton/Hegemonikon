from __future__ import annotations
#!/usr/bin/env python3
# PROOF: mekhane/basanos/l2/resolver.py
# PURPOSE: basanos モジュールの resolver
# PURPOSE: Basanos L3 自動解決ループ — deficit→問い→解決策の自動生成
# REASON: deficit を検出するだけでなく、解決への道筋を自動提案するため
"""Auto-resolution loop for Basanos L3.

Takes detected deficits, generates questions via L2, and uses LLM
to propose resolution strategies. Supports both Cortex (Gemini) and
local analysis fallbacks.
"""


import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mekhane.basanos.l2.models import Deficit, Question
from mekhane.ochema.model_defaults import FLASH

logger = logging.getLogger(__name__)


# PURPOSE: [L2-auto] Resolution のクラス定義
@dataclass
class Resolution:
    """Proposed resolution for a deficit."""

    question: Question
    strategy: str  # proposed resolution strategy
    confidence: float  # 0.0 - 1.0
    actions: list[str] = field(default_factory=list)  # concrete action items
    references: list[str] = field(default_factory=list)  # relevant files/docs
    status: str = "proposed"  # proposed, accepted, rejected, applied

    # PURPOSE: [L2-auto] to_dict の関数定義
    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-safe dict."""
        return {
            "question": self.question.text,
            "deficit_type": self.question.deficit.type.value,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "actions": self.actions,
            "references": self.references,
            "status": self.status,
        }


# PURPOSE: [L2-auto] Resolver のクラス定義
class Resolver:
    """L3 auto-resolution engine.

    Generates resolution strategies for deficits using:
    1. Rule-based heuristics (fast, no LLM)
    2. LLM-assisted analysis (via Cortex/Ochema, if available)
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self._heuristics = self._build_heuristics()

    # PURPOSE: [L2-auto] _build_heuristics の関数定義
    def _build_heuristics(self) -> dict[str, Any]:
        """Build rule-based resolution heuristics per deficit type."""
        return {
            "η": {
                "strategy_template": (
                    "外部論文「{source}」の概念を HGK に吸収する。"
                    "関連する Series を特定し、kernel/ に定義を追加するか、"
                    "既存の定理に紐付ける。"
                ),
                "actions": [
                    "/eat で外部概念を消化",
                    "kernel/ に新定義追加 or 既存定理に注釈追加",
                    "/dia で吸収後の整合性を検証",
                ],
                "confidence": 0.6,
            },
            "ε-impl": {
                "strategy_template": (
                    "kernel/{source} の定理 {target} に対応する実装を "
                    "mekhane/ に作成する。WF 定義も連動して追加。"
                ),
                "actions": [
                    "mekhane/ に実装モジュール作成",
                    "PROOF.md を同ディレクトリに配置",
                    "nous/workflows/ に対応 WF 作成",
                    "/dendron で存在証明チェック",
                ],
                "confidence": 0.7,
            },
            "ε-just": {
                "strategy_template": (
                    "{source} の主張「{target}」に学術的根拠を付与する。"
                    "Gnōsis 検索で関連論文を探索し、根拠を明示する。"
                ),
                "actions": [
                    "/sop で関連論文を調査",
                    "kernel/ ファイルに references セクション追加",
                    "Gnōsis KB に論文を登録",
                ],
                "confidence": 0.5,
            },
            "Δε/Δt": {
                "strategy_template": (
                    "最近の変更による {source} と {target} の不整合を解消する。"
                    "意図的な変更であれば、関連ファイルを連動更新する。"
                ),
                "actions": [
                    "git log で変更の意図を確認",
                    "関連する kernel/ or mekhane/ ファイルを連動更新",
                    "/vet で変更の整合性を再検証",
                ],
                "confidence": 0.5,
            },
        }

    # PURPOSE: [L2-auto] resolve_heuristic の関数定義
    def resolve_heuristic(self, deficit: Deficit) -> Resolution:
        """Generate resolution using rule-based heuristics (no LLM)."""
        question = deficit.to_question()
        type_key = deficit.type.value
        heuristic = self._heuristics.get(type_key, {})

        strategy_template = heuristic.get(
            "strategy_template",
            "{source} と {target} のズレを手動で解消する。",
        )
        strategy = strategy_template.format(
            source=deficit.source,
            target=deficit.target,
        )

        return Resolution(
            question=question,
            strategy=strategy,
            confidence=heuristic.get("confidence", 0.3),
            actions=heuristic.get("actions", []),
            references=self._find_references(deficit),
            status="proposed",
        )

    # PURPOSE: [L2-auto] _find_references の関数定義
    def _find_references(self, deficit: Deficit) -> list[str]:
        """Find relevant files for a deficit."""
        refs: list[str] = []

        # Check if source file exists
        source_path = self.project_root / deficit.source
        if source_path.exists():
            refs.append(str(source_path))

        # Check for related kernel files
        if deficit.target:
            for kernel_file in (self.project_root / "kernel").glob("*.md"):
                if deficit.target.lower() in kernel_file.stem.lower():
                    refs.append(str(kernel_file))

        return refs[:5]  # Limit references

    # PURPOSE: [L2-auto] resolve_batch の関数定義
    def resolve_batch(
        self,
        deficits: list[Deficit],
        max_resolutions: int = 10,
    ) -> list[Resolution]:
        """Resolve multiple deficits, prioritized by severity.

        Args:
            deficits: List of deficits to resolve
            max_resolutions: Maximum number of resolutions to generate

        Returns:
            List of Resolution objects, sorted by confidence (desc)
        """
        # Sort by severity (highest first)
        sorted_deficits = sorted(deficits, key=lambda d: d.severity, reverse=True)
        resolutions: list[Resolution] = []

        for deficit in sorted_deficits[:max_resolutions]:
            try:
                resolution = self.resolve_heuristic(deficit)
                resolutions.append(resolution)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to resolve deficit: %s — %s", deficit.description, exc)

        # Sort by confidence (highest first)
        resolutions.sort(key=lambda r: r.confidence, reverse=True)
        return resolutions

    # PURPOSE: [L2-auto] resolve_with_llm の非同期処理定義
    async def resolve_with_llm(
        self,
        deficit: Deficit,
        context: str = "",
    ) -> Resolution:
        """Resolve deficit using LLM via Cortex API (async).

        Falls back to heuristic if LLM is unavailable.
        """
        question = deficit.to_question()

        prompt = (
            f"Hegemonikón フレームワークの構造的欠陥を分析してください。\n\n"
            f"### 欠陥の種類: {deficit.type.value}\n"
            f"### 問い: {question.text}\n"
            f"### 説明: {deficit.description}\n"
            f"### ソース: {deficit.source}\n"
            f"### ターゲット: {deficit.target}\n"
            f"### 重大度: {deficit.severity:.1f}\n"
        )
        if context:
            prompt += f"\n### 追加コンテキスト:\n{context}\n"
        prompt += (
            "\n以下の形式で解決策を提案してください:\n"
            "1. **戦略**: 1-2文で解決の方向性\n"
            "2. **アクション**: 具体的な手順リスト (3-5項目)\n"
            "3. **確信度**: 0.0-1.0\n"
        )

        try:
            from mekhane.ochema.cortex import CortexClient

            client = CortexClient()
            response = await client.generate(
                prompt,
                model=FLASH,
                max_tokens=1024,
            )

            # Parse structured response
            text = response.get("text", "") if isinstance(response, dict) else str(response)

            return Resolution(
                question=question,
                strategy=text[:500],
                confidence=0.7,
                actions=self._extract_actions(text),
                references=self._find_references(deficit),
                status="proposed",
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("LLM resolution unavailable (%s), falling back to heuristic", exc)
            return self.resolve_heuristic(deficit)

    # PURPOSE: [L2-auto] _extract_actions の関数定義
    def _extract_actions(self, text: str) -> list[str]:
        """Extract action items from LLM response text."""
        actions: list[str] = []
        for line in text.split("\n"):
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("•") or
                         (len(line) > 2 and line[0].isdigit() and line[1] in ".)")):
                actions.append(line.lstrip("-•0123456789.) "))
        return actions[:5]


# PURPOSE: [L2-auto] print_resolutions の関数定義
def print_resolutions(resolutions: list[Resolution]) -> None:
    """Display resolutions in formatted output."""
    if not resolutions:
        print("\n✅ 解決提案なし（deficit が検出されていません）")
        return

    print(f"\n\033[1m━━━ Basanos L3: 自動解決提案 ({len(resolutions)} 件) ━━━\033[0m\n")

    for i, r in enumerate(resolutions, 1):
        conf_icon = "🟢" if r.confidence >= 0.7 else "🟡" if r.confidence >= 0.4 else "🔴"
        print(f"  {conf_icon} \033[1mR{i}\033[0m [{r.question.deficit.type.value}] conf={r.confidence:.1f}")
        print(f"     Q: {r.question.text}")
        print(f"     → {r.strategy}")
        if r.actions:
            print(f"     アクション:")
            for a in r.actions:
                print(f"       • {a}")
        if r.references:
            print(f"     \033[2m参照: {', '.join(r.references[:3])}\033[0m")
        print()
