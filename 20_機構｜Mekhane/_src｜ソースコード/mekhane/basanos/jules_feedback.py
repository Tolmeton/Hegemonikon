# PROOF: [L1/定理] <- mekhane/basanos/jules_feedback.py VISION.md 第2段階: 対話する免疫
"""
JulesFeedback — L2 Jules の結果を L0 Basanos にフィードバックする。

FEP 解釈:
- Jules fix = 予測誤差の解消 → L0 の該当チェッカーの精度を維持/上昇
- Jules false_positive = 偽陽性 → L0 の該当チェッカーの精度を下降
- Jules partial = 部分的修正 → 判断保留

設計:
- パイプラインは非同期: 今回の実行で Jules を起動 → 次回の実行で結果を回収
- pending_sessions.json で追跡
- 結果は feedback_history.json に蓄積
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from mekhane.paths import OUTPUTS_DIR

FEEDBACK_DIR = OUTPUTS_DIR / "jules_feedback"
PENDING_FILE = FEEDBACK_DIR / "pending_sessions.json"
HISTORY_FILE = FEEDBACK_DIR / "feedback_history.json"


# PURPOSE: [L2-auto] FeedbackEntry のクラス定義
@dataclass
class FeedbackEntry:
    """1つの Jules セッションからのフィードバック。"""

    session_id: str
    date: str
    verdict: str  # "fix", "false_positive", "partial", "error", "pending"
    issues_reviewed: int = 0
    issues_fixed: int = 0
    issues_dismissed: int = 0  # false positives
    checker_adjustments: Dict[str, float] = field(default_factory=dict)
    # {checker_code: adjustment} e.g. {"AI-001": -0.1} = reduce weight

    # PURPOSE: [L2-auto] to_dict の関数定義
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "date": self.date,
            "verdict": self.verdict,
            "issues_reviewed": self.issues_reviewed,
            "issues_fixed": self.issues_fixed,
            "issues_dismissed": self.issues_dismissed,
            "checker_adjustments": self.checker_adjustments,
        }

    # PURPOSE: [L2-auto] from_dict の関数定義
    @classmethod
    def from_dict(cls, d: dict) -> "FeedbackEntry":
        return cls(
            session_id=d.get("session_id", ""),
            date=d.get("date", ""),
            verdict=d.get("verdict", "pending"),
            issues_reviewed=d.get("issues_reviewed", 0),
            issues_fixed=d.get("issues_fixed", 0),
            issues_dismissed=d.get("issues_dismissed", 0),
            checker_adjustments=d.get("checker_adjustments", {}),
        )


# PURPOSE: [L2-auto] JulesFeedback のクラス定義
class JulesFeedback:
    """Jules L2 結果を L0 Basanos にフィードバックする。

    Usage:
        fb = JulesFeedback()
        fb.register_session("session-123", issues=[...])
        # ... later (next pipeline run) ...
        completed = fb.collect_completed()
        adjustments = fb.compute_adjustments()
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, feedback_dir: Path = FEEDBACK_DIR):
        self.feedback_dir = feedback_dir
        self.pending_file = feedback_dir / "pending_sessions.json"
        self.history_file = feedback_dir / "feedback_history.json"
        self._ensure_dir()

    # PURPOSE: [L2-auto] _ensure_dir の関数定義
    def _ensure_dir(self) -> None:
        self.feedback_dir.mkdir(parents=True, exist_ok=True)

    # PURPOSE: [L2-auto] _load_pending の関数定義
    def _load_pending(self) -> List[dict]:
        if self.pending_file.exists():
            try:
                return json.loads(self.pending_file.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                return []
        return []

    # PURPOSE: [L2-auto] _save_pending の関数定義
    def _save_pending(self, sessions: List[dict]) -> None:
        self.pending_file.write_text(
            json.dumps(sessions, ensure_ascii=False, indent=2), "utf-8"
        )

    # PURPOSE: [L2-auto] _load_history の関数定義
    def _load_history(self) -> List[dict]:
        if self.history_file.exists():
            try:
                return json.loads(self.history_file.read_text("utf-8"))
            except (json.JSONDecodeError, OSError):
                return []
        return []

    # PURPOSE: [L2-auto] _save_history の関数定義
    def _save_history(self, entries: List[dict]) -> None:
        self.history_file.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2), "utf-8"
        )

    # PURPOSE: [L2-auto] register_session の関数定義
    def register_session(
        self,
        session_id: str,
        issues: List[dict],
    ) -> None:
        """Jules セッションを pending に登録。

        Args:
            session_id: Jules session ID
            issues: L0 issues that triggered L2
        """
        pending = self._load_pending()

        # Deduplicate
        if any(s.get("session_id") == session_id for s in pending):
            logger.debug(f"Session {session_id} already registered")
            return

        pending.append({
            "session_id": session_id,
            "registered_at": datetime.now().isoformat(),
            "issue_codes": [i.get("code", "") for i in issues],
            "issue_count": len(issues),
        })
        self._save_pending(pending)
        logger.info(f"Registered Jules session: {session_id} ({len(issues)} issues)")

    # PURPOSE: [L2-auto] collect_completed の関数定義
    def collect_completed(self) -> List[FeedbackEntry]:
        """完了した Jules セッションの結果を回収して分類。

        Returns:
            FeedbackEntry のリスト (verdict: fix/false_positive/partial/error)
        """
        pending = self._load_pending()
        if not pending:
            return []

        completed = []
        still_pending = []

        for session in pending:
            sid = session.get("session_id", "")
            result = self._check_session_status(sid)

            if result is None:
                # Still running or API unavailable
                still_pending.append(session)
                continue

            verdict, details = result

            entry = FeedbackEntry(
                session_id=sid,
                date=datetime.now().strftime("%Y-%m-%d"),
                verdict=verdict,
                issues_reviewed=session.get("issue_count", 0),
                issues_fixed=details.get("fixed", 0),
                issues_dismissed=details.get("dismissed", 0),
                checker_adjustments=self._compute_checker_adjustments(
                    session.get("issue_codes", []),
                    verdict,
                    details,
                ),
            )
            completed.append(entry)

        # Update pending (remove completed)
        self._save_pending(still_pending)

        # Append to history
        if completed:
            history = self._load_history()
            history.extend(e.to_dict() for e in completed)
            self._save_history(history)
            logger.info(f"Collected {len(completed)} completed Jules sessions")

        return completed

    # PURPOSE: [L2-auto] _check_session_status の関数定義
    def _check_session_status(
        self, session_id: str
    ) -> Optional[tuple]:
        """Jules セッションの状態を確認。

        Returns:
            None if still pending, or (verdict, details_dict)
        """
        try:
            import asyncio
            from mekhane.symploke.jules_client import JulesClient, SessionState
            import os

            api_key = None
            for i in range(1, 10):
                key = os.environ.get(f"JULES_API_KEY_{i:02d}")
                if key:
                    api_key = key
                    break

            if not api_key:
                logger.debug("No Jules API key, cannot check session status")
                return None

            # PURPOSE: [L2-auto] _poll の非同期処理定義
            async def _poll():
                async with JulesClient(api_key) as client:
                    session = await client.get_session(session_id)
                    return session

            session = asyncio.run(_poll())

            # Classify result
            state = session.state
            if state == SessionState.COMPLETED:
                # Check if it created changes
                has_changes = bool(session.plan and session.plan.steps)
                if has_changes:
                    return ("fix", {"fixed": len(session.plan.steps)})
                else:
                    return ("false_positive", {"dismissed": 1})
            elif state == SessionState.FAILED:
                return ("error", {})
            elif state == SessionState.CANCELLED:
                return ("false_positive", {"dismissed": 1})
            else:
                # Still running
                return None

        except ImportError:
            logger.debug("JulesClient not available")
            return None
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Session check failed for {session_id}: {e}")
            return None

    # PURPOSE: [L2-auto] _compute_checker_adjustments の関数定義
    def _compute_checker_adjustments(
        self,
        issue_codes: List[str],
        verdict: str,
        details: dict,
    ) -> Dict[str, float]:
        """チェッカー別の精度調整値を計算。

        - fix → 精度維持 (adjustment = 0 or +0.05)
        - false_positive → 精度下降 (adjustment = -0.1)
        - error → 判断しない (adjustment = 0)
        """
        adjustments: Dict[str, float] = {}

        if verdict == "fix":
            # Jules が修正した → チェッカーは正しかった → 微増
            for code in issue_codes:
                adjustments[code] = adjustments.get(code, 0) + 0.05
        elif verdict == "false_positive":
            # Jules が不要と判断 → チェッカーが偽陽性 → 減少
            for code in issue_codes:
                adjustments[code] = adjustments.get(code, 0) - 0.1
        # partial, error → no adjustment

        return adjustments

    # PURPOSE: [L2-auto] compute_cumulative_adjustments の関数定義
    def compute_cumulative_adjustments(self, days: int = 30) -> Dict[str, float]:
        """過去N日の feedback_history から累積チェッカー調整値を算出。"""
        history = self._load_history()
        if not history:
            return {}

        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        cumulative: Dict[str, float] = {}

        for entry_dict in history:
            if entry_dict.get("date", "") < cutoff:
                continue

            for code, adj in entry_dict.get("checker_adjustments", {}).items():
                cumulative[code] = cumulative.get(code, 0) + adj

        # Clamp to [-1.0, 1.0]
        for code in cumulative:
            cumulative[code] = max(-1.0, min(1.0, round(cumulative[code], 3)))

        return cumulative

    # PURPOSE: [L2-auto] apply_to_rotation の関数定義
    def apply_to_rotation(self, state: "RotationState") -> Dict[str, Any]:
        """累積調整値を RotationState に適用。

        Returns:
            変更サマリ dict。
        """
        adjustments = self.compute_cumulative_adjustments()
        changes: Dict[str, Any] = {"adjustments_applied": {}}

        if not adjustments:
            return changes

        for code, adj in adjustments.items():
            # Map issue codes to domain categories
            category = code.split("-")[0] if "-" in code else code
            domain_map = {
                "AI": "Naming",  # AI-001 etc → Naming domain
                "GIT": "Git",
            }
            domain = domain_map.get(category, category)

            if domain in state.domains:
                old_w = state.domains[domain].weight
                new_w = max(0.1, min(2.0, old_w + adj * 0.5))
                state.domains[domain].weight = round(new_w, 3)
                changes["adjustments_applied"][domain] = {
                    "old": old_w,
                    "new": round(new_w, 3),
                    "from_code": code,
                    "cumulative_adj": adj,
                }

        if changes["adjustments_applied"]:
            logger.info(f"Jules feedback: {len(changes['adjustments_applied'])} domain adjustments")

        return changes

    # PURPOSE: [L2-auto] summary の関数定義
    def summary(self) -> str:
        """フィードバック履歴の要約。"""
        history = self._load_history()
        if not history:
            return "📊 Jules Feedback: No sessions completed yet."

        verdicts = {}
        for e in history:
            v = e.get("verdict", "unknown")
            verdicts[v] = verdicts.get(v, 0) + 1

        lines = [
            f"📊 Jules Feedback ({len(history)} sessions)",
        ]
        for v, count in sorted(verdicts.items()):
            icon = {"fix": "✅", "false_positive": "❌", "partial": "⚠️", "error": "💥"}.get(v, "❓")
            lines.append(f"   {icon} {v}: {count}")

        adjustments = self.compute_cumulative_adjustments()
        if adjustments:
            lines.append("   Checker adjustments:")
            for code, adj in sorted(adjustments.items()):
                direction = "↑" if adj > 0 else "↓"
                lines.append(f"      {code}: {direction}{abs(adj):.2f}")

        return "\n".join(lines)


