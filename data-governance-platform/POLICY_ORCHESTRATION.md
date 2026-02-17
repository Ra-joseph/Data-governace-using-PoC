# Policy Orchestration Engine

## Overview

The **Policy Orchestration Engine** is an intelligent layer that automatically decides which validation engines to use (rule-based, LLM-based, or both) based on contract characteristics, risk level, and your chosen strategy.

### The Problem

You have two validation engines:
- **Rule-Based**: Fast (< 100ms), deterministic, covers explicit patterns
- **Semantic (LLM)**: Slow (2-30s), context-aware, catches nuanced issues

**Question**: When should you use which?

Running both every time is wasteful. Running only one might miss critical issues. **The orchestrator solves this by making intelligent decisions automatically.**

## How It Works

```
                    Contract Submitted
                            │
                            ▼
                ┌───────────────────────┐
                │  Policy Orchestrator  │
                └───────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        Analyze Contract        Choose Strategy
        ├─ Risk Level          ├─ FAST
        ├─ Complexity          ├─ BALANCED
        ├─ PII Detection       ├─ THOROUGH
        ├─ Compliance Needs    └─ ADAPTIVE
        └─ Field Count
                            │
                            ▼
                ┌───────────────────────┐
                │  Orchestration        │
                │  Decision             │
                │  ├─ Use rule-based?   │
                │  ├─ Use semantic?     │
                │  └─ Which policies?   │
                └───────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
        ┌──────────────┐        ┌──────────────┐
        │ Rule Engine  │        │ Semantic LLM │
        │  (17 policies)│        │ (8 policies) │
        └──────────────┘        └──────────────┘
                │                       │
                └───────────┬───────────┘
                            ▼
                ┌───────────────────────┐
                │  Combined Results     │
                │  ├─ Prioritized       │
                │  ├─ Deduplicated      │
                │  └─ Risk-weighted     │
                └───────────────────────┘
```

## Validation Strategies

### 1. FAST Strategy
**Speed**: ⚡ Very fast (~100ms)
**Coverage**: ✓ Basic (rule-based only)
**Use When**: Development, low-risk data, quick iterations

```python
result = orchestrator.validate_contract(
    contract_data,
    strategy=ValidationStrategy.FAST
)
```

**What It Does**:
- ✓ Runs 17 rule-based policies
- ✗ Skips semantic/LLM analysis
- Best for: Simple schemas, internal data, dev environments

**Example Output**:
```json
{
  "strategy": "FAST",
  "engines_used": ["rule-based"],
  "time": "0.08s",
  "violations": 3
}
```

---

### 2. BALANCED Strategy (Recommended)
**Speed**: ⚖️ Moderate (2-10s)
**Coverage**: ✓✓ Good (rules + targeted semantic)
**Use When**: Most production use cases

```python
result = orchestrator.validate_contract(
    contract_data,
    strategy=ValidationStrategy.BALANCED
)
```

**What It Does**:
- ✓ Runs all 17 rule-based policies
- ✓ Selects relevant semantic policies based on contract analysis
- Typically runs 2-4 semantic policies (not all 8)

**Policy Selection Logic**:
| If Contract Has... | Runs Semantic Policies |
|--------------------|------------------------|
| PII or sensitive data | SEM001 (Sensitive Data Detection) |
| Compliance requirements | SEM004 (Compliance Verification) |
| High complexity (score ≥ 50) | SEM002 (Business Logic) |
| Sensitive data | SEM003 (Security Patterns) |

**Example Output**:
```json
{
  "strategy": "BALANCED",
  "engines_used": ["rule-based", "semantic"],
  "semantic_policies": ["SEM001", "SEM003", "SEM004"],
  "time": "8.5s",
  "violations": 5
}
```

---

### 3. THOROUGH Strategy
**Speed**: 🐢 Slow (20-30s)
**Coverage**: ✓✓✓ Comprehensive (all policies)
**Use When**: Critical data, compliance audits, production releases

```python
result = orchestrator.validate_contract(
    contract_data,
    strategy=ValidationStrategy.THOROUGH
)
```

**What It Does**:
- ✓ Runs all 17 rule-based policies
- ✓ Runs all 8 semantic policies
- ✓ Full LLM analysis on every aspect

**Example Output**:
```json
{
  "strategy": "THOROUGH",
  "engines_used": ["rule-based", "semantic"],
  "semantic_policies": "all",
  "time": "24.3s",
  "violations": 7
}
```

