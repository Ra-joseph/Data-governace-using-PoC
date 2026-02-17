# Contributing to Data Governance Platform

Thank you for your interest in contributing to the Data Governance Platform! This document provides guidelines for code contributions, documentation standards, and development practices.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Documentation Standards](#documentation-standards)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker
- Git

### Setting Up Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd Data-governace-using-PoC

# Start PostgreSQL
cd data-governance-platform
docker-compose up -d

# Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Setup frontend
cd ../frontend
npm install

# Run tests to verify setup
cd ../backend
pytest tests/ -v
```

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Development branch
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `docs/*` - Documentation updates

### Creating a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

## Code Standards

### Python Code Standards

#### Style Guide

We follow [PEP 8](https://pep8.org/) with the following tools:

- **Black** - Code formatting (line length: 100)
- **isort** - Import sorting
- **flake8** - Linting
- **mypy** - Type checking
- **pydocstyle** - Docstring validation

#### Running Code Quality Tools

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type check
mypy app/

# Check docstrings
pydocstyle app/
```

#### Type Hints

All functions should include type hints:

```python
from typing import Dict, List, Optional

def process_dataset(
    dataset_id: int,
    options: Optional[Dict[str, any]] = None
) -> Dict[str, any]:
    """Process a dataset with optional configuration."""
    pass
```

### JavaScript/React Code Standards

#### Style Guide

- **ESLint** - Linting
- **Prettier** - Code formatting
- **React best practices**

#### Running Code Quality Tools

```bash
cd frontend

# Lint code
npm run lint

# Format code
npm run format

# Type check (if using TypeScript)
npm run type-check
```

## Documentation Standards

### Python Documentation

#### Module-Level Docstrings

Every Python module must start with a docstring describing its purpose:

```python
"""
Module for contract service operations.

This module provides the ContractService class which handles data contract
creation, validation, versioning, and Git operations. It integrates with the
PolicyEngine for validation and GitService for version control.
"""

import yaml
from typing import Dict, List
# ... rest of imports
```

#### Class Docstrings

Use Google-style docstrings for classes:

```python
class ContractService:
    """
    Service for managing data contract lifecycle.

    This service handles contract creation from datasets, validation against
    governance policies, versioning using semantic versioning, and Git-based
    version control for full audit trails.

    Attributes:
        policy_engine: PolicyEngine instance for validation
        git_service: GitService instance for version control
        contracts_dir: Path to contracts directory

    Example:
        >>> service = ContractService()
        >>> contract = service.create_contract_from_dataset(db, dataset_id)
    """

    def __init__(self, contracts_dir: str = None):
        """
        Initialize ContractService.

        Args:
            contracts_dir: Optional custom path to contracts directory.
                          Defaults to settings.CONTRACTS_PATH.
        """
        pass
```

#### Function/Method Docstrings

Use Google-style docstrings with Args, Returns, Raises sections:

```python
def validate_contract(
    self,
    contract_data: Dict[str, any],
    selected_policies: Optional[List[str]] = None
) -> ValidationResult:
    """
    Validate a contract against governance policies.

    Runs validation against all loaded policies unless specific policies
    are selected. Combines rule-based and semantic validation when enabled.

    Args:
        contract_data: Contract data in dictionary format with dataset,
                      schema, and governance sections.
        selected_policies: Optional list of policy IDs to validate against.
                          If None, validates against all policies.

    Returns:
        ValidationResult containing status, violation counts, and detailed
        violation information with remediation guidance.

    Raises:
        ValueError: If contract_data is missing required sections.
        ValidationError: If contract structure is invalid.

    Example:
        >>> result = engine.validate_contract(contract_data)
        >>> if result.status == ValidationStatus.FAILED:
        ...     for violation in result.violations:
        ...         print(f"{violation.policy}: {violation.message}")
    """
    pass
```

#### Private Method Docstrings

Private methods should have concise docstrings:

```python
def _parse_llm_response(self, response: str) -> Dict[str, any]:
    """
    Parse and validate LLM response into structured format.

    Args:
        response: Raw response text from LLM.

    Returns:
        Parsed response with confidence, message, and reasoning fields.
    """
    pass
```

#### Inline Comments

Use inline comments sparingly, only for complex logic:

```python
# Check if dataset has temporal fields for freshness validation
has_temporal_fields = any(
    field.get('type') in ['date', 'timestamp', 'datetime']
    for field in schema
)
```

### Markdown Documentation

#### File Naming

- Use UPPERCASE for major documentation: `README.md`, `CONTRIBUTING.md`
- Use descriptive names: `SEMANTIC_SCANNING.md`, `DEPLOYMENT.md`
- Use underscores for multi-word names: `FULL_STACK_INVENTORY.md`

#### Document Structure

All major markdown files should follow this structure:

```markdown
# Document Title

Brief one-sentence description.

## Table of Contents

- [Section 1](#section-1)
- [Section 2](#section-2)

## Overview

Detailed introduction and context.

## Main Sections

### Subsection

Content here.

## Troubleshooting

Common issues and solutions.

## References

Links to related documentation.
```

#### Emoji Usage Guidelines

Use emojis consistently for section types:

| Emoji | Usage |
|-------|-------|
| 🎯 | Goals, objectives, overview |
| ✨ | Features, highlights, what's new |
| 🚀 | Quick start, deployment, getting started |
| 📚 | Documentation, learning resources |
| 📊 | Metrics, analytics, dashboards |
| 🔧 | Configuration, troubleshooting |
| ⚠️ | Warnings, important notes |
| ✅ | Completed items, checklists |
| 🔜 | Roadmap, future plans |
| 📦 | Dependencies, prerequisites |
| 🔒 | Security, authentication |
| 🧪 | Testing, experiments |

Example:
```markdown
## 🎯 Overview

## ✨ Key Features

## 🚀 Quick Start

## 📚 Documentation

## 🔧 Troubleshooting
```

#### Code Examples

Always specify language for syntax highlighting:

````markdown
```python
# Python code example
def hello_world():
    print("Hello, World!")
```

```bash
# Shell commands
npm install
npm run dev
```

```json
{
  "key": "value"
}
```
````

Show expected output when helpful:

````markdown
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Data Governance Platform"
}
```
````

#### Tables

Use tables for structured information:

```markdown
| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |
```

#### Links

Use descriptive link text:

```markdown
Good: See the [API documentation](./API.md) for endpoint details.
Bad: Click [here](./API.md) for API docs.
```

#### Admonitions

Use blockquotes for important notes:

```markdown
> **Important:** Always backup your data before running migrations.

> **Note:** This feature requires Ollama to be running locally.

> **Warning:** This operation cannot be undone.
```

### API Documentation

#### Endpoint Documentation

Document API endpoints with:

- HTTP method
- URL path
- Description
- Request parameters/body
- Response format
- Example request/response
- Possible errors

Example:

````markdown
### Create Dataset

```
POST /api/v1/datasets/
```

Create a new dataset with governance metadata.

**Request Body:**
```json
{
  "name": "customer_accounts",
  "description": "Customer account information",
  "owner_name": "John Doe",
  "owner_email": "john.doe@company.com"
}
```

**Response:** 200 OK
```json
{
  "id": 1,
  "name": "customer_accounts",
  "status": "draft"
}
```

**Errors:**
- `400 Bad Request` - Invalid request data
- `409 Conflict` - Dataset name already exists
````

## Testing Requirements

### Test Coverage

- Minimum 80% code coverage for new code
- All new features must include tests
- Bug fixes must include regression tests

### Writing Tests

#### Python Tests

```python
import pytest
from app.services.policy_engine import PolicyEngine


class TestPolicyEngine:
    """Test cases for PolicyEngine validation."""

    def test_pii_encryption_validation(self, sample_contract):
        """Test that PII fields require encryption."""
        engine = PolicyEngine()
        result = engine.validate_contract(sample_contract)

        assert result.status == ValidationStatus.FAILED
        assert any("SD001" in v.policy for v in result.violations)
```

#### JavaScript/React Tests

```javascript
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DataCatalogBrowser from './DataCatalogBrowser'

describe('DataCatalogBrowser', () => {
  it('should render dataset list', () => {
    render(<DataCatalogBrowser />)
    expect(screen.getByText('Data Catalog')).toBeInTheDocument()
  })
})
```

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test
npm run test:coverage
```

## Pull Request Process

### Before Submitting

1. Run all tests and ensure they pass
2. Run code quality tools (black, flake8, eslint)
3. Update documentation for any changed functionality
4. Add/update tests for new features
5. Update CHANGELOG.md (if exists)

### PR Title Format

Use conventional commits format:

```
feat: Add semantic policy validation
fix: Correct PostgreSQL connection handling
docs: Update API documentation
test: Add tests for contract service
refactor: Simplify policy engine logic
```

### PR Description Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?

Describe testing performed.

## Checklist

- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] No new warnings generated
```

### Review Process

1. All PRs require at least one approval
2. CI/CD checks must pass
3. Code coverage must not decrease
4. Documentation must be updated

## Git Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting)
- `refactor` - Code refactoring
- `test` - Test changes
- `chore` - Build/tooling changes

**Example:**

```
feat(api): Add subscription approval endpoint

Add POST /api/v1/subscriptions/{id}/approve endpoint for data stewards
to approve or reject subscription requests with credentials.

- Generates access credentials on approval
- Updates contract version automatically
- Commits new contract to Git

Closes #123
```

## Code Review Guidelines

### For Authors

- Keep PRs small and focused
- Provide context in PR description
- Respond to feedback promptly
- Be open to suggestions

### For Reviewers

- Be constructive and respectful
- Focus on code quality and maintainability
- Check for test coverage
- Verify documentation is updated
- Test locally when possible

## Questions?

If you have questions or need help:

1. Check existing documentation
2. Search existing issues
3. Open a new issue with your question
4. Tag maintainers if urgent

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to the Data Governance Platform!
