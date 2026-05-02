import pytest
import sys
from pathlib import Path

# パッケージパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hermeneus.src.parser import CCLParser


class TestQSeriesParsing:
    """Q[X→Y] 循環修飾子のパーステスト"""

    def test_basic_q_series(self):
        """基本的な Q[Va→Pr] パース"""
        p = CCLParser()
        ast = p.parse("/noe+ Q[Va\u2192Pr]")
        assert ast.modifiers.get("_q_src") == "Va"
        assert ast.modifiers.get("_q_dst") == "Pr"
        assert ast.modifiers.get("_q_edge") == "Va\u2192Pr"
        assert len(p.errors) == 0

    def test_q_series_all_valid_coords(self):
        """有効な全座標ペアの組み合わせ"""
        coords = ["Va", "Fu", "Pr", "Sc", "Vl", "Te"]
        for src in coords:
            for dst in coords:
                if src == dst:
                    continue
                p = CCLParser()
                ast = p.parse(f"/noe Q[{src}\u2192{dst}]")
                assert ast.modifiers.get("_q_src") == src, f"{src}\u2192{dst}"
                assert ast.modifiers.get("_q_dst") == dst, f"{src}\u2192{dst}"
                assert len(p.errors) == 0, f"{src}\u2192{dst}: {p.errors}"

    def test_q_series_same_coordinate_error(self):
        """同一座標エラー"""
        p = CCLParser()
        p.parse("/noe Q[Va\u2192Va]")
        assert len(p.errors) == 1
        assert "\u540c\u4e00" in p.errors[0]

    def test_q_series_invalid_coordinate_error(self):
        """無効な座標エラー"""
        p = CCLParser()
        p.parse("/noe Q[XX\u2192YY]")
        assert len(p.errors) == 1
        assert "\u7121\u52b9" in p.errors[0]

    def test_q_series_with_bracket_modifiers(self):
        """Q-series + ブラケット修飾子の共存"""
        p = CCLParser()
        ast = p.parse("/noe+ Q[Fu\u2192Pr] [Va:E]")
        assert ast.modifiers.get("_q_src") == "Fu"
        assert ast.modifiers.get("_q_dst") == "Pr"
        assert ast.modifiers.get("Va") == "E"

    def test_q_series_preserves_operators(self):
        """Q-series が演算子を壊さない"""
        p = CCLParser()
        ast = p.parse("/noe+ Q[Va\u2192Pr]")
        assert ast.mode == "+"

    def test_q_series_wf_id_preserved(self):
        """Q-series が WF ID を壊さない"""
        p = CCLParser()
        ast = p.parse("/bou Q[Sc\u2192Te]")
        assert ast.id == "bou"


class TestXSeriesDotNotation:
    """X-series .XY ドット記法のパーステスト"""

    def test_basic_x_series_vf(self):
        """.VF (Value x Function) パース"""
        p = CCLParser()
        ast = p.parse("/noe+.VF")
        assert ast.modifiers.get("_x_edge") == "X1"
        assert ast.modifiers.get("_x_coords") == "Va\u00d7Fu"
        assert ast.modifiers.get("_x_dot") == "VF"

    def test_x_series_d2_group(self):
        """群I: d2 内結合 (3本)"""
        cases = {"VF": "X1", "VP": "X2", "FP": "X3"}
        for dot, expected_edge in cases.items():
            p = CCLParser()
            ast = p.parse(f"/noe.{dot}")
            assert ast.modifiers.get("_x_edge") == expected_edge, f".{dot}"

    def test_x_series_d2d3_group(self):
        """群II: d2xd3 結合 (9本)"""
        cases = {
            "VS": "X4", "VV": "X5", "VT": "X6",
            "FS": "X7", "FV": "X8", "FT": "X9",
            "PS": "X10", "PV": "X11", "PT": "X12",
        }
        for dot, expected_edge in cases.items():
            p = CCLParser()
            ast = p.parse(f"/noe.{dot}")
            assert ast.modifiers.get("_x_edge") == expected_edge, f".{dot}"

    def test_x_series_d3_group(self):
        """群III: d3 内結合 (3本)"""
        cases = {"SV": "X13", "ST": "X14", "VlTe": "X15"}
        for dot, expected_edge in cases.items():
            p = CCLParser()
            ast = p.parse(f"/noe.{dot}")
            assert ast.modifiers.get("_x_edge") == expected_edge, f".{dot}"

    def test_x_series_clears_relation(self):
        """.XY は relation フィールドをクリアする"""
        p = CCLParser()
        ast = p.parse("/noe.VF")
        assert ast.relation is None

    def test_unknown_dot_notation_error(self):
        """未知の .XY でエラー"""
        p = CCLParser()
        p.parse("/noe.ZZ")
        assert any("\u672a\u77e5" in e for e in p.errors)

    def test_single_char_relation_preserved(self):
        """1文字 .d/.h/.x は従来通り"""
        p = CCLParser()
        ast = p.parse("/noe.d")
        # .d は RELATION_PARTNERS に noe がない場合、Workflow として返る
        assert type(ast).__name__ in ("Sequence", "Workflow")

    def test_x_series_with_operators(self):
        """.XY が演算子と共存"""
        p = CCLParser()
        ast = p.parse("/noe+.VF")
        assert ast.mode == "+"
        assert ast.modifiers.get("_x_edge") == "X1"
