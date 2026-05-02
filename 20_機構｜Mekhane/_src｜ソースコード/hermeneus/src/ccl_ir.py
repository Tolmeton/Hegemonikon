from __future__ import annotations
# PROOF: [L2/インフラ] <- hermeneus/src/ CCL 中間表現 (IR)
"""
CCL 中間表現 (IR) — AST と実行計画の間の構造化層

AST (構文) → IR (意味 + 精度情報) → plan_template (実行計画)

設計原理:
    - AST ノードごとに IR ノードを生成 (1:1 対応)
    - precision_ml, coherence, drift は Optional (フォールバック)
    - Phase 1 では precision 信号なしでも動作 (後方互換 100%)
    - BindingTime は Futamura Projection に基づく最適化ヒント

Origin: 2026-03-15 CCL IR 設計 (Activity 2)
"""


import itertools
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

from hermeneus.src.ccl_ast import (
    ASTNode,
    Adjunction,
    ColimitExpansion,
    ConvergenceLoop,
    ForLoop,
    Fusion,
    Group,
    IfCondition,
    Lambda,
    LetBinding,
    MacroRef,
    ModifierPeras,
    Morphism,
    OpenEnd,
    Oscillation,
    Parallel,
    PartialDiff,
    Pipeline,
    Integral,
    Sequence,
    Summation,
    TaggedBlock,
    WhileLoop,
    Workflow,
    OpType,
)


# =============================================================================
# BindingTime — Embedding Futamura Projection
# =============================================================================

# PURPOSE: [L2-auto] IR ノードの束縛時間分類
class BindingTime(Enum):
    """IR ノードの束縛時間。

    Futamura Projection に基づく:
        STATIC  = コンパイル時に確定 (WF パス解決済み, 修飾子固定)
        DYNAMIC = 実行時に決定 (条件分岐, ループ回数, context 依存)
        MIXED   = 静的な部分と動的な部分が混在 (Sequence の一部が条件付き等)
    """
    STATIC = auto()
    DYNAMIC = auto()
    MIXED = auto()


# =============================================================================
# CCLIRNode — 中間表現の単一ノード
# =============================================================================

# PURPOSE: [L2-auto] CCL IR の単一ノード
@dataclass
class CCLIRNode:
    """CCL 中間表現の単一ノード。

    AST ノード 1:1 に対応する IR ノード。
    AST の構文情報 + 精度信号 + 最適化ヒントを保持する。

    Attributes:
        node_id: 一意なノード識別子 (例: "ir_0", "ir_1")
        ast_type: 元の AST ノード型名 (例: "Workflow", "Sequence")
        ast_node: 元の AST ノード参照
        wf_id: ワークフロー ID (Workflow ノードの場合)
        depth_discrete: 離散深度 (0-3, + → 3, 無印 → 2, - → 1)
        precision_ml: 連続精度 [0.0, 1.0] (None = 未計測)
        coherence: 文脈内一貫性 [0.0, 1.0] (None = 未計測)
        drift: 文脈からの逸脱 [0.0, ∞) (None = 未計測)
        binding_time: 束縛時間分類
        children: 子 IR ノードのリスト
        metadata: 任意のメタデータ辞書
    """
    node_id: str
    ast_type: str
    ast_node: ASTNode  # 元の ASTNode 参照

    # ワークフロー情報
    wf_id: Optional[str] = None

    # 深度 — 離散 (既存) と連続 (precision_ml) の二重表現
    depth_discrete: int = 2  # デフォルト L2

    # Precision 信号 (P5 で注入, Phase 1 では全て None)
    precision_ml: Optional[float] = None

    # Linkage 三量 (P6 で注入, Phase 1 では全て None)
    coherence: Optional[float] = None
    drift: Optional[float] = None

    # 最適化ヒント (P7 で活用)
    binding_time: BindingTime = BindingTime.STATIC

    # 構造
    children: List[CCLIRNode] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # PURPOSE: 実効深度を計算 — precision + linkage で連続値、なければ離散値
    @property
    def effective_depth(self) -> float:
        """実効深度 [0.0, 3.0]。

        precision_ml が注入されている場合:
            base = depth_discrete + (1 - 2 × precision_ml)
            precision_ml=1.0 → depth - 1 (exploit: 浅くてよい)
            precision_ml=0.5 → depth + 0 (中立)
            precision_ml=0.0 → depth + 1 (explore: 深く必要)

        P6 linkage 補正 (drift/coherence が注入されている場合):
            drift が高い → context と WF 群が乖離 → 深い探索が必要 (+α)
            coherence が低い → WF 群がバラバラ → 深い探索が必要 (+β)
            α=0.5 (drift ∈ [0,1] → 最大 +0.5)
            β=0.3 (incoherence ∈ [0,1] → 最大 +0.3)

        それ以外:
            depth_discrete をそのまま返す (後方互換)
        """
        if self.precision_ml is not None:
            # P5: precision は深度の「シフト量」として機能
            # FEP: precision = prediction error の gain
            #   高 gain (precision=1) → 信号十分 → exploit → 浅い深度
            #   低 gain (precision=0) → 信号不足 → explore → 深い深度
            raw = self.depth_discrete + (1.0 - 2.0 * self.precision_ml)

            # P6 linkage 補正 (#1 /ele+ → /dio 修正)
            # drift: context-WF 乖離 → 高いほど深く
            if self.drift is not None:
                raw += 0.5 * self.drift
            # coherence: WF 間一貫性 → 低いほど深く (incoherence)
            if self.coherence is not None:
                raw += 0.3 * (1.0 - self.coherence)

            return min(3.0, max(0.0, raw))
        return float(self.depth_discrete)

    # PURPOSE: ノードの要約を文字列で返す
    def summary(self) -> str:
        """デバッグ用の要約文字列。"""
        parts = [f"{self.node_id}:{self.ast_type}"]
        if self.wf_id:
            parts.append(f"wf={self.wf_id}")
        parts.append(f"d={self.depth_discrete}")
        if self.precision_ml is not None:
            parts.append(f"p={self.precision_ml:.3f}")
        if self.coherence is not None:
            parts.append(f"coh={self.coherence:.3f}")
        if self.drift is not None:
            parts.append(f"dft={self.drift:.3f}")
        parts.append(f"bt={self.binding_time.name}")
        return " ".join(parts)


