from __future__ import annotations

import json

from mekhane.ochema.nvidia_rerank import NvidiaReranker, load_nvidia_api_key


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self._payload).encode("utf-8")


def test_load_nvidia_api_key_prefers_standard_env(monkeypatch):
    monkeypatch.setenv("NVIDIA_API_KEY", "nv-standard")
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nv-nim")

    assert load_nvidia_api_key() == "nv-standard"


def test_nvidia_reranker_posts_reranking_payload():
    captured = {}

    def _fake_opener(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(request.header_items())
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _FakeResponse(
            {
                "rankings": [
                    {"index": 1, "logit": 7.25},
                    {"index": 0, "logit": 1.0},
                ]
            }
        )

    reranker = NvidiaReranker(
        api_key="nv-key",
        endpoint="https://example.test/reranking",
        timeout=12,
        opener=_fake_opener,
    )

    scores = reranker.rank("query text", ["doc a", "doc b"], top_n=2)

    assert captured["url"] == "https://example.test/reranking"
    assert captured["timeout"] == 12
    assert captured["headers"]["Authorization"] == "Bearer nv-key"
    assert captured["payload"]["model"] == "nvidia/llama-nemotron-rerank-1b-v2"
    assert captured["payload"]["query"] == {"text": "query text"}
    assert captured["payload"]["passages"] == [{"text": "doc a"}, {"text": "doc b"}]
    assert "top_n" not in captured["payload"]
    assert [(score.index, score.logit) for score in scores] == [(1, 7.25), (0, 1.0)]
