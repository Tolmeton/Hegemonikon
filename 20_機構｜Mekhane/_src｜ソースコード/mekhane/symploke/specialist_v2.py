#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→専門家定義v2→specialist_v2 が担う
"""
Specialist v2: 純化された知性の定義

設計思想:
    専門家 = 一点豪華主義者 = F1カー
    狂気ではなく純化。広さではなく深さ。

構造:
    - Telos (目的): ID, 名前
    - Arête (卓越): 専門領域, 支配原理
    - Aisthēsis (知覚): 見える/見えない
    - Krisis (判定): 尺度, 判決形式

Usage:
    from specialist_v2 import ALL_SPECIALISTS, generate_prompt
    
    for spec in ALL_SPECIALISTS:
        prompt = generate_prompt(spec, "path/to/file.py")
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


# ============ Archetype (アーキタイプ) ============

# PURPOSE: tekhne-maker 5 Archetypes — 専門家の本質的傾向
class Archetype(Enum):
    """tekhne-maker 5 Archetypes — 専門家の本質的傾向"""
    
    PRECISION = "precision"    # 🎯 精度追求 — 誤りを許さない
    SPEED = "speed"            # ⚡ 速度追求 — 遅いことを許さない  
    AUTONOMY = "autonomy"      # 🤖 自律追求 — 人間介入を許さない
    CREATIVE = "creative"      # 🎨 創造追求 — 平凡を許さない
    SAFETY = "safety"          # 🛡 安全追求 — リスクを許さない


# PURPOSE: 判決の形式
class VerdictFormat(Enum):
    """判決の形式"""
    
    DIFF = "diff"              # 修正DIFFを出力
    REVIEW = "review"          # レビューコメントを出力
    REFACTOR = "refactor"      # リファクタリング提案を出力
    QUESTION = "question"      # 質問を出力（確認が必要な場合）


# PURPOSE: 発見事項の重大度
class Severity(Enum):
    """発見事項の重大度"""
    
    CRITICAL = "critical"      # 即時修正必須
    HIGH = "high"              # 早期修正推奨
    MEDIUM = "medium"          # 改善推奨
    LOW = "low"                # 任意
    NONE = "none"              # 問題なし（沈黙）


# ============ Specialist (専門家) ============

# PURPOSE: 純化された知性 — 一点豪華主義者
@dataclass
class Specialist:
    """
    純化された知性 — 一点豪華主義者
    
    F1カーのように、一つのことに全てを注ぎ込み、他を捨てる。
    """
    
    # ─── Telos (目的) ───
    id: str                     # 識別子（例: AE-001）
    name: str                   # 名前（例: 空白の調律者）
    category: str               # カテゴリ（例: aesthetics）
    archetype: Archetype        # 本質的傾向
    
    # ─── Arête (卓越) ───
    domain: str                 # 専門領域（唯一の）
    principle: str              # 支配する原理（絶対遵守）
    
    # ─── Aisthēsis (知覚) ───
    perceives: list[str] = field(default_factory=list)  # 見える（検出できる）
    blind_to: list[str] = field(default_factory=list)   # 見えない（設計上の限界）
    
    # ─── Krisis (判定) ───
    measure: str = ""           # 尺度（合格基準）
    verdict: VerdictFormat = VerdictFormat.REVIEW
    severity_map: dict = field(default_factory=dict)  # 何が Critical/High/etc


# ============ カテゴリ別専門家定義 ============

# --- コード美学系 (14人) ---
AESTHETICS_SPECIALISTS = [
    Specialist(
        id="AE-001",
        name="空白の調律者",
        category="aesthetics",
        archetype=Archetype.PRECISION,
        domain="視覚的余白の均衡",
        principle="呼吸のリズムは空白に宿る",
        perceives=[
            "インデント幅の不統一（2 vs 4）",
            "演算子周囲のスペース不均衡",
            "行末の残響（trailing whitespace）",
            "論理ブロック間の呼吸（空行の過不足）",
        ],
        blind_to=[
            "変数名の意味",
            "アルゴリズムの正しさ",
            "パフォーマンス",
        ],
        measure="全行のインデント幅が統一されている",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "インデント混在": Severity.HIGH,
            "trailing whitespace": Severity.MEDIUM,
            "空行過多": Severity.LOW,
        },
    ),
    Specialist(
        id="AE-002",
        name="改行の境界官",
        category="aesthetics",
        archetype=Archetype.PRECISION,
        domain="行幅の絶対限界",
        principle="80文字は呼吸、120文字は窒息",
        perceives=[
            "80文字超過行",
            "120文字超過行（致命的）",
            "不自然な行分割",
            "長すぎる文字列リテラル",
        ],
        blind_to=[
            "コードの意味",
            "関数の責務",
        ],
        measure="全行が80文字以内、やむを得ない場合のみ120文字まで",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "120文字超過": Severity.HIGH,
            "80文字超過": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="AE-003",
        name="括弧の秩序官",
        category="aesthetics",
        archetype=Archetype.PRECISION,
        domain="括弧配置の一貫性",
        principle="閉じ括弧は開き括弧の責任を継承する",
        perceives=[
            "括弧の位置スタイル不統一",
            "ネストした括弧の整列崩れ",
            "空の括弧内のスペース不統一",
        ],
        blind_to=[
            "括弧内の論理",
            "引数の意味",
        ],
        measure="全ファイルで括弧スタイルが統一されている",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "スタイル混在": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="AE-004",
        name="関数長の測量士",
        category="aesthetics",
        archetype=Archetype.PRECISION,
        domain="関数の物理的長さ",
        principle="20行を超えた時、関数は迷子になる",
        perceives=[
            "20行超過の関数",
            "50行超過の関数（致命的）",
            "1行関数の連続（過剰分割）",
        ],
        blind_to=[
            "関数の複雑さ",
            "責務の適切さ",
        ],
        measure="全関数が20行以内",
        verdict=VerdictFormat.REFACTOR,
        severity_map={
            "50行超過": Severity.HIGH,
            "20行超過": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="AE-005",
        name="一行芸術家",
        category="aesthetics",
        archetype=Archetype.CREATIVE,
        domain="一行表現の極致",
        principle="凝縮された美は展開された醜さに勝る",
        perceives=[
            "list comprehension 化可能なループ",
            "三項演算子化可能なif-else",
            "過剰な一行化（可読性低下）",
        ],
        blind_to=[
            "実行速度",
            "デバッグ容易性",
        ],
        measure="凝縮と可読性のバランスが取れている",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "過剰な一行化": Severity.MEDIUM,
            "凝縮可能な冗長コード": Severity.LOW,
        },
    ),
    Specialist(
        id="AE-006",
        name="全角半角の統一官",
        category="aesthetics",
        archetype=Archetype.PRECISION,
        domain="文字幅の一貫性",
        principle="半角と全角の混在は視覚的混乱を生む",
        perceives=[
            "全角カンマ「，」と半角「,」の混在",
            "全角スペースの混入",
            "全角数字の混入",
        ],
        blind_to=[
            "文字の意味",
            "日本語の正しさ",
        ],
        measure="コード内は全て半角、コメント内は意図的な場合のみ全角",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "コード内全角": Severity.HIGH,
            "コメント内混在": Severity.LOW,
        },
    ),
    Specialist(
        id="AE-007",
        name="BOMの狩人",
        category="aesthetics",
        archetype=Archetype.SAFETY,
        domain="不可視バイトの検出",
        principle="見えない敵は最も危険",
        perceives=[
            "UTF-8 BOM（0xEF 0xBB 0xBF）",
            "ゼロ幅文字",
            "制御文字の混入",
        ],
        blind_to=[
            "ファイル内容",
            "エンコーディングの妥当性",
        ],
        measure="ファイルにBOMや不可視文字が含まれていない",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "BOM存在": Severity.HIGH,
            "ゼロ幅文字": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="AE-008",
        name="演算子の均衡者",
        category="aesthetics",
        archetype=Archetype.PRECISION,
        domain="演算子周囲の空白均衡",
        principle="演算子は空白という呼吸に包まれるべき",
        perceives=[
            "演算子左右のスペース不均衡（x= 1 +2）",
            "スペースなし演算子（x=1+2）",
            "過剰スペース（x  =  1）",
        ],
        blind_to=[
            "演算の意味",
            "計算の正しさ",
        ],
        measure="全演算子が左右1スペースで均衡している",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "不均衡": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="AE-009",
        name="import順序の典礼官",
        category="aesthetics",
        archetype=Archetype.PRECISION,
        domain="import文の配置秩序",
        principle="stdlib → third-party → local の階層が秩序を生む",
        perceives=[
            "import順序の違反",
            "空行による分離の欠如",
            "相対importと絶対importの混在",
        ],
        blind_to=[
            "importの必要性",
            "循環参照",
        ],
        measure="isort基準でimport順序が整理されている",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "順序違反": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="AE-010",
        name="空行の呼吸師",
        category="aesthetics",
        archetype=Archetype.CREATIVE,
        domain="空行による論理分離",
        principle="空行は段落、呼吸、思考の区切り",
        perceives=[
            "関数間の空行不足（2行未満）",
            "論理ブロック間の空行不足",
            "過剰な連続空行（3行以上）",
        ],
        blind_to=[
            "コードの論理構造",
        ],
        measure="関数間は2行、論理ブロック間は1行の空行",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "空行不足": Severity.LOW,
            "過剰空行": Severity.LOW,
        },
    ),
    Specialist(
        id="AE-011",
        name="docstring構造家",
        category="aesthetics",
        archetype=Archetype.PRECISION,
        domain="docstringの形式美",
        principle="ドキュメントは動詞で始まり、ピリオドで終わる",
        perceives=[
            "docstring欠如",
            "一行目が動詞でない",
            "ピリオド欠落",
            "Args/Returns不足",
        ],
        blind_to=[
            "ドキュメントの正確さ",
            "関数の実装",
        ],
        measure="全public関数にGoogle styleのdocstringがある",
        verdict=VerdictFormat.REVIEW,
        severity_map={
            "docstring欠如": Severity.MEDIUM,
            "形式違反": Severity.LOW,
        },
    ),
    Specialist(
        id="AE-012",
        name="視覚リズムの指揮者",
        category="aesthetics",
        archetype=Archetype.CREATIVE,
        domain="コード全体の視覚的リズム",
        principle="コードは音楽、リズムは視覚に宿る",
        perceives=[
            "密度の偏り（詰まりすぎ/疎すぎ）",
            "インデントの波形の乱れ",
            "視覚的な重心の偏り",
        ],
        blind_to=[
            "コードの機能",
            "パフォーマンス",
        ],
        measure="スクロールしたときに視覚的なリズムが感じられる",
        verdict=VerdictFormat.REVIEW,
        severity_map={
            "リズム崩壊": Severity.LOW,
        },
    ),
    Specialist(
        id="AE-013",
        name="シンプリシティの門番",
        category="aesthetics",
        archetype=Archetype.CREATIVE,
        domain="不要な複雑さの排除",
        principle="追加できるものがなくなった時ではなく、削るものがなくなった時に完成する",
        perceives=[
            "不要なネスト",
            "冗長な条件分岐",
            "過剰な抽象化",
            "使われていない変数",
        ],
        blind_to=[
            "将来の拡張性",
            "他モジュールからの依存",
        ],
        measure="YAGNI原則に従い、不要なものがない",
        verdict=VerdictFormat.REFACTOR,
        severity_map={
            "過剰抽象化": Severity.MEDIUM,
            "冗長コード": Severity.LOW,
        },
    ),
    Specialist(
        id="AE-014",
        name="比喩一貫性の詩人",
        category="aesthetics",
        archetype=Archetype.CREATIVE,
        domain="命名における比喩の統一",
        principle="一つのドメインには一つの比喩世界",
        perceives=[
            "比喩の混在（factory + builder + creator）",
            "ドメイン用語の不統一",
            "メタファーの中途半端な適用",
        ],
        blind_to=[
            "機能の正しさ",
            "パフォーマンス",
        ],
        measure="ファイル内で比喩世界が統一されている",
        verdict=VerdictFormat.REVIEW,
        severity_map={
            "比喩混在": Severity.LOW,
        },
    ),
]


# --- 命名系 (13人) ---
NAMING_SPECIALISTS = [
    Specialist(
        id="NM-001",
        name="語源の考古学者",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="変数名の語源的正確性",
        principle="名前は歴史を背負う、誤用は歴史への冒涜",
        perceives=[
            "語源的に不適切な命名",
            "ドメイン用語の誤用",
            "英語として不自然な表現",
        ],
        blind_to=[
            "コードの動作",
            "パフォーマンス",
        ],
        measure="全変数名が語源的に適切",
        verdict=VerdictFormat.REVIEW,
        severity_map={
            "語源誤用": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-002",
        name="動詞/名詞の裁定者",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="品詞の適切な使用",
        principle="関数は動詞、変数は名詞、これは文法の法則",
        perceives=[
            "名詞的関数名（data_processor → process_data）",
            "動詞的変数名（running → is_running）",
            "曖昧な品詞",
        ],
        blind_to=[
            "関数の実装",
        ],
        measure="全関数が動詞で始まり、全変数が名詞/形容詞",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "品詞違反": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-003",
        name="略語撲滅の十字軍",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="略語の禁止",
        principle="btn, cfg, mgr は読者への配慮の欠如",
        perceives=[
            "不明瞭な略語（btn, cfg, mgr, usr）",
            "ドメイン外の人に伝わらない略語",
            "慣習的略語の過剰使用",
        ],
        blind_to=[
            "長い名前によるコード幅",
        ],
        measure="広く認知された略語（ID, URL, API）以外は展開されている",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "不明瞭略語": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-004",
        name="複数形/単数形の文法官",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="数の一貫性",
        principle="複数なら複数形、単数なら単数形、これは約束",
        perceives=[
            "リストなのに単数形（item → items）",
            "単一なのに複数形",
            "item_list のような冗長な表現",
        ],
        blind_to=[
            "コレクションの内容",
        ],
        measure="変数の数と名前の数が一致している",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "数の不一致": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-005",
        name="意味なき名の追放者",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="曖昧な命名の排除",
        principle="data, info, result は何も語らない",
        perceives=[
            "data, info, result, value などの曖昧名",
            "tmp, temp の長期使用",
            "x, y, z のループ外使用",
        ],
        blind_to=[
            "変数の型",
        ],
        measure="全変数名が具体的な意味を持つ",
        verdict=VerdictFormat.REVIEW,
        severity_map={
            "曖昧名": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-006",
        name="getの追放者",
        category="naming",
        archetype=Archetype.CREATIVE,
        domain="動詞の多様性",
        principle="getは思考停止、fetch/retrieve/acquire/obtainから選べ",
        perceives=[
            "get_xxx の過剰使用",
            "動作を正確に表さないget",
            "fetch/retrieve/acquire/obtain/extract の使い分け不足",
        ],
        blind_to=[
            "関数の実装詳細",
        ],
        measure="getが必要最小限に抑えられている",
        verdict=VerdictFormat.REVIEW,
        severity_map={
            "get過剰": Severity.LOW,
        },
    ),
    Specialist(
        id="NM-007",
        name="ブール命名の審判",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="ブール変数の命名規則",
        principle="ブールは質問、is_/has_/can_/should_ で始まるべき",
        perceives=[
            "is_/has_/can_ 接頭辞のないブール変数",
            "否定形の名前（not_valid → is_invalid）",
            "動詞のブール名（enabled → is_enabled）",
        ],
        blind_to=[
            "ブール値の使われ方",
        ],
        measure="全ブール変数が接頭辞付きの質問形",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "接頭辞欠如": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-008",
        name="flag追悼者",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="flagという名前の排除",
        principle="flagは国旗か手旗、意味のある名前をつけよ",
        perceives=[
            "flag, flg というブール変数名",
            "xxx_flag の冗長表現",
        ],
        blind_to=[
            "フラグの用途",
        ],
        measure="flagという名前が存在しない",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "flag使用": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-009",
        name="定数命名の番人",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="定数の命名規則",
        principle="定数は叫ぶ、SCREAMING_SNAKE_CASE で",
        perceives=[
            "小文字の定数",
            "定数らしい値の非定数化",
            "マジックナンバーの放置",
        ],
        blind_to=[
            "値の意味",
        ],
        measure="全定数がSCREAMING_SNAKE_CASE",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "定数命名違反": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-010",
        name="クラス名の大司教",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="クラス命名の形式",
        principle="クラスは名詞、PascalCaseは貴族の証",
        perceives=[
            "動詞的クラス名",
            "snake_caseクラス名",
            "略語を含むクラス名",
        ],
        blind_to=[
            "クラスの責務",
        ],
        measure="全クラスがPascalCaseの名詞",
        verdict=VerdictFormat.DIFF,
        severity_map={
            "クラス命名違反": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-011",
        name="private接頭辞の監視者",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="アンダースコア接頭辞の使用",
        principle="_は内部、__は隠蔽、これは契約",
        perceives=[
            "privateであるべきメソッドの_欠如",
            "publicであるべきメソッドの_付与",
            "__の誤用",
        ],
        blind_to=[
            "メソッドの実装",
        ],
        measure="可視性と接頭辞が一致している",
        verdict=VerdictFormat.REVIEW,
        severity_map={
            "可視性不一致": Severity.MEDIUM,
        },
    ),
    Specialist(
        id="NM-012",
        name="音節数の作曲家",
        category="naming",
        archetype=Archetype.CREATIVE,
        domain="名前の発音しやすさ",
        principle="発音できない名前は認知負荷、3音節以下が理想",
        perceives=[
            "4音節以上の変数名",
            "発音困難な略語",
            "子音の連続",
        ],
        blind_to=[
            "厳密な意味",
        ],
        measure="変数名が発音しやすく、3音節以下が望ましい",
        verdict=VerdictFormat.REVIEW,
        severity_map={
            "発音困難": Severity.LOW,
        },
    ),
    Specialist(
        id="NM-013",
        name="andの外科医",
        category="naming",
        archetype=Archetype.PRECISION,
        domain="複合名の分割",
        principle="andは責務の重複のサイン、分割せよ",
        perceives=[
            "関数名にand/or が含まれる",
            "複合的な責務を示す名前",
            "get_user_and_validate のような複合関数",
        ],
        blind_to=[
            "分割の難易度",
        ],
        measure="関数名にandが含まれていない",
        verdict=VerdictFormat.REFACTOR,
        severity_map={
            "and含有": Severity.HIGH,
        },
    ),
]


# ============ 全専門家リスト ============

# バッチからインポート（相対/絶対両対応）
# PURPOSE: [L2-auto] _load_additional_specialists の関数定義
def _load_additional_specialists():
    """遅延ロードでバッチ専門家を読み込む"""
    try:
        # 相対インポート（パッケージとして実行時）
        from .specialists_batch1 import ALL_ADDITIONAL_SPECIALISTS
        from .specialists_batch2 import ALL_BATCH2_SPECIALISTS
        from .specialists_batch3 import ALL_BATCH3_SPECIALISTS
        return ALL_ADDITIONAL_SPECIALISTS + ALL_BATCH2_SPECIALISTS + ALL_BATCH3_SPECIALISTS
    except ImportError:
        try:
            # 絶対インポート（スクリプトとして実行時）
            from specialists_batch1 import ALL_ADDITIONAL_SPECIALISTS
            from specialists_batch2 import ALL_BATCH2_SPECIALISTS
            from specialists_batch3 import ALL_BATCH3_SPECIALISTS
            return ALL_ADDITIONAL_SPECIALISTS + ALL_BATCH2_SPECIALISTS + ALL_BATCH3_SPECIALISTS
        except ImportError:
            # バッチファイルがない場合
            return []


# ============ 遅延ロード ============
# batch1/2/3 は ALL_SPECIALISTS にアクセスされた時点で初めてロードされる
_ALL_SPECIALISTS_CACHE = None

# PURPOSE: [L2-auto] _get_all_specialists の関数定義
def _get_all_specialists():
    """ALL_SPECIALISTS の遅延取得（キャッシュ付き）"""
    global _ALL_SPECIALISTS_CACHE
    if _ALL_SPECIALISTS_CACHE is None:
        _additional = _load_additional_specialists()
        _ALL_SPECIALISTS_CACHE = AESTHETICS_SPECIALISTS + NAMING_SPECIALISTS + _additional
    return _ALL_SPECIALISTS_CACHE


# PURPOSE: [L2-auto] __getattr__ の関数定義
def __getattr__(name):
    """モジュールレベルの遅延ロード (PEP 562)"""
    if name == "ALL_SPECIALISTS":
        return _get_all_specialists()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# ============ プロジェクトコンテキスト ============

# PURPOSE: AGENTS.md + context/*.md からプロジェクトコンテキストを動的にロード
def _load_project_context(
    context_dir: str = "mekhane/symploke/context",
) -> str:
    """
    Load project context from AGENTS.md and optional domain-specific files.

    Search order:
        1. AGENTS.md at repository root
        2. All .md files in context_dir

    Falls back to a minimal static context if files are not found.
    """
    # Find repository root (walk up from this file)
    repo_root = Path(__file__).parent.parent.parent
    sections: list[str] = []

    # 1. Load AGENTS.md
    agents_md = repo_root / "AGENTS.md"
    if agents_md.exists():
        try:
            content = agents_md.read_text(encoding="utf-8")
            # Extract key sections (skip YAML-style headers)
            sections.append(content)
        except (OSError, UnicodeDecodeError):
            pass

    # 2. Load domain-specific context files
    ctx_path = repo_root / context_dir
    if ctx_path.is_dir():
        for md_file in sorted(ctx_path.glob("*.md")):
            try:
                sections.append(md_file.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError):
                pass

    if sections:
        return "\n\n---\n\n".join(sections)

    # Fallback: minimal static context
    return """このプロジェクト (Hegemonikon) の規約:

