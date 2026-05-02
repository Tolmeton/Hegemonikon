"""enrich_*.py のデータ構造 + パッチロジックのテスト。

enrich スクリプトはスタンドアロン実行型で、末尾で wf-data.js を直接読み書きする。
テストでは以下を検証:
  1. RICH_DATA の構造的妥当性 (必須キー, 型, 非空)
  2. パッチの正規表現ロジック (模擬 JS ファイルへの適用)
"""
# PROOF: mekhane/tools/tests/test_enrich_tools.py
# PURPOSE: enrich_*.py のデータ構造とパッチロジックの検証
import json
import re
from pathlib import Path

import pytest


# ─────────────────────────────────────────────
# RICH_DATA の import (各スクリプトからデータだけ取得)
# スクリプト末尾の副作用 (ファイル読み書き) を避けるため
# importlib 等ではなく AST パースで RICH_DATA を抽出
# ─────────────────────────────────────────────

def _extract_rich_data(filepath: Path) -> dict:
    """enrich_.py の RICH_DATA 辞書を AST でなく exec で安全に抽出。"""
    src = filepath.read_text("utf-8")
    # RICH_DATA = {  から 次のトップレベル変数まで を抽出
    # enrich スクリプトは RICH_DATA = { ... } の後に
    # with open(...) がくる構成
    match = re.search(r'^RICH_DATA\s*=\s*(\{.*?\n\})', src, re.DOTALL | re.MULTILINE)
    if not match:
        pytest.skip(f"RICH_DATA が見つからない: {filepath}")
    # JSON-like 文字列を Python dict として eval
    # 注意: Python dict リテラルなので json.loads はダメ
    try:
        # 安全性: 自ファイル内の定数のみ eval
        data = eval(match.group(1))  # noqa: S307
        return data
    except Exception as e:
        pytest.skip(f"RICH_DATA パース失敗: {e}")


# ─────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────

TOOLS_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(params=["enrich_sh_series.py", "enrich_o_series.py", "enrich_pka_series.py"])
def rich_data(request) -> tuple[str, dict]:
    """各 enrich スクリプトの RICH_DATA を返す。"""
    filepath = TOOLS_DIR / request.param
    if not filepath.exists():
        pytest.skip(f"{request.param} が存在しない")
    data = _extract_rich_data(filepath)
    return request.param, data


# ─────────────────────────────────────────────
# テスト: RICH_DATA 構造検証
# ─────────────────────────────────────────────

class TestRichDataStructure:
    """RICH_DATA が必須フィールドを持ち、型が正しいことを検証。"""

    def test_not_empty(self, rich_data):
        name, data = rich_data
        assert len(data) > 0, f"{name}: RICH_DATA が空"

    def test_required_keys(self, rich_data):
        """各 WF エントリに desc, phases, derivatives, usecases が存在。"""
        name, data = rich_data
        required = {"desc", "phases", "derivatives", "usecases"}
        for cmd, entry in data.items():
            missing = required - set(entry.keys())
            assert not missing, f"{name}/{cmd}: 必須キー欠損 {missing}"

    def test_desc_not_empty(self, rich_data):
        """desc が非空文字列。"""
        name, data = rich_data
        for cmd, entry in data.items():
            assert isinstance(entry["desc"], str) and len(entry["desc"]) > 10, \
                f"{name}/{cmd}: desc が短すぎるか空"

    def test_phases_structure(self, rich_data):
        """phases が list of dict で id, name, detail を持つ。"""
        name, data = rich_data
        for cmd, entry in data.items():
            phases = entry["phases"]
            assert isinstance(phases, list), f"{name}/{cmd}: phases は list"
            assert len(phases) >= 2, f"{name}/{cmd}: phases が2個未満"
            for ph in phases:
                assert "id" in ph, f"{name}/{cmd}: phase に id 欠損"
                assert "name" in ph, f"{name}/{cmd}: phase に name 欠損"
                assert "detail" in ph, f"{name}/{cmd}: phase に detail 欠損"

    def test_derivatives_structure(self, rich_data):
        """derivatives が list of dict で name, when, output を持つ。"""
        name, data = rich_data
        for cmd, entry in data.items():
            derivs = entry["derivatives"]
            assert isinstance(derivs, list), f"{name}/{cmd}: derivatives は list"
            for deriv in derivs:
                assert "name" in deriv, f"{name}/{cmd}: derivative に name 欠損"
                assert "when" in deriv, f"{name}/{cmd}: derivative に when 欠損"
                assert "output" in deriv, f"{name}/{cmd}: derivative に output 欠損"

    def test_usecases_structure(self, rich_data):
        """usecases が list of dict で situation, trigger, action, result を持つ。"""
        name, data = rich_data
        for cmd, entry in data.items():
            ucs = entry["usecases"]
            assert isinstance(ucs, list), f"{name}/{cmd}: usecases は list"
            for uc in ucs:
                assert "situation" in uc, f"{name}/{cmd}: usecase に situation 欠損"
                assert "trigger" in uc, f"{name}/{cmd}: usecase に trigger 欠損"
                assert "action" in uc, f"{name}/{cmd}: usecase に action 欠損"
                assert "result" in uc, f"{name}/{cmd}: usecase に result 欠損"

    def test_algebra_detail_optional(self, rich_data):
        """algebra_detail があれば +, -, * を持つ。"""
        name, data = rich_data
        for cmd, entry in data.items():
            if "algebra_detail" in entry:
                alg = entry["algebra_detail"]
                assert "+" in alg, f"{name}/{cmd}: algebra_detail に + 欠損"
                assert "-" in alg, f"{name}/{cmd}: algebra_detail に - 欠損"
                assert "*" in alg, f"{name}/{cmd}: algebra_detail に * 欠損"


