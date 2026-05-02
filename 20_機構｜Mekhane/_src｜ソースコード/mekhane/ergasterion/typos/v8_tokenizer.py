from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/ergasterion/typos/v8_tokenizer.py
"""Typos v8 Tokenizer — 行ベースのスタック式トークナイザー.

RFC v0.4 §7 EBNF + §7 パース優先度に基づく。
Raw text を V8Document (AST) に変換する。

パース優先度:
  1. コードブロック (```) — 内部はパース対象外
  2. <:name: ブロック開始 — スタックに push
  3. /name:> 名前付き閉じ — 名前照合して pop
  4. :> 無名閉じ — 最内側を pop
  5. <:name: value :> インライン — リーフノード
  6. @directive: v7 互換 — hybrid 時のみ (未実装、将来対応)
  7. テキスト行 — 親ノードのコンテンツ
"""


import re
from dataclasses import dataclass, field

try:
    from mekhane.ergasterion.typos.v8_ast import V8Document, V8Node
except ImportError:
    from .v8_ast import V8Document, V8Node  # type: ignore


class V8ParseError(Exception):
    """v8 パースエラー。行番号付き。"""

    def __init__(self, message: str, line: int = 0):
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)


# 正規表現パターン (コンパイル済み)
_META_PATTERN = re.compile(r"^#(\w+)\s*:\s*(.+)$")  # #key: value
_PROMPT_PATTERN = re.compile(r"^#prompt\s+(.+)$")  # #prompt name
_MIXIN_HEADER = re.compile(r"^#mixin\s+(.+)$")  # #mixin name

# v8.4: 識別子パターン (大文字1字 + ハイフン/ブラケット + 数字始まりアドレス)
# 3形式: S-01a, S[01a], S-[01a] (ブラケットがあればハイフン省略可)
_ID_NAME_RE = re.compile(
    r"^([A-Z])"               # プレフィクス (大文字1字)
    r"(?:"
    r"-?\[([^\]]+)\]"          # ブラケット形式: S[addr] or S-[addr]
    r"|"
    r"-(\d[\w.]*)"             # ハイフン形式: S-01a, S-01a.02
    r")$"
)

# v8.4: name = 従来の名前 | 識別子名
_NAME_PATTERN = r"(?:\w[\w-]*|[A-Z](?:-?\[[^\]]+\]|-\d[\w.]*))"

_V8_INLINE = re.compile(r"^<:(" + _NAME_PATTERN + r"):\s*(.*?)\s*:>$")
_V8_BLOCK_OPEN = re.compile(r"^<:(" + _NAME_PATTERN + r"):$")
_V8_IF_OPEN = re.compile(r"^<:if\s+(.+):$")  # <:if condition:
_V8_ELIF_OPEN = re.compile(r"^<:elif\s+(.+):$")  # <:elif condition:
_V8_ELSE_OPEN = re.compile(r"^<:else:$")  # <:else:
_V8_NAMED_CLOSE = re.compile(r"^/(" + _NAME_PATTERN + r"):>$")
_V8_ANON_CLOSE = re.compile(r"^:>$")  # :>
_CODE_FENCE = re.compile(r"^```")  # コードブロック開始/終了


def _parse_id_name(name: str) -> tuple[str | None, str | None]:
    """識別子名をパースし (prefix, address) を返す。

    識別子でない場合は (None, None)。

    Examples:
        _parse_id_name("S-01a")     → ("S", "01a")
        _parse_id_name("S[01a.02]") → ("S", "01a.02")
        _parse_id_name("S-[01a]")   → ("S", "01a")
        _parse_id_name("role")      → (None, None)
    """
    m = _ID_NAME_RE.match(name)
    if not m:
        return (None, None)
    prefix = m.group(1)
    address = m.group(2) if m.group(2) is not None else m.group(3)
    return (prefix, address)


@dataclass
class _StackFrame:
    """トークナイザーのスタックフレーム。"""

    node: V8Node
    expects_name: str  # 名前付き閉じで期待される名前 ("" = 無名閉じ OK)


