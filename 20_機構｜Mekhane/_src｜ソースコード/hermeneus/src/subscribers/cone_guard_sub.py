from __future__ import annotations
# PROOF: [L2/Phase2] <- hermeneus/src/subscribers/cone_guard_sub.py
"""
ConeGuardSubscriber — Devil's Advocate / 矛盾検出ガード

段階 4: V:{} (Verification) ブロック完了時に、
直前のステップ群 (step_outputs) を Cone (圏論の錐) として構築し、
出力間の矛盾 (dispersion) や弱点を Devil's Advocate として指摘する。

発火条件: VERIFICATION イベント時のみ。
影響: 矛盾や改善点があれば文字列を返し、次の C:{} 反復の LLM プロンプトに注入される。
"""

import logging
import re
from typing import Dict, Optional

from ..activation import BaseSubscriber, ActivationPolicy
from ..event_bus import CognitionEvent, EventType

logger = logging.getLogger(__name__)


class ConeGuardSubscriber(BaseSubscriber):
    """ステップ群から Cone を構築し Devil's Advocate を行う subscriber

    V:{} ブロック完了時に、event.metadata["step_outputs"] を読み取り、
    各 node_id (WF名) を Theorem ID に正規化し、最適な Series の Cone を構築する。
    advise() を発動し、アクションが "devil" または "investigate" の場合、
    C:{} ループの次のLLMにアドバイス文を直接フィードバックする。
    """

    # WF名 (prefix) -> Theorem ID マッピング
    WF_TO_THEOREM = {
        "noe": "O1", "bou": "O2", "zet": "O3", "ene": "O4",
        "ske": "V05", "sag": "V06", "pei": "V07", "tek": "V08",
        "kat": "V09", "epo": "V10", "pai": "V11", "dok": "V12",
        "lys": "V13", "ops": "V14", "akr": "V15", "arc": "V16",
        "beb": "V17", "ele": "V18", "kop": "V19", "dio": "V20",
        "hyp": "V21", "prm": "V22", "ath": "V23", "par": "V24",
        "dia": "A2", "sop": "K4", "pro": "H1", "pis": "H2",
        "ore": "H3", "dox": "H4",
    }
    
    # Theorem ID -> 対応 Series マッピング
    THEOREM_SERIES = {
        "O1": "Tel", "O2": "Tel", "O3": "Tel", "O4": "Tel",
        "V05": "Met", "V06": "Met", "V07": "Met", "V08": "Met",
        "V09": "Kri", "V10": "Kri", "V11": "Kri", "V12": "Kri",
        "V13": "Meg", "V14": "Meg", "V15": "Meg", "V16": "Meg",
        "V17": "Ore", "V18": "Ore", "V19": "Ore", "V20": "Ore",
        "V21": "Chr", "V22": "Chr", "V23": "Chr", "V24": "Chr",
    }

    def __init__(self, fire_threshold: float = 0.5):
        super().__init__(
            name="cone_guard",
            policy=ActivationPolicy(
                event_types={EventType.VERIFICATION},
            ),
            fire_threshold=fire_threshold,
        )

    def score(self, event: CognitionEvent) -> float:
        """step_count が多いほど検証価値が高い (Phase 3 動的スコア)"""
        n_steps = event.context_snapshot.get("step_count", 0) if event.context_snapshot else 0
        return min(0.5 + n_steps * 0.1, 1.0)

    def handle(self, event: CognitionEvent) -> Optional[str]:
        """step_outputs から Cone を構築し Devil's Advocate を実行"""
        step_outputs = event.metadata.get("step_outputs", {})
        if not step_outputs or len(step_outputs) < 2:
            return None  # 比較対象が不足

        # 1. node_id (WF名) -> Theorem ID への正規化
        normalized_outputs: Dict[str, str] = {}
        detected_series_count: Dict[str, int] = {}
        
        for node_id, output in step_outputs.items():
            # e.g. "bou+:block" -> "bou"
            m = re.match(r'^([a-z]+)', node_id)
            if not m:
                continue
            wf_name = m.group(1)
            tid = self.WF_TO_THEOREM.get(wf_name)
            if tid:
                normalized_outputs[tid] = output
                series_id = self.THEOREM_SERIES.get(tid)
                if series_id:
                    detected_series_count[series_id] = detected_series_count.get(series_id, 0) + 1

        if len(normalized_outputs) < 2:
            return None

        # 2. 最適な Series を推論 (最も多く出現した Series)
        best_series_id = "Tel"  # fallback
        if detected_series_count:
            best_series_id = max(detected_series_count.items(), key=lambda x: x[1])[0]

        # 3. Cone 構築と判定
        try:
            from mekhane.fep.cone_builder import build_cone
            from mekhane.fep.cone_consumer import advise, format_advice_for_llm
            from mekhane.fep.category import Series
            
            # str to Enum
            series_enum = Series[best_series_id]
            
            cone = build_cone(series_enum, normalized_outputs)
            advice_res = advise(cone)
            
            logger.info("ConeGuard: advice action=%s, dispersion=%.2f", advice_res.action, cone.metadata.get("dispersion", 0.0))
            
            # 4. アクションに応じて LLM プロンプトへのフィードバックを決定
            if advice_res.action in ("devil", "investigate", "reweight"):
                # Phase 4a: Stigmergy Trace を残す
                dispersion = cone.metadata.get("dispersion", 0.0)
                self.leave_trace(
                    event=event,
                    payload={"action": advice_res.action, "dispersion": dispersion},
                    intensity=dispersion  # 矛盾が大きいほど痕跡も強くなる
                )
                
                # アドバイス文字列を生成
                return f"【Cone 判定 (Devil's Advocate)】\n{format_advice_for_llm(advice_res)}\n→ 次の反復でこれらの矛盾や弱点を解消してください。"
                
        except ImportError as e:
            logger.debug("ConeGuard: mekhane.fep not available: %s", e)
        except (KeyError, AttributeError) as e:
            logger.warning("ConeGuard: data structure mismatch: %s", e)
            
        return None
