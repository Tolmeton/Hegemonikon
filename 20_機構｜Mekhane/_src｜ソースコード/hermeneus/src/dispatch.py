# PROOF: [L2/インフラ] <- hermeneus/src/dispatch.py CCL ディスパッチャ
"""
CCL Dispatch — CCL 式の検知・パース・構造表示を環境強制するエントリポイント

新セッションの AI が CCL 式を受け取ったとき:
  python hermeneus/src/dispatch.py '{CCL式}'

Step 0: Hermēneus パース (環境強制)
Step 1: AST 構造表示
Step 2: 実行計画の提案テンプレート出力

Usage:
    python hermeneus/src/dispatch.py '/dia+~*/noe'
    python hermeneus/src/dispatch.py '{(/dia+~*/noe)~*/pan+}~*{(/dia+~*/noe)~*\\pan+}'
"""

import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# パッケージパス追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict


# PURPOSE: G2 — dispatch() 戻り値の型定義
class RouteContext(TypedDict, total=False):
    """Aristos L3 ルーティング文脈。"""
    source: str
    target: str
    route: List[str]
    depth_level: int
    wf_count: int


class DispatchResult(TypedDict, total=False):
    """dispatch() 関数の戻り値型。

    total=False にすることで、全キーがオプショナルになる。
    これにより段階的にキーを設定する dispatch() のパターンと整合する。
    """
    success: bool
    ccl: str
    ast: Any                            # CCLParser の AST ノード
    tree: str                           # AST 木構造のテキスト表示
    workflows: List[str]                # 抽出された WF ID (e.g. ["/noe", "/dia"])
    wf_paths: Dict[str, str]            # WF ID → 絶対パス
    wf_submodules: Dict[str, List[str]] # WF ID → サブモジュールパスのリスト
    wf_summaries: Dict[str, Dict[str, Any]]  # WF ID → 要約情報
    plan_template: str                  # 実行計画テンプレート
    macro_plan: Optional[Dict[str, Any]]     # マクロ実行計画
    error: Optional[str]                     # エラーメッセージ
    exhaustive_warnings: List[str]      # 網羅性チェック警告
    parallel_warnings: List[str]        # 並列安全性チェック警告
    route_context: RouteContext         # Aristos ルーティング文脈
    # Activity 2: CCL 中間表現 (IR)
    ir: Any                             # CCLIR オブジェクト (Optional)
    # C3 Forgetful Functor 統合
    forget_level: int                   # 0-4: Nothing/Context/Design/Impl/All
    forget_mapping: Dict[str, int]      # WF ID → forget_level
    forget_names: Dict[int, str]        # level → 名称 (表示用)
    forget_deficits: List[Dict[str, Any]]  # F7: Basanos 忘却回復 deficits
    contract: Dict[str, Any]            # Compiled CCL contract


# PURPOSE: AST をインデント付きで木構造表示
def format_ast_tree(node, indent=0) -> str:
    """AST をインデント付きで木構造表示"""
    from hermeneus.src.ccl_ast import (
        Workflow, Oscillation, Fusion, Sequence, ConvergenceLoop,
        ColimitExpansion, Pipeline, Parallel, Adjunction, Morphism, OpenEnd, Group,
        PartialDiff, Integral, Summation, PreVerb
    )
    
    prefix = "  " * indent
    lines = []
    
    if isinstance(node, Oscillation):
        mode = "~*" if node.convergent else ("~!" if node.divergent else "~")
        lines.append(f"{prefix}Oscillation ({mode})")
        lines.append(f"{prefix}  left:")
        lines.append(format_ast_tree(node.left, indent + 2))
        lines.append(f"{prefix}  right:")
        lines.append(format_ast_tree(node.right, indent + 2))
    elif isinstance(node, ColimitExpansion):
        lines.append(f"{prefix}ColimitExpansion (\\)")
        lines.append(f"{prefix}  body:")
        lines.append(format_ast_tree(node.body, indent + 2))
    elif isinstance(node, Fusion):
        lines.append(f"{prefix}Fusion (*)")
        lines.append(f"{prefix}  left:")
        lines.append(format_ast_tree(node.left, indent + 2))
        lines.append(f"{prefix}  right:")
        lines.append(format_ast_tree(node.right, indent + 2))
    elif isinstance(node, Sequence):
        lines.append(f"{prefix}Sequence (_ = 順次実行)")
        for i, step in enumerate(node.steps):
            lines.append(f"{prefix}  step {i+1}:")
            lines.append(format_ast_tree(step, indent + 2))
    elif isinstance(node, Pipeline):
        lines.append(f"{prefix}Pipeline (&> = パイプ接続)")
        for i, step in enumerate(node.steps):
            lines.append(f"{prefix}  step {i+1}:")
            lines.append(format_ast_tree(step, indent + 2))
    elif isinstance(node, Parallel):
        lines.append(f"{prefix}Parallel (&& = 並列実行)")
        for i, branch in enumerate(node.branches):
            lines.append(f"{prefix}  branch {i+1}:")
            lines.append(format_ast_tree(branch, indent + 2))
    elif isinstance(node, Adjunction):
        lines.append(f"{prefix}Adjunction (|| = 随伴宣言)")
        lines.append(f"{prefix}  left:")
        lines.append(format_ast_tree(node.left, indent + 2))
        lines.append(f"{prefix}  right:")
        lines.append(format_ast_tree(node.right, indent + 2))
    elif isinstance(node, ConvergenceLoop):
        lines.append(f"{prefix}ConvergenceLoop (~>)")
        lines.append(f"{prefix}  body:")
        lines.append(format_ast_tree(node.body, indent + 2))
        lines.append(f"{prefix}  cond: {node.condition.var} {node.condition.op} {node.condition.value}")
    elif isinstance(node, Morphism):
        direction_map = {
            'forward': '>>', 'reverse': '<<', 'lax': '>*',
            'oplax': '<*', 'directed_fusion': '*>', 'pushforward': '>%',
        }
        op_sym = direction_map.get(node.direction, '??')
        lines.append(f"{prefix}Morphism ({op_sym} = {node.direction})")
        lines.append(f"{prefix}  source:")
        lines.append(format_ast_tree(node.source, indent + 2))
        lines.append(f"{prefix}  target:")
        lines.append(format_ast_tree(node.target, indent + 2))
    elif isinstance(node, PreVerb):
        lines.append(f"{prefix}PreVerb: [{node.id}] ({node.full_name} — 中動態宣言)")
    elif isinstance(node, Workflow):
        ops = ""
        ops_desc = ""
        if node.operators:
            from hermeneus.src.ccl_ast import OpType
            ops_map = {
                OpType.DEEPEN: "+", OpType.CONDENSE: "-",
                OpType.ASCEND: "^", OpType.EXPAND: "!",
                OpType.QUERY: "?", OpType.INVERT: "\\",
                OpType.DIFF: "'",
            }
            # 演算子の日本語意味マップ (視覚的混同防止)
            desc_map = {
                "+": "深化", "-": "軽量", "^": "上昇",
                "!": "全展開", "?": "照会", "\\": "反転", "'": "差分",
            }
            ops = "".join(ops_map.get(op, "") for op in node.operators)
            descs = [desc_map.get(ops_map.get(op, ""), "") for op in node.operators]
            descs = [d for d in descs if d]
            if descs:
                ops_desc = " (" + ", ".join(descs) + ")"
        lines.append(f"{prefix}Workflow: /{node.id}{ops}{ops_desc}")
    elif isinstance(node, Group):
        ops = ",".join(op.name for op in node.operators)
        lines.append(f"{prefix}Group (operators=[{ops}])")
        lines.append(f"{prefix}  body:")
        lines.append(format_ast_tree(node.body, indent + 2))
    elif isinstance(node, PartialDiff):
        lines.append(f"{prefix}PartialDiff (∂{node.coordinate})")
        lines.append(f"{prefix}  body:")
        lines.append(format_ast_tree(node.body, indent + 2))
    elif isinstance(node, Integral):
        lines.append(f"{prefix}Integral (∫)")
        lines.append(f"{prefix}  body:")
        lines.append(format_ast_tree(node.body, indent + 2))
    elif isinstance(node, Summation):
        lines.append(f"{prefix}Σ[{node.items}]")
        if node.body:
            lines.append(f"{prefix}  body:")
            lines.append(format_ast_tree(node.body, indent + 2))
    elif isinstance(node, OpenEnd):
        lines.append(f"{prefix}OpenEnd ([開かれた末尾])")
    else:
        lines.append(f"{prefix}{type(node).__name__}: {node}")
    
    return "\n".join(lines)


