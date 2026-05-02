# PROOF: [L2/テスト] <- mekhane/periskope/tests/test_nl_client.py Cloud NL API テスト
# PURPOSE: NLClient のユニットテスト（モック HTTP / サブプロセス）
import json
import urllib.request
from unittest.mock import patch, MagicMock

import pytest

from mekhane.ochema.nl_client import NLClient, Entity


@pytest.fixture
def clean_token_cache():
    """Clear the token cache before each test."""
    import mekhane.ochema.nl_client as nl
    nl._token_cache.clear()
    yield
    nl._token_cache.clear()


def test_nl_client_get_token_success(clean_token_cache):
    client = NLClient(gcloud_account="test@example.com")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="mock_token\n")
        
        token = client._get_token()
        
        assert token == "mock_token"
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "--account=test@example.com" in args


def test_nl_client_get_token_failure(clean_token_cache):
    client = NLClient()
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="Not logged in")
        
        token = client._get_token()
        
        assert token == ""


def test_nl_client_analyze_entities_success():
    client = NLClient(project_id="test-project-123")
    client._get_token = MagicMock(return_value="mock_token")
    
    # Mock NL API response
    mock_response = {
        "entities": [
            {"name": "Karl Friston", "type": "PERSON", "salience": 0.9, "mentions": [1, 2]},
            {"name": "London", "type": "LOCATION", "salience": 0.4, "mentions": [1]}
        ]
    }
    
    mock_urlopen = MagicMock()
    mock_urlopen.__enter__.return_value.read.return_value = json.dumps(mock_response).encode()
    
    with patch("urllib.request.urlopen", return_value=mock_urlopen) as mock_urlopen_call:
        entities = client.analyze_entities("Karl Friston is in London")
        
        # Verify entities are parsed and sorted by salience
        assert len(entities) == 2
        assert entities[0].name == "Karl Friston"
        assert entities[0].salience == 0.9
        assert entities[0].mentions == 2
        
        assert entities[1].name == "London"
        assert entities[1].salience == 0.4
        
        # Verify API request headers (including Quota Project)
        req: urllib.request.Request = mock_urlopen_call.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer mock_token"
        assert req.get_header("X-goog-user-project") == "test-project-123"


def test_nl_client_analyze_entities_api_error():
    client = NLClient()
    client._get_token = MagicMock(return_value="mock_token")
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        from urllib.error import HTTPError
        fp = MagicMock()
        fp.read.return_value = b'{"error": {"code": 403, "message": "Quota exceeded"}}'
        mock_urlopen.side_effect = HTTPError("url", 403, "Forbidden", {}, fp)
        
        entities = client.analyze_entities("test text")
        
        assert len(entities) == 0


def test_nl_client_no_token_skips_analysis():
    client = NLClient()
    client._get_token = MagicMock(return_value="")
    
    with patch("urllib.request.urlopen") as mock_urlopen:
        entities = client.analyze_entities("test text")
        
        assert len(entities) == 0
        mock_urlopen.assert_not_called()