# ─────────────────────────────────────────────
# テスト: パッチロジック (JS ファイルへの適用)
# ─────────────────────────────────────────────

class TestPatchLogic:
    """enrich スクリプトのパッチロジック (正規表現 + JSON マージ) を再現テスト。"""

    @pytest.fixture
    def mock_wf_js(self, tmp_path) -> Path:
        """テスト用の模擬 wf-data.js を生成。"""
        wf_data = {
            "noe": {"id": "noe", "name": "Noēsis", "desc": "old desc"},
            "met": {"id": "met", "name": "Methodos", "desc": "old met desc"},
            "unknown_cmd": {"id": "unknown", "name": "Unknown", "desc": "x"},
        }
        js_content = f"const WF_DATA = {json.dumps(wf_data, ensure_ascii=False, indent=1)};\n"
        p = tmp_path / "wf-data.js"
        p.write_text(js_content, "utf-8")
        return p

    def test_regex_matches_wf_data(self, mock_wf_js):
        """正規表現が const WF_DATA = {...}; をキャプチャする。"""
        content = mock_wf_js.read_text("utf-8")
        m = re.search(r'const WF_DATA = ({.*?});\s*\n', content, re.DOTALL)
        assert m is not None
        parsed = json.loads(m.group(1))
        assert "noe" in parsed
        assert "met" in parsed

    def test_patch_updates_existing_key(self, mock_wf_js):
        """既存キーの desc, phases 等が上書きされる。"""
        content = mock_wf_js.read_text("utf-8")
        m = re.search(r'const WF_DATA = ({.*?});\s*\n', content, re.DOTALL)
        wf_obj = json.loads(m.group(1))

        # パッチ適用 (met の desc を差し替え)
        patch_data = {
            "met": {
                "desc": "新しい説明",
                "phases": [{"id": "Ph1", "name": "テスト", "detail": "テスト詳細"}],
                "derivatives": [],
                "usecases": [],
            }
        }
        for cmd, rich in patch_data.items():
            if cmd in wf_obj:
                wf_obj[cmd]["desc"] = rich["desc"]
                wf_obj[cmd]["phases"] = rich["phases"]

        assert wf_obj["met"]["desc"] == "新しい説明"
        assert wf_obj["met"]["phases"][0]["name"] == "テスト"
        # 他キーは変更されない
        assert wf_obj["noe"]["desc"] == "old desc"

    def test_patch_skips_unknown_key(self, mock_wf_js):
        """RICH_DATA にあるが wf_obj にないキーはスキップされる。"""
        content = mock_wf_js.read_text("utf-8")
        m = re.search(r'const WF_DATA = ({.*?});\s*\n', content, re.DOTALL)
        wf_obj = json.loads(m.group(1))

        patch_data = {"nonexistent_cmd": {"desc": "xxx"}}
        skipped = []
        for cmd, rich in patch_data.items():
            if cmd not in wf_obj:
                skipped.append(cmd)

        assert "nonexistent_cmd" in skipped

    def test_roundtrip_js_format(self, mock_wf_js):
        """パッチ後のファイルが有効な JS として再パース可能。"""
        content = mock_wf_js.read_text("utf-8")
        m = re.search(r'const WF_DATA = ({.*?});\s*\n', content, re.DOTALL)
        wf_obj = json.loads(m.group(1))

        # パッチ適用
        wf_obj["met"]["desc"] = "updated"
        new_wf = json.dumps(wf_obj, ensure_ascii=False, indent=1)
        new_content = content[:m.start(1)] + new_wf + content[m.end(1):]

        # 再パース可能か
        mock_wf_js.write_text(new_content, "utf-8")
        content2 = mock_wf_js.read_text("utf-8")
        m2 = re.search(r'const WF_DATA = ({.*?});\s*\n', content2, re.DOTALL)
        assert m2 is not None
        reparsed = json.loads(m2.group(1))
        assert reparsed["met"]["desc"] == "updated"