# PURPOSE: AST から全ワークフロー ID を再帰的に抽出
def extract_workflows(node) -> list:
    """AST から全ワークフロー ID を再帰的に抽出"""
    from hermeneus.src.ccl_ast import (
        Workflow, Oscillation, Fusion, Sequence, ConvergenceLoop,
        ColimitExpansion, Pipeline, Parallel, Adjunction, Morphism, Group,
        PartialDiff, Integral, Summation, PreVerb
    )
    wfs = []
    if isinstance(node, Workflow):
        wfs.append(f"/{node.id}")
    elif isinstance(node, Oscillation):
        wfs.extend(extract_workflows(node.left))
        wfs.extend(extract_workflows(node.right))
    elif isinstance(node, ColimitExpansion):
        wfs.extend(extract_workflows(node.body))
    elif isinstance(node, Fusion):
        wfs.extend(extract_workflows(node.left))
        wfs.extend(extract_workflows(node.right))
    elif isinstance(node, Sequence):
        for step in node.steps:
            wfs.extend(extract_workflows(step))
    elif isinstance(node, Pipeline):
        for step in node.steps:
            wfs.extend(extract_workflows(step))
    elif isinstance(node, Parallel):
        for branch in node.branches:
            wfs.extend(extract_workflows(branch))
    elif isinstance(node, Adjunction):
        wfs.extend(extract_workflows(node.left))
        wfs.extend(extract_workflows(node.right))
    elif isinstance(node, ConvergenceLoop):
        wfs.extend(extract_workflows(node.body))
    elif isinstance(node, Morphism):
        wfs.extend(extract_workflows(node.source))
        wfs.extend(extract_workflows(node.target))
    elif isinstance(node, Group):
        wfs.extend(extract_workflows(node.body))
    elif isinstance(node, PartialDiff):
        wfs.extend(extract_workflows(node.body))
    elif isinstance(node, Integral):
        wfs.extend(extract_workflows(node.body))
    elif isinstance(node, Summation):
        if node.body:
            wfs.extend(extract_workflows(node.body))
    return wfs


# PURPOSE: AST から全 PreVerb ID を再帰的に抽出 (H-series 環境強制用)
def extract_preverbs(node) -> list:
    """AST から全 PreVerb ノードの ID を再帰的に抽出。

    extract_workflows と対称的な構造。PreVerb ノードの id を収集する。
    """
    from hermeneus.src.ccl_ast import (
        Workflow, Oscillation, Fusion, Sequence, ConvergenceLoop,
        ColimitExpansion, Pipeline, Parallel, Adjunction, Morphism, Group,
        PartialDiff, Integral, Summation, PreVerb
    )
    pvs = []
    if isinstance(node, PreVerb):
        pvs.append(node.id)
    elif isinstance(node, Oscillation):
        pvs.extend(extract_preverbs(node.left))
        pvs.extend(extract_preverbs(node.right))
    elif isinstance(node, ColimitExpansion):
        pvs.extend(extract_preverbs(node.body))
    elif isinstance(node, Fusion):
        pvs.extend(extract_preverbs(node.left))
        pvs.extend(extract_preverbs(node.right))
    elif isinstance(node, Sequence):
        for step in node.steps:
            pvs.extend(extract_preverbs(step))
    elif isinstance(node, Pipeline):
        for step in node.steps:
            pvs.extend(extract_preverbs(step))
    elif isinstance(node, Parallel):
        for branch in node.branches:
            pvs.extend(extract_preverbs(branch))
    elif isinstance(node, Adjunction):
        pvs.extend(extract_preverbs(node.left))
        pvs.extend(extract_preverbs(node.right))
    elif isinstance(node, ConvergenceLoop):
        pvs.extend(extract_preverbs(node.body))
    elif isinstance(node, Morphism):
        pvs.extend(extract_preverbs(node.source))
        pvs.extend(extract_preverbs(node.target))
    elif isinstance(node, Group):
        pvs.extend(extract_preverbs(node.body))
    elif isinstance(node, PartialDiff):
        pvs.extend(extract_preverbs(node.body))
    elif isinstance(node, Integral):
        pvs.extend(extract_preverbs(node.body))
    elif isinstance(node, Summation):
        if node.body:
            pvs.extend(extract_preverbs(node.body))
    return pvs


# PURPOSE: PreVerb の3用法 + BDQ チェックリストを生成 (H-series 環境強制)
def _build_preverb_section(preverb_ids: list) -> str:
    """PreVerb ID リストから環境強制テキストを生成。

    各前動詞について:
    - 正式名・座標を表示
    - 3用法 (Detection / Guidance / Analysis) を明示
    - BDQ チェックリスト (Detection / Labeling / Transition) を出力
    """
    from hermeneus.src.parser import CCLParser

    # 前動詞 → 修飾座標のマッピング
    PREVERB_COORDS = {
        "tr": "Value (E)・向変",
        "sy": "Value (P)・体感",
        "pa": "Function (Explore)・遊戯",
        "he": "Function (Exploit)・習態",
        "ek": "Precision (C)・驚愕",
        "th": "Precision (U)・戸惑い",
        "eu": "Scale (Mi)・微調和",
        "sh": "Scale (Ma)・一望",
        "ho": "Valence (+)・衝動",
        "ph": "Valence (-)・恐怖",
        "an": "Temporality (Past)・想起再現",
        "pl": "Temporality (Future)・予期反射",
    }

    # 前動詞 → 3用法の記述
    PREVERB_USAGES = {
        "tr": ("向きの変化を検知", "視点転換を誘導", "転換の妥当性を分析"),
        "sy": ("身体的感覚を検知", "体感を活用", "体感の認知的意味を分析"),
        "pa": ("遊びの姿勢を検知", "探索的遊戯を誘導", "遊戯の生産性を分析"),
        "he": ("習慣パターンを検知", "熟達した手法を活用", "習慣の適切さを分析"),
        "ek": ("驚きの反応を検知", "驚愕をエネルギーに変換", "驚きの情報価値を分析"),
        "th": ("戸惑いの状態を検知", "曖昧さの中で留まる", "戸惑いの原因を分析"),
        "eu": ("微細な調和を検知", "精密な調整を誘導", "微調和のパターンを分析"),
        "sh": ("全体俯瞰の状態を検知", "鳥瞰的視点を活用", "一望の盲点を分析"),
        "ho": ("衝動的反応を検知", "衝動をエネルギーに変換", "衝動の方向性を分析"),
        "ph": ("恐怖の反応を検知", "恐怖を注意信号に変換", "恐怖の正当性を分析"),
        "an": ("過去パターンの反復を検知", "記憶を意図的に活用", "記憶の適用妥当性を分析"),
        "pl": ("未来予測の反応を検知", "予期を計画に変換", "予期の根拠を分析"),
    }

    lines = ["【前動詞 (H-series) 環境設定】"]
    seen = set()
    for pv_id in preverb_ids:
        if pv_id in seen:
            continue
        seen.add(pv_id)

        full_name = CCLParser.PREVERB_NAMES.get(pv_id, pv_id)
        coord = PREVERB_COORDS.get(pv_id, "不明")
        usages = PREVERB_USAGES.get(pv_id, ("(未定義)", "(未定義)", "(未定義)"))

        lines.append(f"  [{pv_id}] {full_name} — {coord}")
        lines.append(f"    3用法:")
        lines.append(f"      S極 (検知): {usages[0]}")
        lines.append(f"      A極 (誘導): {usages[1]}")
        lines.append(f"      I極 (分析): {usages[2]}")
        lines.append(f"    BDQ チェック:")
        lines.append(f"      □ Detection: [{pv_id}] の発火を検知したか")
        lines.append(f"      □ Labeling: ラベルが状態に合致しているか")
        lines.append(f"      □ Transition: 後続の WF に適切に接続したか")
        lines.append(f"    → 上記3項目を応答に含めよ")

    return "\n".join(lines)


# PURPOSE: WF → Series マッピング (6族 × 6 = 36動詞)
# Telos (目的) = Flow × Value
# Methodos (方法) = Flow × Function
# Krisis (判断) = Flow × Precision
# Diástasis (拡張) = Flow × Scale
# Orexis (欲求) = Flow × Valence
# Chronos (時間) = Flow × Temporality
WF_TO_SERIES = {
    # Tel (目的)
    "noe": "Tel", "bou": "Tel", "zet": "Tel", "ene": "Tel", "the": "Tel", "ant": "Tel",
    # Met (方法)
    "ske": "Met", "sag": "Met", "pei": "Met", "tek": "Met", "ere": "Met", "agn": "Met",
    # Kri (判断)
    "kat": "Kri", "epo": "Kri", "pai": "Kri", "dok": "Kri", "sap": "Kri", "ski": "Kri",
    # Dia (拡張)
    "lys": "Dia", "ops": "Dia", "akr": "Dia", "arc": "Dia", "prs": "Dia", "per": "Dia",
    # Ore (欲求)
    "beb": "Ore", "ele": "Ore", "kop": "Ore", "dio": "Ore", "apo": "Ore", "exe": "Ore",
    # Chr (時間)
    "hyp": "Chr", "prm": "Chr", "ath": "Chr", "par": "Chr", "his": "Chr", "prg": "Chr",
}

