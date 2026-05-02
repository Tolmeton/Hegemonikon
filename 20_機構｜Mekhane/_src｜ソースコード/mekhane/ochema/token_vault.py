# PROOF: [L2/インフラ] <- mekhane/ochema/token_vault.py A0→多アカウント OAuth トークン管理
# PURPOSE: TokenVault — 複数 Google OAuth アカウントのトークンを管理・切替する
from __future__ import annotations
from typing import Any, Optional
"""TokenVault — Multi-account OAuth token management.

Manages multiple Google OAuth refresh tokens for Cortex API access.
Each account has independent credentials and can be used simultaneously.

Usage:
    from mekhane.ochema.token_vault import TokenVault

    vault = TokenVault()
    token = vault.get_token("default")    # Default gemini-cli account
    token = vault.get_token("work")       # Work account

    vault.add_account("work", Path("~/.gemini/oauth_creds_work.json"))
    vault.list_accounts()
    vault.set_default("work")

Storage:
    ~/.config/ochema/
    ├── vault.json          # Account registry + metadata
    └── tokens/
        ├── default.json    # Default (gemini-cli) credentials
        └── work.json       # Additional account credentials
"""

import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from mekhane.ochema.model_fallback import CooldownManager, ErrorKind

logger = logging.getLogger(__name__)

# --- Constants ---

_VAULT_DIR = Path.home() / ".config" / "ochema"
_VAULT_FILE = _VAULT_DIR / "vault.json"
_TOKENS_DIR = _VAULT_DIR / "tokens"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_OAUTH_CONFIG = Path.home() / ".config" / "cortex" / "oauth.json"
_GEMINI_CLI_CREDS = Path.home() / ".gemini" / "oauth_creds.json"
_TOKEN_TTL = 3300  # 55 minutes


# --- Exceptions ---


# PURPOSE: [L2-auto] VaultError のクラス定義
class VaultError(Exception):
    """TokenVault error."""
    pass


# PURPOSE: [L2-auto] VaultAuthError のクラス定義
class VaultAuthError(VaultError):
    """Authentication error for a specific account."""
    pass


# --- TokenVault ---


