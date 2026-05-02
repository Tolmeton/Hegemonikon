from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/kalon_gate_sub.py
"""
KalonGateSubscriber — 出力構造の品質ゲート

段階 4: V:{} (Verification) ブロック完了時に、
出力テキストが Kalon (美しさ・簡潔さ) の基準たる構造要件
(Trace, Negativa, Iso) を満たしているかを静的スキャンする。

発火条件: VERIFICATION イベント時のみ。
影響: 問題があれば文字列を返し、次の C:{} 反復の LLM プロンプトに注入される。
"""

import logging
import re
from typing import Iterator, List, Optional

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


class KalonGateSubscriber(BaseSubscriber):
    """計画出力の構造的品質を L1 スキャンする subscriber

    V:{} ブロック完了時にテキスト内の構造要件を評価する。
    Trace (順序の理由), Negativa (棄却した代替案),
    Iso (テンプレートからの充填) などの要素が欠落している場合、
    警告テキストを出力し、C:{} ループの収束判定に影響を与える。

    責務境界 (vs SynteleiaSubscriber):
        - Synteleia: STEP_COMPLETE で発火。空出力・低構造スコアの L0 警告。
        - KalonGate: VERIFICATION で発火。計画の構造的完全性 (Trace/Negativa) の L1 検証。
    """

    # 構造要件パターン (テンプレートマーカー「確認済み」等の誤検知を防ぐため 50文字以上の文脈を要求)
    TRACE_PATTERN = re.compile(
        r'(?:理由[::は]|根拠[::は]|TraceAbility|なぜなら|これは.{5,30}から|Because\s|Reason[::])',
        re.IGNORECASE,
    )
    NEGATIVA_PATTERN = re.compile(
        r'(?:棄却|代替案|見送り|採用しない|除外|不採用|Negativa|Alternative|Rejected|instead\sof)',
        re.IGNORECASE,
    )
    # CognitiveStepHandler のテンプレートマーカー (これらがあるだけでは Trace とみなさない)
    TEMPLATE_MARKERS = re.compile(
        r'(?:確認済み[::]\s*(?:本質|対象|品質)|検証済み[::])',
        re.IGNORECASE,
    )
    ISO_SECTION_PATTERN = re.compile(
        r'(?m)^(?:#{1,6}\s+\S+|(?:PHASE|Phase)\s+\d+|P-\d+(?:\.\d+)?|S\[\d+(?:\.\d+)?\])'
    )
    ISO_LIST_PATTERN = re.compile(r'(?m)^\s*(?:[-*•]|\d+\.)\s+')
    ISO_TABLE_PATTERN = re.compile(r'(?m)^\|.+\|$|[┌└├┤│─]{2,}')
    ISO_STATE_PATTERN = re.compile(
        r'(?m)^(?:\[CHECKPOINT\b|WM\b|NQS\b|AQS\b|\$[A-Za-z_][A-Za-z0-9_]*\s*=)'
    )
    IMPLEMENTATION_NODE_PATTERN = re.compile(r'/(?:ene|o4)\b', re.IGNORECASE)
    IMPLEMENTATION_TEMPLATE_PATTERN = re.compile(
        r'(?:実装報告\s*Renderer\s*Policy|\[Implementation Report Template\]|成果核\s*/\s*変更面\s*/\s*検証)',
        re.IGNORECASE,
    )
    KERNEL_PATTERN = re.compile(
        r'(?im)^(?:#{1,6}\s*)?(?:成果核|変更の要旨|最終結果|実装の要旨)\b'
    )
    CHANGED_SURFACES_TABLE_PATTERN = re.compile(
        r'(?im)^\|\s*(?:path|file|変更対象|対象)\s*\|\s*(?:intent|目的|役割)\s*\|\s*(?:change|変更|内容)\s*\|'
    )
    VERIFICATION_BLOCK_PATTERN = re.compile(
        r'```(?:bash|sh|shell|console|text)?\n[\s\S]+?\n```',
        re.IGNORECASE,
    )
    ROLLBACK_PATTERN = re.compile(
        r'(?im)^(?:#{1,6}\s*)?(?:復元|rollback|ロールバック|戻す場合)\b'
    )
    ANNEX_PATTERN = re.compile(
        r'(?im)^(?:#{1,6}\s*)?(?:annex|付録|raw path|参考パス|path annex|パス一覧)\b'
    )
    ABSOLUTE_PATH_PATTERN = re.compile(
        r'(?<![`|])/(?:home|Users|tmp|var|opt|etc|srv)/[^\s`|)]+'
    )

    def __init__(self, fire_threshold: float = 0.5):
        super().__init__(
            name="kalon_gate",
            policy=ActivationPolicy(
                event_types={EventType.VERIFICATION},
            ),
            fire_threshold=fire_threshold,
        )

    def score(self, event: CognitionEvent) -> float:
        """step_count が多いほど検証価値が高い (Phase 3 動的スコア)"""
        n_steps = event.context_snapshot.get("step_count", 0) if event.context_snapshot else 0
        return min(0.5 + n_steps * 0.1, 1.0)

    def _has_iso_structure(self, output: str) -> bool:
        """出力が思考構造を保存する最低限の骨格を持つかを判定する。

        Operationalization:
          - セクション/Phase 見出し
          - 箇条書きや番号付き列挙
          - 表/箱組み
          - CHECKPOINT/WM/NQS などの状態ブロック

        これらのカテゴリが2つ以上あれば、単なる滑らかな prose ではなく
        構造化 artifact とみなす。
        """
        signals = [
            bool(self.ISO_SECTION_PATTERN.search(output)),
            bool(self.ISO_LIST_PATTERN.search(output)),
            bool(self.ISO_TABLE_PATTERN.search(output)),
            bool(self.ISO_STATE_PATTERN.search(output)),
        ]
        return sum(signals) >= 2

    def _iter_node_ids(self, result) -> Iterator[str]:
        """StepResult tree から node_id を再帰収集する。"""
        if result is None:
            return
        node_id = getattr(result, "node_id", "")
        if node_id:
            yield node_id
        for child in getattr(result, "children", []) or []:
            yield from self._iter_node_ids(child)

    def _is_implementation_report_event(self, event: CognitionEvent, output: str) -> bool:
        """VERIFICATION が /ene 実装報告に由来するかを判定する。"""
        if self.IMPLEMENTATION_NODE_PATTERN.search(event.source_node or ""):
            return True

        result = event.step_result
        if result is not None:
            for node_id in self._iter_node_ids(result):
                if self.IMPLEMENTATION_NODE_PATTERN.search(node_id):
                    return True

        return bool(self.IMPLEMENTATION_TEMPLATE_PATTERN.search(output))

    def _implementation_report_warnings(self, output: str) -> List[str]:
        """実装報告専用の readability gate。"""
        warnings: List[str] = []

        if not self.KERNEL_PATTERN.search(output):
            warnings.append(
                "- [Kalon/O4] 成果核 欠落: 冒頭で何が変わったかを固定する短い成果核段落がありません。"
            )

        if not self.CHANGED_SURFACES_TABLE_PATTERN.search(output):
            warnings.append(
                "- [Kalon/O4] 変更面 欠落: `path | intent | change` を持つ変更面テーブルがありません。"
            )

        if not self.VERIFICATION_BLOCK_PATTERN.search(output):
            warnings.append(
                "- [Kalon/O4] 検証面 欠落: 機械的証拠を分離した fenced code block がありません。"
            )

        if not self.ROLLBACK_PATTERN.search(output):
            warnings.append(
                "- [Kalon/O4] 復元面 欠落: rollback 条件や戻し方を示す復元段落がありません。"
            )

        abs_paths = self.ABSOLUTE_PATH_PATTERN.findall(output)
        if abs_paths and not self.ANNEX_PATTERN.search(output):
            warnings.append(
                "- [Kalon/O4] Annex 欠落: raw absolute path が本文に現れていますが、隔離用 annex がありません。"
            )

        return warnings

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """出力の構造的品質をスキャン"""
        result = event.step_result
        if result is None:
            return None

        output = result.output if hasattr(result, 'output') else ""
        if not output:
            return None

        warnings = []

        # 1. Trace 要件検証
        trace_match = self.TRACE_PATTERN.search(output)
        template_match = self.TEMPLATE_MARKERS.search(output)
        # テンプレートマーカーのみでは Trace とみなさない (誤検知防止)
        if not trace_match or (trace_match and template_match and not self.TRACE_PATTERN.search(output[trace_match.end():])):
            warnings.append("- [Kalon] Trace 欠落: 決定の理由や根拠 (Trace) が明記されていません。")

        # 2. Negativa 要件検証 (何を棄却したか、代替案の検討があるか)
        # 計画においては、代替案の棄却提示が「薄さ」を防ぐ
        if not self.NEGATIVA_PATTERN.search(output):
            warnings.append("- [Kalon] Negativa 欠落: 棄却した代替案 (Negativa) の提示がありません。一本道の薄い計画です。")

        # 3. Iso 要件検証 (思考構造と出力構造が同型か)
        if not self._has_iso_structure(output):
            warnings.append(
                "- [Kalon] Iso 欠落: 見出し・列挙・CHECKPOINT・WM/NQS 等の構造痕跡が乏しく、"
                "思考の運動が prose に潰れています。"
            )

        # 4. /ene 実装報告の readability gate
        if self._is_implementation_report_event(event, output):
            warnings.extend(self._implementation_report_warnings(output))

        if not warnings:
            return None  # 品質OK

        lines = [
            "【Kalon 品質ゲート警告 (Anti-Shallow)】",
            "出力構造に以下の Kalon 要件が欠落しています。計画が「薄い」兆候です。"
        ]
        lines.extend(warnings)
        if self._is_implementation_report_event(event, output):
            lines.append(
                "→ /ene 実装報告では `成果核 / 変更面 / 検証 / 復元 / annex` を分離し、"
                "unordered list に流さず reader-facing artifact として再構成してください。"
            )
        else:
            lines.append("→ 次の計画では具体的な理由と代替案の棄却理由を含めてください。")
        
        advice = "\n".join(lines)
        logger.info("KalonGate: detected shallow output (%d warnings)", len(warnings))
        
        # Phase 4a: Stigmergy Trace を残す
        self.leave_trace(
            event=event,
            payload={"warnings": len(warnings)},
            intensity=0.8
        )
        
        return advice
