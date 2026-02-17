"""
Ollama Client for local LLM execution.

This module provides an interface to interact with Ollama running locally,
enabling semantic policy evaluation without relying on external APIs.
"""

import json
import requests
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class OllamaClient:
    """Client for interacting with local Ollama instance."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "mistral:7b",
        temperature: float = 0.1,
        timeout: int = 30
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Base URL of Ollama server
            model: Model name to use (e.g., mistral:7b, codellama:7b)
            temperature: Temperature for generation (0.0 = deterministic)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self._cache: Dict[str, Any] = {}

    def is_available(self) -> bool:
        """
        Check if Ollama is available and responding.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def list_models(self) -> list:
        """
        List available models in Ollama.

        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model['name'] for model in data.get('models', [])]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list models: {e}")
            return []

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        format: str = "json",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response from Ollama.

        Args:
            prompt: The prompt to send to the model
            system: Optional system prompt to set context
            format: Response format (json or text)
            use_cache: Whether to use cached responses

        Returns:
            Dictionary with response and metadata

        Raises:
            OllamaError: If the request fails
        """
        # Check cache
        cache_key = self._get_cache_key(prompt, system)
        if use_cache and cache_key in self._cache:
            logger.info(f"Using cached response for prompt")
            return self._cache[cache_key]

        # Prepare request
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": self.temperature,
            "stream": False
        }

        if system:
            payload["system"] = system

        if format == "json":
            payload["format"] = "json"

        try:
            logger.info(f"Sending request to Ollama: model={self.model}, prompt_length={len(prompt)}")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get('response', '').strip()

            # Parse JSON response if requested
            parsed_response = response_text
            if format == "json":
                try:
                    parsed_response = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON response: {e}")
                    # Return error structure
                    parsed_response = {
                        "error": "Failed to parse JSON",
                        "raw_response": response_text
                    }

            output = {
                "response": parsed_response,
                "raw_text": response_text,
                "model": result.get('model'),
                "tokens": {
                    "prompt": result.get('prompt_eval_count', 0),
                    "response": result.get('eval_count', 0),
                    "total": result.get('prompt_eval_count', 0) + result.get('eval_count', 0)
                },
                "timing": {
                    "total_duration": result.get('total_duration', 0) / 1e9,  # Convert to seconds
                    "load_duration": result.get('load_duration', 0) / 1e9,
                    "prompt_eval_duration": result.get('prompt_eval_duration', 0) / 1e9,
                    "eval_duration": result.get('eval_duration', 0) / 1e9
                }
            }

            # Cache successful response
            if use_cache:
                self._cache[cache_key] = output

            logger.info(f"Ollama response received: tokens={output['tokens']['total']}, "
                       f"time={output['timing']['total_duration']:.2f}s")

            return output

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s")
            raise OllamaError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama request failed: {e}")
            raise OllamaError(f"Request failed: {str(e)}")

    def analyze_with_retry(
        self,
        prompt: str,
        system: Optional[str] = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Generate response with automatic retries.

        Args:
            prompt: The prompt to send
            system: Optional system prompt
            max_retries: Maximum number of retry attempts

        Returns:
            Dictionary with response and metadata
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return self.generate(prompt, system, format="json")
            except OllamaError as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying...")

        # All retries failed
        raise OllamaError(f"All {max_retries} attempts failed. Last error: {last_error}")

    def clear_cache(self):
        """Clear the response cache."""
        self._cache.clear()
        logger.info("Ollama cache cleared")

    def _get_cache_key(self, prompt: str, system: Optional[str]) -> str:
        """Generate cache key from prompt and system message."""
        import hashlib
        content = f"{prompt}:{system or ''}:{self.model}:{self.temperature}"
        return hashlib.sha256(content.encode()).hexdigest()


class OllamaError(Exception):
    """Exception raised for Ollama-related errors."""
    pass


def get_ollama_client(config: Optional[Dict[str, Any]] = None) -> OllamaClient:
    """
    Factory function to create OllamaClient with configuration.

    Args:
        config: Optional configuration dict with keys: base_url, model, temperature, timeout

    Returns:
        Configured OllamaClient instance
    """
    if config is None:
        config = {}

    return OllamaClient(
        base_url=config.get('base_url', 'http://localhost:11434'),
        model=config.get('model', 'mistral:7b'),
        temperature=config.get('temperature', 0.1),
        timeout=config.get('timeout', 30)
    )
