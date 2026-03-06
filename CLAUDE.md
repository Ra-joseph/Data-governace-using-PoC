# CLAUDE.md — AI Assistant Guide for Data Governance Platform

This file documents the codebase structure, development conventions, and workflows for AI assistants (Claude Code and similar tools) working on this repository.

---

## Project Overview

**Data Governance Platform — Policy-as-Code PoC**

A production-ready proof-of-concept implementing federated data governance using the UN Peacekeeping model (shared policies with distributed enforcement). The platform prevents governance violations _before_ they reach production by validating data contracts at publication time.

**Core capabilities:**
- **Policy-as-Code**: YAML-defined governance policies with automated rule-based and LLM-powered validation
- **Prevention at Borders**: Contracts validated before publication; violations surfaced with actionable remediation guidance
- **Intelligent Orchestration**: Four routing strategies (FAST, BALANCED, THOROUGH, ADAPTIVE) that select rule-based vs. semantic validation based on risk
- **End-to-End Subscription Workflow**: Data Owners register datasets → Data Consumers subscribe → Data Stewards approve → Contracts auto-generated and Git-versioned
- **Multi-Role Frontend**: Dedicated React UIs for Data Owners, Consumers, Stewards, and Platform Admins

---

## Repository Layout

```
Data-governace-using-PoC/               ← repo root
├── CLAUDE.md                           ← this file
├── README.md                           ← project overview & quick start
├── CONTRIBUTING.md                     ← contribution guidelines
├── MEDIUM_ARTICLE.md                   ← publication article
├── TEST_RESULTS.md                     ← latest test run results
├── .claude/
│   └── skills/
│       └── test-and-fix.md             ← Claude skill: run tests & suggest fixes
└── data-governance-platform/           ← main platform directory
    ├── README.md                       ← complete platform guide
    ├── QUICKSTART.md                   ← 5-minute setup
    ├── USAGE_GUIDE.md                  ← detailed setup & role workflows
    ├── PROJECT_SUMMARY.md              ← technical deep-dive
    ├── DEPLOYMENT.md                   ← production deployment
    ├── TESTING.md                      ← test suite docs
    ├── FRONTEND_GUIDE.md               ← frontend architecture
    ├── SEMANTIC_SCANNING.md            ← LLM policy guide
    ├── POLICY_ORCHESTRATION.md         ← orchestration strategies
    ├── FULL_STACK_INVENTORY.md         ← complete file inventory
    ├── MANIFEST.md                     ← project manifest
    ├── DIRECTORY_TREE.txt              ← auto-generated file listing
    ├── docker-compose.yml              ← PostgreSQL 15 demo DB
    ├── start.sh                        ← quick-start script
    ├── test_setup.py                   ← automated setup test suite
    ├── backend/                        ← FastAPI backend
    ├── frontend/                       ← React + Vite frontend
    ├── demo/                           ← SQL setup & sample data
    └── examples/                       ← example API payloads
```

---

## Technology Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI | 0.109.0 |
| Metadata DB | SQLite | (bundled) |
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
| Testing | Vitest + RTL | 1.0.4 / 14.1.2 |
| Linting | ESLint | 8.55.0 |

---

## Backend Architecture

