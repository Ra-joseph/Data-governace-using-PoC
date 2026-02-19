"""
Tests for semantic policy scanning with LLM.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.ollama_client import OllamaClient, OllamaError, get_ollama_client
from app.services.semantic_policy_engine import SemanticPolicyEngine
from app.schemas.contract import ValidationStatus, ViolationType


class TestOllamaClient:
    """Test Ollama client functionality."""

    def test_ollama_client_initialization(self):
        """Test OllamaClient initialization."""
        client = OllamaClient(
            base_url="http://localhost:11434",
            model="mistral:7b",
            temperature=0.1,
            timeout=30
        )

        assert client.base_url == "http://localhost:11434"
        assert client.model == "mistral:7b"
        assert client.temperature == 0.1
        assert client.timeout == 30

    @patch('requests.get')
    def test_is_available_success(self, mock_get):
        """Test Ollama availability check when running."""
        mock_get.return_value.status_code = 200

        client = OllamaClient()
        assert client.is_available() is True

    @patch('requests.get')
    def test_is_available_failure(self, mock_get):
        """Test Ollama availability check when not running."""
        import requests as req
        mock_get.side_effect = req.exceptions.ConnectionError("Connection refused")

        client = OllamaClient()
        assert client.is_available() is False

    @patch('requests.get')
    def test_list_models(self, mock_get):
        """Test listing available models."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'models': [
                {'name': 'mistral:7b'},
                {'name': 'llama2:7b'}
            ]
        }
        mock_get.return_value = mock_response

        client = OllamaClient()
        models = client.list_models()

        assert len(models) == 2
        assert 'mistral:7b' in models
        assert 'llama2:7b' in models

    @patch('requests.post')
    def test_generate_success(self, mock_post):
        """Test successful LLM generation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': '{"is_sensitive": true, "confidence": 85}',
            'model': 'mistral:7b',
            'prompt_eval_count': 100,
            'eval_count': 50,
            'total_duration': 2000000000,  # 2 seconds in nanoseconds
            'load_duration': 500000000,
            'prompt_eval_duration': 1000000000,
            'eval_duration': 500000000
        }
        mock_post.return_value = mock_response

        client = OllamaClient()
        result = client.generate("Test prompt", format="json")

        assert 'response' in result
        assert result['response']['is_sensitive'] is True
        assert result['response']['confidence'] == 85
        assert result['tokens']['total'] == 150

    @patch('requests.post')
    def test_generate_timeout(self, mock_post):
        """Test LLM generation timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        client = OllamaClient(timeout=5)

        with pytest.raises(OllamaError) as exc_info:
            client.generate("Test prompt")

        assert "timed out" in str(exc_info.value).lower()

    def test_cache_functionality(self):
        """Test response caching."""
        client = OllamaClient()

        # Mock the generate to avoid actual API call
        with patch.object(client, 'generate', wraps=client.generate) as mock_generate:
            # Set up mock response
            mock_result = {'response': {'test': 'data'}, 'raw_text': '{"test": "data"}'}

            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    'response': '{"test": "data"}',
                    'model': 'mistral:7b',
                    'prompt_eval_count': 10,
                    'eval_count': 5,
                    'total_duration': 1000000000,
                    'load_duration': 100000000,
                    'prompt_eval_duration': 500000000,
                    'eval_duration': 400000000
                }
                mock_post.return_value = mock_response

                # First call
                result1 = client.generate("test", use_cache=True)

                # Second call should use cache
                result2 = client.generate("test", use_cache=True)

                # API should only be called once
                assert mock_post.call_count == 1

    def test_get_ollama_client_factory(self):
        """Test factory function for creating OllamaClient."""
        config = {
            'base_url': 'http://test:11434',
            'model': 'llama2:7b',
            'temperature': 0.2,
            'timeout': 60
        }

        client = get_ollama_client(config)

        assert client.base_url == 'http://test:11434'
        assert client.model == 'llama2:7b'
        assert client.temperature == 0.2
        assert client.timeout == 60