# PURPOSE: [L2-auto] TokenVault のクラス定義
class TokenVault:
    """Multi-account OAuth token manager.

    Stores refresh tokens for multiple Google accounts and provides
    access tokens with caching and auto-refresh.

    Thread-safe for concurrent access to different accounts.
    Not thread-safe for mutations (add/remove/set_default).
    """

    # PURPOSE: [L2-auto] __init__ の関数定義
    def __init__(self, cooldown_manager: Optional[CooldownManager] = None) -> None:
        """Initialize vault. Creates directory structure if needed.
        
        Args:
            cooldown_manager: Optional shared CooldownManager instance.
        """
        self._cache: dict[str, tuple[str, float]] = {}  # account -> (token, expiry)
        self._vault_data: Optional[dict[str, Any]] = None
        self._oauth_config: Optional[tuple[str, str]] = None
        # Round-robin state (Cortex 用と LS 用を独立管理)
        self._rr_index: int = 0
        self._ls_rr_index: int = 0
        self._call_count: dict[str, int] = {}  # account -> call count
        # T-08: CooldownManager handles all cooldown/probe state
        self._cooldown = cooldown_manager if cooldown_manager is not None else CooldownManager()
        # Energy budget (W3)
        self._usage: dict[str, dict[str, int]] = {}  # date -> {model: tokens}
        self._daily_budget: int = 0  # 0 = unlimited
        self._budget_file = _VAULT_DIR / "energy_budget.jsonl"

    # --- Public API ---

    # PURPOSE: [L2-auto] get_token の関数定義
    def get_token(self, account: str = "default") -> str:
        """Get a valid access token for the given account.

        Args:
            account: Account name ("default", "work", etc.)

        Returns:
            Valid OAuth access token (ya29.*)

        Raises:
            VaultError: Account not found
            VaultAuthError: Token refresh failed
        """
        # Resolve 'default' to actual default account name
        if account == "default":
            account = self.get_default_account()

        # Check cache
        if account in self._cache:
            token, expiry = self._cache[account]
            if time.time() < expiry:
                return token

        # Get refresh token for account
        vault = self._load_vault()
        acct_info = vault.get("accounts", {}).get(account)
        if not acct_info:
            # Auto-import default from gemini-cli if not registered
            if account == "default" and _GEMINI_CLI_CREDS.exists():
                self._auto_import_default()
                vault = self._load_vault(force=True)
                acct_info = vault.get("accounts", {}).get(account)

            if not acct_info:
                raise VaultError(
                    f"アカウント '{account}' が見つかりません。\n"
                    f"登録方法: vault.add_account('{account}', Path('/path/to/creds.json'))"
                )

        creds_file = _TOKENS_DIR / acct_info["creds_file"]
        if not creds_file.exists():
            raise VaultError(
                f"認証ファイルが見つかりません: {creds_file}"
            )

        try:
            creds = json.loads(creds_file.read_text())
            refresh_token = creds["refresh_token"]
        except (json.JSONDecodeError, KeyError) as e:
            raise VaultAuthError(f"認証ファイル解析エラー ({account}): {e}")

        # Refresh access token (トークンファイル内の client_id/secret を優先)
        token = self._refresh_token(
            refresh_token,
            client_id=creds.get("client_id"),
            client_secret=creds.get("client_secret"),
        )
        self._cache[account] = (token, time.time() + _TOKEN_TTL)
        return token

    # PURPOSE: [L2-auto] add_account の関数定義
    def add_account(
        self,
        name: str,
        creds_path: Path,
        email: str = "",
    ) -> dict[str, str]:
        """Add a new account to the vault.

        Args:
            name: Account name (e.g. "work", "personal")
            creds_path: Path to OAuth credentials file (with refresh_token)
            email: Optional email for display

        Returns:
            Account info dict

        Raises:
            VaultError: If account already exists or creds invalid
        """
        vault = self._load_vault()

        if name in vault.get("accounts", {}):
            raise VaultError(f"アカウント '{name}' は既に存在します")

        # Validate creds
        creds_path = Path(creds_path).expanduser()
        if not creds_path.exists():
            raise VaultError(f"認証ファイルが見つかりません: {creds_path}")

        try:
            creds = json.loads(creds_path.read_text())
            if "refresh_token" not in creds:
                raise VaultError("refresh_token が含まれていません")
        except json.JSONDecodeError as e:
            raise VaultError(f"認証ファイル解析エラー: {e}")

        # Copy creds to vault
        _TOKENS_DIR.mkdir(parents=True, exist_ok=True)
        dest = _TOKENS_DIR / f"{name}.json"
        dest.write_text(json.dumps(creds, indent=2))
        dest.chmod(0o600)

        # Detect email from creds if not provided
        if not email:
            email = creds.get("email", creds.get("account", ""))

        # Update vault
        acct_info = {
            "email": email,
            "source": "manual",
            "creds_file": f"{name}.json",
            "added_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        vault.setdefault("accounts", {})[name] = acct_info
        if not vault.get("default_account"):
            vault["default_account"] = name
        self._save_vault(vault)

        logger.info("Account added: %s (email=%s)", name, email or "?")
        return acct_info

    # PURPOSE: [L2-auto] remove_account の関数定義
    def remove_account(self, name: str) -> None:
        """Remove an account from the vault.

        Args:
            name: Account name to remove

        Raises:
            VaultError: If account doesn't exist or is the default
        """
        vault = self._load_vault()
        if name not in vault.get("accounts", {}):
            raise VaultError(f"アカウント '{name}' が見つかりません")

        if vault.get("default_account") == name:
            raise VaultError(
                f"デフォルトアカウント '{name}' は削除できません。"
                "先に set_default() で別のアカウントをデフォルトに設定してください。"
            )

        # Remove creds file
        creds_file = _TOKENS_DIR / vault["accounts"][name]["creds_file"]
        if creds_file.exists():
            creds_file.unlink()

        del vault["accounts"][name]
        self._save_vault(vault)

        # Clear cache
        self._cache.pop(name, None)
        logger.info("Account removed: %s", name)

    # PURPOSE: [L2-auto] list_accounts の関数定義
    def list_accounts(self) -> list[dict[str, Any]]:
        """List all registered accounts.

        Returns:
            List of account info dicts with name, email, is_default
        """
        vault = self._load_vault()
        default = vault.get("default_account", "")
        result = []
        for name, info in vault.get("accounts", {}).items():
            result.append({
                "name": name,
                "email": info.get("email", ""),
                "source": info.get("source", "unknown"),
                "is_default": name == default,
                "added_at": info.get("added_at", ""),
            })
        return result

    # PURPOSE: [L2-auto] set_default の関数定義
    def set_default(self, name: str) -> None:
        """Set the default account.

        Args:
            name: Account name to set as default
        """
        vault = self._load_vault()
        if name not in vault.get("accounts", {}):
            raise VaultError(f"アカウント '{name}' が見つかりません")

        vault["default_account"] = name
        self._save_vault(vault)
        logger.info("Default account set: %s", name)

    # PURPOSE: [L2-auto] get_default_account の関数定義
    def get_default_account(self) -> str:
        """Get the name of the default account."""
        vault = self._load_vault()
        return vault.get("default_account", "default")

    # PURPOSE: [L2-auto] get_token_with_failover の関数定義
    def get_token_with_failover(
        self,
        primary: str = "default",
    ) -> tuple[str, str]:
        """Get token with automatic failover to other accounts.

        Tries the primary account first. If it fails, iterates through
        all other registered accounts.

        Args:
            primary: Preferred account name

        Returns:
            (token, account_name) tuple — the token and which account provided it

        Raises:
            VaultError: If no account can provide a valid token
        """
        # Try primary first
        try:
            token = self.get_token(primary)
            return token, primary
        except (VaultError, VaultAuthError) as e:
            logger.warning("Primary account '%s' failed: %s", primary, e)

        # Failover: try all other accounts
        vault = self._load_vault()
        for name in vault.get("accounts", {}):
            if name == primary:
                continue
            try:
                token = self.get_token(name)
                logger.info("Failover: using account '%s' instead of '%s'", name, primary)
                return token, name
            except (VaultError, VaultAuthError) as e:
                logger.debug("Failover account '%s' also failed: %s", name, e)
                continue

        raise VaultError(
            f"全アカウントでトークン取得に失敗しました。"
            f"Primary: '{primary}', Total accounts: {len(vault.get('accounts', {}))}"
        )

    # --- T-08 Cooldown/Probe Strategy (delegated to CooldownManager) ---

    def get_token_round_robin(
        self,
        exclude: list[str] | None = None,
    ) -> tuple[str, str]:
        """Round-robin across all accounts. Returns (token, account_name).

        Skips accounts that are in rate-limit cooldown or in the exclude list.
        Uses CooldownManager for all cooldown/probe decisions.
        Tracks call count per account for stats.

        Args:
            exclude: Account names to skip (e.g. currently rate-limited account).

        Returns:
            (access_token, account_name) tuple

        Raises:
            VaultError: If no accounts are available
        """
        vault = self._load_vault()
        accounts = list(vault.get("accounts", {}).keys())
        if not accounts:
            raise VaultError("TokenVault にアカウントが登録されていません")

        exclude_set = set(exclude) if exclude else set()

        # Filter out cooldown-ed and excluded accounts
        # NOTE: Unlike model-level fallback, account-level round-robin always
        # skips cooldown-ed accounts. Probe is only attempted for the primary
        # (first) account when probe conditions are met.
        available = []
        for i, a in enumerate(accounts):
            if a in exclude_set:
                continue
            if not self._cooldown.is_in_cooldown(a):
                available.append(a)
            elif i == 0 and len(accounts) > 1:
                # Primary account in cooldown: delegate probe decision to CooldownManager
                if self._cooldown.should_probe_account(a):
                    self._cooldown.mark_probe(a)
                    available.append(a)
                    logger.debug("T-08 Probe: primary '%s' cooldown nearly expired, probing", a)

        if not available:
            # All accounts are excluded or in cooldown — use the one with earliest expiry
            fallback_candidates = [a for a in accounts if a not in exclude_set]
            if not fallback_candidates:
                fallback_candidates = accounts  # last resort: ignore exclude
            # Find the account with the earliest cooldown expiry
            def _expiry(acct: str) -> float:
                exp = self._cooldown.get_cooldown_expiry(acct)
                return exp if exp is not None else float("inf")
            earliest = min(fallback_candidates, key=_expiry)
            logger.warning("全アカウントがレート制限中。最短を使用: %s", earliest)
            available = [earliest]

        # Round-robin selection
        idx = self._rr_index % len(available)
        account = available[idx]
        self._rr_index += 1

        # Get token
        token = self.get_token(account)

        # Track call count
        self._call_count[account] = self._call_count.get(account, 0) + 1

        return token, account

    # PURPOSE: LS 用アカウントラウンドロビン (Cortex RR とインデックス独立)
    def get_ls_account_round_robin(
        self,
        exclude: list[str] | None = None,
    ) -> tuple[str, str]:
        """LS (Claude) 用のアカウントラウンドロビン。

        Cortex (Gemini) 用の get_token_round_robin と同じアカウントプールを使うが、
        ラウンドロビンインデックスは独立管理。LS と Cortex のリクエスト頻度が
        異なるため、インデックスを共有すると特定アカウントに偏る。

        Args:
            exclude: スキップするアカウント名のリスト

        Returns:
            (access_token, account_name) タプル

        Raises:
            VaultError: 利用可能なアカウントがない場合
        """
        vault = self._load_vault()
        accounts = list(vault.get("accounts", {}).keys())
        if not accounts:
            raise VaultError("TokenVault にアカウントが登録されていません")

        exclude_set = set(exclude) if exclude else set()

        # クールダウン中・除外リストのアカウントをフィルタ
        available = []
        for i, a in enumerate(accounts):
            if a in exclude_set:
                continue
            if not self._cooldown.is_in_cooldown(a):
                available.append(a)
            elif i == 0 and len(accounts) > 1:
                if self._cooldown.should_probe_account(a):
                    self._cooldown.mark_probe(a)
                    available.append(a)
                    logger.debug("LS RR Probe: primary '%s' cooldown nearly expired, probing", a)

        if not available:
            # 全アカウントがクールダウン中 — 最短 expiry のアカウントを使用
            fallback_candidates = [a for a in accounts if a not in exclude_set]
            if not fallback_candidates:
                fallback_candidates = accounts
            def _expiry(acct: str) -> float:
                exp = self._cooldown.get_cooldown_expiry(acct)
                return exp if exp is not None else float("inf")
            earliest = min(fallback_candidates, key=_expiry)
            logger.warning("LS RR: 全アカウントがレート制限中。最短を使用: %s", earliest)
            available = [earliest]

        # ラウンドロビン選択 (LS 専用インデックス)
        idx = self._ls_rr_index % len(available)
        account = available[idx]
        self._ls_rr_index += 1

        # トークン取得
        token = self.get_token(account)

        # 呼出回数の追跡 (LS/Cortex 共有カウンタ)
        self._call_count[account] = self._call_count.get(account, 0) + 1

        return token, account

    # PURPOSE: T-08 CooldownManager 委譲
    def mark_rate_limited(
        self,
        account: str,
        cooldown: int = 60,
        error_kind: str | ErrorKind = ErrorKind.RATE_LIMIT,
    ) -> None:
        """Mark an account as rate-limited for a cooldown period.

        Delegates to CooldownManager for all state management.

        Args:
            account: Account name that received 429
            cooldown: Seconds to wait before retrying this account
            error_kind: ErrorKind enum or legacy string ("rate_limit", "capacity", "auth", "billing")
        """
        # Convert legacy string to ErrorKind enum
        if isinstance(error_kind, str):
            _KIND_MAP = {
                "rate_limit": ErrorKind.RATE_LIMIT,
                "capacity": ErrorKind.RATE_LIMIT,  # server-level, treated as rate_limit
                "auth": ErrorKind.AUTH,
                "billing": ErrorKind.BILLING,
            }
            kind = _KIND_MAP.get(error_kind, ErrorKind.UNKNOWN)
        else:
            kind = error_kind

        self._cooldown.mark_cooldown(account, error_kind=kind, cooldown=float(cooldown))
        logger.warning(
            "Account '%s' rate-limited for %ds (%s)",
            account, cooldown, kind.value,
        )

    def get_rate_limit_kind(self, account: str) -> str:
        """Get the error kind that caused the rate limit for an account."""
        kind = self._cooldown.get_cooldown_error_kind(account)
        return kind.value if kind else "rate_limit"

    def is_rate_limited(self, account: str) -> bool:
        """Check if an account is currently in cooldown."""
        return self._cooldown.is_in_cooldown(account)

    # PURPOSE: [L2-auto] get_call_counts の関数定義
    def get_call_counts(self) -> dict[str, int]:
        """Get the call count per account (for monitoring)."""
        return dict(self._call_count)

    # --- Energy Budget (W3) ---

    # PURPOSE: [L2] record_usage — トークン消費を記録する (Nucleus 式 Budget Proxy)
    def record_usage(
        self,
        account: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
    ) -> dict[str, Any]:
        """Record token usage for budget tracking.

        Args:
            account: Account that was used
            model: Model name (e.g. "gemini-2.0-flash")
            prompt_tokens: Input token count
            completion_tokens: Output token count

        Returns:
            Current budget status after recording
        """
        today = time.strftime("%Y-%m-%d")
        total = prompt_tokens + completion_tokens

        # In-memory tracking
        if today not in self._usage:
            self._usage[today] = {}
        day_usage = self._usage[today]
        day_usage[model] = day_usage.get(model, 0) + total

        # Persistent JSONL log
        try:
            _VAULT_DIR.mkdir(parents=True, exist_ok=True)
            entry = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "account": account,
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total": total,
            }
            with open(self._budget_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning("Energy budget log error: %s", e)

        return self.get_budget_status()

    # PURPOSE: [L2] get_budget_status — 日次予算に対する消費状況を返す
    def get_budget_status(self) -> dict[str, Any]:
        """Get current energy budget status.

        Returns:
            {
                "date": str,
                "total_tokens": int,
                "by_model": {model: tokens, ...},
                "daily_budget": int,  # 0 = unlimited
                "usage_pct": float,   # 0.0-100.0+ (can exceed 100%)
                "level": "green" | "yellow" | "red" | "unlimited",
                "remaining": int | None,
            }
        """
        today = time.strftime("%Y-%m-%d")
        day_usage = self._usage.get(today, {})
        total = sum(day_usage.values())
        budget = self._daily_budget

        if budget <= 0:
            level = "unlimited"
            pct = 0.0
            remaining = None
        else:
            pct = (total / budget) * 100
            remaining = max(0, budget - total)
            if pct < 70:
                level = "green"
            elif pct < 90:
                level = "yellow"
            else:
                level = "red"

        return {
            "date": today,
            "total_tokens": total,
            "by_model": dict(day_usage),
            "daily_budget": budget,
            "usage_pct": float(f"{pct:.1f}"),
            "level": level,
            "remaining": remaining,
        }

    # PURPOSE: [L2] set_budget — 日次トークン予算を設定する
    def set_budget(self, daily_limit: int = 0) -> None:
        """Set daily token budget.

        Args:
            daily_limit: Max tokens per day. 0 = unlimited.
        """
        self._daily_budget = max(0, daily_limit)
        logger.info("Daily budget set: %d tokens", self._daily_budget)

    # PURPOSE: [L2-auto] get_project の関数定義
    def get_project(self, account: str = "default") -> Optional[str]:
        """Get the project ID for an account (if cached)."""
        vault = self._load_vault()
        acct = vault.get("accounts", {}).get(account, {})
        return acct.get("project")

    # PURPOSE: [L2-auto] set_project の関数定義
    def set_project(self, account: str, project: str) -> None:
        """Cache the project ID for an account."""
        vault = self._load_vault()
        if account in vault.get("accounts", {}):
            vault["accounts"][account]["project"] = project
            self._save_vault(vault)

    # --- Private Methods ---

    # PURPOSE: [L2-auto] _load_vault の関数定義
    def _load_vault(self, force: bool = False) -> dict[str, Any]:
        """Load vault data from disk (cached)."""
        if self._vault_data is not None and not force:
            return self._vault_data

        if _VAULT_FILE.exists():
            try:
                self._vault_data = json.loads(_VAULT_FILE.read_text())
            except json.JSONDecodeError:
                logger.warning("vault.json 破損 — 初期化します")
                self._vault_data = {"default_account": "default", "accounts": {}}
        else:
            self._vault_data = {"default_account": "default", "accounts": {}}

        return self._vault_data

    # PURPOSE: [L2-auto] _save_vault の関数定義
    def _save_vault(self, data: dict[str, Any]) -> None:
        """Save vault data to disk."""
        _VAULT_DIR.mkdir(parents=True, exist_ok=True)
        _VAULT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        _VAULT_FILE.chmod(0o600)
        self._vault_data = data

    # PURPOSE: [L2-auto] _auto_import_default の関数定義
    def _auto_import_default(self) -> None:
        """Auto-import gemini-cli credentials as 'default' account."""
        if not _GEMINI_CLI_CREDS.exists():
            return

        try:
            creds = json.loads(_GEMINI_CLI_CREDS.read_text())
            if "refresh_token" not in creds:
                return
        except json.JSONDecodeError:
            return

        # Copy to vault
        _TOKENS_DIR.mkdir(parents=True, exist_ok=True)
        dest = _TOKENS_DIR / "default.json"
        if not dest.exists():
            dest.write_text(json.dumps(creds, indent=2))
            dest.chmod(0o600)

        # Register in vault
        vault = self._load_vault()
        vault.setdefault("accounts", {})["default"] = {
            "email": creds.get("email", creds.get("account", "")),
            "source": "gemini-cli (auto-imported)",
            "creds_file": "default.json",
            "added_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        vault["default_account"] = "default"
        self._save_vault(vault)
        logger.info("Auto-imported gemini-cli credentials as 'default' account")

    # PURPOSE: [L2-auto] _refresh_token の関数定義
    def _refresh_token(
        self,
        refresh_token: str,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> str:
        """Refresh an access token using the refresh token.

        Args:
            refresh_token: The OAuth refresh token.
            client_id: Per-credential client_id (優先)。None なら oauth.json にフォールバック。
            client_secret: Per-credential client_secret (優先)。
        """
        if not client_id or not client_secret:
            client_id, client_secret = self._get_oauth_config()

        data = urllib.parse.urlencode({
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }).encode("utf-8")

        try:
            req = urllib.request.Request(_TOKEN_URL, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["access_token"]
        except (urllib.error.HTTPError, KeyError, json.JSONDecodeError) as e:
            raise VaultAuthError(f"Token refresh 失敗: {e}")

    # PURPOSE: [L2-auto] _get_oauth_config の関数定義
    def _get_oauth_config(self) -> tuple[str, str]:
        """Load OAuth client_id and client_secret (cached)."""
        if self._oauth_config:
            return self._oauth_config

        if not _OAUTH_CONFIG.exists():
            raise VaultError(
                f"OAuth 設定が見つかりません: {_OAUTH_CONFIG}\n"
                "作成方法: mkdir -p ~/.config/cortex && "
                'echo \'{"client_id":"...","client_secret":"..."}\' > ~/.config/cortex/oauth.json'
            )

        data = json.loads(_OAUTH_CONFIG.read_text())
        self._oauth_config = (data["client_id"], data["client_secret"])
        return self._oauth_config

    # PURPOSE: [L2-auto] status の関数定義
    def status(self) -> dict[str, Any]:
        """Get token health status for all accounts.

        Returns:
            {
                "accounts": {
                    "account_name": {
                        "cached": bool,
                        "ttl_seconds": int or None,
                        "expires_at": str or None,
                        "healthy": bool,
                    },
                    ...
                },
                "default_account": str,
                "total_accounts": int,
            }
        """
        vault = self._load_vault()
        now = time.time()
        result: dict[str, Any] = {}

        for name in vault.get("accounts", {}):
            name = str(name)
            if name in self._cache:
                _token, expiry = self._cache[name]
                ttl = max(0, int(expiry - now))
                result[name] = {
                    "cached": True,
                    "ttl_seconds": ttl,
                    "expires_at": time.strftime(
                        "%Y-%m-%dT%H:%M:%S", time.localtime(expiry)
                    ),
                    "healthy": ttl > 300,  # > 5 min remaining
                }
            else:
                result[name] = {
                    "cached": False,
                    "ttl_seconds": None,
                    "expires_at": None,
                    "healthy": None,  # unknown until first use
                }

        return {
            "accounts": result,
            "default_account": vault.get("default_account", "default"),
            "total_accounts": len(result),
        }

    # PURPOSE: [L2-auto] __repr__ の関数定義
    def __repr__(self) -> str:
        vault = self._load_vault()
        n = len(vault.get("accounts", {}))
        default = vault.get("default_account", "?")
        return f"TokenVault(accounts={n}, default={default!r})"