```
backend/
├── app/
│   ├── main.py          ← FastAPI app factory; registers all routers, sets CORS
│   ├── config.py        ← Pydantic Settings; all env vars with defaults
│   ├── database.py      ← SQLAlchemy engine, session, DB init & seed data
│   ├── api/             ← Route handlers (thin — delegate to services)
│   │   ├── datasets.py          (dataset CRUD, schema import from PostgreSQL)
│   │   ├── subscriptions.py     (subscription lifecycle)
│   │   ├── git.py               (Git history & contract retrieval)
│   │   ├── semantic.py          (LLM semantic policy endpoints)
│   │   ├── orchestration.py     (intelligent policy routing)
│   │   ├── policy_authoring.py  (create/update authored policies)
│   │   ├── policy_dashboard.py  (compliance metrics)
│   │   ├── policy_reports.py    (reporting endpoints)
│   │   ├── policy_exchange.py   (import/export)
│   │   ├── policy_conflicts.py  (exception management)
│   │   └── domain_governance.py (domain-level governance)
│   ├── models/          ← SQLAlchemy ORM models
│   │   ├── dataset.py
│   │   ├── contract.py
│   │   ├── subscription.py
│   │   ├── user.py
│   │   ├── policy_draft.py
│   │   ├── policy_version.py
│   │   ├── policy_artifact.py
│   │   └── policy_approval_log.py
│   ├── schemas/         ← Pydantic request/response schemas
│   │   ├── dataset.py
│   │   ├── contract.py
│   │   ├── subscription.py
│   │   └── policy.py
│   └── services/        ← Business logic (bulk of the complexity)
│       ├── contract_service.py        (contract generation & Git versioning — 481 LoC)
│       ├── policy_engine.py           (rule-based YAML policy validation — 342 LoC)
│       ├── semantic_policy_engine.py  (LLM validation via Ollama — 461 LoC)
│       ├── policy_orchestrator.py     (intelligent routing & risk scoring — 538 LoC)
│       ├── postgres_connector.py      (schema introspection from PostgreSQL — 557 LoC)
│       ├── git_service.py             (Git operations — commit, tag, diff — 317 LoC)
│       ├── ollama_client.py           (HTTP client for local Ollama — 237 LoC)
│       ├── authored_policy_loader.py  (load/manage authored policies — 258 LoC)
│       └── policy_converter.py        (YAML ↔ JSON format conversion — 204 LoC)
├── policies/            ← YAML policy definitions (edit these to change rules)
│   ├── sensitive_data_policies.yaml   (5 PII/encryption policies — SD001–SD005)
│   ├── data_quality_policies.yaml     (5 quality policies — DQ001–DQ005)
│   ├── schema_governance_policies.yaml(7 schema policies — SG001–SG007)
│   └── semantic_policies.yaml         (8 LLM policies — SEM001–SEM008)
├── tests/               ← pytest test suite (510 tests, 23 files)
├── requirements.txt
└── pytest.ini
```

### Layered Architecture Pattern
```
HTTP Request → FastAPI Router (api/) → Service Layer (services/) → ORM (models/) → DB
                                    ↘ Policy Engine (policies/) ↗
```
- **Routers** are thin: validate input via Pydantic schemas, call a service, return the result.
- **Services** own all business logic, policy enforcement, and external integrations.
- **Models** are pure SQLAlchemy; no business logic.
- **Schemas** are pure Pydantic; keep separate from models.

---

## Frontend Architecture

```
frontend/src/
├── App.jsx                      ← Root: router + auth context provider
├── main.jsx                     ← Vite entry point
├── contexts/
│   └── AuthContext.jsx          ← Role-based auth (DataOwner, Consumer, Steward, Admin)
├── stores/
│   └── index.js                 ← Zustand global store
├── services/
│   └── api.js                   ← Axios client; all API calls go through here
├── pages/
│   ├── RoleSelector.jsx         ← Landing page; role picker
│   ├── Dashboard.jsx            ← Main metrics dashboard
│   ├── DatasetCatalog.jsx       ← Grid-view catalog with filters
│   ├── DatasetDetail.jsx        ← Individual dataset detail view
│   ├── SubscriptionQueue.jsx    ← Subscription management view
│   ├── ComplianceDashboard.jsx  ← Top-level compliance view
│   ├── ContractViewer.jsx       ← Contract display (YAML/JSON)
│   ├── GitHistory.jsx           ← Version history viewer
│   ├── PolicyManager.jsx        ← Policy management UI
│   ├── SchemaImport.jsx         ← Schema import from PostgreSQL
│   ├── DataOwner/
│   │   ├── DatasetRegistrationWizard.jsx  ← 4-step registration form
│   │   └── OwnerDashboard.jsx             ← violations & metrics
│   ├── DataConsumer/
│   │   └── DataCatalogBrowser.jsx         ← catalog & subscription flow
│   ├── DataSteward/
│   │   └── ApprovalQueue.jsx              ← approval workflow
│   └── Admin/
│       └── ComplianceDashboard.jsx        ← analytics & Recharts
├── components/
│   ├── Layout.jsx               ← Sidebar navigation layout
│   ├── Layout.css
│   ├── TopNavLayout.jsx         ← Top navigation layout
│   ├── TopNavLayout.css
│   └── PolicyAuthoring/         ← policy editor components
│       ├── PolicyForm.jsx
│       ├── PolicyList.jsx
│       ├── PolicyDetail.jsx
│       ├── PolicyReview.jsx
│       ├── PolicyDashboard.jsx
│       ├── PolicyTimeline.jsx
│       ├── PolicyConflicts.jsx
│       ├── PolicyExchange.jsx
│       ├── DomainGovernance.jsx
│       ├── ComplianceReport.jsx
│       └── index.js
└── test/
    ├── AuthContext.test.jsx     ← Role-based auth tests
    ├── api.test.js              ← Axios client tests
    ├── stores.test.js           ← Zustand store tests
    └── setup.js                 ← Test configuration
```

