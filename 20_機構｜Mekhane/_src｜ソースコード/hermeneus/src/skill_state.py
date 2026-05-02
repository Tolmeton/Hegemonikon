from __future__ import annotations
# PROOF: [L2/状態管理] <- hermeneus/src/skill_state.py O4→スキル状態永続化が必要→skill_state が担う
"""
Skill State Store — ClawX Skill System Adjunction

JSON ファイルベースのスキル状態永続化。enable/disable と per-skill config を管理。

ClawX 対応: skill-config.ts の readConfig/writeConfig パターンを Python に翻訳。
  - ClawX: ~/.openclaw/openclaw.json に直接書き込み
  - HGK:   ~/.hgk/skill_state.json
"""


import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# PURPOSE: デフォルト状態ファイルパス
DEFAULT_STATE_PATH = Path.home() / ".hgk" / "skill_state.json"


# PURPOSE: スキル状態の永続化と config 管理
class SkillStateStore:
    """JSON file-based skill state store.

    ClawX pattern: skill-config.ts の readConfig/writeConfig を参考に、
    skill の enabled/disabled 状態と per-skill 設定を ~/.hgk/skill_state.json に永続化。
    """

    def __init__(self, state_path: Path | None = None):
        self.state_path = state_path or DEFAULT_STATE_PATH
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    # ── 読み書き ──────────────────────────────────────

    # PURPOSE: 状態ファイルの読み込み
    def _read_state(self) -> dict[str, Any]:
        """Read state from JSON file."""
        if not self.state_path.exists():
            return {"skills": {}, "version": "1.0"}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to read skill state: %s", exc)
            return {"skills": {}, "version": "1.0"}

    # PURPOSE: 状態ファイルへの書き込み (atomic)
    def _write_state(self, state: dict[str, Any]) -> None:
        """Write state to JSON file (atomic via temp + rename)."""
        tmp_path = self.state_path.with_suffix(".tmp")
        try:
            tmp_path.write_text(
                json.dumps(state, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            tmp_path.replace(self.state_path)
        except OSError as exc:
            logger.error("Failed to write skill state: %s", exc)
            raise

    # ── Enable/Disable ──────────────────────────────────

    # PURPOSE: スキルの enabled 状態を取得
    def get_skill_enabled(self, skill_id: str) -> bool:
        """Check if a skill is enabled. Default: True (all enabled)."""
        state = self._read_state()
        skill_data = state.get("skills", {}).get(skill_id, {})
        return skill_data.get("enabled", True)

    # PURPOSE: スキルの enabled 状態を設定
    def set_skill_enabled(self, skill_id: str, enabled: bool,
                          is_core: bool = False) -> None:
        """Set skill enabled state.

        ClawX mapping: skill-config.ts updateSkillConfig()
        Core skills cannot be disabled (ClawX: always=true).
        """
        if is_core and not enabled:
            raise ValueError(
                f"Cannot disable core skill: {skill_id} (ClawX: always=true)"
            )
        state = self._read_state()
        skills = state.setdefault("skills", {})
        skill_data = skills.setdefault(skill_id, {})
        skill_data["enabled"] = enabled
        skill_data["updated_at"] = datetime.now().isoformat()
        self._write_state(state)

    # ── Per-Skill Config ──────────────────────────────────

    # PURPOSE: スキルの設定を全取得
    def get_skill_config(self, skill_id: str) -> dict[str, Any]:
        """Get all config values for a skill."""
        state = self._read_state()
        return state.get("skills", {}).get(skill_id, {}).get("config", {})

    # PURPOSE: スキルの設定を更新
    def set_skill_config(self, skill_id: str, key: str, value: Any) -> None:
        """Set a config value for a skill.

        ClawX mapping: skill-config.ts updateSkillConfig()
        設定は ~/.hgk/skill_state.json に直接書き込み (Gateway バイパス)。
        """
        state = self._read_state()
        skills = state.setdefault("skills", {})
        skill_data = skills.setdefault(skill_id, {})
        config = skill_data.setdefault("config", {})
        config[key] = value
        skill_data["updated_at"] = datetime.now().isoformat()
        self._write_state(state)

    # PURPOSE: スキルの全設定一括更新
    def set_skill_config_bulk(self, skill_id: str,
                              config: dict[str, Any]) -> None:
        """Set multiple config values at once."""
        state = self._read_state()
        skills = state.setdefault("skills", {})
        skill_data = skills.setdefault(skill_id, {})
        existing = skill_data.setdefault("config", {})
        existing.update(config)
        skill_data["updated_at"] = datetime.now().isoformat()
        self._write_state(state)

    # ── 一括取得 ──────────────────────────────────────

    # PURPOSE: 全スキルの状態を一括取得
    def get_all_states(self) -> dict[str, dict[str, Any]]:
        """Get all skill states."""
        state = self._read_state()
        return state.get("skills", {})
