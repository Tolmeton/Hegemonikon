from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/plan_recorder.py
# PURPOSE: 計画完了時の通知・記録・違反チェックを行う層6サブスクライバ
"""
PlanRecorderSubscriber — 計画完了時の記録と通知

層6: 計画実行完了後に以下の HGK 機構を統合する
  - Notifications (S6): 計画完了の通知送信
  - ViolationDashboard (S5): Anti-Shallow Gate 違反の記録
  - Chronos (M4): 計画の自動記録

発火条件:
    - MACRO_COMPLETE イベント
    - マクロ名が "plan" を含む
"""

import logging
from typing import Optional

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


class PlanRecorderSubscriber(BaseSubscriber):
    """計画完了時の記録・通知・違反チェック

    FEP 同型: 経験の永続化 — 計画が完了した時点で、
    その経験を記憶に書き込み、システムの予測モデルを更新する。
    """

    def __init__(
        self,
        fire_threshold: float = 0.0,
        notifications_enabled: bool = True,
        violation_check_enabled: bool = True,
    ):
        super().__init__(
            name="plan_recorder",
            policy=ActivationPolicy(
                event_types={EventType.MACRO_COMPLETE},
                custom_predicate=self._is_plan_macro,
            ),
            fire_threshold=fire_threshold,
        )
        self._notifications_enabled = notifications_enabled
        self._violation_check_enabled = violation_check_enabled
        self._plans_recorded = 0

    @staticmethod
    def _is_plan_macro(event: CognitionEvent) -> bool:
        """@plan, @plan-, @plan+ のいずれかか"""
        name = event.metadata.get("macro_name", "")
        return "plan" in name.lower()

    def score(self, event: CognitionEvent) -> float:
        """計画完了は常に記録価値あり"""
        s = 1.0
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """通知・記録・違反チェック"""
        parts: list[str] = []
        output = ""
        if event.step_result and hasattr(event.step_result, "output"):
            output = event.step_result.output or ""

        # 1. Anti-Shallow Gate 違反チェック
        if self._violation_check_enabled:
            violations = self._check_anti_shallow(output)
            if violations:
                parts.append(violations)

        # 2. 完了通知
        if self._notifications_enabled:
            notify_result = self._send_notification(event)
            if notify_result:
                parts.append(notify_result)

        self._plans_recorded += 1

        if not parts:
            return f"[📝 Plan #{self._plans_recorded} recorded]"

        return "\n\n".join(parts)

    def _check_anti_shallow(self, output: str) -> Optional[str]:
        """Anti-Shallow Gate の基本チェック"""
        issues: list[str] = []

        # Negativa チェック: 「棄却」「❌」が含まれるか
        if "棄却" not in output and "❌" not in output:
            issues.append("Negativa 不足: 棄却候補の記述がない")

        # Trace チェック: 「なぜ」「理由」が含まれるか
        if "なぜ" not in output and "理由" not in output and "根拠" not in output:
            issues.append("Trace 不足: 順序の理由説明がない")

        # 弱点チェック
        if "弱点" not in output and "リスク" not in output and "深刻度" not in output:
            issues.append("検証不足: 弱点・リスクの記述がない")

        if issues:
            # pure-Python: violations.jsonl に直接書き出し
            try:
                import json
                from pathlib import Path
                from datetime import datetime, timezone
                viol_file = Path(__file__).parent.parent.parent.parent/ "30_記憶｜Mneme" / "01_記録｜Records" / "e_ログ_logs" / "violations.jsonl"
                viol_file.parent.mkdir(parents=True, exist_ok=True)
                for issue in issues:
                    entry = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "type": "self_detected",
                        "description": f"Anti-Shallow Gate: {issue}",
                        "bc_ids": ["S-I"],
                        "pattern": "shallow_plan",
                    }
                    with open(viol_file, "a", encoding="utf-8") as f:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except Exception as e:  # noqa: BLE001
                logger.debug("Violation logging failed: %s", e)

            lines = ["[⚠️ Anti-Shallow Gate 違反]"]
            for issue in issues:
                lines.append(f"  - {issue}")
            return "\n".join(lines)

        return None

    def _send_notification(self, event: CognitionEvent) -> Optional[str]:
        """計画完了通知を送信"""
        # pure-Python: notifications.jsonl に直接書き出し
        try:
            import json
            from pathlib import Path
            from datetime import datetime, timezone
            macro_name = event.metadata.get("macro_name", "plan")
            notif_file = Path(__file__).parent.parent.parent.parent/ "30_記憶｜Mneme" / "01_記録｜Records" / "e_ログ_logs" / "notifications.jsonl"
            notif_file.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": "INFO",
                "source": "plan_recorder",
                "title": f"計画完了: @{macro_name}",
                "body": f"CCL 実行完了。計画 #{self._plans_recorded + 1}",
                "dismissed": False,
            }
            with open(notif_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:  # noqa: BLE001
            logger.debug("Notification failed: %s", e)
        return None

    @property
    def plans_recorded(self) -> int:
        return self._plans_recorded