**Key frontend patterns:**
- All API calls go through `services/api.js` (single Axios instance with base URL + interceptors).
- Global state lives in Zustand (`stores/index.js`); component-local state uses React `useState`.
- Navigation uses React Router v6 with programmatic `useNavigate`.
- Vite proxies `/api` to `http://localhost:8000` (see `vite.config.js`).
- Two layout variants: `Layout.jsx` (sidebar) and `TopNavLayout.jsx` (top navigation).

---

## Policy System

### Rule-Based Policies (YAML)
Stored in `backend/policies/*.yaml`. Each policy has:
```yaml
policies:
  - id: SD001              # Unique ID (prefix: SD=Sensitive Data, DQ=Quality, SG=Schema, SEM=Semantic)
    name: pii_encryption_required
    severity: critical     # critical | high | medium | low
    rule: |
      IF schema contains PII fields (ssn, credit_card, etc.)
      THEN encryption_required must be true
    remediation: |
      1. Set encryption_required: true in dataset registration
      2. Specify encryption_standard: AES-256
```

**Policy categories:**
| Prefix | File | Count | Focus |
|--------|------|-------|-------|
| SD | `sensitive_data_policies.yaml` | 5 | PII, encryption, masking |
| DQ | `data_quality_policies.yaml` | 5 | Nullability, freshness, quality |
| SG | `schema_governance_policies.yaml` | 7 | Schema structure, naming, types |
| SEM | `semantic_policies.yaml` | 8 | LLM context-aware validation |

### Semantic Policies (LLM)
Evaluated by `semantic_policy_engine.py` via `ollama_client.py`. Ollama must be running locally on port 11434. Semantic policies (SEM001–SEM008) handle nuanced cases that rule-based checks cannot express.

### Orchestration Strategies
`policy_orchestrator.py` routes validation requests based on data classification and risk score:
| Strategy | When Used | Rule-Based | Semantic |
|----------|-----------|-----------|---------|
| FAST | Low risk, no PII | ✓ | — |
| BALANCED | Moderate risk | ✓ | Optional |
| THOROUGH | High risk, PII | ✓ | ✓ |
| ADAPTIVE | Unknown/mixed | Risk-based | Risk-based |

---

## Environment Variables

All settings are in `backend/app/config.py` as a Pydantic `Settings` class. Create a `.env` file in `backend/` to override defaults.

| Variable | Default | Notes |
|----------|---------|-------|
| `SQLALCHEMY_DATABASE_URL` | `sqlite:///governance_metadata.db` | Metadata storage |
| `POSTGRES_HOST` | `localhost` | Demo DB |
| `POSTGRES_PORT` | `5432` | Demo DB |
| `POSTGRES_DB` | `financial_demo` | Demo DB name |
| `POSTGRES_USER` | `governance_user` | Demo DB credentials |
| `POSTGRES_PASSWORD` | `governance_pass` | Demo DB credentials |
| `GIT_CONTRACTS_REPO_PATH` | `backend/contracts` | Where contracts are stored |
| `GIT_USER_NAME` | `"Data Governance Platform"` | Git commit author |
| `GIT_USER_EMAIL` | `"governance@company.com"` | Git commit email |
| `POLICIES_PATH` | `backend/policies` | Policy YAML directory |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed frontend origins |
| `DEBUG` | `True` | FastAPI debug mode |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |

---

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker (for PostgreSQL demo DB)
- Ollama (optional — only needed for semantic/LLM policies)

### Backend Setup
```bash
cd data-governance-platform/backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Frontend Setup
```bash
cd data-governance-platform/frontend
npm install
npm run dev                        # Dev server at http://localhost:3000
```

### PostgreSQL Demo DB (optional)
```bash
cd data-governance-platform
docker-compose up -d               # Starts PostgreSQL on port 5432
# Data is auto-loaded from demo/setup_postgres.sql and demo/sample_data.sql
```

### Quick Start (all-in-one)
```bash
cd data-governance-platform
chmod +x start.sh && ./start.sh
```

---

## Running Tests

### Backend Tests (pytest)
```bash
cd data-governance-platform/backend
# Activate venv first
python -m pytest tests/ -v                         # All tests, verbose
python -m pytest tests/ -m unit                    # Unit tests only
python -m pytest tests/ -m integration             # Integration tests
python -m pytest tests/ -m api                     # API endpoint tests
python -m pytest tests/ -m service                 # Service layer tests
python -m pytest tests/ --cov=app --cov-report=html # Coverage report
python -m pytest tests/test_policy_engine.py -v    # Single file
```

**pytest markers** (defined in `pytest.ini`):
- `unit` — Pure unit tests, no DB or network
- `integration` — Tests requiring a database
- `api` — Tests hitting FastAPI endpoints
- `service` — Service layer business logic tests
- `slow` — Tests that take a long time to run

**Test file map (23 files, ~510 tests):**
| File | What it covers |
|------|---------------|
| `test_policy_engine.py` | Rule-based policy validation logic |
| `test_contract_service.py` | Contract generation and versioning |
| `test_api_datasets.py` | Dataset CRUD endpoints |
| `test_api_subscriptions.py` | Subscription workflow endpoints |
| `test_api_git.py` | Git history & contract endpoints |
| `test_api_orchestration.py` | Orchestration routing endpoints |
| `test_api_semantic.py` | LLM semantic policy endpoints |
| `test_models.py` | SQLAlchemy model operations |
| `test_orchestration.py` | Policy orchestration strategies |
| `test_semantic_scanner.py` | LLM semantic policy evaluation |
| `test_semantic_engine.py` | Semantic engine internals |
| `test_git_service.py` | Git service operations |
| `test_postgres_connector.py` | PostgreSQL schema introspection |
| `test_ollama_client.py` | Ollama HTTP client |
| `test_authored_policy_loader.py` | Authored policy loading |
| `test_policy_authoring.py` | Policy creation and management |
| `test_policy_conflicts.py` | Exception and conflict handling |
| `test_policy_converter.py` | YAML ↔ JSON conversion |
| `test_policy_enforcement.py` | End-to-end enforcement workflows |
| `test_policy_exchange.py` | Policy import/export |
| `test_policy_lifecycle.py` | Full policy lifecycle |
| `test_policy_reports.py` | Reporting endpoints |
| `test_domain_governance.py` | Domain-level governance |

### Frontend Tests (Vitest)
```bash
cd data-governance-platform/frontend
npm test                  # Watch mode
npm run test:ui           # Interactive UI
npm run test:coverage     # Coverage report
```

**Frontend test files (4 files, ~92 tests):**
| File | What it covers |
|------|---------------|
| `test/AuthContext.test.jsx` | Role-based auth context |
| `test/api.test.js` | Axios client and API calls |
| `test/stores.test.js` | Zustand global store |
| `test/setup.js` | Test environment configuration |

### Test Fixtures
`backend/tests/conftest.py` provides:
- `db` — In-memory SQLite test database session
- `client` — FastAPI `TestClient` instance
- Pre-seeded test datasets, users, and contracts

---

### Regression Testing Requirements

**Hard requirement: run the complete regression suite after every code change, without exception.**

"Complete regression" means all 23 backend test files (~510 tests) and all 4 frontend test files (~92 tests) pass with zero failures and zero errors. A partial test run does not satisfy this requirement.

---

#### Complete Regression Commands

Both suites must pass before a task is considered complete.

**Backend (all 23 files, ~510 tests):**
```bash
cd data-governance-platform/backend
source venv/bin/activate
python -m pytest tests/ -v --tb=short
```

**Frontend (all 4 files, ~92 tests):**
```bash
cd data-governance-platform/frontend
npm test -- --run
```

---

#### What "Complete Regression" Covers

| Suite | Files | Tests | Markers included |
|-------|-------|-------|-----------------|
| Backend pytest | All 23 `test_*.py` files in `backend/tests/` | ~510 | `unit`, `integration`, `api`, `service`, `slow` |
| Frontend Vitest | All 4 files in `frontend/src/test/` | ~92 | All suites |

Do **not** limit the run to a single marker (e.g., `-m unit` only). All markers — including `slow` — must be included unless the environment cannot support them (document the reason if any are skipped).

---

#### Pass Criteria

The regression suite passes when **all** of the following are true:

1. `pytest` exits with code `0` — zero failures, zero errors.
2. `npm test -- --run` exits with code `0` — zero failed suites, zero failed test cases.
3. No new `SKIPPED` or `xfail` markers were added as a workaround to hide failures.
4. Test count has not decreased — if fewer tests are collected than ~510 backend / ~92 frontend, investigate before proceeding.

---

#### Handling Failures

1. **Identify scope**: determine whether the failure pre-existed your change (check `TEST_RESULTS.md`). If pre-existing, document it and continue.
2. **Classify**: use the `/test-and-fix` skill's failure classification (implementation bug, test bug, missing fixture, import error, environment issue).
3. **Fix before marking done**: do not mark a task complete with a failing regression.
4. **Do not suppress**: never add `pytest.mark.skip`, `xfail`, or comment out assertions to make the suite green. Fix the root cause.
5. **Re-run full regression** after each fix to confirm no secondary regressions were introduced.

---

#### Regression in the Multi-Agent Workflow

When using multiple sub-agents (see "Multi-Agent Coordination Strategy"), regression is the **orchestrator's responsibility**:

- Sub-agents must not declare their subtask `DONE` based only on tests within their own scope.
- The orchestrator runs full regression after **all** sub-agents have completed and all changes are integrated.
- If regression fails after integration, the orchestrator diagnoses which agent's output caused it and assigns a fix sub-agent.

---

## API Reference (key endpoints)

All routes are prefixed with `/api/v1`.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/datasets/` | List all registered datasets |
| `POST` | `/datasets/` | Register a new dataset (triggers policy validation) |
| `GET` | `/datasets/{id}` | Get dataset details |
| `POST` | `/datasets/{id}/import-schema` | Import schema from PostgreSQL |
| `GET` | `/subscriptions/` | List subscriptions |
| `POST` | `/subscriptions/` | Create subscription request |
| `PUT` | `/subscriptions/{id}/approve` | Approve subscription (generates contract) |
| `PUT` | `/subscriptions/{id}/reject` | Reject subscription |
| `GET` | `/git/contracts` | List all versioned contracts |
| `GET` | `/git/contracts/{name}/history` | Contract version history |
| `POST` | `/semantic/scan` | Run LLM semantic policy scan |
| `POST` | `/orchestration/validate` | Validate via intelligent orchestrator |
| `GET` | `/policy-dashboard/` | Compliance metrics summary |
| `GET` | `/policy-reports/` | Detailed compliance reports |
| `POST` | `/policy-authoring/` | Create authored policy |
| `POST` | `/policy-exchange/export` | Export policies |
| `POST` | `/policy-exchange/import` | Import policies |
| `GET` | `/domain-governance/` | Domain-level governance rules |
| `GET` | `/policy-conflicts/` | List policy exceptions and conflicts |

