# PROOF: [L2/インフラ] <- mekhane/basanos/prompt_generator.py A2→評議会システムが必要→prompt_generator が担う
#!/usr/bin/env python3
"""
Jules Basanos v2: Prompt Generator

Generated via /tek (tekhne-maker) using Hegemonikón Mode.

Theorem Mapping:
  - Primary: S4 Tekhnē (技法構築) — プロンプト生成手法
  - X-series: X-SA (Schema → Akribeia) — 手法から精度へ

Archetype: 🎯 Precision
  - Goal: 誤答率 < 1% in review findings
  - Sacrifice: Speed, Cost
  - Core Stack: CoVe (self-verification), WACK (knowledge check)
"""

import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# PURPOSE: の統一的インターフェースを実現する
@dataclass
# PURPOSE: A single orthogonal review perspective = Domain × Axis.
class Perspective:
    """A single orthogonal review perspective = Domain × Axis."""

    domain_id: str
    domain_name: str
    domain_description: str
    domain_keywords: list[str]
    axis_id: str
    axis_name: str
    axis_question: str
    axis_focus: str
    theorem: str

    # PURPOSE: prompt_generator の id 処理を実行する
    @property
    # PURPOSE: Unique perspective ID.
    def id(self) -> str:
        """Unique perspective ID."""
        return f"{self.domain_id}-{self.axis_id}"

    # PURPOSE: prompt_generator の name 処理を実行する
    @property
    # PURPOSE: Human-readable perspective name.
    def name(self) -> str:
        """Human-readable perspective name."""
        return f"{self.domain_name} × {self.axis_name}"
# PURPOSE: 20 Domains × 6 Axes = 120 Orthogonal Perspectives.


# PURPOSE: [L2-auto] PerspectiveMatrix のクラス定義
class PerspectiveMatrix:
    """
    20 Domains × 6 Axes = 120 Orthogonal Perspectives.

    Usage:
        matrix = PerspectiveMatrix.load()
        perspective = matrix.get("Resource", "O")
        prompt = matrix.generate_prompt(perspective)
    """

    # PURPOSE: PerspectiveMatrix の構成と依存関係の初期化
    def __init__(self, config: dict):
        self._config = config
        self._domains = {d["id"]: d for d in config["domains"]}
        self._axes = {a["id"]: a for a in config["axes"]}
        self._template = config["prompt_template"]

    # PURPOSE: prompt_generator の load 処理を実行する
    @classmethod
    # PURPOSE: Load perspective matrix from YAML.
    def load(cls, path: Optional[Path] = None) -> "PerspectiveMatrix":
        """Load perspective matrix from YAML."""
        if path is None:
            path = Path(__file__).parent / "perspectives.yaml"

        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return cls(config)

    # PURPOSE: prompt_generator の domains 処理を実行する
    @property
    # PURPOSE: List of domain IDs.
    def domains(self) -> list[str]:
        """List of domain IDs."""
        return list(self._domains.keys())

    # PURPOSE: prompt_generator の axes 処理を実行する
    @property
    # PURPOSE: List of axis IDs.
    def axes(self) -> list[str]:
        """List of axis IDs."""
        return list(self._axes.keys())

    # PURPOSE: prompt_generator の total perspectives 処理を実行する
    @property
    # PURPOSE: Total number of perspectives.
    def total_perspectives(self) -> int:
        """Total number of perspectives."""
        return len(self._domains) * len(self._axes)

    # PURPOSE: Get a specific perspective by domain and axis.
    def get(self, domain_id: str, axis_id: str) -> Perspective:
        """Get a specific perspective by domain and axis."""
        domain = self._domains.get(domain_id)
        axis = self._axes.get(axis_id)

        if domain is None:
            raise KeyError(f"Unknown domain: {domain_id}")
        if axis is None:
            raise KeyError(f"Unknown axis: {axis_id}")

        return Perspective(
            domain_id=domain["id"],
            domain_name=domain["name"],
            domain_description=domain["description"],
            domain_keywords=domain["keywords"],
            axis_id=axis["id"],
            axis_name=axis["name"],
            axis_question=axis["question"],
            axis_focus=axis["focus"],
            theorem=axis["theorem"],
        )

    # PURPOSE: Generate all 120 perspectives.
    def all_perspectives(self) -> list[Perspective]:
        """Generate all 120 perspectives."""
        perspectives = []
        for domain_id in self.domains:
            for axis_id in self.axes:
                perspectives.append(self.get(domain_id, axis_id))
        return perspectives

    # PURPOSE: Generate review prompt for a perspective.
    def generate_prompt(self, perspective: Perspective) -> str:
        """Generate review prompt for a perspective."""
        return self._template.format(
            domain_id=perspective.domain_id,
            domain_name=perspective.domain_name,
            domain_description=perspective.domain_description,
            domain_keywords=", ".join(perspective.domain_keywords),
            axis_id=perspective.axis_id,
            axis_name=perspective.axis_name,
            axis_question=perspective.axis_question,
            axis_focus=perspective.axis_focus,
            theorem=perspective.theorem,
        )

    # PURPOSE: Generate prompts for all 120 perspectives.
    def generate_all_prompts(self) -> dict[str, str]:
        """Generate prompts for all 120 perspectives."""
        prompts = {}
        for p in self.all_perspectives():
            prompts[p.id] = self.generate_prompt(p)
        return prompts

# PURPOSE: CLI entry point.
    # PURPOSE: Split perspectives into batches for rate limiting.
    def batch_perspectives(self, batch_size: int = 60) -> list[list[Perspective]]:
        """Split perspectives into batches for rate limiting."""
        all_p = self.all_perspectives()
        return [all_p[i : i + batch_size] for i in range(0, len(all_p), batch_size)]


# =============================================================================
# CLI for testing
# =============================================================================


# PURPOSE: CLI entry point
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Jules Basanos v2 Prompt Generator")
    parser.add_argument("--list", action="store_true", help="List all perspectives")
    parser.add_argument("--domain", help="Domain ID (e.g., Resource)")
    parser.add_argument("--axis", help="Axis ID (e.g., O)")
    parser.add_argument("--prompt", action="store_true", help="Generate prompt")
    args = parser.parse_args()

    matrix = PerspectiveMatrix.load()

    if args.list:
        print(f"Jules Basanos v2: {matrix.total_perspectives} Perspectives")
        print("=" * 60)
        print(f"\nDomains ({len(matrix.domains)}):")
        for d in matrix.domains:
            print(f"  - {d}")
        print(f"\nAxes ({len(matrix.axes)}):")
        for a in matrix.axes:
            print(f"  - {a}")
        print(f"\nBatches (size=60): {len(matrix.batch_perspectives())}")
        return

    if args.domain and args.axis:
        try:
            p = matrix.get(args.domain, args.axis)
            print(f"Perspective: {p.name}")
            print(f"ID: {p.id}")
            print(f"Theorem: {p.theorem}")

            if args.prompt:
                print("\n" + "=" * 60)
                print("PROMPT:")
                print("=" * 60)
                print(matrix.generate_prompt(p))
        except KeyError as e:
            print(f"Error: {e}")
            return

    if not args.list and not (args.domain and args.axis):
        parser.print_help()


if __name__ == "__main__":
    main()
