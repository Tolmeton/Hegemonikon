#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/ DX-010→Vertex AI Claude 直叩きクライアント
# PURPOSE: Vertex AI rawPredict で Claude Opus 4.6 を呼ぶ。LS の 45K 制限を回避し 1M コンテキスト。
#   HGK APP の「秘書 = COO = Control Plane」の脳として使う。
"""
vertex_claude — Vertex AI rawPredict Claude Client (Multi-Account)

HGK OS の統一 LLM 秘書。LS の 45K/30K checkpoint 制限を回避し、
Claude Opus 4.6 の 1M コンテキストをフルに使う。

Features:
    - 6 GCP アカウントのラウンドロビン + 429 自動切替
    - 4 リージョンフェイルオーバー (us-east5, europe-west1, europe-west4, asia-southeast1)
    - 月間コスト管理 ($600 GCP クレジット上限)
    - Vertex AI → Anthropic API → LS の 3 段フォールバック

Usage:
    from mekhane.ochema.vertex_claude import VertexClaudeClient

    client = VertexClaudeClient()
    resp = client.ask("HGK の現在の状態を教えて")
    print(resp.text)

    # ストリーミング
    for chunk in client.ask_stream("長い分析をして"):
        print(chunk, end="", flush=True)

Prerequisites:
    1. gcloud auth application-default login
    2. Vertex AI Model Garden で Claude Opus 4.6 を有効化 (6垢分)
    3. .env に VERTEX_CLAUDE_ACCOUNTS を設定 (または defaults 使用)
    4. Quota 引き上げ申請済み (初期 quota = 0)
"""


from __future__ import annotations
from typing import Any, Generator, Optional
import itertools
import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

# Claude Opus 4.6 Vertex AI Pricing (2026-03)
OPUS_INPUT_PRICE_PER_MTOK = 15.0   # $15 / 1M input tokens
OPUS_OUTPUT_PRICE_PER_MTOK = 75.0  # $75 / 1M output tokens

# Model
DEFAULT_MODEL = "claude-opus-4-6"

# Budget
DEFAULT_MONTHLY_BUDGET_USD = 600.0

# Regions where Claude Opus 4.6 is available (verified 2026-03-05)
AVAILABLE_REGIONS = ["us-east5", "europe-west1", "europe-west4", "asia-southeast1"]

# Cost tracking file
COST_TRACKER_PATH = Path.home() / ".cache" / "ochema" / "vertex_claude_costs.json"


# =============================================================================
# Account Config
# =============================================================================


@dataclass
class VertexAccount:
    """1 GCP アカウントの設定。"""

    name: str
    project: str
    # gcloud config name (for token retrieval)
    gcloud_config: str = ""
    # Cached access token
    _token: str = ""
    _token_expiry: float = 0.0
    # Rate limit state
    _rate_limited_until: float = 0.0
    _error_kind: str = "rate_limit"
    _last_probe: float = 0.0

    # T-08 Cooldown/Probe Strategy Constants
    MIN_PROBE_INTERVAL = 30.0
    PROBE_MARGIN = 120.0

    @property
    def is_rate_limited(self) -> bool:
        now = time.time()
        if now >= self._rate_limited_until:
            return False
            
        # T-08 Probe Strategy
        if self._error_kind in ("auth", "billing", "capacity"):
            return True  # Persistent errors never probe
            
        if now - self._last_probe >= self.MIN_PROBE_INTERVAL and now >= self._rate_limited_until - self.PROBE_MARGIN:
            self._last_probe = now
            logger.debug("T-08 Cooldown/Probe: attempting probe for '%s'", self.name)
            return False

        return True

    def mark_rate_limited(self, cooldown_sec: int = 60, error_kind: str = "rate_limit") -> None:
        self._rate_limited_until = time.time() + cooldown_sec
        self._error_kind = error_kind
        logger.warning(
            "Account %s rate limited for %ds (%s)", 
            self.name, cooldown_sec, error_kind
        )

    def get_access_token(self) -> str:
        """GCP アクセストークンを取得 (キャッシュ付き)。"""
        now = time.time()
        if self._token and now < self._token_expiry - 60:
            return self._token

        try:
            cmd = ["gcloud", "auth", "print-access-token"]
            if self.gcloud_config:
                cmd.extend(["--configuration", self.gcloud_config])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self._token = result.stdout.strip()
                self._token_expiry = now + 3600
                return self._token
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning("gcloud auth failed for %s: %s", self.name, e)
        return ""


