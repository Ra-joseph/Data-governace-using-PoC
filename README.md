# Data Governance Platform - Policy-as-Code PoC

Enabling proactive data governance using Policy-as-Code with a comprehensive multi-role frontend.

## 🎯 Overview

A production-ready proof-of-concept demonstrating federated data governance using the **UN Peacekeeping model** - shared policies with distributed enforcement. This platform prevents governance violations before they reach production through automated policy validation and actionable remediation.

## ✨ Key Features

### Backend
- **25 Governance Policies**: 17 rule-based (sensitive data, data quality, schema governance) + 8 semantic (LLM-powered)
- **Semantic Policy Scanning**: AI-powered context-aware validation via local Ollama LLMs
- **Intelligent Policy Orchestration**: Auto-decides between rule-based & LLM validation based on risk level
- **Automated Schema Import**: PostgreSQL with heuristic PII detection
- **Dual Contracts**: Human-readable YAML + Machine-readable JSON
- **Git Version Control**: Full audit trail for all contracts with semantic versioning
- **Policy Validation**: Real-time validation with actionable remediation guidance

### Frontend
- **Data Owner UI**: Dataset registration wizard with multi-step form and violation dashboard
- **Data Consumer UI**: Catalog browser with subscription requests and SLA negotiation
- **Data Steward UI**: Approval queue with contract review and credential management
- **Platform Admin UI**: Compliance dashboard with interactive analytics and trend charts
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
    ├── backend/              # FastAPI backend
    │   ├── app/
    │   │   ├── api/          # REST endpoints (5 routers, 30+ endpoints)
    │   │   │   ├── datasets.py
    │   │   │   ├── subscriptions.py
    │   │   │   ├── git.py
    │   │   │   ├── semantic.py
    │   │   │   └── orchestration.py
    │   │   ├── models/       # SQLAlchemy models (4 models, 71 fields)
    │   │   ├── schemas/      # Pydantic validation (24+ schemas)
    │   │   ├── services/     # Business logic (7 services)
    │   │   │   ├── policy_engine.py
    │   │   │   ├── contract_service.py
    │   │   │   ├── postgres_connector.py
    │   │   │   ├── git_service.py
    │   │   │   ├── semantic_policy_engine.py
    │   │   │   ├── policy_orchestrator.py
    │   │   │   └── ollama_client.py
    │   │   └── main.py       # FastAPI app
    │   ├── policies/         # YAML policy definitions (4 files, 25 policies)
    │   ├── contracts/        # Git repository for versioned contracts
    │   └── tests/            # Comprehensive test suite
    ├── frontend/             # React 18 + Vite frontend
    │   ├── src/
    │   │   ├── pages/        # Role-based UIs (Owner, Consumer, Steward, Admin)
    │   │   ├── components/   # Shared components
    │   │   ├── contexts/     # Auth context
    │   │   ├── services/     # API client (Axios)
    │   │   └── stores/       # State management (Zustand)
    │   └── package.json
    ├── demo/                 # Demo database (PostgreSQL)
    └── README.md             # Detailed documentation
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Platform README](./data-governance-platform/README.md) | Architecture, API docs, workflows, troubleshooting |
| [Quick Start](./data-governance-platform/QUICKSTART.md) | 5-minute setup guide |
| [Project Summary](./data-governance-platform/PROJECT_SUMMARY.md) | Technical deep-dive and design decisions |
| [Deployment Guide](./data-governance-platform/DEPLOYMENT.md) | Production deployment instructions |
| [Frontend Guide](./data-governance-platform/FRONTEND_GUIDE.md) | Frontend developer guide |
| [Semantic Scanning](./data-governance-platform/SEMANTIC_SCANNING.md) | LLM-powered policy validation guide |
| [Policy Orchestration](./data-governance-platform/POLICY_ORCHESTRATION.md) | Intelligent validation routing |
| [Testing Guide](./data-governance-platform/TESTING.md) | Test suite documentation |
| [Contributing](./CONTRIBUTING.md) | Contribution guidelines and standards |
| [Manifest](./data-governance-platform/MANIFEST.md) | Complete file listing and statistics |

## 🛠️ Technology Stack

**Backend:**
- FastAPI 0.109 (Python 3.10+)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL 15 + SQLite (metadata)
- Pydantic v2 (validation)
- GitPython (contract versioning)
- Ollama (local LLM for semantic scanning)
- PyYAML (policy definitions)

**Frontend:**
- React 18.2
- Vite 5.0 (build tool)
- Zustand 4.4 (state management)
- Recharts 2.10 (interactive analytics)
- React Router 6 (client-side routing)
- Axios 1.6 (HTTP client)
- Framer Motion (animations)
- Lucide React (icons)

## 🎯 Demo Scenario

The platform includes a financial services demo with three tables:
1. **customer_accounts**: Contains PII with intentional violations
2. **transactions**: Financial transactions with quality issues
3. **fraud_alerts**: Fraud detection data with missing thresholds

Use these tables to test the full workflow from registration to subscription approval.

## ✅ Current Status

All planned features are implemented and functional:

- ✅ Backend API (FastAPI with 30+ endpoints)
- ✅ Policy Engine (25 policies: 17 rule-based + 8 semantic)
- ✅ Semantic Policy Scanning (LLM-powered via Ollama)
- ✅ Intelligent Policy Orchestration (4 strategies: FAST, BALANCED, THOROUGH, ADAPTIVE)
- ✅ Schema Import (PostgreSQL with PII detection)
- ✅ Contract Management (dual-format YAML + JSON)
- ✅ Git Integration (full audit trail with semantic versioning)
- ✅ Multi-Role Frontend (Owner, Consumer, Steward, Admin)
- ✅ Subscription Workflow (end-to-end with SLA negotiation)
- ✅ Compliance Dashboard (interactive charts and trend analytics)
- ✅ Violation Tracking (actionable remediation guidance)
- ✅ Comprehensive Test Suite (backend + frontend)

## 🧠 Semantic Policy Scanning

AI-powered semantic policy validation using local LLMs via **Ollama**:

- **8 Semantic Policies**: Context-aware validation beyond rule-based patterns
- **Local LLM Execution**: Privacy-first with Ollama (no data leaves your infrastructure)
- **Smart Detection**: Identifies sensitive data based on context, not just naming patterns
- **Business Logic Validation**: Ensures governance rules make business sense
- **Security Pattern Recognition**: Detects vulnerabilities in schema design

📖 **See [SEMANTIC_SCANNING.md](./data-governance-platform/SEMANTIC_SCANNING.md) for complete guide**

## 🎯 Policy Orchestration

An **intelligent orchestration layer** that automatically decides when to use rule-based vs LLM-based validation:

- **4 Validation Strategies**: FAST, BALANCED, THOROUGH, ADAPTIVE
- **Risk Assessment**: Analyzes contracts to determine risk level (LOW → CRITICAL)
- **Smart Routing**: Automatically chooses optimal validation based on data characteristics
- **Performance Optimized**: Avoids expensive LLM calls when not needed (100ms vs 24s)
- **Production Ready**: Used in all contract validation workflows

**Example**: Low-risk internal data → FAST (rule-based only, 100ms). Critical PII with GDPR → THOROUGH (all policies, 24s).

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