# PURPOSE: K₆ エッジの張力タイプと hint (ax_pipeline.py X_SERIES_EDGES の軽量版)
_X_EDGES = {
    ("Tel", "Met"): ("contradiction", "理想と現実的手法の衝突"),
    ("Tel", "Kri"): ("scale_mismatch", "目的の壮大さと確信度の限界"),
    ("Tel", "Dia"): ("scale_mismatch", "Why の抽象度と Where の具体度"),
    ("Tel", "Ore"): ("value_conflict", "目的の方向性と価値傾向の整合"),
    ("Tel", "Chr"): ("temporal_gap", "理想の時間軸と現実の時制"),
    ("Met", "Kri"): ("complement", "手法の選択と確信度の裏付け"),
    ("Met", "Dia"): ("complement", "方法論の粒度とスケールの対応"),
    ("Met", "Ore"): ("value_conflict", "効率と望ましさの衝突"),
    ("Met", "Chr"): ("temporal_gap", "手順の順序と時間的制約"),
    ("Kri", "Dia"): ("complement", "確信度の深さとスケールの広さ"),
    ("Kri", "Ore"): ("contradiction", "冷静な確信と情動的傾向の対立"),
    ("Kri", "Chr"): ("temporal_gap", "現時点の確信度と時間経過での変化"),
    ("Dia", "Ore"): ("complement", "空間的配置と価値的方向性"),
    ("Dia", "Chr"): ("complement", "空間の構造と時間の流れ"),
    ("Ore", "Chr"): ("value_conflict", "今の欲求と長期的展望の衝突"),
}


# PURPOSE: CCL 内の WF 間の暗黙的 X-series 関係を自動検出 (P4 環境強制)
def _build_xseries_section(workflows: list) -> str:
    """複数 WF が異なる Series に属する場合、K₆ エッジの張力関係を可視化。

    CCL に /noe_/ele が含まれる場合、noe=Tel, ele=Ore → Tel-Ore エッジ
    の張力タイプと hint を表示する。実行者が Series 間の力学を意識して
    WF を実行できるようにする環境強制。
    """
    # WF 名を正規化して Series を特定
    series_map = {}  # series_code -> [wf_names]
    for wf in workflows:
        clean = wf.lstrip("/").rstrip("+-")
        s = WF_TO_SERIES.get(clean)
        if s:
            series_map.setdefault(s, []).append(wf)

    # 異なる Series が 2 つ以上なければ X-series は不要
    if len(series_map) < 2:
        return ""

    # 関与する Series 間のエッジを抽出
    series_codes = sorted(series_map.keys())
    edges = []
    for i, a in enumerate(series_codes):
        for b in series_codes[i + 1:]:
            key = (a, b) if (a, b) in _X_EDGES else (b, a)
            if key in _X_EDGES:
                ttype, hint = _X_EDGES[key]
                a_wfs = ", ".join(series_map.get(key[0], []))
                b_wfs = ", ".join(series_map.get(key[1], []))
                edges.append(f"  ⚡ {key[0]}({a_wfs}) — {key[1]}({b_wfs}): {ttype} | {hint}")

    if not edges:
        return ""

    lines = [
        "🔗 【X-series 張力マップ】(WF 間の Series 関係)",
        f"  関与 Series: {', '.join(series_codes)} ({len(edges)} エッジ)",
    ] + edges + [
        "  → 張力の高いエッジを意識して WF 間の整合性を確認すること。",
    ]
    return "\n".join(lines)


# PURPOSE: θ7.3 次 WF 提案のフォールバック (環境強制)
# morphism_proposer.suggest_from_xseries() に委譲。
# dispatch.py 内の深度ゲートのみ担当。
def _build_next_wf_suggestion(workflows: list, depth_level: int) -> str:
    """θ7.3 WF 完了後の次の WF 候補を X-series エッジから自動提案。

    L2+ でのみ発動。ロジックは morphism_proposer.suggest_from_xseries() に委譲。
    """
    if depth_level < 2:
        return ""

    try:
        from mekhane.taxis.morphism_proposer import suggest_from_xseries
        result = suggest_from_xseries(workflows)
        return result or ""
    except ImportError:
        return ""


# PURPOSE: L3 (+ 修飾子) のとき外部検索義務を注入 (N-5 θ5.2 環境強制)
def _build_l3_search_section(workflows: list) -> str:
    """L3 深化 CCL に対する外部検索義務の環境強制テキストを生成。

    + 修飾子は L3 深化を意味する。L3 では外部検索 (Periskopē/Gnōsis/S2)
    の実行が義務 (θ5.2)。意志依存では弱いため (第零原則)、
    dispatch 層でメッセージを物理注入して検索スキップを防止する。
    """
    wf_names = ", ".join(workflows) if workflows else "(WF未検出)"
    lines = [
        "⚠️ 【L3 外部検索義務 — N-5 θ5.2】",
        f"  対象 WF: {wf_names}",
        "  + 修飾子 = L3 深化。以下の検索を省略してはならない:",
        "    □ Periskopē (periskope_research): 外部ソース並列検索",
        "    □ Gnōsis (mneme search scope=papers): 論文DB 検索",
        "    □ S2 (digestor_paper search): Semantic Scholar 検索",
        "  → 検索結果を統合してから本体の分析・実行に入ること。",
        "  → 検索をスキップした場合、L3 品質は保証されない。",
    ]
    return "\n".join(lines)


# PURPOSE: AST 内の条件分岐の網羅性をチェック (Pepsis Rust Phase 2 — exhaustive_check.md)
def exhaustive_check(node, depth=0) -> list[str]:
    """AST を再帰走査し、/dia+ を含む式で条件分岐の網羅性を検証。

    Rust の exhaustive pattern matching に着想を得た設計。
    I: があれば E: (else) が必須。EI: チェーンも E: で終端すべき。

    Returns:
        list of warning strings (空なら問題なし)
    """
    from hermeneus.src.ccl_ast import (
        Oscillation, Fusion, Sequence, ConvergenceLoop,
        ColimitExpansion, ForLoop, IfCondition, WhileLoop,
        TaggedBlock, Pipeline, Parallel, Adjunction, Morphism, Group
    )

    warnings = []

    if isinstance(node, IfCondition):
        # I: があるが E: がない → 非網羅的
        if node.else_branch is None:
            cond_str = f"{node.condition.var} {node.condition.op} {node.condition.value}"
            warnings.append(
                f"⚠️ [exhaustive] I:[{cond_str}] に E:{{}} (else) がありません。"
                f" 全ケースを網羅していない可能性があります。"
            )
        else:
            # else_branch も再帰チェック
            warnings.extend(exhaustive_check(node.else_branch, depth + 1))
        # then_branch も再帰チェック
        warnings.extend(exhaustive_check(node.then_branch, depth + 1))

    elif isinstance(node, Sequence):
        for step in node.steps:
            warnings.extend(exhaustive_check(step, depth + 1))
    elif isinstance(node, Oscillation):
        warnings.extend(exhaustive_check(node.left, depth + 1))
        warnings.extend(exhaustive_check(node.right, depth + 1))
    elif isinstance(node, Fusion):
        warnings.extend(exhaustive_check(node.left, depth + 1))
        warnings.extend(exhaustive_check(node.right, depth + 1))
    elif isinstance(node, ColimitExpansion):
        warnings.extend(exhaustive_check(node.body, depth + 1))
    elif isinstance(node, ConvergenceLoop):
        warnings.extend(exhaustive_check(node.body, depth + 1))
    elif isinstance(node, ForLoop):
        warnings.extend(exhaustive_check(node.body, depth + 1))
    elif isinstance(node, WhileLoop):
        warnings.extend(exhaustive_check(node.body, depth + 1))
    elif isinstance(node, TaggedBlock):
        warnings.extend(exhaustive_check(node.body, depth + 1))
    elif isinstance(node, Pipeline):
        for step in node.steps:
            warnings.extend(exhaustive_check(step, depth + 1))
    elif isinstance(node, Parallel):
        for branch in node.branches:
            warnings.extend(exhaustive_check(branch, depth + 1))
    elif isinstance(node, Adjunction):
        warnings.extend(exhaustive_check(node.left, depth + 1))
        warnings.extend(exhaustive_check(node.right, depth + 1))
    elif isinstance(node, Morphism):
        warnings.extend(exhaustive_check(node.source, depth + 1))
        warnings.extend(exhaustive_check(node.target, depth + 1))
    elif isinstance(node, Group):
        warnings.extend(exhaustive_check(node.body, depth + 1))

    return warnings