# Default accounts — Creator の 6 垢設定
# 機密情報（project ID等）はハードコードせず、.env の VERTEX_ACCOUNT_{NAME}_PROJECT で設定する
DEFAULT_ACCOUNTS = [
    VertexAccount(name="makaron", project="", gcloud_config="default"),
    VertexAccount(name="movement", project="", gcloud_config="movement"),
    VertexAccount(name="Tolmeton", project="", gcloud_config="Tolmeton"),
    VertexAccount(name="rairaixoxoxo", project="", gcloud_config="rairaixoxoxo"),
    VertexAccount(name="hraiki", project="", gcloud_config="hraiki"),
    VertexAccount(name="nous", project="", gcloud_config="nous"),
]


def _load_accounts_from_env() -> list[VertexAccount]:
    """環境変数から 6 垢の project ID を読み込む。"""
    accounts = []
    for acct in DEFAULT_ACCOUNTS:
        project = os.environ.get(
            f"VERTEX_ACCOUNT_{acct.name.upper()}_PROJECT",
            acct.project,
        )
        gcloud_cfg = os.environ.get(
            f"VERTEX_ACCOUNT_{acct.name.upper()}_GCLOUD_CONFIG",
            acct.gcloud_config,
        )
        if project:  # project が空のアカウントはスキップ
            accounts.append(VertexAccount(
                name=acct.name,
                project=project,
                gcloud_config=gcloud_cfg,
            ))
    return accounts


# =============================================================================
# Response Type
# =============================================================================


@dataclass
class ClaudeResponse:
    """Claude API の統一レスポンス型。"""

    text: str
    model: str = ""
    provider: str = ""      # "vertex" | "anthropic" | "ls"
    account: str = ""       # 使用アカウント名
    region: str = ""        # 使用リージョン
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def estimated_cost_usd(self) -> float:
        """推定コスト (USD)。Claude Opus 4.6 pricing。"""
        return (
            self.input_tokens * OPUS_INPUT_PRICE_PER_MTOK
            + self.output_tokens * OPUS_OUTPUT_PRICE_PER_MTOK
        ) / 1_000_000


# =============================================================================
# Cost Tracker
# =============================================================================


class CostTracker:
    """月間コスト追跡。$600 GCP クレジット上限を管理。"""

    def __init__(self, budget_usd: float = DEFAULT_MONTHLY_BUDGET_USD) -> None:
        self.budget_usd = budget_usd
        self._data: dict = {}
        self._load()

    def _month_key(self) -> str:
        return time.strftime("%Y-%m")

    def _load(self) -> None:
        try:
            if COST_TRACKER_PATH.exists():
                self._data = json.loads(COST_TRACKER_PATH.read_text())
        except (OSError, json.JSONDecodeError) as _e:
            logger.debug("Ignored exception: %s", _e)
            self._data = {}

    def _save(self) -> None:
        try:
            COST_TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
            COST_TRACKER_PATH.write_text(json.dumps(self._data, indent=2))
        except OSError as e:
            logger.warning("Cost tracker save failed: %s", e)

    def record(self, resp: ClaudeResponse) -> None:
        """レスポンスのコストを記録。"""
        month = self._month_key()
        if month not in self._data:
            self._data[month] = {
                "total_cost_usd": 0.0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "request_count": 0,
                "by_account": {},
            }
        entry = self._data[month]
        cost = resp.estimated_cost_usd
        entry["total_cost_usd"] += cost
        entry["total_input_tokens"] += resp.input_tokens
        entry["total_output_tokens"] += resp.output_tokens
        entry["request_count"] += 1

        # Per-account tracking
        acct = resp.account or "unknown"
        if acct not in entry["by_account"]:
            entry["by_account"][acct] = {"cost_usd": 0.0, "requests": 0}
        entry["by_account"][acct]["cost_usd"] += cost
        entry["by_account"][acct]["requests"] += 1

        self._save()

    @property
    def month_cost(self) -> float:
        month = self._month_key()
        return self._data.get(month, {}).get("total_cost_usd", 0.0)

    @property
    def budget_remaining(self) -> float:
        return max(0.0, self.budget_usd - self.month_cost)

    @property
    def budget_exhausted(self) -> bool:
        return self.month_cost >= self.budget_usd

    def status(self) -> dict:
        """コスト状況サマリー。"""
        month = self._month_key()
        entry = self._data.get(month, {})
        return {
            "month": month,
            "budget_usd": self.budget_usd,
            "spent_usd": round(entry.get("total_cost_usd", 0.0), 4),
            "remaining_usd": round(self.budget_remaining, 4),
            "request_count": entry.get("request_count", 0),
            "input_tokens": entry.get("total_input_tokens", 0),
            "output_tokens": entry.get("total_output_tokens", 0),
            "by_account": entry.get("by_account", {}),
        }


