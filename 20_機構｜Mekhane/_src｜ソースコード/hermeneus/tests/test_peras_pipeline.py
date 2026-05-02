# PROOF: [L2/テスト] <- hermeneus/tests/test_peras_pipeline.py
"""
PerasPipeline Unit Tests

テスト内容:
- 全6 Series の初期化
- 定理プロンプト生成
- Limit 出力パーサー
- Phase 3 フォーマット
"""

import pytest
from hermeneus.src.peras_pipeline import (
    PerasPipeline,
    VerbResult,
    LimitResult,
    VERB_DEFINITIONS,
    SERIES_COORDINATES,
    PERAS_SERIES,
)


class TestPerasPipelineInit:
    """初期化テスト"""

    @pytest.mark.parametrize("series_id", ["t", "m", "k", "d", "o", "c"])
    def test_valid_series_init(self, series_id: str):
        """全6 Series で初期化できること"""
        p = PerasPipeline(series_id=series_id)
        assert p.series_id == series_id
        assert len(p.verbs) == 4
        assert p.coordinate is not None

    def test_invalid_series_raises(self):
        """不正な Series ID でエラーになること"""
        with pytest.raises(ValueError, match="Unknown series_id"):
            PerasPipeline(series_id="z")

    def test_series_names(self):
        """各 Series の名前が正しいこと"""
        expected = {
            "t": "Telos", "m": "Methodos", "k": "Krisis",
            "d": "Diástasis", "o": "Orexis", "c": "Chronos",
        }
        for sid, name in expected.items():
            p = PerasPipeline(series_id=sid)
            assert p.series_name == name

    def test_depth_parameter(self):
        """深度パラメータが設定されること"""
        p = PerasPipeline(series_id="t", depth="-")
        assert p.depth == "-"
        p2 = PerasPipeline(series_id="t", depth="+")
        assert p2.depth == "+"


class TestSkillExtractor:
    """SKILL.md コア抽出テスト"""

    def test_extract_skill_core_valid(self):
        """有効な定理IDでコアテキストが抽出されること"""
        from hermeneus.src.peras_pipeline import _extract_skill_core
        # V01 Noesis (確実にあるものをテスト)
        core = _extract_skill_core("noe", 1, "Noesis")
        # 少なくとも何らかのテキストが抽出されているはず
        assert len(core) > 0
        assert "思考プロセス" in core or "フェーズ構成" in core

    def test_extract_skill_core_invalid(self):
        """無効な定理IDでは空文字列が返ること"""
        from hermeneus.src.peras_pipeline import _extract_skill_core
        core = _extract_skill_core("invalid_id", 99, "Invalid")
        assert core == ""

    def test_extract_section(self):
        """セクション抽出が正しく機能すること"""
        from hermeneus.src.peras_pipeline import _extract_section
        lines = [
            "## Processing Logic",
            "Line 1",
            "Line 2",
            "Line 3",
            "## Next Section",
            "Line 4"
        ]
        # max_lines=2 の場合
        extracted = _extract_section(lines, "## Processing Logic", max_lines=2)
        assert "Line 1\nLine 2" in extracted
        assert "Line 3" not in extracted
        assert "Line 4" not in extracted

        # Header Not Found
        not_found = _extract_section(lines, "## Missing", max_lines=5)
        assert not_found == ""


class TestVerbDefinitions:
    """定理定義の完全性テスト"""

    def test_all_series_have_verbs(self):
        """全6 Series に4定理が定義されていること"""
        for series_id in ["t", "m", "k", "d", "o", "c"]:
            assert series_id in VERB_DEFINITIONS
            assert len(VERB_DEFINITIONS[series_id]) == 4

    def test_verb_numbers_sequential(self):
        """定理番号が1-24で連続すること"""
        all_nums = []
        for series_id in ["t", "m", "k", "d", "o", "c"]:
            for verb in VERB_DEFINITIONS[series_id]:
                all_nums.append(verb["num"])
        assert sorted(all_nums) == list(range(1, 25))

    def test_all_verbs_have_required_fields(self):
        """全定理に必須フィールドがあること"""
        for series_id, verbs in VERB_DEFINITIONS.items():
            for verb in verbs:
                assert "id" in verb
                assert "name" in verb
                assert "num" in verb
                assert "role" in verb