class V8Tokenizer:
    """行ベースのスタック式トークナイザー。

    Usage:
        doc = V8Tokenizer(text).tokenize()
    """

    def __init__(self, text: str):
        self.lines = text.split("\n")
        self.pos = 0
        self.doc = V8Document()
        self._stack: list[_StackFrame] = []
        self._in_code_block = False

    def tokenize(self) -> V8Document:
        """テキスト全体をトークナイズし V8Document を返す。"""
        # Phase 1: メタヘッダーをパース
        self._parse_meta()

        # Phase 2: ディレクティブをパース
        while self.pos < len(self.lines):
            self._parse_line()

        # 閉じ忘れチェック
        if self._stack:
            frame = self._stack[-1]
            raise V8ParseError(
                f"Unclosed block <:{frame.node.kind}: (opened at line {frame.node.line})",
                line=len(self.lines),
            )

        return self.doc

    # ── メタヘッダー ──

    def _parse_meta(self):
        """#prompt, #syntax, #depth, #target 等のメタ行をパース。"""
        while self.pos < len(self.lines):
            line = self.lines[self.pos].strip()

            # 空行はスキップ
            if not line:
                self.pos += 1
                continue

            # #prompt name
            m = _PROMPT_PATTERN.match(line)
            if m:
                self.doc.meta["prompt"] = m.group(1).strip()
                self.pos += 1
                continue

            # #mixin name
            m = _MIXIN_HEADER.match(line)
            if m:
                self.doc.meta["mixin"] = m.group(1).strip()
                self.pos += 1
                continue

            # #key: value
            m = _META_PATTERN.match(line)
            if m:
                key = m.group(1)
                # "prompt" は #prompt パターンで処理済みなのでスキップ
                if key != "prompt":
                    self.doc.meta[key] = m.group(2).strip()
                self.pos += 1
                continue

            # メタ行でなければ終了
            break

    # ── メインパースループ ──

    def _parse_line(self):
        """現在行を解析し、適切なノードを生成する。"""
        if self.pos >= len(self.lines):
            return

        line = self.lines[self.pos]
        stripped = line.strip()
        line_num = self.pos + 1  # 1-indexed

        # 空行
        if not stripped:
            self.pos += 1
            return

        # コメント行 (#で始まるがメタではない)
        if stripped.startswith("#") and not stripped.startswith("#prompt") and not stripped.startswith("#syntax"):
            self.pos += 1
            return

        # ── 優先度 1: コードフェンス ──
        if _CODE_FENCE.match(stripped):
            self._in_code_block = not self._in_code_block
            # コードフェンスはテキストとして保持
            self._add_text_line(line)
            self.pos += 1
            return

        # コードブロック内 → すべてテキスト
        if self._in_code_block:
            self._add_text_line(line)
            self.pos += 1
            return

        # ── 優先度 2-4: 閉じタグ ──

        # /name:> 名前付き閉じ
        m = _V8_NAMED_CLOSE.match(stripped)
        if m:
            close_name = m.group(1)
            self._close_named(close_name, line_num)
            self.pos += 1
            return

        # :> 無名閉じ
        if _V8_ANON_CLOSE.match(stripped):
            self._close_anon(line_num)
            self.pos += 1
            return

        # ── 優先度 5: インライン ──
        m = _V8_INLINE.match(stripped)
        if m:
            name = m.group(1)
            prefix, address = _parse_id_name(name)
            node = V8Node(kind=name, value=m.group(2), line=line_num,
                          prefix=prefix, address=address)
            self._add_node(node)
            self.pos += 1
            return

        # ── 優先度 6: <:if condition: ──
        m = _V8_IF_OPEN.match(stripped)
        if m:
            node = V8Node(kind="if", condition=m.group(1).strip(), line=line_num)
            self._push(node, "if")
            self.pos += 1
            return

        # <:elif condition:
        m = _V8_ELIF_OPEN.match(stripped)
        if m:
            node = V8Node(kind="elif", condition=m.group(1).strip(), line=line_num)
            self._push(node, "elif")
            self.pos += 1
            return

        # <:else:
        if _V8_ELSE_OPEN.match(stripped):
            node = V8Node(kind="else", line=line_num)
            self._push(node, "else")
            self.pos += 1
            return

        # ── 優先度 7: ブロック開始 ──
        m = _V8_BLOCK_OPEN.match(stripped)
        if m:
            name = m.group(1)
            prefix, address = _parse_id_name(name)
            node = V8Node(kind=name, line=line_num,
                          prefix=prefix, address=address)
            self._push(node, name)
            self.pos += 1
            return

        # ── 優先度 8: テキスト行 ──
        self._add_text_line(line)
        self.pos += 1

    # ── スタック操作 ──

    def _push(self, node: V8Node, name: str):
        """ノードをスタックに push。"""
        self._stack.append(_StackFrame(node=node, expects_name=name))

    def _pop(self, close_tag: str, line_num: int) -> V8Node:
        """スタックから pop し、閉じたノードを返す。"""
        if not self._stack:
            raise V8ParseError("Unexpected close tag with no open block", line=line_num)
        frame = self._stack.pop()
        frame.node.close_tag = close_tag
        return frame.node

    def _close_named(self, name: str, line_num: int):
        """名前付き閉じタグ /name:> の処理。

        スタック上で一致する名前を探し、そこまでの全ブロックを閉じる。
        RFC: 名前不一致の場合は ParseError。
        ただし if/elif/else は特別扱い: /if:> で else/elif も閉じる。
        """
        # if グループ: /if:> は else, elif も閉じる
        if name == "if":
            self._close_if_group(line_num)
            return

        if not self._stack:
            raise V8ParseError(f"Unexpected /{name}:> with no open block", line=line_num)

        # スタックトップが一致するか確認
        top = self._stack[-1]
        if top.expects_name == name:
            node = self._pop(f"/{name}:>", line_num)
            self._add_node(node)
        else:
            # スタックを遡って探す (ネスト内の暗黙閉じ)
            for i in range(len(self._stack) - 1, -1, -1):
                if self._stack[i].expects_name == name:
                    # i+1 以降を全て閉じる (暗黙閉じ)
                    while len(self._stack) > i + 1:
                        inner = self._pop(":>", line_num)
                        self._stack[-1].node.children.append(inner)
                    # 名前一致のブロックを閉じる
                    node = self._pop(f"/{name}:>", line_num)
                    self._add_node(node)
                    return
            raise V8ParseError(
                f"/{name}:> does not match any open block "
                f"(current: <:{top.expects_name}:)",
                line=line_num,
            )

    def _close_anon(self, line_num: int):
        """無名閉じタグ :> の処理。最内側を閉じる。"""
        node = self._pop(":>", line_num)
        self._add_node(node)

    def _close_if_group(self, line_num: int):
        """<:if ... :> グループ全体を閉じる。

        /if:> が来たら、else → elif → if の順でスタックから pop し、
        if ノードの children に else/elif を格納する。
        """
        if not self._stack:
            raise V8ParseError("Unexpected /if:> with no open block", line=line_num)

        # else/elif を収集
        collected: list[V8Node] = []
        while self._stack and self._stack[-1].expects_name in ("else", "elif"):
            node = self._pop(":>", line_num)
            collected.insert(0, node)  # 順序を維持

        # if ノードを閉じる
        if not self._stack or self._stack[-1].expects_name != "if":
            raise V8ParseError(
                "/if:> found but no matching <:if ...:",
                line=line_num,
            )
        if_node = self._pop("/if:>", line_num)

        # else/elif を if の children に追加
        if_node.children.extend(collected)
        self._add_node(if_node)

    # ── ノード追加 ──

    def _add_node(self, node: V8Node):
        """ノードを適切な親に追加する。"""
        if self._stack:
            # スタックがある → 親ノードの children に追加
            self._stack[-1].node.children.append(node)
        else:
            # トップレベル → ドキュメントの root_nodes に追加
            self.doc.root_nodes.append(node)

    def _add_text_line(self, line: str):
        """テキスト行をスタックトップまたはルートに追加する。"""
        if self._stack:
            self._stack[-1].node.text_lines.append(line)
        # トップレベルのテキスト行は無視 (ディレクティブ外のテキスト)
