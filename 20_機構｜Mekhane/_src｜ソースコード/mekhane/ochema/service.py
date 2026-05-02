#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/ A0→LLMアクセス統合サービス
# PURPOSE: OchemaService — 統一 LLM サービス層。全消費者の唯一のエントリポイント
"""
OchemaService — Unified LLM Service Layer

3つの消費者 (Desktop API / MCP Server / CLI) が
同一インターフェースで LLM にアクセスするためのサービス層。

内部で AntigravityClient (LS経由) と CortexClient (Cortex API 直叩き) を
モデル名に基づいてルーティングする。

Usage:
    from mekhane.ochema.service import OchemaService

    svc = OchemaService.get()
    resp = svc.ask("Hello", model="gemini-2.0-flash")
    print(resp.text)
"""


from __future__ import annotations
from typing import Any, Generator, Optional
import json
import logging
import os
import time
from typing import TYPE_CHECKING, Awaitable, Callable

if TYPE_CHECKING:
    from mekhane.ochema.types import LLMResponse
    from mekhane.ochema.model_fallback import ModelCandidate

logger = logging.getLogger(__name__)


# --- Constants ---

# PURPOSE: デフォルトモデル (CortexClient 用)
DEFAULT_MODEL = "gemini-3-flash-preview"

# --- DX-010 §L: Platform Constraints ---
# BYOK (Bring Your Own Key) is unsupported on local LS
# SeatManagementService returns 404 (not registered for non-Windsurf)
BYOK_STATUS = "unsupported"
# cloudaicompanionProject changes per process — never hardcode
DYNAMIC_PROJECT_ID = True
# Claude via REST generateChat is a false positive (DX-010 §E.3, §L)
# Server echoes requested model name but actual inference is Gemini fallback
CLAUDE_REST_FALSE_POSITIVE = True

# --- DX-010 §N.11: Unleash Feature Flag Constraints ---
# SOURCE: Unleash production API (2026-03-04 gcore + curl 実測)
# CASCADE_PREMIUM_CONFIG_OVERRIDE の variant "40k_limit" (weight=1000)

# Premium チャットのコンテキスト上限 (全モデル共通)
UNLEASH_MAX_TOKEN_LIMIT = 45_000
# チェックポイント閾値 — この値を超えると checkpoint_model で要約が作成される
# ⚠️ 重要: 30K 超の文脈は GPT-4o-mini で要約 → 情報喪失リスク
UNLEASH_CHECKPOINT_THRESHOLD = 30_000
# チェックポイントに使われる LLM (品質劣化の根源: HGK 文脈を理解しない)
UNLEASH_CHECKPOINT_MODEL = "MODEL_CHAT_GPT_4O_MINI_2024_07_18"
# Planner の最大出力トークン数 (1 ステップの出力上限)
UNLEASH_PLANNER_MAX_OUTPUT = 8_192
# Checkpoint overhead ratio
UNLEASH_CHECKPOINT_MAX_OVERHEAD = 0.1

# --- DX-010 §N.11.6: ultra-tier Knowledge Config ---
# cascade-knowledge-config constraint: userTierId IN ['g1-ultra-tier']
UNLEASH_ULTRA_MAX_CONTEXT = 200_000
UNLEASH_ULTRA_MAX_INVOCATIONS = 20

# PURPOSE: 全プロバイダの利用可能モデル (モデルID → 表示名)
AVAILABLE_MODELS: dict[str, str] = {
    # Gemini (Cortex API 経由)
    "gemini-3-pro-preview": "Gemini 3 Pro Preview",
    "gemini-3-flash-preview": "Gemini 3 Flash Preview",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.0-flash": "Gemini 2.0 Flash",
    # Cortex generateChat (LS不要、Gemini のみ直接アクセス)
    "cortex-chat": "Cortex Chat (LS不要 Gemini のみ)",
    # Claude (LS ConnectRPC 経由のみ — REST は偽陽性, DX-010 v9.1)
    "claude-sonnet": "Claude Sonnet 4.6 (LS必須)",
    "claude-sonnet-4-5": "Claude Sonnet 4.6 (LS必須, 後方互換エイリアス)",
    "claude-sonnet-4-6": "Claude Sonnet 4.6 (LS必須)",
    "claude-opus": "Claude Opus 4.6 (LS必須)",
    "claude-opus-4-6": "Claude Opus 4.6 (LS必須)",
    # Vertex AI Claude (GCP クレジット消費、1M コンテキスト)
    "opus-vertex": "Claude Opus 4.6 (Vertex AI, 1M ctx)",
    "opus-direct": "Claude Opus 4.6 (Vertex AI, alias)",
    "claude-opus-vertex": "Claude Opus 4.6 (Vertex AI, 完全名)",
}

# PURPOSE: Claude モデルのフレンドリー名 → model_config_id マッピング
# ⚠️ REST generateChat は Claude に見えるが実体は Gemini (偽陽性, DX-010 v9.1-9.2)
# ⚠️ REST M35 + g1-ultra-tier → 403 IAM PERMISSION_DENIED (2026-02-23 確認)
# Claude 到達には LS (ConnectRPC) 経由が必須。このマップは LS proto enum 解決に使用。
CLAUDE_MODEL_MAP: dict[str, str] = {
    # フレンドリー名 → LS proto enum (LS 経由で使用)
    "claude-sonnet": "MODEL_PLACEHOLDER_M35",
    "claude-sonnet-4-5": "MODEL_PLACEHOLDER_M35",
    "claude-sonnet-4-6": "MODEL_PLACEHOLDER_M35",
    "claude-opus": "MODEL_PLACEHOLDER_M26",
    "claude-opus-4-6": "MODEL_PLACEHOLDER_M26",
    # LS proto enum → そのまま
    "MODEL_CLAUDE_4_5_SONNET_THINKING": "MODEL_PLACEHOLDER_M35",
    "MODEL_PLACEHOLDER_M26": "MODEL_PLACEHOLDER_M26",
    "MODEL_PLACEHOLDER_M35": "MODEL_PLACEHOLDER_M35",
}

# Vertex AI Claude ルート — LS の 45K 制限を回避し 1M コンテキストで Claude Opus 4.6 を呼ぶ
# OchemaService.ask(model="opus-vertex") で発動
VERTEX_CLAUDE_MODELS = {
    "opus-vertex",      # Vertex AI rawPredict 経由 (GCP クレジット消費)
    "opus-direct",      # 同上 (エイリアス)
    "claude-opus-vertex",  # 完全名
}


# PURPOSE: Quota 枯渇時に呼び出し側が fallback 判断できるよう専用例外で通知する
class QuotaExhaustedError(RuntimeError):
    """Claude quota exhausted — 0% remaining."""
    pass


# --- Service ---


