# Data Governance Platform

A comprehensive Policy-as-Code data governance platform implementing federated governance using the UN Peacekeeping model. This platform enables automated schema import, data contract management, policy validation, and subscription workflows.

## 🎯 Key Features

- **Federated Governance**: UN Peacekeeping model - shared policies with distributed enforcement
- **Policy-as-Code**: YAML-defined policies with automated validation
- **Automated Schema Import**: Import from PostgreSQL, files, and Azure (extensible)
- **Dual Contracts**: Human-readable (YAML) + Machine-readable (JSON)
- **Git Version Control**: All contracts tracked with full history
- **Prevention at Borders**: Catch violations before publication, not after cascade
- **Actionable Remediation**: Every violation includes "how to fix it" guidance

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Demo Scenario](#demo-scenario)
- [Policy Definitions](#policy-definitions)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Governance Platform                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Dataset    │  │   Contract   │  │ Subscription │      │
│  │   Registry   │◄─┤  Management  │◄─┤   Workflow   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                                 │
│         │                  │                                 │
│  ┌──────▼──────────────────▼───────────────────────────┐    │
│  │            Policy Engine (YAML Policies)            │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ • Sensitive Data Policies                           │    │
│  │ • Data Quality Policies                             │    │
│  │ • Schema Governance Policies                        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │              Git Repository (Contracts)            │      │
│  │  • Version Control  • Audit Trail  • Diff/Compare │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                      Data Sources                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │PostgreSQL│  │  Files   │  │Azure Blob│  │ Azure DL │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

1. **Dataset Registry**: Catalog of all data assets with metadata
2. **Contract Management**: Version-controlled data contracts (YAML + JSON)
3. **Policy Engine**: Validates contracts against governance policies
4. **PostgreSQL Connector**: Imports schemas with PII detection
5. **Git Service**: Version control and audit trail for contracts
6. **Subscription Workflow**: Consumer access requests with SLA negotiation (Phase 2)

## 📦 Prerequisites

- **Python**: 3.10 or higher
- **Docker**: For PostgreSQL demo database
- **Git**: For contract version control

## 🚀 Installation

### Step 1: Clone or Download (2 minutes)

If you received this as a zip file, extract it. Otherwise:

```bash
git clone <repository-url>
cd data-governance-platform
```

### Step 2: Setup Python Environment (2 minutes)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### Step 3: Start PostgreSQL Demo Database (1 minute)

```bash
# Start PostgreSQL with demo data
docker-compose up -d

# Verify PostgreSQL is running
docker ps

# You should see: governance_postgres container running on port 5432
```

### Step 4: Start Backend API (1 minute)

```bash
# Option 1: Using the start script
chmod +x start.sh
./start.sh

# Option 2: Manual start
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

### Step 5: Verify Installation (1 minute)

```bash
# In a new terminal, run the test suite
python test_setup.py
```

You should see:
- ✓ Health Check
- ✓ PostgreSQL Connection
- ✓ Schema Import
- ✓ Dataset Registration
- ✓ List Datasets

## 🎬 Quick Start

### Import Schema from PostgreSQL

```bash
curl -X POST http://localhost:8000/api/v1/datasets/import-schema \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "postgres",
    "table_name": "customer_accounts",
    "schema_name": "public"
  }'
```

**Expected Response:**
```json
{
  "table_name": "customer_accounts",
  "schema_name": "public",
  "description": "Customer account information - CONTAINS PII",
  "schema_definition": [...],
  "metadata": {
    "contains_pii": true,
    "suggested_classification": "confidential",
    "primary_keys": ["account_id"],
    "row_count": 10
  }
}
```

### Register Dataset

```bash
curl -X POST http://localhost:8000/api/v1/datasets/ \
  -H "Content-Type: application/json" \
  -d @examples/register_customer_accounts.json
```

**What Happens:**
1. Dataset is created in the registry
2. Initial contract (v1.0.0) is generated
3. Contract is validated against all policies
4. Contract is committed to Git repository
5. Violations are reported with remediation guidance

### View Generated Contract

```bash
# Check the Git repository
ls -la backend/contracts/

# View the contract
cat backend/contracts/customer_accounts_v1.0.0.yaml
```

**Example Contract:**
```yaml
# Data Contract
# Dataset: customer_accounts
# Version: 1.0.0
# Generated: 2024-02-04 15:30:00

dataset:
  name: customer_accounts
  owner_name: John Doe
  owner_email: john.doe@company.com
  version: 1.0.0

schema:
  - name: customer_ssn
    type: string
    pii: true
    description: Social Security Number - SENSITIVE DATA
    max_length: 11

governance:
  classification: confidential
  encryption_required: true
  retention_days: 2555
  compliance_tags:
    - GDPR
    - CCPA
```

## 📚 API Documentation

### Interactive Documentation

Visit http://localhost:8000/api/docs for Swagger UI with interactive API testing.

### Core Endpoints

#### Datasets

- `POST /api/v1/datasets/` - Create dataset
- `GET /api/v1/datasets/` - List datasets (with filters)
- `GET /api/v1/datasets/{id}` - Get dataset details
- `PUT /api/v1/datasets/{id}` - Update dataset
- `DELETE /api/v1/datasets/{id}` - Delete dataset (soft delete)

#### Schema Import

- `POST /api/v1/datasets/import-schema` - Import schema from sources
- `GET /api/v1/datasets/postgres/tables` - List PostgreSQL tables

#### System

- `GET /` - Root endpoint with API info
- `GET /health` - Health check

## 🎭 Demo Scenario

The platform includes a realistic financial services demo with intentional policy violations.

### Demo Tables

1. **customer_accounts** (10 records)
   - Contains PII (email, SSN, phone, DOB)
   - **Violations**: Missing encryption documentation, missing compliance tags

2. **transactions** (23 records)
   - Time-sensitive financial transactions
   - **Violations**: Missing freshness SLA, NULL status values, no enum constraints
   - Includes suspicious patterns (large purchases, late-night withdrawals)

3. **fraud_alerts** (6 records)
   - Critical fraud detection data
   - **Violations**: Missing quality thresholds, NULL risk scores
   - Mix of confirmed fraud, false positives, and investigating cases

### Expected Validation Report

When registering `customer_accounts`, you'll see:

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
      "remediation": "Set 'encryption_required: true' in governance metadata..."
    },
    {
      "type": "warning",
      "policy": "SD003: pii_compliance_tags",
      "field": "governance.compliance_tags",
      "message": "Datasets with PII should specify compliance frameworks",
      "remediation": "Add compliance tags like GDPR, CCPA, HIPAA..."
    }
  ]
}
```

## 📜 Policy Definitions

### Sensitive Data Policies (SD)

| ID | Name | Severity | Description |
|----|------|----------|-------------|
| SD001 | pii_encryption_required | Critical | All PII fields must have encryption enabled |
| SD002 | retention_policy_required | Critical | Confidential/restricted data must specify retention period |
| SD003 | pii_compliance_tags | Warning | PII datasets should specify compliance frameworks |
| SD004 | restricted_use_cases | Critical | Restricted data must specify approved use cases |
| SD005 | cross_border_pii | Critical | Cross-border PII requires data residency specification |

### Data Quality Policies (DQ)

| ID | Name | Severity | Description |
|----|------|----------|-------------|
| DQ001 | critical_data_completeness | Critical | Confidential/restricted data requires ≥95% completeness |
| DQ002 | freshness_sla_required | Warning | Temporal datasets should specify freshness SLA |
| DQ003 | uniqueness_specification | Warning | Key fields should have uniqueness constraints |
| DQ004 | accuracy_threshold_alignment | Warning | Accuracy thresholds should align with classification |

### Schema Governance Policies (SG)

| ID | Name | Severity | Description |
|----|------|----------|-------------|
| SG001 | field_documentation_required | Warning | All fields should have descriptions |
| SG002 | required_field_consistency | Critical | Required fields cannot be nullable |
| SG003 | dataset_ownership_required | Critical | Datasets must have assigned ownership |
| SG004 | string_field_constraints | Warning | String fields should have max_length |
| SG005 | enum_value_specification | Warning | Enum fields should list valid values |
| SG006 | breaking_schema_changes | Critical | Breaking changes require major version bump |

## 🔧 Troubleshooting

### PostgreSQL Won't Start

```bash
# Check if port 5432 is already in use
lsof -i :5432

# Stop existing PostgreSQL if needed
docker-compose down

# Remove volumes and restart
docker-compose down -v
docker-compose up -d
```

### Backend Won't Start

```bash
# Check Python version (must be 3.10+)
python --version

# Reinstall dependencies
pip install -r backend/requirements.txt --upgrade

# Check for port conflicts
lsof -i :8000
```

### Schema Import Fails

```bash
# Verify PostgreSQL connection
docker exec -it governance_postgres psql -U governance_user -d financial_demo -c "\dt"

# You should see: customer_accounts, transactions, fraud_alerts
```

### Tests Fail

```bash
# Make sure both PostgreSQL and backend are running
docker ps  # Should show governance_postgres
curl http://localhost:8000/health  # Should return {"status": "healthy"}

# Run tests with verbose output
python test_setup.py
```

## 🚀 Next Steps

### Phase 2: Frontend (React)

- Data Owner UI: Dataset registration wizard
- Data Consumer UI: Catalog browser with subscription form
- Data Steward UI: Approval queue and contract review
- Platform Dashboard: Compliance metrics and violation trends

### Phase 3: Enhancements

- **Additional Connectors**: Azure Data Lake, Azure Blob Storage, CSV/Parquet files
- **Advanced Features**: Pre-commit hooks, CI/CD integration, real-time monitoring
- **Compliance**: Automated data lineage, advanced reporting
- **Subscriptions**: Full workflow with SLA negotiation and access provisioning

### Immediate Enhancements

1. Add authentication and authorization
2. Implement contract approval workflow
3. Add subscription management endpoints
4. Create React frontend
5. Add data lineage tracking
6. Implement notification system

## 📝 File Structure

```
data-governance-platform/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── api/             # FastAPI endpoints
│   │   ├── services/        # Business logic
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   └── main.py          # FastAPI app
│   ├── policies/            # YAML policy files
│   ├── contracts/           # Git repository for contracts
│   └── requirements.txt     # Python dependencies
├── demo/
│   ├── setup_postgres.sql   # Database schema
│   └── sample_data.sql      # Sample data with violations
├── examples/
│   └── register_customer_accounts.json
├── docker-compose.yml       # PostgreSQL setup
├── test_setup.py           # Automated test suite
├── start.sh                # Quick start script
└── README.md               # This file
```

## 🤝 Contributing

This is a demonstration platform. For production use:

1. Add authentication (OAuth2/JWT)
2. Encrypt sensitive data (SSN, passwords)
3. Use proper secret management (Azure Key Vault)
4. Add comprehensive error handling
5. Implement audit logging
6. Add rate limiting
7. Use production-grade database (PostgreSQL/Azure SQL)

## 📄 License

This is a demonstration project for educational purposes.

## 🎓 Key Takeaways

1. **Prevention Over Detection**: Validate at contract creation, not production
2. **Federated Governance**: Autonomy with centralized standards (UN Peacekeeping)
3. **Policy-as-Code**: Version-controlled, testable governance rules
4. **Developer-Friendly**: Clear error messages with actionable remediation
5. **Git Integration**: Full audit trail and diff capabilities
6. **Dual Contracts**: Human-readable for understanding, machine-readable for automation

---

**Built with ❤️ for Data Governance**
