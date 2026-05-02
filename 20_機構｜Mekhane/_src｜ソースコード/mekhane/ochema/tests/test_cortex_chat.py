#!/usr/bin/env python3
# PROOF: [L2/インフラ] <- mekhane/ochema/tests/ テスト
# PURPOSE: CortexClient chat API ユニットテスト
"""
CortexClient chat(), chat_stream(), ChatConversation unit tests.

Tests use mock _call_api to avoid external API calls.
"""


from __future__ import annotations
import json
from unittest.mock import patch, MagicMock

from mekhane.ochema.cortex_client import CortexClient, CortexAPIError
from mekhane.ochema.types import LLMResponse


# --- Fixtures ---

def _make_client():
    """Create a CortexClient with mocked auth."""
    with patch("mekhane.ochema.cortex_auth.CortexAuth"):
        client = CortexClient()
    
    # Mock network/API dependencies that are set up during init
    client._api._get_project = MagicMock(return_value="mock-project")
    return client


def _mock_chat_response(text="Hello!", cid="abc123", tid="def456", model_config=None):
    """Create a mock generateChat response dict."""
    resp = {
        "markdown": text,
        "processingDetails": {"cid": cid, "tid": tid},
    }
    if model_config:
        resp["modelConfig"] = model_config
    return resp


# --- chat() Tests ---


class TestChat:
    """CortexClient.chat() unit tests."""

    def test_chat_basic_response(self):
        """chat() returns LLMResponse with text and model."""
        client = _make_client()
        mock_resp = _mock_chat_response("56")

        with patch.object(client._api, '_call_api', return_value=mock_resp):
            result = client.chat("What is 7*8?")

        assert isinstance(result, LLMResponse)
        assert result.text == "56"
        assert "abc123" in result.cascade_id

    def test_chat_with_history(self):
        """chat() passes history to _call_api payload."""
        client = _make_client()
        mock_resp = _mock_chat_response("I remember")
        history = [
            {"author": 1, "content": "My name is Alice"},
            {"author": 2, "content": "Nice to meet you Alice"},
        ]

        with patch.object(client._api, '_call_api', return_value=mock_resp) as mock_call:
            result = client.chat("What is my name?", history=history)

        # Verify history was passed in the payload
        call_args = mock_call.call_args
        payload = call_args[0][1]  # second positional arg
        assert payload["history"] == history
        assert result.text == "I remember"

    def test_chat_with_tier_id(self):
        """chat() includes tier_id in payload when set."""
        client = _make_client()
        mock_resp = _mock_chat_response("Premium response")

        with patch.object(client._api, '_call_api', return_value=mock_resp) as mock_call:
            client.chat("hello", tier_id="g1-ultra-tier")

        payload = mock_call.call_args[0][1]
        assert payload["tier_id"] == "g1-ultra-tier"

    def test_chat_with_model_config_id(self):
        """chat(model=...) includes model_config_id in payload."""
        client = _make_client()
        mock_resp = _mock_chat_response("Claude response")

        with patch.object(client._api, '_call_api', return_value=mock_resp) as mock_call:
            client.chat("hello", model="claude-sonnet-4-5")

        payload = mock_call.call_args[0][1]
        assert payload["model_config_id"] == "claude-sonnet-4-5"

    def test_chat_without_model_no_config_id(self):
        """chat() without model omits model_config_id from payload."""
        client = _make_client()
        mock_resp = _mock_chat_response("Default response")

        with patch.object(client._api, '_call_api', return_value=mock_resp) as mock_call:
            client.chat("hello")

        payload = mock_call.call_args[0][1]
        assert "model_config_id" not in payload

    def test_chat_with_system_instruction(self):
        """chat() prepends system_instruction to history as author=0."""
        client = _make_client()
        mock_resp = _mock_chat_response("Yes sir")

        with patch.object(client._api, '_call_api', return_value=mock_resp) as mock_call:
            client.chat("hello", system_instruction="You are a cowboy")

        payload = mock_call.call_args[0][1]
        history = payload.get("history", [])
        assert len(history) == 1
        assert history[0]["author"] == 0
        assert history[0]["content"] == "You are a cowboy"

# --- _parse_chat_response Tests ---


