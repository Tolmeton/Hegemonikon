# PROOF: [L2/インフラ] <- mekhane/ochema/cortex_chat.py A0→generateChat API チャット層
# PURPOSE: generateChat / streamGenerateChat + ChatConversation を CortexClient から分離
"""CortexChat — generateChat API layer.

Handles:
- chat() — single-turn generateChat
- chat_stream() — streaming streamGenerateChat
- start_chat() → ChatConversation — multi-turn conversation management
- _parse_chat_response() — response parsing

Extracted from cortex_client.py for maintainability.
"""


from __future__ import annotations
from typing import Any, Generator, Optional
import json
import logging
import time
import urllib.error
import urllib.request
from typing import TYPE_CHECKING

from mekhane.ochema.types import LLMResponse
from mekhane.ochema.session_store import SessionStore, get_default_store

if TYPE_CHECKING:
    from mekhane.ochema.cortex_auth import CortexAuth
    from mekhane.ochema.cortex_api import CortexAPI

logger = logging.getLogger(__name__)


# --- Constants ---
_COOLDOWN_RATE_LIMIT_BASE = 60
_COOLDOWN_RATE_LIMIT_MID = 180
_COOLDOWN_RATE_LIMIT_MAX = 300
_COOLDOWN_CAPACITY_BASE = 180
_COOLDOWN_CAPACITY_MAX = 300

# Reverse map: model_config_id → human-friendly display name
_MODEL_DISPLAY_NAMES: dict[str, str] = {
    "claude-sonnet-4-5": "Claude Sonnet 4.6",
    "claude-sonnet-4-6": "Claude Sonnet 4.6",
    "claude-opus-4-6": "Claude Opus 4.6",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro Preview",
    "gemini-3-pro-preview": "Gemini 3 Pro Preview",
    "gemini-2.5-flash": "Gemini 2.5 Flash",
    "gemini-2.0-flash": "Gemini 2.0 Flash",
    "gemini-3-flash-preview": "Gemini 3 Flash Preview",
}


# --- CortexChat ---


