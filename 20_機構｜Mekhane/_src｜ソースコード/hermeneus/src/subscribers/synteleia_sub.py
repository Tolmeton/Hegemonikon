from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/synteleia_sub.py
"""
SynteleiaSubscriber — 構造的品質の L0 スキャン

段階 2 (読取専用): ステップ出力の構造的品質を静的に解析し、
問題があればアラートを生成する。出力には干渉しない。

検出対象:
    - 空出力または極端に短い出力
    - 構造化されていないテキスト (テーブル/リストなし)
    - 未解決の参照 (TODO, FIXME, TBD)
    - 確信度表明の欠如

リスク: 極低 (読取専用、副作用なし)
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)

# Sekisho 連携用アラート永続化パス (Mneme State と同じ場所)
try:
    from mekhane.paths import MNEME_STATE
    _ALERT_FILE = MNEME_STATE / "synteleia_alerts.jsonl"
except ImportError:
    _ALERT_FILE = Path.home() / ".hegemonikon" / "state" / "synteleia_alerts.jsonl"


@dataclass
class QualityAlert:
    """品質アラート"""
    level: str  # "warning" | "error"
    category: str
    message: str
    source_node: str = ""


class SynteleiaSubscriber(BaseSubscriber):
    """ステップ出力の構造的品質を L0 スキャンする subscriber

    STEP_COMPLETE イベントを受け取り、出力テキストの品質を評価する。
    問題があれば QualityAlert を蓄積し、サマリーを返す。

    L0 = AST ベース静的解析 (LLM 不要)。高速で安全。
    """

    # 品質チェックの閾値
    MIN_OUTPUT_CHARS = 50      # 最小出力文字数
    MIN_STRUCTURE_SCORE = 0.3  # 最小構造化スコア

    # 未解決参照パターン
    UNRESOLVED_PATTERNS = re.compile(
        r'\b(?:TODO|FIXME|TBD|XXX|HACK|PLACEHOLDER|未定|要確認)\b',
        re.IGNORECASE,
    )

    def __init__(self, fire_threshold: float = 0.4):
        super().__init__(
            name="synteleia_l0",
            policy=ActivationPolicy(
                event_types={EventType.STEP_COMPLETE},
            ),
            fire_threshold=fire_threshold,  # Phase 3b: スコアが0.4以上なら自律的に品質スキャン
        )
        self._alerts: List[QualityAlert] = []

    def score(self, event: CognitionEvent) -> float:
        """エントロピーが高いほど品質スキャンの価値が高い

        Phase 3: 不確実性が高い出力ほど品質問題を含みやすい
        Phase 4a: Convergence が苦戦している (高スコア痕跡) ならスキャン価値を高める
        """
        # エントロピーが高い = 品質リスクが高い = スキャン価値が高い
        entropy_score = min(event.entropy_after, 1.0)
        # 過去のアラート率も考慮
        alert_bonus = min(len(self._alerts) * 0.1, 0.3) if self._alerts else 0.0
        
        # Phase 4a: Stigmergy 文脈依存 (Convergence との横の相互作用)
        stigmergy_bonus = 0.0
        if getattr(self, "stigmergy_context", None):
            conv_traces = self.stigmergy_context.get_traces_by_subscriber("convergence_tracker", limit=3)
            if conv_traces:
                # convergence が低類似度 = 高 intensity で痕跡を残している場合、品質スキャン価値を高める
                avg_conv_intensity = sum(t.intensity for t in conv_traces) / len(conv_traces)
                stigmergy_bonus = min(avg_conv_intensity * 0.3, 0.3)

        s = min(entropy_score + alert_bonus + stigmergy_bonus, 1.0)
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """出力の品質を L0 スキャン"""
        result = event.step_result
        if result is None:
            return None

        output = result.output if hasattr(result, 'output') else ""
        node_id = result.node_id if hasattr(result, 'node_id') else event.source_node

        alerts_before = len(self._alerts)

        # Check 1: 空出力
        if not output or len(output.strip()) < self.MIN_OUTPUT_CHARS:
            self._alerts.append(QualityAlert(
                level="warning",
                category="empty_output",
                message=f"出力が短すぎます ({len(output.strip())} chars < {self.MIN_OUTPUT_CHARS})",
                source_node=node_id,
            ))

        # Check 2: 構造化度
        structure_score = self._evaluate_structure(output)
        if structure_score < self.MIN_STRUCTURE_SCORE and len(output) > 100:
            self._alerts.append(QualityAlert(
                level="warning",
                category="low_structure",
                message=f"構造化度が低い (score={structure_score:.2f} < {self.MIN_STRUCTURE_SCORE})",
                source_node=node_id,
            ))

        # Check 3: 未解決参照
        unresolved = self.UNRESOLVED_PATTERNS.findall(output)
        if unresolved:
            self._alerts.append(QualityAlert(
                level="warning",
                category="unresolved_refs",
                message=f"未解決参照: {', '.join(set(unresolved))}",
                source_node=node_id,
            ))

        # Check 4: エントロピー増大 (逆拡散に逆行)
        if hasattr(result, 'entropy_before') and hasattr(result, 'entropy_after'):
            if result.entropy_after > result.entropy_before + 0.1:
                self._alerts.append(QualityAlert(
                    level="error",
                    category="entropy_increase",
                    message=(
                        f"エントロピー増大 ({result.entropy_before:.3f} → "
                        f"{result.entropy_after:.3f}) — 逆拡散に逆行"
                    ),
                    source_node=node_id,
                ))

        new_alerts = len(self._alerts) - alerts_before
        if new_alerts > 0:
            logger.info(
                "Synteleia L0: %d alerts for %s",
                new_alerts,
                node_id,
            )

        # Phase 4a: 環境に痕跡を残す (他 subscriber へのシグナル)
        self.leave_trace(
            event=event,
            payload={
                "new_alerts_count": new_alerts,
                "total_alerts": len(self._alerts)
            },
            intensity=self._score_history[-1] if self._score_history else 0.0
        )

        # Phase 4b: Sekisho 連携 — アラートをファイルに永続化
        # EventBus の stigmergy はインメモリなのでプロセス間共有不可。
        # JSONL ファイル経由で Sekisho MCP に品質情報を伝播する。
        if new_alerts > 0:
            self._persist_alerts_for_sekisho()

        # アラートがあればサマリーを返し、downstream に品質情報を伝播
        # (Sekisho 等がこのコンテキストを受け取れる)
        if new_alerts > 0:
            return self.summary()
        return None  # アラートなし — 出力には干渉しない

    def _persist_alerts_for_sekisho(self) -> None:
        """アラートを JSONL ファイルに永続化 (Sekisho MCP 連携用)。

        PURPOSE: EventBus のインメモリ stigmergy はプロセス間共有できない。
        Synteleia (hermeneus プロセス内) → Sekisho (MCP 別プロセス) の連携には
        ファイルベースのチャネルが必要。
        """
        try:
            _ALERT_FILE.parent.mkdir(parents=True, exist_ok=True)
            # 直近のアラートのみ書き出し (蓄積ではなく最新状態を上書き)
            entries = []
            for alert in self._alerts:
                entries.append({
                    "timestamp": datetime.now().isoformat(),
                    "node_id": alert.source_node,
                    "severity": alert.level,
                    "category": alert.category,
                    "message": alert.message,
                    "source_node": alert.source_node,
                })
            # 最新セッションの全アラートで上書き (古いセッションは不要)
            with open(_ALERT_FILE, "w", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            logger.debug(
                "Synteleia: persisted %d alerts to %s",
                len(entries), _ALERT_FILE,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Synteleia: alert persistence failed: %s", e)

    def _evaluate_structure(self, text: str) -> float:
        """テキストの構造化度を 0.0-1.0 で評価

        構造要素:
            - 見出し (#)
            - リスト (-, *, 1.)
            - テーブル (|)
            - コードブロック (```)
        """
        if not text:
            return 0.0

        lines = text.split('\n')
        total = len(lines)
        if total == 0:
            return 0.0

        structured = 0
        for line in lines:
            stripped = line.strip()
            if (stripped.startswith('#') or
                stripped.startswith('- ') or
                stripped.startswith('* ') or
                stripped.startswith('|') or
                stripped.startswith('```') or
                re.match(r'^\d+\.', stripped)):
                structured += 1

        return structured / total

    @property
    def alerts(self) -> List[QualityAlert]:
        return list(self._alerts)

    def summary(self) -> str:
        """アラートのサマリー"""
        if not self._alerts:
            return "✅ Synteleia L0: No quality alerts."

        errors = [a for a in self._alerts if a.level == "error"]
        warnings = [a for a in self._alerts if a.level == "warning"]

        lines = [
            f"## Synteleia L0 品質スキャン",
            f"",
            f"⚠️ {len(errors)} errors, {len(warnings)} warnings",
            f"",
        ]

        if errors:
            lines.append("### ❌ Errors")
            for a in errors:
                lines.append(f"- `{a.source_node}`: {a.message}")
            lines.append("")

        if warnings:
            lines.append("### ⚠️ Warnings")
            for a in warnings:
                lines.append(f"- `{a.source_node}`: {a.message}")

        return "\n".join(lines)

    def reset(self) -> None:
        self._alerts.clear()
