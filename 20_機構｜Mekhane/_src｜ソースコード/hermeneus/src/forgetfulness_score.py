# PROOF: [L2/インフラ] <- hermeneus/src/forgetfulness_score.py 忘却スコア計算
"""
Forgetfulness Score — Theorema Egregium Cognitionis の実装

CCL 式の AST を走査し、構造的忘却 (座標修飾子の欠落) を
**構文的操作のみ** で検出する。

aletheia.md §6.1 で定義:
    S(e) = |{c ∈ C | c ∉ mod(e)}| / |C|

Origin: 2026-03-18 Creator × Claude — Theorema Egregium Cognitionis の発見

参照:
    - aletheia.md §6.1 (理論的定義)
    - ccl_ast.py (AST ノード定義)
    - parser.py MODIFIER_COORDINATES (6座標定義)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple

from .ccl_ast import (
    ASTNode,
    Workflow, Sequence, Fusion, Oscillation, ColimitExpansion,
    ConvergenceLoop, Morphism, Adjunction, Pipeline, Parallel,
    ForLoop, IfCondition, WhileLoop, Lambda, TaggedBlock,
    ModifierPeras, Group, PartialDiff, Integral, Summation,
    MacroRef, LetBinding, Program, OpenEnd, Condition,
)


# =============================================================================
# 定数: 6座標 C (axiom_hierarchy.md §L1)
# =============================================================================

# PURPOSE: CCL の 6 修飾座標 — 認知の計量テンソル
COORDINATES: FrozenSet[str] = frozenset({
    "Va",  # Value: 内部↔外部 (Epistemic / Pragmatic)
    "Fu",  # Function: 探索↔活用 (Explore / Exploit)
    "Pr",  # Precision: 確実↔不確実 (Confident / Uncertain)
    "Sc",  # Scale: 微視↔巨視 (Micro / Macro)
    "Vl",  # Valence: 正↔負 (Approach / Avoid)
    "Te",  # Temporality: 過去↔未来 (Past / Future)
})

# PURPOSE: 欠落座標 → U パターン → 候補 Nomoi のマッピング (aletheia.md §6.1.1 準拠)
COORDINATE_TO_U_PATTERN: Dict[str, Tuple[str, str, List[str]]] = {
    # 座標 → (U パターン名, 説明, 候補 Nomoi)
    "Va": ("U_arrow",   "射/関係の忘却",      ["N-01"]),
    "Fu": ("U_depth",   "多重性の忘却",        ["N-06"]),
    "Pr": ("U_precision", "精度の忘却",        ["N-02", "N-03", "N-10"]),
    "Sc": ("U_context",  "文脈の忘却",         ["N-06", "N-07"]),
    "Vl": ("U_adjoint",  "双対の忘却",         ["N-07"]),
    "Te": ("U_self",     "自己参照の忘却",     ["N-02", "/ath"]),
}

# PURPOSE: 動詞 → 暗黙座標のマッピング (WORKFLOW_DEFAULT_MODIFIERS から自動導出)
# v2.0: 手書きの族座標マッピングを廃止し、translator.py の
# WORKFLOW_DEFAULT_MODIFIERS のキー集合から自動導出する。
# これにより2辞書の乖離が構造的に不可能になる。
# 旧: 族座標のみ (1座標/動詞) → 新: 運用最適極値 (1-2座標/動詞, cross-series 含む)
def _derive_implicit_coordinates() -> Dict[str, FrozenSet[str]]:
    """WORKFLOW_DEFAULT_MODIFIERS のキー集合を暗黙座標とする。

    translator.py の実行時デフォルトがそのまま「この動詞が暗黙的に扱う座標」
    となるため、分析層と実行層が同一のソースを共有する。
    """
    from hermeneus.src.workflow_defaults import WORKFLOW_DEFAULT_MODIFIERS
    result: Dict[str, FrozenSet[str]] = {}
    for verb, mods in WORKFLOW_DEFAULT_MODIFIERS.items():
        result[verb] = frozenset(mods.keys())
    # Peras 動詞 (各 Series の極限演算) — translator には含まれない
    for v, coord in [("t","Va"),("m","Fu"),("k","Pr"),("d","Sc"),("o","Vl"),("c","Te")]:
        result[v] = frozenset({coord})
    # ハブ動詞 — 座標なし (メタ)
    result["u"] = frozenset()
    return result

VERB_IMPLICIT_COORDINATES: Dict[str, FrozenSet[str]] = _derive_implicit_coordinates()

# =============================================================================
# データ型
# =============================================================================

# PURPOSE: 個別の座標欠落診断
@dataclass(frozen=True)
class Diagnosis:
    """個別の座標欠落診断"""
    coordinate: str       # 欠落した座標 (e.g., "Pr")
    u_pattern: str        # 対応する U パターン名 (e.g., "U_precision")
    description: str      # 忘却の説明
    candidate_nomoi: Tuple[str, ...]  # 候補 Nomoi (e.g., ("N-02", "N-03", "N-10"))


# PURPOSE: S(e) の計算結果 (スコア + 診断)
@dataclass
class ScoreResult:
    """S(e) の計算結果"""
    score: float                         # S(e) ∈ [0.0, 1.0]
    present_coordinates: FrozenSet[str]  # 明示された座標
    missing_coordinates: FrozenSet[str]  # 欠落した座標
    diagnoses: Tuple[Diagnosis, ...]     # 欠落座標ごとの診断
    total_coordinates: int = 6           # |C|
    expression: str = ""                 # 元の CCL 式 (任意)


# =============================================================================
# AST 走査: 座標修飾子の収集
# =============================================================================

# PURPOSE: AST を再帰走査し、明示された座標修飾子の集合を返す
def extract_coordinates(node: Any) -> Set[str]:
    """AST を再帰走査し、全 Workflow ノードから座標修飾子を収集する。
    
    PartialDiff の coordinate や ModifierPeras の coordinates も
    「明示的に付与された座標」として収集する。
    
    Args:
        node: CCL AST ノード (ccl_ast.ASTNode の Union 型)
    
    Returns:
        明示された座標修飾子の集合 (e.g., {"Va", "Pr"})
    """
    coords: Set[str] = set()
    
    if node is None:
        return coords
    
    # --- Workflow ノード: modifiers から座標を抽出 ---
    if isinstance(node, Workflow):
        for key in node.modifiers:
            if key in COORDINATES:
                coords.add(key)
        return coords
    
    # --- PartialDiff: ∂coord/verb — coordinate を明示座標として扱う ---
    if isinstance(node, PartialDiff):
        if node.coordinate in COORDINATES:
            coords.add(node.coordinate)
        coords |= extract_coordinates(node.body)
        return coords
    
    # --- ModifierPeras: .ax / .Va 等 — coordinates を明示座標として扱う ---
    if isinstance(node, ModifierPeras):
        for c in node.coordinates:
            if c in COORDINATES:
                coords.add(c)
        coords |= extract_coordinates(node.base_wf)
        return coords
    
    # --- 二項ノード: 左右の子ノードを union ---
    if isinstance(node, (Fusion, Oscillation)):
        coords |= extract_coordinates(node.left)
        coords |= extract_coordinates(node.right)
        return coords
    
    if isinstance(node, Morphism):
        coords |= extract_coordinates(node.source)
        coords |= extract_coordinates(node.target)
        return coords
    
    if isinstance(node, Adjunction):
        coords |= extract_coordinates(node.left)
        coords |= extract_coordinates(node.right)
        return coords
    
    # --- リストノード: 全要素を union ---
    if isinstance(node, Sequence):
        for step in node.steps:
            coords |= extract_coordinates(step)
        return coords
    
    if isinstance(node, Pipeline):
        for step in node.steps:
            coords |= extract_coordinates(step)
        return coords
    
    if isinstance(node, Parallel):
        for branch in node.branches:
            coords |= extract_coordinates(branch)
        return coords
    
    # --- 制御構文: body を再帰走査 ---
    if isinstance(node, ConvergenceLoop):
        coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, ForLoop):
        coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, WhileLoop):
        coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, IfCondition):
        coords |= extract_coordinates(node.then_branch)
        if node.else_branch is not None:
            coords |= extract_coordinates(node.else_branch)
        return coords
    
    if isinstance(node, Lambda):
        coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, TaggedBlock):
        coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, Group):
        coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, ColimitExpansion):
        coords |= extract_coordinates(node.body)
        return coords
    
    # --- その他: body を持つノード ---
    if isinstance(node, Integral):
        coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, Summation):
        if node.body is not None:
            coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, LetBinding):
        coords |= extract_coordinates(node.body)
        return coords
    
    if isinstance(node, Program):
        for expr in node.expressions:
            coords |= extract_coordinates(expr)
        return coords
    
    # OpenEnd, MacroRef, Condition — 座標情報なし
    return coords


# =============================================================================
# スコア計算
# =============================================================================

# PURPOSE: 忘却スコア S(e) を計算する (aletheia.md §6.1.1 定義)
def forgetfulness_score(node: Any) -> float:
    """忘却スコア S(e) を計算する。
    
    S(e) = |{c ∈ C | c ∉ mod(e)}| / |C|
    
    性質:
        - S(e) = 0.0 ⟺ 全座標が明示 ⟺ 構造的忘却なし
        - S(e) = 1.0 ⟺ 座標修飾子が皆無 ⟺ 完全忘却
        - 全域計算可能関数: 任意の well-formed CCL 式に対して有限時間で停止
    
    Args:
        node: CCL AST ノード
    
    Returns:
        S(e) ∈ [0.0, 1.0]
    """
    present = extract_coordinates(node)
    missing_count = len(COORDINATES - present)
    return missing_count / len(COORDINATES)


# =============================================================================
# 診断生成
# =============================================================================

# PURPOSE: 欠落座標から U パターンと候補 Nomoi を推定する
def diagnose(node: Any) -> List[Diagnosis]:
    """欠落座標から U パターンと候補 Nomoi を推定する。
    
    aletheia.md §6.1.1 のマッピング表に基づき、
    各欠落座標に対応する忘却パターンと関連する Nomoi を返す。
    
    Args:
        node: CCL AST ノード
    
    Returns:
        座標の順序でソートされた診断リスト
    """
    present = extract_coordinates(node)
    missing = COORDINATES - present
    
    diagnoses = []
    for coord in sorted(missing):
        u_name, desc, nomoi = COORDINATE_TO_U_PATTERN[coord]
        diagnoses.append(Diagnosis(
            coordinate=coord,
            u_pattern=u_name,
            description=desc,
            candidate_nomoi=tuple(nomoi),
        ))
    
    return diagnoses


# =============================================================================
# E2E: 文字列 → スコア
# =============================================================================

# PURPOSE: CCL 文字列から S(e) を一括計算する
def score_ccl(ccl_str: str) -> ScoreResult:
    """CCL 文字列を受け取り、パース → スコア計算 → 診断生成を一括実行する。
    
    Args:
        ccl_str: CCL 式文字列 (e.g., "/noe[Va:E, Pr:C]+")
    
    Returns:
        ScoreResult (スコア、座標集合、診断)
    
    Raises:
        ValueError: パースに失敗した場合
    """
    from .parser import CCLParser
    
    parser = CCLParser()
    ast = parser.parse(ccl_str)
    
    present = frozenset(extract_coordinates(ast))
    missing = frozenset(COORDINATES - present)
    s = len(missing) / len(COORDINATES)
    diag = diagnose(ast)
    
    return ScoreResult(
        score=s,
        present_coordinates=present,
        missing_coordinates=missing,
        diagnoses=tuple(diag),
        total_coordinates=len(COORDINATES),
        expression=ccl_str,
    )


# =============================================================================
# 暗黙座標: 動詞の族帰属からの座標推定
# =============================================================================

# PURPOSE: AST を再帰走査し、Workflow ノードの wf_id から暗黙座標を収集する
def extract_implicit_coordinates(node: Any) -> Set[str]:
    """AST を再帰走査し、全 Workflow ノードの wf_id から暗黙座標を収集する。

    各動詞は Flow × 修飾座標 の直積なので、座標修飾子なしでも
    「どの座標を暗黙的にカバーするか」が VERB_IMPLICIT_COORDINATES で決定される。

    Returns:
        暗黙的にカバーされる座標の集合 (e.g., {"Va", "Fu", "Pr"})
    """
    coords: Set[str] = set()

    if node is None:
        return coords

    # --- Workflow ノード: wf_id から暗黙座標を解決 ---
    if isinstance(node, Workflow):
        implicit = VERB_IMPLICIT_COORDINATES.get(node.id, frozenset())
        coords |= implicit
        return coords

    # --- PartialDiff: body 内の暗黙座標も収集 ---
    if isinstance(node, PartialDiff):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    # --- ModifierPeras: base_wf 内の暗黙座標も収集 ---
    if isinstance(node, ModifierPeras):
        coords |= extract_implicit_coordinates(node.base_wf)
        return coords

    # --- 二項ノード ---
    if isinstance(node, (Fusion, Oscillation)):
        coords |= extract_implicit_coordinates(node.left)
        coords |= extract_implicit_coordinates(node.right)
        return coords

    if isinstance(node, Morphism):
        coords |= extract_implicit_coordinates(node.source)
        coords |= extract_implicit_coordinates(node.target)
        return coords

    if isinstance(node, Adjunction):
        coords |= extract_implicit_coordinates(node.left)
        coords |= extract_implicit_coordinates(node.right)
        return coords

    # --- リストノード ---
    if isinstance(node, Sequence):
        for step in node.steps:
            coords |= extract_implicit_coordinates(step)
        return coords

    if isinstance(node, Pipeline):
        for step in node.steps:
            coords |= extract_implicit_coordinates(step)
        return coords

    if isinstance(node, Parallel):
        for branch in node.branches:
            coords |= extract_implicit_coordinates(branch)
        return coords

    # --- 制御構文 ---
    if isinstance(node, ConvergenceLoop):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, ForLoop):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, WhileLoop):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, IfCondition):
        coords |= extract_implicit_coordinates(node.then_branch)
        if node.else_branch is not None:
            coords |= extract_implicit_coordinates(node.else_branch)
        return coords

    if isinstance(node, Lambda):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, TaggedBlock):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, Group):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, ColimitExpansion):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, Integral):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, Summation):
        if node.body is not None:
            coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, LetBinding):
        coords |= extract_implicit_coordinates(node.body)
        return coords

    if isinstance(node, Program):
        for expr in node.expressions:
            coords |= extract_implicit_coordinates(expr)
        return coords

    return coords


# PURPOSE: 暗黙座標を含めた 2 層スコアリング結果
@dataclass
class ImplicitScoreResult:
    """S_explicit と S_implicit の両方を保持する 2 層スコア結果"""
    explicit: ScoreResult           # 従来の明示座標のみのスコア
    implicit_coordinates: FrozenSet[str]  # 動詞の族帰属から推定される暗黙座標
    all_coordinates: FrozenSet[str]       # 明示 ∪ 暗黙
    s_implicit: float                     # 暗黙座標込みのスコア
    missing_implicit: FrozenSet[str]      # 暗黙込みでも欠落する座標
    verb_coverage: Dict[str, int]         # 各座標を何個の動詞がカバーするか


# PURPOSE: CCL 文字列から 2 層スコアを計算する (明示 + 暗黙)
def score_ccl_implicit(ccl_str: str) -> ImplicitScoreResult:
    """CCL 文字列から明示座標と暗黙座標の両方を考慮したスコアを計算する。

    明示座標 (修飾子で付与): S_explicit — 従来の S(e)
    暗黙座標 (動詞の族帰属): S_implicit — 動詞の存在だけでカバーされる座標を含む

    S_implicit ≤ S_explicit: 暗黙座標は明示座標を包含するので必ず等しいか低くなる
    """
    from .parser import CCLParser

    parser = CCLParser()
    ast = parser.parse(ccl_str)

    # 明示座標 (従来)
    explicit_coords = frozenset(extract_coordinates(ast))
    explicit_missing = frozenset(COORDINATES - explicit_coords)
    s_explicit = len(explicit_missing) / len(COORDINATES)
    diag = diagnose(ast)

    explicit_result = ScoreResult(
        score=s_explicit,
        present_coordinates=explicit_coords,
        missing_coordinates=explicit_missing,
        diagnoses=tuple(diag),
        total_coordinates=len(COORDINATES),
        expression=ccl_str,
    )

    # 暗黙座標 (動詞の族帰属)
    implicit_coords = frozenset(extract_implicit_coordinates(ast))
    all_coords = explicit_coords | implicit_coords
    missing_implicit = frozenset(COORDINATES - all_coords)
    s_implicit = len(missing_implicit) / len(COORDINATES)

    # 動詞カバレッジ: 各座標を何個の動詞がカバーするか
    verb_coverage = _count_verb_coverage(ast)

    return ImplicitScoreResult(
        explicit=explicit_result,
        implicit_coordinates=implicit_coords,
        all_coordinates=all_coords,
        s_implicit=s_implicit,
        missing_implicit=missing_implicit,
        verb_coverage=verb_coverage,
    )


# PURPOSE: 各座標を何個の動詞がカバーするかを数える
def _count_verb_coverage(node: Any) -> Dict[str, int]:
    """AST 内の全 Workflow ノードの暗黙座標を集計する。

    Returns:
        各座標名 → その座標を暗黙的にカバーする動詞の出現数
    """
    counts: Dict[str, int] = {c: 0 for c in COORDINATES}
    _collect_verb_coords(node, counts)
    return counts


def _collect_verb_coords(node: Any, counts: Dict[str, int]) -> None:
    """再帰ヘルパー: Workflow ノードの暗黙座標をカウンタに加算する"""
    if node is None:
        return

    if isinstance(node, Workflow):
        for c in VERB_IMPLICIT_COORDINATES.get(node.id, frozenset()):
            counts[c] = counts.get(c, 0) + 1
        return

    # 子ノード走査 (構造は extract_implicit_coordinates と同じ)
    if isinstance(node, (Fusion, Oscillation)):
        _collect_verb_coords(node.left, counts)
        _collect_verb_coords(node.right, counts)
    elif isinstance(node, Morphism):
        _collect_verb_coords(node.source, counts)
        _collect_verb_coords(node.target, counts)
    elif isinstance(node, Adjunction):
        _collect_verb_coords(node.left, counts)
        _collect_verb_coords(node.right, counts)
    elif isinstance(node, Sequence):
        for step in node.steps:
            _collect_verb_coords(step, counts)
    elif isinstance(node, Pipeline):
        for step in node.steps:
            _collect_verb_coords(step, counts)
    elif isinstance(node, Parallel):
        for branch in node.branches:
            _collect_verb_coords(branch, counts)
    elif isinstance(node, (ConvergenceLoop, ForLoop, WhileLoop, Lambda,
                           TaggedBlock, Group, ColimitExpansion, Integral,
                           LetBinding)):
        _collect_verb_coords(node.body, counts)
    elif isinstance(node, IfCondition):
        _collect_verb_coords(node.then_branch, counts)
        if node.else_branch is not None:
            _collect_verb_coords(node.else_branch, counts)
    elif isinstance(node, Summation):
        if node.body is not None:
            _collect_verb_coords(node.body, counts)
    elif isinstance(node, (PartialDiff, ModifierPeras)):
        body = node.body if isinstance(node, PartialDiff) else node.base_wf
        _collect_verb_coords(body, counts)
    elif isinstance(node, Program):
        for expr in node.expressions:
            _collect_verb_coords(expr, counts)


# =============================================================================
# Lēthē Phase C: 忘却制御スコアリング
# =============================================================================

# PURPOSE: 忘却制御込みの 3 層スコア結果
@dataclass
class OblivionScoreResult:
    """S_explicit + S_implicit + φ-based 忘却解析の 3 層結果

    Layer 0: S_explicit — 座標修飾子の明示的欠落 (既存)
    Layer 1: S_implicit — 動詞の族帰属からの暗黙座標 (既存)
    Layer 2: φ-based — LUT による 1-cell/2-cell 忘却制御 (Phase C 新規)
    """
    implicit_result: ImplicitScoreResult  # Layer 0 + 1
    theta: float                         # 忘却閾値
    retained_verbs: List[str]            # φ ≤ θ の動詞 (保持)
    skipped_verbs: List[str]             # φ > θ の動詞 (忘却)
    phi_scores: Dict[str, float]         # 動詞→φ のマッピング
    retention_ratio: float               # 保持率 = retained / total


# PURPOSE: CCL 文字列から θ 込みの 3 層スコアを計算する
def score_ccl_oblivion(ccl_str: str, theta: float = 0.5) -> OblivionScoreResult:
    """CCL 文字列から忘却制御込みの 3 層スコアを計算する。

    既存の score_ccl_implicit() に加えて、LUT の φ による
    1-cell (>> 合成) のフィルタリング解析を行う。

    Args:
        ccl_str: CCL 式文字列
        theta: 忘却閾値 θ ∈ [0.0, 1.0]

    Returns:
        OblivionScoreResult (3 層スコア)
    """
    from .oblivion_lut import get_phi

    # Layer 0 + 1: 既存スコアリング
    implicit_result = score_ccl_implicit(ccl_str)

    # Layer 2: φ-based フィルタリング
    from .parser import CCLParser
    parser = CCLParser()
    ast = parser.parse(ccl_str)

    # 全動詞の φ を収集
    verb_ids = _collect_all_verb_ids(ast)
    phi_scores = {v: get_phi(v) for v in verb_ids}

    # 保持/忘却の分類
    retained = [v for v in verb_ids if phi_scores.get(v, 0.5) <= theta]
    skipped = [v for v in verb_ids if phi_scores.get(v, 0.5) > theta]

    total = len(verb_ids)
    retention_ratio = len(retained) / total if total > 0 else 1.0

    return OblivionScoreResult(
        implicit_result=implicit_result,
        theta=theta,
        retained_verbs=retained,
        skipped_verbs=skipped,
        phi_scores=phi_scores,
        retention_ratio=retention_ratio,
    )


# PURPOSE: AST を走査して全 Workflow ノードの verb_id をリストで返す
def _collect_all_verb_ids(node: Any) -> List[str]:
    """AST を走査して全 Workflow ノードの verb_id を出現順で返す。"""
    ids: List[str] = []

    if node is None:
        return ids

    if isinstance(node, Workflow):
        ids.append(node.id)
        return ids

    if isinstance(node, (Fusion, Oscillation)):
        ids.extend(_collect_all_verb_ids(node.left))
        ids.extend(_collect_all_verb_ids(node.right))
    elif isinstance(node, Morphism):
        ids.extend(_collect_all_verb_ids(node.source))
        ids.extend(_collect_all_verb_ids(node.target))
    elif isinstance(node, Adjunction):
        ids.extend(_collect_all_verb_ids(node.left))
        ids.extend(_collect_all_verb_ids(node.right))
    elif isinstance(node, Sequence):
        for step in node.steps:
            ids.extend(_collect_all_verb_ids(step))
    elif isinstance(node, Pipeline):
        for step in node.steps:
            ids.extend(_collect_all_verb_ids(step))
    elif isinstance(node, Parallel):
        for branch in node.branches:
            ids.extend(_collect_all_verb_ids(branch))
    elif isinstance(node, (ConvergenceLoop, ForLoop, WhileLoop, Lambda,
                           TaggedBlock, Group, ColimitExpansion, Integral,
                           LetBinding)):
        ids.extend(_collect_all_verb_ids(node.body))
    elif isinstance(node, IfCondition):
        ids.extend(_collect_all_verb_ids(node.then_branch))
        if node.else_branch is not None:
            ids.extend(_collect_all_verb_ids(node.else_branch))
    elif isinstance(node, (PartialDiff, ModifierPeras)):
        body = node.body if isinstance(node, PartialDiff) else node.base_wf
        ids.extend(_collect_all_verb_ids(body))
    elif isinstance(node, Program):
        for expr in node.expressions:
            ids.extend(_collect_all_verb_ids(expr))

    return ids
