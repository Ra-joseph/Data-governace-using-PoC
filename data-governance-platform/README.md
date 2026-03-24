# Data Governance Platform

A comprehensive Policy-as-Code data governance platform implementing federated governance using the UN Peacekeeping model. This platform features a **multi-role frontend** with dedicated UIs for Data Owners, Data Consumers, Data Stewards, and Platform Admins, enabling complete end-to-end data governance workflows.

## 🎯 Key Features

### Core Platform
- **Federated Governance**: UN Peacekeeping model - shared policies with distributed enforcement
- **Policy-as-Code**: YAML-defined policies with automated validation
- **Automated Schema Import**: Import from PostgreSQL, files, and Azure (extensible)
- **Dual Contracts**: Human-readable (YAML) + Machine-readable (JSON)
- **Git Version Control**: All contracts tracked with full history
- **Prevention at Borders**: Catch violations before publication, not after cascade
- **Actionable Remediation**: Every violation includes "how to fix it" guidance

### Multi-Role Frontend
- **Data Owner UI**: Dataset registration wizard, violation dashboard, subscriber tracking
- **Data Consumer UI**: Catalog browser, subscription requests with SLA negotiation
- **Data Steward UI**: Approval queue, contract review, access credential management
- **Platform Admin UI**: Compliance metrics, violation trends, analytics dashboards
- **End-to-End Workflows**: Complete subscription lifecycle with automatic contract versioning

### Intelligent Validation
- **Semantic Policy Scanning**: 8 AI-powered policies via local Ollama LLMs
- **Policy Orchestration**: 4 strategies (FAST, BALANCED, THOROUGH, ADAPTIVE) with risk-based routing
- **25 Total Policies**: 17 rule-based + 8 semantic for comprehensive governance coverage

## ODPS 4.1 Compliance

