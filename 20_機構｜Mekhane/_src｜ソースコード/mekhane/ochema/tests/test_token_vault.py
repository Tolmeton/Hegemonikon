# PROOF: mekhane/ochema/tests/test_token_vault.py
# PURPOSE: ochema モジュールの token_vault に対するテスト
"""TokenVault Round-Robin tests (mock-based, no API calls)."""
from __future__ import annotations
import pytest
from unittest.mock import patch
from pathlib import Path
from mekhane.ochema.token_vault import TokenVault


@pytest.fixture
def vault(tmp_path: Path):
    """Create a TokenVault with mocked file paths and 3 test accounts."""
    import json
    import mekhane.ochema.token_vault as tv
    
    # Override module-level paths
    orig_vault_dir = tv._VAULT_DIR
    orig_vault_file = tv._VAULT_FILE
    orig_tokens_dir = tv._TOKENS_DIR
    orig_oauth = tv._OAUTH_CONFIG
    
    tv._VAULT_DIR = tmp_path
    tv._VAULT_FILE = tmp_path / "vault.json"
    tv._TOKENS_DIR = tmp_path / "tokens"
    tv._OAUTH_CONFIG = tmp_path / "oauth.json"
    
    # Create oauth config
    (tmp_path / "oauth.json").write_text(json.dumps({
        "client_id": "test-client-id",
        "client_secret": "test-secret"
    }))
    
    # Create tokens dir
    (tmp_path / "tokens").mkdir()
    
    # Create 3 test accounts with fake refresh tokens
    for name in ["acct_a", "acct_b", "acct_c"]:
        (tmp_path / "tokens" / f"{name}.json").write_text(json.dumps({
            "refresh_token": f"fake-refresh-{name}"
        }))
    
    # Create vault.json
    (tmp_path / "vault.json").write_text(json.dumps({
        "default_account": "acct_a",
        "accounts": {
            "acct_a": {"email": "a@test.com", "creds_file": "acct_a.json", "source": "test"},
            "acct_b": {"email": "b@test.com", "creds_file": "acct_b.json", "source": "test"},
            "acct_c": {"email": "c@test.com", "creds_file": "acct_c.json", "source": "test"},
        }
    }))
    
    v = TokenVault()
    
    yield v
    
    # Restore
    tv._VAULT_DIR = orig_vault_dir
    tv._VAULT_FILE = orig_vault_file
    tv._TOKENS_DIR = orig_tokens_dir
    tv._OAUTH_CONFIG = orig_oauth


class TestRoundRobin:
    def test_cycles_through_accounts(self, vault: TokenVault):
        """Round-robin should cycle through all accounts."""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            accounts_used = []
            for _ in range(6):
                _token, acct = vault.get_token_round_robin()
                accounts_used.append(acct)
            
            # Should cycle: a, b, c, a, b, c
            assert accounts_used == ["acct_a", "acct_b", "acct_c", "acct_a", "acct_b", "acct_c"]

    def test_skips_rate_limited(self, vault: TokenVault):
        """Rate-limited accounts should be skipped."""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            vault.mark_rate_limited("acct_b", cooldown=60)
            
            accounts_used = []
            for _ in range(4):
                _token, acct = vault.get_token_round_robin()
                accounts_used.append(acct)
            
            # acct_b should be skipped (in cooldown)
            assert "acct_b" not in accounts_used
            assert set(accounts_used) == {"acct_a", "acct_c"}

    def test_call_counts(self, vault: TokenVault):
        """Call counts should track usage."""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            for _ in range(5):
                vault.get_token_round_robin()
            
            counts = vault.get_call_counts()
            assert sum(counts.values()) == 5
            # Should be roughly balanced
            assert max(counts.values()) - min(counts.values()) <= 1

    def test_all_rate_limited_uses_earliest(self, vault: TokenVault):
        """When all accounts are rate-limited, use the one expiring soonest."""
        with patch.object(vault, '_refresh_token', return_value='fake-access-token'):
            # Mark all accounts with different cooldown durations
            vault.mark_rate_limited("acct_a", cooldown=120)  # 2 min
            vault.mark_rate_limited("acct_b", cooldown=30)   # 30 sec (earliest)
            vault.mark_rate_limited("acct_c", cooldown=90)   # 1.5 min
            
            _token, acct = vault.get_token_round_robin()
            assert acct == "acct_b"  # earliest cooldown
