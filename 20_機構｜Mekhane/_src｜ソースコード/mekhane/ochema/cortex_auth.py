# PROOF: [L2/インフラ] <- mekhane/ochema/cortex_auth.py A0→外部LLM接続→Cortex 認証層
# PURPOSE: Cortex API のトークン取得・リフレッシュ・キャッシュを管理する認証層。
#   CortexClient から委譲される。
"""CortexAuth — Authentication layer for Cortex API.

Handles OAuth token lifecycle:
- LS OAuth capture from state.vscdb
- TokenVault multi-account support
- gemini-cli OAuth refresh (fallback)
- Token caching (55 min TTL)

DX-010 §J: Three-layer auth (OAuth + apiKey + dynamic projectId)
"""
from __future__ import annotations
from typing import Any, Optional

import json
import logging
import sqlite3
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

# --- Auth Constants ---

import os
import platform

# OAuth credentials loaded from external config (not in source)
_OAUTH_CONFIG = Path.home() / ".config" / "cortex" / "oauth.json"
_CREDS_FILE = Path.home() / ".gemini" / "oauth_creds.json"

if platform.system() == "Windows":
    _LS_STATE_DB = Path(os.environ.get("APPDATA", "")) / "Antigravity" / "User" / "globalStorage" / "state.vscdb"
else:
    _LS_STATE_DB = Path.home() / ".config" / "Antigravity" / "User" / "globalStorage" / "state.vscdb"

_TOKEN_CACHE = Path(tempfile.gettempdir()) / ".cortex_token_cache"
_TOKEN_TTL = 3300  # 55 minutes (access_token expires in 60 min)
_TOKEN_URL = "https://oauth2.googleapis.com/token"

# DX-010 §J: Authentication Three-Layer Structure
AUTH_LAYERS = ("oauth_token", "api_key", "dynamic_project_id")


# PURPOSE: gemini-cli OAuth 設定ファイルからクライアント情報を読み込む (非推奨)
def _load_oauth_config() -> tuple[str, str]:
    """Load OAuth client_id and client_secret from external config.

    .. deprecated::
        LS OAuth is now the primary authentication source.
        oauth.json is only needed as a last-resort fallback for gemini-cli.
    """
    if not _OAUTH_CONFIG.exists():
        raise FileNotFoundError(
            f"OAuth 設定ファイルが見つかりません: {_OAUTH_CONFIG}\n"
            "注: LS OAuth が推奨です。Antigravity IDE が起動中であれば oauth.json は不要です。"
        )
    import warnings
    warnings.warn(
        "oauth.json は非推奨です。LS OAuth (Antigravity IDE) の使用を推奨します。",
        DeprecationWarning,
        stacklevel=2,
    )
    data = json.loads(_OAUTH_CONFIG.read_text())
    return data["client_id"], data["client_secret"]


