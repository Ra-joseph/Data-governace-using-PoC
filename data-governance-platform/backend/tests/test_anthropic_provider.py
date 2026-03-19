"""
Unit tests for AnthropicProvider LLM provider.

All tests mock the anthropic SDK so no API keys or network access are required.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock

from app.services.llm_provider import LLMProvider, LLMProviderError
from app.services.ollama_client import OllamaError


def _make_provider(mock_anthropic_module=None):
    """Create an AnthropicProvider with a mocked anthropic SDK client."""
    if mock_anthropic_module is None:
        mock_anthropic_module = Mock()
    mock_client = Mock()
    mock_anthropic_module.Anthropic.return_value = mock_client

    with patch("app.services.anthropic_provider.anthropic", mock_anthropic_module):
        from app.services.anthropic_provider import AnthropicProvider
        provider = AnthropicProvider(api_key="test-key")
    return provider, mock_client


@pytest.mark.unit
@pytest.mark.service
class TestAnthropicProviderInit:
    """Test AnthropicProvider initialization."""

    def test_default_initialization(self):
        """Test provider initializes with default values."""
        provider, _ = _make_provider()
        assert provider.api_key == "test-key"
        assert provider.model == "claude-sonnet-4-20250514"
        assert provider.temperature == 0.1
        assert provider.timeout == 30
        assert provider.max_tokens == 1024
        assert provider._cache == {}

    def test_custom_initialization(self):
        """Test provider initializes with custom values."""
        mock_mod = Mock()
        mock_mod.Anthropic.return_value = Mock()
        with patch("app.services.anthropic_provider.anthropic", mock_mod):
            from app.services.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(
                api_key="sk-test",
                model="claude-3-opus-20240229",
                temperature=0.5,
                timeout=60,
                max_tokens=2048
            )
        assert provider.model == "claude-3-opus-20240229"
        assert provider.temperature == 0.5
        assert provider.timeout == 60
        assert provider.max_tokens == 2048

    def test_implements_llm_provider(self):
        """Test that AnthropicProvider is a subclass of LLMProvider."""
        from app.services.anthropic_provider import AnthropicProvider
        assert issubclass(AnthropicProvider, LLMProvider)
        provider, _ = _make_provider()
        assert isinstance(provider, LLMProvider)


@pytest.mark.unit
@pytest.mark.service
class TestAnthropicProviderAvailability:
    """Test AnthropicProvider.is_available()."""

    def test_is_available_success(self):
        """Test is_available returns True when API responds."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text="pong")]
        )
        assert provider.is_available() is True

    def test_is_available_failure(self):
        """Test is_available returns False on API error."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.side_effect = Exception("Auth failed")
        assert provider.is_available() is False


@pytest.mark.unit
@pytest.mark.service
class TestAnthropicProviderGenerate:
    """Test AnthropicProvider.generate()."""

    def test_generate_json_success(self):
        """Test successful JSON generation."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text='{"is_sensitive": true, "confidence": 85}')],
            usage=Mock(input_tokens=100, output_tokens=50),
        )

        result = provider.generate("Analyze this schema", system="You are a governance expert")

        assert result["response"] == {"is_sensitive": True, "confidence": 85}
        assert result["raw_text"] == '{"is_sensitive": true, "confidence": 85}'
        assert result["model"] == "claude-sonnet-4-20250514"
        assert result["tokens"]["prompt"] == 100
        assert result["tokens"]["response"] == 50
        assert result["tokens"]["total"] == 150
        assert "total_duration" in result["timing"]

    def test_generate_text_format(self):
        """Test text format generation (no JSON parsing)."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text="This is a plain text response.")],
            usage=Mock(input_tokens=50, output_tokens=20),
        )

        result = provider.generate("Test", format="text")

        assert result["response"] == "This is a plain text response."
        assert result["raw_text"] == "This is a plain text response."

    def test_generate_invalid_json(self):
        """Test graceful handling of invalid JSON response."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text="This is not valid JSON")],
            usage=Mock(input_tokens=50, output_tokens=20),
        )

        result = provider.generate("Test", format="json")

        assert result["response"]["error"] == "Failed to parse JSON"
        assert result["response"]["raw_response"] == "This is not valid JSON"

    def test_generate_api_error(self):
        """Test that API errors raise LLMProviderError."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.side_effect = Exception("Rate limited")

        with pytest.raises(LLMProviderError, match="Anthropic request failed"):
            provider.generate("Test prompt")

    def test_generate_with_system_prompt(self):
        """Test that system prompt is passed to the API."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text='{"result": "ok"}')],
            usage=Mock(input_tokens=80, output_tokens=10),
        )

        provider.generate("Analyze", system="You are a data governance expert")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "You are a data governance expert"

    def test_generate_without_system_prompt(self):
        """Test that system key is omitted when no system prompt."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text='{"result": "ok"}')],
            usage=Mock(input_tokens=80, output_tokens=10),
        )

        provider.generate("Analyze")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert "system" not in call_kwargs


@pytest.mark.unit
@pytest.mark.service
class TestAnthropicProviderCache:
    """Test AnthropicProvider caching."""

    def test_cache_hit(self):
        """Test that identical prompts return cached responses."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text='{"cached": true}')],
            usage=Mock(input_tokens=50, output_tokens=10),
        )

        # First call hits API
        result1 = provider.generate("Test prompt", use_cache=True)
        # Second call should use cache
        result2 = provider.generate("Test prompt", use_cache=True)

        assert result1 == result2
        assert mock_client.messages.create.call_count == 1

    def test_cache_bypass(self):
        """Test that use_cache=False bypasses cache."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text='{"cached": false}')],
            usage=Mock(input_tokens=50, output_tokens=10),
        )

        provider.generate("Test prompt", use_cache=False)
        provider.generate("Test prompt", use_cache=False)

        assert mock_client.messages.create.call_count == 2

    def test_clear_cache(self):
        """Test cache clearing."""
        provider, _ = _make_provider()
        provider._cache["some_key"] = {"response": "cached"}

        provider.clear_cache()
        assert provider._cache == {}


@pytest.mark.unit
@pytest.mark.service
class TestAnthropicProviderRetry:
    """Test AnthropicProvider.analyze_with_retry()."""

    def test_retry_success_on_second_attempt(self):
        """Test retry succeeds after first failure."""
        provider, mock_client = _make_provider()

        # First call fails, second succeeds
        mock_client.messages.create.side_effect = [
            Exception("Temporary error"),
            Mock(
                content=[Mock(text='{"result": "ok"}')],
                usage=Mock(input_tokens=50, output_tokens=10),
            )
        ]

        result = provider.analyze_with_retry("Test prompt", max_retries=3)

        assert result["response"] == {"result": "ok"}
        assert mock_client.messages.create.call_count == 2

    def test_retry_all_attempts_fail(self):
        """Test that all retries exhausted raises LLMProviderError."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.side_effect = Exception("Persistent error")

        with pytest.raises(LLMProviderError, match="All 3 attempts failed"):
            provider.analyze_with_retry("Test prompt", max_retries=3)

    def test_retry_with_system_prompt(self):
        """Test retry passes system prompt through."""
        provider, mock_client = _make_provider()
        mock_client.messages.create.return_value = Mock(
            content=[Mock(text='{"ok": true}')],
            usage=Mock(input_tokens=50, output_tokens=10),
        )

        provider.analyze_with_retry("Test", system="Expert mode")

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "Expert mode"


