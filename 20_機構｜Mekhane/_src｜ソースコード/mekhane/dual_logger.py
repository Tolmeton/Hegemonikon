# PROOF: [L2/インフラ] <- mekhane/dual_logger.py A0→デュアルログ戦略
# PURPOSE: 構造化JSONL + 平文テキストの二重ログ出力。Sympatheiaログ戦略の統一。
#          MiroFish report_agent.py L50-150 のデュアルログパターンをHGK用に再構成。
#          Mimēsis 随伴 D4: デュアルログ戦略。
"""デュアルログ: 構造化 JSONL + 人間可読平文テキスト。

MiroFish の report_agent.py では、2つのログを同時に書き出す:
1. agent_log.jsonl — 構造化ログ (機械解析用)
2. console_log.txt — 平文ログ (人間可読)

HGK の Sympatheia は現在 JSONL のみ。可読性を追加する。
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DualLogger:
    """構造化 JSONL + 平文テキストの二重ログ出力。

    Args:
        jsonl_path: 構造化ログの出力先。
        text_path: 平文ログの出力先。None で平文出力なし。
        component: ログ出力元のコンポーネント名。
        max_file_size_mb: ログファイルの最大サイズ (MB)。超えたらローテーション。
    """

    def __init__(
        self,
        jsonl_path: Path | str,
        text_path: Path | str | None = None,
        component: str = "hgk",
        max_file_size_mb: int = 10,
    ):
        self.jsonl_path = Path(jsonl_path)
        self.text_path = Path(text_path) if text_path else None
        self.component = component
        self.max_file_size_mb = max_file_size_mb

        # ディレクトリの事前作成
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        if self.text_path:
            self.text_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        level: str,
        message: str,
        **extra: Any,
    ) -> None:
        """ログエントリを出力する。

        Args:
            level: ログレベル (INFO, WARN, ERROR, DEBUG)。
            message: ログメッセージ。
            **extra: 追加の構造化データ。
        """
        now = datetime.now(timezone.utc)

        # 構造化エントリ (JSONL)
        entry = {
            "ts": now.isoformat(),
            "level": level,
            "component": self.component,
            "message": message,
            **extra,
        }

        # 平文エントリ
        text_line = f"[{now.strftime('%H:%M:%S')}] [{level}] [{self.component}] {message}"
        if extra:
            # 追加データは key=value 形式で付加
            extras_str = " | ".join(f"{k}={v}" for k, v in extra.items())
            text_line += f" | {extras_str}"

        # 書き出し
        self._write_jsonl(entry)
        if self.text_path:
            self._write_text(text_line)

    def info(self, message: str, **extra: Any) -> None:
        """INFO レベルのログ。"""
        self.log("INFO", message, **extra)

    def warn(self, message: str, **extra: Any) -> None:
        """WARN レベルのログ。"""
        self.log("WARN", message, **extra)

    def error(self, message: str, **extra: Any) -> None:
        """ERROR レベルのログ。"""
        self.log("ERROR", message, **extra)

    def debug(self, message: str, **extra: Any) -> None:
        """DEBUG レベルのログ。"""
        self.log("DEBUG", message, **extra)

    def _write_jsonl(self, entry: dict) -> None:
        """構造化ログを JSONL ファイルに書き出す。"""
        try:
            self._rotate_if_needed(self.jsonl_path)
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ JSONL log failed: {e}", file=sys.stderr)

    def _write_text(self, line: str) -> None:
        """平文ログをテキストファイルに書き出す。"""
        if not self.text_path:
            return
        try:
            self._rotate_if_needed(self.text_path)
            with open(self.text_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception as e:  # noqa: BLE001
            print(f"⚠️ Text log failed: {e}", file=sys.stderr)

    def _rotate_if_needed(self, path: Path) -> None:
        """ファイルサイズが上限を超えていたらローテーション。"""
        if not path.exists():
            return
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            rotated = path.with_suffix(
                f".{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}"
            )
            path.rename(rotated)
