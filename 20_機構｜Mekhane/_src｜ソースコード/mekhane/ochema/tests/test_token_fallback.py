#!/usr/bin/env python3
# PROOF: [L2/テスト] <- mekhane/ochema/tests/ テスト
# PURPOSE: _get_token() のフォールバック順序を検証するユニットテスト
"""Token fallback order tests.

Expected order:
    1. Instance cache
    2. File cache (/tmp)
    3. TokenVault (Primary)
    4. LS OAuth (state.vscdb)
    5. gemini-cli OAuth (last resort)
"""


from __future__ import annotations
import time
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture
def fresh_client():
    """Create a CortexClient with no cached token."""
    from mekhane.ochema.cortex_client import CortexClient
    client = CortexClient()
    client._auth._token = None
    client._auth._account = "default"
    return client


class TestTokenFallbackOrder:

    def test_vault_tried_before_ls_oauth(self, fresh_client):
        """TokenVault should be attempted before LS OAuth."""
        call_order = []

        def mock_vault_get(account):
            call_order.append("vault")
            return "vault_token_value"

        def mock_ls_token(self_):
            call_order.append("ls_oauth")
            return "ya29.ls_token_value"

        from mekhane.ochema.cortex_auth import CortexAuth
        with patch.object(fresh_client._auth.vault, 'get_token', mock_vault_get), \
             patch.object(CortexAuth, '_get_ls_token', mock_ls_token), \
             patch('mekhane.ochema.cortex_auth._TOKEN_CACHE', MagicMock(exists=lambda: False)):
            token = fresh_client._auth.get_token()

        assert token == "vault_token_value"
        assert call_order == ["vault"], f"Expected Vault first, got: {call_order}"

    def test_ls_oauth_tried_after_vault_fails(self, fresh_client):
        """LS OAuth should be tried when TokenVault fails."""
        call_order = []

        def mock_vault_get(account):
            call_order.append("vault")
            raise Exception("vault fail")

        def mock_ls_token(self_):
            call_order.append("ls_oauth")
            return "ya29.ls_token_value"

        from mekhane.ochema.cortex_auth import CortexAuth
        with patch.object(fresh_client._auth.vault, 'get_token', mock_vault_get), \
             patch.object(CortexAuth, '_get_ls_token', mock_ls_token), \
             patch('mekhane.ochema.cortex_auth._TOKEN_CACHE', MagicMock(exists=lambda: False)):
            token = fresh_client._auth.get_token()

        assert token == "ya29.ls_token_value"
        assert call_order == ["vault", "ls_oauth"]

    def test_gemini_cli_is_last_resort(self, fresh_client):
        """gemini-cli OAuth should only be tried after Vault and LS fail."""
        call_order = []

        def mock_vault_get(account):
            call_order.append("vault")
            raise Exception("vault fail")

        def mock_ls_token(self_):
            call_order.append("ls_oauth")
            return None

        def mock_refresh(self_):
            call_order.append("gemini_cli")
            return "gemini_cli_token"

        mock_creds = MagicMock()
        mock_creds.exists.return_value = True

        from mekhane.ochema.cortex_auth import CortexAuth
        with patch.object(fresh_client._auth.vault, 'get_token', mock_vault_get), \
             patch.object(CortexAuth, '_get_ls_token', mock_ls_token), \
             patch.object(CortexAuth, '_refresh_gemini_cli_token', mock_refresh), \
             patch('mekhane.ochema.cortex_auth._CREDS_FILE', mock_creds), \
             patch('mekhane.ochema.cortex_auth._TOKEN_CACHE', MagicMock(exists=lambda: False)):
            token = fresh_client._auth.get_token()

        assert token == "gemini_cli_token"
        assert call_order == ["vault", "ls_oauth", "gemini_cli"]

    def test_cache_hit_skips_all(self, fresh_client):
        """File cache hit should skip vault, LS, and gemini-cli."""
        fresh_client._auth._token = "cached_token"

        mock_cache = MagicMock()
        mock_cache.exists.return_value = True
        mock_cache.stat.return_value = MagicMock(st_mtime=time.time())

        with patch('mekhane.ochema.cortex_auth._TOKEN_CACHE', mock_cache):
            token = fresh_client._auth.get_token()

        assert token == "cached_token"

    def test_ls_token_cached_to_file(self, fresh_client):
        """LS OAuth token should be written to file cache for performance."""
        mock_cache = MagicMock()
        mock_cache.exists.return_value = False

        def mock_vault_get(account):
            raise Exception("vault fail")

        def mock_ls_token(self_):
            return "ya29.a0Aa7MY"

        from mekhane.ochema.cortex_auth import CortexAuth
        with patch.object(fresh_client._auth.vault, 'get_token', mock_vault_get), \
             patch.object(CortexAuth, '_get_ls_token', mock_ls_token), \
             patch('mekhane.ochema.cortex_auth._TOKEN_CACHE', mock_cache):
            token = fresh_client._auth.get_token()

        assert token == "ya29.a0Aa7MY"
        mock_cache.write_text.assert_called_once_with("ya29.a0Aa7MY")
        mock_cache.chmod.assert_called_once_with(0o600)

    def test_all_fail_raises_auth_error(self, fresh_client):
        """CortexAuthError should be raised if all fail."""
        from mekhane.ochema.cortex_client import CortexAuthError

        def mock_vault_get(account):
            raise Exception("vault fail")

        def mock_ls_token(self_):
            return None

        mock_creds = MagicMock()
        mock_creds.exists.return_value = False

        from mekhane.ochema.cortex_auth import CortexAuth
        with patch.object(fresh_client._auth.vault, 'get_token', mock_vault_get), \
             patch.object(CortexAuth, '_get_ls_token', mock_ls_token), \
             patch('mekhane.ochema.cortex_auth._CREDS_FILE', mock_creds), \
             patch('mekhane.ochema.cortex_auth._TOKEN_CACHE', MagicMock(exists=lambda: False)):
            with pytest.raises(CortexAuthError):
                fresh_client._auth.get_token()
