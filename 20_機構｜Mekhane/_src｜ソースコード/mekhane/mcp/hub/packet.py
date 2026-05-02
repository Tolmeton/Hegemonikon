"""
V-009 パケットプロトコル (Return Packet)

バックエンドからの実行結果を定型フォーマット（返却票）にカプセル化するモジュール。
"""

import json
import uuid
from typing import Any, Dict, Optional

def build_return_packet(
    backend: str,
    status: str,
    result: Any,
    task_id: Optional[str] = None,
    elapsed_ms: Optional[int] = None,
    quality_score: Optional[float] = None,
    decisions_log_path: Optional[str] = None,
    next_suggested: Optional[str] = None,
    context_update: Optional[str] = None,
) -> str:
    """
    バックエンドの実行結果を V-009 準拠の返却票（JSON文字列）にカプセル化する。
    """
    if not task_id:
        task_id = f"hub-{uuid.uuid4().hex[:8]}"
        
    packet: Dict[str, Any] = {
        "header": {
            "task_id": task_id,
            "from": backend,
            "status": status,
        },
        "result": result,
        "decisions_log_path": decisions_log_path or "None",
        "forward": {}
    }

    if elapsed_ms is not None:
        packet["header"]["elapsed_ms"] = elapsed_ms
        
    if quality_score is not None:
        if isinstance(packet["result"], dict):
            packet["result"]["quality_score"] = quality_score
        else:
            packet["result"] = {
                "response": result,
                "quality_score": quality_score
            }
            
    if next_suggested is not None:
        packet["forward"]["next_suggested"] = next_suggested
    if context_update is not None:
        packet["forward"]["context_update"] = context_update
        
    return json.dumps(packet, ensure_ascii=False, indent=2)


def build_secretary_packet(
    task_id: str,
    task_description: str,
    status: str,
    elapsed_ms: int,
    routing: Optional[Dict[str, Any]] = None,
    results: Optional[list] = None,
    counter_evidence: Optional[Dict[str, Any]] = None,
    gate: Optional[Dict[str, Any]] = None,
    decisions_log_path: Optional[str] = None,
) -> str:
    """Vision B 統合秘書パイプラインの判断材料パッケージを生成する。

    5セクション構造:
      header          — メタデータ (task_id, status, elapsed)
      routing         — Phase A: ルーティング脳の判断と計画
      results         — Phase B1: 各ステップの実行結果
      counter_evidence — Phase B2: Shadow による反証・助言
      gate            — Phase C: Sekisho による BC 監査
    """
    if not task_id:
        task_id = f"sec-{uuid.uuid4().hex[:8]}"

    packet: Dict[str, Any] = {
        "header": {
            "task_id": task_id,
            "from": "hub_secretary",
            "status": status,
            "elapsed_ms": elapsed_ms,
            "version": "vision_b",
        },
        "routing": routing,
        "results": results or [],
        "counter_evidence": counter_evidence,
        "gate": gate,
        "decisions_log_path": decisions_log_path,
        "forward": {},
    }
    return json.dumps(packet, ensure_ascii=False, indent=2)