This platform implements the [Open Data Product Specification (ODPS) 4.1](https://opendataproducts.org),
maintained by the Linux Foundation LF AI & Data. Each data product exposes a
machine-readable ODPS descriptor so that external catalogue tools (Alation,
Collibra, AI agents) can auto-discover and consume data products in a
standards-compliant way.

### ODPS API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/odps/products` | List all ODPS-described data products |
| `GET` | `/api/odps/products/{id}` | Retrieve full ODPS descriptor (`Content-Type: application/odps+yaml;version=1.0.0`) |
| `GET` | `/api/odps/products/{id}/validate` | Validate dataset stats against declared ODPS quality thresholds |

### What ODPS Descriptors Cover

ODPS 4.1 descriptors are stored as YAML files in `backend/odps/` and include:

- **product** — identity (id, name, status, domain, owner, description)
- **quality** — declared thresholds for completeness, accuracy, and timeliness
- **sla** — update frequency, uptime percentage, response time
- **dataAccess** — personal data flag, access type (open/restricted/private), output ports
- **license** — scope and applicable governance frameworks (GDPR, SOX, PCI-DSS, etc.)
- **pricing** — pricing model and plan

### New ODPS Files

| File | Purpose |
|------|---------|
| `backend/odps/*.yaml` | ODPS 4.1 descriptors for each data product |
| `backend/app/api/odps.py` | ODPS API router (3 endpoints) |
| `backend/app/services/odps_service.py` | ODPS descriptor loading and quality validation |
| `backend/app/schemas/odps.py` | Pydantic models: OdpsDescriptor, OdpsViolation, OdpsValidationResult |

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Multi-Role Frontend](#multi-role-frontend)
- [End-to-End Workflows](#end-to-end-workflows)
- [API Documentation](#api-documentation)
- [Demo Scenario](#demo-scenario)
- [Policy Definitions](#policy-definitions)
- [Troubleshooting](#troubleshooting)
- [Next Steps](#next-steps)

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Frontend Layer (React 18 + Vite)               │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  Data Owner  │ Data Consumer│ Data Steward │  Platform Admin     │
│      UI      │      UI      │      UI      │       UI            │
│  • Register  │  • Browse    │  • Approve   │  • Metrics          │
│  • Manage    │  • Subscribe │  • Review    │  • Trends           │
│  • Violations│  • Request   │  • Credentials│ • Analytics        │
└──────────────┴──────────────┴──────────────┴────────────────────┘
                                 ▲
                                 │ REST API (55+ endpoints)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Data Governance Platform API                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Dataset    │  │   Contract   │  │ Subscription │          │
│  │   Registry   │◄─┤  Management  │◄─┤   Workflow   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            ▼                                      │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │              Policy Orchestration Engine                    │   │
│  │  Strategies: FAST | BALANCED | THOROUGH | ADAPTIVE         │   │
│  │  Risk Assessment: LOW → MEDIUM → HIGH → CRITICAL           │   │
│  └─────────────────────┬─────────────────────┘                │   │
│                ┌───────┴───────┐                                │   │
│                ▼               ▼                                │   │
│  ┌──────────────────┐  ┌──────────────────┐                    │   │
│  │  Rule-Based      │  │  Semantic Engine │                    │   │
│  │  Policy Engine   │  │  (LLM-Powered)   │                    │   │
│  ├──────────────────┤  ├──────────────────┤                    │   │
│  │ SD001-SD005 (5)  │  │ SEM001-SEM008(8)│                    │   │
│  │ DQ001-DQ005 (5)  │  │ Context-aware   │                    │   │
│  │ SG001-SG007 (7)  │  │ via Ollama LLM  │                    │   │
│  └──────────────────┘  └──────────────────┘                    │   │
│                                                                   │
│  ┌───────────────────────────────────────────────────┐          │
│  │              Git Repository (Contracts)            │          │
│  │  • Version Control  • Audit Trail  • Diff/Compare │          │
│  └───────────────────────────────────────────────────┘          │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                      Data Sources                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │PostgreSQL│  │  Files   │  │Azure Blob│  │ Azure DL │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Core Components

**Backend (11 API routers):**
1. **Dataset Registry**: Catalog of all data assets with metadata, schema import from PostgreSQL
2. **Contract Management**: Version-controlled data contracts (YAML + JSON) with Git integration
3. **Subscription Workflow**: End-to-end consumer access requests with SLA negotiation and approvals
4. **Policy Orchestration**: Intelligent routing between rule-based and semantic validation (4 strategies)
5. **Rule-Based Policy Engine**: 17 YAML-defined policies across 3 categories (SD, DQ, SG)
6. **Semantic Policy Engine**: 8 LLM-powered context-aware policies via local Ollama
7. **Policy Authoring**: Full lifecycle management — draft, review, approve, version, deprecate
8. **Policy Dashboard**: Compliance stats, active policy listing, and combined validation
9. **Policy Reports**: Impact analysis, compliance overviews, and bulk validation
10. **Policy Exchange**: Import/export policies, template library, and template instantiation
11. **Domain Governance**: Domain-based policy matrix, analytics, and effectiveness tracking
12. **Policy Exceptions**: Conflict detection, exception requests, approval, and deployment gates
13. **Git Service**: Contract version control and full audit trail
14. **PostgreSQL Connector**: Schema introspection with heuristic PII detection

**Frontend (React + Vite):**
1. **Role-Based UIs**: Dedicated interfaces for Data Owner, Consumer, Steward, and Admin
2. **Dataset Registration Wizard**: Multi-step form with PostgreSQL schema import
3. **Catalog Browser**: Search, filter, and subscribe to datasets
4. **Approval Queue**: Review and approve subscription requests with credential management
5. **Compliance Dashboard**: Real-time metrics, violation trends, and interactive analytics
6. **Policy Manager**: Full policy authoring UI with lifecycle management (`PolicyAuthoring/` components)
7. **Git History Viewer**: Contract version history and diff comparison
8. **Schema Import**: Direct PostgreSQL schema import interface
9. **Contract Viewer**: YAML/JSON contract display with metadata

## 📦 Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18 or higher (for frontend)
- **npm**: 9 or higher (comes with Node.js)
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

### Step 4: Setup Frontend (2 minutes)

```bash
# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 5: Start Backend API (1 minute)

```bash
# Option 1: Using the start script
chmod +x start.sh
./start.sh

# Option 2: Manual start
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: http://localhost:8000

### Step 6: Start Frontend (1 minute)

```bash
# In a new terminal
cd frontend
npm run dev
```

The frontend will be available at: http://localhost:3000 (auto-redirects to the role selector)

### Step 7: Verify Installation (1 minute)

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

### Option 1: Using the Frontend (Recommended)

1. **Access the application** at http://localhost:3000 (auto-redirects to role selector)

2. **Select "Data Owner"** to register a dataset
   - Click on the Data Owner card
   - Navigate to "Register Dataset"
   - Click "Import from PostgreSQL" in Step 2
   - Select `customer_accounts` table
   - Complete the wizard and submit
   - View the validation results

3. **Select "Data Consumer"** to browse and subscribe
   - Click **Switch Role** in the header or navigate to http://localhost:3000
   - Click on the Data Consumer card
   - Browse the catalog
   - Click "Request Access" on a dataset
   - Fill in business justification and SLA requirements
   - Submit subscription request

4. **Select "Data Steward"** to approve requests
   - Click **Switch Role** in the header or navigate to http://localhost:3000
   - Click on the Data Steward card
   - View the pending subscription in the approval queue
   - Click "Review"
   - Approve with credentials or reject with notes

5. **Select "Platform Admin"** to view metrics
   - Click **Switch Role** in the header or navigate to http://localhost:3000
   - Click on the Platform Admin card
   - View compliance dashboard with charts and metrics

### Option 2: Using the API

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

## 🎨 Multi-Role Frontend

The platform features a complete React-based frontend with dedicated UIs for each role in the data governance workflow.

### Accessing the Frontend

1. Start both backend and frontend (see Installation)
2. Navigate to http://localhost:3000 (auto-redirects to role selector)
3. Select your role to access the corresponding UI

### Role-Based User Interfaces

#### 🗂️ Data Owner UI

**Dashboard** (`/owner/dashboard`)
- View all owned datasets with status and violations
- Track subscriber counts and activity
- Get actionable remediation for policy violations
- Quick access to register new datasets

**Dataset Registration Wizard** (`/owner/register`)
- **Step 1 - Basic Info**: Name, description, owner details
- **Step 2 - Schema**: Manual entry or PostgreSQL import
- **Step 3 - Governance**: Classification, retention, compliance tags
- **Step 4 - Review**: Final review before submission
- **Auto-validation**: Immediate policy check on submission
- **PII Detection**: Automatic detection of sensitive fields

**Features:**
- Real-time violation alerts with remediation guidance
- PostgreSQL schema import with automatic PII detection
- Multi-step wizard with validation at each step
- Dataset status tracking (draft, published, deprecated)

#### 🛒 Data Consumer UI

**Catalog Browser** (`/consumer/catalog`)
- Browse all published datasets
- Search by name or description
- Filter by classification level
- View dataset details and schema
- See compliance status and tags

**Subscription Request Form**
- Business justification field
- Use case specification
- SLA requirements:
  - Max latency (ms)
  - Min availability (%)
  - Max staleness (minutes)
- Field-level access selection
- Access duration configuration

**Features:**
- Grid view with dataset cards
- Real-time search and filtering
- Detailed schema preview
- Compliance badge display

#### ⚖️ Data Steward UI

**Approval Queue** (`/steward/approvals`)
- View pending, approved, and rejected subscriptions
- Filter by status
- Detailed request information
- Use case and justification review

**Review Modal**
- Approve or reject with notes
- Select approved fields (subset of requested)
- Generate access credentials:
  - Username
  - API key
  - Connection string (optional)
- Add reviewer comments

**Features:**
- Automatic contract versioning on approval
- Access credential generation
- Comprehensive request details
- Subscription history tracking

#### 📊 Platform Admin UI

**Compliance Dashboard** (`/admin/dashboard`)

**Key Metrics:**
- Compliance rate with trend
- Total active violations
- Active subscriptions
- Pending approvals

**Analytics Charts:**
- **Violation Trends**: Line chart showing violations over time
- **Violations by Severity**: Pie chart (critical, warning, info)
- **Top Violated Policies**: Bar chart of most common violations
- **Compliance by Classification**: Stacked bar chart by data class

**Recent Activity:**
- Latest policy violations
- New subscription requests
- Dataset registrations

**Features:**
- Real-time metrics
- Interactive Recharts visualizations
- Drill-down capabilities
- Export-ready data

## 🔄 End-to-End Workflows

### Workflow 1: Dataset Registration

```
Data Owner Actions:
1. Navigate to /owner/register
2. Enter dataset information (3-step wizard)
3. Import schema from PostgreSQL or enter manually
4. Set governance rules and compliance tags
5. Review and submit

System Actions:
1. Create dataset in registry
2. Generate data contract (v1.0.0)
3. Validate against 17 policies
4. Commit contract to Git
5. Return validation report with violations

Data Owner Result:
- Dataset published (if compliant) or draft (if violations)
- View violations with remediation on dashboard
- Track dataset in owner dashboard
```

### Workflow 2: Data Subscription

```
Data Consumer Actions:
1. Browse catalog (/consumer/catalog)
2. Select dataset
3. Click "Request Access"
4. Fill subscription form:
   - Business justification
   - Use case
   - SLA requirements
   - Select needed fields
5. Submit request

System Actions:
1. Create subscription record (status: pending)
2. Notify data steward (future: email/webhook)
3. Queue request in approval system

Data Steward Actions:
1. View request in /steward/approvals
2. Review business justification and use case
3. Verify SLA feasibility
4. Approve or reject with notes
5. Generate access credentials (if approved)

System Actions (on approval):
1. Update subscription status to "approved"
2. Store access credentials
3. Create new contract version (v1.1.0)
4. Add subscription SLA to contract
5. Commit new contract to Git
6. Grant access to consumer

Data Consumer Result:
- Receive access credentials
- Can access approved fields
- SLA enforced by platform
```

### Workflow 3: Violation Remediation

```
Data Owner Actions:
1. View violation alert on /owner/dashboard
2. Click violation to see details
3. Read remediation guidance
4. Fix issue in source or update metadata
5. Re-submit or update dataset

System Actions:
1. Re-validate contract
2. Update validation status
3. Commit new contract version if changed
4. Clear violation if resolved

Data Owner Result:
- Dataset moves from draft to published
- Violation removed from dashboard
- Compliance metrics updated
```

### Workflow 4: Compliance Monitoring

```
Platform Admin Actions:
1. View /admin/dashboard daily
2. Review compliance rate trend
3. Identify top violated policies
4. Drill into specific violations
5. Report to stakeholders

System Actions:
1. Aggregate metrics across all datasets
2. Calculate trends over time
3. Generate violation analytics
4. Update charts in real-time

Platform Admin Result:
- Understand platform health
- Identify systemic issues
- Track improvement over time
- Data-driven governance decisions
```

## 📚 API Documentation

### Interactive Documentation

Visit http://localhost:8000/api/docs for Swagger UI with interactive API testing.

### Core Endpoints

#### Datasets

- `POST /api/v1/datasets/` - Create dataset (triggers policy validation)
- `GET /api/v1/datasets/` - List datasets (with filters)
- `GET /api/v1/datasets/{id}` - Get dataset details
- `PUT /api/v1/datasets/{id}` - Update dataset
- `DELETE /api/v1/datasets/{id}` - Delete dataset (soft delete)
- `POST /api/v1/datasets/import-schema` - Import schema from sources
- `GET /api/v1/datasets/postgres/tables` - List PostgreSQL tables

#### Subscriptions

- `POST /api/v1/subscriptions/` - Create subscription request
- `GET /api/v1/subscriptions/` - List subscriptions (filters: status, dataset_id, consumer_email)
- `GET /api/v1/subscriptions/{id}` - Get subscription details
- `POST /api/v1/subscriptions/{id}/approve` - Approve or reject subscription
- `PUT /api/v1/subscriptions/{id}` - Update subscription
- `DELETE /api/v1/subscriptions/{id}` - Cancel subscription

#### Git

- `GET /api/v1/git/commits` - List contract commits
- `GET /api/v1/git/commits/{hash}` - Get commit details
- `GET /api/v1/git/diff/{old}..{new}` - Compare contract versions
- `POST /api/v1/git/commit` - Create commit
- `GET /api/v1/git/log` - Get git log
- `GET /api/v1/git/status` - Get repository status
- `GET /api/v1/git/branches` - List branches
- `POST /api/v1/git/checkout` - Checkout branch

#### Semantic Scanning

- `POST /api/v1/semantic/validate` - Validate using semantic policies
- `GET /api/v1/semantic/status` - Check Ollama connectivity
- `GET /api/v1/semantic/models` - List available LLM models
- `POST /api/v1/semantic/scan` - Perform semantic scan
- `GET /api/v1/semantic/results/{id}` - Get scan results

#### Policy Orchestration

- `POST /api/v1/orchestration/validate` - Validate with orchestration engine
- `GET /api/v1/orchestration/strategies` - List validation strategies
- `POST /api/v1/orchestration/analyze-risk` - Analyze contract risk level
- `GET /api/v1/orchestration/metrics` - Get performance metrics
- `POST /api/v1/orchestration/configure` - Configure orchestrator settings

#### Policy Authoring (`/api/v1/policies/authored`)

- `POST /api/v1/policies/authored/` - Create a new authored policy draft
- `GET /api/v1/policies/authored/` - List authored policies
- `GET /api/v1/policies/authored/{policy_id}` - Get policy details
- `PATCH /api/v1/policies/authored/{policy_id}` - Update policy draft
- `POST /api/v1/policies/authored/{policy_id}/submit` - Submit policy for review
- `POST /api/v1/policies/authored/{policy_id}/approve` - Approve policy
- `POST /api/v1/policies/authored/{policy_id}/reject` - Reject policy with feedback
- `GET /api/v1/policies/authored/{policy_id}/yaml` - Get generated YAML artifact
- `GET /api/v1/policies/authored/{policy_id}/preview-yaml` - Preview YAML before approval
- `GET /api/v1/policies/authored/{policy_id}/versions` - List all policy versions
- `GET /api/v1/policies/authored/{policy_id}/versions/{version}/diff` - Compare versions
- `POST /api/v1/policies/authored/{policy_id}/revise` - Create a new revision
- `POST /api/v1/policies/authored/{policy_id}/deprecate` - Deprecate policy
- `GET /api/v1/policies/authored/{policy_id}/timeline` - Get policy lifecycle timeline
- `GET /api/v1/policies/authored/domains/{domain}/policies` - Policies by domain

#### Policy Dashboard (`/api/v1/policy-dashboard`)

- `GET /api/v1/policy-dashboard/stats` - Compliance stats and metrics summary
- `GET /api/v1/policy-dashboard/active-policies` - List active policies
- `POST /api/v1/policy-dashboard/validate-combined` - Combined rule-based + semantic validation

#### Policy Reports (`/api/v1/policy-reports`)

- `GET /api/v1/policy-reports/impact/{policy_id}` - Impact analysis for a policy
- `GET /api/v1/policy-reports/compliance` - Compliance overview across all datasets
- `POST /api/v1/policy-reports/bulk-validate` - Bulk validate multiple datasets
- `GET /api/v1/policy-reports/policy-compliance/{policy_id}` - Per-policy compliance detail

#### Policy Exchange (`/api/v1/policy-exchange`)

- `GET /api/v1/policy-exchange/export/{policy_id}` - Export a single policy
- `GET /api/v1/policy-exchange/export-bundle` - Export all policies as a bundle
- `POST /api/v1/policy-exchange/import` - Import policies from a bundle
- `GET /api/v1/policy-exchange/templates` - List available policy templates
- `GET /api/v1/policy-exchange/templates/{template_id}` - Get template details
- `POST /api/v1/policy-exchange/templates/{template_id}/instantiate` - Create policy from template

#### Domain Governance (`/api/v1/domain-governance`)

- `GET /api/v1/domain-governance/domains` - List all governance domains
- `GET /api/v1/domain-governance/domains/{domain}` - Get domain details and policies
- `GET /api/v1/domain-governance/matrix` - Full domain-policy compliance matrix
- `GET /api/v1/domain-governance/analytics` - Domain-level governance analytics
- `GET /api/v1/domain-governance/effectiveness` - Policy effectiveness metrics by domain

#### Policy Exceptions (`/api/v1/policy-exceptions`)

- `POST /api/v1/policy-exceptions/detect-failures` - Detect active policy conflicts
- `GET /api/v1/policy-exceptions/failures` - List detected policy failures
- `POST /api/v1/policy-exceptions/` - Create exception request
- `GET /api/v1/policy-exceptions/requests` - List exception requests
- `GET /api/v1/policy-exceptions/requests/{exception_id}` - Get exception details
- `POST /api/v1/policy-exceptions/requests/{exception_id}/approve` - Approve exception
- `POST /api/v1/policy-exceptions/requests/{exception_id}/reject` - Reject exception
- `GET /api/v1/policy-exceptions/deployment-gate/{domain}` - Check deployment gate status
- `GET /api/v1/policy-exceptions/stats` - Exception statistics
- `POST /api/v1/policy-exceptions/reset` - Reset exception state

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
| DQ005 | data_quality_tiering | Warning | Datasets should have quality tier (Gold/Silver/Bronze) |

### Schema Governance Policies (SG)

| ID | Name | Severity | Description |
|----|------|----------|-------------|
| SG001 | field_documentation_required | Warning | All fields should have descriptions |
| SG002 | required_field_consistency | Critical | Required fields cannot be nullable |
| SG003 | dataset_ownership_required | Critical | Datasets must have assigned ownership |
| SG004 | string_field_constraints | Warning | String fields should have max_length |
| SG005 | enum_value_specification | Warning | Enum fields should list valid values |
| SG006 | breaking_schema_changes | Critical | Breaking changes require major version bump |
| SG007 | version_strategy_enforcement | Warning | Datasets must specify a versioning strategy |

### Semantic Policies (SEM) - LLM-Powered

| ID | Name | Description |
|----|------|-------------|
| SEM001 | sensitive_data_context | Detects PII/sensitive data based on context, not just naming patterns |
| SEM002 | business_logic_consistency | Validates that governance rules make business sense |
| SEM003 | security_pattern_detection | Identifies potential security vulnerabilities in schema design |
| SEM004 | compliance_intent_verification | Verifies that compliance tags actually apply to the data |
| SEM005 | data_quality_semantic | Validates that quality thresholds make sense for the data type |
| SEM006 | field_relationship_analysis | Detects semantic relationships between fields |
| SEM007 | naming_convention_analysis | Analyzes naming for clarity and consistency |
| SEM008 | use_case_appropriateness | Evaluates if approved use cases fit the data classification |

## ✨ Feature Highlights

### Dataset Registration Wizard
- **Multi-step form** with progress indicator
- **PostgreSQL import** - automatically detect schema and PII
- **Manual entry** - define schema field by field
- **Real-time validation** - see policy violations before submission
- **Governance setup** - classification, retention, compliance tags

### Subscription Workflow
- **Self-service catalog** - browse and discover datasets
- **SLA negotiation** - define latency, availability, staleness requirements
- **Field-level access** - request only the fields you need
- **Business justification** - explain why you need the data
- **Approval tracking** - see status of your requests

### Compliance Dashboard
- **Real-time metrics** - compliance rate, violations, subscriptions
- **Trend analysis** - track improvements over time
- **Policy insights** - identify most violated policies
- **Classification breakdown** - compliance by data sensitivity
- **Interactive charts** - powered by Recharts

### Violation Management
- **Actionable alerts** - see what's wrong and how to fix it
- **Remediation guidance** - step-by-step instructions with examples
- **Policy references** - link to full policy documentation
- **Severity levels** - critical, warning, info
- **Field-specific** - know exactly which fields are problematic

### Contract Versioning
- **Semantic versioning** - MAJOR.MINOR.PATCH
- **Git integration** - full history with commit messages
- **Automatic updates** - new version on subscription approval
- **Diff comparison** - see what changed between versions
- **Audit trail** - who made changes and when

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

### Frontend Won't Start

```bash
# Check Node.js version (must be 18+)
node --version

# Check npm version
npm --version

# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check for port conflicts
lsof -i :5173
```

### Frontend Can't Connect to Backend

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check CORS configuration in backend/app/main.py
# Should include http://localhost:3000

# Check browser console for errors
# Open DevTools (F12) → Console tab
```

### Subscription Approval Fails

```bash
# Check backend logs for errors
# Look for contract versioning errors

# Verify Git is initialized
ls -la backend/contracts/.git

# Check database for subscription record
# Should have status "pending" before approval
```

### Charts Not Displaying

```bash
# Verify Recharts is installed
cd frontend
npm list recharts

# If missing, install it
npm install recharts

# Clear browser cache
# Hard reload: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

## 🚀 Next Steps

### ✅ Completed Features

- ✅ Data Owner UI with dataset registration wizard
- ✅ Data Consumer UI with catalog browser and subscription form
- ✅ Data Steward UI with approval queue and contract review
- ✅ Platform Admin Dashboard with compliance metrics and trends
- ✅ Complete subscription workflow with SLA negotiation
- ✅ Automatic contract versioning on subscription approval
- ✅ Real-time violation tracking and remediation guidance
- ✅ PostgreSQL schema import with PII detection
- ✅ 17 governance policies with actionable validation

### 🔜 Recommended Enhancements

#### Security & Authentication
1. **OAuth2/JWT Authentication**: Replace demo auth with proper authentication
2. **Role-Based Access Control (RBAC)**: Enforce permissions at API level
3. **Audit Logging**: Track all user actions for compliance
4. **Secret Management**: Integrate Azure Key Vault or HashiCorp Vault
5. **Data Encryption**: Encrypt PII fields at rest and in transit

#### Additional Data Sources
1. **Azure Data Lake Gen2**: Import schemas from ADLS
2. **Azure Blob Storage**: Support for CSV/Parquet files
3. **Snowflake Connector**: Schema import from Snowflake
4. **AWS S3**: Support for S3-based data lakes
5. **API Schemas**: Import from OpenAPI/Swagger definitions

#### Advanced Features
1. **Data Lineage Tracking**: Visualize data flow and transformations
2. **Real-Time Monitoring**: Alert on policy violations and SLA breaches
3. **Pre-Commit Hooks**: Prevent non-compliant contracts from being committed
4. **CI/CD Integration**: Validate contracts in deployment pipelines
5. **Notification System**: Email/Slack alerts for approvals and violations
6. **Advanced Analytics**: ML-powered PII detection, anomaly detection
7. **Contract Testing**: Automated tests for contract compatibility
8. **Data Quality Scoring**: Automated quality metrics calculation

#### User Experience
1. **Dataset Preview**: Show sample data in catalog
2. **Contract Diff Viewer**: Visual contract comparison
3. **Policy Editor**: UI for creating/editing policies
4. **Custom Dashboards**: User-configurable analytics views
5. **Export Reports**: PDF/Excel export for compliance reports
6. **Mobile App**: Mobile interface for approvals and monitoring

#### Enterprise Features
1. **Multi-Tenancy**: Support for multiple organizations
2. **SSO Integration**: Azure AD, Okta, etc.
3. **Advanced RBAC**: Fine-grained permissions
4. **Compliance Reports**: Automated SOC2, GDPR, HIPAA reports
5. **SLA Monitoring**: Real-time SLA compliance tracking
6. **Cost Tracking**: Monitor data access costs by consumer

## 📝 File Structure

```
data-governance-platform/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   │   ├── dataset.py
│   │   │   ├── contract.py
│   │   │   ├── subscription.py
│   │   │   ├── user.py
│   │   │   ├── policy_draft.py
│   │   │   ├── policy_version.py
│   │   │   ├── policy_artifact.py
│   │   │   └── policy_approval_log.py
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── api/             # FastAPI routers (11 routers, 55+ endpoints)
│   │   │   ├── datasets.py           # Dataset CRUD and schema import
│   │   │   ├── subscriptions.py      # Subscription workflow
│   │   │   ├── git.py                # Git history & contract retrieval
│   │   │   ├── semantic.py           # LLM semantic policy endpoints
│   │   │   ├── orchestration.py      # Intelligent policy routing
│   │   │   ├── policy_authoring.py   # Policy lifecycle (draft → approve → publish)
│   │   │   ├── policy_dashboard.py   # Compliance metrics & stats
│   │   │   ├── policy_reports.py     # Impact, bulk validation, compliance overview
│   │   │   ├── policy_exchange.py    # Import/export & template library
│   │   │   ├── domain_governance.py  # Domain-level governance & analytics
│   │   │   └── policy_conflicts.py   # Exception management & deployment gates
│   │   ├── services/        # Business logic layer
│   │   │   ├── contract_service.py        # Contract generation & Git versioning
│   │   │   ├── policy_engine.py           # Rule-based YAML policy validation
│   │   │   ├── semantic_policy_engine.py  # LLM validation via Ollama
│   │   │   ├── policy_orchestrator.py     # Intelligent routing & risk scoring
│   │   │   ├── postgres_connector.py      # Schema introspection & PII detection
│   │   │   ├── git_service.py             # Git operations (commit, tag, diff)
│   │   │   ├── ollama_client.py           # HTTP client for local Ollama
│   │   │   ├── authored_policy_loader.py  # Load & manage authored policies
│   │   │   └── policy_converter.py        # YAML ↔ JSON format conversion
│   │   ├── config.py        # Pydantic Settings; all env vars with defaults
│   │   ├── database.py      # SQLAlchemy engine, session, DB init & seed data
│   │   └── main.py          # FastAPI app factory; registers all routers
│   ├── policies/            # YAML policy definitions (25 policies)
│   │   ├── sensitive_data_policies.yaml      # SD001-SD005 (PII, encryption)
│   │   ├── data_quality_policies.yaml        # DQ001-DQ005 (quality, freshness)
│   │   ├── schema_governance_policies.yaml   # SG001-SG007 (schema, naming)
│   │   └── semantic_policies.yaml            # SM001-SM008 (LLM context-aware)
│   ├── contracts/           # Git-versioned data contracts (auto-managed)
│   ├── tests/               # pytest test suite (23 files, 600+ tests)
│   │   ├── test_policy_engine.py         # Rule-based policy validation
│   │   ├── test_contract_service.py      # Contract generation & versioning
│   │   ├── test_api_datasets.py          # Dataset CRUD endpoints
│   │   ├── test_api_subscriptions.py     # Subscription workflow endpoints
│   │   ├── test_api_git.py               # Git operations
│   │   ├── test_api_semantic.py          # Semantic policy endpoints
│   │   ├── test_api_orchestration.py     # Policy orchestration endpoints
│   │   ├── test_models.py                # SQLAlchemy model operations
│   │   ├── test_orchestration.py         # Policy orchestration strategies
│   │   ├── test_semantic_scanner.py      # LLM semantic policy evaluation
│   │   ├── test_semantic_engine.py       # Semantic engine unit tests
│   │   ├── test_policy_authoring.py      # Policy creation and management
│   │   ├── test_policy_conflicts.py      # Exception and conflict handling
│   │   ├── test_policy_converter.py      # YAML ↔ JSON conversion
│   │   ├── test_policy_enforcement.py    # End-to-end enforcement workflows
│   │   ├── test_policy_exchange.py       # Policy import/export
│   │   ├── test_policy_lifecycle.py      # Full policy lifecycle
│   │   ├── test_policy_reports.py        # Reporting endpoints
│   │   ├── test_domain_governance.py     # Domain-level governance
│   │   ├── test_git_service.py           # Git service unit tests
│   │   ├── test_ollama_client.py         # Ollama client tests
│   │   ├── test_authored_policy_loader.py # Authored policy loader
│   │   └── test_postgres_connector.py    # PostgreSQL connector
│   └── requirements.txt     # Python dependencies
├── frontend/               # React 18 + Vite frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx              # App layout with sidebar navigation
│   │   │   ├── TopNavLayout.jsx        # Top navigation layout variant
│   │   │   └── PolicyAuthoring/        # Policy management UI components
│   │   │       ├── PolicyForm.jsx       # Create/edit policy form
│   │   │       ├── PolicyList.jsx       # Policy list with filters
│   │   │       ├── PolicyDetail.jsx     # Policy detail view
│   │   │       ├── PolicyReview.jsx     # Review & approve workflow
│   │   │       ├── PolicyTimeline.jsx   # Lifecycle timeline view
│   │   │       ├── PolicyDashboard.jsx  # Policy compliance dashboard
│   │   │       ├── PolicyExchange.jsx   # Import/export UI
│   │   │       ├── PolicyConflicts.jsx  # Exception management UI
│   │   │       ├── DomainGovernance.jsx # Domain governance UI
│   │   │       └── ComplianceReport.jsx # Compliance reports UI
│   │   ├── contexts/
│   │   │   └── AuthContext.jsx         # Role-based auth context
│   │   ├── pages/
│   │   │   ├── DataOwner/
│   │   │   │   ├── DatasetRegistrationWizard.jsx  # 4-step registration wizard
│   │   │   │   └── OwnerDashboard.jsx             # Owner metrics & violations
│   │   │   ├── DataConsumer/
│   │   │   │   └── DataCatalogBrowser.jsx         # Catalog & subscription flow
│   │   │   ├── DataSteward/
│   │   │   │   └── ApprovalQueue.jsx              # Approval workflow
│   │   │   ├── Admin/
│   │   │   │   └── ComplianceDashboard.jsx        # Platform-wide analytics
│   │   │   ├── RoleSelector.jsx        # Landing page; role picker
│   │   │   ├── PolicyManager.jsx       # Policy management page
│   │   │   ├── GitHistory.jsx          # Contract version history viewer
│   │   │   ├── SchemaImport.jsx        # Schema import from PostgreSQL
│   │   │   ├── ContractViewer.jsx      # Contract display (YAML/JSON)
│   │   │   ├── DatasetCatalog.jsx      # Dataset catalog page
│   │   │   ├── DatasetDetail.jsx       # Dataset detail view
│   │   │   ├── Dashboard.jsx           # General dashboard
│   │   │   ├── ComplianceDashboard.jsx # Compliance metrics page
│   │   │   └── SubscriptionQueue.jsx   # Subscription queue view
│   │   ├── services/
│   │   │   └── api.js       # Axios client; all API calls go through here
│   │   ├── stores/
│   │   │   └── index.js     # Zustand global state management
│   │   ├── App.jsx          # Root: router + auth context provider
│   │   └── main.jsx         # Vite entry point
│   ├── package.json         # NPM dependencies
│   └── vite.config.js       # Vite configuration with /api proxy
├── demo/
│   ├── setup_postgres.sql   # Database schema setup
│   └── sample_data.sql      # Sample data with intentional violations
├── examples/
│   └── register_customer_accounts.json  # Example API payload
├── docker-compose.yml       # PostgreSQL 15 demo DB setup
├── test_setup.py            # Automated setup verification
├── start.sh                 # Quick-start script
└── README.md                # This file
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
7. **Role-Based UIs**: Dedicated interfaces for owners, consumers, stewards, and admins
8. **End-to-End Workflows**: Complete subscription lifecycle with automatic contract versioning
9. **Real-Time Analytics**: Live compliance metrics and violation trends
10. **Self-Service**: Empowers data consumers to discover and request access independently

---

**Built with ❤️ for Data Governance**
