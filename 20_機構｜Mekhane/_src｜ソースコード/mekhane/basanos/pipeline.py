# PROOF: [L1/定理] <- mekhane/basanos/pipeline.py VISION.md A→B→C の具体化パイプライン
"""
DailyReviewPipeline — Basanos L0 → Synteleia L1 → Jules L2 → Feedback

VISION.md Layer A (Immunitas) → Layer B (Nous) → Layer C (Pronoia) の
具体的実装。設計判断は FEP π(ε) の操作化:
- L2 発動 = CRITICAL/HIGH (= ε が閾値超過)
- 重み = π の蓄積で自動調整
- 段階的実装 = 累積原則
"""

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from mekhane.basanos.ai_auditor import AIAuditor, AuditResult as BasanosResult, Issue, Severity
from mekhane.synteleia.base import (
    AuditIssue,
    AuditSeverity,
    AuditTarget,
    AuditTargetType,
)

logger = logging.getLogger(__name__)

# Default path
ROTATION_STATE_PATH = Path(__file__).parent.parent.parent / "synergeia" / "basanos_rotation_state.json"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Adapter: Basanos Issue → Synteleia AuditIssue
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Severity mapping
_SEVERITY_MAP = {
    Severity.CRITICAL: AuditSeverity.CRITICAL,
    Severity.HIGH: AuditSeverity.HIGH,
    Severity.MEDIUM: AuditSeverity.MEDIUM,
    Severity.LOW: AuditSeverity.LOW,
}


# PURPOSE: [L2-auto] basanos_issue_to_synteleia の関数定義
def basanos_issue_to_synteleia(issue: Issue, file_path: str = "") -> AuditIssue:
    """Basanos Issue → Synteleia AuditIssue に変換。"""
    return AuditIssue(
        agent=f"basanos/{issue.code}",
        code=issue.code,
        severity=_SEVERITY_MAP.get(issue.severity, AuditSeverity.LOW),
        message=issue.message,
        location=f"{file_path}:{issue.line}" if file_path else f"L{issue.line}",
        suggestion=issue.suggestion,
    )