# =============================================================================
# CCLIR — IR 全体を保持するコンテナ
# =============================================================================

# PURPOSE: [L2-auto] CCL IR のルートコンテナ
@dataclass
class CCLIR:
    """CCL 中間表現のルートコンテナ。

    AST 全体を走査して生成された IR ノードツリーを保持する。
    精度信号の集約と最適化パスのエントリポイントを提供する。

    Attributes:
        root: IR ルートノード
        ccl_expr: 元の CCL 式文字列
        all_nodes: 全ノードのフラットリスト (走査用)
        global_precision_ml: CCL 全体の precision_ml (context ベース)
        global_coherence: CCL 全体の coherence
        global_drift: CCL 全体の drift
    """
    root: CCLIRNode
    ccl_expr: str = ""

    # フラットインデックス (走査・検索用)
    all_nodes: List[CCLIRNode] = field(default_factory=list)

    # グローバル精度信号 (P5/P6 で注入)
    global_precision_ml: Optional[float] = None
    global_coherence: Optional[float] = None
    global_drift: Optional[float] = None

    # PURPOSE: WF ノードのみを抽出
    @property
    def workflow_nodes(self) -> List[CCLIRNode]:
        """ワークフロー型のノードのみを返す。"""
        return [n for n in self.all_nodes if n.wf_id is not None]

    # PURPOSE: 深度の最大値を返す
    @property
    def max_depth(self) -> int:
        """全ノードの離散深度の最大値。dispatch.py の depth_level と同等。"""
        if not self.all_nodes:
            return 2
        return max(n.depth_discrete for n in self.all_nodes)

    # PURPOSE: 全ノードにグローバルな precision 信号を伝搬する
    def propagate_precision(
        self,
        precision_ml: Optional[float] = None,
        coherence: Optional[float] = None,
        drift: Optional[float] = None,
    ) -> None:
        """グローバル精度信号を全ノードに伝搬する。

        P5/P6 で外部から計測値を注入するためのエントリポイント。
        Individual ノードに既に値がある場合は上書きしない。
        """
        if precision_ml is not None:
            self.global_precision_ml = precision_ml
        if coherence is not None:
            self.global_coherence = coherence
        if drift is not None:
            self.global_drift = drift

        for node in self.all_nodes:
            if node.precision_ml is None and self.global_precision_ml is not None:
                node.precision_ml = self.global_precision_ml
            if node.coherence is None and self.global_coherence is not None:
                node.coherence = self.global_coherence
            if node.drift is None and self.global_drift is not None:
                node.drift = self.global_drift

    # PURPOSE: IR の木構造をテキストで表示
    def format_tree(self, node: Optional[CCLIRNode] = None, indent: int = 0) -> str:
        """IR の木構造をインデント付きテキストで表示する。"""
        if node is None:
            node = self.root
        lines = ["  " * indent + node.summary()]
        for child in node.children:
            lines.append(self.format_tree(child, indent + 1))
        return "\n".join(lines)


