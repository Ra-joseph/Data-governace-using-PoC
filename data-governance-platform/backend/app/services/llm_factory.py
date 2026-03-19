"""
LLM provider factory.

This module provides a factory function that reads the platform configuration
and returns the appropriate LLMProvider instance. Lazy imports ensure that
only the selected provider's SDK is loaded, keeping unused SDKs optional.
"""

import logging
from typing import Any, Dict, Optional

from app.config import settings
from app.services.llm_provider import LLMProvider

logger = logging.getLogger(__name__)


def get_llm_provider(config: Optional[Dict[str, Any]] = None) -> LLMProvider:
    """Create and return the configured LLM provider.

    The provider is selected based on the ``LLM_PROVIDER`` setting (or the
    ``provider`` key in *config* if supplied).  Supported values are
    ``"ollama"`` (default) and ``"anthropic"``.

    Args:
        config: Optional configuration dict that can override settings.
            Recognised keys: ``provider``, plus provider-specific keys
            (``base_url``, ``model``, ``temperature``, ``timeout``,
            ``api_key``).

    Returns:
        A configured :class:`LLMProvider` instance ready for use.
    """
    if config is None:
        config = {}

    provider_name = config.get('provider', settings.LLM_PROVIDER).lower()

    if provider_name == "anthropic":
        from app.services.anthropic_provider import AnthropicProvider

        provider = AnthropicProvider(
            api_key=config.get('api_key', settings.ANTHROPIC_API_KEY),
            model=config.get('model', settings.ANTHROPIC_MODEL),
            temperature=config.get('temperature', 0.1),
            timeout=config.get('timeout', settings.LLM_TIMEOUT),
        )
        logger.info("Using Anthropic LLM provider (model=%s)", provider.model)
        return provider

    # Default: Ollama (also handles unrecognised provider names)
    from app.services.ollama_client import OllamaClient

    if provider_name not in ("ollama", ""):
        logger.warning(
            "Unrecognised LLM_PROVIDER '%s', falling back to Ollama",
            provider_name,
        )

    provider = OllamaClient(
        base_url=config.get('base_url', settings.OLLAMA_BASE_URL),
        model=config.get('model', settings.OLLAMA_MODEL),
        temperature=config.get('temperature', 0.1),
        timeout=config.get('timeout', settings.OLLAMA_TIMEOUT),
    )
    logger.info("Using Ollama LLM provider (model=%s)", provider.model)
    return provider