Interactive API docs: `http://localhost:8000/docs`

---

## Claude Skills

A custom Claude Code skill is included at `.claude/skills/test-and-fix.md`:

- **test-and-fix**: Runs the backend pytest suite and frontend Vitest suite, analyses any failures, and suggests targeted code fixes. Invoke via `/test-and-fix` in Claude Code.

---

## Multi-Agent Coordination Strategy

Every task — regardless of size — must be executed using a coordinated multi-agent approach. A **main (orchestrator) agent** decomposes the work and delegates subtasks to **sub-agents** that run in parallel. The number of sub-agents is determined intelligently by task complexity, scope, and how much of the work can be parallelized.

This is not optional: even a task that could be done sequentially by a single agent must follow this pattern, because parallelism reduces latency and parallel validation catches cross-cutting issues.

---

### Roles: Orchestrator vs. Sub-Agents

| Role | Responsibilities |
|------|----------------|
| **Orchestrator (main agent)** | Reads the task, explores the codebase to understand scope, decomposes into subtasks, assigns each subtask to a sub-agent, collects and integrates results, resolves conflicts, produces the final output |
| **Sub-agent** | Owns exactly one subtask, operates within a defined scope (files, layers, test files), reports results and any blockers back to the orchestrator |

**Orchestrator rules:**
- Explore the codebase first (Glob, Grep, Read) before decomposing — never decompose blindly.
- Assign each sub-agent a scope boundary: specific files, directories, or layers it is allowed to touch.
- Explicitly state which sub-agents can run in parallel vs. which must wait for another agent's output.
- Integrate all sub-agent outputs before writing any file.
- Run the full regression suite (see "Regression Testing Requirements") after all sub-agents complete.