# =============================================================================
# ast_to_ir — AST → IR 変換
# =============================================================================

# 後方互換: テストが _reset_counter() を呼んでいる場合のためのスタブ
def _reset_counter() -> None:
    """後方互換スタブ。ローカルカウンタ移行後は no-op。"""
    pass


# PURPOSE: Workflow ノードから離散深度を算出
def _depth_from_workflow(wf: Workflow) -> int:
    """Workflow の演算子から離散深度を決定する。

    + (DEEPEN) → L3
    - (CONDENSE) → L1
    無印 → L2
    """
    for op in wf.operators:
        if op == OpType.DEEPEN:
            return 3
        if op == OpType.CONDENSE:
            return 1
    return 2


# PURPOSE: AST ノードの束縛時間を判定
def _classify_binding_time(node: ASTNode) -> BindingTime:
    """AST ノードの型から束縛時間を分類する。

    STATIC:  Workflow, MacroRef, OpenEnd, LetBinding
    DYNAMIC: ForLoop, IfCondition, WhileLoop, ConvergenceLoop, Lambda
    MIXED:   Sequence, Fusion, Oscillation, Pipeline, Parallel, TaggedBlock, Group
             (子ノードに動的要素が含まれる可能性があるため)
    """
    # 完全に静的: ワークフロー参照・マクロ・末端
    if isinstance(node, (Workflow, MacroRef, OpenEnd, LetBinding)):
        return BindingTime.STATIC

    # 完全に動的: 条件・ループ
    if isinstance(node, (ForLoop, IfCondition, WhileLoop, ConvergenceLoop, Lambda)):
        return BindingTime.DYNAMIC

    # 混合: 構造ノード (子に依存)
    # Sequence, Fusion, Oscillation 等は子のBT次第で STATIC にもなり得るが、
    # 初期分類では MIXED とし、P7 の最適化パスで精緻化する
    return BindingTime.MIXED


# PURPOSE: [L2-auto] AST → IR 変換のメインエントリポイント
def ast_to_ir(ast_node: ASTNode, ccl_expr: str = "") -> CCLIR:
    """AST を IR に変換する。

    Args:
        ast_node: CCLParser.parse() の出力
        ccl_expr: 元の CCL 式文字列

    Returns:
        CCLIR: IR ルートコンテナ
    """
    # ローカルカウンタ: スレッド安全 (#2 /ele+ 修正)
    counter = itertools.count()
    next_id: Callable[[], str] = lambda: f"ir_{next(counter)}"

    all_nodes: List[CCLIRNode] = []
    root = _convert_node(ast_node, all_nodes, next_id)
    return CCLIR(root=root, ccl_expr=ccl_expr, all_nodes=all_nodes)