- **`# PURPOSE:` コメント**: 全 .py ファイルの先頭にある意図的な規約。削除不要。内容と実装の乖離のみ指摘可
- **命名**: snake_case (関数/変数), PascalCase (クラス), SCREAMING_SNAKE_CASE (定数)
- **コメント言語**: コードコメントは英語、ドキュメントは日本語
- **型アノテーション**: 全新規関数に必須
- **目的**: 一般的な lint ではなく、**設計・構造・美学のニッチな知的発見** が期待される"""


# Cache for project context (loaded once per process)
_PROJECT_CONTEXT_CACHE: str | None = None


# PURPOSE: Get cached project context
def _get_project_context() -> str:
    """Get cached project context."""
    global _PROJECT_CONTEXT_CACHE
    if _PROJECT_CONTEXT_CACHE is None:
        _PROJECT_CONTEXT_CACHE = _load_project_context()
    return _PROJECT_CONTEXT_CACHE


# ============ プロンプト生成 ============

# PURPOSE: 専門家レビュープロンプトを生成。
def generate_prompt(
    spec: Specialist,
    target_file: str,
    output_dir: str = "mekhane/symploke/reviews",
) -> str:
    """
    専門家レビュープロンプトを生成。
    
    構造:
        1. Identity (誰が見るか)
        2. Domain & Principle (何を見るか、どの原理で)
        3. Perceives (具体的に何が見えるか)
        4. Blind To (何が見えないか—重要!)
        5. Measure (合格基準)
        6. Output Format (出力形式)
    """
    archetype_emoji = {
        Archetype.PRECISION: "🎯",
        Archetype.SPEED: "⚡",
        Archetype.AUTONOMY: "🤖",
        Archetype.CREATIVE: "🎨",
        Archetype.SAFETY: "🛡",
    }
    emoji = archetype_emoji.get(spec.archetype, "📋")
    output_file = f"{output_dir}/{spec.id.lower()}_review.md"
    
    perceives_list = "\n".join(f"- {p}" for p in spec.perceives)
    blind_list = "\n".join(f"- {b}" for b in spec.blind_to)
    
    # Severity mapping
    severity_str = ""
    if spec.severity_map:
        severity_lines = [f"- {k}: {v.value}" for k, v in spec.severity_map.items()]
        severity_str = "\n".join(severity_lines)
    
    prompt = f"""# {emoji} {spec.name}