# PURPOSE: generateChat 層を CortexClient から分離し、chat 関連の責任を集約する
class CortexChat:
    """generateChat API layer.

    Manages chat(), chat_stream(), start_chat(), and response parsing.
    Composed into CortexClient as self._chat.
    """

    # PURPOSE: CortexAuth と CortexAPI への参照を保持する
    def __init__(self, auth: "CortexAuth", api: "CortexAPI") -> None:
        self._auth = auth
        self._api = api

    def _derive_429_error_kind(self, error_body: str) -> str:
        """Classify 429 body into token-vault error kind."""
        body = (error_body or "").upper()
        if "RESOURCE_EXHAUSTED" in body or "CAPACITY_EXHAUSTED" in body:
            return "capacity"
        return "rate_limit"

    def _compute_429_cooldown(self, error_kind: str, attempt: int) -> int:
        """Return adaptive cooldown seconds by error kind and retry depth."""
        if error_kind == "capacity":
            # Capacity exhaustion usually recovers slower than normal rate limits.
            return _COOLDOWN_CAPACITY_BASE if attempt <= 0 else _COOLDOWN_CAPACITY_MAX
        if attempt <= 0:
            return _COOLDOWN_RATE_LIMIT_BASE
        if attempt <= 2:
            return _COOLDOWN_RATE_LIMIT_MID
        return _COOLDOWN_RATE_LIMIT_MAX

    # PURPOSE: generateChat API で Claude/Gemini チャット応答を取得する。
    #   LS 不要、model_config_id で全モデルにアクセス可能。
    def chat(
        self,
        message: str,
        model: str = "",
        system_instruction: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tier_id: str = "",
        include_thinking: bool = True,
        thinking_budget: Optional[int] = None,
        enable_prompt_enhancement: bool | None = None,
        timeout: float = 120.0,
    ) -> LLMResponse:
        """generateChat API でチャット応答を取得。

        LS を迂回し、cloudcode-pa の generateChat エンドポイントを直接呼び出す。
        model で Claude/Gemini 全モデルを指定可能。

        Args:
            message: 現在のユーザーメッセージ
            model: モデル ID (e.g. "gemini-3.1-pro-preview", "claude-sonnet-4-6")
                   空文字列の場合はサーバーデフォルト (Gemini 3.1 Pro Preview)
            history: 過去の会話履歴 [{"author": 1, "content": "..."}, ...]
                     author: 1=USER, 2=MODEL
            tier_id: モデルルーティング (""=default, "g1-ultra-tier"=Premium)
            include_thinking: Thinking summaries を含めるか
            enable_prompt_enhancement: Google のプロンプト強化 (rewriting) を有効化
                (DX-010 §N.8 T6 バイナリ解析で発見、None=サーバーデフォルト)
            timeout: リクエストタイムアウト (秒)

        Returns:
            LLMResponse with text and metadata
        """
        from mekhane.ochema.cortex_api import _BASE_URL

        token = self._auth.get_token()
        project = self._api._get_project(token)

        hist = list(history) if history else []
        if system_instruction:
            # Prepend system instruction as author=0
            hist.insert(0, {"author": 0, "content": system_instruction})

        payload: dict[str, Any] = {
            "project": project,
            "user_message": message,
            "history": hist,
            "metadata": {"ideType": "IDE_UNSPECIFIED"},
            "includeThinkingSummaries": include_thinking,
        }
        if model:
            payload["model_config_id"] = model
        if tier_id:
            payload["tier_id"] = tier_id
        if enable_prompt_enhancement is not None:
            payload["enablePromptEnhancement"] = enable_prompt_enhancement

        result = self._api._call_api(
            f"{_BASE_URL}:generateChat",
            payload,
            timeout=timeout,
            token_override=token,
        )

        return self._parse_chat_response(result, request_model=model)

    # PURPOSE: generateChat のストリーミング版。チャンクを逐次 yield。
    def chat_stream(
        self,
        message: str,
        model: str = "",
        system_instruction: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tier_id: str = "",
        include_thinking: bool = True,
        thinking_budget: Optional[int] = None,
        timeout: float = 120.0,
    ) -> Generator[str, None, None]:
        """streamGenerateChat API でストリーミングチャット。

        Note: streamGenerateChat は SSE ではなく JSON 配列を返す。
        各要素の "markdown" フィールドをチャンクとして yield する。

        Args:
            (same as chat())

        Yields:
            str: テキストチャンク (markdown フィールドから抽出)
        """
        from mekhane.ochema.cortex_api import _BASE_URL
        from mekhane.ochema.cortex_auth import _TOKEN_CACHE
        from mekhane.ochema.cortex_client import CortexAPIError

        # 429耐性:
        # - 利用可能アカウントを巡回
        # - 短い指数バックオフで再試行
        # - 疑似ストリームには降格しない
        try:
            vault_accounts = list(self._auth.vault._load_vault().get("accounts", {}).keys())  # type: ignore[attr-defined]
        except (OSError, json.JSONDecodeError, AttributeError) as _e:
            logger.debug("Ignored exception: %s", _e)
            vault_accounts = []
        max_attempts = max(2, len(vault_accounts) + 2)
        excluded_accounts: set[str] = set()
        account_429_counts: dict[str, int] = {}

        for attempt in range(max_attempts):
            token = self._auth.get_token()
            project = self._api._get_project(token)

            hist = list(history) if history else []
            if system_instruction:
                # Prepend system instruction as author=0
                hist.insert(0, {"author": 0, "content": system_instruction})

            payload: dict[str, Any] = {
                "project": project,
                "user_message": message,
                "history": hist,
                "metadata": {"ideType": "IDE_UNSPECIFIED"},
                "includeThinkingSummaries": include_thinking,
            }
            if model:
                payload["model_config_id"] = model
            if tier_id:
                payload["tier_id"] = tier_id

            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

            req = urllib.request.Request(
                f"{_BASE_URL}:streamGenerateChat",
                data=data,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    raw = resp.read().decode("utf-8")

                    try:
                        items = json.loads(raw)
                    except json.JSONDecodeError:
                        # Fallback: SSE 形式の場合
                        for line in raw.split("\n"):
                            line = line.strip()
                            if line.startswith("data: "):
                                try:
                                    d = json.loads(line[6:])
                                    # --- Energy Budget Tracking ---
                                    usage: dict[str, Any] = d.get("usageMetadata") or {}
                                    if usage:
                                        try:
                                            p_tok = usage.get("promptTokenCount", 0)
                                            c_tok = usage.get("candidatesTokenCount", 0)
                                            self._auth.vault.record_usage(
                                                self._auth.account,
                                                model or "unknown",
                                                p_tok, c_tok,
                                            )
                                        except Exception as e:  # noqa: BLE001
                                            logger.debug("Failed to record usage: %s", e)
                                    # ------------------------------
                                    md = d.get("markdown", "")
                                    if md:
                                        yield md
                                except json.JSONDecodeError:
                                    continue
                        return

                    # JSON 配列形式: [{markdown: "...", processingDetails: ...}, ...]
                    if isinstance(items, list):
                        # Extract thinkingSummaries from last chunk
                        last_item = items[-1] if items else {}
                        if not isinstance(last_item, dict):
                            last_item = {}

                        details = last_item.get("processingDetails")
                        if not isinstance(details, dict):
                            details = {}

                        # --- Energy Budget Tracking ---
                        usage = details.get("usageMetadata") or last_item.get("usageMetadata")
                        if isinstance(usage, dict):
                            try:
                                p_tok = usage.get("promptTokenCount", 0)
                                c_tok = usage.get("candidatesTokenCount", 0)
                                if isinstance(p_tok, int) and isinstance(c_tok, int):
                                    self._auth.vault.record_usage(
                                        self._auth.account,
                                        model or "unknown",
                                        p_tok, c_tok,
                                    )
                            except Exception as e:  # noqa: BLE001
                                logger.debug("Failed to record usage: %s", e)
                        # ------------------------------

                        summaries = details.get("thinkingSummaries")
                        if isinstance(summaries, list) and summaries:
                            thinking = "\n\n".join(
                                s.get("text", "") for s in summaries if "text" in s
                            ).strip()
                            if thinking:
                                yield f"__THINKING__:{thinking}"
                        for item in items:
                            md = item.get("markdown", "")
                            if md:
                                yield md
                    elif isinstance(items, dict):
                        # Single response — check for thinkingSummaries
                        details = items.get("processingDetails", {})
                        summaries = details.get("thinkingSummaries", [])
                        if summaries:
                            thinking = "\n\n".join(
                                s.get("text", "") for s in summaries if "text" in s
                            ).strip()
                            if thinking:
                                yield f"__THINKING__:{thinking}"
                        md = items.get("markdown", "")
                        if md:
                            yield md
                return
            except urllib.error.HTTPError as e:
                # HTTPError handling
                err_body = e.read().decode("utf-8", errors="replace")

                if e.code in (401, 403) and attempt == 0:
                    logger.warning("chat_stream: Token expired (401), clearing cache and retrying...")
                    self._auth._token = None
                    if _TOKEN_CACHE.exists():
                        _TOKEN_CACHE.unlink()
                    continue

                # 429: account-level rate-limit/capacity の可能性があるため、
                # 可能なら別アカウントへ即ローテーションして再試行。
                if e.code == 429:
                    try:
                        current_acct = getattr(self._auth, "_current_account", self._auth.account)
                        error_kind = self._derive_429_error_kind(err_body)
                        cooldown_s = self._compute_429_cooldown(error_kind, attempt)
                        account_429_counts[current_acct] = account_429_counts.get(current_acct, 0) + 1
                        # Put current account into cooldown and force RR to pick another one.
                        self._auth.vault.mark_rate_limited(
                            current_acct, cooldown=cooldown_s, error_kind=error_kind
                        )
                        excluded_accounts.add(current_acct)
                        logger.warning(
                            "chat_stream: 429 classified kind=%s account=%s count=%d cooldown=%ss "
                            "(attempt=%d/%d)",
                            error_kind,
                            current_acct,
                            account_429_counts[current_acct],
                            cooldown_s,
                            attempt + 1,
                            max_attempts,
                        )
                        alt_token, alt_acct = self._auth.vault.get_token_round_robin(
                            exclude=list(excluded_accounts)
                        )
                        if alt_acct != current_acct:
                            # Short exponential backoff to reduce immediate 429 cascades.
                            wait_s = min(1.0 * (2 ** min(attempt, 3)), 8.0)
                            logger.warning(
                                "chat_stream: 429 on account=%s, rotating to account=%s and retrying "
                                "(attempt=%d/%d, wait=%.1fs, excluded=%s)",
                                current_acct, alt_acct, attempt + 1, max_attempts, wait_s, sorted(excluded_accounts),
                            )
                            self._auth._current_account = alt_acct
                            self._auth._token = alt_token
                            self._api._invalidate_project_cache()
                            if attempt < max_attempts - 1:
                                time.sleep(wait_s)
                                continue
                        logger.warning(
                            "chat_stream: 429 on account=%s but no alternate account available "
                            "(kind=%s, cooldown=%ss, counts=%s)",
                            current_acct,
                            error_kind,
                            cooldown_s,
                            account_429_counts,
                        )
                        if attempt < max_attempts - 1:
                            wait_s = min(1.0 * (2 ** min(attempt, 3)), 8.0)
                            logger.warning(
                                "chat_stream: retrying same route after 429 "
                                "(attempt=%d/%d, wait=%.1fs)",
                                attempt + 1, max_attempts, wait_s,
                            )
                            time.sleep(wait_s)
                            continue
                    except Exception as rotate_error:  # noqa: BLE001
                        logger.debug("chat_stream: account rotation skipped: %s", rotate_error)

                # Gemini 3.1 Pro Preview 等、streamGenerateChat に非対応なモデルがある。
                # 400 BadRequest (ILLEGAL_MODEL_CONFIG) の場合は単一応答の chat() にフォールバックする
                if e.code == 400 and "ILLEGAL_MODEL_CONFIG" in err_body:
                    logger.warning(
                        "streamGenerateChat failed with 400 (ILLEGAL_MODEL_CONFIG). "
                        "Falling back to non-streaming generateChat for model %s.",
                        model
                    )
                    # Non-streaming fallback
                    res = self.chat(
                        message=message,
                        model=model,
                        system_instruction=system_instruction,
                        history=history,
                        tier_id=tier_id,
                        include_thinking=include_thinking,
                        thinking_budget=thinking_budget,
                        timeout=timeout,
                    )

                    if res.thinking:
                        yield f"__THINKING__:{res.thinking}"
                    if res.text:
                        yield res.text
                    return

                raise CortexAPIError(
                    f"Chat stream failed: {e.code} {e.reason}",
                    status_code=e.code,
                    response_body=err_body,
                )

    # PURPOSE: generateChat レスポンスを LLMResponse に変換。
    def _parse_chat_response(
        self,
        response: dict,
        request_model: str = "",
    ) -> LLMResponse:
        """Parse generateChat response into LLMResponse.

        Args:
            response: Raw API response dict
            request_model: The model_config_id used in the request (for fallback)
        """
        text = response.get("markdown", "")
        details = response.get("processingDetails", {})

        # modelConfig can be in response root or inside processingDetails
        model_config = (
            response.get("modelConfig")
            or details.get("modelConfig")
            or {}
        )

        # Priority: displayName > config id > request_model > fallback
        model_name = (
            model_config.get("displayName")
            or model_config.get("id")
            or _MODEL_DISPLAY_NAMES.get(request_model, "")
            or request_model
            or f"cortex-chat (cid={details.get('cid', '')})"
        )

        # Extract thinking summaries if present
        thinking_text = ""
        summaries = details.get("thinkingSummaries", [])
        if summaries:
            thinking_text = "\n\n".join(
                s.get("text", "") for s in summaries if "text" in s
            ).strip()

        return LLMResponse(
            text=text,
            thinking=thinking_text if thinking_text else None,
            model=model_name,
            cascade_id=details.get("cid", ""),
            trajectory_id=details.get("tid", ""),
        )


# --- ChatConversation ---


# PURPOSE: generateChat のマルチターン会話を管理する。
#   history を自動追跡し、CascadeConversation と対称的な API を提供する。
class ChatConversation:
    """マルチターン generateChat 会話 (history 自動管理)。

    同一 history 内で複数メッセージをやり取りし、
    2MB コンテキスト + 100 ターンまでの大規模会話が可能。

    Usage:
        client = CortexClient()
        conv = client.start_chat()
        r1 = conv.send("Remember: X = 42")
        r2 = conv.send("What is X?")
        print(r2.text)  # → "X is 42"
        conv.close()
    """

    def __init__(
        self,
        chat: "CortexChat",
        model: str = "",
        tier_id: str = "",
        include_thinking: bool = True,
        store: Optional[SessionStore] = None,
        account: str = "default",
        default_model: str = "",
    ):
        self._chat = chat
        self._model = model
        self._tier_id = tier_id
        self._include_thinking = include_thinking
        self._history: list[dict[str, Any]] = []
        self._turn_count = 0

        self._store = store or get_default_store()
        self._session_id = self._store.create_session(
            account=account,
            model=model or default_model,
            pipeline="chat"
        )

    def send(
        self,
        message: str,
        timeout: float = 120.0,
    ) -> LLMResponse:
        """メッセージを送信し、応答を取得する。

        Args:
            message: 送信テキスト
            timeout: 最大待機秒数

        Returns:
            LLMResponse with text and metadata
        """
        self._turn_count += 1

        # 1. Log user turn
        start_time = time.time()
        self._store.add_turn(self._session_id, "user", message, self._turn_count)

        response = self._chat.chat(
            message=message,
            model=self._model,
            history=self._history,
            tier_id=self._tier_id,
            include_thinking=self._include_thinking,
            timeout=timeout,
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # 2. Log model turn
        total_tokens = response.token_usage.get("total_tokens", 0) if response.token_usage else 0
        self._store.add_turn(
            session_id=self._session_id,
            role="model",
            content=response.text,
            turn_number=self._turn_count,
            token_count=total_tokens,
            model=response.model,
            duration_ms=duration_ms
        )

        # Update history for next turn
        self._history.append({"author": 1, "content": message})
        self._history.append({"author": 2, "content": response.text})

        return response

    @property
    def turn_count(self) -> int:
        """現在のターン数。"""
        return self._turn_count

    @property
    def history(self) -> list[dict[str, Any]]:
        """現在の会話履歴 (read-only copy)。"""
        return list(self._history)

    @property
    def session_id(self) -> str:
        """セッション ID。"""
        return self._session_id

    def close(self) -> None:
        """会話を閉じる (リソース解放)。"""
        self._store.close_session(self._session_id)
        self._history.clear()
        self._turn_count = 0
