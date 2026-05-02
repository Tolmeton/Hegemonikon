from __future__ import annotations
# PROOF: [L2/インフラ] <- mekhane/ergasterion/typos/v8_compiler.py
"""Typos v8 Compiler — AST → Prompt 変換.

V8Document (AST) を Prompt dataclass に変換する。
唯一の Prompt 生成箇所。
"""


import re
from typing import Optional

try:
    # pyre-ignore[21]
    from mekhane.ergasterion.typos.v8_ast import V8Document, V8Node
    # pyre-ignore[21]
    from mekhane.ergasterion.typos.typos import (
        Activation,
        Condition,
        ContextItem,
        Prompt,
        Rubric,
        RubricDimension,
    )
except ImportError:
    from .v8_ast import V8Document, V8Node  # type: ignore
    from .typos import (  # type: ignore
        Activation,
        Condition,
        ContextItem,
        Prompt,
        Rubric,
        RubricDimension,
    )


# ── PHILOSOPHY.md v7.0 CANONICAL ──
# A0 (Rate-Distortion) → 7基底 (1+3+3) → 24記述行為 (Endpoint × 6修飾 × 4極)

# Legacy → V7 互換マッピング
_LEGACY_TO_V7: dict[str, str] = {
    "constraints": "spec",      # → How族 target-precise
    "examples": "case",         # → Where族 source-local
    "tools": "data",            # → Which族 source-object
    "resources": "data",        # → Which族 source-object (merged)
    "rubric": "schema",         # → Which族 source-meta
}

# V7 ディレクティブ → 型分類
# text: 単一テキスト値
# list: 順序付きリスト (- item / テキスト両対応)
# list_strict: - item のみ (ネスト対応)
# context: ContextItem 構造化リスト
# scope: 3区間構造 (発動/非発動/グレーゾーン)
# case: examples 構造化パース
# schema: Rubric 構造化パース
# kv: キー値辞書
_V7_TYPE_MAP: dict[str, str] = {
    # Why族 (Endpoint × Reason)
    "context": "context",       # src-arché
    "intent": "text",           # src-telos
    "rationale": "text",        # tgt-arché
    "goal": "text",             # tgt-telos
    # How族 (Endpoint × Resolution)
    "detail": "text",           # src-precise
    "summary": "text",          # src-compressed
    "spec": "list_strict",      # tgt-precise (← constraints)
    "outline": "text",          # tgt-compressed
    # How-much族 (Endpoint × Salience)
    "focus": "list",            # src-focused
    "scope": "scope",           # src-diffuse
    "highlight": "list",        # tgt-focused
    "breadth": "text",          # tgt-diffuse
    # Where族 (Endpoint × Context)
    "case": "case",             # src-local (← examples)
    "principle": "text",        # src-global
    "step": "list",             # tgt-local
    "policy": "text",           # tgt-global
    # Which族 (Endpoint × Order)
    "data": "kv",               # src-object (← tools, resources)
    "schema": "schema",         # src-meta (← rubric)
    "content": "text",          # tgt-object
    "format": "text",           # tgt-meta
    # When族 (Endpoint × Modality)
    "fact": "text",             # src-actual
    "assume": "text",           # src-possible
    "assert": "text",           # tgt-actual
    "option": "text",           # tgt-possible
}

# ── 深度レベルシステム (PHILOSOPHY.md v7.1+) ──
# #depth: L0-L3 に応じて有効なディレクティブを制限する。
# L0: V7 ディレクティブなし (role, goal のみ — レガシー互換)
# L1: + Why族 (Reason) + How族 (Resolution) = 8種
# L2: + How-much族 (Salience) + Where族 (Context) = 16種
# L3: 全24種 (+ Which族 Order + When族 Modality)
DEPTH_ACTIVE_DIRECTIVES: dict[str, frozenset[str]] = {
    "L0": frozenset(),  # レガシーのみ — V7 ディレクティブは無効
    "L1": frozenset([
        # Why族 (Reason)
        "context", "intent", "rationale", "goal",
        # How族 (Resolution)
        "detail", "summary", "spec", "outline",
    ]),
    "L2": frozenset([
        # Why族 + How族
        "context", "intent", "rationale", "goal",
        "detail", "summary", "spec", "outline",
        # How-much族 (Salience)
        "focus", "scope", "highlight", "breadth",
        # Where族 (Context)
        "case", "principle", "step", "policy",
    ]),
    "L3": frozenset(_V7_TYPE_MAP.keys()),  # 全24種
}


