# Data Governance Platform - Policy-as-Code PoC

Enabling proactive data governance using Policy-as-Code with a comprehensive multi-role frontend.

## 🎯 Overview

A production-ready proof-of-concept demonstrating federated data governance using the **UN Peacekeeping model** - shared policies with distributed enforcement. This platform prevents governance violations before they reach production through automated policy validation and actionable remediation.

## ✨ Key Features

### Backend
- **17 Governance Policies**: Sensitive data, data quality, and schema governance (SD001-SD005, DQ001-DQ005, SG001-SG007)
- **8 Semantic Policies**: LLM-powered context-aware validation with local Ollama (SEM001-SEM008)
- **Intelligent Policy Orchestration**: Auto-decides between rule-based & LLM validation based on risk (FAST/BALANCED/THOROUGH/ADAPTIVE)
- **Automated Schema Import**: PostgreSQL with heuristic PII detection
- **Dual Contracts**: Human-readable YAML + Machine-readable JSON with SHA-256 schema hashing
- **Git Version Control**: Full audit trail for all contracts with semantic versioning
- **Policy Validation**: Real-time validation with actionable remediation guidance

### Frontend
- **Data Owner UI**: Multi-step dataset registration wizard with schema import and violation alerts
- **Data Consumer UI**: Catalog browser with subscription requests and SLA negotiation
- **Data Steward UI**: Approval queue with contract review and credential management
- **Platform Admin UI**: Compliance dashboard with Recharts analytics
- **End-to-End Workflows**: Complete subscription lifecycle with automatic contract versioning

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker
- Git

### Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd Data-governace-using-PoC/data-governance-platform

# 2. Start PostgreSQL
docker-compose up -d

# 3. Setup backend
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Setup frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:5173/select-role
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs

## 🎨 User Roles

### 1. Data Owner
- Register datasets with governance metadata
- Import schemas from PostgreSQL
- View policy violations with remediation
- Track subscribers and usage

### 2. Data Consumer
- Browse data catalog
- Request dataset access
- Define SLA requirements
- Select needed fields

### 3. Data Steward
- Review subscription requests
- Approve/reject with credentials
- Manage access controls
- Track approval history

### 4. Platform Admin
- Monitor compliance metrics
- Analyze violation trends
- View top violated policies
- Generate compliance reports

## 📊 Workflows

### Dataset Registration
```
Owner: Register → Import Schema → Set Governance → Submit
System: Validate → Generate Contract → Commit to Git → Report Violations
```

### Data Subscription
```
Consumer: Browse → Request Access → Specify SLA
Steward: Review → Approve/Reject → Grant Credentials
System: Update Contract → Version Bump → Commit to Git
```

### Violation Remediation
```
Owner: View Alert → Read Remediation → Fix Issue → Re-submit
System: Re-validate → Update Contract → Clear Violation
```

## 📁 Project Structure

```
Data-governace-using-PoC/
└── data-governance-platform/
    ├── backend/              # FastAPI backend (Python 3.10+)
    │   ├── app/
    │   │   ├── api/          # REST endpoints (datasets, subscriptions, git, semantic, orchestration)
    │   │   ├── models/       # SQLAlchemy ORM models (Dataset, Contract, Subscription, User)
    │   │   ├── schemas/      # Pydantic v2 validation schemas
    │   │   ├── services/     # Business logic services
    │   │   │   ├── policy_engine.py        # 17 YAML-based governance policies
    │   │   │   ├── contract_service.py     # Contract generation & versioning
    │   │   │   ├── git_service.py          # Git version control
    │   │   │   ├── postgres_connector.py   # PostgreSQL schema import with PII detection
    │   │   │   ├── semantic_policy_engine.py # LLM-powered validation (Ollama)
    │   │   │   ├── policy_orchestrator.py  # Intelligent validation routing
    │   │   │   └── ollama_client.py        # Local LLM client
    │   │   └── main.py       # FastAPI application entry point
    │   ├── policies/         # YAML policy definitions (25 total policies)
    │   ├── contracts/        # Git repository for versioned contracts
    │   └── tests/            # 101 pytest tests (policy, API, service, model)
    ├── frontend/             # React 18 frontend (Vite)
    │   ├── src/
    │   │   ├── pages/        # Role-based UIs (Owner, Consumer, Steward, Admin)
    │   │   ├── contexts/     # Auth context (role-based)
    │   │   ├── services/     # Axios API client
    │   │   └── stores/       # Zustand state management
    │   └── package.json
    ├── demo/                 # Demo PostgreSQL database (3 tables, 39 records)
    ├── examples/             # Example API request payloads
    ├── docker-compose.yml    # PostgreSQL demo setup
    ├── start.sh              # Quick backend start script
    └── test_setup.py         # Automated setup verification
```

## 📚 Documentation