# PURPOSE: [L2-auto] basanos_to_synteleia_target の関数定義
def basanos_to_synteleia_target(basanos_result: BasanosResult) -> AuditTarget:
    """Basanos AuditResult → Synteleia AuditTarget に変換。"""
    content = basanos_result.file_path.read_text(encoding="utf-8")
    return AuditTarget(
        content=content,
        target_type=AuditTargetType.CODE,
        source=str(basanos_result.file_path),
        metadata={
            "basanos_issues": len(basanos_result.issues),
            "has_critical": basanos_result.has_critical,
            "has_high": basanos_result.has_high,
        },
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Domain Weights — π(ε) の蓄積
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PURPOSE: [L2-auto] DomainWeight のクラス定義
@dataclass
class DomainWeight:
    """ドメインの重み — 過去の問題頻度に基づく精度加重。"""
    name: str
    weight: float = 1.0  # 1.0 = 標準、>1 = 要注意、<1 = 安定
    last_issues: int = 0  # 前回の issue 数
    total_issues: int = 0  # 累計 issue 数
    last_reviewed: Optional[str] = None


# PURPOSE: [L2-auto] RotationState のクラス定義
@dataclass
class RotationState:
    """basanos_rotation_state.json の拡張版。"""
    domains: Dict[str, DomainWeight] = field(default_factory=dict)
    cycle: int = 0
    last_date: str = ""

    # PURPOSE: [L2-auto] load の関数定義
    @classmethod
    def load(cls, path: Path = ROTATION_STATE_PATH) -> "RotationState":
        """JSON から読込。旧形式にも対応。"""
        if not path.exists():
            return cls()

        with open(path) as f:
            data = json.load(f)

        state = cls(cycle=data.get("cycle", 0), last_date=data.get("last_date", ""))

        # Handle both old format (last_domains list) and new format (domains dict)
        if "domains" in data and isinstance(data["domains"], dict):
            # New weighted format
            for name, info in data["domains"].items():
                state.domains[name] = DomainWeight(
                    name=name,
                    weight=info.get("weight", 1.0),
                    last_issues=info.get("last_issues", 0),
                    total_issues=info.get("total_issues", 0),
                    last_reviewed=info.get("last_reviewed"),
                )
        elif "last_domains" in data:
            # Old format — migrate
            for name in data["last_domains"]:
                state.domains[name] = DomainWeight(name=name)

        return state

    # PURPOSE: [L2-auto] save の関数定義
    def save(self, path: Path = ROTATION_STATE_PATH) -> None:
        """JSON に保存。"""
        data = {
            "domains": {
                name: {
                    "weight": dw.weight,
                    "last_issues": dw.last_issues,
                    "total_issues": dw.total_issues,
                    "last_reviewed": dw.last_reviewed,
                }
                for name, dw in self.domains.items()
            },
            "cycle": self.cycle,
            "last_date": self.last_date,
            # Backward compat — keep last_domains list
            "last_domains": list(self.domains.keys()),
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # PURPOSE: [L2-auto] select_domains の関数定義
    def select_domains(self, n: int = 3) -> List[str]:
        """重み付きでドメインを選択。重みが高い = ε が大きい = 優先。"""
        if not self.domains:
            return []
        sorted_domains = sorted(
            self.domains.values(),
            key=lambda d: d.weight,
            reverse=True,
        )
        return [d.name for d in sorted_domains[:n]]

    # PURPOSE: [L2-auto] update_weights の関数定義
    def update_weights(self, domain: str, issue_count: int, decay: float = 0.9) -> None:
        """π(ε) 更新: 問題が多い → 重み上昇、少ない → 減衰。"""
        if domain not in self.domains:
            self.domains[domain] = DomainWeight(name=domain)

        dw = self.domains[domain]
        dw.last_issues = issue_count
        dw.total_issues += issue_count
        dw.last_reviewed = datetime.now().strftime("%Y-%m-%d")

        # Weight update: exponential moving average
        # More issues → higher weight (needs more attention)
        if issue_count > 0:
            dw.weight = min(3.0, dw.weight + 0.1 * issue_count)
        else:
            dw.weight = max(0.3, dw.weight * decay)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pipeline Result
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PURPOSE: [L2-auto] PipelineResult のクラス定義
@dataclass
class PipelineResult:
    """パイプライン全体の結果。"""
    files_scanned: int = 0
    l0_issues: List[Dict[str, Any]] = field(default_factory=list)  # Basanos findings
    l1_results: List[Dict[str, Any]] = field(default_factory=list)  # Synteleia findings
    l2_triggered: bool = False  # Jules deep review triggered?
    l2_session_id: Optional[str] = None  # Jules session ID if triggered
    domains_reviewed: List[str] = field(default_factory=list)

    # PURPOSE: [L2-auto] needs_l2 の関数定義
    @property
    def needs_l2(self) -> bool:
        """L2 発動条件: CRITICAL or HIGH が存在 = ε が閾値超過。"""
        return any(
            i.get("severity") in ("critical", "high")
            for i in self.l0_issues
        )

    # PURPOSE: [L2-auto] to_jules_prompt の関数定義
    def to_jules_prompt(self, max_issues: int = 10, context_lines: int = 5) -> str:
        """Jules に渡す深掘りレビュー用プロンプトを生成。

        Args:
            max_issues: 含める最大 issue 数
            context_lines: 問題箇所の前後に含める行数
        """
        critical_high = [
            i for i in self.l0_issues
            if i.get("severity") in ("critical", "high")
        ][:max_issues]

        prompt_parts = [
            "## Deep Review Request (自動生成)",
            "",
            "Basanos L0 + Synteleia L1 の分析で以下の重要な問題が検出されました。",
            "各問題について根本原因を分析し、修正案を提示してください。",
            "",
            "### 検出された問題",
            "",
        ]

        for i, issue in enumerate(critical_high, 1):
            location = issue.get("location", "?")
            prompt_parts.append(
                f"{i}. **[{issue.get('severity', '?').upper()}] {issue.get('code', '?')}** "
                f"at `{location}`"
            )
            prompt_parts.append(f"   {issue.get('message', '')}")
            if issue.get("suggestion"):
                prompt_parts.append(f"   → 提案: {issue['suggestion']}")

            # Attach source code context
            snippet = self._extract_snippet(location, context_lines)
            if snippet:
                prompt_parts.append("")
                prompt_parts.append(f"   ```python")
                prompt_parts.append(snippet)
                prompt_parts.append(f"   ```")

            prompt_parts.append("")

        return "\n".join(prompt_parts)

    # PURPOSE: [L2-auto] _extract_snippet の関数定義
    @staticmethod
    def _extract_snippet(location: str, context_lines: int = 5) -> str:
        """location 文字列 (e.g. "path/to/file.py:42") からコード断片を抽出。"""
        try:
            if ":" not in location:
                return ""
            parts = location.rsplit(":", 1)
            file_path = Path(parts[0])
            line_no = int(parts[1])

            if not file_path.exists() or file_path.stat().st_size > 500_000:
                return ""

            lines = file_path.read_text("utf-8").splitlines()
            start = max(0, line_no - context_lines - 1)
            end = min(len(lines), line_no + context_lines)

            numbered = []
            for idx in range(start, end):
                marker = ">>>" if idx == line_no - 1 else "   "
                numbered.append(f"   {marker} {idx + 1:4d} | {lines[idx]}")

            return "\n".join(numbered)
        except Exception:  # noqa: BLE001
            return ""


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DailyReviewPipeline — Main Orchestrator
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PURPOSE: [L2-auto] DailyReviewPipeline のクラス定義
class DailyReviewPipeline:
    """
    Daily Review Pipeline — VISION.md A→B→C の具体化。

    L0 (Basanos): AST-based static analysis
    L1 (Synteleia): Cognitive auditing (pattern-based agents)
    L2 (Jules): Deep LLM review (triggered by CRITICAL/HIGH)
    FB: Feedback to rotation weights
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(
        self,
        project_root: Optional[Path] = None,
        rotation_state_path: Path = ROTATION_STATE_PATH,
        enable_l2: bool = True,
    ):
        self.project_root = project_root or Path.cwd()
        self.rotation_state = RotationState.load(rotation_state_path)
        self.rotation_state_path = rotation_state_path
        self.enable_l2 = enable_l2
        self.auditor = AIAuditor(strict=False)  # CRITICAL/HIGH only
        self._synteleia = None

    # PURPOSE: [L2-auto] synteleia の関数定義
    @property
    def synteleia(self):
        """Lazy-load Synteleia orchestrator."""
        if self._synteleia is None:
            from mekhane.synteleia.orchestrator import SynteleiaOrchestrator
            self._synteleia = SynteleiaOrchestrator()
        return self._synteleia

    # PURPOSE: [L2-auto] run の関数定義
    def run(
        self,
        files: Optional[List[Path]] = None,
        domains: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> PipelineResult:
        """
        パイプラインを実行。

        Args:
            files: 対象ファイルリスト (None = git diff から自動検出)
            domains: レビュードメイン (None = 重み付き自動選択)
            dry_run: True = L2 発動せず結果のみ返す
        """
        result = PipelineResult()

        # Resolve domains
        if domains is None:
            domains = self.rotation_state.select_domains(n=3)
        result.domains_reviewed = domains

        # Resolve files
        if files is None:
            files = self._discover_changed_files()

        logger.info(f"Pipeline: {len(files)} files, domains={domains}")

        # ── L0: Basanos static analysis ──
        for file_path in files:
            if not file_path.suffix == ".py":
                continue
            try:
                basanos_result = self.auditor.audit_file(file_path)
                result.files_scanned += 1

                for issue in basanos_result.issues:
                    result.l0_issues.append({
                        "code": issue.code,
                        "name": issue.name,
                        "severity": issue.severity.value,
                        "line": issue.line,
                        "message": issue.message,
                        "suggestion": issue.suggestion,
                        "file": str(file_path),
                        "location": f"{file_path}:{issue.line}",
                    })

            except Exception as e:  # noqa: BLE001
                logger.warning(f"L0 audit failed for {file_path}: {e}")

        # ── L1: Synteleia cognitive audit (for files with L0 issues) ──
        files_with_issues = {
            i["file"] for i in result.l0_issues
            if i["severity"] in ("critical", "high")
        }
        for file_str in files_with_issues:
            try:
                file_path = Path(file_str)
                basanos_result = self.auditor.audit_file(file_path)
                target = basanos_to_synteleia_target(basanos_result)
                synteleia_result = self.synteleia.audit(target)

                result.l1_results.append({
                    "file": file_str,
                    "passed": synteleia_result.passed,
                    "issues": len(synteleia_result.all_issues),
                    "summary": synteleia_result.summary,
                })

            except Exception as e:  # noqa: BLE001
                logger.warning(f"L1 audit failed for {file_str}: {e}")

        # ── L2: Jules deep review (if CRITICAL/HIGH detected) ──
        if result.needs_l2 and self.enable_l2 and not dry_run:
            result.l2_triggered = True
            result.l2_session_id = self._trigger_jules_review(result)
            # Register session for feedback tracking
            if result.l2_session_id:
                self._register_jules_session(result)

        # ── Auto-expand: 新ドメイン自動検出 ──
        self._auto_expand_domains(result)

        # ── FB: Feedback loop — update weights ──
        self._update_feedback(result, domains)

        # ── Notify: Sympatheia 通知 ──
        self._notify_result(result)

        # ── Persist: レポート永続化 ──
        if not dry_run:
            self._persist_report(result)

        # ── Trend: 蓄積データからの学習 (G7/G8) ──
        if not dry_run:
            self._apply_trends()

        # ── Git: churn 予兆検知 ──
        if not dry_run:
            self._git_risk_check(result)

        # ── Jules Feedback: L2結果→L0精度調整 ──
        if not dry_run:
            self._collect_jules_feedback()

        return result

    # PURPOSE: [L2-auto] _discover_changed_files の関数定義
    def _discover_changed_files(self) -> List[Path]:
        """git diff から変更されたファイルを検出。"""
        import subprocess
        try:
            output = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True, text=True,
                cwd=self.project_root,
            )
            if output.returncode == 0:
                return [
                    self.project_root / f.strip()
                    for f in output.stdout.strip().split("\n")
                    if f.strip() and f.strip().endswith(".py")
                ]
        except Exception as e:  # noqa: BLE001
            logger.warning(f"git diff failed: {e}")
        return []

    # PURPOSE: [L2-auto] _auto_expand_domains の関数定義
    def _auto_expand_domains(self, result: PipelineResult) -> None:
        """L0 結果から未登録ドメインを自動追加。"""
        # AI-XXX code → name mapping for domain categorization
        CATEGORY_MAP = {
            "Naming": "Naming",
            "API": "API",
            "Type": "Types",
            "Logic": "Logic",
            "Incomplete": "Completeness",
            "Context": "Context",
            "Pattern": "Patterns",
            "Contradiction": "Logic",
            "Security": "Security",
            "Input": "Validation",
            "Boundary": "Boundary",
            "Async": "Async",
            "Concurrency": "Concurrency",
            "Comment": "Documentation",
            "Copy": "DRY",
            "Dead": "DeadCode",
            "Magic": "Magic",
            "Hardcoded": "Config",
        }
        for issue in result.l0_issues:
            name = issue.get("name", "")
            # Extract first word as category key
            key = name.split()[0] if name else ""
            domain = CATEGORY_MAP.get(key, "")
            if domain and domain not in self.rotation_state.domains:
                self.rotation_state.domains[domain] = DomainWeight(name=domain, weight=0.8)
                logger.info(f"Auto-expanded domain: {domain} (from {name})")

    # PURPOSE: [L2-auto] _trigger_jules_review の関数定義
    def _trigger_jules_review(self, result: PipelineResult) -> Optional[str]:
        """Jules API 経由で深掘りレビューを発動。"""
        try:
            import asyncio
            from mekhane.symploke.jules_client import JulesClient

            # API key from environment
            api_key = None
            for i in range(1, 10):
                key = os.environ.get(f"JULES_API_KEY_{i:02d}")
                if key:
                    api_key = key
                    break

            if not api_key:
                logger.warning("L2: No JULES_API_KEY_XX found, skipping")
                return None

            repo = os.environ.get("JULES_REPO", "Tolmeton/oikos")
            prompt = result.to_jules_prompt()
            logger.info(f"L2 triggered: {len(result.l0_issues)} issues → Jules ({repo})")

            # PURPOSE: [L2-auto] _create の非同期処理定義
            async def _create():
                client = JulesClient(api_key)
                source = f"sources/github/{repo}"
                session = await client.create_session(prompt, source, "main")
                return session.id

            session_id = asyncio.run(_create())
            logger.info(f"L2 session created: {session_id}")
            return session_id

        except ImportError:
            logger.warning("L2: JulesClient not available")
            return None
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Jules trigger failed: {e}")
            return None

    # PURPOSE: [L2-auto] _apply_trends の関数定義
    def _apply_trends(self) -> None:
        """G7/G8: 蓄積データからの学習を適用。"""
        try:
            from mekhane.basanos.trend_analyzer import TrendAnalyzer

            analyzer = TrendAnalyzer(days=14)
            changes = analyzer.apply_to_rotation(self.rotation_state)

            if changes.get("weight_adjustments"):
                self.rotation_state.save(self.rotation_state_path)
                logger.info(f"Trend learning: {len(changes['weight_adjustments'])} adjustments")
            else:
                logger.debug("Trend learning: no adjustments needed")

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Trend analysis failed (non-fatal): {e}")

    # PURPOSE: [L2-auto] _register_jules_session の関数定義
    def _register_jules_session(self, result: PipelineResult) -> None:
        """Jules セッションを feedback 追跡に登録。"""
        try:
            from mekhane.basanos.jules_feedback import JulesFeedback

            fb = JulesFeedback()
            critical_issues = [
                i for i in result.l0_issues
                if i.get("severity") in ("critical", "high")
            ]
            fb.register_session(result.l2_session_id, critical_issues)
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Jules session registration skipped: {e}")

    # PURPOSE: [L2-auto] _collect_jules_feedback の関数定義
    def _collect_jules_feedback(self) -> None:
        """前回の Jules セッション結果を回収し L0 精度を調整。"""
        try:
            from mekhane.basanos.jules_feedback import JulesFeedback

            fb = JulesFeedback()
            completed = fb.collect_completed()

            if completed:
                changes = fb.apply_to_rotation(self.rotation_state)
                if changes.get("adjustments_applied"):
                    self.rotation_state.save(self.rotation_state_path)
                    logger.info(f"Jules feedback: {len(changes['adjustments_applied'])} adjustments")
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Jules feedback collection skipped: {e}")

    # PURPOSE: [L2-auto] _git_risk_check の関数定義
    def _git_risk_check(self, result: PipelineResult) -> None:
        """Git churn + TrendAnalyzer の交差で予兆検知。"""
        try:
            from mekhane.basanos.git_metrics import GitMetrics

            gm = GitMetrics(repo_root=self.project_root, days=14)
            risky = gm.risky_files(top_n=5)

            if risky:
                # TrendAnalyzer の hot files と交差させる
                try:
                    from mekhane.basanos.trend_analyzer import TrendAnalyzer
                    ta = TrendAnalyzer(days=14)
                    hot_paths = [fp.path for fp in ta.hot_files(top_n=10)]
                    overlaps = gm.hotspot_overlaps(hot_paths)
                except Exception:  # noqa: BLE001
                    overlaps = []

                git_summary = gm.summary()
                result.l0_issues.append({
                    "file": "",
                    "name": "Git Risk Alert",
                    "code": "GIT-001",
                    "severity": "info",
                    "location": "",
                    "description": git_summary,
                    "risky_files": [{"path": fc.path, "risk": round(fc.risk_score, 1)} for fc in risky[:3]],
                    "hotspot_overlaps": overlaps,
                })
                if overlaps:
                    logger.warning(f"⚠️ Hotspot overlap: {overlaps}")

        except Exception as e:  # noqa: BLE001
            logger.debug(f"Git risk check skipped: {e}")

    # PURPOSE: [L2-auto] _update_feedback の関数定義
    def _update_feedback(self, result: PipelineResult, domains: List[str]) -> None:
        """フィードバックループ: 重みを更新して保存。"""
        # Count issues per domain (approximate mapping)
        issue_count = len(result.l0_issues)

        for domain in domains:
            # Simple heuristic: distribute issues across reviewed domains
            domain_issues = issue_count // max(len(domains), 1)
            self.rotation_state.update_weights(domain, domain_issues)

        # Update cycle
        self.rotation_state.cycle += 1
        self.rotation_state.last_date = datetime.now().strftime("%Y-%m-%d")

        # Save
        self.rotation_state.save(self.rotation_state_path)

    # PURPOSE: [L2-auto] _notify_result の関数定義
    def _notify_result(self, result: PipelineResult) -> None:
        """Sympatheia notifications.jsonl に結果を送信。"""
        try:
            from mekhane.api.routes.sympatheia import _send_notification
            level = "HIGH" if result.needs_l2 else "INFO"
            icon = "🚨" if result.needs_l2 else "📋"
            _send_notification(
                source="DailyReview",
                level=level,
                title=f"{icon} Daily Review: {result.files_scanned} files, {len(result.l0_issues)} issues",
                body=self.summary(result),
                data={
                    "files_scanned": result.files_scanned,
                    "l0_issues": len(result.l0_issues),
                    "l2_triggered": result.l2_triggered,
                    "domains": result.domains_reviewed,
                },
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Sympatheia notification failed: {e}")

    # PURPOSE: [L2-auto] _persist_report の関数定義
    def _persist_report(self, result: PipelineResult) -> Optional[Path]:
        """daily_reviews/YYYY-MM-DD.json に結果を保存。"""
        try:
            from mekhane.paths import OUTPUTS_DIR
            report_dir = OUTPUTS_DIR / "daily_reviews"
            report_dir.mkdir(parents=True, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            report_file = report_dir / f"{today}.json"

            report = {
                "timestamp": datetime.now().isoformat(),
                "files_scanned": result.files_scanned,
                "l0_issues": result.l0_issues,
                "l1_results": result.l1_results,
                "l2_triggered": result.l2_triggered,
                "l2_session_id": result.l2_session_id,
                "domains_reviewed": result.domains_reviewed,
                "needs_l2": result.needs_l2,
                "summary": self.summary(result),
            }

            # Append mode: same day runs get merged
            if report_file.exists():
                existing = json.loads(report_file.read_text("utf-8"))
                if isinstance(existing, list):
                    existing.append(report)
                else:
                    existing = [existing, report]
                report_file.write_text(
                    json.dumps(existing, ensure_ascii=False, indent=2), "utf-8"
                )
            else:
                report_file.write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), "utf-8"
                )

            logger.info(f"Report saved: {report_file}")
            return report_file
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Report persist failed: {e}")
            return None


    # PURPOSE: [L2-auto] summary の関数定義
    def summary(self, result: PipelineResult) -> str:
        """パイプライン結果のサマリーを生成。"""
        lines = [
            "━━━ Daily Review Pipeline ━━━",
            f"📁 Files scanned: {result.files_scanned}",
            f"🔍 L0 (Basanos): {len(result.l0_issues)} issues",
            f"🧠 L1 (Synteleia): {len(result.l1_results)} files reviewed",
            f"🤖 L2 (Jules): {'triggered' if result.l2_triggered else 'not needed'}",
            f"📊 Domains: {', '.join(result.domains_reviewed)}",
        ]

        # Issue breakdown
        severity_counts = {}
        for issue in result.l0_issues:
            sev = issue["severity"]
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        if severity_counts:
            lines.append("┌─ Issue Breakdown ─┐")
            for sev in ["critical", "high", "medium", "low"]:
                if sev in severity_counts:
                    icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}[sev]
                    lines.append(f"│ {icon} {sev}: {severity_counts[sev]}")
            lines.append("└───────────────────┘")

        return "\n".join(lines)
