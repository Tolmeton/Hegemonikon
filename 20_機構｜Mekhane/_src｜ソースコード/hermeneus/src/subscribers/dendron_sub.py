from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/dendron_sub.py
"""
DendronSubscriber — 参照検証

段階 4: V:{} (Verification) ブロック完了時に、
出力内の参照 (ファイルパス, WF名, 定理ID) の存在を検証する。

発火条件: VERIFICATION イベント時のみ。
リスク: 低 (読取専用検証、出力変更なし)
"""

import logging
import os
import re
from typing import List, Optional, Tuple

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


class DendronSubscriber(BaseSubscriber):
    """参照の存在を検証する subscriber

    V:{} ブロック完了時にテキスト内の参照を検出し、
    ファイルパスや WF 名の存在を確認する。

    検出対象:
        - ファイルパス: /home/..., ~/..., ./...
        - WF 参照: /noe, /dia 等
        - 定理 ID: V01, V02, ..., H01, A02 等
    """

    # WF 参照パターン
    WF_PATTERN = re.compile(r'(?<!\w)/([a-z]{2,4}[+\-]?)(?!\w)')

    # ファイルパスパターン
    PATH_PATTERN = re.compile(
        r'(?:(?:/home/\w+|~|\.)/[\w./-]+|'
        r'(?:hermeneus|mekhane|kernel|nous)/[\w./-]+)'
    )

    # 定理 ID パターン
    THEOREM_PATTERN = re.compile(r'\b([VHAKSP])\d{2}\b')

    # __file__ = hermeneus/src/subscribers/dendron_sub.py → 3 levels up = project root
    PROJECT_ROOT = str(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    WF_DIR = os.path.join(PROJECT_ROOT, "nous", "workflows")

    def __init__(self, fire_threshold: float = 0.5):
        super().__init__(
            name="dendron_verifier",
            policy=ActivationPolicy(
                event_types={EventType.VERIFICATION},
            ),
            fire_threshold=fire_threshold,
        )
        self._verified: List[Tuple[str, bool]] = []

    def score(self, event: CognitionEvent) -> float:
        """VERIFICATION イベント専用。常に高い検証価値を持つ (Phase 3)"""
        s = 1.0  # 参照検証は常に最優先 (1.0)
        self._score_history.append(s)
        return s

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """参照の存在を検証"""
        result = event.step_result
        if result is None:
            return None

        output = result.output if hasattr(result, 'output') else ""
        if not output:
            return None

        missing = []
        found = []

        # 1. ファイルパス検証
        paths = self.PATH_PATTERN.findall(output)
        for path in paths:
            full_path = path
            if not path.startswith('/'):
                full_path = os.path.join(self.PROJECT_ROOT, path)
            full_path = os.path.expanduser(full_path)

            exists = os.path.exists(full_path)
            self._verified.append((path, exists))
            if exists:
                found.append(f"✅ `{path}`")
            else:
                missing.append(f"❌ `{path}` — NOT FOUND")

        # 2. WF 参照検証
        wf_refs = self.WF_PATTERN.findall(output)
        for wf_id in wf_refs:
            clean_id = wf_id.rstrip('+-')
            wf_path = os.path.join(self.WF_DIR, f"{clean_id}.md")
            exists = os.path.exists(wf_path)
            self._verified.append((f"/{wf_id}", exists))
            if exists:
                found.append(f"✅ `/{wf_id}`")
            else:
                missing.append(f"❌ `/{wf_id}` — WF not found")

        if not missing and not found:
            return None

        if missing:
            lines = [
                "[🌳 Dendron Verification]",
                f"  検証: {len(found)} found, {len(missing)} missing",
            ]
            for m in missing:
                lines.append(f"  {m}")
            logger.warning("Dendron: %d missing references", len(missing))
            return "\n".join(lines)

        return None  # 全て存在確認 OK — 報告不要

    @property
    def verification_results(self) -> List[Tuple[str, bool]]:
        return list(self._verified)

    def reset(self) -> None:
        self._verified.clear()
