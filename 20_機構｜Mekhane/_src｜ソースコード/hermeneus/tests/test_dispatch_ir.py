"""#6: dispatch.py の CCL IR 統合テスト。

/ele+ Issue #6 で検出された「dispatch.py IR 統合テスト不在」を解消する。
テスト対象:
  - IR 生成成功時: result["ir"] に CCLIR が格納される
  - IR 生成失敗時: フォールバックし result["ir_error"] に理由が記録される
  - max_depth の depth_level への反映
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# プロジェクトルートを PATH に追加
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


class TestDispatchIRGeneration:
    """dispatch() が CCL IR を正しく生成・格納するテスト。"""

    def test_simple_workflow_generates_ir(self):
        """単一 WF の dispatch で result["ir"] に CCLIR が格納される。"""
        from hermeneus.src.dispatch import dispatch
        from hermeneus.src.ccl_ir import CCLIR

        result = dispatch("/noe+")

        assert "ir" in result, "result に 'ir' キーがない"
        assert isinstance(result["ir"], CCLIR), "result['ir'] が CCLIR ではない"
        assert "ir_error" not in result, "正常時に ir_error があってはならない"

    def test_ir_root_matches_ast_type(self):
        """IR のルートノードの ast_type が AST と整合する。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/noe+")
        ir = result.get("ir")
        assert ir is not None

        # /noe+ は単一 WF → root.ast_type は "Workflow"
        assert ir.root.ast_type == "Workflow"

    def test_sequence_generates_ir(self):
        """シーケンス CCL の dispatch で IR が正しく生成される。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/noe+_/dia+")
        ir = result.get("ir")
        assert ir is not None
        assert ir.root.ast_type == "Sequence"
        assert len(ir.root.children) == 2

    def test_ir_max_depth_matches_depth_level(self):
        """IR の max_depth が dispatch の depth_level と一致する。"""
        from hermeneus.src.dispatch import dispatch

        # /noe+ → depth 3
        result = dispatch("/noe+")
        ir = result.get("ir")
        assert ir is not None
        assert ir.max_depth == 3

        # /ene → depth 2
        result2 = dispatch("/ene")
        ir2 = result2.get("ir")
        assert ir2 is not None
        assert ir2.max_depth == 2

        # /bou- → depth 1
        result3 = dispatch("/bou-")
        ir3 = result3.get("ir")
        assert ir3 is not None
        assert ir3.max_depth == 1

    def test_ir_all_nodes_populated(self):
        """IR の all_nodes がルート + 子ノードを全て含む。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/noe+~/dia+")
        ir = result.get("ir")
        assert ir is not None
        # Oscillation ルート + 2子 = 最低3ノード
        assert len(ir.all_nodes) >= 3

    def test_ir_ccl_expr_stored(self):
        """IR に元の CCL 式が保存されている。"""
        from hermeneus.src.dispatch import dispatch

        ccl = "/noe+"
        result = dispatch(ccl)
        ir = result.get("ir")
        assert ir is not None
        assert ir.ccl_expr == ccl


class TestDispatchIRFallback:
    """IR 生成失敗時のフォールバックテスト。"""

    def test_ir_failure_stores_error(self):
        """ast_to_ir が例外を投げた場合、ir_error に記録される。"""
        from hermeneus.src.dispatch import dispatch

        # ast_to_ir をモックして例外を投げさせる
        with patch(
            "hermeneus.src.ccl_ir.ast_to_ir",
            side_effect=ValueError("テスト用 IR 生成エラー"),
        ):
            result = dispatch("/noe+")

        assert "ir" not in result, "失敗時に result['ir'] があってはならない"
        assert "ir_error" in result, "失敗時に ir_error が記録されるべき"
        assert "テスト用" in result["ir_error"]

    def test_ir_failure_falls_back_to_string_depth(self):
        """IR 生成失敗しても depth_level は文字列ベースで正しく判定される。"""
        from hermeneus.src.dispatch import dispatch

        with patch(
            "hermeneus.src.ccl_ir.ast_to_ir",
            side_effect=RuntimeError("IR 壊れた"),
        ):
            # /noe+ → '+' あり → depth_level=3
            result = dispatch("/noe+")

        # 文字列ベースフォールバックでも depth_level=3 が判定されるはず
        assert result.get("depth_level") == 3, "フォールバック時でも depth_level=3 が判定されるべき"


class TestDispatchIRDepthIntegration:
    """IR の max_depth が result["depth_level"] に反映されるテスト。"""

    def test_depth_3_for_plus(self):
        """/noe+ で depth_level=3。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/noe+")
        assert result.get("depth_level") == 3

    def test_depth_2_for_default(self):
        """/ene で depth_level=2。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/ene")
        assert result.get("depth_level") == 2

    def test_depth_1_for_minus(self):
        """/bou- で depth_level=1。"""
        from hermeneus.src.dispatch import dispatch

        result = dispatch("/bou-")
        assert result.get("depth_level") == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