class TestParseChatResponse:
    """_parse_chat_response unit tests."""

    def test_basic_parse(self):
        """Basic response without modelConfig uses fallback."""
        client = _make_client()
        resp = _mock_chat_response("Hello", cid="test-cid")
        result = client._parse_chat_response(resp)

        assert result.text == "Hello"
        assert "cortex-chat" in result.model
        assert "test-cid" in result.model

    def test_model_config_display_name(self):
        """modelConfig.displayName is preferred when present."""
        client = _make_client()
        resp = _mock_chat_response(
            "Hello",
            model_config={"displayName": "Gemini 3 Pro", "id": "gemini-3-pro"},
        )
        result = client._parse_chat_response(resp)
        assert result.model == "Gemini 3 Pro"

    def test_model_config_id_fallback(self):
        """modelConfig.id is used when displayName is absent."""
        client = _make_client()
        resp = _mock_chat_response(
            "Hello",
            model_config={"id": "gemini-3.1-pro-preview"},
        )
        result = client._parse_chat_response(resp)
        assert result.model == "gemini-3.1-pro-preview"

    def test_no_model_config_fallback(self):
        """Falls back to cid-based name when no modelConfig and no request_model."""
        client = _make_client()
        resp = _mock_chat_response("Hello", cid="xyz")
        result = client._parse_chat_response(resp)
        assert result.model == "cortex-chat (cid=xyz)"

    def test_request_model_display_name_mapping(self):
        """request_model resolves via _MODEL_DISPLAY_NAMES when no modelConfig."""
        client = _make_client()
        resp = _mock_chat_response("Hello", cid="abc")
        result = client._parse_chat_response(resp, request_model="claude-sonnet-4-6")
        assert result.model == "Claude Sonnet 4.6"

    def test_request_model_raw_fallback(self):
        """request_model used as-is when not in _MODEL_DISPLAY_NAMES."""
        client = _make_client()
        resp = _mock_chat_response("Hello", cid="abc")
        result = client._parse_chat_response(resp, request_model="unknown-model-x")
        assert result.model == "unknown-model-x"

    def test_model_config_takes_priority_over_request_model(self):
        """modelConfig.displayName beats request_model."""
        client = _make_client()
        resp = _mock_chat_response(
            "Hello",
            model_config={"displayName": "Server Model Name"},
        )
        result = client._parse_chat_response(resp, request_model="claude-sonnet-4-5")
        assert result.model == "Server Model Name"


# --- ChatConversation Tests ---


class TestChatConversation:
    """ChatConversation multi-turn tests."""

    def test_turn_count_increments(self):
        """Each send() increments turn count."""
        client = _make_client()
        mock_resp = _mock_chat_response("OK")

        with patch.object(client._api, '_call_api', return_value=mock_resp):
            conv = client.start_chat()
            assert conv.turn_count == 0

            conv.send("Turn 1")
            assert conv.turn_count == 1

            conv.send("Turn 2")
            assert conv.turn_count == 2

    def test_history_accumulates(self):
        """History grows with each send()."""
        client = _make_client()
        mock_resp = _mock_chat_response("Reply")

        with patch.object(client._api, '_call_api', return_value=mock_resp):
            conv = client.start_chat()
            conv.send("Hello")
            conv.send("How are you?")

        history = conv.history
        assert len(history) == 4  # 2 user + 2 model
        assert history[0] == {"author": 1, "content": "Hello"}
        assert history[1] == {"author": 2, "content": "Reply"}
        assert history[2] == {"author": 1, "content": "How are you?"}
        assert history[3] == {"author": 2, "content": "Reply"}

    def test_close_clears_state(self):
        """close() resets turn count and history."""
        client = _make_client()
        mock_resp = _mock_chat_response("Reply")

        with patch.object(client._api, '_call_api', return_value=mock_resp):
            conv = client.start_chat()
            conv.send("Hello")

        conv.close()
        assert conv.turn_count == 0
        assert conv.history == []

    def test_history_is_readonly_copy(self):
        """history property returns a copy, not internal reference."""
        client = _make_client()
        mock_resp = _mock_chat_response("Reply")

        with patch.object(client._api, '_call_api', return_value=mock_resp):
            conv = client.start_chat()
            conv.send("Hello")

        h1 = conv.history
        h2 = conv.history
        assert h1 is not h2  # different list objects
        assert h1 == h2  # same content


