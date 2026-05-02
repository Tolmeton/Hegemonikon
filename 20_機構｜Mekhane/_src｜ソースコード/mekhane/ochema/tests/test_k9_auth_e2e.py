# PROOF: mekhane/ochema/tests/test_k9_auth_e2e.py
# PURPOSE: ochema モジュールの k9_auth_e2e に対するテスト
from __future__ import annotations
import time
import logging
import pytest
from mekhane.ochema.ls_manager import NonStandaloneLSManager, provision_state_db
from mekhane.ochema.antigravity_client import AntigravityClient
from mekhane.ochema.ext_server import DummyExtServer
from mekhane.ochema.service import OchemaService

logger = logging.getLogger(__name__)

# K9 (model not found) エラーが C9 (無効なトークン) によって引き起こされるかを
# 検証するための E2E テスト。グローバルな state.vscdb を書き換えるため CI ではスキップ。
@pytest.mark.skip(reason="Modifies global state.vscdb, run manually via pytest -s")
def test_k9_repro_headless_invalid_token():
    invalid_token = "ya29.a0ATkoC_invalid_token_test_string_for_K9_repro_1234567890abcdef"
    
    # 事前に意図的に無効なトークンを注入する
    provision_state_db(access_token=invalid_token)

    # IDE との通信を遮断し、純粋な Headless にするために DummyExtServer を立てる
    dummy = DummyExtServer()
    dummy.start()

    mgr = NonStandaloneLSManager(
        ext_server_port=dummy.port,
        ext_server_csrf=dummy.csrf
    )
    
    ls_info = mgr.start()
    client = AntigravityClient(ls_info=ls_info)

    k9_error_raised = False
    try:
        time.time()
        logger.info("Attempting IMMEDIATE ask with M35 and invalid token...")
        # タイムアウトは短めでよい（すぐ 500 error になる）
        client.ask("Hello, are you Claude?", model="MODEL_PLACEHOLDER_M35", timeout=10)
    except RuntimeError as e:
        error_msg = str(e)
        if "model not found" in error_msg.lower():
            k9_error_raised = True
            logger.info("Successfully reproduced K9 (model not found) error.")
        else:
            logger.error(f"Unexpected error: {error_msg}")
            raise
    finally:
        mgr.stop()
        dummy.stop()
        
        # 終わったら正常なトークンに戻しておく
        provision_state_db()
        logger.info("Restored valid token.")

    assert k9_error_raised, "Expected 'model not found' (K9) error was not raised with invalid token."

@pytest.mark.skip(reason="Modifies global state.vscdb, run manually via pytest -s")
def test_k9_auto_recovery_in_service():
    """OchemaService の _ask_ls に実装した強制再起動＋リトライが動作するか検証する。"""
    OchemaService.reset()
    service = OchemaService.get()
    
    invalid_token = "ya29.a0ATkoC_invalid_token_test_string_for_K9_repro_1234567890abcdef"
    
    # 意図的に無効なトークンを注入
    provision_state_db(access_token=invalid_token)
    
    dummy = DummyExtServer()
    dummy.start()

    # OchemaService に特殊な NonStandaloneLSManager を注入
    mgr = NonStandaloneLSManager(
        ext_server_port=dummy.port,
        ext_server_csrf=dummy.csrf
    )
    service._nonstd_mgr = mgr
    
    try:
        # この中では OchemaService._ask_ls が呼ばれる。
        # _get_ls_client 内ですでに _nonstd_mgr があるため再 start はスキップされる？
        # 否、self._ls_client == None なら _get_ls_client() は _nonstd_mgr.start() を呼ぶが、
        # すでに mgr.start() されている状態をシミュレートする必要がある。
        
        # LS を起動
        ls_info = mgr.start()
        service._ls_client = AntigravityClient(ls_info=ls_info)
        
        # ここで ask を叩くと K9 が発生し、リトライロジックが発動するはず。
        # リトライ時には service._nonstd_mgr=None となり _get_ls_client() が新たに mgr を作り直す。
        # 新たな mgr.start() の中で provision_state_db() が走り、トークンが正常化されるため成功する。
        
        resp = service._ask_ls("Hello", model="claude-sonnet")
        assert resp is not None
        assert len(resp.text) > 0
        logger.info("Service correctly recovered from K9 state.")
    finally:
        if service._nonstd_mgr:
            service._nonstd_mgr.stop()
        dummy.stop()
        provision_state_db()
        OchemaService.reset()
