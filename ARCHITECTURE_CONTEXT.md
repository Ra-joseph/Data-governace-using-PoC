# Data Governance Platform — Architecture Context

> Auto-generated from codebase scan on 2026-03-11.
> Use this file as the authoritative reference for the platform's architecture, components, and data flows.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [User Roles](#3-user-roles)
4. [Frontend Architecture](#4-frontend-architecture)
5. [Backend API Layer](#5-backend-api-layer)
6. [Service Layer](#6-service-layer)
7. [Policy System](#7-policy-system)
8. [Data Storage](#8-data-storage)
9. [External Systems](#9-external-systems)
10. [Data Flow Narratives](#10-data-flow-narratives)
11. [Key File Index](#11-key-file-index)
12. [Environment Configuration](#12-environment-configuration)

---

## 1. Project Overview

The **Data Governance Platform** is a production-ready proof-of-concept implementing federated data governance using the UN Peacekeeping model: shared policies with distributed enforcement.

**Core value proposition:** Prevent governance violations *before* they reach production by validating data contracts at publication time.

**Key capabilities:**
- Policy-as-Code: YAML-defined governance policies
- Automated rule-based validation (17 deterministic policies)
- LLM-powered semantic validation (8 context-aware policies via Ollama)
- Intelligent routing between validation strategies based on data risk
- End-to-end subscription workflow with contract auto-generation
- Git-versioned data contracts for full audit trail
- Multi-role UI: Data Owners, Consumers, Stewards, Platform Admins

---

## 2. Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.109.0 |
| Metadata DB | SQLite | bundled |
| Demo DB | PostgreSQL | 15-alpine |
| ORM | SQLAlchemy | 2.0.25 |
| Validation | Pydantic v2 | 2.5.3 |
| Config | pydantic-settings | 2.1.0 |
| Git integration | GitPython | 3.1.41 |
| Policy files | PyYAML | 6.0.1 |
| LLM client | Ollama (local) | — |
| HTTP | httpx | 0.26.0 |
| Server | uvicorn[standard] | 0.27.0 |
| Testing | pytest | 7.4.4 |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | React | 18.2.0 |
| Build tool | Vite | 5.0.8 |
| State | Zustand | 4.4.7 |
| HTTP client | Axios | 1.6.2 |
| Routing | React Router | 6.21.0 |
| Charts | Recharts | 2.10.3 |
| Animation | Framer Motion | 10.16.16 |
| Icons | Lucide React | 0.303.0 |

---

## 3. User Roles

The platform supports four distinct user roles, each with a dedicated UI and API surface:

| Role | Route Prefix | Primary Responsibilities |
|------|-------------|------------------------|
| **Data Owner** | `/owner/*` | Register datasets, define schemas, monitor governance violations |
| **Data Consumer** | `/consumer/*` | Browse the catalog, subscribe to datasets, view approved contracts |
| **Data Steward** | `/steward/*` | Review subscription requests, approve/reject, manage contracts |
| **Platform Admin** | `/admin/*` | Monitor platform-wide compliance metrics and analytics |

**Auth implementation:** `AuthContext.jsx` holds the current user's role. `RoleSelector.jsx` (landing page) simulates authentication for the PoC — no backend auth is required.

---

## 4. Frontend Architecture

**Entry point:** `frontend/src/main.jsx` → `App.jsx` (React Router v6)
**Dev server:** Vite on port 3000, proxies `/api` → `http://localhost:8000`

### Route Structure

```
/select-role                    RoleSelector (landing)

/owner/*                        Layout.jsx (sidebar)
  /owner/dashboard              OwnerDashboard
  /owner/register               DatasetRegistrationWizard (4-step)
  /owner/datasets/:id           DatasetDetail

/consumer/*                     Layout.jsx (sidebar)
  /consumer/catalog             DataCatalogBrowser
  /consumer/datasets/:id        DatasetDetail

/steward/*                      Layout.jsx (sidebar)
  /steward/approvals            ApprovalQueue
  /steward/contracts/:id        ContractViewer

/admin/*                        Layout.jsx (sidebar)
  /admin/dashboard              Admin ComplianceDashboard (Recharts)
  /admin/compliance             Compliance Reports

/policy-authoring               TopNavLayout.jsx (legacy top nav)
/policy-authoring/new           PolicyForm
/policy-authoring/:id           PolicyDetail
/policy-review                  PolicyReview
/policy-dashboard               PolicyDashboard
/compliance-report              ComplianceReport
/policy-exchange                PolicyExchange
/domain-governance              DomainGovernance
/policy-conflicts               PolicyConflicts
```

### Key Components

| Component | Purpose |
|-----------|---------|
| `Layout.jsx` | Sidebar nav — role-aware menu, user profile, logout |
| `TopNavLayout.jsx` | Top nav — multi-level groups for legacy/policy routes |
| `ErrorBoundary.jsx` | Catches render errors, shows friendly UI |
| `SkeletonLoader.jsx` | Shimmer loading placeholders (stat, card, row, chart types) |
| `EmptyState.jsx` | Empty state with optional CTA button |
| `CopyButton.jsx` | Copy-to-clipboard with visual feedback |

### State Management

All cross-page state lives in Zustand stores (`stores/index.js`):

| Store | State | Key Actions |
|-------|-------|------------|
| `useDatasetStore` | datasets[], currentDataset | add, update, remove dataset |
| `useContractStore` | contracts[], validationResult | set contract, set validation |
| `useSubscriptionStore` | subscriptions[], currentSubscription | approve, reject (optimistic) |
| `usePolicyStore` | policies {} | set policies |
| `useGitStore` | history[], contracts[], currentDiff | set history, set diff |

### API Client

All HTTP calls go through `services/api.js` (single Axios instance):
- Base URL: `http://localhost:8000`
- Auth token auto-injected from localStorage
- 401 → auto-logout + redirect
- Namespaced API groups: `datasetAPI`, `contractAPI`, `subscriptionAPI`, `policyAPI`, `gitAPI`, `policyAuthoringAPI`, `policyDashboardAPI`, `policyReportsAPI`, `policyExchangeAPI`, `domainGovernanceAPI`, `policyExceptionsAPI`

---

## 5. Backend API Layer

**Framework:** FastAPI — `backend/app/main.py`
**Port:** 8000
**URL prefix:** `/api/v1` (all routers)
**Docs:** `http://localhost:8000/docs` (Swagger), `/redoc` (ReDoc)

### Registered Routers

| Router File | Prefix | Key Endpoints |
|-------------|--------|--------------|
| `datasets.py` | `/api/v1/datasets` | CRUD, `POST /import-schema`, `GET /postgres/tables` |
| `subscriptions.py` | `/api/v1/subscriptions` | CRUD, `POST /{id}/approve`, `PUT /{id}` |
| `git.py` | `/api/v1/git` | `GET /history`, `GET /contracts`, `GET /diff`, `GET /contract/{dataset}/{version}` |
| `semantic.py` | `/api/v1/semantic` | `GET /health`, `GET /policies`, `POST /validate`, `GET /models` |
| `orchestration.py` | `/api/v1/orchestration` | `GET /strategies`, `POST /analyze`, `POST /validate` |
| `policy_authoring.py` | `/api/v1/policies/authored` | Full lifecycle: create → submit → approve/reject |
| `policy_dashboard.py` | `/api/v1/policy-dashboard` | `GET /stats`, `POST /validate-combined` |
| `policy_reports.py` | `/api/v1/policy-reports` | `GET /impact/{id}`, `GET /compliance-overview`, `POST /bulk-validate` |
| `policy_exchange.py` | `/api/v1/policy-exchange` | `POST /export`, `POST /import`, `GET /templates` |
| `domain_governance.py` | `/api/v1/domain-governance` | `GET /domains`, `GET /matrix`, `GET /effectiveness` |
| `policy_conflicts.py` | `/api/v1/policy-exceptions` | Exception management: detect, list, create, approve/reject |

### Layered Architecture Pattern

```
HTTP Request
    → FastAPI Router  (api/)        ← thin: validate input, call service, return
    → Service Layer   (services/)   ← all business logic
    → ORM Models      (models/)     ← pure SQLAlchemy, no logic
    → Database        (SQLite)
           ↕
       Policy YAML    (policies/)   ← loaded at startup by PolicyEngine
```

---

## 6. Service Layer

All business logic lives in `backend/app/services/`.

| Service | LoC | Responsibility |
|---------|-----|----------------|
| `contract_service.py` | 481 | Contract generation, validation, Git versioning, version management |
| `policy_engine.py` | 342 | Rule-based validation of 17 deterministic policies |
| `policy_orchestrator.py` | 538 | Intelligent routing (FAST/BALANCED/THOROUGH/ADAPTIVE), risk scoring |
| `semantic_policy_engine.py` | 461 | LLM-based evaluation of 8 semantic policies via Ollama |
| `git_service.py` | 317 | Git operations: commit, retrieve, history, diff, tags |
| `postgres_connector.py` | 557 | Demo DB schema introspection and PII detection |
| `ollama_client.py` | 237 | HTTP client for local Ollama (with caching, retry, JSON format) |
| `authored_policy_loader.py` | 258 | Load and validate authored policies from SQLite |
| `policy_converter.py` | 204 | YAML ↔ JSON format conversion for policy artifacts |

### Contract Service Flow

```
ContractService.create_contract_from_dataset(db, dataset_id, version)
  │
  ├─ 1. Fetch dataset from SQLite
  ├─ 2. Build contract_data JSON structure
  │      └─ schema, governance rules, compliance tags, encryption flags
  ├─ 3. Validate via PolicyOrchestrator
  │      └─ Returns ValidationResult (PASSED | WARNING | FAILED)
  ├─ 4. Commit YAML to Git (GitService)
  │      └─ backend/contracts/{dataset_name}_v{version}.yaml
  └─ 5. Persist Contract record to SQLite
         └─ Stores: git_commit_hash, validation_results, schema_hash
```

---

## 7. Policy System

### Rule-Based Policies (Deterministic)

Stored in `backend/policies/*.yaml`. Loaded at startup by `PolicyEngine`.

| File | Policy IDs | Count | Focus |
|------|-----------|-------|-------|
| `sensitive_data_policies.yaml` | SD001–SD005 | 5 | PII, encryption, masking, retention, cross-border |
| `data_quality_policies.yaml` | DQ001–DQ005 | 5 | Completeness, freshness, uniqueness, accuracy, quality tiers |
| `schema_governance_policies.yaml` | SG001–SG007 | 7 | Field documentation, naming, ownership, consistency |

**Total: 17 deterministic policies**

### Semantic Policies (LLM-Powered)

Stored in `backend/policies/semantic_policies.yaml`. Evaluated by `SemanticPolicyEngine` via Ollama.

| Policy ID | Focus |
|-----------|-------|
| SEM001 | Sensitive data context detection |
| SEM002 | Business logic consistency |
| SEM003 | Security pattern detection |
| SEM004 | Compliance intent verification |
| SEM005–SEM008 | Naming conventions, documentation quality, SLA feasibility, data lineage |

**Total: 8 semantic policies** (disabled by default; set `ENABLE_LLM_VALIDATION=true` to enable)

### Orchestration Strategies

`PolicyOrchestrator` routes validation based on risk assessment:

```
Contract Analysis → Risk Scoring → Strategy Selection → Execution → Result Combining
```

| Strategy | Rule-Based | Semantic | Trigger Condition | Est. Time |
|----------|-----------|----------|-------------------|-----------|
| **FAST** | ✓ | — | Low risk, no PII, complexity < 30 | ~0.1s |
| **BALANCED** | ✓ | Targeted | Moderate risk; selected SEM policies | ~0.1s + N×3s |
| **THOROUGH** | ✓ | All 8 | High risk, PII, ≥2 compliance frameworks | ~24s |
| **ADAPTIVE** | auto | auto | Default — auto-selects based on risk level | varies |

**Risk levels:** LOW → FAST, MEDIUM → BALANCED, HIGH/CRITICAL → THOROUGH

---

## 8. Data Storage

### SQLite — Metadata Database

**Path:** `backend/governance_metadata.db`
**Purpose:** All platform metadata (datasets, contracts, subscriptions, users, policy authoring)

| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `datasets` | id, name, owner, schema, classification, contains_pii, status | Data asset catalog |
| `contracts` | id, dataset_id, version, human_readable, machine_readable, git_commit_hash, validation_status | Versioned data contracts |
| `subscriptions` | id, dataset_id, contract_id, consumer, purpose, sla_*, status | Consumer access requests |
| `users` | id, email, username, role, team | Platform users |
| `policy_drafts` | id, title, category, severity, status, authored_by | Authored governance policies |
| `policy_versions` | id, policy_id, version_number, change_log | Policy version history |
| `policy_artifacts` | id, policy_id, yaml_content, json_content, git_commit_hash | Generated policy files |
| `policy_approval_logs` | id, policy_id, action, decided_by, comments | Approval audit trail |

**Seed data:** 5 sample datasets loaded on first startup (customer_accounts, transaction_ledger, product_catalog, employee_directory, web_analytics_events).

### Git Repository — Contract Versioning

**Path:** `backend/contracts/`
**Purpose:** Full audit trail of all data contract versions

- Auto-initialized as a Git repo on first startup
- Each contract approval creates a new commit: `{dataset_name}_v{version}.yaml`
- Supports: version history, diff between versions, tagged releases
- Managed entirely by `GitService` — **do not edit manually**

### PostgreSQL — Demo Database (Optional)

**Port:** 5432
**Database:** `financial_demo`
**Credentials:** `governance_user` / `governance_pass`
**Purpose:** Demo source database for schema import feature

- Started via `docker-compose up -d`
- Pre-populated with `demo/setup_postgres.sql` + `demo/sample_data.sql`
- Used by `PostgresConnector` for schema introspection and PII detection
- **Not required for core platform functionality**

---

## 9. External Systems

| System | Port | Purpose | Required | Fallback |
|--------|------|---------|----------|---------|
| **SQLite** | N/A (in-process) | Primary metadata store | **Required** | Platform fails |
| **Git** | N/A (local) | Contract versioning | **Required** | Contracts not versioned |
| **PostgreSQL** | 5432 | Demo DB for schema import | Optional | Schema import unavailable |
| **Ollama** | 11434 | LLM inference (mistral:7b) | Optional | Falls back to rule-based only |

### Ollama Integration

- Called by `OllamaClient` → `SemanticPolicyEngine`
- Model: `mistral:7b` (configurable via `OLLAMA_MODEL`)
- Temperature: 0.1 (near-deterministic for consistent results)
- Response caching by prompt hash
- Retry: up to 3 attempts on failure
- Timeout: 30 seconds per request
- Disabled by default (`ENABLE_LLM_VALIDATION=False`)

---

## 10. Data Flow Narratives

### Flow 1: Dataset Registration (Data Owner)

```
1. Data Owner opens DatasetRegistrationWizard (4 steps)
2. Fills: dataset name, description, schema, classification, PII fields, compliance tags
3. Frontend: datasetAPI.create(payload) → POST /api/v1/datasets
4. Router: datasets.py calls ContractService
5. ContractService:
   a. Builds contract_data from dataset fields
   b. Validates via PolicyOrchestrator (ADAPTIVE strategy)
   c. PolicyEngine validates 17 deterministic rules
   d. SemanticPolicyEngine validates (if enabled + risk warrants it)
   e. Commits contract YAML to Git (backend/contracts/)
   f. Persists Dataset + Contract records to SQLite
6. Response: dataset ID, validation_status, violations (if any)
7. Frontend: shows validation summary with remediation guidance
```

### Flow 2: Subscription + Approval (Consumer + Steward)

```
1. Data Consumer: DataCatalogBrowser → finds dataset → clicks Subscribe
2. Frontend: subscriptionAPI.create(payload) → POST /api/v1/subscriptions
3. Backend: Subscription record created (status=pending) in SQLite
4. Data Steward: ApprovalQueue shows pending requests
5. Steward reviews → clicks Approve
6. Frontend: subscriptionAPI.approve(id, {sla_freshness, ...}) → POST /api/v1/subscriptions/{id}/approve
7. Backend:
   a. Subscription status → approved
   b. ContractService.add_subscription_to_contract() creates new contract version (1.0.0 → 1.1.0)
   c. New version committed to Git
   d. Consumer access credentials generated
8. Contract now includes subscriber SLA requirements
```

### Flow 3: Policy Validation (Orchestration)

```
POST /api/v1/orchestration/validate (contract_data, strategy=ADAPTIVE)
   │
   PolicyOrchestrator.validate_contract(contract_data)
      │
      ├─ _analyze_contract() → has_pii, classification, compliance_frameworks, complexity_score
      ├─ _score_risk() → LOW | MEDIUM | HIGH | CRITICAL
      ├─ _make_orchestration_decision() → strategy, semantic_policies, estimated_time
      │
      ├─ [Always] PolicyEngine.validate_contract()
      │    └─ Run SD001-005, DQ001-005, SG001-007 deterministically from YAML rules
      │
      └─ [Conditional] SemanticPolicyEngine.validate_contract()
           └─ For each selected SEM policy:
                OllamaClient.generate(prompt, system_prompt)
                POST http://localhost:11434/api/generate
                    model=mistral:7b, temperature=0.1, format=json
                └─ Parse LLM response → violations
      │
      _combine_results() → deduplicate, prioritize by severity
      └─ Return ValidationResult {status, passed, warnings, failures, violations, metadata}
```

### Flow 4: Contract Git Versioning

```
Every contract write:
   GitService.commit_contract(yaml_content, dataset_name, version)
      ├─ Write {dataset_name}_v{version}.yaml to backend/contracts/
      ├─ git add {filename}
      ├─ git commit -m "..." --author="Data Governance Platform <governance@company.com>"
      └─ Return {commit_hash, file_path, timestamp}

History retrieval:
   GET /api/v1/git/history → GitService.get_commit_history()
   GET /api/v1/git/contracts → GitService.list_contracts()
   GET /api/v1/git/diff?c1={hash}&c2={hash} → GitService.get_diff()
```

---

## 11. Key File Index

| File | Role |
|------|------|
| `backend/app/main.py` | FastAPI app factory; registers all 11 routers, CORS, startup |
| `backend/app/config.py` | Pydantic Settings; all env vars with defaults |
| `backend/app/database.py` | SQLAlchemy engine, session, table init, seed data |
| `backend/app/services/contract_service.py` | Core contract generation and versioning (481 LoC) |
| `backend/app/services/policy_engine.py` | Rule-based YAML policy validation (342 LoC) |
| `backend/app/services/policy_orchestrator.py` | Intelligent routing and risk scoring (538 LoC) |
| `backend/app/services/semantic_policy_engine.py` | LLM semantic validation (461 LoC) |
| `backend/app/services/git_service.py` | Git contract operations (317 LoC) |
| `backend/app/services/postgres_connector.py` | PostgreSQL schema introspection (557 LoC) |
| `backend/app/services/ollama_client.py` | Ollama HTTP client with cache and retry (237 LoC) |
| `backend/policies/sensitive_data_policies.yaml` | SD001-SD005 policies |
| `backend/policies/data_quality_policies.yaml` | DQ001-DQ005 policies |
| `backend/policies/schema_governance_policies.yaml` | SG001-SG007 policies |
| `backend/policies/semantic_policies.yaml` | SEM001-SEM008 LLM policies |
| `frontend/src/App.jsx` | Root router; all route definitions |
| `frontend/src/services/api.js` | Single Axios client; all API call functions |
| `frontend/src/stores/index.js` | Zustand global stores (5 stores) |
| `frontend/src/contexts/AuthContext.jsx` | Role-based auth context |
| `frontend/src/components/Layout.jsx` | Sidebar nav layout (role-aware) |
| `frontend/src/components/TopNavLayout.jsx` | Top navigation layout (legacy routes) |
| `data-governance-platform/docker-compose.yml` | PostgreSQL 15 container definition |
| `data-governance-platform/start.sh` | Quick-start: docker → backend |

---

## 12. Environment Configuration

All settings in `backend/app/config.py` (Pydantic `BaseSettings`). Override via `backend/.env`.

| Variable | Default | Notes |
|----------|---------|-------|
| `SQLALCHEMY_DATABASE_URL` | `sqlite:///governance_metadata.db` | Metadata storage |
| `POSTGRES_HOST` | `localhost` | Demo DB |
| `POSTGRES_PORT` | `5432` | Demo DB |
| `POSTGRES_DB` | `financial_demo` | Demo DB name |
| `POSTGRES_USER` | `governance_user` | Demo DB |
| `POSTGRES_PASSWORD` | `governance_pass` | Demo DB |
| `GIT_CONTRACTS_REPO_PATH` | `backend/contracts` | Contract Git repo |
| `GIT_USER_NAME` | `Data Governance Platform` | Git author name |
| `GIT_USER_EMAIL` | `governance@company.com` | Git author email |
| `POLICIES_PATH` | `backend/policies` | YAML policy directory |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |
| `DEBUG` | `True` | FastAPI debug mode |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |
| `ENABLE_LLM_VALIDATION` | `False` | Enable Ollama semantic validation |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `mistral:7b` | LLM model name |
| `OLLAMA_TIMEOUT` | `30` | Ollama request timeout (seconds) |

---

*Generated by Claude Code — Data Governance Platform PoC.*