class TestCoordinates:
    """座標定義テスト"""

    def test_all_series_have_coordinates(self):
        """全6 Series に座標が定義されていること"""
        for series_id in ["t", "m", "k", "d", "o", "c"]:
            assert series_id in SERIES_COORDINATES
            coord = SERIES_COORDINATES[series_id]
            assert "axis" in coord
            assert "poles" in coord
            assert len(coord["poles"]) == 2


class TestVerbPromptGeneration:
    """定理プロンプト生成テスト"""

    def test_prompt_contains_verb_info(self):
        """プロンプトに定理情報が含まれること"""
        p = PerasPipeline(series_id="t")
        verb = VERB_DEFINITIONS["t"][0]  # noe
        prompt = p._build_verb_prompt(verb, "テスト対象")

        assert "Noēsis" in prompt
        assert "V01" in prompt
        assert "テスト対象" in prompt
        assert "Value" in prompt
        assert "Epistemic" in prompt

    def test_prompt_contains_context(self):
        """プロンプトにコンテキストが含まれること"""
        p = PerasPipeline(series_id="m")
        verb = VERB_DEFINITIONS["m"][0]
        prompt = p._build_verb_prompt(verb, "方法論の分析")

        assert "方法論の分析" in prompt
        assert "Function" in prompt


class TestLimitParser:
    """Limit 出力パーサーテスト"""

    def test_parse_well_formed_output(self):
        """整形された出力を正しくパースできること"""
        p = PerasPipeline(series_id="t")
        text = """
C0_PW: V01 高, V02 中, V03 中, V04 低
C1_CONTRAST: 認識と行為が一致, 探求は未完了
C2_FUSION: 目的は明確だが実行手段が不足
C3_KALON: バランスは良好
CONCLUSION: 目的は正しいが方法論の精緻化が必要
CONFIDENCE: 75
COORDINATE: Epistemic寄り
"""
        result = p._parse_limit_output(text)
        assert "V01 高" in result.c0_pw
        assert result.confidence == 0.75
        assert "Epistemic" in result.coordinate_value
        assert "目的は正しい" in result.conclusion

    def test_parse_empty_output(self):
        """空の出力でもエラーにならないこと"""
        p = PerasPipeline(series_id="t")
        result = p._parse_limit_output("")
        assert result.confidence == 0.0
        assert result.conclusion == ""

    def test_parse_unstructured_output(self):
        """構造化されていない出力はフォールバックすること"""
        p = PerasPipeline(series_id="t")
        result = p._parse_limit_output("これは自由形式の回答です。")
        assert "自由形式" in result.conclusion
        assert result.confidence == 0.5


class TestPhase3Format:
    """Phase 3 出力フォーマットテスト"""

    def test_format_with_results(self):
        """正常な結果をフォーマットできること"""
        p = PerasPipeline(series_id="t")

        verb_results = [
            VerbResult(
                verb_id="noe", verb_name="Noēsis", verb_number=1,
                output="深い認識の結果", success=True
            ),
        ]
        limit_result = LimitResult(
            conclusion="統合結論",
            confidence=0.8,
            coordinate_value="Epistemic寄り",
            c0_pw="均等",
            c1_contrast="一致",
            c2_fusion="融合済み",
            c3_kalon="検証OK",
        )

        output = p._phase3_format(verb_results, limit_result)
        assert "/t Peras 結果" in output
        assert "統合結論" in output
        assert "80%" in output
        assert "Epistemic" in output
        assert "✅" in output

    def test_format_with_failed_verb(self):
        """失敗した定理が ❌ で表示されること"""
        p = PerasPipeline(series_id="m")

        verb_results = [
            VerbResult(
                verb_id="ske", verb_name="Skepsis", verb_number=5,
                output="", success=False, error="timeout"
            ),
        ]
        limit_result = LimitResult(conclusion="部分結論", confidence=0.3)

        output = p._phase3_format(verb_results, limit_result)
        assert "❌" in output
