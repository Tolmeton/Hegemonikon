# PROOF: [L2/インフラ] <- mekhane/symploke/ A0→ワークスペース・PJ判定が必要→workspace_detect が担う
"""
Workspace & Project Detection — セッションのワークスペースとプロジェクトを自動判定する

判定方法:
  ワークスペース:
    A: CWD / URI / パスパターンマッチ (セッション開始時)
    C: Handoff 内容からのキーワード自動分類 (事後分類)
  プロジェクト:
    フロントマター project: タグ優先
    なければ内容キーワードから自動推定

Usage:
    from mekhane.symploke.workspace_detect import (
        detect_workspace, resolve_handoff_workspace, resolve_handoff_project,
    )

    ws = detect_workspace(context="FileMaker 案件01 の作業")  # => "fm"
    ws = resolve_handoff_workspace(handoff_content)            # => "fm" or "hgk"
    pj = resolve_handoff_project(handoff_content)              # => "Ergon" or ""
"""

# PURPOSE: ワークスペース・PJ 判定の一元管理
import re
from pathlib import Path
from typing import Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ワークスペース定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WORKSPACE_DEFINITIONS = {
    "fm": {
        "label": "FileMaker",
        # A: パスパターン
        "path_patterns": [
            r"ファイルメーカー",
            r"FileMaker",
            r"a_ファイルメーカー",
            r"01_MICKS",
            r"案件\d+",
            r"fm-agent",
        ],
        # C: コンテンツキーワード (Handoff 内容から判定)
        "content_keywords": [
            "FileMaker",
            r"FM\s*[\(\(]?[JK][\)\)]?",  # FM(J), FM(K)
            "fmp12",
            "DDR",
            r"案件\d+",
            "MICKS",
            "レイアウト定義",
            "フィールド定義",
            "スクリプト定義",
            "Forge",
            "PyBridge",
            "XMLPaste",
            "FileMaker Pro",
            "fm-boot",
            "fm-analyze",
            "Controller パターン",
        ],
        # 最低マッチ数 (C: キーワード分類の閾値)
        "min_keyword_hits": 2,
    },
    # 将来の拡張: 他のワークスペースをここに追加
    # "research": { ... },
}

# デフォルトワークスペース (どのパターンにもマッチしない場合)
DEFAULT_WORKSPACE = "hgk"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# プロジェクト定義
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 既知プロジェクトのキーワード定義
# key = 正規化されたプロジェクト名, value = マッチキーワード (1つ以上ヒットで判定)
PROJECT_DEFINITIONS = {
    "Ergon": [r"Ergon", r"能動", r"L\s*関手", r"R\s*関手", r"Markov\s*blanket", r"active\s*inference\s*実装"],
    "OssAdjoint": [r"OssAdjoint", r"随伴", r"pm-skills", r"OSS.*adjoint"],
    "GWSIntegration": [r"GWSIntegration", r"GWS", r"統合.*Integration", r"Google\s*Workspace"],
    "UnifiedIndex": [r"UnifiedIndex", r"統一索引", r"統一インデックス", r"Knowledge\s*Graph\s*DB"],
    "Kalon": [r"美論", r"Kalon", r"Fix\(G∘F\)", r"kalon\.md"],
    "Hermeneus": [r"Hermeneus", r"解釈", r"CCL.*パーサ", r"hermeneus.*MCP"],
    "Agora": [r"Agora", r"市場"],
    "Autophonos": [r"Autophonos", r"自律"],
    "Doxa": [r"Doxa", r"信念", r"doxa_promoter", r"doxa_boot"],
    "Perception": [r"Perception", r"知覚", r"V-001", r"V-002"],
    "FormalDerivation": [r"FormalDerivation", r"形式導出", r"圏論.*導出"],
    "Vision": [r"hgk_vision", r"VISION.*v4", r"ロードマップ"],
}

# 最低マッチ数 (PJ キーワードは 1 ヒットで判定 — WS より閾値が低い)
PROJECT_MIN_HITS = 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ワークスペース判定関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# PURPOSE: コンテキスト文字列からワークスペースを判定する (方式 A)
def detect_workspace(
    context: Optional[str] = None,
    cwd: Optional[str] = None,
    uri: Optional[str] = None,
) -> str:
    """コンテキストからワークスペースを自動判定する (方式 A: パターンマッチ)。

    Args:
        context: セッションコンテキスト文字列 (user_information 等)
        cwd: カレントワーキングディレクトリ
        uri: ワークスペース URI

    Returns:
        ワークスペースタグ (例: "fm", "hgk")
    """
    # 検査対象テキストを結合
    search_text = ""
    if context:
        search_text += context + "\n"
    if cwd:
        search_text += cwd + "\n"
    if uri:
        search_text += uri + "\n"

    if not search_text.strip():
        return DEFAULT_WORKSPACE

    # 各ワークスペースのパスパターンをチェック
    for ws_tag, ws_def in WORKSPACE_DEFINITIONS.items():
        for pattern in ws_def["path_patterns"]:
            if re.search(pattern, search_text, re.IGNORECASE):
                return ws_tag

    return DEFAULT_WORKSPACE


