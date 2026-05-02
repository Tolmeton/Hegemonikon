#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/mcp/ 出張 HGK MCP Gateway
"""
出張 HGK MCP Gateway — モバイルからの HGK アクセス

FastMCP + Streamable HTTP で、Claude/ChatGPT のモバイルアプリから
MCP 経由で HGK の認知機能にアクセスするリモートサーバー。

Usage:
    # ローカル起動 (開発)
    python -m mekhane.mcp.hgk_gateway

    # Tailscale Funnel で公開
    tailscale funnel 8765
    python -m mekhane.mcp.hgk_gateway

Architecture:
    [スマホ Claude/ChatGPT] → MCP (Streamable HTTP) → [このサーバー] → [HGK モジュール]
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # hegemonikon/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mekhane.mcp.gateway_hooks import HGKFastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.server.auth.provider import (
    OAuthAuthorizationServerProvider,
    AuthorizationParams,
    AuthorizationCode,
    RefreshToken,
    AccessToken,
    construct_redirect_uri,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

# =============================================================================
# Configuration
# =============================================================================

GATEWAY_HOST = os.getenv("HGK_GATEWAY_HOST", "127.0.0.1")
GATEWAY_PORT = int(os.getenv("HGK_GATEWAY_PORT", "8765"))

# Bearer Token for OAuth access token (generated once, used as the access token)
GATEWAY_TOKEN = os.getenv("HGK_GATEWAY_TOKEN", "")

# [C-1] TOKEN 未設定: STDIO モードでは OAuth 不要なため警告のみ
# HTTP モード時は __main__ で起動拒否する
if not GATEWAY_TOKEN:
    print("⚠️ HGK_GATEWAY_TOKEN is not set. OAuth will be disabled (OK for STDIO mode).", file=sys.stderr)

# [C-2] 許可されたクライアントID (名前付き) + 許可された redirect_uri ドメイン
# claude.ai は毎セッション新しい UUID client_id を生成するため、
# ドメインベースで許可する (redirect_uri に含まれるドメインで判定)
ALLOWED_CLIENT_IDS: set[str] = {
    "claude.ai",
    "chatgpt.com",
    "hgk-mobile",
}
ALLOWED_REDIRECT_DOMAINS: set[str] = {
    "claude.ai",
    "chatgpt.com",
}

# Tailscale hostname auto-detection
# PURPOSE: [L2-auto] _detect_tailscale_hostname の関数定義
def _detect_tailscale_hostname() -> str | None:
    """Tailscale の DNS 名を自動検出。失敗時は None。"""
    import signal
    import subprocess

    # PURPOSE: [L2-auto] _alarm_handler の関数定義
    def _alarm_handler(signum, frame):
        raise TimeoutError("tailscale status timed out (signal)")

    old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
    try:
        signal.alarm(3)  # Hard timeout: 3 seconds
        result = subprocess.run(
            ["tailscale", "status", "--self", "--json"],
            capture_output=True, text=True, timeout=3,
        )
        signal.alarm(0)
        if result.returncode == 0:
            import json as _json
            data = _json.loads(result.stdout)
            dns_name = data.get("Self", {}).get("DNSName", "").rstrip(".")
            if dns_name:
                return dns_name
    except Exception:  # noqa: BLE001
        signal.alarm(0)
    finally:
        signal.signal(signal.SIGALRM, old_handler)
    return None

# Gateway URL: env → Tailscale auto-detect → fallback
# [FIX] HGK_GATEWAY_URL が設定済みなら Tailscale auto-detect をスキップ
# (tailscale status --self --json がハングすると起動がブロックされるため)
_env_url = os.getenv("HGK_GATEWAY_URL")
if _env_url:
    _GATEWAY_URL = _env_url
    print(f"🌐 Gateway URL (env): {_GATEWAY_URL}", file=sys.stderr)
else:
    _ts_hostname = _detect_tailscale_hostname()
    _GATEWAY_URL = (
        f"https://{_ts_hostname}" if _ts_hostname else f"http://localhost:{GATEWAY_PORT}"
    )
    if _ts_hostname:
        print(f"🌐 Tailscale detected: {_ts_hostname}", file=sys.stderr)
    else:
        print(f"⚠️ Tailscale not detected, using: {_GATEWAY_URL}", file=sys.stderr)

# Allowed hosts for DNS rebinding protection (auto-derived from URL)
from urllib.parse import urlparse as _urlparse
_parsed_url = _urlparse(_GATEWAY_URL)
_url_host = _parsed_url.hostname or "localhost"
_static_hosts = ["localhost", f"localhost:{GATEWAY_PORT}", "127.0.0.1", f"127.0.0.1:{GATEWAY_PORT}"]
_dynamic_hosts = [_url_host] if _url_host not in _static_hosts else []
ALLOWED_HOSTS = os.getenv(
    "HGK_GATEWAY_ALLOWED_HOSTS",
    ",".join(_static_hosts + _dynamic_hosts),
).split(",")



# =============================================================================
# [L2] Policy Loader — 宣言的ポリシー管理
# =============================================================================

# PURPOSE: gateway_policy.yaml から宣言的ポリシーを読み込む
def _load_policy() -> dict:
    """gateway_policy.yaml を読み込み、ポリシー辞書を返す。

    ファイルが見つからない場合はデフォルト値を返す。
    起動時に1回だけ呼ばれ、グローバル変数に格納される。
    """
    import yaml

    policy_path = Path(__file__).parent / "gateway_policy.yaml"
    if not policy_path.exists():
        print(f"⚠️ Policy file not found: {policy_path}. Using defaults.", file=sys.stderr)
        return {"version": "0.0", "defaults": {"max_input_size": 10000}, "tools": {}, "security": {}, "trace": {"enabled": False}}

    try:
        with open(policy_path, "r", encoding="utf-8") as f:
            policy = yaml.safe_load(f)
        print(f"✅ Policy loaded: v{policy.get('version', '?')} ({len(policy.get('tools', {}))} tools)", file=sys.stderr)
        return policy
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Policy load failed: {e}. Using defaults.", file=sys.stderr)
        return {"version": "0.0", "defaults": {"max_input_size": 10000}, "tools": {}, "security": {}, "trace": {"enabled": False}}


# PURPOSE: ポリシーからツール固有の制約値を取得する
def _get_policy(tool_name: str, key: str, default=None):
    """ポリシーからツール固有の値を取得。なければ defaults → default の順。"""
    tool_policy = POLICY.get("tools", {}).get(tool_name, {})
    if key in tool_policy:
        return tool_policy[key]
    defaults = POLICY.get("defaults", {})
    if key in defaults:
        return defaults[key]
    return default


POLICY = _load_policy()


# =============================================================================
# [L2] Trace Logger — ツール呼び出し監査ログ
# =============================================================================

# PURPOSE: ツール呼び出しをJSONL形式で監査ログに記録する
def _trace_tool_call(
    tool_name: str,
    input_size: int,
    duration_ms: float,
    success: bool,
) -> None:
    """ツール呼び出しをトレースログに記録する。

    gateway_policy.yaml の trace.enabled が true の場合のみ記録。
    出力先: MNEME_DIR / gateway_trace.jsonl (JSON Lines 形式)。
    """
    trace_config = POLICY.get("trace", {})
    if not trace_config.get("enabled", False):
        return

    from datetime import timezone

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "input_size": input_size,
        "duration_ms": round(duration_ms, 1),
        "success": success,
    }

    trace_filename = trace_config.get("output", "gateway_trace.jsonl")
    # Use STATE_LOGS for trace files (moved from Mneme root)
    trace_path = _STATE_LOGS / trace_filename

    try:
        _STATE_LOGS.mkdir(parents=True, exist_ok=True)

        # ローテーション: 最大サイズ超過時にリネーム
        max_mb = trace_config.get("max_file_size_mb", 10)
        if trace_path.exists() and trace_path.stat().st_size > max_mb * 1024 * 1024:
            rotated = trace_path.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
            trace_path.rename(rotated)

        with open(trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ Trace log failed: {e}", file=sys.stderr)


# PURPOSE: 引数から入力サイズを推定する
def _estimate_input_size(*args: Any, **kwargs: Any) -> int:
    """ツール引数から入力サイズ (文字数) を推定する。"""
    total = 0
    for a in args:
        if isinstance(a, str):
            total += len(a)
    for v in kwargs.values():
        if isinstance(v, str):
            total += len(v)
    return total


# PURPOSE: ツール関数にトレースを自動付与するデコレータ
def _traced(fn):
    """ツール関数にトレースを自動付与するデコレータ。

    関数の引数から入力サイズを推定し、実行時間と成否を記録する。
    手動で _start / _trace_tool_call を書く必要がなくなる。
    """
    import functools

    # PURPOSE: [L2-auto] wrapper の関数定義
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        _start = time.time()
        input_size = _estimate_input_size(*args, **kwargs)
        try:
            result = fn(*args, **kwargs)
            _trace_tool_call(fn.__name__, input_size, (time.time() - _start) * 1000, True)
            return result
        except Exception as e:  # noqa: BLE001
            _trace_tool_call(fn.__name__, input_size, (time.time() - _start) * 1000, False)
            raise

    return wrapper


# =============================================================================
# [L2] WBC Security Event Logger — Sympatheia 統合
# =============================================================================

# State L2 paths (Sympatheia と共有)
try:
    from mekhane.paths import (
    INCOMING_DIR as _INCOMING_DIR,
    MNEME_DIR,
    MNEME_DIR as _MNEME_DIR,
    PROCESSED_DIR as _PROCESSED_DIR,
    SESSIONS_DIR as _STATE_SESSIONS,
    STATE_CACHE as _STATE_CACHE,
    STATE_LOGS as _STATE_LOGS,
    STATE_VIOLATIONS as _STATE_VIOLATIONS,
)
except ImportError:
    _MNEME_STATE = Path(os.getenv("HGK_MNEME", str(MNEME_DIR))) / "05_状態｜State"
    _STATE_VIOLATIONS = _MNEME_STATE / "A_違反｜Violations"
    _STATE_CACHE = _MNEME_STATE / "B_キャッシュ｜Cache"
    _STATE_LOGS = _MNEME_STATE / "C_ログ｜Logs"
    _MNEME_DIR = Path(os.getenv("HGK_MNEME", str(MNEME_DIR)))
    _STATE_SESSIONS = _MNEME_DIR / "01_記録｜Records" / "b_対話｜sessions"
    _INCOMING_DIR = _MNEME_DIR / "03_素材｜Materials" / "a_受信｜incoming"
    _PROCESSED_DIR = _MNEME_DIR / "03_素材｜Materials" / "b_処理済｜processed"


# PURPOSE: [L2-auto] セキュリティイベントを wbc_state.json に書き込む。
def _wbc_log_security_event(
    event_type: str,
    severity: str,
    details: str,
    source: str = "hgk_gateway",
) -> None:
    """セキュリティイベントを wbc_state.json に書き込む。

    Sympatheia WBC と同じフォーマットでアラートを追加し、
    /boot 時の sympatheia_status で検知される。
    """
    import json
    from datetime import datetime, timezone

    wbc_file = _STATE_VIOLATIONS / "wbc_state.json"
    try:
        _STATE_VIOLATIONS.mkdir(parents=True, exist_ok=True)
        if wbc_file.exists():
            state = json.loads(wbc_file.read_text("utf-8"))
        else:
            state = {"alerts": [], "totalAlerts": 0}

        alert = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": source,
            "severity": severity,
            "eventType": event_type,
            "details": details,
            "threatScore": 5 if severity == "medium" else (10 if severity == "high" else 2),
        }
        state["alerts"].append(alert)
        state["totalAlerts"] = state.get("totalAlerts", 0) + 1

        # 直近100件のみ保持
        state["alerts"] = state["alerts"][-100:]

        wbc_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ WBC log failed: {e}", file=sys.stderr)


# =============================================================================
# OAuth 2.1 Provider (auto-approve, single-user)
# =============================================================================

# PURPOSE: の統一的インターフェースを実現する
class HGKOAuthProvider(OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]):
    """
    最小 OAuth 2.1 プロバイダー。
    - claude.ai Connector 用の /authorize → /token フローを処理
    - 認証コードを自動承認 (単一ユーザー、GATEWAY_TOKEN で保護)
    - インメモリストレージ
    """

    # PURPOSE: [L2-auto] 初期化: init__
    def __init__(self, access_token: str):
        self._access_token = access_token
        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._auth_codes: dict[str, AuthorizationCode] = {}
        self._refresh_tokens: dict[str, RefreshToken] = {}
        self._load_state()

    # PURPOSE: [L2-auto] _save_state の関数定義
    def _save_state(self) -> None:
        import json
        state_file = _STATE_CACHE / "gateway_oauth.json"
        try:
            _STATE_CACHE.mkdir(parents=True, exist_ok=True)
            state = {
                "clients": {k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v.dict() for k, v in self._clients.items()},
                "auth_codes": {k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v.dict() for k, v in self._auth_codes.items()},
                "refresh_tokens": {k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v.dict() for k, v in self._refresh_tokens.items()},
            }
            state_file.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            import sys
            print(f"⚠️ Failed to save OAuth state: {e}", file=sys.stderr)

    # PURPOSE: [L2-auto] _load_state の関数定義
    def _load_state(self) -> None:
        import json
        state_file = _STATE_CACHE / "gateway_oauth.json"
        if not state_file.exists():
            return
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
            for k, v in state.get("clients", {}).items():
                self._clients[k] = OAuthClientInformationFull(**v)
            # Filter expired auth codes
            now = time.time()
            for k, v in state.get("auth_codes", {}).items():
                if v.get("expires_at", 0) > now:
                    self._auth_codes[k] = AuthorizationCode(**v)
            expired_count = len(state.get("auth_codes", {})) - len(self._auth_codes)
            for k, v in state.get("refresh_tokens", {}).items():
                self._refresh_tokens[k] = RefreshToken(**v)
            import sys
            msg = f"✅ Loaded OAuth state: {len(self._clients)} clients, {len(self._refresh_tokens)} refresh tokens"
            if expired_count > 0:
                msg += f" (pruned {expired_count} expired auth codes)"
            print(msg, file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            import sys
            print(f"⚠️ Failed to load OAuth state: {e}", file=sys.stderr)

    # PURPOSE: client を取得する
    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        client = self._clients.get(client_id)
        if client is None:
            # [C-2] Check: named whitelist OR UUID format (claude.ai dynamic IDs)
            import re
            is_uuid = bool(re.match(
                r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
                client_id
            ))
            if client_id not in ALLOWED_CLIENT_IDS and not is_uuid:
                print(f"⚠️ Rejected unknown client: {client_id[:32]}", file=sys.stderr)
                _wbc_log_security_event(
                    event_type="client_rejected",
                    severity="medium",
                    details=f"Unknown client_id rejected: {client_id[:32]}",
                )
                return None
            # Auto-register: whitelisted names or UUID clients (claude.ai dynamic)
            from pydantic import AnyHttpUrl
            client = OAuthClientInformationFull(
                client_id=client_id,
                client_secret=None,
                redirect_uris=[AnyHttpUrl("https://claude.ai/api/mcp/auth_callback")],
                client_name=f"auto-{client_id[:16]}",
                grant_types=["authorization_code", "refresh_token"],
                response_types=["code"],
                token_endpoint_auth_method="none",
            )
            self._clients[client_id] = client
            self._save_state()
        return client

    # PURPOSE: client を登録する
    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self._clients[client_info.client_id] = client_info
        self._save_state()

    # PURPOSE: hgk_gateway の authorize 処理を実行する
    async def authorize(
        self, client: OAuthClientInformationFull, params: AuthorizationParams
    ) -> str:
        """Auto-approve: 認証コードを即発行し redirect_uri にリダイレクト。"""
        import secrets
        # Dynamically add redirect_uri to client's registered URIs
        if client.redirect_uris is None:
            client.redirect_uris = [params.redirect_uri]
        elif params.redirect_uri not in client.redirect_uris:
            client.redirect_uris.append(params.redirect_uri)
        code = secrets.token_urlsafe(32)
        self._auth_codes[code] = AuthorizationCode(
            code=code,
            scopes=params.scopes or [],
            expires_at=time.time() + 600,  # 10 min
            client_id=client.client_id,
            code_challenge=params.code_challenge,
            redirect_uri=params.redirect_uri,
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
        )
        self._save_state()
        return construct_redirect_uri(
            str(params.redirect_uri),
            code=code,
            state=params.state,
        )

    # PURPOSE: authorization code を読み込む
    async def load_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: str
    ) -> AuthorizationCode | None:
        ac = self._auth_codes.get(authorization_code)
        if ac and ac.client_id == client.client_id and ac.expires_at > time.time():
            return ac
        return None

    # PURPOSE: hgk_gateway の exchange authorization code 処理を実行する
    async def exchange_authorization_code(
        self, client: OAuthClientInformationFull, authorization_code: AuthorizationCode
    ) -> OAuthToken:
        """認証コード → アクセストークン交換。固定トークンを返す。"""
        self._auth_codes.pop(authorization_code.code, None)
        import secrets
        refresh = secrets.token_urlsafe(32)
        self._refresh_tokens[refresh] = RefreshToken(
            token=refresh,
            client_id=client.client_id,
            scopes=authorization_code.scopes,
        )
        self._save_state()
        return OAuthToken(
            access_token=self._access_token,
            token_type="bearer",
            expires_in=604800,  # [C-4] 7 days (persistent tokens via gateway_oauth.json)
            refresh_token=refresh,
            scope=" ".join(authorization_code.scopes) if authorization_code.scopes else None,
        )

    # PURPOSE: refresh token を読み込む
    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        rt = self._refresh_tokens.get(refresh_token)
        if rt and rt.client_id == client.client_id:
            return rt
        return None

    # PURPOSE: hgk_gateway の exchange refresh token 処理を実行する
    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        import secrets
        new_refresh = secrets.token_urlsafe(32)
        self._refresh_tokens.pop(refresh_token.token, None)
        self._refresh_tokens[new_refresh] = RefreshToken(
            token=new_refresh,
            client_id=client.client_id,
            scopes=scopes or refresh_token.scopes,
        )
        self._save_state()
        return OAuthToken(
            access_token=self._access_token,
            token_type="bearer",
            expires_in=604800,  # [C-4] 7 days
            refresh_token=new_refresh,
            scope=" ".join(scopes) if scopes else None,
        )

    # PURPOSE: access token を読み込む
    async def load_access_token(self, token: str) -> AccessToken | None:
        if token == self._access_token:
            return AccessToken(
                token=token,
                client_id="hgk",
                scopes=[],
            )
        # [L2] Invalid token → WBC alert
        _wbc_log_security_event(
            event_type="invalid_token",
            severity="high",
            details=f"Invalid access token attempt (prefix: {token[:8]}...)",
        )
        return None

    # PURPOSE: hgk_gateway の revoke token 処理を実行する
    async def revoke_token(self, token: AccessToken | RefreshToken) -> None:
        if isinstance(token, RefreshToken):
            self._refresh_tokens.pop(token.token, None)
            self._save_state()


# =============================================================================
# Gateway Server
# =============================================================================

from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions

# _GATEWAY_URL is already defined above (auto-detected)

_oauth_provider = HGKOAuthProvider(GATEWAY_TOKEN) if GATEWAY_TOKEN else None
_auth_settings = AuthSettings(
    issuer_url=_GATEWAY_URL,
    resource_server_url=_GATEWAY_URL,
    client_registration_options=ClientRegistrationOptions(enabled=True),
) if GATEWAY_TOKEN else None

mcp = HGKFastMCP(
    "hgk-gateway",
    host=GATEWAY_HOST,
    port=GATEWAY_PORT,
    auth_server_provider=_oauth_provider,
    auth=_auth_settings,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=ALLOWED_HOSTS,
    ),
    instructions=(
        "Hegemonikón 出張 MCP Gateway。"
        "モバイルから HGK の認知機能にアクセスする。"
        "/sop 調査依頼書の生成、KI/Gnōsis 検索、"
        "CCL パース、Doxa/Handoff 参照、アイデアメモ保存、"
        "Digestor (消化パイプライン実行・候補一覧・消化済マーク・トピック管理) が可能。"
    ),
)

# Paths — paths.py が Single Source of Truth (try/except block at L271 で import 済み)
MNEME_DIR = _MNEME_DIR
SESSIONS_DIR = _STATE_SESSIONS
DOXA_DIR = _MNEME_DIR / "doxa"
SOP_OUTPUT_DIR = _MNEME_DIR / "workflows"
IDEA_DIR = _MNEME_DIR / "ideas"


# hgk_sop_generate → gateway_tools に移動


# hgk_search → gateway_tools に移動

# CCL Dispatch → gateway_tools/ccl.py に移動


# hgk_doxa_read → gateway_tools に移動


# hgk_handoff_read → gateway_tools に移動


# hgk_idea_capture → gateway_tools に移動


# hgk_status → gateway_tools に移動


# hgk_pks_stats → gateway_tools に移動


# hgk_pks_health → gateway_tools に移動


# hgk_pks_search → gateway_tools に移動


# CCL Execute + CCL Run → gateway_tools/ccl.py に移動


# hgk_paper_search → gateway_tools に移動


# =============================================================================
# Digestor: Incoming Check (消化候補一覧)
# =============================================================================

# PURPOSE: incoming/ の消化候補を確認する
INCOMING_DIR = _INCOMING_DIR
PROCESSED_DIR = _PROCESSED_DIR

# hgk_digest_check → gateway_tools に移動


# hgk_digest_mark → gateway_tools に移動


# hgk_digest_list → gateway_tools に移動


# hgk_digest_topics → gateway_tools に移動


# hgk_digest_run → gateway_tools に移動


# =============================================================================
# Ochēma: LLM 呼出し (Cortex API 経由)
# =============================================================================

# Rate limiter: 5 req/min
_ask_timestamps: list[float] = []
_ASK_RATE_LIMIT = 5
_ASK_RATE_WINDOW = 60  # seconds
# _check_rate_limit → gateway_tools に移動

# hgk_sessions → gateway_tools に移動


# _sessions_from_handoffs → gateway_tools に移動


# hgk_session_read → gateway_tools に移動


# hgk_ask → gateway_tools に移動


# hgk_models → gateway_tools に移動


# hgk_ochema_status → gateway_tools に移動


# =============================================================================
# Ochēma: ツール付き LLM エージェント + ステートフルチャット
# =============================================================================

# Chat session storage (in-memory, max 5 for Gateway)
_chat_sessions: dict[str, object] = {}
_MAX_CHAT_SESSIONS = 5


# hgk_ask_with_tools → gateway_tools に移動


# hgk_chat_start → gateway_tools に移動


# hgk_chat_send → gateway_tools に移動


# hgk_chat_close → gateway_tools に移動


# hgk_health → gateway_tools に移動


# hgk_notifications → gateway_tools に移動

# =============================================================================
# Autophōnos / PKS (Proactive Knowledge Surface)
# =============================================================================

_pks_engine = None


# _get_pks_engine → gateway_tools に移動



# hgk_proactive_push → gateway_tools に移動


# _auto_extract_topics → gateway_tools に移動




# =============================================================================
# Jules: コード生成タスク管理
# =============================================================================

# Jules API Key Pool (18 keys across 6 accounts, load-balanced)
_jules_api_key_pool: list[tuple[int, str]] = []
_jules_api_key_index = 0
_jules_dashboard = None


# _jules_init_pool → gateway_tools に移動


# _jules_get_key → gateway_tools に移動


# _jules_record → gateway_tools に移動


# hgk_jules_create_task → gateway_tools に移動


# hgk_jules_get_status → gateway_tools に移動


# hgk_jules_list_repos → gateway_tools に移動


# hgk_jules_batch_execute → gateway_tools に移動


# hgk_research → gateway_tools に移動


# hgk_research_search → gateway_tools に移動


# hgk_research_sources → gateway_tools に移動


# hgk_gateway_health → gateway_tools に移動


# =============================================================================
# Cowork: セッション活動の永続化
# =============================================================================

_COWORK_DIR = _STATE_SESSIONS / "cowork"
_COWORK_ARCHIVE = _COWORK_DIR / "_archive"
_COWORK_MAX_ACTIVE = 5  # 最新 N 件を保持


# _cowork_ensure_dirs → gateway_tools に移動


# _cowork_rotate → gateway_tools に移動


# hgk_cowork_save → gateway_tools に移動


# hgk_cowork_resume → gateway_tools に移動


# =============================================================================
# Register all domain tools from gateway_tools/ (DI pattern)
# =============================================================================
from mekhane.mcp.gateway_tools import register_all as _register_all
_register_all(mcp)  # mcp を依存注入 — gateway_tools/ → hgk_gateway への逆インポート不要


if __name__ == "__main__":
    import argparse
    _parser = argparse.ArgumentParser(description="HGK Gateway MCP Server")
    _parser.add_argument(
        "--transport", type=str, default="streamable-http",
        choices=["stdio", "streamable-http"],
        help="MCP トランスポート: stdio (Claude Desktop) / streamable-http (モバイル)",
    )
    _args = _parser.parse_args()
    import sys as _sys

    _tool_count = len(mcp._tool_manager._tools)

    if _args.transport == "stdio":
        # STDIO モード: print() は stderr に出力 (JSON-RPC 汚染防止)
        # OAuth は GATEWAY_TOKEN 未設定なら自動スキップ済み (L560)
        print(f"🔌 HGK Gateway starting in STDIO mode ({_tool_count} tools)", file=_sys.stderr)
        mcp.run(transport="stdio")
    else:
        # HTTP モード (従来のモバイル向け) — TOKEN 必須
        if not GATEWAY_TOKEN:
            print("❌ FATAL: HGK_GATEWAY_TOKEN is not set. Required for HTTP mode.", file=_sys.stderr)
            print("   Set HGK_GATEWAY_TOKEN in .env or environment.", file=_sys.stderr)
            _sys.exit(1)
        print("🔒 OAuth 2.1 authentication ENABLED", file=_sys.stderr)
        print(f"🚀 HGK Gateway starting on {GATEWAY_HOST}:{GATEWAY_PORT}", file=_sys.stderr)
        print(f"✅ {_tool_count} tools registered", file=_sys.stderr)
        mcp.run(transport="streamable-http")

# =============================================================================
# Sympatheia: 自律神経系コア (WBC, Attractor, Digest, Feedback)
# =============================================================================

_sympatheia = None

# _get_sympatheia → gateway_tools に移動


# hgk_sympatheia_wbc → gateway_tools に移動


# hgk_sympatheia_attractor → gateway_tools に移動


# hgk_sympatheia_digest → gateway_tools に移動


# hgk_sympatheia_feedback → gateway_tools に移動


# hgk_sympatheia_basanos_scan → gateway_tools に移動


# hgk_sympatheia_peira_health → gateway_tools に移動


# hgk_sympatheia_log_violation → gateway_tools に移動


# hgk_sympatheia_violation_dashboard → gateway_tools に移動


# hgk_sympatheia_escalate → gateway_tools に移動

# =============================================================================
# Týpos: Hegemonikón Skill Generator
# =============================================================================

_pl_module = None
_PARSER_AVAILABLE = False
_PromptLangParser = None
_parse_file = None
_parse_all = None
_resolve = None
_validate_file = None
_Prompt = None
_ParseError = None
_typos_generate = None
_typos_classify_task = None
_typos_detect_domain = None
_typos_validate_domain = None

def _ensure_typos_parser():
    """Týpos パーサーの遅延ロード。"""
    global _pl_module, _PARSER_AVAILABLE
    global _PromptLangParser, _parse_file, _parse_all, _resolve, _validate_file
    global _Prompt, _ParseError, _typos_generate, _typos_classify_task, _typos_detect_domain, _typos_validate_domain
    
    if _pl_module is not None:
        return _PARSER_AVAILABLE
        
    try:
        import sys
        from pathlib import Path
        import importlib
        
        # typos_mcp_server.py と同じロードロジック
        current_dir = Path(__file__).parent
        erg_dir = current_dir.parent / "ergasterion" / "typos"
        if str(erg_dir) not in sys.path:
            sys.path.insert(0, str(erg_dir))
            
        _pl_module = importlib.import_module("typos")
        _PromptLangParser = _pl_module.PromptLangParser
        _parse_file = _pl_module.parse_file
        _parse_all = _pl_module.parse_all
        _resolve = _pl_module.resolve
        _validate_file = _pl_module.validate_file
        _Prompt = _pl_module.Prompt
        _ParseError = _pl_module.ParseError
        
        # typos_mcp_server.py 側のユーティリティを借用するためインポート
        if str(current_dir) not in sys.path:
           sys.path.insert(0, str(current_dir))
        
        import typos_mcp_server as tms
        _typos_generate = tms.generate_typos
        _typos_classify_task = tms.classify_task
        _typos_detect_domain = tms.detect_domain
        _typos_validate_domain = tms.validate_domain

        _PARSER_AVAILABLE = True
    except Exception as e:  # noqa: BLE001
        print(f"[Gateway] Týpos parser import error: {e}", file=sys.stderr)
        _pl_module = object() # sentinel
        _PARSER_AVAILABLE = False
        
    return _PARSER_AVAILABLE

def _get_typos_content(content: str = "", filepath: str = "") -> str:
    """Extract content from arguments (content or filepath)."""
    from pathlib import Path
    if content:
        return content
    elif filepath:
        from mekhane.paths import resolve_client_path
        path = resolve_client_path(filepath)
        if path.exists():
            return path.read_text(encoding="utf-8")
        else:
            raise FileNotFoundError(f"File not found: {filepath} (resolved: {path})")
    else:
        raise ValueError("Either 'content' or 'filepath' is required")


# hgk_typos_generate → gateway_tools に移動


# hgk_typos_parse → gateway_tools に移動


# hgk_typos_validate → gateway_tools に移動


# hgk_typos_compile → gateway_tools に移動


# hgk_typos_expand → gateway_tools に移動


# hgk_typos_policy_check → gateway_tools に移動


# =============================================================================
# Periskopē: Research Tracking & Benchmarking
# =============================================================================

def _apply_schedule_override(engine, decay_type: str, alpha_schedule: str, prefix: str = ""):
    """Override schedule config if specified via MCP."""
    if decay_type or alpha_schedule:
        iter_cfg = engine._config.get("iterative_deepening", {})
        if decay_type:
            iter_cfg["decay_type"] = decay_type
        if alpha_schedule:
            iter_cfg["alpha_schedule"] = alpha_schedule
        engine._config["iterative_deepening"] = iter_cfg
        log_prefix = prefix + "s" if prefix else "S"
        print(f"{log_prefix}chedule override: decay_type={decay_type!r}, alpha_schedule={alpha_schedule!r}", file=sys.stderr)


# hgk_periskope_track → gateway_tools に移動


# hgk_periskope_metrics → gateway_tools に移動


# hgk_periskope_benchmark → gateway_tools に移動

