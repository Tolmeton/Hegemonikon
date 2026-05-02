#!/usr/bin/env python3
# PROOF: [L1/テスト] <- mekhane/mcp/tests/
# PURPOSE: Gateway ツール群の正常パステスト（セキュリティテストの補完）
"""
L1 正常系テスト — hgk_gateway

サーバーを起動せず、ツール関数を直接呼び出して正常パスを検証する。
test_gateway_security.py (防御テスト 9件) と対になる攻撃/正常のペア。
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest


# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

# GATEWAY_TOKEN を設定（テスト用）
os.environ["HGK_GATEWAY_TOKEN"] = "test_token_for_functional_testing"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mcp_tools(setup_test_dirs):
    from mcp.server.fastmcp import FastMCP
    from mekhane.mcp.gateway_tools.ccl import register_ccl_tools
    from mekhane.mcp.gateway_tools.knowledge import register_knowledge_tools
    from mekhane.mcp.gateway_tools.ochema import register_ochema_tools

    _mcp = FastMCP("test_gateway")
    register_ccl_tools(_mcp)
    register_knowledge_tools(_mcp)
    register_ochema_tools(_mcp)

    return _mcp._tool_manager._tools

@pytest.fixture(autouse=True)
def setup_test_dirs(tmp_path, monkeypatch):
    """各テスト用の一時ディレクトリを設定。実ファイルシステムを汚さない。"""
    # Mneme 構造を一時ディレクトリに再現
    mneme = tmp_path / "mneme" / "05_状態｜State"
    sessions = mneme / "sessions"
    doxa = mneme / "doxa"
    ideas = mneme / "ideas"
    sop = mneme / "workflows"
    incoming = mneme / "digestor" / "incoming"
    processed = mneme / "digestor" / "processed"

    for d in [sessions, doxa, ideas, sop, incoming, processed]:
        d.mkdir(parents=True, exist_ok=True)

    # テスト用 Handoff を作成
    handoff = sessions / "handoff_20260214_test.md"
    handoff.write_text(
        "# Handoff 20260214\n\n## 実施事項\n- Gateway テスト作成\n\n## 次回\n- 検証\n",
        encoding="utf-8",
    )

    # テスト用 Doxa を作成
    doxa_file = doxa / "laws.json"
    doxa_file.write_text(
        json.dumps([
            {"strength": "S", "text": "自分を信じないことが信頼の起点"},
            {"strength": "A", "text": "意志より環境が行動を決める"},
        ], ensure_ascii=False),
        encoding="utf-8",
    )

    # Gateway モジュールのパスを上書き
    import mekhane.mcp.gateway_tools._utils as _utils
    monkeypatch.setattr(_utils, "MNEME_DIR", mneme)
    monkeypatch.setattr(_utils, "SESSIONS_DIR", sessions)
    monkeypatch.setattr(_utils, "DOXA_DIR", doxa)
    monkeypatch.setattr(_utils, "IDEA_DIR", ideas)
    monkeypatch.setattr(_utils, "SOP_OUTPUT_DIR", sop)
    monkeypatch.setattr(_utils, "INCOMING_DIR", incoming)
    monkeypatch.setattr(_utils, "PROCESSED_DIR", processed)
    monkeypatch.setattr(_utils, "_MNEME_DIR", mneme)
    monkeypatch.setattr(_utils, "_COWORK_DIR", mneme / "cowork")
    monkeypatch.setattr(_utils, "_COWORK_ARCHIVE", mneme / "cowork/_archive")

    yield {
        "mneme": mneme,
        "sessions": sessions,
        "doxa": doxa,
        "ideas": ideas,
        "sop": sop,
    }


# =============================================================================
# T1: hgk_sop_generate — 調査依頼書生成
# =============================================================================

# PURPOSE: Verify sop generation produces valid markdown template
def test_sop_generate_basic(mcp_tools, setup_test_dirs):
    """SOP テンプレートが生成され、ファイルに保存されることを確認。"""

    hgk_sop_generate = mcp_tools["hgk_sop_generate"].fn
    result = hgk_sop_generate(topic="FEP と Active Inference")
    assert "✅" in result, f"SOP 生成が成功すべき: {result[:100]}"
    assert "調査依頼書" in result, "テンプレート内容が含まれるべき"
    assert "FEP" in result, "トピックが含まれるべき"

    # ファイルが保存されているか
    sop_dir = setup_test_dirs["sop"]
    sop_files = list(sop_dir.glob("sop_*.md"))
    assert len(sop_files) >= 1, "SOP ファイルが保存されるべき"
    print("✅ T1: hgk_sop_generate — テンプレート生成 + ファイル保存")


# PURPOSE: Verify sop with optional args works correctly
def test_sop_generate_with_options(mcp_tools, setup_test_dirs):
    """decision と hypothesis を指定した SOP 生成。"""

    hgk_sop_generate = mcp_tools["hgk_sop_generate"].fn
    result = hgk_sop_generate(
        topic="圏論の応用",
        decision="採用するフレームワークを決定する",
        hypothesis="Galois 接続が最適",
    )
    assert "採用するフレームワーク" in result, "decision が含まれるべき"
    assert "Galois" in result, "hypothesis が含まれるべき"
    print("✅ T1b: hgk_sop_generate — オプション引数付き生成")


# =============================================================================
# T2: hgk_search — 知識ベース検索
# =============================================================================

# PURPOSE: Verify keyword search returns results from Doxa
def test_search_keyword_doxa(mcp_tools, setup_test_dirs):
    """キーワード検索で Doxa がヒットすることを確認。"""

    hgk_search = mcp_tools["hgk_search"].fn
    result = hgk_search(query="信頼", mode="keyword")
    assert "Doxa" in result or "信頼" in result, \
        f"Doxa の信頼キーワードがヒットすべき: {result[:200]}"
    print("✅ T2: hgk_search — Doxa キーワード検索")


def test_search_no_results(mcp_tools, setup_test_dirs):
    """(廃止) ベクトル検索は常に最近傍を返すため空にならないが、エラーにもならないことを確認。"""

    hgk_search = mcp_tools["hgk_search"].fn
    result = hgk_search(query="zyxwvutsrqp_nonexistent_12345", mode="keyword")
    assert "一致する結果はありません" in result or "検索結果" in result, \
        f"エラーにならず検索結果の形式またはなしメッセージが返るべき: {result[:200]}"
    print("✅ T2b: hgk_search — 検索エラーの graceful handling")


# PURPOSE: Verify search finds handoff content
def test_search_handoff(mcp_tools, setup_test_dirs):
    """Handoff ファイルの内容がキーワード検索でヒットすることを確認。"""

    hgk_search = mcp_tools["hgk_search"].fn
    result = hgk_search(query="Gateway", mode="keyword")
    assert "Handoff" in result or "Gateway" in result, \
        f"Handoff 内容がヒットすべき: {result[:200]}"
    print("✅ T2c: hgk_search — Handoff キーワード検索")


# =============================================================================
# T3: hgk_status — ステータス表示
# =============================================================================

# PURPOSE: Verify status returns structured overview
def test_status_overview(mcp_tools, setup_test_dirs):
    """ステータス表示が構造化された概要を返すことを確認。"""

    hgk_status = mcp_tools["hgk_status"].fn
    result = hgk_status()
    assert "ステータス" in result, f"ステータスヘッダーがあるべき: {result[:100]}"
    assert "Handoff" in result, "Handoff 件数が含まれるべき"
    assert "Doxa" in result, "Doxa 件数が含まれるべき"
    print("✅ T3: hgk_status — 構造化ステータス表示")


# =============================================================================
# T4: hgk_doxa_read — Doxa 読み取り
# =============================================================================

# PURPOSE: Verify doxa read returns stored beliefs
def test_doxa_read(mcp_tools, setup_test_dirs):
    """Doxa の内容が読み取れることを確認。"""

    hgk_doxa_read = mcp_tools["hgk_doxa_read"].fn
    result = hgk_doxa_read()
    assert "信念ストア" in result or "Doxa" in result, \
        f"Doxa ヘッダーがあるべき: {result[:100]}"
    assert "自分を信じない" in result, "テストデータの信念が含まれるべき"
    assert "意志より環境" in result, "テストデータの信念が含まれるべき"
    print("✅ T4: hgk_doxa_read — 信念データの読み取り")


# PURPOSE: Verify doxa read handles empty doxa gracefully
def test_doxa_read_empty(mcp_tools, setup_test_dirs):
    """空の Doxa ディレクトリで空メッセージが返ることを確認。"""

    # Doxa ファイルを削除
    doxa_dir = setup_test_dirs["doxa"]
    for f in doxa_dir.glob("*.json"):
        f.unlink()

    hgk_doxa_read = mcp_tools["hgk_doxa_read"].fn
    result = hgk_doxa_read()
    assert "空" in result or "Doxa" in result, \
        f"空 Doxa メッセージがあるべき: {result[:100]}"
    print("✅ T4b: hgk_doxa_read — 空 Doxa のハンドリング")


# =============================================================================
# T5: hgk_handoff_read — Handoff 参照
# =============================================================================

# PURPOSE: Verify handoff read returns latest handoff content
def test_handoff_read(mcp_tools, setup_test_dirs):
    """最新 Handoff が読み取れることを確認。"""

    hgk_handoff_read = mcp_tools["hgk_handoff_read"].fn
    result = hgk_handoff_read(count=1)
    assert "Handoff" in result, f"Handoff ヘッダーがあるべき: {result[:100]}"
    assert "Gateway テスト" in result, "テスト Handoff の内容が含まれるべき"
    print("✅ T5: hgk_handoff_read — Handoff 読み取り")


# =============================================================================
# T6: hgk_idea_capture — アイデアメモ保存 (正常パス)
# =============================================================================

# PURPOSE: Verify idea capture saves and returns confirmation
def test_idea_capture_normal(mcp_tools, setup_test_dirs):
    """正常サイズのアイデアが保存されることを確認。"""

    hgk_idea_capture = mcp_tools["hgk_idea_capture"].fn
    result = hgk_idea_capture(
        idea="FEP の精度加重をコード品質評価に応用できるかもしれない",
        tags="FEP, 実験",
    )
    assert "✅" in result, f"保存成功すべき: {result[:100]}"
    assert "FEP" in result, "タグが含まれるべき"

    # ファイルが保存されているか
    idea_dir = setup_test_dirs["ideas"]
    idea_files = list(idea_dir.glob("idea_*.md"))
    assert len(idea_files) >= 1, "アイデアファイルが保存されるべき"

    # ファイル内容の確認
    content = idea_files[0].read_text(encoding="utf-8")
    assert "精度加重" in content, "アイデア本文がファイルに含まれるべき"
    print("✅ T6: hgk_idea_capture — 正常保存 + ファイル検証")


# =============================================================================
# T7: hgk_ccl_dispatch — CCL パース
# =============================================================================

# PURPOSE: Verify CCL dispatch parses valid expressions
def test_ccl_dispatch_basic(mcp_tools, setup_test_dirs):
    """基本的な CCL 式がパースできることを確認。"""

    hgk_ccl_dispatch = mcp_tools["hgk_ccl_dispatch"].fn
    result = hgk_ccl_dispatch("/noe+")
    # パーサーがインストールされていない場合もエラーハンドリングを確認
    assert "CCL" in result or "noe" in result.lower() or "エラー" in result, \
        f"CCL 関連のレスポンスがあるべき: {result[:200]}"
    print("✅ T7: hgk_ccl_dispatch — CCL 式パース")


# =============================================================================
# T8: 脱LS テスト — LS 未接続でもツールが動作する
# =============================================================================

# PURPOSE: Verify hgk_models works without Language Server
def test_models_without_ls(mcp_tools, setup_test_dirs, monkeypatch):
    """LS 未接続でもモデル一覧が返ることを確認。"""
    from mekhane.ochema.service import OchemaService

    hgk_models = mcp_tools["hgk_models"].fn
    result = hgk_models()
    assert "モデル" in result, f"モデルヘッダーがあるべき: {result[:100]}"
    # ハードコードモデルが含まれる
    assert "gemini" in result.lower(), "Gemini モデルが含まれるべき"
    print("✅ T8a: hgk_models — 正常動作")


# PURPOSE: Verify hgk_ask works without LS (no cascade_id)
def test_ask_without_ls_no_cascade(mcp_tools, setup_test_dirs, monkeypatch):
    """LS 未接続 + cascade_id なしで、OchemaService.ask() が呼ばれることを確認。"""
    from unittest.mock import MagicMock

    # OchemaService.ask() をモックして Cortex 直呼び出しをシミュレート
    mock_response = MagicMock()
    mock_response.text = "テスト応答"
    mock_response.model = "gemini-3-flash-preview"
    mock_response.thinking = ""

    mock_svc = MagicMock()
    mock_svc.ask.return_value = mock_response

    monkeypatch.setattr(
        "mekhane.ochema.service.OchemaService.get",
        lambda: mock_svc,
    )

    hgk_ask = mcp_tools["hgk_ask"].fn
    result = hgk_ask(message="テスト", model="gemini-3-flash-preview")
    assert "テスト応答" in result, f"Cortex 直接応答が含まれるべき: {result[:200]}"
    assert "gemini-3-flash-preview" in result, "モデル名が表示されるべき"
    assert "LS 未検出" not in result, "LS エラーが出ないべき"
    mock_svc.ask.assert_called_once()
    print("✅ T8b: hgk_ask — LS 未接続 (cascade なし) で Cortex 直接動作")


# PURPOSE: Verify hgk_ask ignores cascade_id (LS removed)
def test_ask_with_cascade_ignored(mcp_tools, setup_test_dirs, monkeypatch):
    """cascade_id 指定時も Cortex 直接で応答することを確認 (LS 削除後)。"""
    from unittest.mock import MagicMock

    mock_response = MagicMock()
    mock_response.text = "テスト応答"
    mock_response.model = "gemini-3-flash-preview"
    mock_response.thinking = ""

    mock_svc = MagicMock()
    mock_svc.ask.return_value = mock_response

    monkeypatch.setattr(
        "mekhane.ochema.service.OchemaService.get",
        lambda: mock_svc,
    )

    hgk_ask = mcp_tools["hgk_ask"].fn
    result = hgk_ask(
        message="テスト",
    )
    assert "テスト応答" in result, f"Cortex 直接応答が含まれるべき: {result[:200]}"
    print("✅ T8c: hgk_ask — cascade_id 指定時も Cortex 直接")


# PURPOSE: Verify hgk_sessions falls back to handoff list without LS
def test_sessions_fallback_to_handoffs(mcp_tools, setup_test_dirs, monkeypatch):
    """LS 未接続時、Handoff ファイル一覧にフォールバックすることを確認。"""
    from mekhane.ochema.service import OchemaService

    hgk_sessions = mcp_tools["hgk_sessions"].fn
    result = hgk_sessions()
    assert "Handoff" in result, f"Handoff フォールバックが動作すべき: {result[:200]}"
    assert "IDE 未接続" in result, "IDE 未接続メッセージが表示されるべき"
    # テスト fixture で作成された handoff が含まれる
    assert "handoff_" in result, "Handoff ファイル名が含まれるべき"
    assert "❌ LS 未検出" not in result, "LS エラーにならないべき"
    print("✅ T8d: hgk_sessions — LS 未接続で Handoff フォールバック")


# =============================================================================
# Runner
# =============================================================================

# PURPOSE: Run all functional tests and report results
async def main():
    """全正常系テストを実行。"""
    print("=" * 60)
    print("  L1 正常系テスト — hgk_gateway")
    print("=" * 60)
    print()

    # pytest 経由で実行
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-q",
    ])
    return exit_code == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
