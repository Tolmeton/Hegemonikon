from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


DEFAULT_NVIDIA_RERANK_MODEL = "nvidia/llama-nemotron-rerank-1b-v2"
DEFAULT_NVIDIA_RERANK_ENDPOINT = (
    "https://ai.api.nvidia.com/v1/retrieval/nvidia/"
    "llama-nemotron-rerank-1b-v2/reranking"
)
DEFAULT_NVIDIA_TIMEOUT_SEC = 30.0

_KEY_ENV_NAMES = (
    "NVIDIA_API_KEY",
    "NVIDIA_NIM_API_KEY",
    "NVIDIA_API_CATALOG_KEY",
    "NGC_API_KEY",
)


class NvidiaRerankError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class NvidiaRerankScore:
    index: int
    logit: float
    raw: dict[str, Any]


def load_nvidia_api_key() -> str:
    for name in _KEY_ENV_NAMES:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


class NvidiaReranker:
    provider = "nvidia"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = DEFAULT_NVIDIA_RERANK_MODEL,
        endpoint: str = DEFAULT_NVIDIA_RERANK_ENDPOINT,
        timeout: float = DEFAULT_NVIDIA_TIMEOUT_SEC,
        truncate: str = "END",
        opener: Callable[..., Any] | None = None,
    ) -> None:
        self.api_key = (api_key or load_nvidia_api_key()).strip()
        if not self.api_key:
            raise NvidiaRerankError(
                "NVIDIA API key is required. Set NVIDIA_API_KEY or NVIDIA_NIM_API_KEY."
            )
        self.model = model
        self.endpoint = endpoint
        self.timeout = float(timeout)
        self.truncate = truncate
        self._opener = opener or urllib.request.urlopen

    def rank(
        self,
        query: str,
        passages: list[str],
        *,
        top_n: int | None = None,
    ) -> list[NvidiaRerankScore]:
        if not passages:
            return []

        payload: dict[str, Any] = {
            "model": self.model,
            "query": {"text": query},
            "passages": [{"text": passage or ""} for passage in passages],
            "truncate": self.truncate,
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )

        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise NvidiaRerankError(
                f"NVIDIA rerank request failed with HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise NvidiaRerankError(f"NVIDIA rerank request failed: {exc}") from exc

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            raise NvidiaRerankError("NVIDIA rerank returned non-JSON response") from exc

        rankings = data.get("rankings")
        if not isinstance(rankings, list):
            raise NvidiaRerankError("NVIDIA rerank response is missing rankings[]")

        scores: list[NvidiaRerankScore] = []
        for item in rankings:
            if not isinstance(item, dict):
                continue
            index = _coerce_index(item.get("index"))
            if index is None or index < 0 or index >= len(passages):
                continue
            logit = _coerce_float(item.get("logit", item.get("score")))
            if logit is None:
                continue
            scores.append(NvidiaRerankScore(index=index, logit=logit, raw=item))
        if top_n is not None:
            return scores[: max(int(top_n), 0)]
        return scores


def _coerce_index(value: Any) -> int | None:
    try:
        if isinstance(value, bool):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    try:
        if isinstance(value, bool):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
