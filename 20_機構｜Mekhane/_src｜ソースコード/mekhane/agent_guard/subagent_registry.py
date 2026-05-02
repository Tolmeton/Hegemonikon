# PROOF: mekhane/agent_guard/subagent_registry.py
# PURPOSE: agent_guard モジュールの subagent_registry
"""
Subagent Registry (T-21)

スポーンされたサブエージェント (Jules など) のライフサイクルを管理する。
OpenClaw の subagent-registry.ts の軽量版。

Features:
- run 登録/完了
- ステータス追跡
- アクティブ run カウント (同時実行制限)
- orphan run の sweeper (timeout ベース)
- JSON state persistence
"""
import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class SubagentRun:
    run_id: str
    session_key: str
    agent_id: str
    status: RunStatus = RunStatus.PENDING
    started_at: float = 0.0
    ended_at: Optional[float] = None
    outcome: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, session_key: str, agent_id: str, **kwargs) -> "SubagentRun":
        return cls(
            run_id=str(uuid.uuid4())[:8],
            session_key=session_key,
            agent_id=agent_id,
            status=RunStatus.RUNNING,
            started_at=time.time(),
            **kwargs,
        )

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SubagentRun":
        data = dict(data)  # copy
        data["status"] = RunStatus(data.get("status", "pending"))
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# Default timeout for orphan run detection
DEFAULT_RUN_TIMEOUT_S = 30 * 60  # 30 minutes
DEFAULT_MAX_ACTIVE = 30  # Max concurrent subagent runs
DEFAULT_STATE_PATH = os.path.expanduser("~/.hgk/subagent_registry.json")


class SubagentRegistry:
    """サブエージェントの run ライフサイクルを管理するレジストリ"""
    
    def __init__(self, state_path: Optional[str] = None, max_active: int = DEFAULT_MAX_ACTIVE):
        self._state_path = state_path or DEFAULT_STATE_PATH
        self._runs: Dict[str, SubagentRun] = {}
        self._max_active = max_active
    
    def register_run(self, session_key: str, agent_id: str, **metadata) -> SubagentRun:
        """新しい run を登録"""
        run = SubagentRun.create(session_key=session_key, agent_id=agent_id, metadata=metadata)
        self._runs[run.run_id] = run
        return run
    
    def complete_run(self, run_id: str, status: RunStatus = RunStatus.COMPLETED, outcome: Optional[str] = None) -> Optional[SubagentRun]:
        """run を完了状態にする"""
        run = self._runs.get(run_id)
        if run is None:
            return None
        
        run.status = status
        run.ended_at = time.time()
        if outcome:
            run.outcome = outcome
        return run
    
    def get_run(self, run_id: str) -> Optional[SubagentRun]:
        """run を取得"""
        return self._runs.get(run_id)
    
    def list_runs(self, status: Optional[RunStatus] = None, session_key: Optional[str] = None) -> List[SubagentRun]:
        """run の一覧を取得"""
        runs = list(self._runs.values())
        if status is not None:
            runs = [r for r in runs if r.status == status]
        if session_key is not None:
            runs = [r for r in runs if r.session_key == session_key]
        return sorted(runs, key=lambda r: r.started_at, reverse=True)
    
    def count_active(self) -> int:
        """アクティブな run 数"""
        return sum(1 for r in self._runs.values() if r.status in (RunStatus.PENDING, RunStatus.RUNNING))
    
    def can_spawn(self) -> bool:
        """新しいサブエージェントを起動できるか (同時実行制限チェック)"""
        return self.count_active() < self._max_active
    
    def sweep_stale(self, timeout_s: float = DEFAULT_RUN_TIMEOUT_S) -> List[SubagentRun]:
        """タイムアウトした orphan run を回収"""
        now = time.time()
        swept = []
        
        for run in list(self._runs.values()):
            if run.status not in (RunStatus.PENDING, RunStatus.RUNNING):
                continue
            
            age_s = now - run.started_at
            if age_s > timeout_s:
                run.status = RunStatus.TIMEOUT
                run.ended_at = now
                run.outcome = f"Swept by watchdog after {age_s:.0f}s (timeout={timeout_s:.0f}s)"
                swept.append(run)
        
        return swept
    
    def persist(self) -> None:
        """状態をファイルに保存"""
        state_dir = os.path.dirname(self._state_path)
        if state_dir:
            os.makedirs(state_dir, exist_ok=True)
        
        data = {
            "runs": {rid: run.to_dict() for rid, run in self._runs.items()},
            "persisted_at": time.time(),
        }
        
        with open(self._state_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def restore(self) -> int:
        """ファイルから状態を復元。復元した run 数を返す"""
        if not os.path.exists(self._state_path):
            return 0
        
        try:
            with open(self._state_path, "r") as f:
                data = json.load(f)
            
            runs_data = data.get("runs", {})
            count = 0
            for rid, run_data in runs_data.items():
                try:
                    run = SubagentRun.from_dict(run_data)
                    self._runs[rid] = run
                    count += 1
                except (ValueError, TypeError, KeyError):
                    continue
            
            return count
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            return 0
    
    def stats(self) -> Dict[str, int]:
        """統計"""
        by_status: Dict[str, int] = {}
        for run in self._runs.values():
            status_val = run.status.value
            by_status[status_val] = by_status.get(status_val, 0) + 1
        return {
            "total": len(self._runs),
            "active": self.count_active(),
            "max_active": self._max_active,
            **by_status,
        }
