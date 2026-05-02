#!/usr/bin/env python3
# PROOF: [L2/テスト] <- hermeneus/tests/
# PURPOSE: Skill State + SkillDefinition 拡張 (ClawX Skill Adjunction) のユニットテスト
"""
Skill State tests — ClawX Skill System Adjunction

skill_state.py + skill_registry.py の ClawX 拡張フィールドを検証:
- SkillStateStore の enable/disable + config 永続化
- Core skill の disable 禁止
- SkillDefinition の isCore/isBundled/config_schema パース
"""

import json
import textwrap
from pathlib import Path

import pytest

from hermeneus.src.skill_state import SkillStateStore


# ── SkillStateStore テスト ──────────────────────────────

class TestSkillStateStore:
    """SkillStateStore の永続化テスト。"""

    def test_enable_disable_roundtrip(self, tmp_path: Path):
        """enable/disable の永続化が正しい。"""
        store = SkillStateStore(state_path=tmp_path / "state.json")
        store.set_skill_enabled("V05", False)
        assert store.get_skill_enabled("V05") is False

        # 別インスタンスから読み直し
        store2 = SkillStateStore(state_path=tmp_path / "state.json")
        assert store2.get_skill_enabled("V05") is False

    def test_default_enabled(self, tmp_path: Path):
        """デフォルトは enabled=True。"""
        store = SkillStateStore(state_path=tmp_path / "state.json")
        assert store.get_skill_enabled("nonexistent") is True

    def test_core_skill_cannot_disable(self, tmp_path: Path):
        """Core skill の disable → ValueError。"""
        store = SkillStateStore(state_path=tmp_path / "state.json")
        with pytest.raises(ValueError, match="Cannot disable core skill"):
            store.set_skill_enabled("governance", False, is_core=True)

    def test_core_skill_can_enable(self, tmp_path: Path):
        """Core skill の enable は OK。"""
        store = SkillStateStore(state_path=tmp_path / "state.json")
        store.set_skill_enabled("governance", True, is_core=True)
        assert store.get_skill_enabled("governance") is True

    def test_config_roundtrip(self, tmp_path: Path):
        """per-skill config の永続化。"""
        store = SkillStateStore(state_path=tmp_path / "state.json")
        store.set_skill_config("V05", "max_depth", "L3")
        store.set_skill_config("V05", "timeout", 30)

        config = store.get_skill_config("V05")
        assert config["max_depth"] == "L3"
        assert config["timeout"] == 30

    def test_config_bulk_update(self, tmp_path: Path):
        """一括 config 更新。"""
        store = SkillStateStore(state_path=tmp_path / "state.json")
        store.set_skill_config_bulk("V01", {"mode": "deep", "limit": 100})

        config = store.get_skill_config("V01")
        assert config["mode"] == "deep"
        assert config["limit"] == 100

    def test_get_all_states(self, tmp_path: Path):
        """全スキル状態の一括取得。"""
        store = SkillStateStore(state_path=tmp_path / "state.json")
        store.set_skill_enabled("V01", True)
        store.set_skill_enabled("V05", False)

        states = store.get_all_states()
        assert "V01" in states
        assert "V05" in states
        assert states["V05"]["enabled"] is False


# ── SkillDefinition 拡張テスト ──────────────────────────

class TestSkillDefinitionAdjunction:
    """SkillDefinition の ClawX 拡張フィールドテスト。"""

    def test_is_core_from_frontmatter(self, tmp_path: Path):
        """is_core: true の SKILL.md → SkillDefinition.is_core == True"""
        from hermeneus.src.skill_registry import SkillParser

        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(textwrap.dedent("""\
            ---
            id: "TEST01"
            name: "CoreTest"
            is_core: true
            is_bundled: true
            ---
            # TEST01: CoreTest
        """))

        parser = SkillParser()
        skill = parser.parse(skill_md)
        assert skill is not None
        assert skill.is_core is True
        assert skill.is_bundled is True

    def test_config_schema_from_frontmatter(self, tmp_path: Path):
        """frontmatter の config_schema → SkillDefinition.config_schema"""
        from hermeneus.src.skill_registry import SkillParser

        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(textwrap.dedent("""\
            ---
            id: "TEST02"
            name: "ConfigTest"
            config_schema:
              - key: "max_depth"
                type: "select"
                options: ["L1", "L2", "L3"]
                default: "L2"
              - key: "timeout"
                type: "number"
                default: 60
            ---
            # TEST02: ConfigTest
        """))

        parser = SkillParser()
        skill = parser.parse(skill_md)
        assert skill is not None
        assert len(skill.config_schema) == 2
        assert skill.config_schema[0]["key"] == "max_depth"
        assert skill.config_schema[1]["type"] == "number"

    def test_default_values(self, tmp_path: Path):
        """デフォルト: is_core=False, is_bundled=True, config_schema=[]"""
        from hermeneus.src.skill_registry import SkillParser

        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(textwrap.dedent("""\
            ---
            id: "TEST03"
            name: "DefaultTest"
            ---
            # TEST03: DefaultTest
        """))

        parser = SkillParser()
        skill = parser.parse(skill_md)
        assert skill is not None
        assert skill.is_core is False
        assert skill.is_bundled is True
        assert skill.config_schema == []


