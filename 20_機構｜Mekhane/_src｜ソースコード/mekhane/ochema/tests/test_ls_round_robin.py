#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/ochema/tests/ テスト
# PURPOSE: LS アカウントラウンドロビン機能のユニットテスト
"""LS Account Round-Robin tests.

TokenVault.get_ls_account_round_robin() と provision_state_db(account=...) の
ユニットテスト。

Run:
    cd ~/oikos/01_ヘゲモニコン｜Hegemonikon && \
    PYTHONPATH="20_機構｜Mekhane/_src｜ソースコード" .venv/bin/python -m pytest \
        "20_機構｜Mekhane/_src｜ソースコード/mekhane/ochema/tests/test_ls_round_robin.py" -v
"""


from __future__ import annotations
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mekhane.ochema.token_vault import TokenVault


# ── テスト用 fixtures ──


@pytest.fixture
def vault(tmp_path: Path):
    """3アカウント構成の TokenVault を返す (既存テストと同じパターン)。"""
    import mekhane.ochema.token_vault as tv

    # モジュールレベルパスをオーバーライド
    orig_vault_dir = tv._VAULT_DIR
    orig_vault_file = tv._VAULT_FILE
    orig_tokens_dir = tv._TOKENS_DIR
    orig_oauth = tv._OAUTH_CONFIG

    tv._VAULT_DIR = tmp_path
    tv._VAULT_FILE = tmp_path / "vault.json"
    tv._TOKENS_DIR = tmp_path / "tokens"
    tv._OAUTH_CONFIG = tmp_path / "oauth.json"

    # OAuth 設定を作成
    (tmp_path / "oauth.json").write_text(json.dumps({
        "client_id": "test-client-id",
        "client_secret": "test-secret"
    }))

    # トークンディレクトリ
    (tmp_path / "tokens").mkdir()

    # 3アカウントを作成
    for name in ["alpha", "bravo", "charlie"]:
        (tmp_path / "tokens" / f"{name}.json").write_text(json.dumps({
            "refresh_token": f"fake-refresh-{name}"
        }))

    # vault.json を作成
    (tmp_path / "vault.json").write_text(json.dumps({
        "default_account": "alpha",
        "accounts": {
            "alpha": {"email": "a@test.com", "creds_file": "alpha.json", "source": "test"},
            "bravo": {"email": "b@test.com", "creds_file": "bravo.json", "source": "test"},
            "charlie": {"email": "c@test.com", "creds_file": "charlie.json", "source": "test"},
        }
    }))

    v = TokenVault()

    yield v

    # 復元
    tv._VAULT_DIR = orig_vault_dir
    tv._VAULT_FILE = orig_vault_file
    tv._TOKENS_DIR = orig_tokens_dir
    tv._OAUTH_CONFIG = orig_oauth


# ── get_ls_account_round_robin テスト ──


class TestLsRoundRobin:
    """LS 用ラウンドロビンのコアロジック検証。"""

    def test_cycles_through_accounts(self, vault: TokenVault):
        """3アカウントを順番に巡回すること。"""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            seen = []
            for _ in range(6):
                _token, acct = vault.get_ls_account_round_robin()
                seen.append(acct)

            # 6回で alpha, bravo, charlie を2周
            assert seen == ["alpha", "bravo", "charlie", "alpha", "bravo", "charlie"]

    def test_independent_from_cortex_rr(self, vault: TokenVault):
        """LS RR インデックスは Cortex RR インデックスと独立であること。"""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            # Cortex RR を3回回す
            for _ in range(3):
                vault.get_token_round_robin()

            # LS RR の1回目は最初のアカウントから始まるべき
            _token, ls_first = vault.get_ls_account_round_robin()
            assert ls_first == "alpha", \
                f"LS RR は Cortex RR に影響されず alpha から始まるべき。実際: {ls_first}"

    def test_skips_rate_limited(self, vault: TokenVault):
        """レートリミット中のアカウントをスキップすること。"""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            # alpha をレートリミット
            vault.mark_rate_limited("alpha", cooldown=300)

            # 次の3回の結果に alpha は含まれない
            results = []
            for _ in range(3):
                _token, acct = vault.get_ls_account_round_robin()
                results.append(acct)
            assert "alpha" not in results, \
                f"レートリミット中の alpha がスキップされるべき。実際: {results}"

    def test_excludes_accounts(self, vault: TokenVault):
        """exclude パラメータで指定されたアカウントを除外すること。"""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            # alpha と bravo を exclude → charlie のみ
            _token, result = vault.get_ls_account_round_robin(exclude=["alpha", "bravo"])
            assert result == "charlie", \
                f"exclude されたアカウントを避けて charlie を返すべき。実際: {result}"

    def test_all_rate_limited_returns_earliest_cooldown(self, vault: TokenVault):
        """全アカウントがレートリミットの場合、最早クールダウンのものを返す。"""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            vault.mark_rate_limited("alpha", cooldown=300)
            vault.mark_rate_limited("bravo", cooldown=100)  # 最短
            vault.mark_rate_limited("charlie", cooldown=200)

            _token, result = vault.get_ls_account_round_robin()
            assert result == "bravo", \
                f"最短クールダウンの bravo を返すべき。実際: {result}"


class TestProvisionStateDbAccount:
    """provision_state_db の account パラメータ検証。"""

    def test_account_parameter_passed_to_get_token(self, tmp_path: Path):
        """account パラメータが TokenVault.get_token に渡されること。

        provision_state_db() は内部で `from mekhane.ochema.token_vault import TokenVault`
        を lazy import する。patch 対象は token_vault モジュール側のクラス。
        """
        from mekhane.ochema.ls_manager import provision_state_db
        import sqlite3

        # テスト用 state.vscdb を作成
        db_path = tmp_path / "state.vscdb"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
            ("google.login.accessToken", '"old_token"'),
        )
        conn.commit()
        conn.close()

        mock_vault_instance = MagicMock()
        mock_vault_instance.get_token.return_value = "ya29.new_token_for_bravo"
        mock_vault_cls = MagicMock(return_value=mock_vault_instance)

        with patch("mekhane.ochema.token_vault.TokenVault", mock_vault_cls):
            provision_state_db(db_path=Path(db_path), account="bravo")

        # get_token が account="bravo" で呼ばれたか
        mock_vault_instance.get_token.assert_called_once_with("bravo")

    def test_default_none_uses_default_account(self, tmp_path: Path):
        """account=None の場合、get_token("default") が呼ばれること。"""
        from mekhane.ochema.ls_manager import provision_state_db
        import sqlite3

        db_path = tmp_path / "state.vscdb"
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
            ("google.login.accessToken", '"old_token"'),
        )
        conn.commit()
        conn.close()

        mock_vault_instance = MagicMock()
        mock_vault_instance.get_token.return_value = "ya29.default_token"
        mock_vault_cls = MagicMock(return_value=mock_vault_instance)

        with patch("mekhane.ochema.token_vault.TokenVault", mock_vault_cls):
            provision_state_db(db_path=Path(db_path))

        # デフォルト引数 "default" で呼ばれるべき
        mock_vault_instance.get_token.assert_called_once_with("default")
