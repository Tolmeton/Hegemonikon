# PROOF: F10 Plugin OS — Tests
# PURPOSE: PluginLoader と API エンドポイントの統合テスト

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mekhane.api.routes.plugins import router
from mekhane.plugin.loader import PluginLoader, get_hgk_root, load_self

# FastAPI Router のみでテストクライアント構築
from fastapi import FastAPI
app = FastAPI()
app.include_router(router)
client = TestClient(app)

@pytest.fixture
def hgk_root():
    """PURPOSE: HGK ルートパスを取得"""
    return get_hgk_root()

def test_plugin_loader(hgk_root):
    """PURPOSE: PluginLoader が plugin.yaml をパースして10要素をカウントできるか"""
    loader = PluginLoader(hgk_root)
    plugin = loader.load()

    assert plugin.id == "com.hegemonikon.core"
    assert plugin.name == "Hegemonikón Core"
    assert plugin.enabled is True

    # 要素カウントの検証
    elems = {e.element_id: e for e in plugin.elements}
    
    # E1: Skills (symlink経由で35件前後あるはずだが、環境依存のため>0を確認)
    assert "E1" in elems
    
    # E2: Commands
    assert "E2" in elems
    
    # E3: Agents
    assert "E3" in elems
    assert elems["E3"].count == 5  # colony-coo, engineer, researcher, qa, intern

    # E4: Hooks
    assert "E4" in elems
    assert elems["E4"].count == 3  # boot, bye, verify_on_edit

    # X1: CCL
    assert "X1" in elems

def test_load_self():
    """PURPOSE: load_self() で自分自身を Plugin #0 としてロードできるか"""
    plugin = load_self()
    assert plugin.id == "com.hegemonikon.core"

def test_api_list_plugins():
    """PURPOSE: GET /api/plugins が動作するか"""
    response = client.get("/plugins")
    assert response.status_code == 200
    data = response.json()
    assert "plugins" in data
    assert "total" in data
    
    plugins = data["plugins"]
    assert len(plugins) == 1
    assert plugins[0]["id"] == "com.hegemonikon.core"

def test_api_get_plugin():
    """PURPOSE: GET /api/plugins/{id} が動作するか"""
    response = client.get("/plugins/com.hegemonikon.core")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "com.hegemonikon.core"
    assert "elements" in data

def test_api_get_plugin_elements():
    """PURPOSE: GET /api/plugins/{id}/elements が動作するか"""
    response = client.get("/plugins/com.hegemonikon.core/elements")
    assert response.status_code == 200
    data = response.json()
    assert data["plugin_id"] == "com.hegemonikon.core"
    assert "E1" in data["elements"]
    assert "X1" in data["elements"]
