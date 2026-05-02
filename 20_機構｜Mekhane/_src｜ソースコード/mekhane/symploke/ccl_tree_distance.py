from __future__ import annotations
#!/usr/bin/env python3
# PROOF: [L2/モジュール] <- 20_機構｜Mekhane/symploke → CCL 木構造距離関数
"""CCL 木構造距離 (Tree Edit Distance)。

CCL 文字列を木構造に変換し、Zhang-Shasha アルゴリズムで
Tree Edit Distance (TED) を計算する。

Wave 2 改善: token Levenshtein (ρ=0.614) → TED (目標 ρ=0.75-0.80)。
token Levenshtein は木構造を反映しない線形距離。
TED はサブツリーの挿入・削除・置換を自然に扱う。

使用法:
    from mekhane.symploke.ccl_tree_distance import normalized_ted

    d = normalized_ted("_ >> fn1 >> _", "_ >> fn2 >> _")
    # d ∈ [0.0, 1.0]  (0=同一, 1=完全に異なる)
"""

# PURPOSE: CCL 木構造距離関数 — Wave 2 改善モジュール



# ============================================================
# 木ノードの表現
# ============================================================

# PURPOSE: 順序付き木のノード
class Node:
    """CCL 木のノード。"""

    __slots__ = ("label", "children")

    def __init__(self, label: str, children: list[Node] | None = None):
        self.label = label
        self.children = children if children is not None else []

    def size(self) -> int:
        """サブツリーのノード数。"""
        return 1 + sum(c.size() for c in self.children)

    def __repr__(self) -> str:
        if not self.children:
            return self.label
        kids = ", ".join(repr(c) for c in self.children)
        return f"{self.label}({kids})"


# ============================================================
# CCL → 木構造パーサー
# ============================================================

# PURPOSE: CCL トークン列を木構造に変換する
def ccl_to_tree(ccl_str: str) -> Node:
    """CCL 文字列を木構造に変換する。

    パース規則:
    - `>>` `//` は兄弟ノードの区切り (スキップ)
    - `{` は子ノード開始 (制御フローブロック)
    - `}` は子ノード終了
    - `(` `)` は **スキップ** (式グルーピングは構造的情報量が低い)
    - `X{` (例: `F:[each]{`) は X をラベルとする親ノード + 子開始
    - その他 → 葉ノード

    Returns:
        root Node (label="root")
    """
    tokens = _tokenize_ccl(ccl_str)
    root = Node(label="root")
    stack: list[Node] = [root]

    # `(` `)` はスキップ — 式グルーピングは木にしない
    _SKIP = {"(", ")"}
    _SEP = {">>", "//"}

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        if tok in _SEP or tok in _SKIP:
            i += 1
            continue

        if tok == "{":
            block = Node(label="block")
            stack[-1].children.append(block)
            stack.append(block)
            i += 1
            continue

        if tok == "}":
            if len(stack) > 1:
                stack.pop()
            i += 1
            continue

        # `X{` パターン: ラベル付きブロック開始
        if len(tok) > 1 and tok[-1] == "{":
            label = tok[:-1]
            block = Node(label=label if label else "block")
            stack[-1].children.append(block)
            stack.append(block)
            i += 1
            continue

        # `X(` パターン: ラベル + 丸括弧 → ラベルを葉に、括弧はスキップ
        if len(tok) > 1 and tok[-1] == "(":
            label = tok[:-1]
            if label:
                stack[-1].children.append(Node(label=label))
            i += 1
            continue

        # `X}` パターン: トークン + ブロック終了
        if len(tok) > 1 and tok[-1] == "}":
            label = tok[:-1]
            if label:
                stack[-1].children.append(Node(label=label))
            if len(stack) > 1:
                stack.pop()
            i += 1
            continue

        # `X)` パターン: トークン + 丸括弧閉じ → トークンのみ
        if len(tok) > 1 and tok[-1] == ")":
            label = tok[:-1]
            if label:
                stack[-1].children.append(Node(label=label))
            i += 1
            continue

        # 通常トークン — 次が `{` ならラベル付きブロック
        if i + 1 < len(tokens) and tokens[i + 1] == "{":
            block = Node(label=tok)
            stack[-1].children.append(block)
            stack.append(block)
            i += 2
            continue

        # 純粋な葉
        stack[-1].children.append(Node(label=tok))
        i += 1

    return root


