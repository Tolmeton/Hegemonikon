# PROOF: [L2/テスト] <- hermeneus/tests/test_skill_registry.py
"""
SkillRegistry テスト

全 24 SKILL.md のパース、Phase 抽出、派生選択、
execution plan 生成を検証する。
"""

import pytest
from pathlib import Path

from hermeneus.src.skill_registry import (
    SkillParser,
    SkillRegistry,
    SkillDefinition,
    PhaseDefinition,
    get_skill,
    list_skills,
)


SKILLS_DIR = Path.home() / "oikos" / "hegemonikon" / "nous" / "skills"


class TestSkillParser:
    """SkillParser のユニットテスト"""
    
    def setup_method(self):
        self.parser = SkillParser()
    
    def test_parse_v05_skepsis(self):
        """V05 Skepsis がパースできること"""
        path = SKILLS_DIR / "methodos" / "v05-skepsis" / "SKILL.md"
        if not path.exists():
            pytest.skip("SKILL.md not found")
        
        skill = self.parser.parse(path)
        assert skill is not None
        assert skill.id == "V05"
        assert skill.name == "Skepsis"
        assert skill.family == "Methodos"
        assert len(skill.phases) >= 2, f"Expected >=2 phases, got {len(skill.phases)}"
    
    def test_parse_v06_synagoge(self):
        """V06 Synagōgē がパースできること"""
        path = SKILLS_DIR / "methodos" / "v06-synagoge" / "SKILL.md"
        if not path.exists():
            pytest.skip("SKILL.md not found")
        
        skill = self.parser.parse(path)
        assert skill is not None
        assert skill.id == "V06"
        assert skill.name in ("Synagōgē", "Synagoge")
    
    def test_parse_v09_katalepsis(self):
        """V09 Katalēpsis がパースできること"""
        path = SKILLS_DIR / "krisis" / "v09-katalepsis" / "SKILL.md"
        if not path.exists():
            pytest.skip("SKILL.md not found")
        
        skill = self.parser.parse(path)
        assert skill is not None
        assert skill.id == "V09"
    
    def test_parse_frontmatter_required(self):
        """frontmatter なしのファイルは None を返すこと"""
        # 空の一時ファイル
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# No frontmatter\nJust content\n")
            path = Path(f.name)
        
        skill = self.parser.parse(path)
        assert skill is None
        path.unlink()

    def test_parse_execution_contract(self, tmp_path: Path):
        """execution_contract frontmatter を読み取れること"""
        skill_dir = tmp_path / "ske"
        skill_dir.mkdir()
        path = skill_dir / "SKILL.md"
        path.write_text(
            """---
name: ske
execution_contract:
  explicit_invocation: strict
  fallback_behavior: declare_and_stop
  default_depth: L2
  required_outputs:
    - phase_0
    - checkpoints
---

## PHASE 0: Test
body
""",
            encoding="utf-8",
        )
        skill = self.parser.parse(path)
        assert skill is not None
        assert skill.execution_contract.explicit_invocation == "strict"
        assert skill.execution_contract.required_outputs == ["phase_0", "checkpoints"]


class TestSkillRegistry:
    """SkillRegistry のテスト"""
    
    def setup_method(self):
        self.registry = SkillRegistry(skills_dir=SKILLS_DIR)
    
    def test_get_v05(self):
        """V05 を取得できること"""
        skill = self.registry.get("V05")
        assert skill is not None
        assert skill.id == "V05"
    
    def test_get_case_insensitive(self):
        """大文字小文字を区別しないこと"""
        skill = self.registry.get("v05")
        assert skill is not None
        assert skill.id == "V05"
    
    def test_get_nonexistent(self):
        """存在しない ID は None"""
        skill = self.registry.get("V99")
        assert skill is None
    
    def test_load_all(self):
        """全 SKILL.md をロードできること"""
        all_skills = self.registry.load_all()
        assert len(all_skills) >= 20, f"Expected >=20 skills, got {len(all_skills)}"
    
    def test_list_ids(self):
        """ID 一覧が取得できること"""
        ids = self.registry.list_ids()
        assert len(ids) >= 20
        assert "V05" in ids
        assert "V06" in ids
    
    def test_cache_works(self):
        """キャッシュが機能すること"""
        skill1 = self.registry.get("V05")
        skill2 = self.registry.get("V05")
        assert skill1 is skill2  # 同一オブジェクト