@pytest.mark.unit
@pytest.mark.service
class TestAnthropicProviderModels:
    """Test AnthropicProvider.list_models()."""

    def test_list_models_returns_known_models(self):
        """Test that list_models returns known Claude models."""
        provider, _ = _make_provider()
        models = provider.list_models()

        assert isinstance(models, list)
        assert len(models) > 0
        assert "claude-sonnet-4-20250514" in models


@pytest.mark.unit
@pytest.mark.service
class TestLLMProviderErrorHierarchy:
    """Test that error hierarchy works correctly."""

    def test_ollama_error_is_llm_provider_error(self):
        """Test that OllamaError is a subclass of LLMProviderError."""
        assert issubclass(OllamaError, LLMProviderError)

    def test_catch_ollama_error_as_provider_error(self):
        """Test that OllamaError can be caught as LLMProviderError."""
        with pytest.raises(LLMProviderError):
            raise OllamaError("test error")

    def test_llm_provider_error_standalone(self):
        """Test LLMProviderError can be raised and caught directly."""
        with pytest.raises(LLMProviderError, match="direct error"):
            raise LLMProviderError("direct error")


@pytest.mark.unit
@pytest.mark.service
class TestLLMFactory:
    """Test the LLM provider factory."""

    @patch("app.services.llm_factory.settings")
    def test_factory_returns_ollama_by_default(self, mock_settings):
        """Test factory returns OllamaClient when LLM_PROVIDER is ollama."""
        mock_settings.LLM_PROVIDER = "ollama"
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "mistral:7b"
        mock_settings.OLLAMA_TIMEOUT = 30

        from app.services.llm_factory import get_llm_provider
        from app.services.ollama_client import OllamaClient

        provider = get_llm_provider()
        assert isinstance(provider, OllamaClient)

    @patch("app.services.llm_factory.settings")
    def test_factory_returns_anthropic(self, mock_settings):
        """Test factory returns AnthropicProvider when LLM_PROVIDER is anthropic."""
        mock_settings.LLM_PROVIDER = "anthropic"
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_settings.ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
        mock_settings.LLM_TIMEOUT = 30

        from app.services.llm_factory import get_llm_provider
        from app.services.anthropic_provider import AnthropicProvider

        provider = get_llm_provider()
        assert isinstance(provider, AnthropicProvider)

    @patch("app.services.llm_factory.settings")
    def test_factory_falls_back_to_ollama_for_unknown(self, mock_settings):
        """Test factory falls back to Ollama for unrecognised provider."""
        mock_settings.LLM_PROVIDER = "unknown_provider"
        mock_settings.OLLAMA_BASE_URL = "http://localhost:11434"
        mock_settings.OLLAMA_MODEL = "mistral:7b"
        mock_settings.OLLAMA_TIMEOUT = 30

        from app.services.llm_factory import get_llm_provider
        from app.services.ollama_client import OllamaClient

        provider = get_llm_provider()
        assert isinstance(provider, OllamaClient)

    def test_factory_config_override(self):
        """Test factory respects config dict override."""
        from app.services.llm_factory import get_llm_provider
        from app.services.anthropic_provider import AnthropicProvider

        provider = get_llm_provider({"provider": "anthropic", "api_key": "test"})
        assert isinstance(provider, AnthropicProvider)