# PURPOSE: 並列実行 (||) ノードの安全性チェック (Pepsis Rust Phase 2 — parallel_model.md)
def parallel_safety_check(node, depth=0) -> list[str]:
    """AST を再帰走査し、|| ノードの安全性を検証。

    Rust の Send/Sync 特性に着想を得た設計。
    同一 WF が複数ブランチに出現する場合、データ競合の可能性を警告。

    Returns:
        list of warning strings (空なら問題なし)
    """
    from hermeneus.src.ccl_ast import (
        Oscillation, Fusion, Sequence, ConvergenceLoop,
        ColimitExpansion, ForLoop, IfCondition, WhileLoop,
        TaggedBlock, Pipeline, Parallel, Adjunction, Morphism, Group
    )

    warnings = []

    if isinstance(node, Parallel):
        # 各ブランチから WF ID を収集
        branch_wfs = []
        for branch in node.branches:
            wfs = set(extract_workflows(branch))
            branch_wfs.append(wfs)

        # ブランチ間の重複 WF を検出
        for i in range(len(branch_wfs)):
            for j in range(i + 1, len(branch_wfs)):
                shared = branch_wfs[i] & branch_wfs[j]
                if shared:
                    shared_str = ", ".join(sorted(shared))
                    warnings.append(
                        f"⚠️ [parallel] || ブランチ {i+1} と {j+1} で同一 WF ({shared_str}) が重複。"
                        f" データ競合の可能性があります。`*` で共有参照にするか、独立した WF に分割してください。"
                    )

        # 各ブランチも再帰チェック
        for branch in node.branches:
            warnings.extend(parallel_safety_check(branch, depth + 1))

    elif isinstance(node, Sequence):
        for step in node.steps:
            warnings.extend(parallel_safety_check(step, depth + 1))
    elif isinstance(node, Oscillation):
        warnings.extend(parallel_safety_check(node.left, depth + 1))
        warnings.extend(parallel_safety_check(node.right, depth + 1))
    elif isinstance(node, Fusion):
        warnings.extend(parallel_safety_check(node.left, depth + 1))
        warnings.extend(parallel_safety_check(node.right, depth + 1))
    elif isinstance(node, ColimitExpansion):
        warnings.extend(parallel_safety_check(node.body, depth + 1))
    elif isinstance(node, ConvergenceLoop):
        warnings.extend(parallel_safety_check(node.body, depth + 1))
    elif isinstance(node, ForLoop):
        warnings.extend(parallel_safety_check(node.body, depth + 1))
    elif isinstance(node, WhileLoop):
        warnings.extend(parallel_safety_check(node.body, depth + 1))
    elif isinstance(node, TaggedBlock):
        warnings.extend(parallel_safety_check(node.body, depth + 1))
    elif isinstance(node, Pipeline):
        for step in node.steps:
            warnings.extend(parallel_safety_check(step, depth + 1))
    elif isinstance(node, IfCondition):
        warnings.extend(parallel_safety_check(node.then_branch, depth + 1))
        if node.else_branch:
            warnings.extend(parallel_safety_check(node.else_branch, depth + 1))
    elif isinstance(node, Adjunction):
        warnings.extend(parallel_safety_check(node.left, depth + 1))
        warnings.extend(parallel_safety_check(node.right, depth + 1))
    elif isinstance(node, Morphism):
        warnings.extend(parallel_safety_check(node.source, depth + 1))
        warnings.extend(parallel_safety_check(node.target, depth + 1))
    elif isinstance(node, Group):
        warnings.extend(parallel_safety_check(node.body, depth + 1))

    return warnings


# PURPOSE: WF ID → WF定義ファイルの絶対パスに解決。
def _find_hgk_root() -> Path:
    """HGK ルートディレクトリを自動検出。

    検索順序:
        1. 環境変数 HGK_ROOT
        2. dispatch.py から親を辿り *知性*Nous ディレクトリを持つ祖先を検出
    """
    import os
    env_root = os.environ.get("HGK_ROOT")
    if env_root:
        return Path(env_root)
    # dispatch.py → src/ → hermeneus/ → _src/ → Mekhane/ → 01_ヘゲモニコン
    candidate = Path(__file__).parent
    for _ in range(8):
        candidate = candidate.parent
        if list(candidate.glob("*知性*Nous")):
            return candidate
    # フォールバック: 旧動作 (project_root = _src/)
    return Path(__file__).parent.parent.parent


def _resolve_wf_dirs() -> list[Path]:
    """WF 検索ディレクトリのリストを返す (優先順)。"""
    hgk_root = _find_hgk_root()
    dirs = []
    # 1. 新構造: 10_知性｜Nous/02_手順｜Procedures/A_手順｜Workflows/
    for nous_dir in sorted(hgk_root.glob("*知性*Nous")):
        for procedures_dir in sorted(nous_dir.glob("*手順*Procedures")):
            for wf_dir in sorted(procedures_dir.glob("*手順*Workflows")):
                if wf_dir.is_dir():
                    dirs.append(wf_dir)
    # 2. .agents/workflows/ (IDE ワークフロー)
    agents_wf = hgk_root / ".agents" / "workflows"
    if agents_wf.is_dir():
        dirs.append(agents_wf)
    agent_wf = hgk_root / ".agent" / "workflows"
    if agent_wf.is_dir():
        dirs.append(agent_wf)
    # 3. 旧構造 (フォールバック): project_root / nous / workflows
    legacy_dir = Path(__file__).parent.parent.parent / "nous" / "workflows"
    if legacy_dir.is_dir():
        dirs.append(legacy_dir)
    return dirs


def resolve_wf_paths(wf_ids: list[str]) -> dict[str, str]:
    """WF ID → WF定義ファイルの絶対パスに解決。

    /dia → dia.md, /noe → noe.md のように対応。
    存在しないファイルは除外。

    検索順序 (各 wf_dir について):
        1. {wf_dir}/{name}.md (フラットパス)
        2. {wf_dir}/**/{name}.md (再帰検索 — サブディレクトリ内)

    Returns:
        {"/dia": "/absolute/path/.../dia.md", ...}
    """
    wf_dirs = _resolve_wf_dirs()
    paths = {}
    for wf_id in wf_ids:
        clean = wf_id.lstrip("/")
        # 演算子を除去したベース名も用意
        base = clean.rstrip("+-^!?'")
        names_to_try = [clean]
        if base != clean:
            names_to_try.append(base)

        for name in names_to_try:
            if wf_id in paths:
                break
            for wf_dir in wf_dirs:
                # 1. フラットパス検索
                wf_path = wf_dir / f"{name}.md"
                if wf_path.exists():
                    paths[wf_id] = str(wf_path.resolve())
                    break
                # 2. 再帰検索 (サブディレクトリ内)
                matches = list(wf_dir.rglob(f"{name}.md"))
                if matches:
                    paths[wf_id] = str(matches[0].resolve())
                    break
    return paths


# PURPOSE: WF 定義ファイルから構造的要約を自動抽出 (L1 テンプレート自動充填)
def resolve_wf_summaries(wf_paths: dict[str, str]) -> dict[str, dict]:
    """WF 定義ファイルから purpose / phases / output_hint を抽出。

    抽出元:
      - YAML frontmatter の description: → purpose (fallback)
      - blockquote `> **目的**:` → purpose (優先)
      - `## 処理フロー` or `PHASE N` 見出し → phases
      - `## 出力形式` → output_hint

    Returns:
        {"/noe": {"purpose": "...", "phases": [...], "output_hint": "..."}, ...}
    """
    import re
    import yaml as _yaml

    summaries: dict[str, dict] = {}

    for wf_id, wf_path_str in wf_paths.items():
        summary: dict = {"purpose": "", "phases": [], "output_hint": ""}

        try:
            content = Path(wf_path_str).read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            summaries[wf_id] = summary
            continue

        # --- 1. YAML frontmatter から description を抽出 ---
        fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if fm_match:
            try:
                fm = _yaml.safe_load(fm_match.group(1))
                if isinstance(fm, dict) and fm.get("description"):
                    summary["purpose"] = fm["description"]
            except Exception:  # noqa: BLE001
                pass

        # --- 2. blockquote `> **目的**:` で上書き (より具体的) ---
        # frontmatter 直後 〜 最初の ## セクション見出しまでに限定
        # (各 STEP/PHASE 内の局所的な `> **目的**:` を拾わない)
        body = content[fm_match.end():] if fm_match else content
        # 最初の "## " 見出しの前までを冒頭定義ブロックとする
        intro_lines = []
        for line in body.split("\n"):
            if line.startswith("## "):
                break
            intro_lines.append(line)
        intro_block = "\n".join(intro_lines)
        purpose_match = re.search(
            r">\s*\*\*目的\*\*\s*[:：]\s*(.+)", intro_block
        )
        if purpose_match:
            summary["purpose"] = purpose_match.group(1).strip()

        # --- 3. PHASE / STEP 行を抽出 ---
        # パターン: "N. **PHASE N" or "N. **STEP N" (numbered list items)
        phase_pattern = re.compile(
            r"^\d+\.\s+\*\*(?:PHASE|STEP)\s+[\d.]+[\w]*\s*(?:—|:|-)\s*(.+?)\*\*",
            re.MULTILINE,
        )
        phases = phase_pattern.findall(content)
        if phases:
            summary["phases"] = [p.strip().rstrip("*") for p in phases]

        # fallback: `## PHASE N` 見出し
        if not summary["phases"]:
            heading_pattern = re.compile(
                r"^##\s+PHASE\s+\d+\s*(?:—|:|-)\s*(.+)", re.MULTILINE
            )
            summary["phases"] = [
                h.strip() for h in heading_pattern.findall(content)
            ]

        # --- 4. 出力形式セクションの冒頭を取得 ---
        output_match = re.search(
            r"##\s*出力形式\s*\n((?:.*\n){1,5})", content
        )
        if output_match:
            hint = output_match.group(1).strip()
            # コードフェンス (```) や空行を除外
            hint_lines = [
                l for l in hint.split("\n")
                if l.strip()
                and not l.strip().startswith("```")
                and "---" not in l
            ]
            if hint_lines:
                # テーブルヘッダーがあればそれだけ、なければ最初の行
                table_lines = [l for l in hint_lines if l.strip().startswith("|")]
                hint = table_lines[0] if table_lines else hint_lines[0]
                summary["output_hint"] = hint.strip()[:120]

        summaries[wf_id] = summary

    return summaries