---

### 4. ADAPTIVE Strategy (Smart Default)
**Speed**: 🔄 Variable (adjusts to risk)
**Coverage**: 🧠 Risk-appropriate
**Use When**: Unknown risk level, automated workflows

```python
result = orchestrator.validate_contract(
    contract_data,
    strategy=ValidationStrategy.ADAPTIVE
)
```

**How It Decides**:

| Risk Level | Complexity | → Strategy Chosen |
|------------|------------|------------------|
| Critical/High | Any | THOROUGH (all policies) |
| Low | Low (<30) | FAST (rule-based only) |
| Medium | Medium | BALANCED (targeted) |

**Example Decision Tree**:
```
Contract Analysis:
  PII: Yes (5 fields)
  Classification: Confidential
  Compliance: GDPR, CCPA
  Fields: 15
  Complexity Score: 75

Risk Assessment: HIGH
↓
Strategy Selected: THOROUGH
  - Run all rule-based policies
  - Run all semantic policies
  - Estimated time: 24s
```

## Risk Assessment

The orchestrator analyzes contracts to determine risk level:

### Risk Calculation

```python
CRITICAL if:
  - classification == "restricted" OR
  - 3+ compliance frameworks

HIGH if:
  - classification == "confidential" AND (has_pii OR compliance_tags) OR
  - 2+ compliance frameworks OR
  - complexity_score >= 70

MEDIUM if:
  - has_pii OR
  - compliance_tags OR
  - classification == "confidential" OR
  - field_count > 15 OR
  - complexity_score >= 40

LOW otherwise
```

### Complexity Score (0-100)

| Component | Max Points | How It's Calculated |
|-----------|------------|---------------------|
| Field Count | 30 | `min(30, fields * 1.5)` |
| PII Fields | 20 | `min(20, pii_count * 5)` |
| Compliance | 20 | `min(20, compliance_count * 10)` |
| Quality Rules | 15 | `min(15, rule_count * 3)` |
| Classification | 15 | public=0, internal=5, confidential=10, restricted=15 |

**Example**:
```
Schema: 20 fields, 4 PII
Compliance: GDPR, CCPA (2 frameworks)
Classification: Confidential
Quality Rules: 3 defined

Complexity Score:
  Field Count: 20 * 1.5 = 30 → 30 points
  PII: 4 * 5 = 20 → 20 points
  Compliance: 2 * 10 = 20 → 20 points
  Quality: 3 * 3 = 9 → 9 points
  Classification: confidential → 10 points

Total: 89/100 → HIGH complexity
```

## API Usage

### 1. Analyze a Contract

Get risk assessment and recommended strategy:

```bash
POST /api/v1/orchestration/analyze
{
  "contract_id": 1
}
```

**Response**:
```json
{
  "contract_id": 1,
  "contract_name": "customer_data",
  "risk_level": "high",
  "complexity_score": 75,
  "has_pii": true,
  "has_sensitive_data": true,
  "classification": "confidential",
  "requires_compliance": true,
  "compliance_frameworks": ["GDPR", "CCPA"],
  "field_count": 15,
  "concerns": [
    "Contains PII",
    "High classification: confidential",
    "Compliance requirements: GDPR, CCPA"
  ],
  "recommended_strategy": "thorough",
  "reasoning": "Adaptive: High risk (high) → thorough validation"
}
```

### 2. Validate with Strategy

Run validation with a specific strategy:

```bash
POST /api/v1/orchestration/validate
{
  "contract_id": 1,
  "strategy": "balanced"
}
```

**Response**:
```json
{
  "status": "warning",
  "passed": 20,
  "warnings": 3,
  "failures": 1,
  "violations": [...],
  "metadata": {
    "strategy": "balanced",
    "risk_level": "high",
    "complexity_score": 75,
    "orchestration_reasoning": "Balanced strategy: rule-based + 4 semantic policies",
    "estimated_time": 12.5
  }
}
```

### 3. Get Strategy Recommendation

```bash
POST /api/v1/orchestration/recommend-strategy
{
  "contract_id": 1
}
```

**Response**:
```json
{
  "contract_id": 1,
  "recommended_strategy": "balanced",
  "reasoning": "Medium risk with PII and compliance requirements",
  "estimated_time_seconds": 9.0,
  "will_use_rule_based": true,
  "will_use_semantic": true,
  "semantic_policies_count": 4
}
```

### 4. List Available Strategies

```bash
GET /api/v1/orchestration/strategies
```