class TestExecutionPlan:
    """get_execution_plan のテスト"""
    
    def setup_method(self):
        self.registry = SkillRegistry(skills_dir=SKILLS_DIR)
    
    def test_l2_plan(self):
        """L2 で Phase リストが返ること"""
        phases = self.registry.get_execution_plan("V05", depth="L2")
        assert len(phases) >= 2, f"Expected >=2 phases for L2, got {len(phases)}"
    
    def test_l3_includes_all(self):
        """L3 で全 Phase が返ること"""
        phases = self.registry.get_execution_plan("V05", depth="L3")
        l2_phases = self.registry.get_execution_plan("V05", depth="L2")
        assert len(phases) >= len(l2_phases)
    
    def test_l0_minimal(self):
        """L0 で最小限の Phase が返ること"""
        phases = self.registry.get_execution_plan("V05", depth="L0")
        assert len(phases) <= 2  # Phase 0 only
    
    def test_phase_has_content(self):
        """Phase に内容があること"""
        phases = self.registry.get_execution_plan("V05", depth="L2")
        if phases:
            assert phases[0].name != ""
            assert phases[0].number >= 0

    def test_phase_to_prompt_with_context(self):
        """PhaseDefinition から LLM プロンプトが生成できること (コンテキストあり)"""
        skill = self.registry.get("V05")
        if not skill or not skill.phases:
            pytest.skip("V05 or phases not found")
        p0 = skill.phases[0]
        
        prompt = p0.to_prompt(skill.id, skill.name, context="ユーザーからの入力: テスト")
        assert "V05" in prompt
        assert skill.name in prompt
        assert f"Phase {p0.number}" in prompt
        assert p0.name in prompt
        assert p0.raw_content.strip()[:30] in prompt
        assert "ユーザーからの入力: テスト" in prompt

    def test_phase_to_prompt_no_context(self):
        """PhaseDefinition から LLM プロンプトが生成できること (コンテキストなし)"""
        skill = self.registry.get("V05")
        if not skill or not skill.phases:
            pytest.skip("V05 or phases not found")
        p0 = skill.phases[0]
        
        prompt = p0.to_prompt(skill.id, skill.name)
        assert "V05" in prompt
        assert "入力コンテキスト" not in prompt

    def test_phase_to_prompt_includes_anti_shallow_contract(self):
        """Phase prompt が Trace/Negativa/Iso の強制規約を含むこと"""
        skill = self.registry.get("V05")
        if not skill or not skill.phases:
            pytest.skip("V05 or phases not found")
        p0 = skill.phases[0]

        prompt = p0.to_prompt(skill.id, skill.name)
        assert "Anti-Shallow" in prompt
        assert "Trace 必須" in prompt
        assert "Negativa 必須" in prompt
        assert "Iso 必須" in prompt
        assert "言い換えで埋めず" in prompt

    def test_build_phase_instructions_enforces_native_artifact_rules(self, tmp_path: Path):
        """compile-only 用指示が Trace/Negativa/Iso と累積を強制すること"""
        skill_dir = tmp_path / "ske"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
id: V05
name: Skepsis
---

## PHASE 0: Intake
S[0.1] SOURCE を読む

## PHASE 1: Expansion
S[1.1] 候補を列挙する
""",
            encoding="utf-8",
        )

        registry = SkillRegistry(skills_dir=tmp_path)
        instructions = registry.build_phase_instructions("ske", depth="L2", context="ctx")

        assert "Trace 義務" in instructions
        assert "Negativa 義務" in instructions
        assert "Iso 義務" in instructions
        assert "累積義務" in instructions
        assert "representation_role 義務" in instructions
        assert "rejection_ledger 義務" in instructions
        assert "carry-forward manifest 義務" in instructions
        assert "S[x.y]" in instructions
        assert "[CHECKPOINT PHASE 0/" in instructions
        assert "native artifact" in instructions
        assert "**representation_role**:" in instructions
        assert "[Carry-Forward Manifest]" in instructions
        assert "[Rejection Ledger]" in instructions

    def test_build_phase_instructions_includes_implementation_renderer_policy(self, tmp_path: Path):
        """O4 実装報告では reader-facing renderer template を注入すること"""
        skill_dir = tmp_path / "ene"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            """---
id: O4
name: Energeia
---

## PHASE 0: Read-Resolve-Proceed
前提条件を確認する