**Sub-agent rules:**
- Work only within the assigned scope. Never touch files outside the assigned boundary.
- Report: what was done, what files were changed, any assumptions made, any blockers encountered.
- If a blocker requires touching another agent's scope, escalate to the orchestrator — do not expand scope unilaterally.

---

### Task Decomposition: Use the Layered Architecture as Boundaries

| Layer | Typical Sub-Agent Scope |
|-------|------------------------|
| Models (`app/models/`) | Schema changes, new model fields, relationships |
| Schemas (`app/schemas/`) | Pydantic request/response shapes |
| Services (`app/services/`) | Business logic, policy enforcement |
| Routers (`app/api/`) | Endpoint wiring, HTTP surface |
| Policies (`backend/policies/`) | YAML rule additions or edits |
| Frontend API (`frontend/src/services/api.js`) | New API call bindings |
| Frontend UI (`frontend/src/pages/`, `components/`) | New pages, component changes |
| Tests (`backend/tests/`, `frontend/src/test/`) | New or updated test coverage |

---

### Agent Count by Task Complexity

| Task Type | Sub-Agents | Parallelism Strategy |
|-----------|-----------|----------------------|
| **Trivial** — Fix a typo, update one config value, add one field to a schema | 1–2 | Agent 1: implement. Agent 2: update affected test. |
| **Simple** — Add a new policy rule (YAML + engine method + test) | 2–3 | Agent 1: YAML + engine. Agent 2: test. Agent 3 (if needed): frontend display. |
| **Moderate** — Add a new API endpoint (router + schema + service + test + frontend) | 3–5 | Agent 1: model + schema. Agent 2: service logic. Agent 3: router. Agent 4: tests. Agent 5: frontend API binding. Agents 1–3 often run in parallel; Agent 4 waits on 1–3. |
| **Complex** — Add a new governance feature end-to-end (DB model, service, orchestration, policy, UI, tests) | 5–8 | Decompose by layer. Parallel: models, policies, frontend scaffold. Sequential gate: schemas depend on models; router depends on service; tests depend on all implementation. |
| **Cross-cutting** — Refactor a service used by many routers, update a core data model, change auth logic | 5+ | One agent per affected module. Orchestrator produces a dependency graph before spawning agents. All agents report diffs; orchestrator merges and checks for conflicts before writing. |

**Rule of thumb for determining agent count:**
1. Count the number of distinct files that need non-trivial changes.
2. Identify which changes are independent (can run in parallel) vs. dependent (must sequence).
3. Assign one sub-agent per group of independent files.
4. Add one extra sub-agent for integration testing if the task touches more than 3 files.

---

### Example: Adding a New API Endpoint

Task: *"Add a `GET /api/v1/datasets/{id}/audit-log` endpoint."*

**Orchestrator decomposition:**

