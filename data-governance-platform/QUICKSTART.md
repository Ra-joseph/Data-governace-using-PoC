# Quick Start Guide

Get the Data Governance Platform running in 6 easy steps.

## Table of Contents

- [Prerequisites Check](#prerequisites-check)
- [Step 1: Setup](#step-1-setup)
- [Step 2: Start PostgreSQL](#step-2-start-postgresql)
- [Step 3: Start Backend](#step-3-start-backend)
- [Step 4: Start Frontend](#step-4-start-frontend)
- [Step 5: Test](#step-5-test)
- [Step 6: Explore](#step-6-explore)
- [What's Next](#whats-next)
- [Troubleshooting](#troubleshooting)
- [Understanding the Demo](#understanding-the-demo)
- [Key Concepts](#key-concepts)
- [Common Use Cases](#common-use-cases)
- [Architecture Overview](#architecture-overview)
- [Ready for More](#ready-for-more)

## Prerequisites Check

Before starting, make sure you have:
- [ ] Python 3.10 or higher (`python3 --version`)
- [ ] Node.js 18 or higher (`node --version`)
- [ ] Docker installed and running (`docker --version`)
- [ ] Git installed (`git --version`)

> **macOS users**: Install everything at once with Homebrew:
> ```bash
> brew install python@3.12 node@20 git && brew install --cask docker
> ```
> Open Docker.app from Applications and wait for the whale icon to appear in the menu bar before proceeding.
> For full macOS setup instructions see [USAGE_GUIDE.md](./USAGE_GUIDE.md#macos-setup-homebrew).

## Step 1: Setup

Run these commands from the `data-governance-platform/` directory:

```bash
# Create the virtual environment (one-time setup)
python3 -m venv venv

# Activate it — required in every new terminal session
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows PowerShell

# Install all Python backend dependencies into the venv
pip install -r backend/requirements.txt
```

> The virtual environment (`venv/`) keeps all Python packages isolated from your system Python. Nothing is installed globally.

## Step 2: Start PostgreSQL

```bash
# Start the demo database
docker-compose up -d

# Verify it's running
docker ps | grep governance_postgres
```

You should see the container running on port 5432.

## Step 3: Start Backend

Open a **new terminal** in `data-governance-platform/`:

```bash
# Activate the virtual environment (required in each new terminal)
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows PowerShell

# Start the API server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will start at http://localhost:8000. Keep this terminal open — API logs appear here.

Alternatively, use the convenience script:

```bash
# From data-governance-platform/ with venv activated
chmod +x start.sh && ./start.sh
```

## Step 4: Start Frontend

Open a **new terminal** in `data-governance-platform/frontend/`:

```bash
cd frontend
npm install    # first-time only — installs all npm packages
npm run dev
```

The frontend will start at http://localhost:3000

## Step 5: Test

Open a **new terminal** and run:

```bash
# From data-governance-platform/ — activate the virtual environment
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows PowerShell

# Run the automated setup validation script
python test_setup.py
```

You should see 5 green checkmarks:
- ✓ Health Check
- ✓ PostgreSQL Connection
- ✓ Schema Import
- ✓ Dataset Registration
- ✓ List Datasets

## Step 6: Explore

### View API Documentation

Open in your browser:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### Explore the Frontend

Open http://localhost:3000 (auto-redirects to the role selector) and try each role:
- **Data Owner**: Register datasets, view violations
- **Data Consumer**: Browse catalog, request access
- **Data Steward**: Review and approve subscriptions
- **Platform Admin**: View compliance dashboard

### Try Some Commands

```bash
# List all tables in PostgreSQL
curl http://localhost:8000/api/v1/datasets/postgres/tables

# Import a schema
curl -X POST http://localhost:8000/api/v1/datasets/import-schema \
  -H "Content-Type: application/json" \
  -d '{"source_type": "postgres", "table_name": "transactions"}'

# List registered datasets
curl http://localhost:8000/api/v1/datasets/
```

### View Generated Contracts

```bash
# Contracts are stored in Git
ls -la backend/contracts/

# View a contract
cat backend/contracts/customer_accounts_v1.0.0.yaml
```

### Check Git History

```bash
cd backend/contracts
git log --oneline
git show HEAD
cd ../..
```

## What's Next?

1. **Read the README**: Full documentation in `README.md`
2. **Explore the Demo**: Check out the 3 demo tables with intentional violations
3. **Review Policies**: See YAML policy files in `backend/policies/`
4. **Try the API**: Use Swagger UI to test all endpoints
5. **Check Validation**: See how policy violations are caught and reported

## Troubleshooting

### PostgreSQL won't start?

```bash
# Check if port 5432 is in use
lsof -i :5432

# Stop and restart
docker-compose down
docker-compose up -d
```

### Backend won't start?

```bash
# Check Python version
python --version  # Must be 3.10+

# Reinstall dependencies
pip install -r backend/requirements.txt
```

### Tests fail?

```bash
# Make sure both services are running
docker ps  # PostgreSQL
curl http://localhost:8000/health  # Backend
```

## Understanding the Demo

### The Financial Scenario

The demo includes 3 tables with realistic financial data:

1. **customer_accounts** - Contains PII (email, SSN, phone)
   - **Intentional Violations**: Missing encryption, no compliance tags
   
2. **transactions** - Time-sensitive financial transactions
   - **Intentional Violations**: Missing freshness SLA, NULL status values
   
3. **fraud_alerts** - Critical fraud detection data
   - **Intentional Violations**: Missing quality thresholds, NULL risk scores

### What Gets Validated?

When you register `customer_accounts`, the platform checks:

✓ **Sensitive Data Policies**
- Are PII fields encrypted?
- Is retention period specified?
- Are compliance tags present?

✓ **Data Quality Policies**
- Is completeness threshold adequate?
- Is freshness SLA specified?
- Are uniqueness fields identified?

✓ **Schema Governance Policies**
- Are all fields documented?
- Are required fields consistent?
- Is ownership specified?

✓ **Semantic Policies** (with Ollama)
- Context-aware PII detection
- Business logic validation
- Security pattern recognition
- Compliance verification

### The Validation Report

You'll see output like:

```json
{
  "status": "failed",
  "passed": 8,
  "warnings": 3,
  "failures": 2,
  "violations": [
    {
      "type": "critical",
      "policy": "SD001: pii_encryption_required",
      "message": "PII fields require encryption...",
      "remediation": "Set encryption_required: true..."
    }
  ]
}
```

Each violation includes:
- **Type**: Critical, Warning, or Info
- **Policy**: Which policy was violated
- **Message**: What's wrong
- **Remediation**: How to fix it

## Key Concepts

### Federated Governance (UN Peacekeeping Model)

- **Shared Policies**: Central governance team defines policies
- **Distributed Enforcement**: Policies enforced at data source
- **Local Autonomy**: Teams own their data but follow standards
- **Prevention at Borders**: Catch violations early, not in production

### Policy-as-Code

All policies are defined in YAML files:
- Version controlled
- Testable
- Auditable
- Easy to update

### Dual Contracts

Each dataset gets two formats:
- **YAML**: Human-readable for documentation
- **JSON**: Machine-readable for automation

Both are version-controlled in Git!

## Common Use Cases

### As a Data Owner

```bash
# 1. Import your table schema
curl -X POST http://localhost:8000/api/v1/datasets/import-schema \
  -H "Content-Type: application/json" \
  -d '{"source_type": "postgres", "table_name": "your_table"}'

# 2. Review the suggested classification and PII detection

# 3. Register your dataset (fix any violations first!)
curl -X POST http://localhost:8000/api/v1/datasets/ \
  -H "Content-Type: application/json" \
  -d @your_dataset.json
```

### As a Data Consumer

```bash
# 1. Browse available datasets
curl http://localhost:8000/api/v1/datasets/

# 2. View a specific dataset
curl http://localhost:8000/api/v1/datasets/1

# 3. Request subscription
curl -X POST http://localhost:8000/api/v1/subscriptions/ \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "consumer_name": "Jane Smith", "consumer_email": "jane@company.com", "business_justification": "Analytics", "use_case": "reporting"}'
```

### As a Data Steward

```bash
# 1. Review all datasets
curl http://localhost:8000/api/v1/datasets/

# 2. Check validation status
# Look for datasets in "draft" status

# 3. Review contracts in Git
cd backend/contracts
git log --all --graph --oneline
```

## Architecture Overview

```
User Request
    ↓
FastAPI Endpoint (30+ endpoints)
    ↓
Service Layer
    ↓
Policy Orchestrator ← Chooses strategy
    ├── Rule Engine (17 policies)
    └── Semantic Engine (8 policies, via Ollama)
    ↓
Contract Service → Git Repo (contracts)
    ↓
Database (SQLite metadata)
    ↓
PostgreSQL Connector → Source Database
```

## Ready for More?

- **Full Documentation**: See `README.md` for complete details
- **API Docs**: http://localhost:8000/api/docs
- **Policy Files**: Explore `backend/policies/*.yaml`
- **Demo Data**: Check `demo/*.sql` files
- **Semantic Scanning**: See `SEMANTIC_SCANNING.md` for LLM setup
- **Policy Orchestration**: See `POLICY_ORCHESTRATION.md` for strategies

---

**Questions or Issues?**

Check the Troubleshooting section in README.md or review the test output for specific error messages.

Happy Data Governing!
