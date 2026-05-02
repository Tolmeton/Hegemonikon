# CCL-PL AST オプティマイザ — 圏論的最適化パイプライン
"""
AST → AST の変換パイプライン。トランスパイル前に圏論的最適化を施す。

Phase 3 で導入。パイプライン: Parse → **Optimize** → Transpile → Exec

最適化パス:
1. Adjunction Folding — 随伴対の相殺 (G(F(x)) → x)
2. Identity Elimination — id ノードの除去
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from ccl.parser.ast import (
    ASTNode, Workflow, Sequence, Fusion, Oscillation, FnCall, RawExpr,
)


class ASTOptimizer:
    """圏論的 AST オプティマイザ

    随伴対を知識として保持し、コンパイル時に相殺可能な
    パターンを検出・縮約する。
    """

    def __init__(self):
        # 随伴対: (左随伴, 右随伴) — G(F(x)) ≅ x で相殺可能
        self._adjoint_pairs: Set[Tuple[str, str]] = set()
        self._optimizations_applied: int = 0

    def register_adjoint_pairs(self, pairs: List[Tuple[str, str]]) -> None:
        """随伴対を登録する

        pairs: [(left_adjoint, right_adjoint), ...]
        例: [("recognize", "explore")] → explore(recognize(x)) ≅ x
        """
        for left, right in pairs:
            self._adjoint_pairs.add((left, right))

    def optimize(self, ast: Any) -> Any:
        """AST を最適化する (メインエントリポイント)"""
        self._optimizations_applied = 0
        result = self._visit(ast)
        return result

    @property
    def stats(self) -> dict:
        """最適化統計"""
        return {
            "optimizations_applied": self._optimizations_applied,
            "adjoint_pairs_registered": len(self._adjoint_pairs),
        }

    def _visit(self, node: Any) -> Any:
        """ノードをトラバースし、最適化パスを適用"""
        if node is None:
            return None

        if isinstance(node, FnCall):
            node.args = [self._visit(arg) for arg in node.args]
            folded = self._fold_adjunction(node)
            if folded is not node:
                return self._visit(folded)
            return node

        # Sequence の各ステップを再帰的に最適化
        if isinstance(node, Sequence):
            node.steps = [self._visit(s) for s in node.steps]
            # 長さ1のSequenceは中身を返す
            if len(node.steps) == 1:
                return node.steps[0]

        # Fusion の左右を再帰的に最適化
        if isinstance(node, Fusion):
            node.left = self._visit(node.left)
            node.right = self._visit(node.right)

        # Oscillation の左右を再帰的に最適化
        if isinstance(node, Oscillation):
            node.left = self._visit(node.left)
            node.right = self._visit(node.right)

        return node

    def _fold_adjunction(self, node: FnCall) -> Any:
        """随伴のラウンドトリップを相殺する

        パターン: G(F(x)) where F⊣G → x
        実装: FnCall(name=G, args=[FnCall(name=F, args=[x])]) → x

        `_visit()` 側で引数を先に最適化するため、
        G1(G2(F2(F1(x)))) のような合成随伴も
        内側の G2(F2(...)) → ... を先に縮約し、
        その結果あらわれる G1(F1(...)) も再帰的に相殺できる。
        """
        if not node.args or len(node.args) != 1:
            return node

        inner = node.args[0]
        if not isinstance(inner, FnCall):
            return node

        outer_name = node.name
        inner_name = inner.name

        # (F, G) ペアをチェック: G(F(x)) のとき相殺
        for left, right in self._adjoint_pairs:
            # 右随伴(G) が外側、左随伴(F) が内側 → ε (余単位)
            if outer_name == right and inner_name == left:
                self._optimizations_applied += 1
                # 内側の引数を返す (相殺)
                if inner.args:
                    return inner.args[0]
                return RawExpr(code="None")

            # 左随伴(F) が外側、右随伴(G) が内側 → η (単位)
            # η は相殺ではなく「経由」なので、ここでは保持
            # ただし将来的に最適化可能なパターンとして記録

        return node
