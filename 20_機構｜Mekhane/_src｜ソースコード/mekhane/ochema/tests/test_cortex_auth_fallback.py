# PROOF: mekhane/ochema/tests/test_cortex_auth_fallback.py
# PURPOSE: ochema モジュールの cortex_auth_fallback に対するテスト
"""CortexAuth non-default fallback テスト (mock-based)."""
from __future__ import annotations
import pytest
from unittest.mock import patch, MagicMock
from mekhane.ochema.cortex_auth import CortexAuth


class TestNonDefaultFallback:
    """non-default アカウントの LS OAuth フォールバックテスト。"""

    def test_vault_success_no_fallback(self):
        """TokenVault が成功する場合、フォールバックしない。"""
        auth = CortexAuth(account="movement")
        mock_vault = MagicMock()
        mock_vault.get_token.return_value = "ya29.vault_token"
        auth._vault = mock_vault

        token = auth.get_token()
        assert token == "ya29.vault_token"
        mock_vault.get_token.assert_called_once_with("movement")

    def test_vault_fails_ls_fallback(self, tmp_path):
        """TokenVault が失敗した場合、LS OAuth にフォールバックする。"""
        auth = CortexAuth(account="movement")
        mock_vault = MagicMock()
        mock_vault.get_token.side_effect = Exception("アカウント 'movement' が見つかりません")
        auth._vault = mock_vault

        # LS OAuth のモック
        with patch.object(auth, "_get_ls_token", return_value="ya29.ls_fallback_token"):
            # _TOKEN_CACHE を tmp_path に差し替え
            with patch("mekhane.ochema.cortex_auth._TOKEN_CACHE", tmp_path / "cache"):
                token = auth.get_token()
                assert token == "ya29.ls_fallback_token"

    def test_vault_and_ls_both_fail(self):
        """TokenVault も LS OAuth も失敗した場合、CortexAuthError。"""
        from mekhane.ochema.cortex_client import CortexAuthError

        auth = CortexAuth(account="movement")
        mock_vault = MagicMock()
        mock_vault.get_token.side_effect = Exception("アカウント未登録")
        auth._vault = mock_vault

        with patch.object(auth, "_get_ls_token", return_value=None):
            with pytest.raises(CortexAuthError, match="TokenVault \\+ LS OAuth 両方失敗"):
                auth.get_token()

    def test_auto_account_uses_round_robin(self):
        """account='auto' の場合、vault の round-robin を使う。"""
        auth = CortexAuth(account="auto")
        mock_vault = MagicMock()
        mock_vault.get_token_round_robin.return_value = ("ya29.rr_token", "acct_b")
        auth._vault = mock_vault

        token = auth.get_token()
        assert token == "ya29.rr_token"
        assert auth.account == "acct_b"
