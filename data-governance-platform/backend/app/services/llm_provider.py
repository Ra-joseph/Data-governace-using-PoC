"""
Abstract base class for LLM providers.

This module defines the interface that all LLM provider implementations must
conform to, enabling the platform to swap between different LLM backends
(e.g., Ollama, OpenAI, Azure) without changing consuming code. It also defines
the base exception hierarchy for LLM-related errors.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class LLMProviderError(Exception):
    """Base exception for LLM provider errors.

    All provider-specific exceptions (e.g., OllamaError) should inherit
    from this class so that consuming code can catch a single base type
    regardless of the underlying provider.
    """
    pass


class LLMProvider(ABC):
    """Abstract base class that all LLM provider implementations must extend.

    Defines the contract for availability checks, text generation, retried
    analysis, model listing, and cache management. Implementations are
    expected to handle provider-specific transport, authentication, and
    response parsing internally while exposing a uniform interface.
    """

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the LLM provider is reachable and ready to serve requests.

        Returns:
            True if the provider is available, False otherwise.
        """
        ...

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format: str = "json",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Generate a response from the LLM.

        Args:
            prompt: The user prompt to send to the model.
            system: Optional system prompt to set context for the generation.
            format: Desired response format. Use ``"json"`` for structured
                output or ``"text"`` for free-form text.
            use_cache: Whether to return a cached response when one exists
                for an identical request.

        Returns:
            Dictionary containing at minimum:
                - ``response``: The parsed model output (dict when format is
                  ``"json"``, string otherwise).
                - ``raw_text``: The raw text returned by the model.
                - ``model``: Identifier of the model that produced the response.

        Raises:
            LLMProviderError: If the request fails after exhausting any
                internal retry logic.
        """
        ...

    @abstractmethod
    def analyze_with_retry(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Generate a response with automatic retries on transient failures.

        This is a convenience wrapper around :meth:`generate` that retries
        on provider errors up to *max_retries* times before raising.

        Args:
            prompt: The user prompt to send to the model.
            system: Optional system prompt to set context.
            max_retries: Maximum number of attempts before giving up.

        Returns:
            Dictionary with the same structure as :meth:`generate`.

        Raises:
            LLMProviderError: If all retry attempts are exhausted.
        """
        ...

    @abstractmethod
    def list_models(self) -> list:
        """List models available on the provider.

        Returns:
            A list of model name strings. Returns an empty list if the
            provider is unreachable or the query fails.
        """
        ...

    def clear_cache(self) -> None:
        """Clear any cached LLM responses.

        The default implementation is a no-op. Providers that maintain a
        response cache should override this method.
        """
        pass
