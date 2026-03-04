"""
Unit tests for OllamaClient service.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import requests

from app.services.ollama_client import OllamaClient, OllamaError, get_ollama_client


@pytest.mark.unit
@pytest.mark.service
class TestOllamaClientInit:
    """Test OllamaClient initialization."""

    def test_init_defaults(self):
        """Test default initialization values."""
        client = OllamaClient()
        assert client.base_url == "http://localhost:11434"
        assert client.model == "mistral:7b"
        assert client.temperature == 0.1
        assert client.timeout == 30

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        client = OllamaClient(
            base_url="http://custom:8080",
            model="llama2:13b",
            temperature=0.5,
            timeout=60
        )
        assert client.base_url == "http://custom:8080"
        assert client.model == "llama2:13b"
        assert client.temperature == 0.5
        assert client.timeout == 60

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from base_url."""
        client = OllamaClient(base_url="http://localhost:11434/")
        assert client.base_url == "http://localhost:11434"

    def test_init_empty_cache(self):
        """Test that cache starts empty."""
        client = OllamaClient()
        assert client._cache == {}


@pytest.mark.unit
@pytest.mark.service
class TestOllamaClientAvailability:
    """Test OllamaClient availability checks."""

    @patch("app.services.ollama_client.requests.get")
    def test_is_available_server_up(self, mock_get):
        """Test is_available returns True when server responds 200."""
        mock_get.return_value = Mock(status_code=200)
        client = OllamaClient()
        assert client.is_available() is True
        mock_get.assert_called_once_with("http://localhost:11434/api/tags", timeout=5)

    @patch("app.services.ollama_client.requests.get")
    def test_is_available_server_down(self, mock_get):
        """Test is_available returns False when server is unreachable."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        client = OllamaClient()
        assert client.is_available() is False

    @patch("app.services.ollama_client.requests.get")
    def test_is_available_timeout(self, mock_get):
        """Test is_available returns False on timeout."""
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        client = OllamaClient()
        assert client.is_available() is False

    @patch("app.services.ollama_client.requests.get")
    def test_is_available_non_200_status(self, mock_get):
        """Test is_available returns False on non-200 status."""
        mock_get.return_value = Mock(status_code=500)
        client = OllamaClient()
        assert client.is_available() is False


@pytest.mark.unit
@pytest.mark.service
class TestOllamaClientListModels:
    """Test OllamaClient model listing."""

    @patch("app.services.ollama_client.requests.get")
    def test_list_models_success(self, mock_get):
        """Test successful model listing."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"models": [{"name": "mistral:7b"}, {"name": "llama2:7b"}]}
        )
        mock_get.return_value.raise_for_status = Mock()
        client = OllamaClient()
        models = client.list_models()
        assert models == ["mistral:7b", "llama2:7b"]

    @patch("app.services.ollama_client.requests.get")
    def test_list_models_failure(self, mock_get):
        """Test model listing returns empty list on failure."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        client = OllamaClient()
        models = client.list_models()
        assert models == []

    @patch("app.services.ollama_client.requests.get")
    def test_list_models_empty(self, mock_get):
        """Test model listing when no models are available."""
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"models": []}
        )
        mock_get.return_value.raise_for_status = Mock()
        client = OllamaClient()
        models = client.list_models()
        assert models == []


@pytest.mark.unit
@pytest.mark.service
class TestOllamaClientGenerate:
    """Test OllamaClient generation."""

    @patch("app.services.ollama_client.requests.post")
    def test_generate_success_json(self, mock_post):
        """Test successful JSON generation."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "response": '{"is_sensitive": true, "confidence": 85}',
                "model": "mistral:7b",
                "prompt_eval_count": 100,
                "eval_count": 50,
                "total_duration": 1_000_000_000,
                "load_duration": 100_000_000,
                "prompt_eval_duration": 400_000_000,
                "eval_duration": 500_000_000
            }
        )
        mock_post.return_value.raise_for_status = Mock()
        client = OllamaClient()
        result = client.generate("Test prompt", format="json", use_cache=False)

        assert result["response"] == {"is_sensitive": True, "confidence": 85}
        assert result["model"] == "mistral:7b"
        assert result["tokens"]["total"] == 150
        assert result["timing"]["total_duration"] == 1.0

    @patch("app.services.ollama_client.requests.post")
    def test_generate_success_text(self, mock_post):
        """Test successful text generation."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "response": "This is a text response",
                "model": "mistral:7b",
                "prompt_eval_count": 50,
                "eval_count": 30,
                "total_duration": 500_000_000,
                "load_duration": 0,
                "prompt_eval_duration": 200_000_000,
                "eval_duration": 300_000_000
            }
        )
        mock_post.return_value.raise_for_status = Mock()
        client = OllamaClient()
        result = client.generate("Test prompt", format="text", use_cache=False)

        assert result["response"] == "This is a text response"
        assert result["raw_text"] == "This is a text response"

    @patch("app.services.ollama_client.requests.post")
    def test_generate_invalid_json_response(self, mock_post):
        """Test handling of invalid JSON in response."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "response": "not valid json {[",
                "model": "mistral:7b",
                "prompt_eval_count": 10,
                "eval_count": 5,
                "total_duration": 100_000_000,
                "load_duration": 0,
                "prompt_eval_duration": 50_000_000,
                "eval_duration": 50_000_000
            }
        )
        mock_post.return_value.raise_for_status = Mock()
        client = OllamaClient()
        result = client.generate("Test prompt", format="json", use_cache=False)

        assert "error" in result["response"]
        assert result["response"]["error"] == "Failed to parse JSON"

    @patch("app.services.ollama_client.requests.post")
    def test_generate_uses_cache(self, mock_post):
        """Test that cached responses are returned on second call."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "response": '{"result": "cached"}',
                "model": "mistral:7b",
                "prompt_eval_count": 10,
                "eval_count": 5,
                "total_duration": 100_000_000,
                "load_duration": 0,
                "prompt_eval_duration": 50_000_000,
                "eval_duration": 50_000_000
            }
        )
        mock_post.return_value.raise_for_status = Mock()
        client = OllamaClient()

        # First call hits the server
        result1 = client.generate("Test prompt", use_cache=True)
        assert mock_post.call_count == 1

        # Second call should use cache
        result2 = client.generate("Test prompt", use_cache=True)
        assert mock_post.call_count == 1  # Not called again
        assert result1 == result2

    @patch("app.services.ollama_client.requests.post")
    def test_generate_cache_disabled(self, mock_post):
        """Test that cache is bypassed when use_cache=False."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "response": '{"result": "fresh"}',
                "model": "mistral:7b",
                "prompt_eval_count": 10,
                "eval_count": 5,
                "total_duration": 100_000_000,
                "load_duration": 0,
                "prompt_eval_duration": 50_000_000,
                "eval_duration": 50_000_000
            }
        )
        mock_post.return_value.raise_for_status = Mock()
        client = OllamaClient()

        client.generate("Test prompt", use_cache=False)
        client.generate("Test prompt", use_cache=False)
        assert mock_post.call_count == 2

    @patch("app.services.ollama_client.requests.post")
    def test_generate_timeout_error(self, mock_post):
        """Test OllamaError on timeout."""
        mock_post.side_effect = requests.exceptions.Timeout("Timed out")
        client = OllamaClient(timeout=5)

        with pytest.raises(OllamaError, match="timed out"):
            client.generate("Test prompt", use_cache=False)

    @patch("app.services.ollama_client.requests.post")
    def test_generate_network_error(self, mock_post):
        """Test OllamaError on network failure."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        client = OllamaClient()

        with pytest.raises(OllamaError, match="Request failed"):
            client.generate("Test prompt", use_cache=False)

    @patch("app.services.ollama_client.requests.post")
    def test_generate_with_system_prompt(self, mock_post):
        """Test that system prompt is included in payload."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "response": '{"result": "ok"}',
                "model": "mistral:7b",
                "prompt_eval_count": 10,
                "eval_count": 5,
                "total_duration": 100_000_000,
                "load_duration": 0,
                "prompt_eval_duration": 50_000_000,
                "eval_duration": 50_000_000
            }
        )
        mock_post.return_value.raise_for_status = Mock()
        client = OllamaClient()
        client.generate("Test prompt", system="You are an expert", use_cache=False)

        call_args = mock_post.call_args
        payload = call_args[1]["json"]
        assert payload["system"] == "You are an expert"


