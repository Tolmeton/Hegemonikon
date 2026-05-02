#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ H4→永続化を自動化
"""
/bye 永続化自動化スクリプト

persistence.md の9ステップを一括実行する。
各ステップは独立して失敗可能で、失敗しても次へ進む。

Usage:
    python scripts/bye_persist.py                  # 全ステップ実行
    python scripts/bye_persist.py --steps 1,2,3    # 指定ステップのみ
    python scripts/bye_persist.py --dry-run         # 実行せず確認
"""

from __future__ import annotations

import argparse
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ─── Result tracking ───

@dataclass
class StepResult:
    name: str
    step_num: int
    success: bool
    message: str = ""
    error: Optional[str] = None


@dataclass
class PersistReport:
    results: list[StepResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success)

    def summary(self) -> str:
        lines = [f"\n{'═'*50}", f"永続化レポート: {self.passed}/{len(self.results)} 成功"]
        for r in self.results:
            icon = "✅" if r.success else "❌"
            lines.append(f"  {icon} Step {r.step_num}: {r.name}")
            if r.message:
                lines.append(f"     → {r.message}")
            if r.error:
                lines.append(f"     ⚠ {r.error[:80]}")
        return "\n".join(lines)


# ─── Individual steps ───

def step_1_kairos() -> str:
    """Kairos インデックス投入"""
    import subprocess
    script = PROJECT_ROOT / "mekhane" / "symploke" / "kairos_ingest.py"
    if not script.exists():
        return "Kairos script not found (skipped)"
    result = subprocess.run(
        [sys.executable, str(script), "--all"],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True, timeout=120,
        env={**__import__("os").environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )
    if result.returncode == 0:
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        return lines[-1] if lines else "Kairos ingest complete"
    return f"Kairos script failed: {result.stderr[:100]}"


def step_2_handoff_index() -> str:
    """Handoff インデックス再構築"""
    from mekhane.symploke.handoff_search import build_handoff_index, load_handoffs
    docs = load_handoffs()
    adapter = build_handoff_index(docs)
    count = len(docs) if docs else 0
    return f"Handoff index: {count} docs"


def step_3_persona() -> str:
    """Persona 更新"""
    from mekhane.symploke.persona import update_persona
    persona = update_persona(session_increment=1, trust_delta=0.01)
    sessions = persona.get("relationship", {}).get("sessions_together", "?")
    return f"Persona: {sessions} sessions"


def step_4_sophia() -> str:
    """Sophia 同期 (KI 吸収)"""
    import subprocess
    script = PROJECT_ROOT / "mekhane" / "symploke" / "sophia_ingest.py"
    if not script.exists():
        return "Sophia script not found (skipped)"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True, timeout=120,
        env={**__import__("os").environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )
    if result.returncode == 0:
        # Extract last meaningful line
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        return lines[-1] if lines else "Sophia sync complete"
    raise RuntimeError(result.stderr[:200])


def step_5_fep_a_matrix() -> str:
    """FEP A行列永続化"""
    a_matrix_path = Path.home() / "oikos/mneme/.hegemonikon/fep/a_matrix.npy"
    a_matrix_path.parent.mkdir(parents=True, exist_ok=True)

    # Try v2 agent first
    try:
        from mekhane.fep.fep_agent_v2 import HegemonikónFEPAgentV2
        agent = HegemonikónFEPAgentV2()
        if a_matrix_path.exists():
            agent.load_learned_A(str(a_matrix_path))
        agent.save_learned_A(str(a_matrix_path))
        return f"FEP v2 A-matrix: {a_matrix_path}"
    except ImportError:
        pass

    # Fallback to v1
    from mekhane.fep import HegemonikónFEPAgent
    agent = HegemonikónFEPAgent(use_defaults=True)
    import numpy as np
    np.save(str(a_matrix_path), agent.A)
    return f"FEP v1 A-matrix: {a_matrix_path}"


def step_6_wf_inventory() -> str:
    """ワークフロー一覧更新"""
    import subprocess
    script = PROJECT_ROOT / "mekhane" / "anamnesis" / "workflow_inventory.py"
    if not script.exists():
        return "WF inventory script not found (skipped)"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(PROJECT_ROOT),
        capture_output=True, text=True, timeout=60,
        env={**__import__("os").environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )
    if result.returncode == 0:
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        return lines[-1] if lines else "WF inventory updated"
    raise RuntimeError(result.stderr[:200])


def step_7_meaningful_traces() -> str:
    """意味ある瞬間の保存"""
    try:
        from mekhane.fep.meaningful_traces import save_traces, get_session_traces
        traces = get_session_traces()
        if traces:
            saved_path = save_traces()
            return f"Meaningful traces: {len(traces)} 件 → {saved_path}"
        return "No meaningful traces in this session"
    except ImportError:
        return "meaningful_traces module not available (skipped)"


def step_8_derivative_selection() -> str:
    """派生選択学習永続化"""
    try:
        from mekhane.fep.derivative_selector import SELECTION_LOG_PATH
        if not SELECTION_LOG_PATH.exists():
            return "No derivative selections this session"

        import yaml
        from mekhane.fep.doxa_persistence import get_store, BeliefStrength
        with open(SELECTION_LOG_PATH) as f:
            selections = yaml.safe_load(f).get("selections", [])
        store = get_store()
        high_conf = [s for s in selections if s.get("confidence", 0) >= 0.80]
        for sel in high_conf:
            content = f"{sel['theorem']}:{sel['derivative']} = {sel['problem'][:50]}"
            store.persist(content, BeliefStrength.STRONG, sel["confidence"])
        return f"Derivative learning: {len(high_conf)} persisted"
    except ImportError:
        return "derivative_selector not available (skipped)"


def step_9_x_series() -> str:
    """X-series 使用経路記録"""
    # X-series routes are collected during session — check if any exist
    x_routes_path = Path.home() / "oikos/mneme/.hegemonikon/fep/x_routes.yaml"
    if not x_routes_path.exists():
        return "No X-series routes this session"
    try:
        import yaml
        from mekhane.fep.doxa_persistence import get_store, BeliefStrength
        with open(x_routes_path) as f:
            routes = yaml.safe_load(f) or []
        store = get_store()
        for r in routes:
            content = f"X-{r['from']}{r['to']}: success={r.get('rate', 0.5):.2f}"
            strength = BeliefStrength.STRONG if r.get("rate", 0) >= 0.8 else BeliefStrength.MODERATE
            store.persist(content, strength, r.get("rate", 0.5))
        return f"X-series: {len(routes)} routes persisted"
    except Exception as e:
        return f"X-series: error ({e})"


# ─── Registry ───

STEPS: list[tuple[int, str, Callable[[], str]]] = [
    (1, "Kairos インデックス", step_1_kairos),
    (2, "Handoff インデックス", step_2_handoff_index),
    (3, "Persona 更新", step_3_persona),
    (4, "Sophia 同期", step_4_sophia),
    (5, "FEP A行列", step_5_fep_a_matrix),
    (6, "WF一覧更新", step_6_wf_inventory),
    (7, "意味ある瞬間", step_7_meaningful_traces),
    (8, "派生選択学習", step_8_derivative_selection),
    (9, "X-series 経路", step_9_x_series),
]


# ─── Main ───

def run_persist(steps: list[int] | None = None, dry_run: bool = False) -> PersistReport:
    """Run persistence steps.

    Args:
        steps: Specific step numbers to run (None = all)
        dry_run: If True, only show which steps would run
    """
    report = PersistReport()

    for num, name, func in STEPS:
        if steps and num not in steps:
            continue

        if dry_run:
            print(f"  🔍 Step {num}: {name} (would run)")
            continue

        print(f"  ▶ Step {num}: {name}...", end=" ", flush=True)
        try:
            msg = func()
            report.results.append(StepResult(name, num, True, msg))
            print(f"✅ {msg}")
        except Exception as e:
            err = traceback.format_exc()
            report.results.append(StepResult(name, num, False, error=str(e)))
            print(f"❌ {e}")

    return report


def main():
    parser = argparse.ArgumentParser(description="/bye 永続化自動実行")
    parser.add_argument(
        "--steps", type=str, default=None,
        help="実行するステップ番号 (カンマ区切り, e.g. 1,2,5)"
    )
    parser.add_argument("--dry-run", action="store_true", help="実行せず確認")
    args = parser.parse_args()

    step_nums = None
    if args.steps:
        step_nums = [int(s.strip()) for s in args.steps.split(",")]

    print("📦 /bye 永続化開始...\n")
    report = run_persist(steps=step_nums, dry_run=args.dry_run)

    if not args.dry_run:
        print(report.summary())
        sys.exit(0 if report.failed == 0 else 1)


if __name__ == "__main__":
    main()