# =============================================================================
# Client
# =============================================================================


class VertexClaudeClient:
    """Vertex AI / Anthropic API の統一 Claude クライアント (Multi-Account)。

    プロバイダー優先順位:
    1. Vertex AI rawPredict (GCP クレジット、6 垢ラウンドロビン、1M context)
    2. Anthropic API 直叩き (API キー、1M context)
    3. LS 経由 (フォールバック、45K 制限)

    429 (Quota Exhausted) 時の挙動:
    1. 同アカウントの別リージョンを試す
    2. 別アカウントに切り替える
    3. 全滅なら Anthropic → LS にフォールバック
    """

    def __init__(
        self,
        accounts: list[VertexAccount] | None = None,
        model: str = "",
        anthropic_api_key: str = "",
        budget_usd: float = DEFAULT_MONTHLY_BUDGET_USD,
    ) -> None:
        self.accounts = accounts or _load_accounts_from_env()
        self.model = model or os.environ.get("VERTEX_CLAUDE_MODEL", DEFAULT_MODEL)
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.anthropic_version = "vertex-2023-10-16"
        self.max_tokens_default = int(os.environ.get("VERTEX_CLAUDE_MAX_TOKENS", "8192"))
        self.temperature_default = 0.7

        # Round-robin iterator for accounts
        self._account_cycle = itertools.cycle(self.accounts) if self.accounts else None

        # Cost tracking
        self.costs = CostTracker(budget_usd)

    def _get_next_account(self) -> VertexAccount | None:
        """次に使うアカウントを取得 (rate limited をスキップ)。"""
        if not self._account_cycle:
            return None
        for _ in range(len(self.accounts)):
            acct = next(self._account_cycle)
            if not acct.is_rate_limited:
                return acct
        return None  # 全アカウント rate limited

    def _build_endpoint(self, project: str, region: str) -> str:
        return (
            f"https://{region}-aiplatform.googleapis.com/v1/"
            f"projects/{project}/locations/{region}/"
            f"publishers/anthropic/models/{self.model}:rawPredict"
        )

    def _build_stream_endpoint(self, project: str, region: str) -> str:
        return (
            f"https://{region}-aiplatform.googleapis.com/v1/"
            f"projects/{project}/locations/{region}/"
            f"publishers/anthropic/models/{self.model}:streamRawPredict"
        )

    def _build_messages_payload(
        self,
        message: str,
        *,
        system: str = "",
        history: list[dict] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> dict:
        """Anthropic Messages API 形式のペイロードを構築する。"""
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": message})

        payload: dict = {
            "anthropic_version": self.anthropic_version,
            "max_tokens": max_tokens or self.max_tokens_default,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        payload["temperature"] = temperature if temperature is not None else self.temperature_default
        return payload

    # --- Public API ---

    def ask(
        self,
        message: str,
        *,
        system: str = "",
        history: list[dict] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float = 120.0,
        response_model: Optional[Any] = None,
    ) -> ClaudeResponse:
        """Claude に質問する (同期)。"""
        import json
        
        if response_model is not None:
            try:
                schema = response_model.model_json_schema()
            except AttributeError:
                schema = response_model.schema()
            
            injection = (
                f"\n\nIMPORTANT: Respond EXACTLY with a valid JSON object matching the following schema. "
                f"Do not include markdown formatting or any other text before or after the JSON.\n\n"
                f"{json.dumps(schema, indent=2)}\n"
            )
            system = system + injection

            # Force `{` pre-fill for Claude to ensure JSON response
            if history is None:
                history = []
            else:
                history = list(history)
            
        # Budget check
        if self.costs.budget_exhausted:
            logger.warning("Monthly budget exhausted ($%.2f/%$.2f)", self.costs.month_cost, self.costs.budget_usd)
            raise RuntimeError("Vertex budget exhausted")

        payload = self._build_messages_payload(
            message, system=system, history=history,
            max_tokens=max_tokens, temperature=temperature,
        )

        # Try Vertex AI with multi-account + multi-region
        resp = self._ask_vertex_with_failover(payload, timeout=timeout)
        if resp:
            self.costs.record(resp)
            return resp

        # Anthropic API fallback
        if self.anthropic_api_key:
            logger.info("All Vertex accounts exhausted, falling back to Anthropic API")
            resp = self._ask_anthropic(payload)
            self.costs.record(resp)
            return resp

        # No fallbacks left
        raise RuntimeError("All Vertex accounts exhausted and no Anthropic API key")

    def ask_stream(
        self,
        message: str,
        *,
        system: str = "",
        history: list[dict] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Generator[str, None, ClaudeResponse]:
        """Claude に質問する (ストリーミング)。"""
        if self.costs.budget_exhausted:
            resp = self._ask_ls(message, system=system)
            def _gen():
                yield resp.text
                return resp
            return _gen()

        payload = self._build_messages_payload(
            message, system=system, history=history,
            max_tokens=max_tokens, temperature=temperature,
        )
        payload["stream"] = True

        # Streaming は primary account + primary region で試行
        acct = self._get_next_account()
        if acct:
            token = acct.get_access_token()
            if token:
                region = AVAILABLE_REGIONS[0]
                return self._stream_vertex(payload, token, acct.project, region, acct.name)

        # Anthropic streaming
        if self.anthropic_api_key:
            return self._stream_anthropic(payload)

        # LS fallback
        resp = self._ask_ls(message, system=system)
        def _gen():
            yield resp.text
            return resp
        return _gen()

    # --- Async API (Colony Integration) ---

    async def ask_async(
        self,
        message: str,
        *,
        system: str = "",
        history: list[dict] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float = 120.0,
    ) -> ClaudeResponse:
        """Claude に質問する (非同期)。Colony から直接 await で呼べる。"""
        import asyncio
        return await asyncio.to_thread(
            self.ask,
            message,
            system=system,
            history=history,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )

    # --- Vertex AI with Multi-Account + Multi-Region Failover ---

    def _ask_vertex_with_failover(self, payload: dict, *, timeout: float = 120.0) -> ClaudeResponse | None:
        """全アカウント × 全リージョンで試行。429 で次へ。"""
        import urllib.request
        import urllib.error

        tried = 0
        for _ in range(len(self.accounts)):
            acct = self._get_next_account()
            if not acct:
                break

            token = acct.get_access_token()
            if not token:
                continue

            for region in AVAILABLE_REGIONS:
                tried += 1
                endpoint = self._build_endpoint(acct.project, region)

                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode(),
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                )

                try:
                    with urllib.request.urlopen(req, timeout=timeout) as resp:
                        data = json.loads(resp.read())

                    logger.info(
                        "Vertex AI success: account=%s region=%s",
                        acct.name, region,
                    )
                    return ClaudeResponse(
                        text=data.get("content", [{}])[0].get("text", ""),
                        model=data.get("model", self.model),
                        provider="vertex",
                        account=acct.name,
                        region=region,
                        input_tokens=data.get("usage", {}).get("input_tokens", 0),
                        output_tokens=data.get("usage", {}).get("output_tokens", 0),
                        stop_reason=data.get("stop_reason", ""),
                        raw=data,
                    )

                except urllib.error.HTTPError as e:
                    body = e.read().decode()
                    if e.code == 429:
                        error_kind = "capacity" if "quota" in body.lower() else "rate_limit"
                        logger.warning(
                            "429 (%s): account=%s region=%s",
                            error_kind, acct.name, region,
                        )
                        continue  # 次のリージョンへ
                    elif e.code == 404:
                        logger.debug("404: account=%s region=%s", acct.name, region)
                        continue  # 次のリージョンへ
                    elif e.code in (401, 403):
                        error_kind = "billing" if "billing" in body.lower() else "auth"
                        logger.warning("%d (%s) from %s: skipping account.", e.code, error_kind, acct.name)
                        acct.mark_rate_limited(cooldown_sec=300, error_kind=error_kind)
                        break
                    else:
                        logger.error(
                            "Vertex AI error %d: account=%s region=%s: %s",
                            e.code, acct.name, region, body[:200],
                        )
                        continue

                except (OSError, json.JSONDecodeError, Exception) as e:  # noqa: BLE001
                    logger.error("Vertex AI request failed: %s", e)
                    continue

            # このアカウントの全リージョンが失敗 → rate limit 扱い
            if getattr(acct, "_error_kind", "rate_limit") not in ("auth", "billing", "capacity"):
                acct.mark_rate_limited(cooldown_sec=60, error_kind="rate_limit")

        logger.warning("All Vertex accounts/regions exhausted (tried %d)", tried)
        return None

    # --- Vertex AI Streaming ---

    def _stream_vertex(
        self, payload: dict, token: str, project: str, region: str, account_name: str,
    ) -> Generator[str, None, ClaudeResponse]:
        """Vertex AI streamRawPredict。"""
        import urllib.request
        import urllib.error

        endpoint = self._build_stream_endpoint(project, region)
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        full_text = ""
        input_tokens = 0
        output_tokens = 0
        model = self.model

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                for line_bytes in resp:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        event = json.loads(data_str)
                        event_type = event.get("type", "")
                        if event_type == "content_block_delta":
                            text = event.get("delta", {}).get("text", "")
                            if text:
                                full_text += text
                                yield text
                        elif event_type == "message_start":
                            msg = event.get("message", {})
                            model = msg.get("model", model)
                            input_tokens = msg.get("usage", {}).get("input_tokens", 0)
                        elif event_type == "message_delta":
                            output_tokens = event.get("usage", {}).get("output_tokens", 0)
                    except json.JSONDecodeError:
                        continue
        except urllib.error.HTTPError as e:
            logger.error("Vertex AI stream error %d", e.code)
            raise

        result = ClaudeResponse(
            text=full_text, model=model, provider="vertex",
            account=account_name, region=region,
            input_tokens=input_tokens, output_tokens=output_tokens, raw={},
        )
        self.costs.record(result)
        return result

    # --- Anthropic API Provider ---

    def _ask_anthropic(self, payload: dict) -> ClaudeResponse:
        """Anthropic API 直叩き。"""
        import urllib.request
        import urllib.error

        api_payload = {k: v for k, v in payload.items() if k != "anthropic_version"}
        api_payload["model"] = self.model.replace("-", "-", 2)  # Keep model name as-is

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(api_payload).encode(),
            headers={
                "x-api-key": self.anthropic_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"Anthropic API error {e.code}: {body}") from e

        return ClaudeResponse(
            text=data.get("content", [{}])[0].get("text", ""),
            model=data.get("model", ""),
            provider="anthropic",
            input_tokens=data.get("usage", {}).get("input_tokens", 0),
            output_tokens=data.get("usage", {}).get("output_tokens", 0),
            stop_reason=data.get("stop_reason", ""),
            raw=data,
        )

    def _stream_anthropic(self, payload: dict) -> Generator[str, None, ClaudeResponse]:
        """Anthropic API ストリーミング。"""
        import urllib.request

        api_payload = {k: v for k, v in payload.items() if k != "anthropic_version"}
        api_payload["model"] = self.model

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(api_payload).encode(),
            headers={
                "x-api-key": self.anthropic_api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
        )

        full_text = ""
        input_tokens = 0
        output_tokens = 0
        model = ""

        with urllib.request.urlopen(req, timeout=300) as resp:
            for line_bytes in resp:
                line = line_bytes.decode("utf-8").strip()
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    event = json.loads(data_str)
                    event_type = event.get("type", "")
                    if event_type == "content_block_delta":
                        text = event.get("delta", {}).get("text", "")
                        if text:
                            full_text += text
                            yield text
                    elif event_type == "message_start":
                        msg = event.get("message", {})
                        model = msg.get("model", "")
                        input_tokens = msg.get("usage", {}).get("input_tokens", 0)
                    elif event_type == "message_delta":
                        output_tokens = event.get("usage", {}).get("output_tokens", 0)
                except json.JSONDecodeError:
                    continue

        result = ClaudeResponse(
            text=full_text, model=model, provider="anthropic",
            input_tokens=input_tokens, output_tokens=output_tokens, raw={},
        )
        self.costs.record(result)
        return result

    # --- LS Fallback ---

    def _ask_ls(self, message: str, *, system: str = "") -> ClaudeResponse:
        """LS 経由で Claude を呼ぶ (フォールバック, 45K 制限)。"""
        try:
            from mekhane.ochema.service import OchemaService
            svc = OchemaService.get()
            resp = svc.ask(message, model="claude-sonnet", system_instruction=system)
            return ClaudeResponse(
                text=resp.text if hasattr(resp, "text") else str(resp),
                model="claude-sonnet",
                provider="ls",
                raw={},
            )
        except (OSError, Exception) as e:  # Intentional Catch-All (Fallback)  # noqa: BLE001
            logger.error("LS fallback failed: %s", e)
            return ClaudeResponse(text=f"Error: {e}", provider="ls_error")


# =============================================================================
# CLI
# =============================================================================


if __name__ == "__main__":
    import argparse
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Vertex AI Claude Client — HGK 秘書")
    parser.add_argument("message", nargs="?", default="こんにちは。HGK の秘書として自己紹介してください。")
    parser.add_argument("--model", default=None, help="モデル名")
    parser.add_argument("--system", default="あなたは HGK (Hegemonikón) の認知補佐官です。日本語で応答してください。")
    parser.add_argument("--stream", action="store_true", help="ストリーミングモード")
    parser.add_argument("--max-tokens", type=int, default=1024)
    parser.add_argument("--info", action="store_true", help="設定情報を表示")
    parser.add_argument("--costs", action="store_true", help="コスト状況を表示")
    args = parser.parse_args()

    client = VertexClaudeClient(model=args.model or "")

    if args.costs:
        status = client.costs.status()
        print(f"Month:      {status['month']}")
        print(f"Budget:     ${status['budget_usd']:.2f}")
        print(f"Spent:      ${status['spent_usd']:.4f}")
        print(f"Remaining:  ${status['remaining_usd']:.4f}")
        print(f"Requests:   {status['request_count']}")
        print(f"Tokens:     {status['input_tokens']} in / {status['output_tokens']} out")
        if status["by_account"]:
            print("\nBy account:")
            for name, info in status["by_account"].items():
                print(f"  {name}: ${info['cost_usd']:.4f} ({info['requests']} req)")
        sys.exit(0)

    if args.info:
        print(f"Model:    {client.model}")
        print(f"Accounts: {len(client.accounts)}")
        for acct in client.accounts:
            token = acct.get_access_token()
            print(f"  {acct.name:20s} project={acct.project:35s} token={'✅' if token else '❌'}")
        print(f"Regions:  {', '.join(AVAILABLE_REGIONS)}")
        print(f"Anthropic key: {'set' if client.anthropic_api_key else 'not set'}")
        print(f"Budget:   ${client.costs.budget_usd:.0f}/month (spent: ${client.costs.month_cost:.4f})")
        sys.exit(0)

    if args.stream:
        gen = client.ask_stream(args.message, system=args.system, max_tokens=args.max_tokens)
        for chunk in gen:
            print(chunk, end="", flush=True)
        print()
    else:
        resp = client.ask(args.message, system=args.system, max_tokens=args.max_tokens)
        print(f"[Provider: {resp.provider} | Account: {resp.account} | Region: {resp.region}]")
        print(f"[Model: {resp.model}]")
        print(f"[Tokens: {resp.input_tokens} in + {resp.output_tokens} out = {resp.total_tokens}]")
        print(f"[Cost: ${resp.estimated_cost_usd:.4f}]")
        print()
        print(resp.text)
