# Automated Data Controls Platform (ADCP)
### Policy-as-Code Enforcement Layer for Financial Data Governance

> **Governance defines the rules. This platform makes them enforceable.**

---

## Overview

The **Automated Data Controls Platform** is a proof-of-concept **enforcement and observability layer** that operationalises data governance policies into automated controls applied at data borders.

It is not a governance framework. Governance — data ownership, stewardship accountability, policy authoring, and domain glossary alignment — belongs with your data councils and stewards. This platform is the technical layer that ensures those decisions are actually enforced, consistently, at scale, and with an auditable trail.

The design follows a **federated enforcement model** — shared policies with distributed validation — where prevention at borders is more effective than retrospective detection. It demonstrates how a regulated financial institution can automate the operationalisation of governance policy without displacing the human accountability structures that governance requires.

Built with regulated financial institutions in mind, targeting alignment with **BCBS 239**, **DORA**, **GDPR Article 25**, and **EU AI Act** obligations.

---

## What Problem This Solves

In most organisations, data governance policies exist as documents. Controls are manually applied, inconsistently enforced, and difficult to audit. The gap between a policy statement and a running data pipeline is where regulatory risk accumulates.

This platform closes that gap by:

- Encoding approved governance decisions as executable, version-controlled policies
- Evaluating those policies automatically at every data movement event — before data crosses a domain boundary
- Generating an auditable trail of every enforcement decision, tied to the policy version that triggered it
- Providing actionable remediation guidance when a violation is detected, rather than a bare rejection

---

## Key Capabilities

### Enforcement Engine
- **25 governance policies**: 17 rule-based (sensitive data, data quality, schema governance) + 8 semantic (LLM-assisted)
- **Intelligent orchestration**: Automatically routes validation to rule-based or LLM engine based on assessed risk level — avoids expensive LLM calls when not warranted (100ms vs 24s)
- **4 validation strategies**: FAST, BALANCED, THOROUGH, ADAPTIVE — matched to contract risk profile
- **Prevention at borders**: Policies evaluated before data crosses domain boundaries, not discovered in retrospect

### Contract Management
- **Dual-format contracts**: Human-readable YAML for stewards and business owners; machine-readable JSON for system integration
- **Git-backed versioning**: Every contract change committed with semantic versioning — full lineage of policy decisions
- **Automated schema import**: PostgreSQL schema ingestion with heuristic PII detection

### Semantic Policy Scanning (Experimental)
- **8 semantic policies** using local Ollama LLM execution — no data leaves the infrastructure
- Context-aware validation beyond pattern matching: business logic coherence, schema vulnerability patterns, sensitive data in context
- **All LLM recommendations require human steward review before enforcement** — this layer is advisory, not autonomous

### Multi-Role Operational Interface

| Role | Capability |
|---|---|
| **Data Owner** | Dataset registration, schema import, violation dashboard with remediation guidance |
| **Data Consumer** | Catalog browsing, access requests, SLA negotiation |
| **Data Steward** | Approval queue, contract review, credential management |
| **Platform Admin** | Compliance dashboard, violation trends, policy analytics |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  Governance Layer  (Human)                   │
│     Data Council · Stewardship Model · Policy Authoring      │
│     Business Glossary · Ownership & Accountability           │
└───────────────────────────┬──────────────────────────────────┘
                            │  Approved policies (YAML)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              Policy Management API  (FastAPI)                │
│      Policy Registry · Version Control · Approval Workflow   │
│      12 API routers · 78 endpoints                           │
└──────┬───────────────────────────────────────────┬───────────┘
       │                                           │
       ▼                                           ▼
┌─────────────────┐                     ┌─────────────────────┐
│  Policy Engine  │                     │  Audit & Contracts  │
│                 │                     │                     │
│  Rule-based     │                     │  Git-versioned      │
│  17 policies    │                     │  contracts          │
│                 │                     │                     │
│  Semantic       │                     │  Immutable event    │
│  8 policies     │                     │  trail              │
│  (LLM-assisted, │                     │                     │
│  human-reviewed)│                     │  PostgreSQL +       │
└────────┬────────┘                     │  SQLite metadata    │
         │                              └─────────────────────┘
         ▼
┌──────────────────────────────────────────────────────────────┐
│                    Enforcement Points                        │
│    Data Contract Validation · Schema Import Gates            │
│    Subscription Approval · Classification Controls           │
│    Violation Detection + Remediation Guidance                │
└──────────────────────────────────────────────────────────────┘
```

---

## Regulatory Alignment

| Regulation | How This Platform Supports Compliance |
|---|---|
| **BCBS 239** | Automated data quality controls at ingestion; policy-gated lineage at domain borders; contract versioning as accuracy evidence |
| **DORA** | ICT risk controls embedded in data pipeline; policy validation in CI/CD; resilience through orchestration strategies |
| **GDPR Art. 25** | Privacy-by-design enforced at registration — PII detection gates schema import; data minimisation in subscription SLA workflow |
| **EU AI Act** | LLM scoped to advisory suggestions only; mandatory human-in-the-loop before any AI-assisted recommendation takes effect; local execution — no external data transfer |

> **Note on the AI component:** The semantic scanning layer (Ollama/Mistral) is explicitly scoped as an advisory tool. It operates locally, produces no autonomous enforcement decisions, and all outputs require steward review before acting. This scoping is intentional — it keeps the component outside the EU AI Act's high-risk classification threshold for financial institutions.

---

## Technology Stack

**Backend**
- FastAPI 0.109 (Python 3.10+)
- SQLAlchemy 2.0 / PostgreSQL 15 + SQLite
- Pydantic v2 (contract validation)
- GitPython (policy and contract versioning)
- Ollama + Mistral (local LLM — semantic scanning only)
- PyYAML (policy definitions)

**Frontend**
- React 18.2 + Vite 5.0
- Zustand 4.4 (state management)
- Recharts 2.10 (compliance analytics)
- React Router 6 / Axios 1.6

---

## Quick Start

**Prerequisites:** Python 3.10+, Node.js 18+, Docker, Git

```bash
# 1. Clone repository
git clone https://github.com/Ra-joseph/Data-governace-using-PoC.git
cd Data-governace-using-PoC/data-governance-platform

