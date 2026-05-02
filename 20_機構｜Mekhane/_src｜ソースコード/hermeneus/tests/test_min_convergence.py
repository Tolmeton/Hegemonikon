"""
Macro Executor Convergence Test

min_convergence_iters がフロントマターから抽出され、
コンテキスト変数を通じて収束ループの最小反復回数に影響を与えることを検証する。
消去テスト: macro_executor.py の動的抽出ロジックを消すとこのテストが壊れる。
"""
import pytest
from unittest.mock import MagicMock

from hermeneus.src.macro_executor import ASTWalker, ExecutionContext
from hermeneus.src.ccl_ast import ConvergenceLoop, Workflow


class MockEstimator:
    def estimate(self, text):
        return 0.5
        
    def estimate_convergence(self, prev, curr) -> float:
        # 常に完全に一致して収束していると判定する (0.95以上)
        return 1.0


class TestMinConvergenceIters:
    def test_walk_convergence_loop_min_iters(self):
        """_walk_convergence_loop メソッドが min_iters を尊重するか"""
        executor = ASTWalker()
        executor.estimator = MockEstimator()
        
        # 収束判定は即座に true (1.0) になるが、min_iters までループが回るか
        ctx = ExecutionContext()
        ctx.current_output = "init"
        ctx.variables["$min_convergence_iters"] = 4
        
        # mock step node inside convergence loop
        node = ConvergenceLoop(body=Workflow(id="mock"), condition=MagicMock())
        
        # We need to mock the single step execution
        executor.walk = MagicMock()
        mock_child = MagicMock()
        mock_child.output = "static output"
        mock_child.entropy_after = 0.5
        mock_child.duration_ms = 100
        executor.walk.return_value = mock_child
        executor._emit_event = MagicMock()

        # Run loop
        result = executor._walk_convergence_loop(node, ctx)
        
        # Should have executed exactly 4 times despite immediate convergence
        assert executor.walk.call_count == 4
        assert len(result.children) == 4