class TestSemanticPolicyEngine:
    """Test semantic policy engine functionality."""

    @pytest.fixture
    def mock_ollama_client(self):
        """Create a mock Ollama client."""
        client = Mock(spec=OllamaClient)
        client.is_available.return_value = True
        return client

    @pytest.fixture
    def sample_contract(self):
        """Sample contract data for testing."""
        return {
            'dataset': {
                'name': 'customer_data',
                'description': 'Customer information',
                'owner_name': 'John Doe',
                'owner_email': 'john@example.com'
            },
            'schema': [
                {
                    'name': 'user_info',
                    'type': 'string',
                    'description': 'Contains user personal information',
                    'pii': False
                },
                {
                    'name': 'account_id',
                    'type': 'integer',
                    'description': 'Account identifier',
                    'pii': False
                }
            ],
            'governance': {
                'classification': 'internal',
                'encryption_required': False,
                'compliance_tags': []
            },
            'quality_rules': {}
        }

    def test_semantic_engine_initialization(self):
        """Test SemanticPolicyEngine initialization."""
        engine = SemanticPolicyEngine(enabled=False)
        assert engine.enabled is False

    def test_semantic_engine_disabled(self, sample_contract):
        """Test that disabled engine returns passed status."""
        engine = SemanticPolicyEngine(enabled=False)

        result = engine.validate_contract(sample_contract)

        assert result.status == ValidationStatus.PASSED
        assert len(result.violations) == 0

    @patch('app.services.semantic_policy_engine.get_ollama_client')
    def test_semantic_engine_unavailable_ollama(self, mock_get_client, sample_contract):
        """Test behavior when Ollama is not available."""
        mock_client = Mock()
        mock_client.is_available.return_value = False
        mock_get_client.return_value = mock_client

        engine = SemanticPolicyEngine(enabled=True)

        result = engine.validate_contract(sample_contract)

        # Should return passed since semantic is not available
        assert result.status == ValidationStatus.PASSED

    @patch('app.services.semantic_policy_engine.get_ollama_client')
    def test_validate_contract_with_semantic(self, mock_get_client, sample_contract):
        """Test contract validation with semantic policies."""
        # Setup mock Ollama client
        mock_client = Mock(spec=OllamaClient)
        mock_client.is_available.return_value = True

        # Mock LLM response for SEM001 (sensitive data detection)
        mock_client.analyze_with_retry.return_value = {
            'response': {
                'is_sensitive': True,
                'confidence': 85,
                'reasoning': 'Field name suggests personal information',
                'suggested_classification': 'confidential',
                'recommended_actions': ['Mark field as PII', 'Enable encryption']
            },
            'raw_text': '...',
            'tokens': {'total': 100},
            'timing': {'total_duration': 1.5}
        }

        mock_get_client.return_value = mock_client

        engine = SemanticPolicyEngine(enabled=True)

        # Run validation on specific policy
        result = engine.validate_contract(sample_contract, selected_policies=['SEM001'])

        # Should detect a violation
        assert len(result.violations) > 0
        assert any('SEM001' in v.policy for v in result.violations)

    def test_format_fields_list(self):
        """Test field list formatting."""
        engine = SemanticPolicyEngine(enabled=False)

        schema = [
            {'name': 'email', 'type': 'string', 'description': 'Email address', 'pii': True},
            {'name': 'count', 'type': 'integer', 'description': 'Counter', 'pii': False}
        ]

        formatted = engine._format_fields_list(schema)

        assert 'email' in formatted
        assert 'string' in formatted
        assert '[PII]' in formatted
        assert 'Email address' in formatted

    def test_severity_conversion(self):
        """Test severity string to ViolationType conversion."""
        engine = SemanticPolicyEngine(enabled=False)

        assert engine._severity_to_type('critical') == ViolationType.CRITICAL
        assert engine._severity_to_type('high') == ViolationType.CRITICAL
        assert engine._severity_to_type('warning') == ViolationType.WARNING
        assert engine._severity_to_type('medium') == ViolationType.WARNING
        assert engine._severity_to_type('info') == ViolationType.INFO


class TestSemanticIntegration:
    """Integration tests for semantic scanning."""

    @pytest.fixture
    def sample_contract_with_pii(self):
        """Sample contract with PII fields."""
        return {
            'dataset': {
                'name': 'sensitive_data',
                'description': 'Contains sensitive customer information',
                'owner_name': 'Jane Smith',
                'owner_email': 'jane@example.com'
            },
            'schema': [
                {
                    'name': 'customer_ssn',
                    'type': 'string',
                    'description': 'Social Security Number',
                    'pii': True
                },
                {
                    'name': 'personal_details',
                    'type': 'json',
                    'description': 'Personal information blob',
                    'pii': False  # Not marked but may contain PII
                }
            ],
            'governance': {
                'classification': 'confidential',
                'encryption_required': True,
                'compliance_tags': ['GDPR', 'CCPA']
            },
            'quality_rules': {
                'completeness_threshold': 99
            }
        }

    def test_combined_validation_without_semantic(self, sample_contract_with_pii):
        """Test that contract service works without semantic scanning."""
        from app.services.contract_service import ContractService

        service = ContractService(enable_semantic=False)

        result = service.validate_contract_combined(sample_contract_with_pii)

        # Should have rule-based violations only
        assert result is not None
        assert isinstance(result.status, ValidationStatus)

    @patch('app.services.semantic_policy_engine.get_ollama_client')
    def test_combined_validation_with_semantic_disabled_ollama(
        self, mock_get_client, sample_contract_with_pii
    ):
        """Test combined validation when Ollama is not available."""
        from app.services.contract_service import ContractService

        mock_client = Mock()
        mock_client.is_available.return_value = False
        mock_get_client.return_value = mock_client

        service = ContractService(enable_semantic=True)

        result = service.validate_contract_combined(sample_contract_with_pii)

        # Should still work with only rule-based validation
        assert result is not None
        assert isinstance(result.status, ValidationStatus)
