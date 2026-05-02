# PROOF: [L3/テスト] <- hermeneus/tests/test_template_enforcement.py Q4 Output Template Enforcement
"""
Q4 出力テンプレート強制テスト

translator.py が WorkflowRegistry から output_template を読み込み、
LMQL プロンプトに動的挿入することを検証する。
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermeneus.src import compile_ccl


# All 6 hub WFs that have output_template in their frontmatter
HUB_WFS = ["t", "m", "k", "d", "c", "o"]


class TestOutputTemplateInsertion:
    """Q4: 出力テンプレートが LMQL に挿入されるか"""

    @pytest.mark.parametrize("wf_id", HUB_WFS)
    def test_hub_wf_has_template_in_lmql(self, wf_id: str):
        """各ハブWFのコンパイル結果にテンプレートが含まれる"""
        lmql_code = compile_ccl(f"/{wf_id}")
        assert "出力テンプレート" in lmql_code, (
            f"/{wf_id} のコンパイル結果にテンプレートが挿入されていない"
        )

    @pytest.mark.parametrize("wf_id", HUB_WFS)
    def test_template_contains_structural_sections(self, wf_id: str):
        """テンプレートには構造的セクション (4射サマリー等) が含まれる"""
        lmql_code = compile_ccl(f"/{wf_id}")
        # 全ハブWFテンプレートに共通する「4射サマリー」セクション
        assert "4射サマリー" in lmql_code or "統合判断" in lmql_code, (
            f"/{wf_id} テンプレートに構造的セクションがない"
        )

    def test_nonexistent_wf_no_template(self):
        """存在しないWFはテンプレートなしでも正常にコンパイルできる"""
        lmql_code = compile_ccl("/noe")
        # /noe はハブWFではないのでテンプレートは任意
        assert "[RESULT]" in lmql_code

    def test_template_is_escaped(self):
        """テンプレート内の特殊文字がエスケープされている"""
        lmql_code = compile_ccl("/t")
        # テンプレートが存在するなら、改行は \\n に変換されているはず
        assert "出力テンプレート" in lmql_code
        # LMQL 文字列内に生の改行がないことを確認 (テンプレート行内)
        for line in lmql_code.split("\n"):
            if "出力テンプレート" in line:
                # この行は1行の長い文字列であるべき
                assert len(line) > 100, "テンプレートが正しくインライン化されていない"
                break


class TestTemplatePathResolution:
    """テンプレートパスの解決テスト"""

    def test_all_hub_templates_exist(self):
        """全ハブWFの output_template ファイルが実際に存在する"""
        from hermeneus.src.registry import get_workflow

        for wf_id in HUB_WFS:
            wf_def = get_workflow(wf_id)
            assert wf_def is not None, f"/{wf_id} の定義が見つからない"

            tmpl_path = wf_def.metadata.get("output_template")
            assert tmpl_path, f"/{wf_id} に output_template メタデータがない"

            # パス解決: source_path.parents を遡る
            resolved = None
            if wf_def.source_path:
                for p in wf_def.source_path.parents:
                    candidate = p / tmpl_path
                    if candidate.exists():
                        resolved = candidate
                        break

            assert resolved is not None, (
                f"/{wf_id} のテンプレートファイルが見つからない: {tmpl_path}"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