# PURPOSE: Cortex API のトークン取得・キャッシュ・リフレッシュを集約した認証クラス
class CortexAuth:
    """Authentication manager for Cortex API.

    Token priority (default account):
        1. Instance cache (in-memory)
        2. File cache (tempdir/.cortex_token_cache)
        3. LS OAuth capture (state.vscdb) ← most reliable in IDE
        4. TokenVault (multi-account, internal caching)
        5. gemini-cli OAuth refresh (last resort)
    """

    def __init__(self, account: str = "default", cooldown_manager: Optional[Any] = None):
        self._account = account
        self._current_account: str = account
        self._token: Optional[str] = None
        self._prev_token: Optional[str] = None
        self._vault: Optional[Any] = None
        self._cooldown_manager = cooldown_manager
        # Callback: called when token changes (for project cache invalidation)
        self._on_token_change: Optional[callable] = None

    @property
    def account(self) -> str:
        """Currently active account name."""
        return self._current_account

    @property
    def vault(self) -> Any:
        """Get or create TokenVault instance."""
        if self._vault is None:
            from mekhane.ochema.token_vault import TokenVault
            self._vault = TokenVault(cooldown_manager=self._cooldown_manager)
        return self._vault

    # PURPOSE: トークン変更時にプロジェクトキャッシュを無効化する
    def set_token(self, new_token: str) -> None:
        """Set token and notify listeners if token changed."""
        if self._prev_token and new_token != self._prev_token:
            logger.debug("Token changed, invalidating caches")
            if self._on_token_change:
                self._on_token_change()
        self._token = new_token
        self._prev_token = new_token

    # PURPOSE: 優先順位に従ってアクセストークンを取得する
    def get_token(self) -> str:
        """Get access token (cached for 55 min).

        Returns:
            OAuth access token string.

        Raises:
            CortexAuthError: if no authentication source is available.
        """
        from mekhane.ochema.cortex_client import CortexAuthError

        # Auto mode: use round-robin across all accounts
        if self._account == "auto":
            token, acct = self.vault.get_token_round_robin()
            self._current_account = acct
            self._token = token
            return token

        # Non-default アカウント: TokenVault → LS OAuth フォールバック
        if self._account != "default":
            try:
                token = self.vault.get_token(self._account)
                self._token = token
                return token
            except Exception as vault_err:  # noqa: BLE001
                logger.warning(
                    "TokenVault failed for '%s': %s", self._account, vault_err
                )
                # フォールバック: LS OAuth (quota 分離不可だが 403 よりマシ)
                ls_token = self._get_ls_token()
                if ls_token:
                    logger.warning(
                        "Falling back to LS OAuth for '%s' (quota分離なし)",
                        self._account,
                    )
                    self.set_token(ls_token)
                    _TOKEN_CACHE.write_text(ls_token)
                    _TOKEN_CACHE.chmod(0o600)
                    return self._token
                raise CortexAuthError(
                    f"アカウント '{self._account}' のトークン取得に失敗 "
                    f"(TokenVault + LS OAuth 両方失敗): {vault_err}"
                )

        # --- default account below ---

        # Check instance cache
        if self._token:
            if _TOKEN_CACHE.exists():
                age = time.time() - _TOKEN_CACHE.stat().st_mtime
                if age < _TOKEN_TTL:
                    return self._token

        # Check file cache
        if _TOKEN_CACHE.exists():
            age = time.time() - _TOKEN_CACHE.stat().st_mtime
            if age < _TOKEN_TTL:
                self._token = _TOKEN_CACHE.read_text().strip()
                return self._token

        # Primary: TokenVault (active refresh flow, resilient in headless/remote)
        try:
            token = self.vault.get_token(self._account)
            self.set_token(token)
            _TOKEN_CACHE.write_text(token)
            _TOKEN_CACHE.chmod(0o600)
            return token
        except Exception as vault_err:  # noqa: BLE001
            logger.debug("TokenVault failed for '%s': %s", self._account, vault_err)

        # Secondary: LS OAuth (state.vscdb - passive, might be stale on remote)
        ls_token = self._get_ls_token()
        if ls_token:
            self.set_token(ls_token)
            _TOKEN_CACHE.write_text(ls_token)
            _TOKEN_CACHE.chmod(0o600)
            return self._token

        # Last resort: gemini-cli OAuth refresh
        if _CREDS_FILE.exists():
            try:
                return self._refresh_gemini_cli_token()
            except CortexAuthError:
                logger.warning("gemini-cli OAuth refresh failed")

        raise CortexAuthError(
            "認証ソースがありません。以下のいずれかが必要:\n"
            "  1. Antigravity IDE が起動中 (LS OAuth)\n"
            "  2. TokenVault にアカウントを追加\n"
            "  3. gemini-cli: npx @google/gemini-cli --prompt 'hello'"
        )

    # PURPOSE: gemini-cli OAuth で refresh_token からアクセストークンを再取得する
    def _refresh_gemini_cli_token(self) -> str:
        """Refresh token via gemini-cli OAuth credentials."""
        from mekhane.ochema.cortex_client import CortexAuthError

        try:
            creds = json.loads(_CREDS_FILE.read_text())
            refresh_token = creds["refresh_token"]
        except (json.JSONDecodeError, KeyError) as e:
            raise CortexAuthError(f"oauth_creds.json の解析に失敗: {e}")

        client_id, client_secret = _load_oauth_config()
        data = urllib.parse.urlencode(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        ).encode("utf-8")

        try:
            req = urllib.request.Request(_TOKEN_URL, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                self._token = result["access_token"]
        except (urllib.error.HTTPError, KeyError, json.JSONDecodeError) as e:
            raise CortexAuthError(f"Token refresh 失敗: {e}")

        # Save cache
        _TOKEN_CACHE.write_text(self._token)
        _TOKEN_CACHE.chmod(0o600)
        return self._token

    # PURPOSE: LS の state.vscdb から OAuth トークンを直接キャプチャする
    def _get_ls_token(self) -> Optional[str]:
        """Capture OAuth token from Antigravity LS state database."""
        if not _LS_STATE_DB.exists():
            logger.debug("LS state DB not found: %s", _LS_STATE_DB)
            return None

        import shutil
        import tempfile
        import os

        # DANGER: IDE may lock the db. Reading it directly hangs Python in sqlite3 C-extension.
        # FIX: Copy the file to a temp location before reading.
        temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".vscdb")
        os.close(temp_db_fd)
        try:
            shutil.copy2(_LS_STATE_DB, temp_db_path)
            
            db = sqlite3.connect(
                f"file:{temp_db_path}?mode=ro",
                uri=True,
                timeout=1.0,
            )
            row = db.execute(
                "SELECT value FROM ItemTable WHERE key = ?",
                ("antigravityAuthStatus",),
            ).fetchone()
            db.close()

            if not row:
                logger.debug("antigravityAuthStatus key not found in state DB")
                return None

            data = json.loads(row[0])
            token = data.get("apiKey", "")
            if token and token.startswith("ya29."):
                logger.info("LS OAuth token captured (email: %s)", data.get("email", "?"))
                return token

            logger.debug("LS token format unexpected: %s...", str(token)[:10])
            return None

        except (sqlite3.Error, json.JSONDecodeError, KeyError) as e:
            logger.warning("LS OAuth 取得失敗: %s", e)
            return None

    # PURPOSE: DX-010 §J の3層認証が全て利用可能かを検証する
    def validate_auth_chain(self, get_project_fn=None) -> dict[str, bool]:
        """Validate that all three authentication layers are available.

        Args:
            get_project_fn: Optional callable to check project ID availability.

        Returns:
            Dict mapping AUTH_LAYERS names to availability status.
        """
        status: dict[str, bool] = {layer: False for layer in AUTH_LAYERS}
        try:
            token = self.get_token()
            status["oauth_token"] = bool(token)
        except (OSError, json.JSONDecodeError, AttributeError) as _e:
            logger.debug("Ignored exception: %s", _e)
        status["api_key"] = True
        try:
            if status["oauth_token"] and get_project_fn:
                project = get_project_fn(self.get_token())
                status["dynamic_project_id"] = bool(project)
        except (OSError, json.JSONDecodeError, AttributeError) as _e:
            logger.debug("Ignored exception: %s", _e)
        return status