# PURPOSE: [L2] GateResult — 品質関門の1段階の結果
@dataclass
class GateResult:
    """品質関門の1ステージの結果。"""

    stage: str  # "spec_compliance" | "code_quality"
    passed: bool
    issues: List[dict] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "passed": self.passed,
            "issues": self.issues,
            "details": self.details,
        }


# PURPOSE: [L2] SequentialQualityGate — 直列2段品質関門
class SequentialQualityGate:
    """直列2段品質関門: Spec Compliance → Code Quality。

    Stage 1 (Spec Compliance) を通過しない限り Stage 2 に進まない。
    /ccl-vet から呼ばれる Python 実装。

    Usage:
        gate = SequentialQualityGate()
        results = gate.run(diff_text, spec={"planned_files": [...]})
        if all(r.passed for r in results):
            print("All gates passed")
    """

    # PURPOSE: [L2] run — 品質関門パイプラインを実行
    def run(
        self,
        diff: str,
        spec: Optional[Dict[str, Any]] = None,
        changed_files: Optional[List[str]] = None,
    ) -> List[GateResult]:
        """品質関門を直列実行。

        Args:
            diff: git diff の出力テキスト
            spec: 仕様情報 (planned_files, planned_deletions 等)
            changed_files: 変更されたファイルの絶対パスリスト

        Returns:
            GateResult のリスト。Stage 1 不合格時は1要素のみ。
        """
        results: List[GateResult] = []

        # Stage 1: Spec Compliance
        spec_result = self._check_spec_compliance(diff, spec or {})
        results.append(spec_result)

        if not spec_result.passed:
            logger.info("Stage 1 (Spec Compliance) failed — Stage 2 blocked")
            return results

        # Stage 2: Code Quality
        quality_result = self._check_code_quality(diff, changed_files or [])
        results.append(quality_result)

        return results

    # PURPOSE: [L2] _check_spec_compliance — Stage 1: 仕様準拠チェック
    def _check_spec_compliance(
        self, diff: str, spec: Dict[str, Any]
    ) -> GateResult:
        """diff が仕様 (implementation_plan) と合致するか検証。"""
        issues: List[dict] = []

        if not diff or not diff.strip():
            issues.append({
                "code": "SPEC-001",
                "message": "diff が空です。変更がありません。",
                "severity": "error",
            })
            return GateResult(
                stage="spec_compliance",
                passed=False,
                issues=issues,
                details={"reason": "empty_diff"},
            )

        # diff からファイルリストを抽出
        changed_in_diff = self._extract_files_from_diff(diff)

        # 計画されたファイルと照合
        planned_files = spec.get("planned_files", [])
        if planned_files:
            # 計画にあるが diff にないファイル
            missing = [f for f in planned_files if f not in changed_in_diff]
            if missing:
                issues.append({
                    "code": "SPEC-002",
                    "message": f"計画にあるが未変更: {missing}",
                    "severity": "warning",
                })

            # diff にあるが計画にないファイル (想定外の変更)
            unexpected = [f for f in changed_in_diff if f not in planned_files]
            if unexpected:
                issues.append({
                    "code": "SPEC-003",
                    "message": f"計画外の変更: {unexpected}",
                    "severity": "info",
                })

        # 計画された削除ファイルの確認
        planned_deletions = spec.get("planned_deletions", [])
        for del_file in planned_deletions:
            if del_file not in changed_in_diff:
                issues.append({
                    "code": "SPEC-004",
                    "message": f"削除予定だが未削除: {del_file}",
                    "severity": "warning",
                })

        # error レベルの issue があれば不合格
        has_errors = any(i["severity"] == "error" for i in issues)

        return GateResult(
            stage="spec_compliance",
            passed=not has_errors,
            issues=issues,
            details={
                "files_in_diff": len(changed_in_diff),
                "files_planned": len(planned_files),
            },
        )

    # PURPOSE: [L2] _check_code_quality — Stage 2: コード品質チェック
    def _check_code_quality(
        self, diff: str, changed_files: List[str]
    ) -> GateResult:
        """Basanos L0 + Dendron PROOF で品質検証。"""
        issues: List[dict] = []
        details: Dict[str, Any] = {}

        # Basanos L0 静的解析
        basanos_issues = self._run_basanos_l0(changed_files)
        if basanos_issues:
            issues.extend(basanos_issues)
            details["basanos_count"] = len(basanos_issues)

        # Dendron PROOF チェック
        dendron_issues = self._run_dendron_check(changed_files)
        if dendron_issues:
            issues.extend(dendron_issues)
            details["dendron_count"] = len(dendron_issues)

        has_errors = any(i.get("severity") == "error" for i in issues)

        return GateResult(
            stage="code_quality",
            passed=not has_errors,
            issues=issues,
            details=details,
        )

    # PURPOSE: [L2] _extract_files_from_diff — diff テキストからファイル名を抽出
    @staticmethod
    def _extract_files_from_diff(diff: str) -> List[str]:
        """git diff 出力からファイルパスを抽出。"""
        import re

        files = []
        for line in diff.splitlines():
            # 'diff --git a/path b/path' or '+++ b/path'
            m = re.match(r"^\+\+\+ b/(.+)$", line)
            if m:
                files.append(m.group(1))
        return files

    # PURPOSE: [L2] _run_basanos_l0 — AST 構文チェック (py compile)
    @staticmethod
    def _run_basanos_l0(changed_files: List[str]) -> List[dict]:
        """変更ファイルに対して L0 構文チェック (ast.parse) を実行。"""
        import ast as _ast

        issues: List[dict] = []
        py_files = [f for f in changed_files if f.endswith(".py")]

        for filepath in py_files:
            path = Path(filepath)
            if not path.exists():
                continue
            try:
                source = path.read_text(encoding="utf-8")
                _ast.parse(source, filename=str(path))
            except SyntaxError as e:
                issues.append({
                    "code": "L0-SYNTAX",
                    "message": f"{path.name}:{e.lineno}: {e.msg}",
                    "severity": "error",
                    "source": "basanos_l0",
                })
            except Exception as e:  # noqa: BLE001
                issues.append({
                    "code": "L0-READ",
                    "message": f"{path.name}: {e}",
                    "severity": "warning",
                    "source": "basanos_l0",
                })

        return issues

    # PURPOSE: [L2] _run_dendron_check — Dendron PROOF/PURPOSE チェックの実行
    @staticmethod
    def _run_dendron_check(changed_files: List[str]) -> List[dict]:
        """変更ファイルに対して Dendron PROOF ヘッダー + PURPOSE コメントを検証。"""
        issues: List[dict] = []
        py_files = [f for f in changed_files if f.endswith(".py")]

        if not py_files:
            return issues

        try:
            from mekhane.dendron.checker import DendronChecker
            from mekhane.dendron.models import ProofStatus

            checker = DendronChecker(check_functions=True)
            for filepath in py_files:
                path = Path(filepath)
                if not path.exists():
                    continue

                # L1: PROOF ヘッダーチェック
                file_proof = checker.check_file_proof(path)
                if file_proof.status == ProofStatus.MISSING:
                    issues.append({
                        "code": "DENDRON-PROOF",
                        "message": f"{path.name}: PROOF ヘッダーなし",
                        "severity": "warning",
                        "source": "dendron",
                    })
                elif file_proof.status == ProofStatus.INVALID:
                    issues.append({
                        "code": "DENDRON-PROOF",
                        "message": f"{path.name}: {file_proof.reason}",
                        "severity": "error",
                        "source": "dendron",
                    })

                # L2: PURPOSE コメントチェック
                func_proofs = checker.check_functions_in_file(path)
                missing_purposes = [
                    fp for fp in func_proofs
                    if fp.status == ProofStatus.MISSING and not fp.is_private
                ]
                if missing_purposes:
                    names = [fp.name for fp in missing_purposes[:3]]
                    suffix = f" (+{len(missing_purposes) - 3})" if len(missing_purposes) > 3 else ""
                    issues.append({
                        "code": "DENDRON-PURPOSE",
                        "message": f"{path.name}: PURPOSE なし: {', '.join(names)}{suffix}",
                        "severity": "warning",
                        "source": "dendron",
                    })
        except ImportError:
            logger.debug("DendronChecker not available for PROOF check")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Dendron check failed: {e}")

        return issues

    # PURPOSE: [L2] summary — 品質関門の結果サマリ
    @staticmethod
    def format_results(results: List[GateResult]) -> str:
        """GateResult リストを人間可読な文字列に整形。"""
        lines = ["📋 Sequential Quality Gate Results:"]
        for r in results:
            icon = "✅" if r.passed else "❌"
            stage_name = {
                "spec_compliance": "Stage 1: Spec Compliance",
                "code_quality": "Stage 2: Code Quality",
            }.get(r.stage, r.stage)
            lines.append(f"  {icon} {stage_name}")
            for issue in r.issues:
                sev_icon = {"error": "🔴", "warning": "🟡", "info": "🔵"}.get(
                    issue.get("severity", ""), "⚪"
                )
                lines.append(f"    {sev_icon} [{issue.get('code', '')}] {issue.get('message', '')}")

        all_passed = all(r.passed for r in results)
        lines.append(f"\n  {'🟢 All gates passed' if all_passed else '🔴 Gate blocked'}")
        return "\n".join(lines)