```
Parallel batch 1 — these agents run concurrently (no dependencies between them):
  Sub-agent A — app/models/dataset.py          Add audit_log relationship if needed
  Sub-agent B — app/schemas/dataset.py         Add AuditLogResponse schema
  Sub-agent C — app/services/ (new file)       Implement audit log retrieval logic

Sequential batch 2 — these agents start only after batch 1 is complete:
  Sub-agent D — app/api/datasets.py            Wire GET endpoint, call service from A/B/C
  Sub-agent E — backend/tests/                 Add test_api_audit_log.py: happy path + 404
  Sub-agent F — frontend/src/services/api.js   Expose getAuditLog(datasetId) function

Orchestrator final step:
  Collect all outputs → resolve schema conflicts → run full regression suite
```

---

### How Sub-Agents Report Results

Each sub-agent returns a structured summary to the orchestrator:

```
Agent: <label, e.g., "Sub-agent B — Pydantic schemas">
Status: DONE | BLOCKED
Files changed:
  - backend/app/schemas/dataset.py  (added AuditLogResponse, AuditLogEntry)
Assumptions made:
  - audit_log field on Dataset model exists (relies on Sub-agent A output)
Blockers:
  - None
Cross-agent dependencies introduced:
  - Sub-agent D (router) must import AuditLogResponse from this schema
```

The orchestrator reads all reports, checks for conflicts (e.g., two agents editing the same line of the same file), resolves them, and then writes all changes before triggering regression.

---

### When to Use Fewer Sub-Agents

Use fewer sub-agents when:
- The entire change fits in a single file (use 1 sub-agent + orchestrator verification).
- Changes are strictly sequential with no parallelizable steps (avoid fake parallelism with forced hand-offs).
- The task is a pure documentation update with no code change.

Even in these cases, the orchestrator role remains: it must still explore before acting and run regression after any code change.

---

## Code Conventions

### Python (Backend)

**File docstrings** — Every module starts with a triple-quoted docstring explaining its purpose.

**FastAPI route pattern:**
```python
@router.post("/", response_model=ResponseSchema, status_code=201)
def create_item(
    item: CreateSchema,
    db: Session = Depends(get_db)
):
    """One-line summary.

    Longer description if needed.

    Args:
        item: Validated request body.
        db: Database session (injected by FastAPI).

    Returns:
        Created item with generated ID.

    Raises:
        HTTPException: 400 if validation fails, 404 if dependency not found.
    """
    return some_service.create(item, db)
```

**Service pattern:**
- Services are plain classes or module-level functions (not FastAPI-specific).
- Services call models directly via SQLAlchemy; they do not call other routers.
- `PolicyEngine` is instantiated once at import time and loads all YAML policies.

**Models:**
- Extend `Base` from `database.py`.
- Use `JSON` type for flexible schema fields.
- Include `created_at` / `updated_at` timestamps for audit trails.
- Relationships use `back_populates` (not `backref`).

**Schemas:**
- Request schemas: `CreateX`, `UpdateX`.
- Response schemas: `XResponse`, `XDetail`.
- Keep schemas in `schemas/` — never put Pydantic models inside route files.

**Imports:** stdlib → third-party → local (separated by blank lines, as per PEP 8 / isort).

**Naming:**
- Functions and variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private helpers: `_leading_underscore`

### JavaScript / React (Frontend)

**Component pattern:**
```jsx
// pages/DataOwner/MyComponent.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

export default function MyComponent() {
  const [data, setData] = useState(null);
  const navigate = useNavigate();
  // ...
}
```

**API calls:** Always use `services/api.js`; never import Axios directly in components.

**State management:**
- Component-local state: `useState`
- Cross-page shared state: Zustand store in `stores/index.js`
- Auth/role: `useContext(AuthContext)` from `contexts/AuthContext.jsx`

**Layouts:** Use `Layout.jsx` for sidebar navigation or `TopNavLayout.jsx` for top navigation, depending on the page role context.

**Naming:**
- Components: `PascalCase.jsx`
- Hooks: `useCamelCase`
- Utility functions: `camelCase`
- CSS classes: `kebab-case`

---

## Git Workflow

### Branch Strategy
```
main          ← production-stable
master        ← primary development branch (existing)
feature/*     ← new features
bugfix/*      ← bug fixes
docs/*        ← documentation updates
claude/*      ← AI-assisted changes (e.g., claude/add-claude-documentation-UEP9p)
```

