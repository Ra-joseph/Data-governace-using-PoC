# Quick Start Guide

Get the full Data Governance Platform (backend + frontend) running in minutes.

## Table of Contents

- [Prerequisites Check](#prerequisites-check)
- [Step 1: Setup Python Environment](#step-1-setup-python-environment)
- [Step 2: Start PostgreSQL](#step-2-start-postgresql)
- [Step 3: Start Backend API](#step-3-start-backend-api)
- [Step 4: Start Frontend](#step-4-start-frontend)
- [Step 5: Verify Setup](#step-5-verify-setup)
- [Step 6: Explore the Platform](#step-6-explore-the-platform)
- [Optional: Enable Semantic Scanning](#optional-enable-semantic-scanning)
- [Understanding the Demo](#understanding-the-demo)
- [Common Use Cases by Role](#common-use-cases-by-role)
- [Troubleshooting](#troubleshooting)
- [Architecture Overview](#architecture-overview)

## Prerequisites Check

Before starting, make sure you have:
- [ ] Python 3.10 or higher (`python --version`)
- [ ] Node.js 18 or higher (`node --version`)
- [ ] Docker installed and running (`docker --version`)
- [ ] Git installed (`git --version`)

## Step 1: Setup Python Environment

```bash
# From data-governance-platform/ directory
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

## Step 2: Start PostgreSQL

```bash
# Start the demo database (customer_accounts, transactions, fraud_alerts)
docker-compose up -d

# Verify it's running
docker ps | grep governance_postgres
```

You should see `governance_postgres` running on port 5432.

## Step 3: Start Backend API

```bash
# Option A: Use the start script
chmod +x start.sh
./start.sh

# Option B: Manual start
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API starts at **http://localhost:8000**. Keep this terminal open — you'll see API logs here.

## Step 4: Start Frontend

Open a **new terminal** and run:

```bash
# From data-governance-platform/ directory
cd frontend
npm install
npm run dev
```

The frontend starts at **http://localhost:5173**. Keep this terminal open.

## Step 5: Verify Setup

Open a **new terminal** and run:

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run automated setup tests
python test_setup.py
```

Expected output:
```
✓ Health Check
✓ PostgreSQL Connection
✓ Schema Import
✓ Dataset Registration
✓ List Datasets

🎉 All tests passed! Setup is complete.
```

## Step 6: Explore the Platform

### Using the Frontend (Recommended)

1. **Open** http://localhost:5173/select-role
2. **Select a role** to access its dedicated interface:

| Role | URL | What you can do |
|------|-----|-----------------|
| Data Owner | `/owner/dashboard` | Register datasets, view violations, track subscribers |
| Data Consumer | `/consumer/catalog` | Browse catalog, request dataset access with SLA |
| Data Steward | `/steward/approvals` | Review and approve subscription requests |
| Platform Admin | `/admin/dashboard` | View compliance metrics and violation analytics |

### Quick Walkthrough (End-to-End)

```
1. Data Owner → Register Dataset
   - Select "customer_accounts" from PostgreSQL import
   - Complete the 4-step wizard
   - View policy violations (SD001, SD003 will trigger)

2. Data Consumer → Request Access
   - Browse the catalog
   - Click "Request Access" on your dataset
   - Fill in business justification and SLA requirements

3. Data Steward → Approve Request
   - Go to /steward/approvals
   - Review the pending request
   - Approve with credentials

4. Platform Admin → View Metrics
   - Go to /admin/dashboard
   - See compliance rate, violation trends, top policies
```

### Using the API Directly

```bash
# View API documentation (Swagger UI)
open http://localhost:8000/api/docs

# List all tables in PostgreSQL
curl http://localhost:8000/api/v1/datasets/postgres/tables

# Import a schema with PII detection
curl -X POST http://localhost:8000/api/v1/datasets/import-schema \
  -H "Content-Type: application/json" \
  -d '{"source_type": "postgres", "table_name": "customer_accounts", "schema_name": "public"}'

# Register a dataset
curl -X POST http://localhost:8000/api/v1/datasets/ \
  -H "Content-Type: application/json" \
  -d @examples/register_customer_accounts.json

# List registered datasets
curl http://localhost:8000/api/v1/datasets/
```

### View Generated Contracts

```bash
# Contracts are stored in Git with semantic versioning
ls -la backend/contracts/

# View a contract
cat backend/contracts/customer_accounts_v1.0.0.yaml

# View Git history
cd backend/contracts && git log --oneline
```

## Optional: Enable Semantic Scanning

For AI-powered policy validation (requires 4-7 GB disk space):

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama
ollama serve

# Pull a model (in a new terminal)
ollama pull mistral:7b  # Recommended: ~4GB, good balance of speed/quality

# Verify semantic scanning is available
curl http://localhost:8000/api/v1/semantic/health
```

Expected response:
```json
{
  "available": true,
  "ollama_running": true,
  "available_models": ["mistral:7b"],
  "policies_loaded": 8
}
```

See [SEMANTIC_SCANNING.md](./SEMANTIC_SCANNING.md) for full setup and [POLICY_ORCHESTRATION.md](./POLICY_ORCHESTRATION.md) for intelligent routing.

## Understanding the Demo

### The Financial Services Scenario

The demo includes 3 tables with realistic financial data containing **intentional policy violations**:

| Table | Records | PII | Violations |
|-------|---------|-----|------------|
| `customer_accounts` | 10 | email, SSN, phone, DOB | Missing encryption, no compliance tags |
| `transactions` | 23 | None | Missing freshness SLA, NULL status values |
| `fraud_alerts` | 6 | None | Missing quality thresholds, NULL risk scores |

### What Gets Validated

When you register `customer_accounts`, the platform checks all applicable policies:

**Sensitive Data Policies (SD001-SD005)**
- Are PII fields documented as encrypted? → **SD001 Critical violation**
- Is retention period specified? → SD002 check
- Are compliance tags present (GDPR, CCPA)? → **SD003 Warning**

**Data Quality Policies (DQ001-DQ005)**
- Is completeness threshold adequate?
- Is freshness SLA specified?
- Are uniqueness constraints defined?

**Schema Governance Policies (SG001-SG007)**
- Are all fields documented?
- Are required fields non-nullable?
- Is ownership specified? → SG003 check

### Sample Validation Report

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
      "field": "customer_ssn, customer_email, customer_phone",
      "message": "PII fields require encryption but encryption_required is False",
      "remediation": "Set 'encryption_required: true' and add 'encryption_details' to your contract specifying algorithm (e.g., AES-256) and key management approach."
    },
    {
      "type": "warning",
      "policy": "SD003: pii_compliance_tags",
      "field": "governance.compliance_tags",
      "message": "Datasets with PII should specify compliance frameworks",
      "remediation": "Add compliance_tags: ['GDPR', 'CCPA'] to governance metadata."
    }
  ]
}
```

## Common Use Cases by Role

### As a Data Owner

```bash
# Import schema and see automatic PII detection
curl -X POST http://localhost:8000/api/v1/datasets/import-schema \
  -H "Content-Type: application/json" \
  -d '{"source_type": "postgres", "table_name": "customer_accounts"}'

# Register dataset (review validation report for violations)
curl -X POST http://localhost:8000/api/v1/datasets/ \
  -H "Content-Type: application/json" \
  -d @examples/register_customer_accounts.json
```

### As a Data Consumer

```bash
# Browse available published datasets
curl "http://localhost:8000/api/v1/datasets/?status=published"

# View dataset details and schema
curl http://localhost:8000/api/v1/datasets/1

# Create subscription request
curl -X POST http://localhost:8000/api/v1/subscriptions/ \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "consumer_name": "Analytics Team",
    "consumer_email": "analytics@company.com",
    "business_justification": "Customer segmentation analysis",
    "use_case": "analytics",
    "sla_requirements": {"max_latency_ms": 500, "min_availability_percent": 99}
  }'
```

### As a Data Steward

```bash
# Review pending subscriptions
curl "http://localhost:8000/api/v1/subscriptions/?status=pending"

# Approve a subscription (generates credentials + new contract version)
curl -X POST http://localhost:8000/api/v1/subscriptions/1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "approved_fields": ["account_id", "customer_name", "customer_email"],
    "access_credentials": {
      "username": "analytics_user",
      "api_key": "key_abc123"
    },
    "notes": "Approved for analytics use case"
  }'

# View Git history of contracts
curl http://localhost:8000/api/v1/git/commits
```

## Troubleshooting

### PostgreSQL won't start

```bash
# Check if port 5432 is in use
lsof -i :5432

# Stop and restart with fresh volumes
docker-compose down -v
docker-compose up -d
```

### Backend won't start

```bash
# Check Python version (must be 3.10+)
python --version

# Reinstall dependencies
pip install -r backend/requirements.txt --upgrade

# Check for port conflicts
lsof -i :8000
```

### Frontend won't start

```bash
# Check Node.js version (must be 18+)
node --version

# Clear and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Frontend can't connect to backend

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check browser console (F12 → Console) for CORS or connection errors
# Verify Vite proxy in frontend/vite.config.js targets http://localhost:8000
```

### Tests fail

```bash
# Ensure both services are running
docker ps          # PostgreSQL should be listed
curl http://localhost:8000/health  # Should return {"status": "healthy"}

# Run tests with verbose output
python test_setup.py
```

## Architecture Overview

```
User Browser
    ↓
React Frontend (http://localhost:5173)
    ↓  Axios HTTP / Vite proxy
FastAPI Backend (http://localhost:8000)
    ↓
Policy Orchestrator
    ├── Rule Engine (17 YAML policies)  ←── backend/policies/*.yaml
    └── Semantic Engine (8 LLM policies) ←── Ollama (optional)
    ↓
Contract Service → Git Repository (backend/contracts/)
    ↓
SQLite Metadata DB ←── Dataset, Contract, Subscription, User records
    ↓
PostgreSQL Connector → Demo Database (Docker port 5432)
```

## Ready for More?

- **Full Documentation**: See [README.md](./README.md) for complete details
- **API Docs**: http://localhost:8000/api/docs (Swagger UI)
- **Policy Files**: Explore `backend/policies/*.yaml`
- **Semantic Scanning**: See [SEMANTIC_SCANNING.md](./SEMANTIC_SCANNING.md)
- **Policy Orchestration**: See [POLICY_ORCHESTRATION.md](./POLICY_ORCHESTRATION.md)
- **Deployment**: See [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**Questions or Issues?** Check the Troubleshooting section above or open an issue on GitHub.