# PURPOSE: WF 定義ファイルからサブモジュールのパスを抽出。
def resolve_submodules(wf_paths: dict[str, str]) -> dict[str, list[str]]:
    """WF 定義ファイルからサブモジュールのパスを抽出。

    WF の md ファイルを読み、## サブモジュール テーブル内の
    Markdown リンク [name](../path) を検出して絶対パスに解決する。

    Returns:
        {"/bye": ["/abs/path/value-pitch.md", "/abs/path/pitch_gallery.md"], ...}
    """
    import re
    submodules: dict[str, list[str]] = {}

    # Markdown リンクパターン: [text](relative/path.md)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+\.md)\)')

    for wf_id, wf_path_str in wf_paths.items():
        wf_path = Path(wf_path_str)
        subs: list[str] = []

        try:
            content = wf_path.read_text(encoding='utf-8')
        except Exception:  # noqa: BLE001
            continue

        # サブモジュールセクションを探す
        in_submodule_section = False
        for line in content.split('\n'):
            if line.strip().startswith('## サブモジュール') or line.strip().startswith('## Sub'):
                in_submodule_section = True
                continue
            if in_submodule_section and line.strip().startswith('## '):
                break  # 次のセクションに入った
            if in_submodule_section:
                for match in link_pattern.finditer(line):
                    rel_path = match.group(2)
                    # 相対パスを絶対パスに解決
                    abs_path = (wf_path.parent / rel_path).resolve()
                    if abs_path.exists():
                        subs.append(str(abs_path))

        if subs:
            submodules[wf_id] = subs

    return submodules


