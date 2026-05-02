# PROOF: [L1/インフラ] <- A0→全パスの Single Source of Truth が必要→paths.py が担う
"""
Hegemonikón Path Registry — Single Source of Truth

全ディレクトリパスをここで一元管理する。
ハードコードされたパスをコードベースから排除するための基盤。

Usage:
    from mekhane.paths import INCOMING_DIR, SESSIONS_DIR, WORKFLOWS_DIR

Override:
    HGK_ROOT=/path/to/hegemonikon pytest  # テスト環境
"""
# PURPOSE: 全 Hegemonikón パスの一元管理

from pathlib import Path
import os

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# .env ロード — Single Point of Load
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_env_loaded = False


def ensure_env() -> None:
    """HGK_ROOT/.env を一度だけロードする (冪等)。
    
    paths.py のロード時に自動的に実行されるため、
    各モジュールで個別に呼ぶ必要はない。

    - .env が存在しない場合は何もしない
    - python-dotenv が未インストールの場合も何もしない
    - 既にロード済みなら即座に return (冪等)
    """
    global _env_loaded
    if _env_loaded:
        return
    try:
        from dotenv import load_dotenv
        env_file = _detect_root() / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        _env_loaded = True
    except ImportError:
        _env_loaded = True  # dotenv 未インストール — 再試行しない


def _detect_root() -> Path:
    """HGK_ROOT を自動検出する。

    優先順位:
    1. 環境変数 HGK_ROOT
    2. __file__ から上方探索 (mekhane/paths.py → _src → Mekhane → HGK_ROOT)
    3. フォールバック: ~/Sync/oikos/01_ヘゲモニコン｜Hegemonikon
    """
    # 1. 環境変数
    env = os.environ.get("HGK_ROOT")
    if env:
        p = Path(env)
        if p.is_dir():
            return p

    # 2. __file__ から探索
    # paths.py → mekhane/ → _src｜ソースコード/ → 20_機構｜Mekhane/ → HGK_ROOT
    current = Path(__file__).resolve()
    for _ in range(6):  # 最大6階層上まで探索
        current = current.parent
        # 00_核心｜Kernel が存在すれば HGK_ROOT
        if (current / "00_核心｜Kernel").is_dir():
            return current

    # 3. フォールバック
    fallback = Path.home() / "Sync" / "oikos" / "01_ヘゲモニコン｜Hegemonikon"
    if fallback.is_dir():
        return fallback

    # 最終手段: 存在しなくてもパスは返す (テスト環境用)
    return fallback


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Root
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HGK_ROOT = _detect_root()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Top-level numbered directories
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KERNEL_DIR = HGK_ROOT / "00_核心｜Kernel"
NOUS_DIR = HGK_ROOT / "10_知性｜Nous"
MEKHANE_DIR = HGK_ROOT / "20_機構｜Mekhane"
MNEME_DIR = HGK_ROOT / "30_記憶｜Mneme"
POIEMA_DIR = HGK_ROOT / "40_作品｜Poiema"
EXTERNAL_DIR = HGK_ROOT / "50_外部｜External"
PEIRA_DIR = HGK_ROOT / "60_実験｜Peira"
OPS_DIR = HGK_ROOT / "80_運用｜Ops"
ARCHIVE_DIR = HGK_ROOT / "90_保管庫｜Archive"

# 後方互換エイリアス
ORGANON_DIR = POIEMA_DIR

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Source code directories
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MEKHANE_SRC = MEKHANE_DIR / "_src｜ソースコード"
POIEMA_SRC = POIEMA_DIR / "_src｜ソースコード"
OPS_SRC = OPS_DIR / "_src｜ソースコード"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Nous (知性) subdirectories
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONSTRAINTS_DIR = NOUS_DIR / "01_制約｜Constraints"  # Rules, BC, safety
PROCEDURES_DIR = NOUS_DIR / "02_手順｜Procedures"    # WF, Skills, Macros
EPISTEME_DIR = NOUS_DIR / "03_知識｜Epistēmē"       # KI, docs
BOULESIS_DIR = NOUS_DIR / "04_企画｜Boulēsis"       # Projects, plans
HYLE_DIR = NOUS_DIR / "05_素材｜Hylē"               # Templates, assets

# Boulēsis の下位ディレクトリ (Helm / Pinakas)
HELM_DIR = BOULESIS_DIR / "00_舵｜Helm"
PINAKAS_DIR = HELM_DIR / "pinakas"

# 後方互換エイリアス
NOMOS_DIR = CONSTRAINTS_DIR
METHODOS_DIR = PROCEDURES_DIR