**Response**:
```json
{
  "strategies": [
    {
      "name": "FAST",
      "description": "Rule-based validation only",
      "use_when": "Low-risk data, simple schemas, development environments",
      "speed": "Very fast (<100ms)",
      "coverage": "Basic (rule-based policies only)"
    },
    ...
  ],
  "default": "ADAPTIVE",
  "recommendation": "Use ADAPTIVE for automatic intelligence"
}
```

### 5. Get Orchestration Stats

```bash
GET /api/v1/orchestration/stats
```

**Response**:
```json
{
  "engines": {
    "rule_based": {
      "available": true,
      "policies": 17,
      "avg_time_ms": 50
    },
    "semantic": {
      "available": true,
      "policies": 8,
      "avg_time_ms": 3000
    }
  },
  "strategies": {
    "fast": { "avg_time_seconds": 0.05 },
    "balanced": { "avg_time_seconds": 9.0 },
    "thorough": { "avg_time_seconds": 24.0 }
  },
  "total_policies": 25
}
```

## Python SDK

### Basic Usage

```python
from app.services.policy_orchestrator import PolicyOrchestrator, ValidationStrategy

# Initialize orchestrator
orchestrator = PolicyOrchestrator(enable_semantic=True)

# Validate with adaptive strategy (recommended)
result = orchestrator.validate_contract(contract_data)

# Or specify strategy explicitly
result = orchestrator.validate_contract(
    contract_data,
    strategy=ValidationStrategy.BALANCED
)

print(f"Status: {result.status}")
print(f"Violations: {len(result.violations)}")
print(f"Strategy used: {result.metadata['strategy']}")
print(f"Risk level: {result.metadata['risk_level']}")
```

### Get Recommendation

```python
# Analyze and get recommendation
strategy, reasoning = orchestrator.get_recommended_strategy(contract_data)

print(f"Recommended: {strategy.value}")
print(f"Because: {reasoning}")
```

### Custom Orchestration

```python
# Analyze contract manually
analysis = orchestrator._analyze_contract(contract_data)

print(f"Risk: {analysis.risk_level.value}")
print(f"Complexity: {analysis.complexity_score}/100")
print(f"PII: {analysis.has_pii}")
print(f"Concerns: {analysis.concerns}")

# Make custom decision
if analysis.risk_level == RiskLevel.CRITICAL:
    strategy = ValidationStrategy.THOROUGH
elif analysis.complexity_score > 60:
    strategy = ValidationStrategy.BALANCED
else:
    strategy = ValidationStrategy.FAST

result = orchestrator.validate_contract(contract_data, strategy=strategy)
```

## Best Practices

### 1. Choose the Right Default Strategy

**Development**: Use `FAST`
```python
orchestrator = PolicyOrchestrator(
    enable_semantic=False,
    default_strategy=ValidationStrategy.FAST
)
```

**Production**: Use `ADAPTIVE` (recommended)
```python
orchestrator = PolicyOrchestrator(
    enable_semantic=True,
    default_strategy=ValidationStrategy.ADAPTIVE
)
```

**Compliance/Audit**: Use `THOROUGH`
```python
orchestrator = PolicyOrchestrator(
    enable_semantic=True,
    default_strategy=ValidationStrategy.THOROUGH
)
```

### 2. Trust the Adaptive Strategy

The `ADAPTIVE` strategy is designed to make intelligent decisions. It:
- ✓ Analyzes risk automatically
- ✓ Selects appropriate validation depth
- ✓ Balances thoroughness and performance
- ✓ Adjusts to contract characteristics

**When to override**:
- You know the data is critical → use `THOROUGH`
- You're in development → use `FAST`
- You want predictable performance → use `BALANCED`

### 3. Monitor Performance

```python
import time

start = time.time()
result = orchestrator.validate_contract(contract_data)
elapsed = time.time() - start

print(f"Strategy: {result.metadata['strategy']}")
print(f"Estimated: {result.metadata['estimated_time']}s")
print(f"Actual: {elapsed:.2f}s")
```

### 4. Use Analysis to Understand Decisions

```python
analysis = orchestrator._analyze_contract(contract_data)

# Log for auditing
logger.info(f"Contract: {contract_data['dataset']['name']}")
logger.info(f"Risk: {analysis.risk_level.value}")
logger.info(f"Complexity: {analysis.complexity_score}")
logger.info(f"Concerns: {', '.join(analysis.concerns)}")

# Make informed decisions
if analysis.risk_level >= RiskLevel.HIGH:
    # Notify compliance team
    send_notification(f"High-risk contract detected: {analysis.concerns}")
```