# PURPOSE: CCL 式をディスパッチ: パース → 構造表示 → 実行計画テンプレート
def dispatch(
    ccl_expr: str,
    context: str = "",
    invocation_mode: str = "explicit",
) -> DispatchResult:
    """CCL 式をディスパッチ: パース → 構造表示 → 実行計画テンプレート

    v3.0: @macro 検出時に MacroExecutor を自動実行し、
    エントロピー計測 + 逆伝播の結果を plan_template に埋め込む。
    これにより「意志より環境」(第零原則) が達成される。

    v3.3: 入力を冒頭で正規化し、マクロなら展開結果をパーサーに渡す。
    AST とマクロ計画の矛盾を解消 (反証 1 修復)。

    Returns:
        DispatchResult: TypedDict — success, ast, tree, workflows,
                        wf_paths, wf_submodules, plan_template, macro_plan, error 等
    """
    from hermeneus.src.parser import CCLParser as _Parser
    from hermeneus.src.ccl_normalizer import normalize_ccl_input, is_ccl_macro

    # Step -1: 入力の正規化 (v3.3 — 全経路で最初に実行)
    # /ccl-plan- → @plan-, @plan → @plan, /noe+ → /noe+
    original_input = ccl_expr
    ccl_expr = normalize_ccl_input(ccl_expr)

    # マクロ入力の場合、AST パースは展開後の CCL で行う
    # 展開は MacroExecutor (Step 2.5) に一本化 — ここでは展開しない (v4: 二重初期化排除)
    parse_target = ccl_expr

    parser = _Parser()
    result: DispatchResult = {  # type: ignore[typeddict-item]
        "success": False,
        "ccl": ccl_expr,
        "ast": None,
        "tree": "",
        "workflows": [],
        "wf_paths": {},
        "wf_submodules": {},
        "wf_summaries": {},
        "plan_template": "",
        "macro_plan": None,
        "error": None,
        "contract": {},
    }


    # Step 0: パース (マクロなら展開結果をパースする)
    try:
        ast = parser.parse(parse_target)
        result["ast"] = ast
        result["success"] = True
    except Exception as e:  # noqa: BLE001
        result["error"] = str(e)
        return result

    # Step 1: 木構造表示
    result["tree"] = format_ast_tree(ast)

    # Step 2: ワークフロー抽出 + パス解決 + 要約抽出
    result["workflows"] = extract_workflows(ast)
    result["wf_paths"] = resolve_wf_paths(result["workflows"])
    result["wf_submodules"] = resolve_submodules(result["wf_paths"])
    result["wf_summaries"] = resolve_wf_summaries(result["wf_paths"])

    # Step 2.2: CCL execution contract compile
    try:
        from hermeneus.src.ccl_contracts import compile_ccl_contract
        result["contract"] = compile_ccl_contract(
            ccl_expr,
            invocation_mode=invocation_mode,
        ).to_dict()
    except Exception as _contract_err:  # noqa: BLE001
        import logging as _log
        _log.getLogger(__name__).warning("CCL contract compile error: %s", _contract_err)
        result["contract_error"] = str(_contract_err)

    # Step 2.3: 網羅性チェック (Pepsis Rust — exhaustive_check)
    exhaustive_warnings = exhaustive_check(ast)
    result["exhaustive_warnings"] = exhaustive_warnings

    # Step 2.4: 並列安全性チェック (Pepsis Rust — parallel_safety_check)
    parallel_warnings = parallel_safety_check(ast)
    result["parallel_warnings"] = parallel_warnings

    # Step 2.5: マクロ自動実行計画 (L1 環境制約)
    # v3.3: ccl_expr は冒頭で正規化済み。is_ccl_macro も冒頭で import 済み。
    macro_section = ""

    if is_ccl_macro(ccl_expr):
        try:
            from hermeneus.src.macro_executor import MacroExecutor
            executor = MacroExecutor()
            macro_result = executor.execute(ccl_expr)
            result["macro_plan"] = macro_result

            # N3: 展開後の CCL で AST を再構築し還流
            try:
                expanded_ast = parser.parse(macro_result.expanded_ccl)
                result["ast"] = expanded_ast
                # AP-3: AST 更新後にワークフロー関連情報も再抽出
                result["workflows"] = extract_workflows(expanded_ast)
                result["wf_paths"] = resolve_wf_paths(result["workflows"])
                result["wf_submodules"] = resolve_submodules(result["wf_paths"])
                result["wf_summaries"] = resolve_wf_summaries(result["wf_paths"])
            except Exception as e:  # noqa: BLE001
                # AP-5: サイレント失敗を解消 — ログに記録
                import logging
                logging.getLogger(__name__).debug("展開後 CCL のパース失敗 (元の AST を維持): %s", e)

            # AP-4: depth_labels は ExecutionResult._DEPTH_LABELS を正規の定義として参照
            from hermeneus.src.macro_executor import ExecutionResult as _ER
            depth_label = _ER._DEPTH_LABELS.get(macro_result.derivative, "L2")

            # マクロ実行計画セクションを生成
            lines = [
                f"【マクロ実行計画】@macro → AST walk (自動生成)",
                f"  展開: {macro_result.expanded_ccl}",
                f"  深度: {depth_label}",
                f"  ステップ数: {len(macro_result.steps)}",
                f"  確信度: {macro_result.final_confidence:.0%}",
            ]
            if macro_result.bottleneck_step:
                lines.append(
                    f"  ⚠️ ボトルネック: {macro_result.bottleneck_step} "
                    f"(gradient={macro_result.gradient_map.get(macro_result.bottleneck_step, 0):.2f})"
                )
            lines.append("  実行順序:")
            for i, step in enumerate(macro_result.steps, 1):
                lines.append(f"    {i}. {step.node_id} (Δε={step.entropy_reduction:+.2f})")
            lines.append("  → 上記順序で各 WF 定義を view_file し、順次実行せよ")

            macro_section = "\n".join(lines)
        except Exception as e:  # noqa: BLE001
            macro_section = f"【マクロ実行計画】⚠️ MacroExecutor エラー: {e}"

    # Step 3: 射提案の自動生成 (N-8 引力化)
    morphism_section = ""
    try:
        from mekhane.taxis.morphism_proposer import parse_trigonon, format_proposal
        for wf_id, wf_path in result["wf_paths"].items():
            trigonon = parse_trigonon(Path(wf_path))
            if trigonon:
                proposal = format_proposal(
                    wf_id.lstrip("/"), trigonon, confidence=None
                )
                morphism_section += f"\n{proposal}\n"
    except Exception:  # noqa: BLE001
        morphism_section = "\n  (射提案の自動生成に失敗 — 手動で trigonon を確認)\n"

    # Step 4: 実行計画テンプレート
    wf_list = ", ".join(result["workflows"])

    # view_file コマンド一覧 (Agent がコピペで開ける)
    view_lines = []
    for wf_id, wf_path in result["wf_paths"].items():
        view_lines.append(f"  view_file {wf_path}")
        # サブモジュールがあれば階層表示
        subs = result["wf_submodules"].get(wf_id, [])
        for i, sub_path in enumerate(subs):
            prefix = "└──" if i == len(subs) - 1 else "├──"
            sub_name = Path(sub_path).name
            view_lines.append(f"    {prefix} view_file {sub_path}  ({sub_name})")
    view_cmds = "\n".join(view_lines)
    if not view_cmds:
        view_cmds = "  (WF 定義ファイルが見つかりません)"

    # マクロセクションがあれば plan_template の先頭に挿入
    macro_block = f"\n{macro_section}\n" if macro_section else ""

    # Step 5: 実行計画の自動充填 (L1 テンプレート自動充填)
    execution_plan_lines = []
    wf_summaries = result["wf_summaries"]
    for i, wf_id in enumerate(result["workflows"], 1):
        summary = wf_summaries.get(wf_id, {})
        purpose = summary.get("purpose", "")
        phases = summary.get("phases", [])
        output_hint = summary.get("output_hint", "")

        line = f"  Step {i}: {wf_id}"
        if purpose:
            line += f"\n    目的: {purpose}"
        if phases:
            phase_str = " → ".join(phases[:5])  # 最大5フェーズ
            line += f"\n    フェーズ: {phase_str}"
        if output_hint:
            line += f"\n    出力: {output_hint}"
        execution_plan_lines.append(line)

    if execution_plan_lines:
        execution_plan = "\n".join(execution_plan_lines)
    else:
        execution_plan = "  (WF 要約を抽出できませんでした — view_file で確認してください)"

    # Step 5.5: CCL 中間表現 (IR) 生成 (Activity 2)
    ccl_ir = None
    try:
        from hermeneus.src.ccl_ir import ast_to_ir
        ccl_ir = ast_to_ir(ast, ccl_expr=ccl_expr)
        result["ir"] = ccl_ir
    except Exception as _ir_err:  # noqa: BLE001
        import logging as _log
        _log.getLogger(__name__).warning("IR 生成エラー (文字列ベースにフォールバック): %s", _ir_err)
        result["ir_error"] = str(_ir_err)

    # Step 6: 深度レベル判定
    # IR がある場合は IR の max_depth を使用、なければ文字列ベースのフォールバック
    if ccl_ir is not None:
        depth_level = ccl_ir.max_depth
    else:
        # フォールバック: 既存の文字列ベース判定
        has_plus = "+" in ccl_expr
        has_minus = "-" in ccl_expr and ">" not in ccl_expr  # >> は除外
        if has_plus:
            depth_level = 3
        elif has_minus:
            depth_level = 1
        else:
            depth_level = 2
    # Step 6.0a: Precision-Aware Routing (Activity 3)
    # context が渡されている場合、precision gradient で depth を動的調整
    precision_strategy = None
    precision_result = None  # P6: PrecisionResult (embedding 保持)
    if context and len(context) >= 100:
        try:
            from hermeneus.src.precision_router import (
                compute_context_precision,
                route_execution,
            )
            precision_result = compute_context_precision(context)
            precision_strategy = route_execution(precision_result.diff, depth_level)
            depth_level = precision_strategy.depth_level
        except ImportError:
            import logging as _log
            _log.getLogger(__name__).info(
                "precision_router 未インストール — 深度レベル %d で続行", depth_level
            )
        except Exception as _e:  # noqa: BLE001
            import logging as _log
            _log.getLogger(__name__).info(
                "precision_router エラー (フォールバック): %s", _e
            )

    result["depth_level"] = depth_level
    if precision_strategy is not None:
        result["precision_strategy"] = {
            "precision_ml": precision_strategy.precision_ml,
            "strategy": precision_strategy.reasoning,
            "search_budget": precision_strategy.search_budget,
            "gnosis_search": precision_strategy.gnosis_search,
            "confidence_threshold": precision_strategy.confidence_threshold,
        }

    # Step 6.0b: Precision + Linkage → IR 注入 (Activity 2-3 接続)
    # precision_router の diff 値を IR の precision_ml [0,1] にマッピングし、
    # WF description embedding で coherence/drift を算出し、全ノードに伝播。
    if ccl_ir is not None and precision_strategy is not None:
        try:
            from hermeneus.src.ccl_ir import diff_to_precision_ml
            p_ml = diff_to_precision_ml(precision_strategy.precision_ml)

            # P6: Linkage metrics (coherence / drift)
            linkage_coherence = None
            linkage_drift = None
            if precision_result is not None and precision_result.embedding:
                try:
                    from hermeneus.src.precision_router import compute_linkage
                    # IR から WF ID を抽出
                    wf_ids = [
                        n.wf_id for n in ccl_ir.workflow_nodes if n.wf_id
                    ]
                    if wf_ids:
                        linkage = compute_linkage(
                            precision_result.embedding, wf_ids
                        )
                        linkage_coherence = linkage.coherence
                        linkage_drift = linkage.drift
                        result["linkage"] = {
                            "coherence": linkage.coherence,
                            "drift": linkage.drift,
                            "wf_ids": list(linkage.wf_ids),
                            "reasoning": linkage.reasoning,
                        }
                except Exception as _lk_err:  # noqa: BLE001
                    import logging as _log
                    _log.getLogger(__name__).warning(
                        "Linkage 算出エラー: %s", _lk_err
                    )

            ccl_ir.propagate_precision(
                precision_ml=p_ml,
                coherence=linkage_coherence,
                drift=linkage_drift,
            )
            result["ir_effective_depth"] = ccl_ir.root.effective_depth
        except Exception as _p_err:  # noqa: BLE001
            import logging as _log
            _log.getLogger(__name__).warning(
                "IR precision 注入エラー: %s", _p_err
            )

    # Step 6.1: Forgetful Functor — 忘却レベル計算 (C3)
    # 核心: depth_level と forget_level は逆相関。深い思考 = 多く保存。
    # forget_level = 4 - depth_level (depth 0-3 → forget 4-1)
    FORGET_NAMES = {0: "Nothing", 1: "Context", 2: "Design", 3: "Impl", 4: "All"}
    forget_level = max(0, min(4, 4 - depth_level))  # clamp to [0, 4]
    result["forget_level"] = forget_level
    result["forget_names"] = FORGET_NAMES

    # per-WF 忘却マッピング: AST の operators フィールドから個別忘却レベルを計算
    forget_mapping: Dict[str, int] = {}

    def _collect_wf_operators(node: Any) -> Dict[str, list]:
        """AST を再帰走査し、WF ID → operators リストを収集。"""
        from hermeneus.src.ccl_ast import (
            Workflow as WfNode, Oscillation, Fusion, Sequence,
            ColimitExpansion, ForLoop, IfCondition, Pipeline, Parallel, Group
        )
        result_map: Dict[str, list] = {}
        if isinstance(node, WfNode):
            result_map[f"/{node.id}"] = node.operators
        elif isinstance(node, Oscillation):
            result_map.update(_collect_wf_operators(node.left))
            result_map.update(_collect_wf_operators(node.right))
        elif isinstance(node, Fusion):
            result_map.update(_collect_wf_operators(node.left))
            result_map.update(_collect_wf_operators(node.right))
        elif isinstance(node, (Sequence, Pipeline, Parallel)):
            for child in getattr(node, 'steps', getattr(node, 'branches', [])):
                result_map.update(_collect_wf_operators(child))
        elif isinstance(node, (ForLoop, IfCondition)):
            result_map.update(_collect_wf_operators(getattr(node, 'body', None)))
        elif isinstance(node, ColimitExpansion):
            result_map.update(_collect_wf_operators(node.body))
        elif isinstance(node, Group):
            # Group内の各WFにGroupのオペレーターを追加した扱いでマージする
            inner_ops = _collect_wf_operators(node.body)
            for wid, ops in inner_ops.items():
                # 既存のリストを変更せず新しいリストを作る
                new_ops = ops.copy()
                for op in node.operators:
                    if op not in new_ops:
                        new_ops.append(op)
                inner_ops[wid] = new_ops
            result_map.update(inner_ops)
        return result_map

    from hermeneus.src.ccl_ast import OpType
    wf_ops = _collect_wf_operators(result.get("ast"))
    for wf_id, ops in wf_ops.items():
        # DEEPEN (+) → Context (1), CONDENSE (-) → Impl (3), 無印 → Design (2)
        if OpType.DEEPEN in ops:
            forget_mapping[wf_id] = 1   # Context: 文脈まで保存
        elif OpType.CONDENSE in ops:
            forget_mapping[wf_id] = 3   # Impl: 実装まで忘却
        else:
            forget_mapping[wf_id] = 2   # Design: 標準
    result["forget_mapping"] = forget_mapping

    # Step 6.1b: 忘却レベルの合成則 (F5)
    # Sequence/Fusion = max (pessimistic: 最大忘却に引きずられる)
    # Oscillation = min (optimistic: 反復で情報が回復する)
    def _compose_forget_levels(node: Any, fmap: Dict[str, int]) -> int:
        """AST 構造に基づく忘却レベルの合成。"""
        from hermeneus.src.ccl_ast import (
            Workflow as WfNode, Oscillation as Osc, Fusion as Fus,
            Sequence as Seq, Pipeline as Pipe, Parallel as Par,
            ForLoop as FLp, IfCondition as IfC, ColimitExpansion as Col, Group
        )
        if isinstance(node, WfNode):
            return fmap.get(f"/{node.id}", 2)
        elif isinstance(node, Osc):
            l = _compose_forget_levels(node.left, fmap)
            r = _compose_forget_levels(node.right, fmap)
            if getattr(node, 'divergent', False):
                # ~! 発散振動: max — 情報が散乱する
                return max(l, r)
            else:
                # ~ / ~* 収束振動: min — 反復は情報を回復する
                return min(l, r)
        elif isinstance(node, Fus):
            # Fusion: max — 融合は保守的
            l = _compose_forget_levels(node.left, fmap)
            r = _compose_forget_levels(node.right, fmap)
            return max(l, r)
        elif isinstance(node, (Seq, Pipe)):
            # Sequence/Pipeline: max — 順次は情報が減衰する
            children = getattr(node, 'steps', [])
            if not children:
                return 2
            return max(_compose_forget_levels(c, fmap) for c in children)
        elif isinstance(node, Par):
            # Parallel: min — 並列は最も保存する分岐が活きる
            branches = getattr(node, 'branches', [])
            if not branches:
                return 2
            return min(_compose_forget_levels(c, fmap) for c in branches)
        elif isinstance(node, (FLp, IfC)):
            body = getattr(node, 'body', None)
            if body:
                return _compose_forget_levels(body, fmap)
            return 2
        elif isinstance(node, Col):
            return _compose_forget_levels(node.body, fmap)
        elif isinstance(node, Group):
            return _compose_forget_levels(node.body, fmap)
        return 2  # fallback: Design

    ast_node = result.get("ast")
    if ast_node and forget_mapping:
        composed = _compose_forget_levels(ast_node, forget_mapping)
        result["forget_level"] = composed  # 合成後の値で上書き

    # Step 6.1c: Basanos 忘却回復 deficits (F7)
    # forget_level >= 2 の WF に対し、忘却された情報を問う deficit を生成
    # Basanos が実装されたときに consume する接続点
    forget_deficits: list = []
    PRESERVED_INFO = {
        1: ["context", "design", "impl"],   # Context: 全保存
        2: ["design", "impl"],              # Design: 設計+実装
        3: ["impl"],                        # Impl: 実装のみ
        4: [],                              # All: 全忘却
    }
    FORGOTTEN_INFO = {
        1: [],                              # Context: なし
        2: ["context"],                     # Design: 文脈を忘却
        3: ["context", "design"],           # Impl: 文脈+設計を忘却
        4: ["context", "design", "impl"],   # All: 全忘却
    }
    for wf_id, fl in forget_mapping.items():
        if fl >= 2:  # Design 以上の忘却
            forget_deficits.append({
                "wf": wf_id,
                "forget_level": fl,
                "forget_name": FORGET_NAMES.get(fl, "Unknown"),
                "forgotten": FORGOTTEN_INFO.get(fl, []),
                "preserved": PRESERVED_INFO.get(fl, []),
                "question_type": "recovery",
            })
    result["forget_deficits"] = forget_deficits

    # Step 6.2: Adaptive Depth トリガー (Context Rot v3.5)
    result["adaptive_depth"] = {
        "current_level": depth_level,
        "triggers": [
            {"condition": "N-2 (θ2.2) FaR confidence <50% x2", "action": "propose L+1"},
            {"condition": "AMP loop Stage 3→1 x2", "action": "force L+1"},
            {"condition": "Creator explicit request", "action": "immediate L+1"},
        ],
    }

    # UML セクション: L2+ のみ (θ2.3 — 深度別差分化)
    if depth_level >= 3:
        # L3 Deep: 全チェック + INPUT TAINT 検証 + AMP ループ
        uml_pre = """【UML Pre-check — L3】(WF 実行前に必ず回答)
  S1 [Noēsis]: 入力を正しく理解したか？ → (回答)
  S2 [Hypomnēsis]: 第一印象・直感はどうか？ → (回答)
  S2b [INPUT TAINT]: 前セッション由来の前提はないか？ → (回答)
    「この結論は、入力がなくても同じに至るか？」"""
        uml_post = """【UML Post-check — L3】(WF 実行後に必ず回答)
  S3 [Elenchos]: 批判的に再評価したか？ → (回答)
    CD-3 確証バイアス: 反証を探したか？
    CD-5 迎合推論: Creator に合わせていないか？
  S4 [Energeia]: 決定は妥当か？ 説明できるか？ → (回答)
  S5 [Katalēpsis]: 確信度は適切か？ 過信していないか？ → (回答)
  🔄 AMP ループ: S5 で過信を検出 → S1 に戻る (最大2回)"""
    elif depth_level >= 2:
        # L2 Standard: 基本チェック + CD 指示
        uml_pre = """【UML Pre-check】(WF 実行前に回答)
  S1 [Noēsis]: 入力を正しく理解したか？ → (回答)
  S2 [Hypomnēsis]: 第一印象・直感はどうか？ → (回答)"""
        uml_post = """【UML Post-check】(WF 実行後に回答)
  S3 [Elenchos]: 批判的に再評価したか？ → (回答)
  S4 [Energeia]: 決定は妥当か？ 説明できるか？ → (回答)
  S5 [Katalēpsis]: 確信度は適切か？ 過信していないか？ → (回答)"""
    else:
        uml_pre = ""
        uml_post = ""

    # 射提案セクション: L2+ のみ、かつ改善版フォーマット
    if depth_level >= 2 and morphism_section.strip():
        morphism_block = f"""【射提案 @complete】(WF 完了時に以下を出力すること)
{morphism_section}"""
    else:
        morphism_block = ""

    # Step 7: 演算子警告の生成 (spec_injector + ccl_linter + failure_db 連携)
    warnings_block = ""
    quiz_block = ""
    try:
        from mekhane.ccl.spec_injector import (
            get_warnings_for_expr, get_warned_operators, SpecInjector
        )
        # 7a: 既知の危険パターン警告 (ccl_linter から取得)
        op_warnings = get_warnings_for_expr(ccl_expr)
        already_warned = get_warned_operators(ccl_expr)

        # 7b: failure_db からの過去失敗パターン警告 (演算子ベース重複排除)
        try:
            from mekhane.ccl.learning.failure_db import get_failure_db
            db = get_failure_db()
            db_warnings = db.get_warnings(ccl_expr)
            for w in db_warnings:
                if w.operator not in already_warned:
                    op_warnings.append(f"⚠️ [{w.severity}] {w.operator}: {w.message}")
                    already_warned.add(w.operator)
        except (ImportError, Exception):  # noqa: BLE001
            pass

        if op_warnings:
            warnings_block = "【⚠️ 演算子注意】\n" + "\n".join(f"  {w}" for w in op_warnings)

        # 7c: 危険演算子含有時のみ理解確認クイズを注入
        dangerous_ops = {'!', '*^', '\\'}
        injector = SpecInjector()
        detected_ops = injector.parse_operators(ccl_expr)
        # parse_operators が複合演算子も検出するため、直接 & で判定
        quiz_target = detected_ops & dangerous_ops
        if quiz_target:
            quiz_block = injector.generate_quiz(quiz_target)
            # G4: クイズ効果ログ — 生成を記録
            try:
                from mekhane.ccl.learning.quiz_logger import get_quiz_logger
                ql = get_quiz_logger()
                result["quiz_entry_id"] = ql.log_quiz_generated(  # type: ignore[typeddict-unknown-key]
                    ccl_expr=ccl_expr,
                    operators=quiz_target,
                )
            except (ImportError, Exception):  # noqa: BLE001
                pass
    except ImportError:
        pass  # spec_injector が利用不可の場合はスキップ

    # ---------------------------------------------------------
    # Step 7.1: 修飾子 (Dokimasia) の抽出と解決 (v4.1)
    # ---------------------------------------------------------
    def _collect_wf_modifiers(node: Any) -> Dict[str, dict]:
        """AST を再帰走査し、WF ID → modifiers 辞書を収集。"""
        from hermeneus.src.ccl_ast import (
            Workflow as WfNode, Oscillation, Fusion, Sequence,
            ColimitExpansion, ForLoop, IfCondition, Pipeline, Parallel, ModifierPeras
        )
        result_map: Dict[str, dict] = {}
        if isinstance(node, WfNode):
            result_map[f"/{node.id}"] = getattr(node, 'modifiers', {})
        elif isinstance(node, ModifierPeras):
            base_id = getattr(node.base_wf, 'id', 'unknown')
            coords = getattr(node, 'coordinates', [])
            preset = getattr(node, 'preset_name', '')
            if preset:
                desc = f"(preset: {preset})"
            elif not coords:
                desc = "(all coords)"
            else:
                desc = f"({','.join(coords)})"
            # 修飾子全展開の特別な表現として登録
            result_map[f"/{base_id}.ax {desc}"] = getattr(node.base_wf, 'modifiers', {})
            # ベースWF自体の修飾子も収集
            result_map.update(_collect_wf_modifiers(node.base_wf))
        elif isinstance(node, Oscillation):
            result_map.update(_collect_wf_modifiers(node.left))
            result_map.update(_collect_wf_modifiers(node.right))
        elif isinstance(node, Fusion):
            result_map.update(_collect_wf_modifiers(node.left))
            result_map.update(_collect_wf_modifiers(node.right))
        elif isinstance(node, (Sequence, Pipeline, Parallel)):
            for child in getattr(node, 'steps', getattr(node, 'branches', [])):
                result_map.update(_collect_wf_modifiers(child))
        elif isinstance(node, (ForLoop, IfCondition)):
            result_map.update(_collect_wf_modifiers(getattr(node, 'body', None)))
        elif isinstance(node, ColimitExpansion):
            result_map.update(_collect_wf_modifiers(node.body))
        return result_map

    try:
        from hermeneus.src.translator import WORKFLOW_DEFAULT_MODIFIERS
        wf_modifiers = _collect_wf_modifiers(ast)
        mod_lines = []
        qx_lines = []  # Q-series / X-series 専用行
        for wf_id, explicit_mods in wf_modifiers.items():
            clean_id = wf_id.lstrip("/")
            default_mods = WORKFLOW_DEFAULT_MODIFIERS.get(clean_id, {})
            
            # Q-series / X-series 修飾子を分離
            q_mods = {k: v for k, v in explicit_mods.items() if k.startswith("_q_")}
            x_mods = {k: v for k, v in explicit_mods.items() if k.startswith("_x_")}
            normal_mods = {k: v for k, v in explicit_mods.items()
                          if not k.startswith("_q_") and not k.startswith("_x_")}
            
            # Q-series 表示
            if q_mods.get("_q_edge"):
                qx_lines.append(
                    f"  - {wf_id}: Q[{q_mods['_q_edge']}] "
                    f"(循環: {q_mods.get('_q_src', '?')}→{q_mods.get('_q_dst', '?')})"
                )
            # X-series 表示
            if x_mods.get("_x_edge"):
                qx_lines.append(
                    f"  - {wf_id}: .{x_mods.get('_x_dot', '??')} "
                    f"({x_mods['_x_edge']}: {x_mods.get('_x_coords', '?')})"
                )
            
            # 通常 Dokimasia パラメータの表示
            if normal_mods or default_mods:
                mod_strs = []
                for k, v in default_mods.items():
                    if k in normal_mods:
                        mod_strs.append(f"{k}:{normal_mods[k]} (override)")
                    else:
                        mod_strs.append(f"{k}:{v} (default)")
                for k, v in normal_mods.items():
                    if k not in default_mods:
                        mod_strs.append(f"{k}:{v} (explicit)")
                if mod_strs:
                    mod_lines.append(f"  - {wf_id}: " + ", ".join(mod_strs))
        
        modifier_block = ""
        if qx_lines:
            modifier_block += "【Q/X-series 修飾子】\n" + "\n".join(qx_lines)
        if mod_lines:
            if modifier_block:
                modifier_block += "\n"
            modifier_block += "【修飾子 (Dokimasia パラメータ)】\n" + "\n".join(mod_lines)
    except Exception as e:  # noqa: BLE001
        modifier_block = f"【修飾子取得エラー】: {e}"

    # テンプレート構築 (空セクションを除外して組み立て)
    sections = [
        f"【CCL】{ccl_expr}",
    ]
    if warnings_block:
        sections.append(warnings_block)
    sections += [
        f"【構造】\n{result['tree']}",
        f"【関連WF】{wf_list}",
    ]

    # 網羅性 + 並列安全性の警告を注入
    safety_warnings = result.get("exhaustive_warnings", []) + result.get("parallel_warnings", [])
    if safety_warnings:
        safety_block = "【🦀 Pepsis Safety Check】\n" + "\n".join(f"  {w}" for w in safety_warnings)
        sections.append(safety_block)

    sections += [
        f"【WF定義】以下を view_file で開くこと:\n{view_cmds}{macro_block}",
    ]
    # H-series 前動詞 (PreVerb) 環境強制セクション
    preverb_ids = extract_preverbs(ast)
    if preverb_ids:
        preverb_block = _build_preverb_section(preverb_ids)
        sections.append(preverb_block)
    # N-5 θ5.2 L3 外部検索義務の環境強制セクション
    if depth_level >= 3:
        l3_search_block = _build_l3_search_section(result.get("workflows", []))
        sections.append(l3_search_block)
    # P4: X-series 張力マップの自動可視化 (複数 Series にまたがる CCL)
    xseries_block = _build_xseries_section(result.get("workflows", []))
    if xseries_block:
        sections.append(xseries_block)
    if modifier_block:
        sections.append(modifier_block)
    if uml_pre:
        sections.append(uml_pre)
    sections.append(f"【実行計画】(AST 順序に基づく自動生成)\n{execution_plan}")
    if quiz_block:
        sections.append(f"【理解確認】\n{quiz_block}")
    sections.append("【/dia 反論】(AI が最低1つの懸念を提示)")
    if uml_post:
        sections.append(uml_post)
    if morphism_block:
        sections.append(morphism_block)
    else:
        # P5: θ7.3 フォールバック — trigonon frontmatter がない WF に対して
        # X-series エッジから次の WF 候補を自動提案
        next_suggestion = _build_next_wf_suggestion(
            result.get("workflows", []), depth_level
        )
        if next_suggestion:
            sections.append(next_suggestion)
    # Forgetful Functor セクション: L2+ で忘却レベルを表示
    if depth_level >= 2 and forget_mapping:
        forget_rows = []
        for wf_id, fl in forget_mapping.items():
            fl_name = FORGET_NAMES.get(fl, "?")
            preserved = [FORGET_NAMES[i] for i in range(fl, 5) if i > 0]
            preserved_str = " + ".join(preserved) if preserved else "—"
            forget_rows.append(f"  | {wf_id} | G{fl} ({fl_name}) | {preserved_str} |")
        forget_section = (
            "【🔮 Forgetful Functor】(C3 — 忘却レベル)\n"
            f"  全体忘却レベル: G{forget_level} ({FORGET_NAMES[forget_level]})\n"
            "  | WF | ForgetLevel | 保存される情報 |\n"
            "  |:---|:------------|:-------------|\n"
            + "\n".join(forget_rows)
        )
        sections.append(forget_section)
    # Adaptive Depth: L1 以下のとき深度上昇トリガーを表示
    if depth_level <= 1:
        ad_section = """【📈 Adaptive Depth】(実行中に以下を検知したら深度を上げよ)
  ・N-2 (θ2.2) FaR 確信度 <50% が 2 回連続 → L+1 を提案
  ・AMP ループ Stage 3→1 が 2 回発動 → L+1 を強制
  ・Creator が「もっと深く」と指示 → 即座に L+1"""
        sections.append(ad_section)
    # Step 8: ルーティングフィードバック収集の環境強制 (Aristos L3)
    if len(result["workflows"]) >= 2:
        fb_section = """【📊 Aristos Feedback】(WF 完了後に実行)
  以下を実行してルーティング品質を記録せよ:
  ```python
  from aristos.route_feedback import log_from_dispatch
  log_from_dispatch(dispatch_result, actual_time_min=X, had_errors=False)
  ```
  → フィードバックは PT 最適化 (L3 GA) の学習データになる"""
        sections.append(fb_section)

        # route_context を result に付加
        result["route_context"] = {
            "source": result["workflows"][0].lstrip("/"),
            "target": result["workflows"][-1].lstrip("/"),
            "route": [w.lstrip("/") for w in result["workflows"]],
            "depth_level": depth_level,
            "wf_count": len(result["workflows"]),
        }

    # P3: θ12.1d tape 記録義務の環境強制 — 直接実行ルートのみ
    if depth_level < 3:
        wf_args = " ".join(result.get("workflows", []))
        depth_str = f"L{depth_level}" if depth_level >= 0 else "L2"
        tape_section = f"""📼 【tape 記録義務 — θ12.1d】(WF 完了後に実行)
  直接実行 (hermeneus_run 非経由) のため tape 記録が必要:
  ```
  python3 80_運用｜Ops/record_wf_trace.py --wf {wf_args} --depth {depth_str}
  ```
  → 記録忘れ = invisible な遷移 = Q-series 分析の計測バイアス"""
        sections.append(tape_section)

    # P1: θ12.1 環境強制 — execute 呼び出しの強制指示
    sections.append(f"""⚠️⚠️⚠️ 【次のステップ — θ12.1 必須】⚠️⚠️⚠️
  このディスパッチ結果を受け取ったら、次に必ず
  hermeneus_execute を呼び出すこと。

  手書きで「実行結果」を生成してはならない (BRD-B11 違反)。
  → execute 完了後に Creator に報告すること。""")

    sections.append("→ これで進めてよいですか？")

    tmpl = "\n".join(sections)
    result["plan_template"] = tmpl

    return result