# PURPOSE: Handoff コンテンツからワークスペースを事後分類する (方式 C)
def classify_handoff_workspace(content: str) -> str:
    """Handoff ファイルの内容からワークスペースを事後分類する (方式 C: キーワード分類)。

    Args:
        content: Handoff ファイルの全文テキスト

    Returns:
        ワークスペースタグ (例: "fm", "hgk")
    """
    if not content:
        return DEFAULT_WORKSPACE

    for ws_tag, ws_def in WORKSPACE_DEFINITIONS.items():
        hits = 0
        for keyword in ws_def["content_keywords"]:
            if re.search(keyword, content, re.IGNORECASE):
                hits += 1
        if hits >= ws_def["min_keyword_hits"]:
            return ws_tag

    return DEFAULT_WORKSPACE


# PURPOSE: YAML フロントマターから workspace タグを抽出する
def extract_workspace_from_frontmatter(content: str) -> Optional[str]:
    """YAML フロントマターから workspace: タグを抽出する。

    Args:
        content: Handoff ファイルの全文テキスト

    Returns:
        workspace タグ (見つからなければ None)
    """
    match = re.search(
        r"^\s*workspace:\s*[\"']?(\w+)[\"']?",
        content,
        re.MULTILINE,
    )
    if match:
        return match.group(1).lower()
    return None


# PURPOSE: Handoff のワークスペースを決定する (フロントマター優先、なければ自動分類)
def resolve_handoff_workspace(content: str) -> str:
    """Handoff のワークスペースを決定する。

    優先順位:
    1. YAML フロントマターの workspace: タグ
    2. コンテンツキーワード自動分類 (方式 C)
    3. デフォルト "hgk"

    Args:
        content: Handoff ファイルの全文テキスト

    Returns:
        ワークスペースタグ
    """
    # 1. フロントマター
    ws = extract_workspace_from_frontmatter(content)
    if ws:
        return ws

    # 2. 自動分類
    return classify_handoff_workspace(content)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# プロジェクト判定関数
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


# PURPOSE: YAML フロントマターから project タグを抽出する
def extract_project_from_frontmatter(content: str) -> Optional[str]:
    """YAML フロントマターから project: タグを抽出する。

    Args:
        content: Handoff ファイルの全文テキスト

    Returns:
        project タグ (見つからなければ None)
    """
    match = re.search(
        r"^\s*project:\s*[\"']?([^\n\"']+?)[\"']?\s*$",
        content,
        re.MULTILINE,
    )
    if match:
        return match.group(1).strip()
    return None


# PURPOSE: Handoff 内容からプロジェクトを自動推定する
def classify_handoff_project(content: str) -> str:
    """Handoff 内容からプロジェクトを推定する (キーワードマッチ)。

    最もヒット数が多いプロジェクトを返す。
    同点の場合は先に定義されたものが優先。

    Args:
        content: Handoff ファイルの全文テキスト

    Returns:
        プロジェクト名 (推定できなければ "")
    """
    if not content:
        return ""

    best_project = ""
    best_hits = 0

    for pj_name, keywords in PROJECT_DEFINITIONS.items():
        hits = 0
        for keyword in keywords:
            if re.search(keyword, content, re.IGNORECASE):
                hits += 1
        if hits >= PROJECT_MIN_HITS and hits > best_hits:
            best_hits = hits
            best_project = pj_name

    return best_project


# PURPOSE: Handoff のプロジェクトを決定する (フロントマター優先、なければ自動推定)
def resolve_handoff_project(content: str) -> str:
    """Handoff のプロジェクトを決定する。

    優先順位:
    1. YAML フロントマターの project: タグ
    2. コンテンツキーワード自動推定
    3. デフォルト "" (未分類)

    Args:
        content: Handoff ファイルの全文テキスト

    Returns:
        プロジェクト名 (未分類なら "")
    """
    # 1. フロントマター
    pj = extract_project_from_frontmatter(content)
    if pj:
        return pj

    # 2. 自動推定
    return classify_handoff_project(content)