# PURPOSE: CCL 文字列をトークンに分割
def _tokenize_ccl(ccl_str: str) -> list[str]:
    """CCL 文字列をトークンに分割する。

    全括弧 `({[]})` を独立トークンとして分離しつつ、
    `F:[each]{` のような接頭辞付きパターンは「ラベル+開括弧」として保持する。
    """
    raw_tokens = ccl_str.split()
    result = []

    _BRACKETS = set("({})")

    for tok in raw_tokens:
        if not tok:
            continue

        # `>>` `//` はそのまま
        if tok in (">>", "//"):
            result.append(tok)
            continue

        # 単独の括弧
        if len(tok) == 1 and tok in _BRACKETS:
            result.append(tok)
            continue

        # 文字列を走査して括弧を分離
        buf = ""
        for ch in tok:
            if ch in _BRACKETS:
                if ch in "({[":
                    # 開括弧 — prefix があれば `prefix{` として保持
                    if buf:
                        result.append(buf + ch)
                        buf = ""
                    else:
                        result.append(ch)
                else:  # )}]
                    if buf:
                        result.append(buf)
                        buf = ""
                    result.append(ch)
            else:
                buf += ch
        if buf:
            result.append(buf)

    return result


# ============================================================
# Zhang-Shasha Tree Edit Distance
# ============================================================

# PURPOSE: Zhang-Shasha TED の前処理 — ポストオーダー走査
def _postorder(node: Node) -> list[Node]:
    """ポストオーダー (左→右→根) で全ノードを列挙。"""
    result = []
    for child in node.children:
        result.extend(_postorder(child))
    result.append(node)
    return result


# PURPOSE: 各ノードの left-most leaf descendant (LLD) を計算
def _compute_lmld(nodes: list[Node]) -> list[int]:
    """各ノード (ポストオーダー) の left-most leaf descendant index を計算。

    LLD: あるノードのサブツリーにおける、最も左の葉のポストオーダーインデックス。
    Zhang-Shasha で keyroots を決定するために必要。
    """
    node_to_idx = {id(n): i for i, n in enumerate(nodes)}
    lmld = [0] * len(nodes)

    for i, node in enumerate(nodes):
        if not node.children:
            # 葉ノード → 自分自身
            lmld[i] = i
        else:
            # 内部ノード → 最も左の子の LLD
            left_child = node.children[0]
            left_idx = node_to_idx[id(left_child)]
            lmld[i] = lmld[left_idx]

    return lmld


# PURPOSE: keyroots を計算 (Zhang-Shasha アルゴリズム)
def _compute_keyroots(lmld: list[int]) -> list[int]:
    """keyroots を計算する。

    keyroot: 同じ LLD を共有するノードの中で最も大きいインデックス。
    TED 計算のエントリポイント。
    """
    # LLD → 最大インデックスのマッピング
    lmld_to_max = {}
    for i, l in enumerate(lmld):
        lmld_to_max[l] = i  # 最後に上書き = 最大

    # ソートして返す
    return sorted(lmld_to_max.values())


