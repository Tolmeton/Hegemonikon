from __future__ import annotations
# PROOF: [L2/インフラ] <- Pinakas セッション横断タスクボードの YAML CRUD
"""
Pinakas Store — セッション横断タスクボードの YAML CRUD

6 ボード体制 (v1.3〜):
  - Seed / Task / Question / Wish / Backlog: 短文付箋 (同一スキーマ)
  - Whiteboard: 索引 YAML + 本体 md の二層構造 (戦略ノート)

付箋 5 ボードには従来通り post/list/done/drop を提供。
Whiteboard は別スキーマのため索引読込 + 本体 md 解決の専用 API を提供する。
アトミック書込み (tmp → rename) で Syncthing 競合を最小化。

Usage:
    from mekhane.symploke.pinakas_store import PinakasStore
    store = PinakasStore()
    store.post("task", "mneme search TaskGroup エラー修正", source="session_abc")
    items = store.list_open("task")

    # Whiteboard (索引 + 本体 md 分離)
    wbs = store.load_whiteboard_index()
    body = store.load_whiteboard_body("WB-001")
"""


import tempfile
import shutil
from datetime import date
from pathlib import Path
from typing import Literal

import yaml

from mekhane.paths import PINAKAS_DIR

# 付箋 5 ボード (同一スキーマ、post/list/done/drop が使える)
BoardType = Literal["seed", "task", "question", "wish", "backlog"]

_BOARD_FILES: dict[BoardType, str] = {
    "seed": "PINAKAS_SEED.yaml",
    "task": "PINAKAS_TASK.yaml",
    "question": "PINAKAS_QUESTION.yaml",
    "wish": "PINAKAS_WISH.yaml",
    "backlog": "PINAKAS_BACKLOG.yaml",
}

_ID_PREFIX: dict[BoardType, str] = {
    "seed": "S",
    "task": "T",
    "question": "Q",
    "wish": "W",
    "backlog": "B",
}

# Whiteboard は別スキーマ (索引 YAML + 本体 md 分離)。
# 付箋 5 ボードと同じ post/list インターフェースは意図的に提供しない —
# WB 新設は頻度が低く手動で十分 (PROTOCOL.md v1.3 参照)。
_WHITEBOARD_FILE = "PINAKAS_WHITEBOARD.yaml"