# Methodos の下位ディレクトリ (高頻度アクセス)
WORKFLOWS_DIR = PROCEDURES_DIR / "A_手順｜Workflows"
SKILLS_DIR = PROCEDURES_DIR / "C_技能｜Skills"
MACROS_DIR = PROCEDURES_DIR / "D_マクロ｜Macros"

# 旧名エイリアス (後方互換)
RULES_DIR = CONSTRAINTS_DIR
DOCS_DIR = EPISTEME_DIR

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Mneme (記憶) subdirectories
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MNEME_RECORDS = MNEME_DIR / "01_記録｜Records"
MNEME_INDEX = MNEME_DIR / "02_索引｜Index"
MNEME_MATERIALS = MNEME_DIR / "03_素材｜Materials"
MNEME_GNOSIS = MNEME_DIR / "04_知識｜Gnosis"
MNEME_STATE = MNEME_DIR / "05_状態｜State"

GNOSIS_DATA_DIR = MNEME_GNOSIS / "00_知識基盤｜KnowledgeBase"
GNOSIS_DB_DIR = GNOSIS_DATA_DIR / "lancedb"  # 歴史的ディレクトリ名 (実体は FAISS)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Records (記録) — 高頻度アクセスパス
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HANDOFF_DIR = MNEME_RECORDS / "a_引継｜handoff"
SESSIONS_DIR = MNEME_RECORDS / "b_対話｜sessions"
ROM_DIR = MNEME_RECORDS / "c_ROM｜rom"
ARTIFACTS_DIR = MNEME_RECORDS / "d_成果物｜artifacts"
REVIEWS_DIR = MNEME_RECORDS / "e_レビュー｜reviews"
LOGS_DIR = MNEME_RECORDS / "f_ログ｜logs"
TRACES_DIR = MNEME_RECORDS / "g_実行痕跡｜traces"

# 後方互換エイリアス (旧 e_出力 → d_成果物 に統合)
OUTPUTS_DIR = ARTIFACTS_DIR

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# State (状態) L2 — A_ prefix 付与済み
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATE_VIOLATIONS = MNEME_STATE / "A_違反｜Violations"
STATE_CACHE = MNEME_STATE / "B_キャッシュ｜Cache"
STATE_LOGS = MNEME_STATE / "C_ログ｜Logs"
STATE_RUNTIME = MNEME_STATE / "F_ランタイム｜Runtime"
STATE_SYNTELEIA = MNEME_STATE / "G_合成ログ｜SynteleiaLogs"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Materials (素材) — Digestor pipeline
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INCOMING_DIR = MNEME_MATERIALS / "a_受信｜incoming"
PROCESSED_DIR = MNEME_MATERIALS / "b_処理済｜processed"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Index (索引) — Mneme indices
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INDICES_DIR = MNEME_INDEX   # sophia.pkl, link_graph.json, etc.
INDEX_DIR = INDICES_DIR     # 後方互換性エイリアス
SOPHIA_INDEX = INDICES_DIR / "sophia.pkl"
KAIROS_INDEX = INDICES_DIR / "kairos.pkl"
CHRONOS_INDEX = INDICES_DIR / "chronos.pkl"
CODE_INDEX = INDICES_DIR / "code.pkl"
CODE_CCL_INDEX = INDICES_DIR / "code_ccl.pkl"  # CCL-only 構造検索用
CODE_CCL_FEATURES_INDEX = INDICES_DIR / "code_ccl_features.pkl"  # 49d 構造類似検索用
FILE_DISTANCES_INDEX = INDICES_DIR / "file_distances.pkl"  # ファイル間 ED 構造距離

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Beliefs (信念) — FEP 学習データ
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MNEME_BELIEFS = MNEME_DIR / "00_信念｜Beliefs"
FEP_DATA_DIR = MNEME_DIR / "fep"
EVOLVED_WEIGHTS = MNEME_DIR / "evolved_weights.json"
DERIVATIVE_SELECTIONS = MNEME_DIR / "derivative_selections.yaml"
MEANINGFUL_TRACES = MNEME_DIR / "meaningful_traces.json"
LEARNED_A_PATH = FEP_DATA_DIR / "learned_A.npy"
LEARNED_A_META = FEP_DATA_DIR / "learned_A_meta.json"
FEEDBACK_JSON = MNEME_BELIEFS / "feedback.json"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Peira (実験) subdirectories
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXPERIMENTS_DIR = PEIRA_DIR / "00_実験｜Experiments"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IDE / dot-directory paths
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KI_DIR = Path.home() / ".gemini" / "antigravity" / "knowledge"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Oikos (家) — プロジェクト外パス
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OIKOS_ROOT = HGK_ROOT.parent  # 01_ヘゲモニコン の親 = oikos

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Ops (運用) scripts
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCRIPTS_DIR = OPS_SRC / "scripts"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Agent config (.agent)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT_DIR = HGK_ROOT / ".agent"
AGENT_WORKFLOWS_DIR = AGENT_DIR / "workflows"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Windows → WSL パス変換
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PURPOSE: Windows IDE から受け取ったパスを WSL パスに変換する