@pytest.mark.unit
@pytest.mark.service
class TestOllamaClientRetry:
    """Test OllamaClient retry logic."""

    @patch("app.services.ollama_client.requests.post")
    def test_analyze_with_retry_first_attempt(self, mock_post):
        """Test success on first attempt."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                "response": '{"result": "success"}',
                "model": "mistral:7b",
                "prompt_eval_count": 10,
                "eval_count": 5,
                "total_duration": 100_000_000,
                "load_duration": 0,
                "prompt_eval_duration": 50_000_000,
                "eval_duration": 50_000_000
            }
        )
        mock_post.return_value.raise_for_status = Mock()
        client = OllamaClient()
        client.clear_cache()
        result = client.analyze_with_retry("Test prompt", max_retries=3)

        assert result["response"] == {"result": "success"}

    @patch("app.services.ollama_client.requests.post")
    def test_analyze_with_retry_eventual_success(self, mock_post):
        """Test success after initial failures."""
        success_response = Mock(
            status_code=200,
            json=lambda: {
                "response": '{"result": "success"}',
                "model": "mistral:7b",
                "prompt_eval_count": 10,
                "eval_count": 5,
                "total_duration": 100_000_000,
                "load_duration": 0,
                "prompt_eval_duration": 50_000_000,
                "eval_duration": 50_000_000
            }
        )
        success_response.raise_for_status = Mock()

        mock_post.side_effect = [
            requests.exceptions.Timeout("Timeout"),
            requests.exceptions.Timeout("Timeout"),
            success_response
        ]

        client = OllamaClient()
        client.clear_cache()
        result = client.analyze_with_retry("Test prompt", max_retries=3)

        assert result["response"] == {"result": "success"}
        assert mock_post.call_count == 3

    @patch("app.services.ollama_client.requests.post")
    def test_analyze_with_retry_all_fail(self, mock_post):
        """Test OllamaError after all retries exhausted."""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")
        client = OllamaClient()
        client.clear_cache()

        with pytest.raises(OllamaError, match="All 3 attempts failed"):
            client.analyze_with_retry("Test prompt", max_retries=3)


@pytest.mark.unit
@pytest.mark.service
class TestOllamaClientCache:
    """Test OllamaClient caching."""

    def test_clear_cache(self):
        """Test cache clearing."""
        client = OllamaClient()
        client._cache["test_key"] = {"data": "cached"}
        assert len(client._cache) == 1

        client.clear_cache()
        assert len(client._cache) == 0

    def test_cache_key_deterministic(self):
        """Test that same inputs produce same cache key."""
        client = OllamaClient()
        key1 = client._get_cache_key("prompt1", "system1")
        key2 = client._get_cache_key("prompt1", "system1")
        assert key1 == key2

    def test_cache_key_varies_with_input(self):
        """Test that different inputs produce different cache keys."""
        client = OllamaClient()
        key1 = client._get_cache_key("prompt1", "system1")
        key2 = client._get_cache_key("prompt2", "system1")
        key3 = client._get_cache_key("prompt1", "system2")
        assert key1 != key2
        assert key1 != key3

    def test_cache_key_none_system(self):
        """Test cache key with None system prompt."""
        client = OllamaClient()
        key1 = client._get_cache_key("prompt", None)
        key2 = client._get_cache_key("prompt", None)
        assert key1 == key2


@pytest.mark.unit
@pytest.mark.service
class TestOllamaClientFactory:
    """Test get_ollama_client factory function."""

    def test_factory_defaults(self):
        """Test factory with no config."""
        client = get_ollama_client()
        assert client.base_url == "http://localhost:11434"
        assert client.model == "mistral:7b"
        assert client.temperature == 0.1
        assert client.timeout == 30

    def test_factory_custom_config(self):
        """Test factory with custom config."""
        config = {
            "base_url": "http://custom:8080",
            "model": "codellama:7b",
            "temperature": 0.3,
            "timeout": 60
        }
        client = get_ollama_client(config)
        assert client.base_url == "http://custom:8080"
        assert client.model == "codellama:7b"
        assert client.temperature == 0.3
        assert client.timeout == 60

    def test_factory_partial_config(self):
        """Test factory with partial config uses defaults for missing keys."""
        config = {"model": "phi:latest"}
        client = get_ollama_client(config)
        assert client.model == "phi:latest"
        assert client.base_url == "http://localhost:11434"  # default