class PinakasStore:
    """Pinakas YAML ボードの CRUD 操作を提供する。"""

    def __init__(self, pinakas_dir: Path | None = None):
        self.dir = pinakas_dir or PINAKAS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def _board_path(self, board: BoardType) -> Path:
        return self.dir / _BOARD_FILES[board]

    def _load(self, board: BoardType) -> dict:
        path = self._board_path(board)
        if not path.exists():
            return {"version": "1.0", "next_id": 1, "items": []}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if "items" not in data:
            data["items"] = []
        if "next_id" not in data:
            data["next_id"] = 1
        return data

    def _save(self, board: BoardType, data: dict) -> None:
        """アトミック書込み: tmp ファイルに書いてから rename。"""
        path = self._board_path(board)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.dir), suffix=".tmp", prefix=".pinakas_"
        )
        try:
            with open(fd, "w", encoding="utf-8") as f:
                # コメントヘッダを保持
                header = _BOARD_FILES[board].replace(".yaml", "")
                f.write(f"# {header}\n")
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            shutil.move(tmp_path, str(path))
        except Exception:  # noqa: BLE001
            Path(tmp_path).unlink(missing_ok=True)
            raise

    def post(self, board: BoardType, text: str, source: str = "manual", tags: list[str] | None = None) -> str:
        """新規項目を追加。生成された ID を返す。"""
        data = self._load(board)
        prefix = _ID_PREFIX[board]
        item_id = f"{prefix}-{data['next_id']:03d}"
        data["next_id"] += 1
        data["items"].append({
            "id": item_id,
            "text": text,
            "status": "open",
            "created": str(date.today()),
            "source": source,
            "tags": tags or [],
        })
        self._save(board, data)
        return item_id

    def list_open(self, board: BoardType) -> list[dict]:
        """open 状態の項目一覧を返す。"""
        data = self._load(board)
        return [item for item in data["items"] if item.get("status") == "open"]

    def list_all(self, board: BoardType) -> list[dict]:
        """全項目を返す。"""
        return self._load(board)["items"]

    def done(self, board: BoardType, item_id: str) -> bool:
        """項目を done にする。成功したら True。"""
        return self._set_status(board, item_id, "done")

    def drop(self, board: BoardType, item_id: str) -> bool:
        """項目を dropped にする。成功したら True。"""
        return self._set_status(board, item_id, "dropped")

    def _set_status(self, board: BoardType, item_id: str, status: str) -> bool:
        data = self._load(board)
        for item in data["items"]:
            if item["id"] == item_id:
                item["status"] = status
                self._save(board, data)
                return True
        return False

    def summary(self) -> dict[str, int]:
        """各付箋ボードの open 件数を返す。Whiteboard は active 件数を別途 `whiteboard` キーで返す。"""
        result: dict[str, int] = {
            board: len(self.list_open(board))
            for board in _BOARD_FILES
        }
        try:
            result["whiteboard"] = len(self.list_active_whiteboards())
        except Exception:  # noqa: BLE001
            result["whiteboard"] = 0
        return result

    # ------------------------------------------------------------------
    # Whiteboard 専用 API (索引 YAML + 本体 md 分離)
    #
    # WB は他ボードと異なり、YAML 側は索引のみを持ち、実質コンテンツは
    # whiteboards/WB-NNN_*.md に保存される。そのため post/list/done/drop は
    # 付箋 5 ボード向け API を流用しない:
    #   - 索引読込:    load_whiteboard_index()
    #   - 本体読込:    load_whiteboard_body(wb_id)
    #   - active 抽出: list_active_whiteboards()
    # ------------------------------------------------------------------

    def _whiteboard_path(self) -> Path:
        return self.dir / _WHITEBOARD_FILE

    def load_whiteboard_index(self) -> list[dict]:
        """PINAKAS_WHITEBOARD.yaml を読み、items (索引エントリ一覧) を返す。

        各 item は id/title/path/target/status/created/updated/tags/note 等を含む。
        本体 md の内容はロードしない (コンテキスト爆発防止)。
        """
        path = self._whiteboard_path()
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        items = data.get("items") or []
        return list(items)

    def list_active_whiteboards(self) -> list[dict]:
        """status == 'active' な WB 索引エントリのみ返す。"""
        return [w for w in self.load_whiteboard_index() if w.get("status") == "active"]

    def load_whiteboard_body(self, wb_id: str) -> str | None:
        """WB の本体 md を読み込む。見つからなければ None。

        `path` フィールド (pinakas/ からの相対パス) を解決して読む。
        長文になりうるため呼出側で明示的に要求された場合のみ使う。
        """
        for item in self.load_whiteboard_index():
            if item.get("id") != wb_id:
                continue
            rel = item.get("path")
            if not rel:
                return None
            body_path = (self.dir / rel).resolve()
            if not body_path.exists():
                return None
            with open(body_path, "r", encoding="utf-8") as f:
                return f.read()
        return None


if __name__ == "__main__":
    store = PinakasStore()
    print("Pinakas Summary:", store.summary())
    for board in _BOARD_FILES:
        items = store.list_open(board)
        if items:
            print(f"\n{board.upper()} ({len(items)} open):")
            for item in items:
                print(f"  {item['id']}: {item['text']}")
    active_wbs = store.list_active_whiteboards()
    if active_wbs:
        print(f"\nWHITEBOARD ({len(active_wbs)} active):")
        for wb in active_wbs:
            print(f"  {wb['id']}: {wb.get('title', '')}")