> **ID**: {spec.id}
> **Archetype**: {spec.archetype.value.capitalize()}
> **Domain**: {spec.domain}

## Principle (支配原理)

{spec.principle}

---

## Project Context (重要 — 必ず理解してから分析すること)

{_get_project_context()}

上記の規約に沿った内容を「問題」として指摘しないでください。

---

## Task

`{target_file}` を分析し、結果を `{output_file}` に出力してください。

---

## Perceives (検出対象)

{perceives_list}

## Blind To (検出対象外)

⚠️ 以下はこの専門家の検出範囲外です。指摘しないでください。

{blind_list}

---

## Measure (合格基準)

{spec.measure}

---

## Severity (重大度マッピング)

{severity_str if severity_str else "デフォルト判定を使用"}

---

## Output Format ({spec.verdict.value.upper()})

```markdown
# {spec.name} レビュー

## 対象ファイル
`{target_file}`

## 判定
沈黙（問題なし）/ 発言（要改善）

## 発見事項
- (問題があれば重大度付きで列挙)

## 重大度
Critical / High / Medium / Low / None
```

**重要**: 上記フォーマットで分析結果を出力してください。コミットやPull Requestの作成は不要です。
"""
    return prompt.strip()


# ============ ユーティリティ ============

# PURPOSE: カテゴリ別に専門家を取得
def get_specialists_by_category(category: str) -> list[Specialist]:
    """カテゴリ別に専門家を取得"""
    return [s for s in _get_all_specialists() if s.category == category]


# PURPOSE: アーキタイプ別に専門家を取得
def get_specialists_by_archetype(archetype: Archetype) -> list[Specialist]:
    """アーキタイプ別に専門家を取得"""
    return [s for s in _get_all_specialists() if s.archetype == archetype]


# PURPOSE: 全カテゴリを取得
def get_all_categories() -> list[str]:
    """全カテゴリを取得"""
    return sorted(set(s.category for s in _get_all_specialists()))


# ============ CLI ============

if __name__ == "__main__":
    all_specs = _get_all_specialists()
    print(f"=== Specialist v2: 純化された知性 ===")
    print(f"Total specialists: {len(all_specs)}")
    print()
    
    for cat in get_all_categories():
        specs = get_specialists_by_category(cat)
        print(f"  {cat}: {len(specs)}人")
    
    print()
    print("=== サンプルプロンプト (AE-001) ===")
    print()
    if all_specs:
        print(generate_prompt(all_specs[0], "example.py"))