# ── 統合テスト(実行パス接続) ──────────────────────────

class TestSkillRegistryIntegration:
    """SkillRegistry の ClawX 統合テスト — 削除テスト対策。"""

    def test_disabled_skill_returns_none(self, tmp_path: Path):
        """disabled スキルは get() で None を返す。"""
        from hermeneus.src.skill_registry import SkillRegistry, SkillParser

        # SKILL.md を作成 (is_core=False)
        skill_dir = tmp_path / "v99-test"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(textwrap.dedent("""\
            ---
            id: "V99"
            name: "DisableTest"
            is_core: false
            ---
            # V99: DisableTest
        """))

        # state file で V99 を disabled に
        state_path = tmp_path / "skill_state.json"
        state_path.write_text(json.dumps({
            "skills": {"V99": {"enabled": False, "config": {}}}
        }))

        registry = SkillRegistry(search_paths=[tmp_path])
        # state store を手動注入
        from hermeneus.src.skill_state import SkillStateStore
        registry._state_store = SkillStateStore(state_path=state_path)

        result = registry.get("V99")
        assert result is None, "disabled skill should return None"

    def test_core_skill_always_returns(self, tmp_path: Path):
        """core スキルは disabled 設定されても get() で返る。"""
        from hermeneus.src.skill_registry import SkillRegistry

        skill_dir = tmp_path / "v98-core"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(textwrap.dedent("""\
            ---
            id: "V98"
            name: "CoreAlways"
            is_core: true
            ---
            # V98: CoreAlways
        """))

        state_path = tmp_path / "skill_state.json"
        state_path.write_text(json.dumps({
            "skills": {"V98": {"enabled": False, "config": {}}}
        }))

        registry = SkillRegistry(search_paths=[tmp_path])
        from hermeneus.src.skill_state import SkillStateStore
        registry._state_store = SkillStateStore(state_path=state_path)

        result = registry.get("V98")
        assert result is not None, "core skill should always return"
        assert result.is_core is True

    def test_load_bundles(self, tmp_path: Path):
        """skill_bundles.json のロードが動作する。"""
        from hermeneus.src.skill_registry import SkillRegistry

        bundles_file = tmp_path / "skill_bundles.json"
        bundles_file.write_text(json.dumps({
            "bundles": [
                {"id": "kernel", "name": "Kernel", "skills": ["V01"]},
                {"id": "telos", "name": "Telos", "skills": ["V05"]},
            ]
        }))

        registry = SkillRegistry(search_paths=[tmp_path])
        bundles = registry.load_bundles()
        assert len(bundles) == 2
        assert bundles[0]["id"] == "kernel"

    def test_list_all_with_state(self, tmp_path: Path):
        """list_all() が state とマージされた一覧を返す。"""
        from hermeneus.src.skill_registry import SkillRegistry

        skill_dir = tmp_path / "v97-listed"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(textwrap.dedent("""\
            ---
            id: "V97"
            name: "ListedTest"
            ---
            # V97: ListedTest
        """))

        state_path = tmp_path / "skill_state.json"
        state_path.write_text(json.dumps({
            "skills": {"V97": {"enabled": True, "config": {"depth": "L3"}}}
        }))

        registry = SkillRegistry(search_paths=[tmp_path])
        from hermeneus.src.skill_state import SkillStateStore
        registry._state_store = SkillStateStore(state_path=state_path)

        all_skills = registry.list_all()
        assert len(all_skills) >= 1

        v97 = next(s for s in all_skills if s["id"] == "V97")
        assert v97["enabled"] is True
        assert v97["config"]["depth"] == "L3"
