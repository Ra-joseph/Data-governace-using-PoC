# Data Governance Platform - Policy-as-Code PoC

Enabling proactive data governance using Policy-as-Code with a comprehensive multi-role frontend.

## 🎯 Overview

A production-ready proof-of-concept demonstrating federated data governance using the **UN Peacekeeping model** - shared policies with distributed enforcement. This platform prevents governance violations before they reach production through automated policy validation and actionable remediation.

## ✨ Key Features

### Backend
- **17 Governance Policies**: Sensitive data, data quality, and schema governance
- **8 Semantic Policies (NEW!)**: LLM-powered context-aware validation with local Ollama
- **Automated Schema Import**: PostgreSQL with PII detection
- **Dual Contracts**: Human-readable YAML + Machine-readable JSON
- **Git Version Control**: Full audit trail for all contracts
- **Policy Validation**: Real-time validation with actionable remediation

### Frontend (NEW!)
- **Data Owner UI**: Dataset registration wizard with multi-step form
- **Data Consumer UI**: Catalog browser with subscription requests
- **Data Steward UI**: Approval queue with contract review
- **Platform Admin UI**: Compliance dashboard with analytics
- **End-to-End Workflows**: Complete subscription lifecycle

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
    │   │   ├── api/          # REST endpoints
    │   │   ├── models/       # Database models
    │   │   ├── services/     # Business logic
    │   │   └── main.py       # FastAPI app
    │   ├── policies/         # YAML policy definitions
    │   └── contracts/        # Git repository
    ├── frontend/             # React frontend
    │   ├── src/
    │   │   ├── pages/        # Role-based UIs
    │   │   ├── contexts/     # Auth context
    │   │   └── services/     # API client
    │   └── package.json
    ├── demo/                 # Demo database
    └── README.md            # Detailed documentation
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
- FastAPI (Python 3.10+)
- SQLAlchemy 2.0
- PostgreSQL
- Pydantic v2
- GitPython

**Frontend:**
- React 18.2
- Vite
- Zustand (state management)
- Recharts (analytics)
- React Router 6
- Axios

## 🎯 Demo Scenario

The platform includes a financial services demo with three tables:
1. **customer_accounts**: Contains PII with intentional violations
2. **transactions**: Financial transactions with quality issues
3. **fraud_alerts**: Fraud detection data with missing thresholds

Use these tables to test the full workflow from registration to subscription approval.

## ✅ Current Status

- ✅ Backend API (FastAPI)
- ✅ Policy Engine (17 policies)
- ✅ Schema Import (PostgreSQL)
- ✅ Contract Management
- ✅ Git Integration
- ✅ Multi-Role Frontend
- ✅ Subscription Workflow
- ✅ Compliance Dashboard
- ✅ Violation Tracking
- ✅ **Semantic Policy Scanning (LLM-powered)**

## 🆕 Semantic Scanning (NEW!)

The platform now supports AI-powered semantic policy validation using local LLMs via **Ollama**:

- **8 Semantic Policies**: Context-aware validation beyond rule-based patterns
- **Local LLM Execution**: Privacy-first with Ollama (no data leaves your infrastructure)
- **Smart Detection**: Identifies sensitive data based on context, not just naming patterns
- **Business Logic Validation**: Ensures governance rules make business sense
- **Security Pattern Recognition**: Detects vulnerabilities in schema design

📖 **See [SEMANTIC_SCANNING.md](./data-governance-platform/SEMANTIC_SCANNING.md) for complete guide**

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