# PURPOSE: CLI エントリポイント
def main():
    """CLI エントリポイント"""
    if len(sys.argv) < 2:
        print("Usage: python hermeneus/src/dispatch.py '<CCL式>'")
        print("Example: python hermeneus/src/dispatch.py '/dia+~/noe'")
        print("Example: python hermeneus/src/dispatch.py '(/dia+~/noe)~/pan+'")
        sys.exit(1)

    ccl_expr = sys.argv[1]

    print(f"{'='*60}")
    print(f"  Hermēneus CCL Dispatch")
    print(f"  入力: {ccl_expr}")
    print(f"{'='*60}")
    print()

    # 循環インポート回避: dispatch() 内でパーサーを遅延インポート
    result = dispatch(ccl_expr)

    if not result["success"]:
        print(f"❌ Parse Error: {result['error']}")
        print()
        print("パーサー拡張が必要か、式の修正が必要です。")
        print("Creator に報告してください。")
        sys.exit(1)

    print("✅ パース成功")
    print()
    print("── AST 構造 ──────────────────────────────")
    print(result["tree"])
    print()
    print(f"── 関連 WF: {', '.join(result['workflows'])} ──")
    print()

    # WF 定義ファイルパス
    if result["wf_paths"]:
        print("── WF 定義ファイル (view_file で開け) ────")
        for wf_id, path in result["wf_paths"].items():
            print(f"  {wf_id} → {path}")
        print()

    print("── 実行計画テンプレート ──────────────────")
    print(result["plan_template"])
    print()
    print("─" * 60)
    print("↑ この出力を基に AST 順序で WF を実行せよ。")


if __name__ == "__main__":
    main()