### Commit Convention
Use imperative mood, present tense:
```
Add policy validation for schema versioning
Fix: null pointer in contract service when dataset has no schema
Update: semantic policy engine to handle Ollama timeouts
Refactor: extract risk scoring logic into separate method
Test: add coverage for domain governance endpoints
Docs: update QUICKSTART with PostgreSQL setup steps
```

### Contract Versioning (Git)
The platform uses Git to version data contracts. Contracts are committed to `backend/contracts/` by `git_service.py` on each approval. This is an **application-level** Git operation — do not interfere with files in `backend/contracts/` manually.

---

## Key Files to Know

| File | Why It Matters |
|------|---------------|
| `backend/app/config.py` | All configuration; change env defaults here |
| `backend/app/database.py` | DB initialization and seed data |
| `backend/app/main.py` | FastAPI app setup and router registration |
| `backend/app/services/policy_engine.py` | Core rule-based policy logic |
| `backend/app/services/policy_orchestrator.py` | Intelligent routing logic |
| `backend/policies/*.yaml` | Policy definitions — edit these to add/modify rules |
| `frontend/src/services/api.js` | All API calls; add new endpoints here |
| `frontend/src/stores/index.js` | Global state; add new state slices here |
| `frontend/src/components/Layout.jsx` | Sidebar navigation layout |
| `frontend/src/components/TopNavLayout.jsx` | Top navigation layout |
| `data-governance-platform/docker-compose.yml` | PostgreSQL demo DB setup |
| `.claude/skills/test-and-fix.md` | Claude skill for running tests |

---

## Common Tasks for AI Assistants

### Adding a New Policy
1. Choose the correct YAML file in `backend/policies/` based on category.
2. Add a policy entry with a unique ID (next in sequence), `name`, `severity`, `rule`, and `remediation`.
3. If the rule requires code logic, add an evaluation method in `policy_engine.py`.
4. Add a test case in `tests/test_policy_engine.py`.

### Adding a New API Endpoint
1. Create or extend a router file in `backend/app/api/`.
2. Define Pydantic request/response schemas in `backend/app/schemas/`.
3. Implement business logic in a service in `backend/app/services/`.
4. Register the router in `backend/app/main.py` if it's a new file.
5. Add tests in `backend/tests/`.
6. Expose the endpoint in `frontend/src/services/api.js`.

### Adding a New Frontend Page
1. Create `frontend/src/pages/<Role>/NewPage.jsx`.
2. Add a route in `frontend/src/App.jsx`.
3. Link to it from the relevant role dashboard.
4. Use `api.js` for data fetching; use `useState` for local state.
5. Choose `Layout.jsx` or `TopNavLayout.jsx` as the wrapping layout.

### Modifying the Database Schema
1. Update the SQLAlchemy model in `backend/app/models/`.
2. Update corresponding Pydantic schemas in `backend/app/schemas/`.
3. Update `database.py` if seed data needs to change.
4. Drop and recreate the SQLite DB in development (`rm governance_metadata.db`).
5. Update affected tests.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError` on backend start | venv not activated | `source venv/bin/activate` |
| CORS error in browser | Backend not running or wrong port | Start uvicorn on port 8000 |
| `Connection refused` to PostgreSQL | Docker not running | `docker-compose up -d` |
| LLM semantic scan returns error | Ollama not running | `ollama serve` + pull a model |
| `sqlite3.OperationalError: no such table` | DB not initialized | Restart backend (auto-creates tables) |
| Git contract commit fails | `backend/contracts/` not a git repo | Backend auto-inits it; check permissions |
| Frontend API calls return 422 | Pydantic validation failure | Check request payload matches schema |
| Tests fail with import errors | Missing dependencies | `pip install -r requirements.txt` |
| Frontend tests fail | Node modules missing | `npm install` |

---

## Out of Scope (do not modify)

- `backend/contracts/` — Auto-managed by the application's Git service.
- `demo/` SQL files — Reference data only; do not use in production.
- Azure-related code (`azure-storage-blob`) — Wired for future use; currently unused.

---

*Last updated: 2026-03-04. Generated by Claude Code for the Data Governance Platform PoC.*