# Syncthing マッピング: Windows ユーザー名 → WSL ユーザー名
# このテーブルを拡張すれば複数環境に対応可能
_SYNCTHING_MAPPINGS: list[tuple[str, str]] = [
    # (Windows の prefix (小文字・正規化済み), WSL の prefix)
    ("c:/users/makar/sync/", "/home/makaron8426/Sync/"),
]

import re as _re

# Windows パス検出パターン: C:\ or C:/ で始まる
_WIN_PATH_RE = _re.compile(r'^([A-Za-z]):[/\\]')


def resolve_client_path(filepath: str) -> Path:
    """クライアント (Windows IDE) から受け取った filepath を WSL パスに変換する。

    変換ルール:
    1. Syncthing マッピングに一致 → マッピング先に変換
    2. 一般的な Windows ドライブパス → /mnt/{drive}/... に変換
    3. 既に WSL パス → そのまま返す

    Args:
        filepath: クライアントから受け取ったファイルパス文字列

    Returns:
        Path: WSL で解決可能な Path オブジェクト

    Examples:
        >>> resolve_client_path(r"C:\\Users\\makar\\Sync\\oikos\\file.txt")
        PosixPath('/home/makaron8426/Sync/oikos/file.txt')
        >>> resolve_client_path("/home/makaron8426/Sync/oikos/file.txt")
        PosixPath('/home/makaron8426/Sync/oikos/file.txt')
        >>> resolve_client_path(r"D:\\SomeDir\\file.txt")
        PosixPath('/mnt/d/SomeDir/file.txt')
    """
    if not filepath:
        return Path(filepath)

    # バックスラッシュをスラッシュに正規化
    normalized = filepath.replace("\\", "/")

    # Windows パスかどうか判定
    match = _WIN_PATH_RE.match(normalized)
    if not match:
        # WSL パスまたは相対パス → そのまま返す
        return Path(filepath)

    # Syncthing マッピングを試行
    normalized_lower = normalized.lower()
    for win_prefix, wsl_prefix in _SYNCTHING_MAPPINGS:
        if normalized_lower.startswith(win_prefix):
            # マッピング先に変換 (元のパスの大文字小文字を保持)
            relative = normalized[len(win_prefix):]
            wsl_path = wsl_prefix + relative
            return Path(wsl_path)

    # 一般的な Windows ドライブパス → /mnt/{drive}/...
    drive_letter = match.group(1).lower()
    rest = normalized[3:]  # "C:/" の後
    return Path(f"/mnt/{drive_letter}/{rest}")


def ensure_dirs(*dirs: Path) -> None:
    """指定されたディレクトリが存在しなければ作成する。"""
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def ensure_standard_dirs() -> None:
    """標準ディレクトリ構造を作成する。"""
    ensure_dirs(
        INCOMING_DIR,
        PROCESSED_DIR,
        SESSIONS_DIR,
        HANDOFF_DIR,
        ROM_DIR,
        ARTIFACTS_DIR,
        REVIEWS_DIR,
        LOGS_DIR,
        INDICES_DIR,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Auto-load Environment Variables
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ensure_env()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Debug / self-test
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
if __name__ == "__main__":
    print(f"HGK_ROOT:      {HGK_ROOT}")
    print(f"  exists:      {HGK_ROOT.is_dir()}")
    print(f"KERNEL_DIR:    {KERNEL_DIR}  {'✅' if KERNEL_DIR.is_dir() else '❌'}")
    print(f"NOUS_DIR:      {NOUS_DIR}  {'✅' if NOUS_DIR.is_dir() else '❌'}")
    print(f"MEKHANE_DIR:   {MEKHANE_DIR}  {'✅' if MEKHANE_DIR.is_dir() else '❌'}")
    print(f"MNEME_DIR:     {MNEME_DIR}  {'✅' if MNEME_DIR.is_dir() else '❌'}")
    print(f"WORKFLOWS_DIR: {WORKFLOWS_DIR}  {'✅' if WORKFLOWS_DIR.is_dir() else '❌'}")
    print(f"INCOMING_DIR:  {INCOMING_DIR}  {'✅' if INCOMING_DIR.is_dir() else '❌'}")
    print(f"SESSIONS_DIR:  {SESSIONS_DIR}  {'✅' if SESSIONS_DIR.is_dir() else '❌'}")
    print(f"INDICES_DIR:   {INDICES_DIR}  {'✅' if INDICES_DIR.is_dir() else '❌'}")
