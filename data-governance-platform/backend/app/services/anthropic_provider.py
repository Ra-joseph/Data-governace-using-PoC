"""
Anthropic Claude LLM provider implementation.

This module implements the LLMProvider ABC for Anthropic's Claude API,
enabling semantic policy evaluation using Claude models as an alternative
to local Ollama inference.
"""

import hashlib
import json
import time
import logging
from typing import Any, Dict, List, Optional

from app.services.llm_provider import LLMProvider, LLMProviderError

try:
    import anthropic
except ImportError:
    anthropic = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

# Static list of known Claude model identifiers.
_KNOWN_CLAUDE_MODELS: List[str] = [
    "claude-sonnet-4-20250514",
    "claude-haiku-4-20250414",
    "claude-opus-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
]


class AnthropicProvider(LLMProvider):
    """LLM provider backed by the Anthropic Claude API.

    Conforms to the same response dict shape returned by
    ``OllamaClient.generate()`` so that consuming code (e.g. the semantic
    policy engine and policy orchestrator) can swap providers transparently.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        temperature: float = 0.1,
        timeout: int = 30,
        max_tokens: int = 1024,
    ):
        """Initialize the Anthropic provider.

        Args:
            api_key: Anthropic API key used for authentication.
            model: Claude model identifier (e.g. ``"claude-sonnet-4-20250514"``).
            temperature: Sampling temperature (0.0 = near-deterministic).
            timeout: Request timeout in seconds.
            max_tokens: Maximum number of tokens to generate per request.
        """
        if anthropic is None:
            raise LLMProviderError(
                "The 'anthropic' package is not installed. "
                "Install it with: pip install anthropic"
            )
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_tokens = max_tokens
        self._cache: Dict[str, Any] = {}
        self._client = anthropic.Anthropic(
            api_key=self.api_key,
            timeout=self.timeout,
        )

    # ------------------------------------------------------------------
    # LLMProvider interface
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check whether the Anthropic API is reachable.

        Sends a minimal request to verify that the API key is valid and
        the service is responding.

        Returns:
            True if the API is reachable and the key is accepted, False
            otherwise.
        """
        try:
            self._client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return True
        except Exception as exc:
            logger.debug("Anthropic availability check failed: %s", exc)
            return False

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format: str = "json",
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Generate a response from the Claude API.

        Args:
            prompt: The user prompt to send to the model.
            system: Optional system prompt to set context.
            format: Desired response format. ``"json"`` attempts to parse the
                model output as JSON; ``"text"`` returns raw text.
            use_cache: Whether to return a cached response when one exists
                for an identical request.

        Returns:
            Standardized dictionary matching the shape returned by
            ``OllamaClient.generate()``.

        Raises:
            LLMProviderError: If the API request fails.
        """
        cache_key = self._get_cache_key(prompt, system)
        if use_cache and cache_key in self._cache:
            logger.info("Using cached Anthropic response for prompt")
            return self._cache[cache_key]

        try:
            kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system

            logger.info(
                "Sending request to Anthropic: model=%s, prompt_length=%d",
                self.model,
                len(prompt),
            )

            start_time = time.monotonic()
            message = self._client.messages.create(**kwargs)
            elapsed = time.monotonic() - start_time

            response_text = message.content[0].text.strip()

            # Parse JSON response if requested.
            parsed_response: Any = response_text
            if format == "json":
                try:
                    parsed_response = json.loads(response_text)
                except json.JSONDecodeError as exc:
                    logger.warning("Failed to parse JSON response: %s", exc)
                    parsed_response = {
                        "error": "Failed to parse JSON",
                        "raw_response": response_text,
                    }

            prompt_tokens = message.usage.input_tokens
            response_tokens = message.usage.output_tokens

            output: Dict[str, Any] = {
                "response": parsed_response,
                "raw_text": response_text,
                "model": self.model,
                "tokens": {
                    "prompt": prompt_tokens,
                    "response": response_tokens,
                    "total": prompt_tokens + response_tokens,
                },
                "timing": {
                    "total_duration": elapsed,
                    "load_duration": 0,
                    "prompt_eval_duration": 0,
                    "eval_duration": elapsed,
                },
            }

            if use_cache:
                self._cache[cache_key] = output

            logger.info(
                "Anthropic response received: tokens=%d, time=%.2fs",
                output["tokens"]["total"],
                output["timing"]["total_duration"],
            )

            return output

        except LLMProviderError:
            raise
        except Exception as exc:
            logger.error("Anthropic request failed: %s", exc)
            raise LLMProviderError(f"Anthropic request failed: {exc}") from exc

    def analyze_with_retry(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_retries: int = 3,
    ) -> Dict[str, Any]:
        """Generate a response with automatic retries on transient failures.

        Args:
            prompt: The user prompt to send to the model.
            system: Optional system prompt to set context.
            max_retries: Maximum number of attempts before giving up.

        Returns:
            Standardized dictionary matching the shape returned by
            ``generate()``.

        Raises:
            LLMProviderError: If all retry attempts are exhausted.
        """
        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                return self.generate(prompt, system, format="json")
            except LLMProviderError as exc:
                last_error = exc
                logger.warning(
                    "Attempt %d/%d failed: %s", attempt + 1, max_retries, exc
                )
                if attempt < max_retries - 1:
                    logger.info("Retrying...")

        raise LLMProviderError(
            f"All {max_retries} attempts failed. Last error: {last_error}"
        )

    def list_models(self) -> list:
        """Return a static list of known Claude model identifiers.

        Returns:
            List of model name strings.
        """
        return list(_KNOWN_CLAUDE_MODELS)

    def clear_cache(self) -> None:
        """Clear the in-memory response cache."""
        self._cache.clear()
        logger.info("Anthropic response cache cleared")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_cache_key(self, prompt: str, system: Optional[str]) -> str:
        """Generate a SHA-256 cache key from the prompt, system message, and model settings.

        Args:
            prompt: The user prompt.
            system: Optional system prompt.

        Returns:
            Hex-encoded SHA-256 digest string.
        """
        content = f"{prompt}:{system or ''}:{self.model}:{self.temperature}"
        return hashlib.sha256(content.encode()).hexdigest()
