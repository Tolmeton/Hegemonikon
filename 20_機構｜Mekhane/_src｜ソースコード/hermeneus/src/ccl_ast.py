# PROOF: [L2/インフラ] <- hermeneus/src/ccl_ast.py CCL AST 定義
"""
Hermēneus AST (Abstract Syntax Tree) Nodes

CCL 式を表現する抽象構文木のノード定義。
lmql_translator.py PoC から正式版へリファクタ。

Origin: 2026-01-31 CCL Execution Guarantee Architecture
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Any, Union


# =============================================================================
# Operator Types
# =============================================================================

# PURPOSE: [L2-auto] CCL 演算子タイプ (v7.6)
class OpType(Enum):
    """CCL 演算子タイプ (v7.6)"""
    # Tier 1: 単項演算子 (強度・次元)
    DEEPEN = auto()      # + 深化
    CONDENSE = auto()    # - 縮約
    ASCEND = auto()      # ^ 上昇 (メタ化)
    DESCEND = auto()     # √ 下降 (アクション)
    QUERY = auto()       # ? 質問
    INVERT = auto()      # \ 位相反転
    DIFF = auto()        # ' 微分 (変化率)
    EXPAND = auto()      # ! 全展開
    # FEP 演算子 (前置)
    PARTIAL_DIFF = auto()  # ∂ 偏微分 (特定座標の変化率)
    INTEGRAL = auto()      # ∫ 積分 (履歴統合)
    SUMMATION = auto()     # Σ 総和 (結果集約)
    
    # Tier 2: 二項演算子 (合成)
    FUSE = auto()        # * 融合 (内積)
    OUTER = auto()       # % 外積 (テンソル展開)
    FUSE_OUTER = auto()  # *% 内積+外積
    OSC = auto()         # ~ 振動
    SEQ = auto()         # _ シーケンス
    COLIMIT = auto()     # \ Colimit (展開・発散)
    REVERSE_ARROW = auto()   # << 逆射 (pullback)
    MORPHIC_FUSE = auto()    # >* 射的融合 (Lax Actegory)
    OPLAX_FUSE = auto()      # <* 逆射融合 (Oplax) — v7.7
    DIRECTED_FUSE = auto()   # *> 方向付き融合 — v7.7
    PUSHFORWARD_TENSOR = auto()  # >% 射的展開 (Pushforward) — v7.7
    
    # Tier 3: 制御演算子
    CONVERGE = auto()    # >> or lim 収束
    PIPE = auto()        # &> 分散パイプライン (v7.6: 旧 |>)
    PARALLEL = auto()    # && 分散並列 (v7.6: 旧 ||)
    
    # Tier 4: 随伴演算子 (v7.6 新設)
    ADJUNCTION = auto()     # || 随伴宣言 (F ⊣ G)
    RIGHT_ADJOINT = auto()  # |> 右随伴取得 (単項後置)
    LEFT_ADJOINT = auto()   # <| 左随伴取得 (単項後置)


# =============================================================================
# AST Nodes: Basic
# =============================================================================

# PURPOSE: [L2-auto] 変数参照: $var, $var.field, ¥, #, ¥[name], #[name]
@dataclass
class Variable:
    """変数参照: $var, $var.field, ¥, #, ¥[name], #[name]
    
    例: $insight, $result.decision, ¥, #[computed]
    """
    name: str                            # 変数名 ($, ¥, # を含む)
    projection: Optional[str] = None     # 射影されるフィールド名 (例: "insight")

# PURPOSE: [L2-auto] ワークフローノード
@dataclass
class Workflow:
    """ワークフローノード
    
    例: /noe+, /bou-, /s+a1:2, /noe.h, /bou.x
    """
    id: str                              # ワークフロー ID (e.g., "noe", "bou")
    operators: List[OpType] = field(default_factory=list)  # 適用された演算子
    modifiers: Dict[str, Any] = field(default_factory=dict)  # 修飾子 (e.g., {"a1": 2})
    mode: Optional[str] = None           # --mode 指定 (e.g., "nous")
    selector: Optional[str] = None       # [target] セレクタ
    relation: Optional[str] = None       # .d/.h/.x 関係サフィックス (v7.2)
    projection: Optional[str] = None     # 即時射影 (eager projection) 例: "insight" (v7.7)


# PURPOSE: [L2-auto] 前動詞（中動態）ノード — H-series
@dataclass
class PreVerb:
    """前動詞（中動態）ノード — H-series
    
    例: [th], [ph], [ho], [th] >> /noe
    
    Poiesis 動詞 (/verb) = doing（能動態）に対し、
    H-series 前動詞 ([略記]) = being（中動態）。
    φ_SA (感覚∩行為の反射弧) × 6修飾座標 × 2極 から生まれる12の状態。
    """
    id: str           # 前動詞 ID (e.g., "th", "ph", "ho")
    full_name: str = ""  # 正式名 (e.g., "Thambos")。パーサーが自動解決


# PURPOSE: [L2-auto] 条件ノード
@dataclass
class Condition:
    """条件ノード
    
    例: V[] < 0.3, E[] > 0.5
    """
    var: str      # 変数名 (e.g., "V[]", "E[]")
    op: str       # 比較演算子 (e.g., "<", ">", "=", "<=", ">=")
    value: float  # 閾値


# PURPOSE: [L2-auto] マクロ参照ノード
@dataclass
class MacroRef:
    """マクロ参照ノード
    
    例: @think, @tak, @dig
    """
    name: str                            # マクロ名
    args: List[Any] = field(default_factory=list)  # 引数


# =============================================================================
# AST Nodes: Compound
# =============================================================================

# PURPOSE: [L2-auto] 収束ループ: A ~> cond または lim[cond]{A}
@dataclass
class ConvergenceLoop:
    """収束ループ: A ~> cond または lim[cond]{A}
    
    例: /noe+ ~> V[] < 0.3
    """
    body: Any                            # Workflow or Expression
    condition: Condition                 # 収束条件
    max_iterations: int = 5              # 最大反復回数


# PURPOSE: [L2-auto] シーケンス: A _ B _ C
@dataclass
class Sequence:
    """シーケンス: A _ B _ C
    
    例: /boot _/bou _/ene
    """
    steps: List[Any] = field(default_factory=list)
    source_notation: Optional[str] = None  # .d/.h/.x 展開元の記法 (例: "/noe.d")


# PURPOSE: [L2-auto] 融合: A * B, A % B (外積), A *% B (内積+外積)
@dataclass
class Fusion:
    """融合: A * B, A % B (外積), A *% B (内積+外積)
    
    例: /noe * /dia, /noe % /dia, /noe+*%/dia+
    
    Markov圏対応:
        * = inner product (⟨−,−⟩)
        % = outer product (⊗ tensor expansion, copy morphism)
        *% = inner+outer product (収束+展開の同時操作)
    """
    left: Any
    right: Any
    meta_display: bool = False           # *^ のメタ表示フラグ
    outer_product: bool = False          # % の外積フラグ
    fuse_outer: bool = False             # *% の内積+外積フラグ


# PURPOSE: [L2-auto] 振動: A ~ B, A ~* B (収束), A ~! B (発散)
@dataclass
class Oscillation:
    """振動: A ~ B, A ~* B (収束), A ~! B (発散)
    
    例: /u+ ~ /noe!, /dia+~*/noe (収束振動)
    """
    left: Any
    right: Any
    convergent: bool = False              # ~* 収束振動
    divergent: bool = False               # ~! 発散振動
    max_iterations: int = 5               # 収束時の最大反復回数
    source_notation: Optional[str] = None  # .x 展開元の記法 (例: "/noe.x")


# PURPOSE: [L2-auto] Colimit 展開: \A
@dataclass
class ColimitExpansion:
    """Colimit 展開: \\A
    
    例: \\pan+ (pan の全派生展開)
    圏論的意味: Colimit = 余極限 = 全射影の合併
    """
    body: Any                              # 展開対象の WF/Expression
    operators: List[OpType] = field(default_factory=list)  # 追加演算子


# PURPOSE: [L2-auto] 射 (Morphism): A >> B, A << B, A >* B, A <* B, A *> B, A >% B
@dataclass
class Morphism:
    """射 (Morphism): 構造的変換
    
    >> = forward (f:A→B) — A が B に変わる (X-series 構造的変換)
    << = reverse/pullback (f*:B→A) — ゴールから原因を逆算
    >* = lax actegory (B⊳A) — A が B の視点で変容
    <* = oplax (v7.7) — A が B の構造を自身に取り込んで変容
    *> = directed_fusion (v7.7) — A の融合結果が B 方向に流れる
    >% = pushforward (v7.7) — A の射を B の全次元に展開
    
    圏論: >> は射 f:A→B、<< は pullback f*:B→A、>* は Lax Actegory
           <* は Oplax functor、*> は directed colimit + 射、>% は pushforward tensor
    
    指向性: 左辺が主語 (基点)。2文字演算子の読み規則 v7.7 準拠:
      1文字目 = 主語のアクション、2文字目 = 客語への効果
    """
    source: Any      # 左辺 (主語/基点)
    target: Any      # 右辺
    direction: str   # 'forward' | 'reverse' | 'lax' | 'oplax' | 'directed_fusion' | 'pushforward'


# PURPOSE: [L2-auto] 随伴宣言: A || B (v7.6 新設)
@dataclass
class Adjunction:
    """随伴宣言: A || B (v7.6)
    
    F ⊣ G (F は左随伴、G は右随伴) を宣言する。
    例: /noe || /zet = noe ⊣ zet
    
    単項後置の右随伴 (|>) / 左随伴 (<|) と連携:
      /noe|> → /zet (右随伴取得)
      /zet<| → /noe (左随伴取得)
    """
    left: Any   # 左随伴 (F)
    right: Any  # 右随伴 (G)


# PURPOSE: [L2-auto] 分散パイプライン: A &> B &> C (v7.6: 旧 |>)
@dataclass
class Pipeline:
    """分散パイプライン: A &> B &> C
    
    例: /noe+ &> /dia+ (前段の出力を次段の入力に)
    v7.6: 旧記号 |> → &> に移行。|> は随伴演算子に再割り当て。
    """
    steps: List[Any] = field(default_factory=list)


# PURPOSE: [L2-auto] 分散並列: A && B && C (v7.6: 旧 ||)
@dataclass
class Parallel:
    """分散並列: A && B && C
    
    例: /noe+ && /dia+ (同時並行で実行)
    v7.6: 旧記号 || → && に移行。|| は随伴宣言に再割り当て。
    """
    branches: List[Any] = field(default_factory=list)


# PURPOSE: [L2-auto] 末尾の開放状態: ... &> 
@dataclass
class OpenEnd:
    """末尾の開放状態 (次に結合可能であることの明示)
    
    例: /noe+ &> /bou- &> 
    """
    pass


# =============================================================================
# AST Nodes: CPL v2.0 Control Structures
# =============================================================================

# PURPOSE: [L2-auto] FOR ループ: F:[×N]{body} または F:[A,B,C]{body}
@dataclass
class ForLoop:
    """FOR ループ: F:[×N]{body} または F:[A,B,C]{body}
    
    例: F:[×3]{/dia}
    """
    iterations: Union[int, List[Any]]    # 反復回数 or 対象リスト
    body: Any


# PURPOSE: [L2-auto] IF 条件分岐: I:[cond]{then} E:{else}
@dataclass
class IfCondition:
    """IF 条件分岐: I:[cond]{then} E:{else}
    
    例: I:[V[] > 0.5]{/noe+} E:{/noe-}
    """
    condition: Condition
    then_branch: Any
    else_branch: Optional[Any] = None


# PURPOSE: [L2-auto] WHILE ループ: W:[cond]{body}
@dataclass
class WhileLoop:
    """WHILE ループ: W:[cond]{body}
    
    例: W:[E[] > 0.3]{/dia}
    """
    condition: Condition
    body: Any


# PURPOSE: [L2-auto] Lambda 関数: L:[x]{body}
@dataclass
class Lambda:
    """Lambda 関数: L:[x]{body}
    
    例: L:[wf]{wf+}
    """
    params: List[str]
    body: Any


# PURPOSE: [L2-auto] タグ付きブロック: V:{body}, C:{body}, R:{body}, M:{body}
@dataclass
class TaggedBlock:
    """タグ付きブロック: V:{body}, C:{body}, R:{body}, M:{body}
    
    CPL v2.0 意味タグ。制御フローではなく意図を示す。
    
    Tags:
        V = Validate (検証)
        C = Cycle (反復サイクル)
        R = Repeat (反復)
        M = Memorize (記憶・永続化)
    
    例: V:{/dia+}, C:{/dia+_/ene+}, M:{/dox-}
    """
    tag: str      # "V", "C", "R", "M"
    body: Any     # 内部の CCL 式


# =============================================================================
# AST Nodes: FEP 演算子
# =============================================================================

# PURPOSE: [L2-auto] 偏微分: ∂coord/verb — 特定座標の変化率のみ観測
@dataclass
class PartialDiff:
    """偏微分: ∂coord/verb

    例: ∂Pr/noe — Precision 座標の変化率のみ観測
    FEP: ∂f/∂x — 特定次元の prediction error 変化率
    """
    coordinate: str    # Dokimasia 座標名 (Va, Fu, Pr, Sc, Vl, Te)
    body: Any          # 対象の WF/Expression


# PURPOSE: [L2-auto] 積分: ∫/verb — 過去実行の履歴統合
@dataclass
class Integral:
    """積分: ∫/verb

    例: ∫/dox — 過去の信念の累積・経験統合
    FEP: ∫ε dt — 予測誤差の時間積分
    環境強制: mneme search で過去実行履歴を自動検索
    """
    body: Any          # 対象の WF/Expression


# PURPOSE: [L2-auto] 総和: Σ[items] — 複数結果の集約
@dataclass
class Summation:
    """総和: Σ[items] or Σ[items]{body}

    例: Σ[results] — 直前の分岐・ループ結果の集約
    FEP: Σ x_i — 複数の観測/結果の合計
    """
    items: str                   # 集約対象の識別子
    body: Optional[Any] = None   # 省略可能な対象式


# =============================================================================
# AST Node: Program (Root)
# =============================================================================

# PURPOSE: [L2-auto] CCL プログラム (ルートノード)
@dataclass
class Program:
    """CCL プログラム (ルートノード)"""
    expressions: List[Any] = field(default_factory=list)
    macros: Dict[str, Any] = field(default_factory=dict)  # let 定義


# PURPOSE: [L2-auto] マクロ定義: let @name = CCL 式
@dataclass
class LetBinding:
    """マクロ定義: let @name = CCL 式
    
    例: let @think = /noe+ _ /dia
    """
    name: str                            # マクロ名 (@ なし)
    body: Any                            # 束縛される CCL 式


# PURPOSE: [L2-auto] グループ修飾子: (expr)+ のように式全体に修飾子を適用
@dataclass
class Group:
    """グループ修飾子: (expr)op
    
    例: (/ske*/sag)+, (/noe_/dia)-
    
    意味論:
        (A*B)+ は「A と B の融合結果を深化する」。
        これは A+ * B+ (各要素を個別に深化してから融合) とは異なる操作。
        Group ノードは内部式全体に対する修飾子適用を表現する。
    """
    body: Any                            # 内部の式 (Fusion, Sequence 等)
    operators: List[OpType] = field(default_factory=list)  # 適用する修飾子


# PURPOSE: [L2-auto] 修飾子空間の Peras 演算 (.ax suffix)
@dataclass
class ModifierPeras:
    """修飾子空間の Peras — WF を修飾座標で全展開して対比する。
    
    構文:
        /noe.ax           → 6座標 × 2極 = 12パターンで全展開
        /noe.Va            → Va の両極対比 (2パターン)
        /noe.ax[Va,Fu]     → Va と Fu の部分展開 (4パターン)
        /noe.critical      → プリセット適用
    
    設計:
        `.` は WF の属性アクセスとして統一。
        1文字 (.d, .h, .x) = relation suffix (既存)
        2文字以上 (.ax, .Va, .critical) = modifier 操作 (新規)
    """
    base_wf: Any                         # 展開対象の WF (Workflow ノード)
    coordinates: List[str] = field(default_factory=list)  # 展開する座標 (空 = 全6座標)
    preset_name: str = ""                # プリセット名 (.critical など)
    operators: List[Any] = field(default_factory=list)     # 演算子 (+, -, etc.)


# =============================================================================
# AST Nodes: Lēthē (忘却制御)
# =============================================================================

# PURPOSE: [L2-auto] 忘却制御ブロック: @oblivion[θ=<float>]{CCL}
@dataclass
class OblivionBlock:
    """忘却制御ブロック: @oblivion[θ=<float>]{<CCL expression>}

    Lēthē Phase C: ∇Φ ≠ 0 (忘却勾配の非一様性) を CCL に注入する演算子。
    内部 CCL 式の >> 合成順序 (1-cell) と ~ 振動戦略 (2-cell) を
    忘却スコア φ に基づいて動的に制御する。

    核心命題:
        Think Anywhere は推論の忘却における非一様性 (∇Φ ≠ 0) を利用し、
        有限なスペクトル効率 ρ の非一様配分により局所的推論力を極大化する。

    構文:
        @oblivion[θ=0.3]{/noe+ >> /dia+ >> /ene+}
        → φ > 0.3 のステップを忘却 (スキップ/再配置)

    圏論的意味:
        0-cell (位置選択): LLM 内部 — 制御不能
        1-cell (経路選択): >> 合成順序の φ 依存フィルタリング
        2-cell (戦略選択): ~ 自然変換の φ 依存切替
    """
    theta: float                          # 忘却閾値 θ ∈ [0.0, 1.0]
    body: Any                             # 内部 CCL 式
    phi_scores: Dict[str, float] = field(default_factory=dict)  # 動詞→φ (LUT 注入)


# =============================================================================
# Type Aliases
# =============================================================================

ASTNode = Union[
    Workflow, PreVerb, Condition, MacroRef, Variable,
    ConvergenceLoop, Sequence, Fusion, Oscillation, ColimitExpansion,
    Adjunction, Pipeline, Parallel, Morphism, OpenEnd,
    ForLoop, IfCondition, WhileLoop, Lambda, TaggedBlock,
    LetBinding, ModifierPeras, Group, Program,
    PartialDiff, Integral, Summation,
    OblivionBlock,
]
