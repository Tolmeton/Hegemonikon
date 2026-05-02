from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/ergasterion/typos/v8_ast.py
"""Typos v8 AST — 抽象構文木データ構造.

RFC v0.4 §7 EBNF に基づく中間表現。
Tokenizer が生成し、Compiler が Prompt に変換する。
"""


from dataclasses import dataclass, field
from typing import Optional


@dataclass
class V8Node:
    """v8 AST の単一ノード。

    RFC §7 EBNF の `directive` に対応する。
    ツリー構造を持ち、ネストされたディレクティブを children として保持する。

    v8.4: 識別子ディレクティブ対応。
    prefix (大文字1字) + address (数字+文字の階層) で構造化ノードを表現。

    Examples:
        # インライン: <:role: Senior Developer :>
        V8Node(kind="role", value="Senior Developer", line=3)

        # ブロック: <:constraints:\n  - item1\n  - item2\n:>
        V8Node(kind="constraints", text_lines=["  - item1", "  - item2"], line=5)

        # v8.4 識別子: <:S-01a: 仮説α :>
        V8Node(kind="S-01a", prefix="S", address="01a", value="仮説α", line=7)

        # v8.4 ブラケット: <:S[01a.02]: 統合 :>
        V8Node(kind="S[01a.02]", prefix="S", address="01a.02", value="統合", line=9)
    """

    kind: str  # ディレクティブ名: "role", "constraints", "S-01a", etc.
    value: str = ""  # インライン値 (単行の場合)
    children: list[V8Node] = field(default_factory=list)
    text_lines: list[str] = field(default_factory=list)  # ブロック内テキスト行
    line: int = 0  # ソース行番号 (1-indexed、エラー報告用)
    condition: Optional[str] = None  # if/elif 用条件式
    close_tag: str = ""  # 実際に使われた閉じタグ: ":>" or "/name:>"
    prefix: Optional[str] = None  # v8.4: 識別子プレフィクス (大文字1字: "S", "H" 等)
    address: Optional[str] = None  # v8.4: 識別子アドレス ("01a", "01a.02" 等)

    @property
    def is_inline(self) -> bool:
        """インライン形式 (<:name: value :>) かどうか。"""
        return bool(self.value) and not self.children and not self.text_lines

    @property
    def is_identifier(self) -> bool:
        """v8.4 識別子ディレクティブかどうか。"""
        return self.prefix is not None

    @property
    def has_children(self) -> bool:
        """子ノードを持つかどうか。"""
        return bool(self.children)

    @property
    def text_content(self) -> str:
        """text_lines を結合したテキストコンテンツ。"""
        return "\n".join(self.text_lines)

    def find_children(self, kind: str) -> list[V8Node]:
        """指定された kind の直接の子ノードを返す。"""
        return [c for c in self.children if c.kind == kind]

    def find_first(self, kind: str) -> Optional[V8Node]:
        """指定された kind の最初の子ノードを返す。"""
        for c in self.children:
            if c.kind == kind:
                return c
        return None

    def __repr__(self) -> str:
        parts = [f"V8Node(kind={self.kind!r}"]
        if self.value:
            parts.append(f", value={self.value!r}")
        if self.condition:
            parts.append(f", condition={self.condition!r}")
        if self.children:
            parts.append(f", children=[{len(self.children)} nodes]")
        if self.text_lines:
            parts.append(f", text_lines=[{len(self.text_lines)} lines]")
        parts.append(f", line={self.line})")
        return "".join(parts)


@dataclass
class V8Document:
    """パース済み v8 ドキュメント全体。

    メタデータ (#prompt, #syntax 等) とトップレベルの V8Node 群を保持する。
    """

    meta: dict[str, str] = field(default_factory=dict)
    root_nodes: list[V8Node] = field(default_factory=list)

    @property
    def name(self) -> str:
        """プロンプト名 (#prompt の値)。"""
        return self.meta.get("prompt", "")

    @property
    def syntax_version(self) -> str:
        """構文バージョン (#syntax の値、デフォルト hybrid)。"""
        return self.meta.get("syntax", "hybrid")

    @property
    def depth(self) -> Optional[str]:
        """Depth Level (#depth の値)。"""
        return self.meta.get("depth")

    @property
    def target(self) -> str:
        """コンパイルターゲット (#target の値、デフォルト typos)。"""
        return self.meta.get("target", "typos")

    def find_nodes(self, kind: str) -> list[V8Node]:
        """指定された kind のトップレベルノードを返す。"""
        return [n for n in self.root_nodes if n.kind == kind]

    def find_first_node(self, kind: str) -> Optional[V8Node]:
        """指定された kind の最初のトップレベルノードを返す。"""
        for n in self.root_nodes:
            if n.kind == kind:
                return n
        return None
