# Semantic Policy Scanning with Local LLM

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Setup Guide](#setup-guide)
- [Usage](#usage)
- [Configuration](#configuration)
- [Performance Considerations](#performance-considerations)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Comparison: Rule-Based vs Semantic](#comparison-rule-based-vs-semantic)
- [Advanced: Using Remote LLMs](#advanced-using-remote-llms)
- [FAQs](#faqs)
- [Examples](#examples)
- [Conclusion](#conclusion)
- [Quick Start Checklist](#quick-start-checklist)

## 🎯 Overview

The Data Governance Platform optionally supports **semantic policy scanning** powered by local LLM models via [Ollama](https://ollama.ai/). This feature is **disabled by default** (`ENABLE_LLM_VALIDATION=false`) and must be explicitly enabled in configuration. When disabled, the platform runs only the 17 deterministic rule-based policies. When enabled, semantic scanning adds 8 AI-powered policies that go beyond rule-based pattern matching to understand the **semantic meaning and context** of your data.

> **Note:** If your environment has restrictions on AI/LLM usage, you can skip this guide entirely. The rule-based policy engine provides comprehensive governance validation without any LLM dependency.

### Why Semantic Scanning?

Traditional rule-based policy engines excel at checking explicit patterns (e.g., "field named `ssn` requires encryption"), but they struggle with:

- **Context-aware detection**: Is `user_info` sensitive? Depends on what it contains
- **Business logic validation**: Do quality thresholds make sense for this data type?
- **Security pattern recognition**: Are there field combinations that create vulnerabilities?
- **Compliance verification**: Does the data actually require GDPR/CCPA compliance?

Semantic scanning uses AI to analyze these nuanced scenarios that require understanding context, relationships, and business meaning.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Contract Service                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   Combined Validation                                 │  │
│  │  ┌────────────────┐    ┌────────────────────────┐   │  │
│  │  │  Rule-Based    │    │  Semantic (LLM-based)  │   │  │
│  │  │  Policy Engine │    │  Policy Engine         │   │  │
│  │  └────────────────┘    └────────────────────────┘   │  │
│  │         │                         │                   │  │
│  │         ▼                         ▼                   │  │
│  │   17 YAML Policies        8 Semantic Policies        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │  Ollama Service  │
                        │  (Local LLM)     │
                        └──────────────────┘
                                  │
                        ┌─────────┴─────────┐
                        ▼                   ▼
                  mistral:7b          codellama:7b
```

## ✨ Features

### 8 Semantic Policies

1. **SEM001: Sensitive Data Context Detection**
   - Detects PII/sensitive data based on context, not just naming patterns
   - Example: Identifies that `user_details` contains personal information

2. **SEM002: Business Logic Consistency**
   - Validates that governance rules make business sense
   - Example: Catches when retention period doesn't match classification level

3. **SEM003: Security Pattern Detection**
   - Identifies potential security vulnerabilities in schema design
   - Example: Detects fields that together expose too much information

4. **SEM004: Compliance Intent Verification**
   - Verifies that compliance tags actually apply to the data
   - Example: Ensures GDPR is appropriate for the data and geography

5. **SEM005: Data Quality Semantic Validation**
   - Validates that quality thresholds make sense for the data type
   - Example: Checks if 99% completeness is realistic for optional fields

6. **SEM006: Field Relationship Analysis**
   - Detects semantic relationships between fields
   - Example: Identifies that `user_id` + `email` together increase sensitivity

7. **SEM007: Naming Convention Analysis**
   - Analyzes naming for clarity and consistency
   - Example: Suggests clearer names for ambiguous abbreviations

8. **SEM008: Use Case Appropriateness**
   - Evaluates if approved use cases fit the data classification
   - Example: Flags when "marketing" use case conflicts with "restricted" classification

## 🚀 Setup Guide

### Prerequisites

- Docker (for running the platform)
- Ollama installed locally
- `ENABLE_LLM_VALIDATION=true` set in `backend/.env`

### Step 0: Enable LLM Validation in Configuration

Before installing Ollama, enable the feature in your backend configuration:

```bash
# Create or edit the .env file in the backend directory
echo "ENABLE_LLM_VALIDATION=true" >> backend/.env

# Optionally configure Ollama connection settings (defaults shown):
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=mistral:7b
# OLLAMA_TIMEOUT=30
```

> **Important:** Without this setting, all semantic endpoints will return "LLM validation is disabled by configuration" even if Ollama is running.

### Step 1: Install Ollama

```bash
# Linux / macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

### Step 2: Start Ollama

```bash
ollama serve
```

Ollama will start on `http://localhost:11434`

### Step 3: Pull a Model

```bash
# Recommended: Mistral 7B (good balance of performance and size)
ollama pull mistral:7b

# Alternative options:
ollama pull codellama:7b  # Better for code understanding
ollama pull llama2:7b     # General purpose
ollama pull phi:latest    # Smaller, faster (2.7GB)
```

### Step 4: Verify Setup

Check that semantic scanning is available:

```bash
curl http://localhost:8000/api/v1/semantic/health
```

Expected response (when `ENABLE_LLM_VALIDATION=true` and Ollama is running):
```json
{
  "available": true,
  "ollama_running": true,
  "available_models": ["mistral:7b"],
  "current_model": "mistral:7b",
  "policies_loaded": 8,
  "message": "Semantic scanning is available with 8 policies"
}
```

If `ENABLE_LLM_VALIDATION` is not set or is `false`, you will see:
```json
{
  "available": false,
  "ollama_running": false,
  "available_models": [],
  "current_model": "disabled",
  "policies_loaded": 0,
  "message": "LLM validation is disabled by configuration. Set ENABLE_LLM_VALIDATION=true to enable."
}
```

## 📚 Usage

### API Endpoints

#### 1. Check Semantic Health

```bash
GET /api/v1/semantic/health
```

Returns status of Ollama, available models, and loaded policies.

#### 2. List Semantic Policies

```bash
GET /api/v1/semantic/policies
```

Returns all 8 semantic policies with descriptions.

#### 3. Run Semantic Validation

```bash
POST /api/v1/semantic/validate
Content-Type: application/json

{
  "contract_id": 1,
  "selected_policies": ["SEM001", "SEM002"]  // Optional: run specific policies
}
```

Runs semantic validation on an existing contract.

#### 4. List Available Models

```bash
GET /api/v1/semantic/models
```

Lists models available in Ollama.

#### 5. Pull a New Model

```bash
POST /api/v1/semantic/models/pull/mistral:7b
```

Triggers model download (runs in background).

### Python SDK Usage

```python
from app.config import settings
from app.services.semantic_policy_engine import SemanticPolicyEngine

# Initialize using the global config flag
engine = SemanticPolicyEngine(enabled=settings.ENABLE_LLM_VALIDATION)

# Check if available
if engine.is_available():
    # Validate a contract
    result = engine.validate_contract(contract_data)

    print(f"Status: {result.status}")
    print(f"Violations: {len(result.violations)}")

    for violation in result.violations:
        print(f"- {violation.policy}: {violation.message}")
```

### Integrated with Contract Service

Semantic scanning is automatically included when enabled via configuration:

```python
from app.config import settings
from app.services.contract_service import ContractService

# Create service using the global config flag
service = ContractService(enable_semantic=settings.ENABLE_LLM_VALIDATION)

# Validation now includes both rule-based + semantic
result = service.validate_contract_combined(contract_data)

# Results combine violations from both engines
print(f"Total passed: {result.passed}")
print(f"Total warnings: {result.warnings}")
print(f"Total failures: {result.failures}")
```

## 🔧 Configuration

### Global Toggle (Environment Variables / `.env`)

The following environment variables control LLM validation. Set them in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_LLM_VALIDATION` | `false` | Master switch — must be `true` to use any semantic features |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API server URL |
| `OLLAMA_MODEL` | `mistral:7b` | Model to use for semantic validation |
| `OLLAMA_TIMEOUT` | `30` | Request timeout in seconds |

### Policy-Level Configuration

Edit `/backend/policies/semantic_policies.yaml` to fine-tune policy behavior:

```yaml
semantic_config:
  provider: "ollama"  # or "openai", "huggingface"

  ollama:
    base_url: "http://localhost:11434"
    model: "mistral:7b"
    temperature: 0.1  # Low = consistent, High = creative
    timeout: 30

  execution:
    enable_caching: true  # Cache LLM responses
    cache_ttl: 3600       # 1 hour
    max_retries: 3
    parallel_execution: false
    confidence_threshold: 70  # Minimum confidence to report
```

## Performance Considerations

### Model Size vs Performance

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| **mistral:7b** | 4GB | Medium | High | **Recommended** - Best balance |
| **codellama:7b** | 7GB | Slow | Highest | Code-heavy schemas |
| **phi:latest** | 2.7GB | Fast | Good | Quick validation |
| **llama2:7b** | 4GB | Medium | High | General purpose |

### Execution Time

- **Rule-based policies**: <100ms per contract
- **Semantic policies**: 2-5 seconds per policy (with LLM)
- **Caching**: Repeat validations are instant (cached for 1 hour)

### Resource Usage

- **RAM**: 8GB minimum, 16GB recommended
- **GPU**: Optional (CPU works fine for 7B models)
- **Disk**: 4-7GB per model

## ✅ Best Practices

### When to Use Semantic Scanning

✅ **Use semantic scanning for:**
- Complex data contracts with ambiguous classifications
- Compliance-critical datasets (GDPR, HIPAA, etc.)
- Security-sensitive data (financial, health, PII)
- Cross-functional data governance reviews
- Onboarding new data sources

❌ **Skip semantic scanning for:**
- Simple, well-understood schemas
- Rapid development iterations
- Low-risk internal data
- Performance-critical validation paths

### Selective Policy Execution

Run only relevant policies to save time:

```python
# Only check for sensitive data patterns
result = engine.validate_contract(
    contract_data,
    selected_policies=["SEM001", "SEM003"]
)
```

### Caching Strategy

- Semantic validation results are cached for 1 hour
- Re-validation of the same contract is instant
- Clear cache when policies change:

```python
engine.llm_client.clear_cache()
```

## 🔧 Troubleshooting

### LLM Validation Disabled by Configuration

**Error**: "LLM validation is disabled by configuration"

**Solution**:
```bash
# Enable LLM validation in backend/.env
echo "ENABLE_LLM_VALIDATION=true" >> backend/.env

# Restart the backend
# The setting defaults to false — you must explicitly enable it
```

### Ollama Not Running

**Error**: "Semantic scanning is not available"

**Solution**:
```bash
# Make sure ENABLE_LLM_VALIDATION=true is set, then:

# Start Ollama
ollama serve

# Or on macOS/Linux with brew
brew services start ollama
```

### Model Not Found

**Error**: "model 'mistral:7b' not found"

**Solution**:
```bash
# Pull the model
ollama pull mistral:7b

# Verify it's available
ollama list
```

### Slow Performance

**Issue**: Semantic validation takes too long

**Solutions**:
1. Use smaller model: `ollama pull phi:latest`
2. Enable GPU acceleration (if available)
3. Run only specific policies: `selected_policies=["SEM001"]`
4. Ensure caching is enabled in config

### Out of Memory

**Issue**: System runs out of RAM

**Solutions**:
1. Use smaller model (phi:latest = 2.7GB)
2. Close other applications
3. Disable semantic scanning: `enable_semantic=False`
4. Use quantized models: `ollama pull mistral:7b-q4`

## Comparison: Rule-Based vs Semantic

| Aspect | Rule-Based | Semantic (LLM) |
|--------|------------|----------------|
| **Speed** | <100ms | 2-5s per policy |
| **Accuracy** | 100% (for defined rules) | 80-95% (context-dependent) |
| **Coverage** | Explicit patterns only | Context-aware |
| **Maintenance** | Manual rule updates | Self-improving |
| **Cost** | Zero | Local (free) or API (paid) |
| **Examples** | "field contains 'ssn'" | "field likely contains SSN" |

## Advanced: Using Remote LLMs

While local execution with Ollama is recommended, you can use cloud LLMs:

### OpenAI (GPT-3.5/4)

```yaml
semantic_config:
  provider: "openai"

  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-3.5-turbo"
    temperature: 0.1
```

### Hugging Face (Self-Hosted)

```yaml
semantic_config:
  provider: "huggingface"

  huggingface:
    model: "bigcode/starcoder"
    device: "cuda"  # or "cpu"
```

**Note**: Local execution with Ollama is recommended for:
- Privacy (data never leaves your infrastructure)
- Cost (no API fees)
- Speed (no network latency)
- Compliance (data governance systems often restrict external APIs)

## FAQs

**Q: Do I need a GPU?**
A: No, 7B models run fine on CPU. GPU makes it faster but isn't required.

**Q: Can I run this in production?**
A: Yes! Use local Ollama for privacy and compliance. Monitor performance and cache aggressively.

**Q: How accurate is semantic scanning?**
A: 80-95% accuracy depending on the model and policy. Always review findings, especially for critical decisions.

**Q: Can I add custom semantic policies?**
A: Yes! Edit `semantic_policies.yaml` and add your policy with a custom prompt template.

**Q: Does this replace rule-based policies?**
A: No, it complements them. Use both for comprehensive validation.

**Q: What about data privacy?**
A: With local Ollama, your data never leaves your infrastructure. This is a key advantage over cloud LLMs.

## 📚 Examples

### Example 1: Detecting Context-Sensitive PII

**Scenario**: Field named `user_details` (not obvious if it contains PII)

**Rule-Based Result**: ✅ PASSED (no PII keyword match)

**Semantic Result**: ⚠️ WARNING
```
Policy: SEM001 (Sensitive Data Context Detection)
Message: Field 'user_details' likely contains personal information (85% confidence)
Reasoning: Field name and description suggest personal data storage
Recommended Actions:
  - Mark field as PII
  - Enable encryption
  - Add compliance tags (GDPR, CCPA)
```

### Example 2: Business Logic Validation

**Scenario**: 99% completeness threshold for optional birthday field

**Rule-Based Result**: ✅ PASSED (threshold is set)

**Semantic Result**: ⚠️ WARNING
```
Policy: SEM005 (Data Quality Semantic Validation)
Message: Completeness threshold of 99% is unrealistic for optional field 'date_of_birth'
Reasoning: Optional fields typically have 60-80% completeness in customer databases
Suggested Value: 75%
```

### Example 3: Security Pattern Detection

**Scenario**: Schema has `username`, `password_hash`, and `security_question_answer` fields

**Rule-Based Result**: ✅ PASSED (individual fields are fine)

**Semantic Result**: ⚠️ CRITICAL
```
Policy: SEM003 (Security Pattern Detection)
Message: Security vulnerability detected - storing security answers is risky
Affected Fields: security_question_answer
Remediation:
  - Hash security question answers
  - Consider removing this authentication method
  - Implement MFA instead
```

## 🎯 Conclusion

Semantic scanning brings AI-powered intelligence to data governance, catching issues that rule-based systems miss. With local LLM execution via Ollama, you get:

- **Privacy**: Data never leaves your infrastructure
- **Cost**: No API fees
- **Intelligence**: Context-aware validation
- **Compliance**: Enhanced governance without external dependencies

Start with `mistral:7b`, enable caching, and run semantic validation on critical datasets to experience the power of AI-assisted data governance!

## ✅ Quick Start Checklist

- [ ] Enable LLM validation: `echo "ENABLE_LLM_VALIDATION=true" >> backend/.env`
- [ ] Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
- [ ] Start Ollama: `ollama serve`
- [ ] Pull model: `ollama pull mistral:7b`
- [ ] Restart the backend to pick up the new config
- [ ] Check health: `curl http://localhost:8000/api/v1/semantic/health`
- [ ] Run validation: `POST /api/v1/semantic/validate`
- [ ] Review results and iterate!

**Need help?** Open an issue on GitHub or check the troubleshooting section above.
