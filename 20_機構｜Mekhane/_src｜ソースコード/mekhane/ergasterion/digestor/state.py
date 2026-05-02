# PROOF: [L2/インフラ] <- mekhane/ergasterion/digestor/state.py A0→実行状態の永続化が必要→state が担う
"""
Digestor State — 実行状態の永続化

scheduler の実行履歴を state.json に保存し、
/boot や hgk_status から参照可能にする。
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# PURPOSE: 状態ファイルのパス
STATE_DIR = Path.home() / ".hegemonikon" / "digestor"
STATE_FILE = STATE_DIR / "state.json"


# PURPOSE: 状態を読み込む
def load_state() -> dict:
    """state.json を読み込む。存在しなければ初期状態を返す。"""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "last_run": None,
        "last_result": None,
        "total_runs": 0,
        "total_candidates": 0,
        "errors": [],
    }


# PURPOSE: 状態を保存する
def save_state(state: dict) -> None:
    """state.json に状態を書き込む。"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# PURPOSE: パイプライン実行結果を記録する
def record_run(
    total_papers: int,
    candidates_selected: int,
    errors: Optional[list[str]] = None,
) -> dict:
    """パイプライン実行結果を state.json に記録する。

    Args:
        total_papers: 取得した論文数
        candidates_selected: 選定された候補数
        errors: エラーメッセージのリスト

    Returns:
        更新された state dict
    """
    state = load_state()
    now = datetime.now(timezone.utc).isoformat()

    state["last_run"] = now
    state["last_result"] = {
        "timestamp": now,
        "total_papers": total_papers,
        "candidates_selected": candidates_selected,
        "errors": errors or [],
    }
    state["total_runs"] = state.get("total_runs", 0) + 1
    state["total_candidates"] = state.get("total_candidates", 0) + candidates_selected

    # エラー履歴は直近10件のみ保持
    if errors:
        all_errors = state.get("errors", [])
        all_errors.extend(
            {"timestamp": now, "message": e} for e in errors
        )
        state["errors"] = all_errors[-10:]

    save_state(state)
    return state


# PURPOSE: 状態のサマリー文字列を生成
def get_status_summary() -> str:
    """hgk_status 用のワンライン サマリーを生成する。"""
    state = load_state()

    if state["last_run"] is None:
        return "🔄 Digestor: 未実行"

    last = state["last_result"] or {}
    papers = last.get("total_papers", 0)
    candidates = last.get("candidates_selected", 0)
    total = state.get("total_runs", 0)

    # 最終実行からの経過時間
    try:
        last_dt = datetime.fromisoformat(state["last_run"])
        delta = datetime.now(timezone.utc) - last_dt
        hours = int(delta.total_seconds() / 3600)
        if hours < 24:
            age = f"{hours}h ago"
        else:
            age = f"{hours // 24}d ago"
    except (ValueError, TypeError):
        age = "?"

    return (
        f"🔄 Digestor: {age} | "
        f"直近 {papers}論文→{candidates}候補 | "
        f"累計 {total}回"
    )
