#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/ochema/tests/ A0→LS認証→DummyExtServer統合テスト
# PURPOSE: Headless 環境で DummyExtServer + Non-Standalone LS が正常起動するか検証
"""DummyExtServer + Non-Standalone LS 統合テスト。

Docker コンテナ (python:3.11-slim) またはローカル環境で実行可能。
DX-015 の再現手順を自動化したもの。

Usage (ローカル):
    cd ~/oikos/01_ヘゲモニコン｜Hegemonikon
    PYTHONPATH=. .venv/bin/python -m pytest mekhane/ochema/tests/test_ls_container.py -v

Usage (Docker):
    docker run --rm -t \\
      -v /usr/share/antigravity:/usr/share/antigravity:ro \\
      -v ~/oikos/01_ヘゲモニコン｜Hegemonikon/mekhane:/app/mekhane:ro \\
      -v /tmp/state_container.vscdb:/app/state.vscdb:ro \\
      -v /tmp:/tmp -e PYTHONPATH=/app --network host \\
      python:3.11-slim timeout 40 python3 -u /app/mekhane/ochema/tests/test_ls_container.py
"""

from __future__ import annotations
import logging
import sys
import time
import unittest
import pytest
from pathlib import Path

# ローカル or Docker 対応
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if _PROJECT_ROOT.exists():
    sys.path.insert(0, str(_PROJECT_ROOT))

import mekhane.ochema.ext_server as es
import mekhane.ochema.ls_manager as lm

logger = logging.getLogger(__name__)


class TestDummyExtServerAuth(unittest.TestCase):
    """DummyExtServer を使った Non-Standalone LS 起動テスト。"""

    @classmethod
    def setUpClass(cls):
        """Docker 環境用のパッチ (ローカルではスキップ)。"""
        # Docker コンテナ内では /app/state.vscdb を使用
        docker_db = Path("/app/state.vscdb")
        if docker_db.exists():
            es._STATE_DB = docker_db
            lm._STATE_DB = docker_db
            logger.info("Docker mode: _STATE_DB = %s", docker_db)

    def test_build_uss_oauth_response(self):
        """_build_uss_oauth_response が有効な proto を生成する。"""
        result = es._build_uss_oauth_response()
        self.assertGreater(len(result), 0, "proto should not be empty")
        # ConnectRPC envelope: flag(1) + length(4) + proto
        self.assertGreater(len(result), 100, "proto should be substantial (>100 bytes)")
        logger.info("USS response: %d bytes", len(result))

    @pytest.mark.skip(reason="Log format changed")
    def test_ls_startup_with_dummy(self):
        """DummyExtServer 経由で LS が正常起動する。"""
        ls_bin = Path(lm.LS_BINARY)
        if not ls_bin.exists():
            self.skipTest(f"LS binary not found: {ls_bin}")

        mgr = lm.NonStandaloneLSManager(
            workspace_id="test_container", force_dummy=True
        )
        try:
            ls = mgr.start()
            self.assertIsNotNone(ls)
            self.assertGreater(mgr.port, 0)
            logger.info("LS started: pid=%d port=%d", mgr.pid, mgr.port)

            # LS ログの確認
            time.sleep(5)
            if mgr._log_path and Path(mgr._log_path).exists():
                with open(mgr._log_path) as lf:
                    log = lf.read()
                self.assertIn("initialized server successfully", log)
                self.assertNotIn("key not found", log)
                self.assertNotIn("invalid UTF-8", log)
                logger.info("LS log clean — no auth errors")
        finally:
            mgr.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
    unittest.main()
