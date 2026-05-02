# PROOF: [L3/テスト] <- hermeneus/tests/test_outer_product.py % 演算子テスト
"""
Hermēneus Outer Product (% / *%) Unit Tests

% (Outer Product) と *% (Fuse-Outer) の動作保証。
parser のフラグ (outer_product, fuse_outer) が
MacroExecutor で正しく処理されるかを検証する。

Origin: 2026-02-25 Bugfix
"""

import pytest
import sys
from pathlib import Path

from hermeneus.src.parser import CCLParser
from hermeneus.src.macro_executor import MacroExecutor, ExecutionContext, StepType
from hermeneus.src.ccl_ast import Fusion

def mock_step_handler(node_id: str, params: dict, ctx: ExecutionContext) -> str:
    """固定の出力を返すダミーハンドラ（ASTWalker 用の Callable）"""
    return f"Result of {node_id}"

class TestOuterProduct:
    """外積展開のテスト"""
    
    def setup_method(self):
        self.parser = CCLParser()
        self.executor = MacroExecutor(step_handler=mock_step_handler)
        
    def test_percentage_outer_product(self):
        """% 単独での外積展開テスト"""
        # Parse
        ast = self.parser.parse('/noe % /dia')
        
        # AST check
        assert isinstance(ast, Fusion)
        assert ast.outer_product is True
        assert ast.fuse_outer is False
        
        # Execute
        ctx = ExecutionContext(initial_input="テスト入力")
        result = self.executor.walker.walk(ast, ctx)
        
        # Validate
        assert result.step_type == StepType.FUSION
        assert result.node_id == "fusion%"
        assert "[OuterProduct:" in result.output
        assert "×" in result.output  # 組み合わせの掛け合わせ記号
        
    def test_fuse_outer_product(self):
        """*% 内積+外積の展開テスト"""
        # Parse
        ast = self.parser.parse('/noe *% /dia')
        
        # AST check
        assert isinstance(ast, Fusion)
        assert ast.outer_product is False
        assert ast.fuse_outer is True
        
        # Execute
        ctx = ExecutionContext(initial_input="テスト入力")
        result = self.executor.walker.walk(ast, ctx)
        
        # Validate
        assert result.step_type == StepType.FUSION
        assert result.node_id == "fusion*%"
        assert "[OuterProduct:" in result.output
        assert "×" in result.output

    def test_normal_fusion(self):
        """* 通常融合のテスト (外積と区別)"""
        # Parse
        ast = self.parser.parse('/noe * /dia')
        
        # AST check
        assert isinstance(ast, Fusion)
        assert ast.outer_product is False
        assert ast.fuse_outer is False
        
        # Execute
        ctx = ExecutionContext(initial_input="テスト入力")
        result = self.executor.walker.walk(ast, ctx)
        
        # Validate
        assert result.step_type == StepType.FUSION
        assert result.node_id == "fusion"
        assert "[Fusion]" in result.output
        assert "[OuterProduct:" not in result.output

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