# PURPOSE: Zhang-Shasha Tree Edit Distance
def tree_edit_distance(
    tree1: Node,
    tree2: Node,
    insert_cost: float = 1.0,
    delete_cost: float = 1.0,
    rename_cost_fn=None,
) -> float:
    """Zhang-Shasha アルゴリズムで木の編集距離を計算する。

    時間計算量: O(n₁² × n₂²)
    空間計算量: O(n₁ × n₂)

    medium 関数 (10-30 ノード) なら十分高速。

    Args:
        tree1, tree2: 比較する木
        insert_cost: ノード挿入コスト
        delete_cost: ノード削除コスト
        rename_cost_fn: (label1, label2) → コスト。None なら 0/1
    """
    if rename_cost_fn is None:
        rename_cost_fn = lambda a, b: 0.0 if a == b else 1.0

    # ポストオーダー走査
    nodes1 = _postorder(tree1)
    nodes2 = _postorder(tree2)
    n1 = len(nodes1)
    n2 = len(nodes2)

    if n1 == 0 and n2 == 0:
        return 0.0
    if n1 == 0:
        return n2 * insert_cost
    if n2 == 0:
        return n1 * delete_cost

    # LLD と keyroots
    lmld1 = _compute_lmld(nodes1)
    lmld2 = _compute_lmld(nodes2)
    keyroots1 = _compute_keyroots(lmld1)
    keyroots2 = _compute_keyroots(lmld2)

    # DP テーブル (全体)
    td = [[0.0] * (n2 + 1) for _ in range(n1 + 1)]

    for kr1 in keyroots1:
        for kr2 in keyroots2:
            # 部分問題の DP テーブル
            l1 = lmld1[kr1]
            l2 = lmld2[kr2]

            m = kr1 - l1 + 2  # 行数
            n = kr2 - l2 + 2  # 列数
            fd = [[0.0] * n for _ in range(m)]

            # 初期化
            fd[0][0] = 0.0
            for i in range(1, m):
                fd[i][0] = fd[i - 1][0] + delete_cost
            for j in range(1, n):
                fd[0][j] = fd[0][j - 1] + insert_cost

            for i in range(1, m):
                for j in range(1, n):
                    idx1 = l1 + i - 1  # nodes1 のインデックス
                    idx2 = l2 + j - 1  # nodes2 のインデックス

                    if lmld1[idx1] == l1 and lmld2[idx2] == l2:
                        # 両方のサブツリーのルートが同じ left-most leaf
                        cost = rename_cost_fn(
                            nodes1[idx1].label,
                            nodes2[idx2].label,
                        )
                        fd[i][j] = min(
                            fd[i - 1][j] + delete_cost,
                            fd[i][j - 1] + insert_cost,
                            fd[i - 1][j - 1] + cost,
                        )
                        td[idx1 + 1][idx2 + 1] = fd[i][j]
                    else:
                        # サブツリー参照
                        p = lmld1[idx1] - l1
                        q = lmld2[idx2] - l2
                        fd[i][j] = min(
                            fd[i - 1][j] + delete_cost,
                            fd[i][j - 1] + insert_cost,
                            fd[p][q] + td[idx1 + 1][idx2 + 1],
                        )

    return td[n1][n2]


# ============================================================
# 公開 API
# ============================================================

# PURPOSE: 正規化 TED — P3b で使用する主距離関数
def normalized_ted(ccl_a: str, ccl_b: str) -> float:
    """2つの CCL 文字列の正規化 Tree Edit Distance。

    0.0 = 完全に同一の木構造
    1.0 = 完全に異なる木構造

    Args:
        ccl_a, ccl_b: CCL 文字列

    Returns:
        正規化 TED ∈ [0.0, 1.0]
    """
    tree_a = ccl_to_tree(ccl_a)
    tree_b = ccl_to_tree(ccl_b)

    size_a = tree_a.size()
    size_b = tree_b.size()
    max_size = max(size_a, size_b)

    if max_size == 0:
        return 0.0

    ted = tree_edit_distance(tree_a, tree_b)
    return min(ted / max_size, 1.0)


# PURPOSE: 木構造を可視化 (デバッグ用)
def tree_to_str(node: Node, indent: int = 0) -> str:
    """木構造をインデント付き文字列で表示 (デバッグ用)。"""
    prefix = "  " * indent
    connector = "├── " if indent > 0 else ""
    lines = [f"{prefix}{connector}{node.label}"]
    for child in node.children:
        lines.append(tree_to_str(child, indent + 1))
    return "\n".join(lines)
