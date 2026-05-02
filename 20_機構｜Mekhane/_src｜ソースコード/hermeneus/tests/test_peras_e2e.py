# E2E テスト — PerasPipeline で実際の LLM を呼び出す
"""pytest 経由で実行 (PYTHONPATH 問題を回避)

Usage:
    cd ~/oikos/01_ヘゲモニコン｜Hegemonikon
    PYTHONPATH=. .venv/bin/pytest hermeneus/tests/test_peras_e2e.py -xvs --timeout=120
"""
import json
import os
import pytest
from pathlib import Path
from hermeneus.src.peras_pipeline import PerasPipeline


def _ensure_google_key():
    """GOOGLE_API_KEY を環境変数 or mcp_config.json から読み込む"""
    if os.environ.get("GOOGLE_API_KEY"):
        return True
    config_path = Path.home() / ".gemini" / "antigravity" / "mcp_config.json"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text())
            key = config.get("mcpServers", {}).get("hermeneus", {}).get("env", {}).get("GOOGLE_API_KEY")
            if key:
                os.environ["GOOGLE_API_KEY"] = key
                return True
        except Exception:
            pass
    return False


HAS_GOOGLE_KEY = _ensure_google_key()


@pytest.mark.asyncio
@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_API_KEY not available")
@pytest.mark.timeout(300)
async def test_e2e_telos_pipeline():
    """E2E: /t (Telos) パイプラインの完全実行"""
    p = PerasPipeline(series_id="t", model="gemini-3-flash-preview", depth="+")

    result = await p.run(context="ハブWF自動実行の実現性分析")

    # Basic assertions
    assert result.series_id == "t"
    assert result.series_name == "Telos"
    assert result.ccl_executed == "/t+"

    # Output
    print(f"\n=== E2E Result ===")
    print(f"Success: {result.success}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Duration: {result.duration_ms:.0f}ms")
    if result.error:
        print(f"Error: {result.error}")
    if result.output:
        print(f"\n--- Output ---\n{result.output[:2000]}")