class V8Compiler:
    """V8Document → Prompt 変換コンパイラ。

    Usage:
        prompt = V8Compiler(doc).compile()
    """

    def __init__(self, doc: V8Document, base_prompt: Optional[Prompt] = None):
        self.doc = doc
        self.prompt = base_prompt or Prompt(name=doc.name)
        # メタデータの反映
        self.prompt.syntax_version = doc.syntax_version
        if doc.depth:
            self.prompt.depth = doc.depth
        if "target" in doc.meta:
            self.prompt.target = doc.target
        elif doc.syntax_version == "v8":
            self.prompt.target = "typos"

    def compile(self) -> Prompt:
        """V8Document を Prompt に変換する。"""
        for node in self.doc.root_nodes:
            self._compile_node(node)
        return self.prompt

    def _compile_node(self, node: V8Node):
        """単一ノードをコンパイルし、Prompt フィールドに反映する。"""
        kind = node.kind

        # ── Legacy → V7 互換マッピング ──
        kind = _LEGACY_TO_V7.get(kind, kind)

        # ── Endpoint (d=0 生成子 — 24記述行為の外) ──
        if kind == "role":
            self.prompt.blocks["@role"] = self._get_content(node)
            return

        # ── V7 24記述行為 (型別ディスパッチ) ──
        dtype = _V7_TYPE_MAP.get(kind)
        if dtype is not None:
            # 深度チェック: 深度外のディレクティブはスキップ
            depth = self.prompt.depth or "L3"  # デフォルト全開放
            active = DEPTH_ACTIVE_DIRECTIVES.get(depth)
            if active is not None and kind not in active:
                return  # 深度外 — 静かにスキップ
            key = f"@{kind}"
            if dtype == "text":
                self.prompt.blocks[key] = self._get_content(node)
            elif dtype == "list":
                # 柔軟リスト: - item / テキスト行 両対応
                if key not in self.prompt.blocks:
                    self.prompt.blocks[key] = []
                self.prompt.blocks[key].extend(self._parse_list_or_text(node))
            elif dtype == "list_strict":
                # 厳密リスト: - item のみ (ネスト対応)
                if key not in self.prompt.blocks:
                    self.prompt.blocks[key] = []
                self.prompt.blocks[key].extend(self._parse_list_items(node))
            elif dtype == "context":
                if key not in self.prompt.blocks:
                    self.prompt.blocks[key] = []
                self.prompt.blocks[key].extend(self._compile_context(node))
            elif dtype == "scope":
                self.prompt.blocks[key] = self._compile_scope(node)
            elif dtype == "case":
                if key not in self.prompt.blocks:
                    self.prompt.blocks[key] = []
                self.prompt.blocks[key].extend(self._compile_examples(node))
            elif dtype == "schema":
                self.prompt.blocks[key] = self._compile_rubric(node)
            elif dtype == "kv":
                if key not in self.prompt.blocks:
                    self.prompt.blocks[key] = {}
                self.prompt.blocks[key].update(self._parse_kv_items(node))
            return

        # ── 構造化データ (v8.1) ──
        if kind == "table":
            self.prompt.blocks["@table"] = self._compile_table(node)

        # ── v8.4: flow ディレクティブ (CCL 構造演算子) ──
        elif kind == "flow":
            self.prompt.blocks["@flow"] = self._compile_flow(node)

        # ── v8.4: 識別子ノード ──
        elif node.is_identifier:
            # 識別子ノードは @id:{prefix} にグループ化
            group_key = f"@id:{node.prefix}"
            if group_key not in self.prompt.blocks:
                self.prompt.blocks[group_key] = []
            entry = {
                "address": node.address,
                "content": self._get_content(node),
            }
            self.prompt.blocks[group_key].append(entry)
            # 個別キーとしても保存 (参照用)
            self.prompt.blocks[f"@{kind}"] = self._get_content(node)

        # ── コンパイラ命令 ──
        elif kind == "if":
            self._compile_if(node)
        elif kind == "activation":
            self.prompt.activation = self._compile_activation(node)
        elif kind == "extends":
            self.prompt.extends = self._get_content(node)
        elif kind == "mixin":
            # <:mixin: name :> (参照) vs <:mixin: (定義) — 参照のみ処理
            content = self._get_content(node)
            if content:
                self.prompt.mixins.append(content)

        # ── 汎用ブロック (未知のディレクティブ) ──
        else:
            self.prompt.blocks[f"@{kind}"] = self._get_content(node)

    # ── コンテンツ取得ヘルパー ──

    def _get_content(self, node: V8Node) -> str:
        """ノードからテキストコンテンツを取得する。

        子ノードに table がある場合は、コンパイル済み MD テーブルを
        テキスト位置にインライン展開する (v8.1)。
        """
        if node.value:
            return node.value.strip()

        parts: list[str] = []
        if node.text_lines:
            parts.append("\n".join(node.text_lines).strip())

        # 子ノードの table をインライン展開
        for child in node.children:
            if child.kind == "table":
                compiled = self._compile_table(child)
                if compiled:
                    parts.append(compiled)

        return "\n\n".join(parts) if parts else ""

    def _parse_list_items(self, node: V8Node) -> list[str]:
        """ノードからリスト項目 (- item) をパースする。"""
        items: list[str] = []
        for line in node.text_lines:
            stripped = line.strip()
            if stripped.startswith("- "):
                items.append(stripped[2:])

        # 子ノードの spec/constraints もマージ (ネスト対応)
        for child_kind in ("spec", "constraints"):
            for child in node.find_children(child_kind):
                items.extend(self._parse_list_items(child))

        # インライン値がある場合 (単一項目)
        if not items and node.value:
            items.append(node.value.strip())

        return items

    def _parse_list_or_text(self, node: V8Node) -> list[str]:
        """リスト項目があればリスト、なければ段落テキストをリストとして返す。

        Hóros の step/focus/highlight は箇条書きと自由テキストが混在する。
        """
        items = self._parse_list_items(node)
        if items:
            return items
        # リスト項目がなければテキスト全体を1要素として
        content = self._get_content(node)
        if content:
            return [content]
        return []

    def _compile_scope(self, node: V8Node) -> dict:
        """scope ノードを構造化辞書に変換する。

        Hóros 12法の scope は3区間構造:
          - 発動条件 (triggered)
          - 非発動条件 (not_triggered)
          - グレーゾーン (gray_zone)
        セクション切替はキーワード検出で行う。
        """
        sections: dict[str, list[str]] = {
            "triggered": [],
            "not_triggered": [],
            "gray_zone": [],
        }
        current_section = "triggered"

        for line in node.text_lines:
            stripped = line.strip()
            if not stripped:
                continue

            # セクション切替検出 (日本語・英語両対応)
            lower = stripped.lower().rstrip(":")
            if "非発動" in stripped or lower in ("not_triggered", "non-trigger", "not triggered"):
                current_section = "not_triggered"
                continue
            if "グレーゾーン" in stripped or lower in ("gray_zone", "grey_zone", "gray zone", "grey zone"):
                current_section = "gray_zone"
                continue
            if ("発動" in stripped and "非" not in stripped) or lower == "triggered":
                current_section = "triggered"
                continue

            # リスト項目
            if stripped.startswith("- "):
                sections[current_section].append(stripped[2:])
            else:
                # テーブル行やフリーテキスト
                sections[current_section].append(stripped)

        return sections

    def _parse_kv_items(self, node: V8Node) -> dict[str, str]:
        """ノードからキー: 値 ペアをパースする。"""
        result: dict[str, str] = {}
        for line in node.text_lines:
            stripped = line.strip()
            if stripped.startswith("- ") and ": " in stripped:
                key, val = stripped[2:].split(": ", 1)
                result[key.strip()] = val.strip()
        return result

    # ── Rubric コンパイル ──

    def _compile_rubric(self, node: V8Node) -> Rubric:
        """rubric ノードを Rubric オブジェクトに変換する。"""
        rubric = Rubric()

        # 子ノードに <:dimension: がある場合 (RFC §9 スタイル)
        for dim_node in node.find_children("dimension"):
            dim = self._compile_dimension(dim_node)
            if dim:
                rubric.dimensions.append(dim)

        # テキストから YAML 風にパース (簡易 demo スタイル)
        if not rubric.dimensions and node.text_lines:
            rubric.dimensions = self._parse_rubric_text(node.text_lines)

        return rubric

    def _compile_dimension(self, node: V8Node) -> Optional[RubricDimension]:
        """dimension ノードを RubricDimension に変換する。"""
        name = ""
        description = ""
        scale = ""
        criteria: dict[str, str] = {}

        for line in node.text_lines:
            stripped = line.strip()
            if stripped.startswith("name:"):
                name = stripped[5:].strip()
            elif stripped.startswith("description:"):
                description = stripped[12:].strip()
            elif stripped.startswith("scale:"):
                scale = stripped[6:].strip()

        # criteria 子ノード
        criteria_node = node.find_first("criteria")
        if criteria_node:
            for line in criteria_node.text_lines:
                stripped = line.strip()
                if ":" in stripped:
                    k, v = stripped.split(":", 1)
                    criteria[k.strip()] = v.strip()

        if name:
            return RubricDimension(
                name=name, description=description, scale=scale, criteria=criteria
            )
        return None

    def _parse_rubric_text(self, lines: list[str]) -> list[RubricDimension]:
        """テキスト行から YAML 風の rubric をパースする (簡易スタイル)。"""
        dims: list[RubricDimension] = []
        current_name = ""
        current_desc = ""
        current_scale = ""
        current_criteria: dict[str, str] = {}

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith("- ") and stripped.endswith(":"):
                # 新しい dimension
                if current_name:
                    dims.append(RubricDimension(
                        name=current_name, description=current_desc,
                        scale=current_scale, criteria=current_criteria,
                    ))
                current_name = stripped[2:-1].strip()  # pyre-ignore
                current_desc = ""
                current_scale = ""
                current_criteria = {}
            elif stripped.startswith("description:"):
                current_desc = stripped[12:].strip()  # pyre-ignore
            elif stripped.startswith("scale:"):
                current_scale = stripped[6:].strip()  # pyre-ignore
            elif stripped.startswith("criteria:"):
                continue
            elif ":" in stripped and current_name:
                k, v = stripped.split(":", 1)
                try:
                    int(k.strip())  # スコアキーか確認
                    current_criteria[k.strip()] = v.strip()
                except ValueError:
                    pass

        if current_name:
            dims.append(RubricDimension(
                name=current_name, description=current_desc,
                scale=current_scale, criteria=current_criteria,
            ))

        return dims

    # ── Examples コンパイル ──

    def _compile_examples(self, node: V8Node) -> list[dict]:
        """examples ノードを list[dict] に変換する。"""
        examples: list[dict] = []

        # 子ノードに <:example: がある場合 (RFC §9 スタイル)
        for ex_node in node.find_children("example"):
            example: dict[str, str] = {}
            input_node = ex_node.find_first("input")
            output_node = ex_node.find_first("output")
            if input_node:
                example["input"] = self._get_content(input_node)
            if output_node:
                example["output"] = self._get_content(output_node)
            if example:
                examples.append(example)

        # テキストから簡易パース (demo スタイル)
        if not examples and node.text_lines:
            current: dict[str, str] = {}
            for line in node.text_lines:
                stripped = line.strip()
                if stripped.startswith("- input:"):
                    if current:
                        examples.append(current)
                    current = {"input": stripped[8:].strip()}
                elif stripped.startswith("output:") or stripped.startswith("- output:"):
                    prefix = "- output:" if stripped.startswith("- output:") else "output:"
                    current["output"] = stripped[len(prefix):].strip()
            if current:
                examples.append(current)

        return examples

    # ── Context コンパイル ──

    _CONTEXT_BRACKET = re.compile(
        r'^-\s+\[(.*?)\]\s+([^\(]+)(?:\(priority:\s*(.*?)\))?'
    )
    _CONTEXT_YAML = re.compile(
        r'^-\s+(file|knowledge|url|api):\s+(.+)$'
    )

    def _compile_context(self, node: V8Node) -> list[ContextItem]:
        """context ノードを list[ContextItem] に変換する。

        2形式をサポート:
          形式 1 (ブラケット): - [type] path (priority: P)
          形式 2 (YAML風):     - file: path
                                  priority: HIGH
        """
        items: list[ContextItem] = []
        pending_type = ""
        pending_path = ""

        for line in node.text_lines:
            stripped = line.strip()
            if not stripped:
                continue

            # 形式 1: - [type] path (priority: P)
            m = self._CONTEXT_BRACKET.match(stripped)
            if m:
                self._flush_pending(items, pending_type, pending_path)
                pending_type = pending_path = ""
                items.append(ContextItem(
                    ref_type=m.group(1).strip(),
                    path=m.group(2).strip(),
                    priority=m.group(3).strip() if m.group(3) else "MEDIUM",
                ))
                continue

            # 形式 2: - file: path / - knowledge: ...
            m2 = self._CONTEXT_YAML.match(stripped)
            if m2:
                self._flush_pending(items, pending_type, pending_path)
                pending_type = m2.group(1)
                pending_path = m2.group(2).strip()
                continue

            # 形式 2 の continuation: priority: HIGH
            if stripped.startswith("priority:") and pending_path:
                priority = stripped.split(":", 1)[1].strip()
                items.append(ContextItem(
                    ref_type=pending_type,
                    path=pending_path,
                    priority=priority,
                ))
                pending_type = pending_path = ""
                continue

            # フォールバック
            if stripped.startswith("- "):
                self._flush_pending(items, pending_type, pending_path)
                pending_type = pending_path = ""
                items.append(ContextItem(
                    ref_type="unknown",
                    path=stripped[2:].strip(),
                    priority="MEDIUM",
                ))

        # 残留フラッシュ
        self._flush_pending(items, pending_type, pending_path)
        return items

    @staticmethod
    def _flush_pending(
        items: list[ContextItem], ref_type: str, path: str
    ):
        """pending 状態の YAML 風 context を ContextItem として追加。"""
        if path:
            items.append(ContextItem(
                ref_type=ref_type or "unknown",
                path=path,
                priority="MEDIUM",
            ))

    # ── If/Else コンパイル ──

    _COND_PATTERN = re.compile(
        r'(\w+)\s*(==|!=|>=|<=|>|<)\s*["\']?([^"\']+?)["\']?\s*$'
    )

    def _compile_if(self, node: V8Node):
        """if ノードを Condition に変換する。

        if ノードの children には直接の子ディレクティブと、
        else/elif ノードが含まれる。
        """
        if not node.condition:
            return

        m = self._COND_PATTERN.match(node.condition)
        if not m:
            return

        # if_content: if ブロック直下のディレクティブをコンパイル
        if_prompt = Prompt(name="__if_branch__")
        if_compiler = V8Compiler(self.doc, base_prompt=if_prompt)

        # else_content
        else_prompt = Prompt(name="__else_branch__")
        else_compiler = V8Compiler(self.doc, base_prompt=else_prompt)

        # elif conditions を集約 (if の後に追加するため)
        elif_conditions: list[Condition] = []

        for child in node.children:
            if child.kind == "else":
                # else の子を else_compiler に
                for ec in child.children:
                    else_compiler._compile_node(ec)
            elif child.kind == "elif":
                # elif を追加の Condition として生成
                if child.condition:
                    m_elif = self._COND_PATTERN.match(child.condition)
                    if m_elif:
                        elif_prompt = Prompt(name="__elif_branch__")
                        elif_compiler = V8Compiler(self.doc, base_prompt=elif_prompt)
                        for ec in child.children:
                            elif_compiler._compile_node(ec)
                        elif_conditions.append(Condition(
                            variable=m_elif.group(1),
                            operator=m_elif.group(2),
                            value=m_elif.group(3),
                            if_content=elif_prompt.to_dict(),
                            else_content={},
                        ))
            else:
                # if 直下の子を if_compiler に
                if_compiler._compile_node(child)

        # if ブロック内のテキスト行からもリスト項目を抽出
        if_text_items = []
        for line in node.text_lines:
            stripped = line.strip()
            if stripped.startswith("- "):
                if_text_items.append(stripped[2:])
        if if_text_items:
            if_prompt.blocks.setdefault("@spec", []).extend(if_text_items)

        # if condition を先に追加
        condition = Condition(
            variable=m.group(1),
            operator=m.group(2),
            value=m.group(3),
            if_content=if_prompt.to_dict(),
            else_content=else_prompt.to_dict() if node.find_first("else") else {},
        )
        self.prompt.conditions.append(condition)

        # elif conditions を if の後に追加 (順序保証)
        self.prompt.conditions.extend(elif_conditions)

    # ── Table コンパイル (v8.1) ──

    _TABLE_DELIM = "::"

    def _compile_table(self, node: V8Node) -> str:
        """table ノードを MD テーブル文字列に変換する。

        v8.1 <:table:> ディレクティブ:
          - :: デリミタで列を分割
          - 1行目をヘッダ、2行目以降をデータ行として扱う
          - MD パイプテーブルに変換して返す

        根拠: Zhang et al. (2026) arXiv:2602.08548 — LLM は
        デリミタを数えて暗黙の2D座標系を再構築する。
        パイプ | はこの機構の最も堅牢なトリガー (訓練データ豊富)。
        :: は Týpos ネイティブだが compile 時に | に変換することで
        LLM の座標系構築を最大化する。
        """
        lines: list[str] = [l.strip() for l in node.text_lines if l.strip()]
        if not lines:
            return ""

        # インライン値にヘッダがある場合: <:table: col1 :: col2 :>
        # → tokenizer がインラインとしてパースした場合のフォールバック
        if node.value and self._TABLE_DELIM in node.value:
            header_line = node.value
        else:
            header_line = lines[0]
            # pyre-ignore[16]
            lines = lines[1:]

        # :: で分割してセルを取得
        headers = [h.strip() for h in header_line.split(self._TABLE_DELIM)]
        col_count = len(headers)

        # MD テーブル生成
        md_lines = []
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("|" + "|".join(["---"] * col_count) + "|")

        for line in lines:
            cells: list[str] = [c.strip() for c in line.split(self._TABLE_DELIM)]
            # 列数が足りない場合は空セルで補完
            while len(cells) < col_count:
                cells.append("")
            # pyre-ignore[16]
            md_lines.append("| " + " | ".join(cells[:col_count]) + " |")

        return "\n".join(md_lines)

    # ── Activation コンパイル ──

    def _compile_activation(self, node: V8Node) -> Activation:
        """activation ノードを Activation に変換する。"""
        activation = Activation()
        for line in node.text_lines:
            stripped = line.strip()
            if stripped.startswith("mode:"):
                activation.mode = stripped[5:].strip()
            elif stripped.startswith("pattern:"):
                activation.pattern = stripped[8:].strip()
            elif stripped.startswith("priority:"):
                try:
                    activation.priority = int(stripped[9:].strip())
                except ValueError:
                    pass
            elif stripped.startswith("- "):
                activation.rules.append(stripped[2:])
        # インライン値
        if node.value:
            activation.mode = node.value.strip()
        return activation

    # ── v8.4: Flow コンパイル (CCL 構造演算子) ──

    _FLOW_CHAIN_RE = re.compile(r">>{1,2}")  # >> (順序/パイプ)

    def _compile_flow(self, node: V8Node) -> dict:
        """flow ノードを構造化辞書に変換する。

        CCL 構造演算子を解析:
          >>  : 順序 (chain/pipe)
          *   : 並列 (fork)
          [,] : グルーピング

        Returns:
            {
                "expression": "原文の flow 式",
                "stages": [  # >> で分割された段階
                    {"nodes": ["S-01a", "S-01b"], "parallel": True},
                    {"nodes": ["S-02"], "parallel": False},
                ]
            }
        """
        expr = self._get_content(node).strip()
        if not expr:
            return {"expression": "", "stages": []}

        # >> で段階に分割
        raw_stages = self._FLOW_CHAIN_RE.split(expr)
        stages = []
        for raw in raw_stages:
            raw = raw.strip()
            if not raw:
                continue
            # [A, B] グループまたは A*B 並列
            if raw.startswith("[") and raw.endswith("]"):
                # グループ内をカンマで分割
                inner = raw[1:-1]
                nodes = [n.strip() for n in inner.split(",") if n.strip()]
                stages.append({"nodes": nodes, "parallel": True})
            elif "*" in raw:
                # 並列
                nodes = [n.strip() for n in raw.split("*") if n.strip()]
                stages.append({"nodes": nodes, "parallel": True})
            else:
                stages.append({"nodes": [raw], "parallel": False})

        return {"expression": expr, "stages": stages}