# PURPOSE: 統一 LLM サービス。モデル名に基づくルーティング + シングルトン管理
class OchemaService:
    """Unified LLM Service — routes to AntigravityClient or CortexClient.

    Singleton pattern: use OchemaService.get() to obtain the shared instance.
    """

    _instance: Optional["OchemaService"] = None

    # --- Resource Limits ---
    MAX_CONCURRENT_REQUESTS = 5   # 同時 LLM リクエスト上限
    QUOTA_WARNING_THRESHOLD = 10  # Quota 残量警告閾値 (%)
    LS_RETRY_COOLDOWN_SEC = 60    # LS 接続失敗後の再試行クールダウン (秒)
    MAX_LS_RETRIES = 5            # LS 接続の最大リトライ回数
    LS_RETRY_RESET_SEC = 300      # リトライ上限時の自動回復時間 (秒)
    QUOTA_CACHE_TTL_SEC = 300     # Quota キャッシュ有効期間 (5分)
    LS_CONNECT_TIMEOUT_SEC = 15   # _get_ls_client() 全体のタイムアウト (秒)

    def __init__(self) -> None:
        """Initialize service (use get() for singleton access)."""
        self._ls_client: Any = None
        self._cortex_clients: dict[str, Any] = {}  # account -> CortexClient
        self._ls_last_fail_time: float = 0.0  # 最後に LS 接続が失敗した時刻 (epoch)
        self._ls_retry_count: int = 0          # LS 接続の連続失敗回数
        self._nonstd_mgr: Any = None  # NonStandaloneLSManager (フォールバック用)
        # 動的モデル発見キャッシュ: {"sonnet": "MODEL_...", "opus": "MODEL_..."}
        self._quota_cache: dict[str, Any] | None = None  # quota_status() の結果キャッシュ
        self._quota_cache_time: float = 0.0               # キャッシュ取得時刻 (monotonic)
        self._dynamic_claude_models: dict[str, str] = {}
        self._vertex_client: Any = None  # VertexClaudeClient (lazy init)

        # Provider-level cooldown state (shared across all ask() calls)
        # Tracks which providers (vertex, ls, cortex) are in cooldown.
        # Separate from TokenVault's CooldownManager which tracks account-level cooldowns.
        from mekhane.ochema.model_fallback import CooldownManager
        self._provider_cooldown = CooldownManager()
        
        # 同時リクエスト制限 (threading.Semaphore — sync context で使用)
        import threading
        self._request_semaphore = threading.Semaphore(self.MAX_CONCURRENT_REQUESTS)
        
        # 終了時に必ず NonStandalone LS を停止する
        import atexit
        atexit.register(self._cleanup)

    def _cleanup(self) -> None:
        """Cleanup resources on exit."""
        if self._nonstd_mgr is not None:
            try:
                logger.info("Stopping Non-Standalone LS (cleanup)")
                self._nonstd_mgr.stop()
            except OSError as e:
                logger.error("Failed to stop Non-Standalone LS: %s", e)
        if self._vertex_client is not None:
            try:
                logger.info("VertexClaudeClient cleanup: %s", self._vertex_client.costs.status())
            except AttributeError:
                pass
            self._vertex_client = None

    @classmethod
    def get(cls) -> "OchemaService":
        """Get the singleton service instance."""
        if cls._instance is None:
            cls._instance = cls()
            logger.info("OchemaService initialized")
        assert cls._instance is not None  # satisfy type checker
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton (for testing)."""
        if cls._instance is not None:
            cls._instance._cleanup()
        cls._instance = None

    def reset_ls(self) -> None:
        """Reset only the LS connection state. (Used for HTTP recovery)"""
        logger.info("Resetting LS connection state.")
        self._ls_client = None
        self._ls_retry_count = 0
        self._ls_last_fail_time = 0.0
        if self._nonstd_mgr is not None:
            try:
                self._nonstd_mgr.stop()
            except OSError:
                pass
            self._nonstd_mgr = None

    def ls_diagnostic(self) -> dict[str, Any]:
        """Return diagnostic info for LS connection."""
        pid = 0
        port = 0
        if self._ls_client is not None:
            pid = getattr(self._ls_client, 'pid', 0)
            port = getattr(self._ls_client, 'port', 0)
            source = getattr(getattr(self._ls_client, "ls", None), "source", "local")
            remote_host = getattr(getattr(self._ls_client, "ls", None), "remote_host", "")
            remote_port = getattr(getattr(self._ls_client, "ls", None), "remote_port", 0)
        else:
            source = "disconnected"
            remote_host = ""
            remote_port = 0
            
        elapsed = 0.0
        if self._ls_last_fail_time > 0:
            elapsed = time.monotonic() - self._ls_last_fail_time
            
        return {
            "has_client": self._ls_client is not None,
            "pid": pid,
            "port": port,
            "source": source,
            "remote_host": remote_host,
            "remote_port": remote_port,
            "retry_count": self._ls_retry_count,
            "max_retries": self.MAX_LS_RETRIES,
            "last_fail_ago_sec": round(elapsed, 1),
            "state": (
                "permanently_failed" 
                if self._ls_retry_count >= self.MAX_LS_RETRIES and elapsed < self.LS_RETRY_RESET_SEC
                else ("connected" if self._ls_client is not None else "disconnected")
            )
        }

    # --- Client Access (lazy) ---

    def _get_ls_client(self) -> Any:
        """Get AntigravityClient (lazy, cached). Returns None if LS unavailable.

        タイムアウトラッパー: _get_ls_client_inner() をスレッドで実行し、
        LS_CONNECT_TIMEOUT_SEC 以内に完了しなければ None を返す。
        これにより LS 接続がハングしても呼び出し元がブロックされない。
        """
        # キャッシュ済みクライアントの quick check (タイムアウト不要)
        if self._ls_client is not None:
            return self._check_cached_client()

        # 新規接続はタイムアウト付きで実行
        import threading
        result: list[Any] = [None]

        def _connect() -> None:
            result[0] = self._get_ls_client_inner()

        thread = threading.Thread(target=_connect, daemon=True)
        thread.start()
        thread.join(timeout=self.LS_CONNECT_TIMEOUT_SEC)

        if thread.is_alive():
            logger.warning(
                "_get_ls_client timed out after %ds. LS connection abandoned.",
                self.LS_CONNECT_TIMEOUT_SEC,
            )
            # タイムアウトはリトライカウンタに記録
            self._ls_retry_count += 1
            self._ls_last_fail_time = time.monotonic()
            return None

        return result[0]

    def _check_cached_client(self) -> Any:
        """キャッシュ済み LS クライアントのヘルスチェック。"""
        if self._ls_client is not None:
            # Quick health check — プロセス生存確認を優先
            # LS が LLM 処理中は GetUserStatus に応答しないことがある
            try:
                self._ls_client.get_status()
                return self._ls_client
            except (Exception, OSError) as e:  # urllib.error.URLError not imported  # noqa: BLE001
                # プロセスが生きているかを os.kill(pid, 0) で確認
                import os
                ls_info = getattr(self._ls_client, 'ls', None)
                source = getattr(ls_info, 'source', 'local')
                pid = getattr(self._ls_client, 'pid', 0) or (
                    self._nonstd_mgr.pid if self._nonstd_mgr else 0
                )
                process_alive = False
                if pid:
                    try:
                        os.kill(pid, 0)
                        process_alive = True
                    except OSError:
                        pass
                if process_alive and source != "remote":
                    # プロセスは生きている — LLM 処理中の可能性。クライアントを維持
                    logger.debug(
                        "LS health check timed out but process alive (PID %d). Keeping client.", pid
                    )
                    return self._ls_client
                if process_alive and source == "remote":
                    logger.warning(
                        "Remote LS health check failed despite live tunnel (PID %d). Resetting client.",
                        pid,
                    )
                logger.warning("LS health check failed: %s. Restarting client.", e)
                self._ls_client = None
                # ヘルスチェック失敗はリトライカウンタをリセットして再接続を許可
                self._ls_retry_count = 0
                self._ls_last_fail_time = 0.0
                if self._nonstd_mgr is not None:
                    try:
                        self._nonstd_mgr.stop()
                    except OSError:
                        pass
                    self._nonstd_mgr = None

    def _get_ls_client_inner(self) -> Any:
        """LS クライアント接続の実ロジック (タイムアウトなし)。

        優先順位:
        1. IDE LS に接続 (AntigravityClient 自動検出)
        2. NonStandaloneLSManager で独立 LS を起動しフォールバック
        """
        remote_ls_required = bool(
            os.environ.get("HGK_REMOTE_LS_HOST")
            or os.environ.get("HGK_DISABLE_LOCAL_LS_FALLBACK") == "1"
        )
        # TTL ベースのリトライゲート
        if self._ls_last_fail_time > 0:
            elapsed = time.monotonic() - self._ls_last_fail_time
            if self._ls_retry_count >= self.MAX_LS_RETRIES:
                if elapsed >= self.LS_RETRY_RESET_SEC:
                    logger.info("LS retry reset sec elapsed (%.0fs). Auto-recovering.", elapsed)
                    self._ls_retry_count = 0
                    self._ls_last_fail_time = 0.0
                else:
                    # リトライ上限超過 — 永続的にあきらめる (reset_ls() でリセット可能)
                    return None
            elif elapsed < self.LS_RETRY_COOLDOWN_SEC:
                # クールダウン中 — 再試行しない
                return None
            
            if self._ls_retry_count > 0:
                logger.info(
                    "LS retry attempt %d/%d (%.0fs since last failure)",
                    self._ls_retry_count + 1, self.MAX_LS_RETRIES, elapsed,
                )

        # Strategy 1: IDE LS に接続
        try:
            from mekhane.ochema.antigravity_client import AntigravityClient
            self._ls_client = AntigravityClient()
            logger.info(
                "LS client connected (IDE): PID=%s Port=%s",
                self._ls_client.pid, self._ls_client.port,
            )
            # 成功 — リトライ状態をリセット
            self._ls_retry_count = 0
            self._ls_last_fail_time = 0.0
            self._refresh_dynamic_models()
            self._update_quota_cache()
            return self._ls_client
        except (Exception, OSError) as e:  # noqa: BLE001
            logger.debug("IDE LS unavailable: %s", e)

        if remote_ls_required:
            self._ls_retry_count += 1
            self._ls_last_fail_time = time.monotonic()
            logger.warning("Remote LS required. Local Non-Standalone fallback is disabled.")
            return None

        # Strategy 2: NonStandaloneLSManager で独立 LS を起動
        try:
            from mekhane.ochema.ls_manager import NonStandaloneLSManager
            from mekhane.ochema.antigravity_client import AntigravityClient
            self._nonstd_mgr = NonStandaloneLSManager()
            ls_info = self._nonstd_mgr.start()
            self._ls_client = AntigravityClient(ls_info=ls_info)
            logger.info(
                "LS client connected (Non-Standalone): PID=%s Port=%s",
                self._ls_client.pid, self._ls_client.port,
            )
            # 成功 — リトライ状態をリセット
            self._ls_retry_count = 0
            self._ls_last_fail_time = 0.0
            self._refresh_dynamic_models()
            self._update_quota_cache()
            return self._ls_client
        except (Exception, OSError) as e:  # noqa: BLE001
            self._ls_retry_count += 1
            self._ls_last_fail_time = time.monotonic()
            if self._ls_retry_count >= self.MAX_LS_RETRIES:
                logger.error(
                    "LS connection failed %d/%d times. Giving up. "
                    "Call OchemaService.reset() to retry.",
                    self._ls_retry_count, self.MAX_LS_RETRIES,
                )
            else:
                logger.warning(
                    "LS connection failed (%d/%d). Will retry in %ds: %s",
                    self._ls_retry_count, self.MAX_LS_RETRIES,
                    self.LS_RETRY_COOLDOWN_SEC, e,
                )
            return None

    def _get_cortex_client(self, account: str = "default") -> Any:
        """Get CortexClient for account (lazy, cached per account)."""
        if account in self._cortex_clients:
            return self._cortex_clients[account]

        from mekhane.ochema.cortex_client import CortexClient
        client = CortexClient(
            model=DEFAULT_MODEL, 
            account=account, 
            cooldown_manager=self._provider_cooldown
        )
        self._cortex_clients[account] = client
        logger.info("CortexClient initialized (account=%s)", account)
        return client

    # --- Routing ---

    def _is_claude_model(self, model: str) -> bool:
        """Check if model is a Claude model."""
        return model in CLAUDE_MODEL_MAP

    def _resolve_model_config_id(self, model: str) -> str:
        """Resolve friendly name to model_config_id for generateChat."""
        return CLAUDE_MODEL_MAP.get(model, model)

    def _resolve_ls_proto_model(self, model: str) -> str:
        """Resolve friendly name to LS proto enum.

        優先順位:
        1. 動的キャッシュ (LS から取得した実際の proto enum)
        2. ハードコード CLAUDE_MODEL_MAP
        3. MODEL_ プレフィックスならそのまま
        4. デフォルトフォールバック
        """
        # Step 0: 動的キャッシュから検索 (LS バイナリ更新に追従)
        if self._dynamic_claude_models:
            lower = model.lower()
            if "opus" in lower:
                dyn = self._dynamic_claude_models.get("opus")
                if dyn:
                    return dyn
            elif "sonnet" in lower or "claude" in lower:
                dyn = self._dynamic_claude_models.get("sonnet")
                if dyn:
                    return dyn
        # Step 1: ハードコードマップ
        proto = CLAUDE_MODEL_MAP.get(model)
        if proto:
            return proto
        # Step 2: proto enum 形式ならそのまま返す
        if model.startswith("MODEL_"):
            return model
        # Step 3: フォールバック (デフォルトモデル)
        return "MODEL_PLACEHOLDER_M35"

    def _refresh_dynamic_models(self) -> None:
        """LS のモデル一覧から Claude モデルの proto enum を動的に取得しキャッシュする。

        DX-010 §F.7 K2: GetCascadeModelConfigData は空を返すことがあるため、
        失敗時はハードコードフォールバックを維持する。
        """
        ls = self._ls_client
        if not ls:
            return
        try:
            models = ls.list_models()
            for m in models:
                name = m.get("name", "").upper()
                label = m.get("label", "").lower()
                if not name.startswith("MODEL_"):
                    continue
                # Claude モデルを label から分類
                if "opus" in label:
                    self._dynamic_claude_models["opus"] = name
                elif "sonnet" in label or "claude" in label:
                    self._dynamic_claude_models["sonnet"] = name
            if self._dynamic_claude_models:
                logger.info(
                    "Dynamic Claude models discovered: %s",
                    self._dynamic_claude_models,
                )
        except (Exception, OSError, json.JSONDecodeError, KeyError) as e:  # noqa: BLE001
            logger.debug("Dynamic model discovery failed (using hardcoded): %s", e)

    # --- Core API ---

    # PURPOSE: Build ordered ModelCandidate list for fallback engine
    def _build_candidates(self, model: str) -> list["ModelCandidate"]:
        """Build ordered candidate list based on requested model.

        Routing logic:
        - Vertex Claude models → [vertex, ls] (Vertex primary, LS fallback)
        - Claude models (non-Vertex) → [ls] (LS only, no REST fallback)
        - Gemini/Cortex models → [cortex] (single candidate)
        """
        from mekhane.ochema.model_fallback import ModelCandidate

        if model in VERTEX_CLAUDE_MODELS:
            # Vertex AI → LS fallback chain
            return [
                ModelCandidate(provider="vertex", model=model),
                ModelCandidate(provider="ls", model="claude-opus"),
            ]
        elif self._is_claude_model(model):
            # Claude via LS only (REST is false positive)
            return [
                ModelCandidate(provider="ls", model=model),
            ]
        else:
            # Gemini / Cortex
            return [
                ModelCandidate(provider="cortex", model=model),
            ]

    # PURPOSE: Execute a single attempt for the given provider/model pair
    def _execute_attempt(
        self,
        message: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        account: str = "default",
        response_model: Optional[Any] = None,
    ) -> "Callable[[str, str], LLMResponse]":
        """Return a callback that routes to the appropriate provider method.

        The returned callable has signature (provider, model) → LLMResponse.
        """
        def _attempt(provider: str, model: str) -> "LLMResponse":
            if provider == "vertex":
                return self._ask_vertex_claude(
                    message,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    response_model=response_model,
                )
            elif provider == "ls":
                return self._ask_ls(
                    message,
                    model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    timeout=timeout,
                    response_model=response_model,
                )
            else:  # cortex
                return self._ask_cortex(
                    message, model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    timeout=timeout,
                    account=account,
                    response_model=response_model,
                )
        return _attempt

    def _parse_structured_response(self, resp: "LLMResponse", response_model: Optional[Any]) -> "LLMResponse":
        """Parse structured output from response text using Pydantic model."""
        if response_model is None:
            return resp

        # Strip markdown code blocks if the model wrapped the JSON in them
        clean_text = resp.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        elif clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        try:
            try:
                resp.parsed = response_model.model_validate_json(clean_text)
            except AttributeError:
                resp.parsed = response_model.parse_raw(clean_text)
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            logger.error("Failed to parse structured output: %s", e)
            resp.parsed = None

        return resp

    def ask(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
        *,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        account: str = "default",
        response_model: Optional[Any] = None,
    ) -> "LLMResponse":
        """Send a prompt and get a response.

        Routes to the appropriate client based on model name, with automatic
        model fallback via run_with_model_fallback_sync:
        - opus-vertex, opus-direct → Vertex AI → LS fallback
        - claude-* → LS (ConnectRPC) only
        - gemini-*, cortex-* → CortexClient

        Args:
            message: The prompt text
            model: Model name (see AVAILABLE_MODELS)
            system_instruction: Optional system prompt (Cortex only)
            temperature: Generation temperature
            max_tokens: Max output tokens
            thinking_budget: Thinking budget (Cortex only)
            timeout: Request timeout in seconds
            account: Account to use for CortexClient

        Returns:
            LLMResponse with text, thinking, model, token_usage
        """
        from mekhane.ochema.model_fallback import (
            AllCandidatesFailedError,
            run_with_model_fallback_sync,
        )

        candidates = self._build_candidates(model)
        attempt_fn = self._execute_attempt(
            message,
            system_instruction=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            timeout=timeout,
            account=account,
            response_model=response_model,
        )

        # Single candidate — skip fallback overhead, call directly
        if len(candidates) == 1:
            c = candidates[0]
            resp = attempt_fn(c.provider, c.model)
            return self._parse_structured_response(resp, response_model)

        # Multiple candidates — use fallback engine
        try:
            result = run_with_model_fallback_sync(
                candidates=candidates,
                run=attempt_fn,
                cooldown_manager=self._provider_cooldown,
                deadline=time.monotonic() + timeout * 2,  # 2x timeout for total
            )
            if result.attempts:
                logger.info(
                    "Model fallback succeeded: provider=%s after %d attempt(s)",
                    result.provider,
                    len(result.attempts),
                )
            return self._parse_structured_response(result.result, response_model)
        except AllCandidatesFailedError as e:
            logger.error("All model candidates failed: %s", e)
            raise

    # PURPOSE: Execute a single async attempt for the given provider/model pair
    def _execute_attempt_async(
        self,
        message: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        account: str = "default",
        response_model: Optional[Any] = None,
    ) -> "Callable[[str, str], Awaitable[LLMResponse]]":
        """Return an async callback that routes to the appropriate provider method."""
        async def _attempt_async(provider: str, model: str) -> "LLMResponse":
            import asyncio
            import functools
            if provider == "vertex":
                return await asyncio.to_thread(
                    functools.partial(
                        self._ask_vertex_claude,
                        message,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        timeout=timeout,
                        response_model=response_model,
                    )
                )
            elif provider == "ls":
                return await asyncio.to_thread(
                    functools.partial(
                        self._ask_ls,
                        message,
                        model=model,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        thinking_budget=thinking_budget,
                        timeout=timeout,
                        response_model=response_model,
                    )
                )
            elif provider == "cortex":
                client = self._get_cortex_client(account)
                logger.info("Cortex ask_async: model=%s account=%s", model, account)
                await asyncio.to_thread(self._request_semaphore.acquire)
                try:
                    return await client.ask_async(
                        message,
                        model=model,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        thinking_budget=thinking_budget,
                        timeout=timeout,
                        response_model=response_model,
                    )
                finally:
                    self._request_semaphore.release()
            else:
                raise ValueError(f"Unknown provider: {provider}")

        return _attempt_async

    async def ask_async(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
        **kwargs: Any,
    ) -> "LLMResponse":
        """Async version of ask(). Uses run_with_model_fallback internally."""
        from mekhane.ochema.model_fallback import run_with_model_fallback, AllCandidatesFailedError
        
        candidates = self._build_candidates(model)
        
        attempt_kwargs = {
            "system_instruction": kwargs.get("system_instruction"),
            "temperature": kwargs.get("temperature"),
            "max_tokens": kwargs.get("max_tokens"),
            "thinking_budget": kwargs.get("thinking_budget"),
            "timeout": kwargs.get("timeout", 120.0),
            "account": kwargs.get("account", "default"),
            "response_model": kwargs.get("response_model"),
        }
        
        attempt_cb = self._execute_attempt_async(message, **attempt_kwargs)
        
        try:
            result = await run_with_model_fallback(
                candidates=candidates,
                run=attempt_cb,
                cooldown_manager=self._provider_cooldown,
            )
            if result.attempts:
                logger.info(
                    "Model fallback succeeded (async): provider=%s after %d attempt(s)",
                    result.provider,
                    len(result.attempts),
                )
            return self._parse_structured_response(result.result, attempt_kwargs.get("response_model"))
        except AllCandidatesFailedError as e:
            logger.error("All model candidates failed (async): %s", e)
            raise

    def stream(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
        *,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        account: str = "default",
    ) -> Generator[str, None, None]:
        """Stream a response token by token.

        Routes to:
        - LS ConnectRPC (Claude — REST は偽陽性, DX-010 v9.1)
        - Cortex ask_stream (Gemini models with system_instruction support)

        Yields text chunks as they arrive.
        """
        if model in VERTEX_CLAUDE_MODELS:
            # Vertex Claude — ストリーミング未対応、LS フォールバック
            raise NotImplementedError(
                "Vertex Claude はストリーミング未対応です。"
                "ask(model='opus-vertex') を使用するか、"
                "stream(model='claude-opus') で LS 経由をご利用ください。"
            )
        elif self._is_claude_model(model):
            # Claude: LS (ConnectRPC) 経由のみ
            # REST generateChat は偽陽性のため使用禁止 (DX-010 v9.1)
            ls = self._get_ls_client()
            if not ls:
                raise RuntimeError(
                    "Claude streaming には Language Server が必要です。"
                    "IDE を起動してから再試行してください。"
                )
            proto_model = self._resolve_ls_proto_model(model)
            logger.info("Claude stream via LS: model=%s proto=%s", model, proto_model)
            yield from ls.chat_stream(message, model=proto_model, timeout=timeout)
        else:
            # Gemini → Cortex streaming (supports system_instruction etc.)
            client = self._get_cortex_client(account)
            yield from client.ask_stream(
                message,
                model=model,
                system_instruction=system_instruction,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking_budget=thinking_budget,
                timeout=timeout,
            )

    # --- Info API ---

    def models(self, account: str = "default") -> dict[str, Any]:
        """Return all available models with provider status.

        Merges hardcoded AVAILABLE_MODELS with dynamically fetched models (F6).

        Returns:
            {
                "models": {model_id: display_name, ...},
                "default": str,
                "ls_available": bool,
                "cortex_available": bool,
                "dynamic_models": list,
            }
        """
        # Start with hardcoded models
        merged = dict(AVAILABLE_MODELS)

        # Attempt dynamic model discovery (F6)
        dynamic: list[dict[str, Any]] = []
        try:
            client = self._get_cortex_client(account)
            dynamic = client.fetch_available_models()
            for m in dynamic:
                mid = m.get("id", m.get("modelId", ""))
                name = m.get("displayName", mid)
                if mid and mid not in merged:
                    merged[mid] = name
        except (Exception, OSError, json.JSONDecodeError, KeyError) as e:  # noqa: BLE001
            logger.debug("Dynamic model fetch failed: %s", e)

        return {
            "models": merged,
            "default": DEFAULT_MODEL,
            "ls_available": self.ls_available,
            "cortex_available": self.cortex_available,
            "dynamic_models": dynamic,
        }

    def status(self) -> dict[str, Any]:
        """Return connection status for all providers."""
        result: dict[str, Any] = {
            "ls_available": self.ls_available,
            "cortex_available": self.cortex_available,
        }

        ls = self._get_ls_client()
        if ls:
            try:
                status = ls.get_status()
                user_status = status.get("userStatus", {})
                result["ls"] = {
                    "pid": ls.pid,
                    "port": ls.port,
                    "workspace": ls.workspace,
                    "name": user_status.get("name", "N/A"),
                }
            except (Exception, OSError, json.JSONDecodeError, KeyError) as e:  # noqa: BLE001
                result["ls_error"] = str(e)

        # Token cache info (F3)
        from mekhane.ochema.cortex_client import _TOKEN_CACHE, _TOKEN_TTL
        if _TOKEN_CACHE.exists():
            import time
            age = time.time() - _TOKEN_CACHE.stat().st_mtime
            remaining = max(0, _TOKEN_TTL - age)
            result["token_cache"] = {
                "remaining_seconds": int(remaining),
                "remaining_human": f"{int(remaining // 60)}m{int(remaining % 60)}s",
                "expired": remaining <= 0,
            }

        return result

    def quota(self, account: str = "default") -> dict[str, Any]:
        """Return unified quota info from LS and Cortex.

        Includes token health from TokenVault.

        Note: REST API shows only Gemini quotas (100% increments).
        Full Premium model pool (Claude+GPT-OSS, 20% increments, 5h reset)
        is only visible via LS ConnectRPC. See DX-010 §K for details.
        """
        result: dict[str, Any] = {"ls": None, "cortex": None, "token_health": None}

        # LS quota
        ls = self._get_ls_client()
        if ls:
            try:
                result["ls"] = ls.quota_status()
            except (Exception, OSError, json.JSONDecodeError, KeyError) as e:  # noqa: BLE001
                logger.debug("LS quota error: %s", e)

        # Cortex quota
        try:
            cortex = self._get_cortex_client(account)
            result["cortex"] = cortex.retrieve_quota()
        except (Exception, OSError, json.JSONDecodeError, KeyError) as e:  # noqa: BLE001
            logger.debug("Cortex quota error: %s", e)

        # Warn if any quota is low
        self._check_low_quota(result)

        # Token health (F5)
        try:
            result["token_health"] = cortex.vault.status()  # type: ignore[possibly-undefined]
        except (OSError, KeyError) as e:
            logger.debug("Token health error: %s", e)

        return result
        
    def _check_low_quota(self, quota_data: dict[str, Any]) -> None:
        """Log a warning if any quota is below the threshold."""
        threshold = self.QUOTA_WARNING_THRESHOLD
        
        cortex = quota_data.get("cortex")
        if cortex:
            for q in cortex.get("quotas", []):
                # e.g. "40%"
                val_str = q.get("remaining", "100%")
                try:
                    val = float(val_str.replace("%", ""))
                    if val <= threshold:
                        logger.warning("Cortex quota critical: %s is at %.1f%%", q.get("model", "unknown"), val)
                except ValueError:
                    pass
                    
        ls = quota_data.get("ls")
        if ls:
            features = ls.get("status", {}).get("features", {})
            for name, details in features.items():
                if not isinstance(details, dict):
                    continue
                rem = details.get("remainingUsageRequests")
                limit = details.get("limitUsageRequests")
                if rem is not None and limit and limit > 0:
                    val = (rem / limit) * 100
                    if val <= threshold:
                        logger.warning("LS quota critical: %s is at %.1f%% (%d/%d)", name, val, rem, limit)

    def ls_models(self) -> list[dict[str, Any]]:
        """Return LS model list with quota info. Empty list if unavailable."""
        ls = self._get_ls_client()
        if not ls:
            return []
        try:
            return ls.list_models()
        except (Exception, OSError, json.JSONDecodeError, KeyError):  # noqa: BLE001
            return []

    # --- Session API (LS only) ---

    def session_info(self, cascade_id: Optional[str] = None) -> dict[str, Any]:
        """Get session info from LS. Raises if LS unavailable."""
        ls = self._get_ls_client()
        if not ls:
            raise RuntimeError("Language Server is not available")
        return ls.session_info(cascade_id)

    def context_health(self, cascade_id: Optional[str] = None) -> dict[str, Any]:
        """Get context health from LS. Raises if LS unavailable."""
        ls = self._get_ls_client()
        if not ls:
            raise RuntimeError("Language Server is not available")
        return ls.context_health(cascade_id)

    # --- Properties ---

    @property
    def ls_available(self) -> bool:
        """Check if Language Server is reachable."""
        return self._get_ls_client() is not None

    @property
    def cortex_available(self) -> bool:
        """Check if Cortex API is authenticated."""
        from mekhane.ochema.cortex_client import CortexAuthError

        try:
            client = self._get_cortex_client()
            client._get_token()
            return True
        except (CortexAuthError, FileNotFoundError):
            return False

    # --- Quota Guard ---

    def _preflight_quota_check(self, model: str) -> None:
        """Claude リクエスト前に Quota を検査する。

        キャッシュ未取得 or TTL 超過時はチェックをスキップ (初回は通す)。
        0% → QuotaExhaustedError、閾値以下 → warning ログ。
        """
        if self._quota_cache is None:
            return  # キャッシュなし → スキップ
        if time.monotonic() - self._quota_cache_time > self.QUOTA_CACHE_TTL_SEC:
            self._quota_cache = None  # 期限切れ → 無効化してスキップ
            return

        # キャッシュからClaude系モデルの残量を探す
        models = self._quota_cache.get("models", [])
        for m in models:
            label = m.get("label", "").lower()
            if "claude" not in label and "premium" not in label:
                continue
            remaining = m.get("remaining_pct", 100)
            if remaining <= 0:
                raise QuotaExhaustedError(
                    f"Claude quota exhausted (0%). "
                    f"Reset: {m.get('reset_time', 'unknown')}. "
                    f"Model: {model}"
                )
            if remaining <= self.QUOTA_WARNING_THRESHOLD:
                logger.warning(
                    "Claude quota low: %d%% remaining (model=%s)",
                    remaining, model,
                )
            return  # 最初の一致で判定完了

    def _update_quota_cache(self) -> None:
        """LS から Quota 情報を取得しキャッシュを更新する。

        _ask_ls() 成功後にバックグラウンドで呼び出す。
        失敗してもリクエスト処理には影響しない。
        """
        ls = self._ls_client
        if not ls:
            return
        try:
            self._quota_cache = ls.quota_status()
            self._quota_cache_time = time.monotonic()
            logger.debug("Quota cache updated: %d models", len(self._quota_cache.get("models", [])))
        except (Exception, OSError, json.JSONDecodeError, KeyError) as e:  # noqa: BLE001
            logger.debug("Quota cache update failed: %s", e)

    # --- Internal ---

    def _log_thinking_to_tape(
        self,
        result: "LLMResponse",
        model: str,
        proto_model: str,
    ) -> None:
        """Thinking メタデータを tape に JSONL で永続化する。

        失敗しても LLM 応答には影響しない (best-effort)。
        """
        if not result.thinking:
            return  # thinking なし → ログ不要
        try:
            from mekhane.ccl.tape import TapeWriter
            tape = TapeWriter()
            tape.log(
                wf="ochema",
                step="THINKING",
                model=proto_model,
                model_alias=model,
                cascade_id=result.cascade_id,
                message_id=result.message_id,
                thinking_duration=result.thinking_duration,
                stop_reason=result.stop_reason,
                thinking_length=len(result.thinking),
                thinking_preview=result.thinking[:200],
            )
        except (OSError, json.JSONDecodeError) as e:
            logger.debug("Tape logging failed (non-fatal): %s", e)

        # Prostasia TAINT 分析 (best-effort)
        try:
            from mekhane.agent_guard.prostasia import get_prostasia
            prostasia = get_prostasia()
            taints = prostasia.analyze_thinking(result.thinking)
            if taints:
                logger.warning(
                    "Thinking TAINT detected: %s",
                    [(t["taint_type"], t["severity"]) for t in taints],
                )
        except (OSError, json.JSONDecodeError, KeyError) as e:
            logger.debug("Thinking TAINT analysis failed (non-fatal): %s", e)

    # --- Vertex AI Claude Provider ---

    def _ask_vertex_claude(
        self,
        message: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: float = 120.0,
        response_model: Optional[Any] = None,
    ) -> "LLMResponse":
        """Vertex AI rawPredict で Claude Opus 4.6 を呼ぶ (1M コンテキスト)。

        6 垢ラウンドロビン + 4 リージョンフェイルオーバー。
        全滅時は LS にフォールバック。
        """
        from mekhane.ochema.types import LLMResponse

        try:
            from mekhane.ochema.vertex_claude import VertexClaudeClient

            # シングルトン的に管理 (初回のみ生成)
            if self._vertex_client is None:
                self._vertex_client = VertexClaudeClient()
                logger.info(
                    "VertexClaudeClient initialized: %d accounts, budget=$%.0f",
                    len(self._vertex_client.accounts),
                    self._vertex_client.costs.budget_usd,
                )

            resp = self._vertex_client.ask(
                message,
                system=system_instruction or "",
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                response_model=response_model,
            )

            response = LLMResponse(
                text=resp.text,
                model=f"claude-opus-4-6 ({resp.provider}:{resp.account}:{resp.region})",
                token_usage={
                    "input_tokens": resp.input_tokens,
                    "output_tokens": resp.output_tokens,
                    "total_tokens": resp.total_tokens,
                    "estimated_cost_usd": resp.estimated_cost_usd,
                },
                stop_reason=resp.stop_reason,
            )
            if hasattr(resp, "parsed") and resp.parsed is not None:
                response.parsed = resp.parsed
            return response
        except Exception as e:  # noqa: BLE001
            # Manual LS fallback removed (C-2): ask() routes through
            # run_with_model_fallback_sync which handles Vertex → LS fallback.
            logger.error("Vertex Claude failed: %s", e)
            raise

    def _ask_ls(
        self,
        message: str,
        model: str,
        *,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        cascade_id: str = "",
        _retry: bool = False,
        response_model: Optional[Any] = None,
    ) -> "LLMResponse":
        """Send via AntigravityClient (LS). Supports stateful chat via cascade_id.

        Args:
            cascade_id: 既存の cascadeId を再利用する場合に指定。
                        空文字列の場合は新規 cascade を開始。
            _retry: 内部用 (K9 エラー時のリトライフラグ)。
        """

        ls = self._get_ls_client()
        if not ls:
            raise RuntimeError(
                "Language Server が起動していません。"
                "IDE を開いてから再試行してください。"
            )

        # Quota プリフライトチェック (枯渇時は LS に送信せず即エラー)
        self._preflight_quota_check(model)

        proto_model = self._resolve_ls_proto_model(model)

        if system_instruction and str(system_instruction).strip():
            full_message = f"{str(system_instruction).strip()}\n\n{message}"
        else:
            full_message = message

        try:
            with self._request_semaphore:
                if cascade_id:
                    # Stateful chat: 既存の cascade に追加メッセージを送信
                    logger.info("LS chat: model=%s proto=%s cascade=%s", model, proto_model, cascade_id[:12])
                    # Note: cascade doesn't currently support response_model natively, we pass it down
                    result = ls.chat(full_message, model=proto_model, cascade_id=cascade_id, timeout=timeout, response_model=response_model)
                else:
                    # Single-shot: 新規 cascade を開始
                    logger.info("LS ask: model=%s proto=%s", model, proto_model)
                    result = ls.ask(full_message, model=proto_model, timeout=timeout, response_model=response_model)

            # Thinking メタデータを tape に永続化 (失敗しても応答に影響しない)
            self._log_thinking_to_tape(result, model, proto_model)
            return result
        except RuntimeError as e:
            if "model not found" in str(e).lower() and not _retry:
                logger.warning("LS K9 error (model not found) detected. Forcing LS restart for auth re-provision.")
                # LS を強制再起動して再試行
                self._ls_client = None
                if self._nonstd_mgr is not None:
                    try:
                        self._nonstd_mgr.stop()
                    except OSError:
                        pass
                    self._nonstd_mgr = None
                # セマフォは with 文を抜けて自動解放されているため、再帰時に二重消費しない
                return self._ask_ls(
                    message, model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    timeout=timeout,
                    cascade_id=cascade_id, _retry=True, response_model=response_model
                )
            raise
        except TimeoutError as e:
            # Cascade ポーリング期限切れや接続先の取り残しに対し、キャッシュを捨てて 1 回だけ再試行
            if not _retry:
                logger.warning(
                    "LS TimeoutError; invalidating cached client and retrying once: %s",
                    e,
                )
                self._ls_client = None
                return self._ask_ls(
                    message, model,
                    system_instruction=system_instruction,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    thinking_budget=thinking_budget,
                    timeout=timeout,
                    cascade_id=cascade_id, _retry=True, response_model=response_model,
                )
            raise

    def _ask_cortex(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
        *,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        account: str = "default",
        response_model: Optional[Any] = None,
    ) -> "LLMResponse":
        """Send via CortexClient (Cortex API direct)."""
        client = self._get_cortex_client(account)
        logger.info("Cortex ask: model=%s account=%s", model, account)
        self._request_semaphore.acquire()
        try:
            return client.ask(
                message,
                model=model,
                system_instruction=system_instruction,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking_budget=thinking_budget,
                timeout=timeout,
                response_model=response_model,
            )
        finally:
            self._request_semaphore.release()

    # --- Chat API (generateChat) ---

    def chat(
        self,
        message: str,
        model: str = "",
        history: list[dict] | None = None,
        tier_id: str = "",
        include_thinking: bool = True,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        account: str = "default",
        cascade_id: str = "",
    ) -> "LLMResponse":
        """generateChat API でチャット応答を取得。

        ⚠️ Claude モデルは REST generateChat では偽陽性 (DX-010 v9.1)。
        Claude 指定時は LS 経由にフォールバックする。

        Claude (LS 経由) はサーバーサイドで cascade_id により会話履歴を保持。
        Gemini (Cortex 経由) はクライアントサイドで history を再送信。
        """
        if self._is_claude_model(model):
            # Claude: LS 経由 stateful chat (cascadeId で会話履歴を保持)
            logger.info(
                "Claude chat via LS: model=%s cascade=%s (DX-010 v9.1)",
                model, cascade_id[:12] if cascade_id else "new",
            )
            return self._ask_ls(message, model, timeout=timeout, cascade_id=cascade_id)

        resolved_model = self._resolve_model_config_id(model) if model else model
        client = self._get_cortex_client(account)
        logger.info("Cortex chat: model=%s account=%s", resolved_model or "default", account)
        return client.chat(
            message=message,
            model=resolved_model,
            history=history,
            tier_id=tier_id,
            include_thinking=include_thinking,
            thinking_budget=thinking_budget,
            timeout=timeout,
        )

    def _ask_cortex_chat(
        self,
        message: str,
        model: str = "",
        timeout: float = 120.0,
        account: str = "default",
        thinking_budget: Optional[int] = 32768,
    ) -> "LLMResponse":
        """Send via CortexClient.chat() (generateChat API direct).

        ⚠️ Claude は REST generateChat で偽陽性 (DX-010 v9.1) のため LS 迂回。
        """
        if self._is_claude_model(model):
            logger.warning(
                "_ask_cortex_chat: Claude '%s' は REST 不可。LS に迂回 (DX-010 v9.1)", model,
            )
            return self._ask_ls(message, model, timeout=timeout)

        resolved = self._resolve_model_config_id(model) if model else model
        client = self._get_cortex_client(account)
        logger.info("Cortex chat direct: model=%s account=%s", resolved or "default", account)
        return client.chat(
            message=message,
            model=resolved,
            timeout=timeout,
            thinking_budget=thinking_budget,
        )

    def start_chat(
        self,
        model: str = "",
        tier_id: str = "",
        include_thinking: bool = True,
        account: str = "default",
    ) -> Any:
        """マルチターン generateChat 会話を開始する。"""
        client = self._get_cortex_client(account)
        resolved_model = self._resolve_model_config_id(model) if model else model
        return client.start_chat(
            model=resolved_model,
            tier_id=tier_id,
            include_thinking=include_thinking,
        )

    # --- Tool Use API (F0 + F3) ---

    # Known Claude model prefixes for routing
    _CLAUDE_MODELS = {"claude", "model_claude", "model_placeholder"}

    def _is_claude_model(self, model: str) -> bool:
        """Check if model name refers to a Claude model (LS route)."""
        lower = model.lower().replace("-", "_")
        return any(lower.startswith(prefix) for prefix in self._CLAUDE_MODELS)

    def ask_with_tools(
        self,
        message: str,
        model: str = DEFAULT_MODEL,
        *,
        system_instruction: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        max_iterations: int = 10,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        account: str = "default",
    ) -> "LLMResponse":
        """Send a prompt with tool use support.

        Routes automatically based on model:
        - Gemini models → CortexClient (native Function Calling)
        - Claude models → AntigravityClient (text-based Tool Use)

        AI がローカルファイルを読み書き・コマンド実行できるエージェントループ。

        Args:
            message: The prompt text
            model: Model name (gemini-* or claude-*/MODEL_PLACEHOLDER_*)
            system_instruction: Optional system prompt (or template name)
            tools: Custom tool definitions (default: file/cmd tools)
            max_iterations: Max tool call rounds
            temperature: Generation temperature
            max_tokens: Max output tokens
            thinking_budget: Thinking token budget (Gemini only)
            timeout: Per-API-call timeout
            account: TokenVault account

        Returns:
            LLMResponse with final text (after tool calls resolved)
        """
        # Resolve system instruction template names
        from mekhane.ochema.tools import get_system_template
        if system_instruction and system_instruction in (
            "default", "hgk_citizen", "code_review", "researcher"
        ):
            system_instruction = get_system_template(system_instruction)

        if self._is_claude_model(model):
            return self._ask_with_tools_claude(
                message=message,
                model=model,
                system_instruction=system_instruction,
                max_iterations=max_iterations,
                timeout=timeout,
                account=account,
            )
        else:
            return self._ask_with_tools_gemini(
                message=message,
                model=model,
                system_instruction=system_instruction,
                tools=tools,
                max_iterations=max_iterations,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking_budget=thinking_budget,
                timeout=timeout,
                account=account,
            )

    def _ask_with_tools_gemini(
        self,
        message: str,
        model: str,
        *,
        system_instruction: Optional[str] = None,
        tools: Optional[list[dict]] = None,
        max_iterations: int = 10,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
        account: str = "default",
    ) -> "LLMResponse":
        """Gemini route: native Function Calling."""
        client = self._get_cortex_client(account)
        logger.info("Tool use (Gemini): model=%s account=%s", model, account)
        return client.ask_with_tools(
            message=message,
            model=model,
            system_instruction=system_instruction,
            tools=tools,
            max_iterations=max_iterations,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking_budget=thinking_budget,
            timeout=timeout,
        )

    def _ask_with_tools_claude(
        self,
        message: str,
        model: str,
        *,
        system_instruction: Optional[str] = None,
        max_iterations: int = 10,
        timeout: float = 120.0,
        account: str = "default",
    ) -> "LLMResponse":
        """Claude Tool Use: LS primary → Cortex chat fallback.

        Tries:
        1. LS ask() — tested and working (system prompt with tool definitions)
        2. Cortex generateChat — if LS unavailable

        System prompt teaches Claude the tool_call format,
        then parses responses for tool invocations.
        """
        from mekhane.ochema.tools import (
            execute_tool,
            get_claude_system_prompt,
            has_tool_calls,
            parse_tool_calls_from_text,
        )

        logger.info("Tool use (Claude): model=%s", model)

        # Build system prompt with tool descriptions
        tool_system = get_claude_system_prompt(system_instruction or "")

        # First turn: include system prompt + user message
        first_message = f"[System Instructions]\n{tool_system}\n\n[User Request]\n{message}"
        current_message = first_message

        from mekhane.ochema.types import LLMResponse

        def _call_claude(msg: str) -> LLMResponse:
            """Try LS first, then Cortex chat."""
            # Try LS (primary — confirmed working)
            try:
                ls_client = self._get_ls_client()
                return ls_client.ask(message=msg, model=model, timeout=timeout)
            except Exception as e_ls:  # Intentional Catch-All (LS Call Boundary)  # noqa: BLE001
                logger.info("LS unavailable (%s), trying Cortex chat", e_ls)

            # Try Cortex chat (fallback)
            try:
                config_id = CLAUDE_MODEL_MAP.get(model, "claude-sonnet-4-5")
                client = self._get_cortex_client(account)
                return client.chat(message=msg, model=config_id, timeout=timeout)
            except Exception as e_cx:  # noqa: BLE001
                raise RuntimeError(f"Claude unavailable: LS={e_ls if 'e_ls' in locals() else 'unknown'}, Cortex={e_cx}") from e_cx

        for iteration in range(max_iterations):
            logger.info("Claude tool loop: iteration %d/%d", iteration + 1, max_iterations)

            response = _call_claude(current_message)

            # Check if Claude wants to use tools
            if not has_tool_calls(response.text):
                logger.info("Claude tool loop complete: %d iterations", iteration + 1)
                return response

            # Parse and execute tool calls
            tool_calls = parse_tool_calls_from_text(response.text)

            tool_results = []
            for tc in tool_calls:
                name = tc["name"]
                args = tc["args"]
                logger.info("Claude tool call [%d]: %s(%s)", iteration + 1, name, args)
                result = execute_tool(name, args)
                tool_results.append(f"### Tool: {name}\nArgs: {args}\nResult:\n```json\n{json.dumps(result, ensure_ascii=False, indent=2)}\n```")

            # Build follow-up message with tool results
            results_text = "\n\n".join(tool_results)
            current_message = (
                f"Here are the results of your tool calls:\n\n{results_text}\n\n"
                f"Based on these results, continue your analysis. "
                f"If you need more information, make additional tool calls. "
                f"Otherwise, provide your final answer."
            )

        # Max iterations reached
        logger.warning("Claude tool loop: max iterations (%d) reached", max_iterations)
        return LLMResponse(
            text="[Tool Use] Maximum iterations reached. Last tool calls may be incomplete.",
            model=model,
        )

    def __repr__(self) -> str:
        return (
            f"OchemaService("
            f"ls={'✓' if self._ls_client else '✗'}, "
            f"cortex={'✓' if self._cortex_clients else '✗'})"
        )