# --- chat_stream() Tests ---


class TestChatStream:
    """CortexClient.chat_stream() unit tests."""

    def test_json_array_parsing(self):
        """chat_stream() correctly parses JSON array response."""
        client = _make_client()
        json_array = json.dumps([
            {"markdown": "chunk1"},
            {"markdown": "chunk2"},
            {"markdown": "chunk3"},
        ])

        mock_resp = MagicMock()
        mock_resp.read.return_value = json_array.encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_resp):
            chunks = list(client.chat_stream("hello"))

        assert chunks == ["chunk1", "chunk2", "chunk3"]

    def test_single_object_parsing(self):
        """chat_stream() handles single JSON object (non-array)."""
        client = _make_client()
        json_obj = json.dumps({"markdown": "single response"})

        mock_resp = MagicMock()
        mock_resp.read.return_value = json_obj.encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_resp):
            chunks = list(client.chat_stream("hello"))

        assert chunks == ["single response"]

    def test_empty_markdown_skipped(self):
        """chat_stream() skips items with empty markdown."""
        client = _make_client()
        json_array = json.dumps([
            {"markdown": "content"},
            {"markdown": ""},
            {"markdown": "more content"},
        ])

        mock_resp = MagicMock()
        mock_resp.read.return_value = json_array.encode("utf-8")
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)

        with patch('urllib.request.urlopen', return_value=mock_resp):
            chunks = list(client.chat_stream("hello"))

        assert chunks == ["content", "more content"]

    def test_derive_429_error_kind_capacity(self):
        """RESOURCE_EXHAUSTED should map to capacity kind."""
        client = _make_client()
        kind = client._chat._derive_429_error_kind(
            '{"error":{"status":"RESOURCE_EXHAUSTED"}}'
        )
        assert kind == "capacity"

    def test_derive_429_error_kind_rate_limit_default(self):
        """Non-capacity 429 body should default to rate_limit."""
        client = _make_client()
        kind = client._chat._derive_429_error_kind(
            '{"error":{"status":"RATE_LIMIT_EXCEEDED"}}'
        )
        assert kind == "rate_limit"

    def test_compute_429_cooldown_rate_limit_escalates(self):
        """rate_limit cooldown should escalate 60 -> 180 -> 300."""
        client = _make_client()
        assert client._chat._compute_429_cooldown("rate_limit", 0) == 60
        assert client._chat._compute_429_cooldown("rate_limit", 1) == 180
        assert client._chat._compute_429_cooldown("rate_limit", 3) == 300

    def test_compute_429_cooldown_capacity_escalates(self):
        """capacity cooldown should start higher and cap at 300."""
        client = _make_client()
        assert client._chat._compute_429_cooldown("capacity", 0) == 180
        assert client._chat._compute_429_cooldown("capacity", 1) == 300


# --- ask() Fallback Tests ---

class TestAskFallback:
    """ask() fallback to chat() logic tests."""

    def test_ask_404_caches_and_falls_back(self):
        """ask() caches model as chat-only on 404 and uses generateChat."""
        client = _make_client()
        # Reset cache for testing
        client._chat_only_cache = set()
        
        mock_chat_resp = _mock_chat_response("Fallback successful", cid="fallback123")
        
        def mock_call_api(url, payload, **kwargs):
            if "generateContent" in url:
                raise CortexAPIError("Not found", status_code=404, response_body="{}")
            elif "generateChat" in url:
                return mock_chat_resp
            raise ValueError(f"Unexpected URL: {url}")
            
        with patch.object(client._api, '_call_api', side_effect=mock_call_api) as mock_call:
             
            resp = client.ask("Hello", model="test-404-model", system_instruction="system prompt")
            
        assert resp.text == "Fallback successful"
        assert "test-404-model" in client._chat_only_cache
        
        # Verify generateChat payload has system_instruction in history
        chat_call = [call for call in mock_call.call_args_list if "generateChat" in call[0][0]][0]
        chat_payload = chat_call[0][1]
        assert len(chat_payload["history"]) > 0
        assert chat_payload["history"][0]["author"] == 0
        assert chat_payload["history"][0]["content"] == "system prompt"