# PURPOSE: AST ノードを再帰的に IR ノードに変換
def _convert_node(
    node: ASTNode, all_nodes: List[CCLIRNode], next_id: Callable[[], str]
) -> CCLIRNode:
    """AST ノードを再帰的に IR ノードに変換する。"""
    ast_type = type(node).__name__
    ir_node = CCLIRNode(
        node_id=next_id(),
        ast_type=ast_type,
        ast_node=node,
        binding_time=_classify_binding_time(node),
    )

    # --- Workflow ---
    if isinstance(node, Workflow):
        ir_node.wf_id = node.id
        ir_node.depth_discrete = _depth_from_workflow(node)

    # --- Sequence ---
    elif isinstance(node, Sequence):
        for step in node.steps:
            child = _convert_node(step, all_nodes, next_id)
            ir_node.children.append(child)
        # 深度は子の最大値を継承
        if ir_node.children:
            ir_node.depth_discrete = max(c.depth_discrete for c in ir_node.children)
        # 全子が STATIC なら STATIC に昇格
        if ir_node.children and all(
            c.binding_time == BindingTime.STATIC for c in ir_node.children
        ):
            ir_node.binding_time = BindingTime.STATIC
        # .d/.h/.x 展開元の記法を保持
        if getattr(node, "source_notation", None):
            ir_node.metadata["source_notation"] = node.source_notation

    # --- Fusion ---
    elif isinstance(node, Fusion):
        left = _convert_node(node.left, all_nodes, next_id)
        right = _convert_node(node.right, all_nodes, next_id)
        ir_node.children = [left, right]
        ir_node.depth_discrete = max(left.depth_discrete, right.depth_discrete)
        if left.binding_time == BindingTime.STATIC and right.binding_time == BindingTime.STATIC:
            ir_node.binding_time = BindingTime.STATIC

    # --- Morphism (>*, <*, *>, >%, <<) ---
    elif isinstance(node, Morphism):
        source = _convert_node(node.source, all_nodes, next_id)
        target = _convert_node(node.target, all_nodes, next_id)
        ir_node.children = [source, target]
        ir_node.depth_discrete = max(source.depth_discrete, target.depth_discrete)
        ir_node.metadata["direction"] = node.direction
        # 射は source/target の組み合わせ次第で MIXED
        if source.binding_time == BindingTime.STATIC and target.binding_time == BindingTime.STATIC:
            ir_node.binding_time = BindingTime.STATIC
        else:
            ir_node.binding_time = BindingTime.MIXED

    # --- Adjunction (||, |>, <|) ---
    elif isinstance(node, Adjunction):
        left = _convert_node(node.left, all_nodes, next_id)
        right = _convert_node(node.right, all_nodes, next_id)
        ir_node.children = [left, right]
        ir_node.depth_discrete = max(left.depth_discrete, right.depth_discrete)
        # 随伴宣言は構造的関係の記述 → STATIC
        if left.binding_time == BindingTime.STATIC and right.binding_time == BindingTime.STATIC:
            ir_node.binding_time = BindingTime.STATIC

    # --- Oscillation ---
    elif isinstance(node, Oscillation):
        left = _convert_node(node.left, all_nodes, next_id)
        right = _convert_node(node.right, all_nodes, next_id)
        ir_node.children = [left, right]
        ir_node.depth_discrete = max(left.depth_discrete, right.depth_discrete)
        # 振動は反復を伴うので DYNAMIC
        ir_node.binding_time = BindingTime.DYNAMIC
        # .x 展開元の記法を保持
        if getattr(node, "source_notation", None):
            ir_node.metadata["source_notation"] = node.source_notation

    # --- ConvergenceLoop ---
    elif isinstance(node, ConvergenceLoop):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete
        ir_node.metadata["condition"] = str(node.condition)

    # --- Pipeline ---
    elif isinstance(node, Pipeline):
        for step in node.steps:
            child = _convert_node(step, all_nodes, next_id)
            ir_node.children.append(child)
        if ir_node.children:
            ir_node.depth_discrete = max(c.depth_discrete for c in ir_node.children)
        if ir_node.children and all(
            c.binding_time == BindingTime.STATIC for c in ir_node.children
        ):
            ir_node.binding_time = BindingTime.STATIC

    # --- Parallel ---
    elif isinstance(node, Parallel):
        for branch in node.branches:
            child = _convert_node(branch, all_nodes, next_id)
            ir_node.children.append(child)
        if ir_node.children:
            ir_node.depth_discrete = max(c.depth_discrete for c in ir_node.children)
        # 全分岐が STATIC なら STATIC に昇格 (#3 /ele+ 修正)
        if ir_node.children and all(
            c.binding_time == BindingTime.STATIC for c in ir_node.children
        ):
            ir_node.binding_time = BindingTime.STATIC

    # --- ForLoop ---
    elif isinstance(node, ForLoop):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete
        ir_node.metadata["iterations"] = node.iterations

    # --- IfCondition ---
    elif isinstance(node, IfCondition):
        then_node = _convert_node(node.then_branch, all_nodes, next_id)
        ir_node.children = [then_node]
        ir_node.depth_discrete = then_node.depth_discrete
        if node.else_branch is not None:
            else_node = _convert_node(node.else_branch, all_nodes, next_id)
            ir_node.children.append(else_node)
            ir_node.depth_discrete = max(
                ir_node.depth_discrete, else_node.depth_discrete
            )
        ir_node.metadata["condition"] = str(node.condition)

    # --- WhileLoop ---
    elif isinstance(node, WhileLoop):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete

    # --- Lambda ---
    elif isinstance(node, Lambda):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete
        ir_node.metadata["params"] = node.params

    # --- TaggedBlock ---
    elif isinstance(node, TaggedBlock):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete
        ir_node.metadata["tag"] = node.tag
        if body.binding_time == BindingTime.STATIC:
            ir_node.binding_time = BindingTime.STATIC

    # --- Group ---
    elif isinstance(node, Group):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete
        # Group の operators から深度を上書き
        for op in node.operators:
            if op == OpType.DEEPEN:
                ir_node.depth_discrete = 3
                break
            if op == OpType.CONDENSE:
                ir_node.depth_discrete = 1
                break
        if body.binding_time == BindingTime.STATIC:
            ir_node.binding_time = BindingTime.STATIC

    # --- ColimitExpansion ---
    elif isinstance(node, ColimitExpansion):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete
        # Colimit は展開 → 実行時
        ir_node.binding_time = BindingTime.DYNAMIC

    # --- MacroRef ---
    elif isinstance(node, MacroRef):
        ir_node.metadata["macro_name"] = node.name
        ir_node.metadata["macro_args"] = node.args

    # --- ModifierPeras ---
    elif isinstance(node, ModifierPeras):
        base = _convert_node(node.base_wf, all_nodes, next_id)
        ir_node.children = [base]
        ir_node.depth_discrete = base.depth_discrete
        ir_node.metadata["coordinates"] = node.coordinates
        # Peras は全展開 → DYNAMIC
        ir_node.binding_time = BindingTime.DYNAMIC

    # --- PartialDiff ---
    elif isinstance(node, PartialDiff):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete
        ir_node.metadata["coordinate"] = node.coordinate

    # --- Integral ---
    elif isinstance(node, Integral):
        body = _convert_node(node.body, all_nodes, next_id)
        ir_node.children = [body]
        ir_node.depth_discrete = body.depth_discrete
        # 積分は過去検索 → DYNAMIC
        ir_node.binding_time = BindingTime.DYNAMIC

    # --- Summation ---
    elif isinstance(node, Summation):
        if node.body is not None:
            body = _convert_node(node.body, all_nodes, next_id)
            ir_node.children = [body]
            ir_node.depth_discrete = body.depth_discrete
        ir_node.metadata["items"] = node.items
        ir_node.binding_time = BindingTime.DYNAMIC

    # --- OpenEnd / LetBinding / 未知 ---
    # (子なし、デフォルト値でOK)

    # 全ノードリストに登録
    all_nodes.append(ir_node)
    return ir_node


# =============================================================================
# diff → precision_ml マッピング (P5: precision_router v3 連携)
# =============================================================================

# PURPOSE: precision_router の diff 値を IR の precision_ml に変換
def diff_to_precision_ml(diff: float) -> float:
    """precision_router の diff 値を IR の precision_ml [0, 1] にマッピング。

    precision_router v3 は cos sim 差を返す:
      diff = cos(input, simple_anchor) - cos(input, complex_anchor)
      正 → テキスト単純 → exploit
      負 → テキスト複雑 → explore

    IR の precision_ml は [0, 1]:
      1.0 → exploit (高 precision, 浅い深度で十分)
      0.0 → explore (低 precision, 深い深度が必要)
      0.5 → 中立

    線形変換: precision_ml = (diff + 1) / 2
      diff = +1.0 → precision_ml = 1.0
      diff =  0.0 → precision_ml = 0.5
      diff = -1.0 → precision_ml = 0.0

    FEP 根拠: precision = prediction error のゲイン。
    diff が正 = 入力が既知パターンに近い = 高ゲイン = exploit。
    """
    return max(0.0, min(1.0, (diff + 1.0) / 2.0))