See [data-governance-platform/README.md](./data-governance-platform/README.md) for detailed documentation including:
- Architecture diagrams
- Policy definitions
- API documentation
- Troubleshooting guide
- Development roadmap

## 🛠️ Technology Stack

**Backend:**
- FastAPI 0.109.0 (Python 3.10+) + Uvicorn 0.27.0
- SQLAlchemy 2.0.25 ORM with SQLite (metadata) + PostgreSQL 15 (demo)
- Pydantic v2 (data validation) + pydantic-settings 2.1.0
- GitPython 3.1.41 (contract version control)
- PyYAML 6.0.1 (policy definitions)
- Ollama (local LLM for semantic validation)
- pytest + httpx (testing, 101 tests)

**Frontend:**
- React 18.2 + Vite 5.0.8
- React Router 6 (navigation)
- Zustand 4.4.7 (state management)
- Recharts 2.10.3 (analytics charts)
- Axios 1.6.2 (HTTP client)
- Framer Motion 10.16.16 (animations)
- Lucide React (icons)

**Infrastructure:**
- Docker + Docker Compose (PostgreSQL demo)
- Git (contract version control and audit trail)

## 🎯 Demo Scenario

The platform includes a financial services demo with three tables:
1. **customer_accounts**: Contains PII with intentional violations
2. **transactions**: Financial transactions with quality issues
3. **fraud_alerts**: Fraud detection data with missing thresholds

Use these tables to test the full workflow from registration to subscription approval.

## ✅ Current Status

- ✅ Backend API (FastAPI, 20+ REST endpoints)
- ✅ Policy Engine (17 rule-based policies across 3 categories)
- ✅ Semantic Policy Engine (8 LLM-powered policies via Ollama)
- ✅ Intelligent Policy Orchestration (FAST/BALANCED/THOROUGH/ADAPTIVE strategies)
- ✅ Schema Import (PostgreSQL with automatic PII detection)
- ✅ Contract Management (dual YAML+JSON format, semantic versioning)
- ✅ Git Integration (full audit trail, diffs, commit history)
- ✅ Multi-Role Frontend (Data Owner, Consumer, Steward, Admin)
- ✅ Subscription Workflow (request → review → approve → credential generation)
- ✅ Compliance Dashboard (real-time metrics, Recharts analytics)
- ✅ Violation Tracking (severity-based with actionable remediation)
- ✅ Test Suite (101 backend tests + frontend Vitest setup)

## 🧬 Semantic Scanning

The platform includes AI-powered semantic policy validation using local LLMs via **Ollama**:

- **8 Semantic Policies (SEM001-SEM008)**: Context-aware validation beyond rule-based patterns
- **Local LLM Execution**: Privacy-first with Ollama (no data leaves your infrastructure)
- **Smart Detection**: Identifies sensitive data based on context, not just field naming patterns
- **Business Logic Validation**: Ensures governance rules make business sense
- **Security Pattern Recognition**: Detects vulnerabilities in schema design
- **Optional**: Works without Ollama installed — falls back to rule-based validation only

📖 **See [SEMANTIC_SCANNING.md](./data-governance-platform/SEMANTIC_SCANNING.md) for complete guide**

## 🧠 Policy Orchestration

An intelligent orchestration layer automatically decides when to use rule-based vs LLM-based validation:

- **4 Validation Strategies**:
  - **FAST** (~100ms): Rule-based policies only — for development and low-risk data
  - **BALANCED** (~5-10s): Rules + targeted semantic — for most production use cases
  - **THOROUGH** (~20-30s): All 25 policies — for compliance audits and critical data
  - **ADAPTIVE** (variable): Auto-selects strategy based on contract risk analysis
- **Risk Assessment**: Analyzes contracts to determine risk level (LOW → CRITICAL)
- **Performance Optimized**: Avoids expensive LLM calls when not needed

**Example**: Low-risk internal data → FAST (rule-based, ~100ms). PII dataset with GDPR/CCPA → THOROUGH (all 25 policies, ~24s).

📖 **See [POLICY_ORCHESTRATION.md](./data-governance-platform/POLICY_ORCHESTRATION.md) for complete guide**

## 🔜 Future Enhancements

- Authentication & Authorization (OAuth2/JWT)
- Additional connectors (Azure, Snowflake, S3)
- Data lineage tracking
- Real-time monitoring
- Email/Slack notifications
- Advanced analytics (ML-powered)
- Mobile app
- Expand semantic policies (custom domain-specific validations)

## 📄 License

This is a demonstration project for educational purposes.

## 🤝 Contributing

For production use, consider adding:
- Proper authentication
- Secret management
- Comprehensive error handling
- Audit logging
- Rate limiting
- Production database setup

---

**Built with ❤️ for Data Governance**

For detailed setup instructions, API documentation, and troubleshooting, see the [full documentation](./data-governance-platform/README.md).