## PHASE 1: Execute
変更を実装する
""",
            encoding="utf-8",
        )

        registry = SkillRegistry(skills_dir=tmp_path)
        instructions = registry.build_phase_instructions("ene", depth="L2", context="ctx")

        assert "実装報告 Renderer Policy" in instructions
        assert "unordered list を default renderer にしてはならない" in instructions
        assert "[Implementation Report Template]" in instructions
        assert "成果核 / 変更面 / 検証 / 偏差 / 復元 / annex" in instructions
        assert "path | intent | change" in instructions


class TestAllSkillsParse:
    """全 24 SKILL.md がパースできることの網羅テスト"""
    
    def test_all_skills_parseable(self):
        """全 SKILL.md がエラーなくパースできる"""
        registry = SkillRegistry(skills_dir=SKILLS_DIR)
        all_skills = registry.load_all()
        
        # 少なくとも 24 件
        assert len(all_skills) >= 36, (
            f"Expected 24 skills, got {len(all_skills)}. "
            f"IDs: {sorted(all_skills.keys())}"
        )
    
    def test_all_skills_have_phases(self):
        """全 SKILL.md に Phase 定義があること"""
        registry = SkillRegistry(skills_dir=SKILLS_DIR)
        all_skills = registry.load_all()
        
        no_phase = []
        for skill_id, skill in all_skills.items():
            if len(skill.phases) == 0:
                no_phase.append(skill_id)
        
        assert len(no_phase) == 0, (
            f"Skills without phases: {no_phase}"
        )
    
    def test_all_skills_have_id(self):
        """全 SKILL.md に ID があること"""
        registry = SkillRegistry(skills_dir=SKILLS_DIR)
        all_skills = registry.load_all()
        
        for skill_id, skill in all_skills.items():
            assert skill.id != "", f"Skill {skill_id} has empty id"
            assert skill.name != "", f"Skill {skill_id} has empty name"


class TestRegressions:
    """品質精査で発見した問題のリグレッションテスト"""
    
    def setup_method(self):
        self.registry = SkillRegistry(skills_dir=SKILLS_DIR)
    
    def test_v02_phase_1_2_combined_header(self):
        """V02 Boulēsis の PHASE 1-2 結合ヘッダーが正しくパースされる"""
        skill = self.registry.get("V02")
        if not skill:
            pytest.skip("V02 not found")
        
        phase_nums = [p.number for p in skill.phases]
        # Phase 1 が存在すること (PHASE 1-2 から抽出)
        assert 1 in phase_nums, f"Phase 1 not found in V02, got {phase_nums}"
        
        # Phase 1 の名前が "2" ではないこと (正規表現のバグで壊れていた)
        phase_1 = [p for p in skill.phases if p.number == 1][0]
        assert phase_1.name != "2", (
            f"V02 Phase 1 name is '2' — PHASE 1-2 header was parsed incorrectly"
        )
        assert len(phase_1.name) > 3, f"V02 Phase 1 name too short: '{phase_1.name}'"
    
    def test_v14_phases_start_from_correct_number(self):
        """V14 Synopsis の Phase 構成が正しいこと"""
        skill = self.registry.get("V14")
        if not skill:
            pytest.skip("V14 not found")
        
        phase_nums = [p.number for p in skill.phases]
        # V14 は Phase 0 がない (Phase 1 から開始) — これは SKILL.md の構造
        assert len(phase_nums) >= 3, f"V14 should have >=3 phases, got {phase_nums}"
    
    def test_phase_names_not_corrupted(self):
        """全スキルの Phase 名が壊れていないこと"""
        all_skills = self.registry.load_all()
        corrupted = []
        
        for sid, skill in all_skills.items():
            for phase in skill.phases:
                # Phase 名が1文字数字だけなら壊れている
                if phase.name.strip().isdigit():
                    corrupted.append(f"{sid} Phase {phase.number}: name='{phase.name}'")
                # Phase 名が空
                if not phase.name.strip():
                    corrupted.append(f"{sid} Phase {phase.number}: empty name")
        
        assert len(corrupted) == 0, f"Corrupted phase names:\n" + "\n".join(corrupted)
    
    def test_all_phase_numbers_are_sequential(self):
        """Phase 番号が概ね連続していること"""
        all_skills = self.registry.load_all()
        gaps = []
        
        for sid, skill in all_skills.items():
            nums = sorted(p.number for p in skill.phases)
            if not nums:
                continue
            # 最初の Phase 番号が 0 か 1 であること
            if nums[0] > 1:
                gaps.append(f"{sid}: starts at Phase {nums[0]}")
        
        # V14 は Phase 1 から始まるので1件は許容
        assert len(gaps) <= 2, f"Unexpected phase gaps:\n" + "\n".join(gaps)
    
    def test_o1_alias_resolution(self):
        """O1 で V01 Noēsis を取得できること (エイリアス解決)"""
        skill = self.registry.get("O1")
        assert skill is not None, "O1 alias should resolve to V01 Noēsis"
        assert skill.name in ("Noēsis", "Noesis"), f"Expected Noēsis, got {skill.name}"
    
    def test_o4_alias_resolution(self):
        """O4 で V04 Energeia を取得できること"""
        skill = self.registry.get("O4")
        assert skill is not None, "O4 alias should resolve to V04 Energeia"
