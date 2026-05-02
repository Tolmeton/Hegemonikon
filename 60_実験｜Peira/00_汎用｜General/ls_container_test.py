#!/usr/bin/env python3
"""Headless コンテナでの LS 起動テスト。

IDE なし環境で DummyExtServer + Non-Standalone LS が正常に起動し、
認証を通過できることを検証する。
"""
import sys
import time
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger("container-test")

# _STATE_DB を /app/state.vscdb にパッチ
sys.path.insert(0, "/app")
import mekhane.ochema.ext_server as es
import mekhane.ochema.ls_manager as lm

state_db = Path("/app/state.vscdb")
es._STATE_DB = state_db
lm._STATE_DB = state_db
logger.info("_STATE_DB = %s (exists=%s)", state_db, state_db.exists())

# LS binary 確認
ls_bin = Path(lm.LS_BINARY)
logger.info("LS binary = %s (exists=%s)", ls_bin, ls_bin.exists())
if not ls_bin.exists():
    logger.error("LS binary not found!")
    sys.exit(1)

# テスト実行
try:
    mgr = lm.NonStandaloneLSManager(workspace_id="container_test", force_dummy=True)
    logger.info("MGR created")
    ls = mgr.start()
    logger.info("START OK pid=%d port=%d", mgr.pid, mgr.port)
except Exception as e:
    logger.error("START FAILED: %s", e)
    import traceback
    traceback.print_exc()
    sys.exit(1)

logger.info("Waiting 15s for LS auth...")
time.sleep(15)

# LS ログ確認
log_path = getattr(mgr, "_log_path", None)
if log_path and Path(log_path).exists():
    with open(log_path) as lf:
        lines = lf.readlines()
        logger.info("=== LS log: %d lines ===", len(lines))
        for l in lines[:30]:
            print(f"  {l.rstrip()}")

        # auth 関連行
        auth_keywords = [
            'auth', 'token', 'key not', 'OAuth', 'Cache(',
            'model', 'protocol', 'UTF-8', 'unmarshal', 'permission',
            'error', 'fail', 'Error',
        ]
        auth = [l for l in lines if any(k in l for k in auth_keywords)]
        if auth:
            logger.info("=== Auth/Error lines (%d) ===", len(auth))
            for l in auth[:25]:
                print(f"  {l.rstrip()}")
        else:
            logger.info("No auth/error lines found — clean startup!")
else:
    logger.warning("LS log not found: %s", log_path)

mgr.stop()
logger.info("DONE — test complete")