## Performance Comparison

| Strategy | Avg Time | Policies Run | When to Use |
|----------|----------|--------------|-------------|
| **FAST** | 0.05s | 17 (rule-based) | Dev, low-risk, quick checks |
| **BALANCED** | 9.0s | 17 + 2-4 semantic | Most production cases |
| **THOROUGH** | 24.0s | 17 + 8 semantic | Critical data, audits |
| **ADAPTIVE** | 0.05-24s | Variable | Unknown risk, automation |

**Real-World Example**:

100 contracts validated per day:

| Strategy | Time/Day | Cost (API)* | Coverage |
|----------|----------|-------------|----------|
| FAST | 5 seconds | $0 | Basic |
| BALANCED | 15 minutes | $0 (local) | Good |
| THOROUGH | 40 minutes | $0 (local) | Complete |
| ADAPTIVE | 10 minutes | $0 (local) | Optimal |

*Using local Ollama (free). Cloud LLM would add costs.

## Advanced: Custom Orchestration Logic

You can extend the orchestrator with custom logic:

```python
class CustomOrchestrator(PolicyOrchestrator):
    """Custom orchestrator with organization-specific rules."""

    def _assess_risk_level(self, has_pii, classification, compliance_tags,
                          field_count, complexity_score):
        """Override risk assessment with custom logic."""

        # Your organization's rules
        if 'PCI-DSS' in compliance_tags:
            return RiskLevel.CRITICAL  # Always critical for payment data

        if has_pii and field_count > 50:
            return RiskLevel.HIGH  # Large PII datasets are high risk

        # Fall back to default logic
        return super()._assess_risk_level(
            has_pii, classification, compliance_tags,
            field_count, complexity_score
        )
```

## Troubleshooting

### Orchestrator Always Uses FAST Strategy

**Cause**: Semantic engine not available

**Solution**:
```bash
# Check Ollama status
curl http://localhost:8000/api/v1/semantic/health

# Start Ollama if needed
ollama serve

# Pull model if needed
ollama pull mistral:7b
```

### Validation Too Slow

**Cause**: Using THOROUGH or ADAPTIVE with high-risk contracts

**Solutions**:
1. Use `BALANCED` for predictable performance
2. Use smaller LLM model (phi:latest instead of mistral:7b)
3. Disable semantic for non-critical workflows
4. Cache validation results

### Unexpected Strategy Selection

**Cause**: Risk assessment not matching expectations

**Solution**: Analyze the contract manually
```python
analysis = orchestrator._analyze_contract(contract_data)
print(f"Risk: {analysis.risk_level}")
print(f"Complexity: {analysis.complexity_score}")
print(f"Concerns: {analysis.concerns}")

# See what strategy would be chosen
strategy, reasoning = orchestrator.get_recommended_strategy(contract_data)
print(f"Strategy: {strategy}, Reason: {reasoning}")
```

## Summary

The Policy Orchestration Engine brings **intelligence** to data governance:

✅ **Automatic decision-making** - Analyzes contracts and chooses optimal validation
✅ **Risk-aware** - Adjusts validation depth based on data sensitivity
✅ **Performance optimized** - Avoids expensive LLM calls when not needed
✅ **Flexible strategies** - From fast (100ms) to thorough (24s)
✅ **Production-ready** - Used in contract creation, updates, and audits

**Start with ADAPTIVE strategy** - it makes smart decisions automatically, balancing thoroughness and performance based on your data's actual risk level.

---

## Quick Reference

```python
# Most common usage
orchestrator = PolicyOrchestrator(enable_semantic=True)
result = orchestrator.validate_contract(contract_data)  # Uses ADAPTIVE by default

# Explicit strategies
result = orchestrator.validate_contract(contract_data, strategy=ValidationStrategy.FAST)
result = orchestrator.validate_contract(contract_data, strategy=ValidationStrategy.BALANCED)
result = orchestrator.validate_contract(contract_data, strategy=ValidationStrategy.THOROUGH)

# Get recommendation
strategy, reasoning = orchestrator.get_recommended_strategy(contract_data)

# Analyze contract
analysis = orchestrator._analyze_contract(contract_data)
```

**Need help?** Check `/api/v1/orchestration/strategies` for strategy details or `/api/v1/orchestration/stats` for system status.
