#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/ ls_daemon
# PURPOSE: Non-Standalone LS を常駐プロセスとして管理するデーモン
"""Non-Standalone LS Daemon.

hgk サーバー等で systemd から起動され、Non-Standalone LS を安定稼働させる。
接続情報 (port, csrf) を JSON ファイルに書き出し、他プロセスからの接続を可能にする。
"""
from __future__ import annotations
from typing import Any

import argparse
import fcntl
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import List, Dict

from mekhane.ochema.ls_manager import NonStandaloneLSManager
from mekhane.ochema.antigravity_client import AntigravityClient

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("ls_daemon")

# 接続情報の保存先 (環境変数でオーバーライド可能 — コンテナ対応)
DAEMON_INFO_PATH = Path(os.environ.get(
    "LS_DAEMON_INFO_PATH",
    str(Path.home() / ".gemini/antigravity/ls_daemon.json"),
))


class LSPoolDaemon:
    def __init__(self, workspace_prefix: str = "nonstd_hgk", num_instances: int = 1, force_dummy: bool = True, source: str = "local"):
        self.workspace_prefix = workspace_prefix
        self.num_instances = num_instances
        self.force_dummy = force_dummy
        self.source = source  # "local" | "docker" — ls_daemon.json に記録
        self.managers: List[NonStandaloneLSManager] = []
        self.ls_infos: List[Any] = []
        self.account_assignments: List[str] = []  # 各 LS に割り当てたアカウント
        self._running = False

    def start(self):
        """デーモンを起動し、ブロックする。"""
        # vault.json からアカウントリストを取得
        self._load_accounts()
        logger.info(
            f"Starting LS Daemon Pool ({self.num_instances} instances, "
            f"{len(self.account_assignments)} accounts) "
            f"for workspace prefix {self.workspace_prefix}..."
        )
        for i, acct in enumerate(self.account_assignments):
            logger.info(f"  LS {i} ← Account '{acct}'")
        
        for i in range(self.num_instances):
            ws_id = f"{self.workspace_prefix}_{i}"
            account = self.account_assignments[i] if i < len(self.account_assignments) else "default"
            mgr = NonStandaloneLSManager(
                workspace_id=ws_id,
                force_dummy=self.force_dummy,
                account=account,
            )
            try:
                ls_info = mgr.start()
                self.managers.append(mgr)
                self.ls_infos.append(ls_info)
                logger.info(f"LS {i} started: PID={ls_info.pid}, Port={ls_info.port}, Account='{account}'")
            except Exception as e:  # Intentional Catch-All (Daemon spawn)  # noqa: BLE001
                logger.error(f"Failed to start LS {i} (account={account}): {e}")
                self.stop()
                sys.exit(1)

        # 接続情報を JSON で書き出す (他プロセスがこれを読んで利用する)
        self._write_info()

        self._running = True
        try:
            self._loop()
        finally:
            # ループ終了 = 異常事態。クリーンアップして非ゼロ終了 (systemd Restart=on-failure を発火)
            self.stop()
            logger.error("LS Daemon pool exiting with code 1 for systemd restart.")
            sys.exit(1)

    def _load_accounts(self):
        """アカウントリストを vault.json から取得し、各 LS に割り当てる。"""
        try:
            from mekhane.ochema.token_vault import TokenVault
            vault = TokenVault()
            accounts = [a["name"] for a in vault.list_accounts()]
            if not accounts:
                accounts = ["default"]
        except Exception as e:  # Intentional Catch-All (Vault load)  # noqa: BLE001
            logger.warning(f"TokenVault 読み込み失敗、default のみ使用: {e}")
            accounts = ["default"]
        
        # アカウントをラウンドロビンで各 LS に割り当て
        self.account_assignments = []
        for i in range(self.num_instances):
            self.account_assignments.append(accounts[i % len(accounts)])

    def stop(self):
        """デーモンプール全体を停止する。"""
        logger.info("Stopping LS Daemon Pool...")
        self._running = False
        for mgr in self.managers:
            try:
                mgr.stop()
            except Exception as e:  # Intentional Catch-All (Manager stop)  # noqa: BLE001
                logger.error(f"Error stopping a manager: {e}")
                
        # 自分の source のエントリだけを削除し、他 source のエントリは保持する
        # (旧実装: unlink() でファイル全体を削除 → 他 source のエントリも消失するバグ)
        if DAEMON_INFO_PATH.exists():
            try:
                with open(DAEMON_INFO_PATH, "a+") as f:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        f.seek(0)
                        content = f.read().strip()
                        if content:
                            existing = json.loads(content)
                            remaining = [e for e in existing if e.get("source") != self.source]
                            f.seek(0)
                            f.truncate()
                            if remaining:
                                json.dump(remaining, f, indent=2)
                            logger.info(
                                f"Removed {self.source} entries from {DAEMON_INFO_PATH} "
                                f"({len(remaining)} entries remain)"
                            )
                        else:
                            # 空ファイルなら削除
                            f.seek(0)
                            f.truncate()
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            except Exception as e:  # Intentional Catch-All (File cleanup)  # noqa: BLE001
                logger.warning(f"Failed to clean {DAEMON_INFO_PATH}: {e}")
        self.managers.clear()
        self.ls_infos.clear()
        logger.info("LS Daemon Pool stopped.")

    def _write_info(self):
        """接続情報をマージ書き込みする。

        自分の source のエントリだけを置換し、他の source のエントリは保持する。
        これにより Docker LS とローカル LS が同じ ls_daemon.json を共有できる。
        fcntl.LOCK_EX でファイルレベルの排他ロックを使用し、read-modify-write の
        競合を防ぐ。
        """
        # fcntl はトップレベルで import 済み (stop() からも使用するため)

        DAEMON_INFO_PATH.parent.mkdir(parents=True, exist_ok=True)

        # 自分の source のエントリを構築
        my_entries: List[Dict[str, Any]] = []
        for idx, ls_info in enumerate(self.ls_infos):
            my_entries.append({
                "pid": ls_info.pid,
                "port": ls_info.port,
                "host": "127.0.0.1",
                "csrf": ls_info.csrf,
                "workspace": ls_info.workspace,
                "is_https": ls_info.is_https,
                "source": self.source,
                "account": self.account_assignments[idx] if idx < len(self.account_assignments) else "default",
                "updated_at": time.time(),
            })

        # ファイルロック付きで read-modify-write
        # "a+" で開くとファイルがなければ作成、あれば追記モードで開く
        # ロック取得後に seek(0) で先頭から read → truncate → write
        with open(DAEMON_INFO_PATH, "a+") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.seek(0)
                content = f.read().strip()
                existing: List[Dict[str, Any]] = []
                if content:
                    try:
                        existing = json.loads(content)
                    except json.JSONDecodeError:
                        logger.warning(f"Corrupted {DAEMON_INFO_PATH}, overwriting.")
                        existing = []

                # 他の source のエントリを保持
                other_entries = [e for e in existing if e.get("source") != self.source]

                # マージ: 他 source + 自分の source
                merged = other_entries + my_entries

                f.seek(0)
                f.truncate()
                json.dump(merged, f, indent=2)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        logger.info(
            f"Wrote {len(my_entries)} {self.source} instance(s) to {DAEMON_INFO_PATH} "
            f"(total {len(my_entries) + len(other_entries)} entries, "
            f"preserved {len(other_entries)} from other sources)"
        )

    def _loop(self):
        """メインループ: 全 LS プロセスの監視とポーリング"""
        # クライアントリストを作る
        clients = [AntigravityClient(ls_info=info) for info in self.ls_infos]
        fail_counts = [0] * len(clients)
        last_refresh = time.time()
        _token_refresh_unavailable = False

        while self._running:
            # プロセスが生きているか各々確認
            for idx, mgr in enumerate(self.managers):
                if not mgr._proc or mgr._proc.poll() is not None:
                    logger.error(f"LS process {idx} died unexpectedly. Exiting for systemd to restart.")
                    self._running = False
                    break
            
            if not self._running:
                break

            # 30分に1回アカウント別にトークンリフレッシュ
            if time.time() - last_refresh > 1800:
                logger.info("トークンリフレッシュ実行中 (%d LS インスタンス)...", len(self.managers))
                for idx, mgr in enumerate(self.managers):
                    try:
                        mgr.ensure_token_fresh()
                        logger.info(f"  LS {idx} ({mgr.account}): トークン更新OK")
                    except Exception as e:  # Intentional Catch-All (Token refresh)  # noqa: BLE001
                        logger.error(f"  LS {idx} ({mgr.account}): トークン更新失敗: {e}")
                last_refresh = time.time()

            # 1分に1回 GetStatus を呼んで死活監視する
            start_check = time.time()
            for idx, client in enumerate(clients):
                try:
                    client.get_status()
                    fail_counts[idx] = 0
                except Exception as e:  # Intentional Catch-All (Health check)  # noqa: BLE001
                    logger.warning(f"Health check failed for LS {idx}: {e}")
                    fail_counts[idx] += 1
                    if fail_counts[idx] >= 3:
                        logger.error(f"LS {idx} health check failed 3 times. Exiting.")
                        self._running = False
                        break
            
            if not self._running:
                break
                
            # Wait remainder of the minute
            elapsed = time.time() - start_check
            if elapsed < 60:
                time.sleep(60 - elapsed)


def main():
    parser = argparse.ArgumentParser(description="Non-Standalone LS Pool Daemon")
    parser.add_argument("--workspace", default="nonstd_hgk", help="Workspace filter prefix")
    parser.add_argument("--no-dummy", action="store_true", help="Do not force DummyExtServer")
    parser.add_argument("--instances", type=int, default=int(os.environ.get("HGK_LS_MAX_INSTANCES", "4")), help="Number of LS instances to start in the pool")
    parser.add_argument("--source", default=os.environ.get("LS_SOURCE", "local"),
                        choices=["local", "docker"],
                        help="source タグ (default: local, Docker 環境では 'docker' を指定)")
    args = parser.parse_args()

    daemon = LSPoolDaemon(
        workspace_prefix=args.workspace,
        num_instances=args.instances,
        force_dummy=not args.no_dummy,
        source=args.source,
    )

    def handle_sigterm(signum, frame):
        logger.info(f"Received signal {signum}")
        daemon.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    daemon.start()


if __name__ == "__main__":
    import sys
    # When running directly, ensure imports work
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    main()