# 2. Start PostgreSQL
docker-compose up -d

# 3. Backend
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4. Frontend (new terminal)
cd frontend && npm install && npm run dev
```

| Interface   | URL                              |
|-------------|----------------------------------|
| Frontend    | http://localhost:3000            |
| Backend API | http://localhost:8000            |
| API Docs    | http://localhost:8000/api/docs   |

---

## Demo Scenario

The platform ships with a financial services demo database containing three tables with intentional governance violations:
- `customer_accounts` — PII violations (unmasked fields, missing classification)
- `transactions` — Data quality failures (nullability, threshold breaches)
- `fraud_alerts` — Missing governance metadata (thresholds, retention policy)

Use these to walk through the full enforcement workflow: registration → violation detection → remediation → steward approval → contract versioning.

---

## Enforcement Workflows

**Dataset Registration (Owner → System)**
```
Register dataset → Import schema → PII detection gate →
Policy evaluation → Contract generation → Git commit → Violation report + remediation
```

**Data Subscription (Consumer → Steward → System)**
```
Browse catalog → Request access + SLA definition →
Steward review → Approve/reject → Credential issuance →
Contract version bump → Git commit
```

**Violation Remediation (Owner → System)**
```
View violation alert → Read remediation guidance →
Fix dataset → Re-submit → Re-validate → Contract cleared
```

---

## Project Structure

```
Data-governace-using-PoC/
└── data-governance-platform/
    ├── backend/
    │   ├── app/
    │   │   ├── api/          # 12 routers, 78 endpoints
    │   │   ├── models/       # 8 SQLAlchemy models
    │   │   ├── schemas/      # 41 Pydantic schemas
    │   │   └── services/     # 10 services (policy engine, orchestrator, git, semantic, ODPS)
    │   ├── policies/         # YAML policy definitions (25 policies, 4 files)
    │   ├── contracts/        # Git-versioned contract repository
    │   └── tests/            # 26 test files
    └── frontend/
        └── src/
            ├── pages/        # Role-based UIs (Owner, Consumer, Steward, Admin)
            ├── components/
            ├── services/     # Axios API client
            └── stores/       # Zustand state management
```

---

## Documentation Index

| Document | Purpose |
|---|---|
| [Usage Guide](data-governance-platform/USAGE_GUIDE.md) | Start here — setup, dependency layers, role demo flows |
| [Platform README](data-governance-platform/README.md) | Architecture, API docs, full workflow reference |
| [Quick Start](data-governance-platform/QUICKSTART.md) | 5-minute setup |
| [Project Summary](data-governance-platform/PROJECT_SUMMARY.md) | Design decisions and technical deep-dive |
| [Semantic Scanning](data-governance-platform/SEMANTIC_SCANNING.md) | LLM-assisted policy validation guide |
| [Policy Orchestration](data-governance-platform/POLICY_ORCHESTRATION.md) | Validation routing and strategy selection |
| [Testing Guide](data-governance-platform/TESTING.md) | Test suite documentation |
| [Deployment Guide](data-governance-platform/DEPLOYMENT.md) | Production deployment |

---

## Current Status

| Component | Status |
|---|---|
| Backend API (FastAPI, 78 endpoints) | ✅ Complete |
| Policy Engine (25 policies: 17 rule-based + 8 semantic) | ✅ Complete |
| Semantic Scanning (Ollama, local LLM) | ✅ Complete |
| Policy Orchestration (FAST / BALANCED / THOROUGH / ADAPTIVE) | ✅ Complete |
| Schema Import with PII detection | ✅ Complete |
| Contract Management (YAML + JSON dual-format) | ✅ Complete |
| Git Integration (versioned audit trail) | ✅ Complete |
| Multi-Role Frontend (Owner, Consumer, Steward, Admin) | ✅ Complete |
| Subscription Workflow (end-to-end with SLA negotiation) | ✅ Complete |
| Compliance Dashboard (interactive analytics) | ✅ Complete |
| Test Suite (backend + frontend) | ✅ Complete |
| ODPS (Open Data Product Standard) connector | ✅ Complete |

---

## Roadmap

- Authentication & Authorisation (OAuth2/JWT)
- Additional source connectors (Azure Data Lake, Snowflake, S3)
- Data lineage tracking across enforcement points
- Real-time monitoring and alerting (Slack/email)
- OPA/Rego integration for external policy evaluation

---

## Production Caveats

This is a proof-of-concept. For deployment in a regulated financial institution, the following are required:
- Proper authentication and secret management
- Tamper-evident audit logging (the Git trail here is demonstrative — production requires write-once logging)
- Formal model card and bias audit for the LLM component before scope expansion
- Integration with existing stewardship and DORA operational resilience frameworks
- Rate limiting, error handling, and production database hardening

---

*Proof-of-concept for portfolio and demonstration purposes. Built to illustrate enforcement-layer architecture for regulated data environments.*
