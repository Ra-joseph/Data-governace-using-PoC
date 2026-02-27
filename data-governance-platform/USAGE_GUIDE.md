# Usage Guide: Hosting & Demo Walkthrough

## Table of Contents

- [Prerequisites](#prerequisites)
  - [macOS Setup (Homebrew)](#macos-setup-homebrew)
- [Architecture & Layer Dependencies](#architecture--layer-dependencies)
  - [Layer 1 — Infrastructure](#layer-1--infrastructure)
  - [Layer 2 — Backend (Python)](#layer-2--backend-python)
  - [Layer 3 — Frontend (Node.js)](#layer-3--frontend-nodejs)
- [Part 1: Hosting on Your MacBook](#part-1-hosting-on-your-macbook)
  - [Step 1: Clone the Repository](#step-1-clone-the-repository)
  - [Step 2: Start the Demo Database](#step-2-start-the-demo-database)
  - [Step 3: Start the Backend API](#step-3-start-the-backend-api)
  - [Step 4: Start the Frontend](#step-4-start-the-frontend)
  - [Step 5: Verify Everything Is Running](#step-5-verify-everything-is-running)
- [Part 2: Navigating the Web Application](#part-2-navigating-the-web-application)
  - [Role Selector](#role-selector)
  - [Data Owner View](#data-owner-view)
  - [Data Consumer View](#data-consumer-view)
  - [Data Steward View](#data-steward-view)
  - [Platform Admin View](#platform-admin-view)
  - [Shared Pages](#shared-pages)
- [Role-Based API Quick Reference](#role-based-api-quick-reference)
  - [Data Owner Commands](#data-owner-commands)
  - [Data Consumer Commands](#data-consumer-commands)
  - [Data Steward Commands](#data-steward-commands)
  - [Platform Admin Commands](#platform-admin-commands)
- [Part 3: Complete Demo Walkthrough](#part-3-complete-demo-walkthrough)
  - [Scenario: Governing a Financial Customer Accounts Dataset](#scenario-governing-a-financial-customer-accounts-dataset)
  - [Act 1 — Data Owner Registers a Dataset](#act-1--data-owner-registers-a-dataset)
  - [Act 2 — Policy Engine Catches Violations](#act-2--policy-engine-catches-violations)
  - [Act 3 — Data Consumer Requests Access](#act-3--data-consumer-requests-access)
  - [Act 4 — Data Steward Reviews and Approves](#act-4--data-steward-reviews-and-approves)
  - [Act 5 — Platform Admin Reviews Compliance](#act-5--platform-admin-reviews-compliance)
  - [Act 6 — Examining the Audit Trail](#act-6--examining-the-audit-trail)
- [Stopping the Application](#stopping-the-application)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Install the following on your laptop before you begin:

| Tool | Version | Check Command | Install |
|------|---------|---------------|---------|
| **Python** | 3.10 or higher | `python3 --version` | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18 or higher | `node --version` | [nodejs.org](https://nodejs.org/) |
| **npm** | 9 or higher | `npm --version` | Included with Node.js |
| **Docker** | 20 or higher | `docker --version` | [docker.com](https://www.docker.com/get-started/) |
| **Git** | 2.30 or higher | `git --version` | [git-scm.com](https://git-scm.com/) |

**Optional** (for semantic/LLM-powered policy scanning):

| Tool | Purpose | Install |
|------|---------|---------|
| **Ollama** | Local LLM for semantic policies | [ollama.com](https://ollama.com/) |

> Ollama is not required for the core demo. The rule-based policy engine (17 policies) works without it. Ollama adds 8 additional semantic policies for deeper, context-aware validation.

### macOS Setup (Homebrew)

If you are running on a MacBook, Homebrew is the easiest way to install every prerequisite in one go.

**1. Install Homebrew** (skip if already installed):

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

After installation, follow the printed instructions to add Homebrew to your PATH, then close and reopen the terminal.

**2. Install all prerequisites:**

```bash
# Python 3.12 (satisfies the 3.10+ requirement)
brew install python@3.12

# Verify
python3 --version   # should print Python 3.12.x

# Node.js 20 LTS (satisfies the 18+ requirement)
brew install node@20

# Add Node 20 to PATH (Homebrew will print the exact command — copy and run it)
echo 'export PATH="/opt/homebrew/opt/node@20/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc

# Verify
node --version   # should print v20.x.x
npm --version    # should print 10.x.x

# Git (usually pre-installed via Xcode Command Line Tools)
git --version || brew install git

# Docker Desktop — download and install the macOS app
open https://www.docker.com/products/docker-desktop/
# After installation, open Docker.app from Applications and wait for the whale icon in the menu bar
docker --version   # verify once Docker Desktop is running
```

**3. Optional — Ollama for semantic/LLM policies:**

```bash
brew install ollama
```

> **Apple Silicon (M1/M2/M3) note**: All tools above are native ARM64 builds via Homebrew. No Rosetta translation is needed.

---

## Architecture & Layer Dependencies

The platform is built in three layers that must start in order. Each layer has its own dependency set and communicates with adjacent layers over localhost network ports.

```
┌──────────────────────────────────────────────────────────────────┐
│  Layer 3 — Frontend (React 18 + Vite)           Port 3000        │
│  Installed via: npm install (inside frontend/)                    │
│  Talks to: Backend REST API on port 8000                         │
└──────────────────────────┬───────────────────────────────────────┘
                           │  HTTP REST API (Axios)
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│  Layer 2 — Backend (FastAPI + Python venv)      Port 8000        │
│  Installed via: pip install -r requirements.txt                   │
│  Talks to: PostgreSQL on port 5432 (schema import)               │
│            SQLite file (metadata storage)                         │
│            Ollama on port 11434 (optional, semantic scanning)     │
└──────┬────────────────────────────────────┬────────────────────── ┘
       │  psycopg2 (PostgreSQL driver)       │  requests (HTTP)
       ▼                                     ▼
┌──────────────────────┐       ┌──────────────────────────────────┐
│  Layer 1a            │       │  Layer 1b (optional)             │
│  PostgreSQL 15       │       │  Ollama LLM                      │
│  Port 5432           │       │  Port 11434                      │
│  Started via Docker  │       │  Started via: ollama serve       │
│  Demo tables:        │       │  Model: llama3.2                 │
│  customer_accounts   │       │  Enables 8 semantic policies     │
│  transactions        │       └──────────────────────────────────┘
│  fraud_alerts        │
└──────────────────────┘
```

**Startup order**: Layer 1 (Docker / PostgreSQL) → Layer 2 (Backend) → Layer 3 (Frontend)

---

### Layer 1 — Infrastructure

| Component | Managed By | Port | Required |
|-----------|-----------|------|----------|
| PostgreSQL 15 | Docker Compose | 5432 | Yes |
| Ollama LLM | `ollama serve` | 11434 | No |

The `docker-compose.yml` file in `data-governance-platform/` automatically:
- Pulls the `postgres:15-alpine` image
- Creates the `financial_demo` database
- Seeds 3 demo tables from `demo/setup_postgres.sql` and `demo/sample_data.sql`

---

### Layer 2 — Backend (Python)

All Python dependencies are isolated inside a **virtual environment** created at the `data-governance-platform/` level.

```bash
# Create the venv (run once, from data-governance-platform/)
python3 -m venv venv

# Activate (must repeat in every new terminal session)
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Install all backend packages
pip install -r backend/requirements.txt
```

| Package | Version | Layer Role |
|---------|---------|-----------|
| `fastapi` | 0.109.0 | Web framework — REST API routing & request handling |
| `uvicorn[standard]` | 0.27.0 | ASGI server — runs the FastAPI app in production-grade mode |
| `sqlalchemy` | 2.0.25 | ORM — manages the SQLite metadata database (datasets, contracts, subscriptions) |
| `psycopg2-binary` | 2.9.9 | PostgreSQL driver — connects to the demo database for schema import |
| `pydantic` | 2.5.3 | Data validation — enforces request/response schemas |
| `pydantic-settings` | 2.1.0 | Settings management — loads config from environment variables / `.env` |
| `pyyaml` | 6.0.1 | YAML parsing — loads all 25 policy definitions from `backend/policies/` |
| `gitpython` | 3.1.41 | Git operations — commits and versions data contracts in `backend/contracts/` |
| `pandas` | 2.1.4 | Data utilities — assists with schema analysis and column profiling |
| `python-dotenv` | 1.0.0 | Env vars — reads `.env` file overrides for config values |
| `azure-storage-blob` | 12.19.0 | Azure Blob connector (future data source; safe to ignore for local demo) |
| `azure-identity` | 1.15.0 | Azure auth (future; safe to ignore for local demo) |
| `colorama` | 0.4.6 | Colored terminal output for startup logs |
| `pytest` | 7.4.4 | Test framework |
| `httpx` | 0.26.0 | Async HTTP client — used by pytest tests to call the API |
| `requests` | 2.31.0 | Sync HTTP client — used in utility scripts |

**Backend ↔ Database dependency**: The backend reads `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` from `config.py` (defaults match the Docker Compose credentials). If PostgreSQL is not running, schema import endpoints will fail gracefully — all other endpoints remain functional.

---

### Layer 3 — Frontend (Node.js)

All JavaScript dependencies are installed into `frontend/node_modules/` by npm.

```bash
# Install all frontend packages (run once, from data-governance-platform/frontend/)
npm install

# Start the dev server (hot-reload)
npm run dev
```

**Runtime packages** (shipped to the browser):

| Package | Version | Role |
|---------|---------|------|
| `react` | 18.2 | Core UI component framework |
| `react-dom` | 18.2 | Mounts React into the browser DOM |
| `react-router-dom` | 6.21 | Client-side routing (`/owner/dashboard`, `/consumer/catalog`, etc.) |
| `axios` | 1.6.2 | HTTP client — all API calls to the backend on port 8000 |
| `zustand` | 4.4.7 | Global state management (selected role, dataset list, subscription queue) |
| `recharts` | 2.10.3 | Interactive charts in the Platform Admin compliance dashboard |
| `framer-motion` | 10.16.16 | Page and component animations |
| `lucide-react` | 0.303.0 | SVG icon library |
| `react-hot-toast` | 2.4.1 | Toast notification popups |
| `date-fns` | 3.0.6 | Date formatting utilities |
| `react-markdown` | 9.0.1 | Renders markdown content in contract views |
| `prism-react-renderer` | 2.3.1 | Code syntax highlighting for YAML/JSON contract display |
| `yaml` | 2.3.4 | Parses YAML contract files in the browser |

**Dev-only packages** (build tools, not shipped to browser):

| Package | Purpose |
|---------|---------|
| `vite` | Dev server with hot-reload + production bundler |
| `@vitejs/plugin-react` | Vite plugin for JSX/React Fast Refresh |
| `vitest` | Unit test framework (Jest-compatible) |
| `@testing-library/react` | React component testing utilities |
| `eslint` | Code linting |
| `jsdom` | Browser DOM simulation for tests |

**Frontend ↔ Backend dependency**: Vite's dev server proxies all requests matching `/api/*` to `http://localhost:8000`. This proxy is configured in `frontend/vite.config.js`. The frontend will load and render even if the backend is down, but all data-fetching will show error states.

---

## Part 1: Hosting on Your MacBook

You will open **three terminal windows** — one each for the database, backend, and frontend.

> **macOS tip**: Use `Cmd + T` to open a new tab in Terminal.app, or `Cmd + D` in iTerm2 to split vertically.

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ra-joseph/Data-governace-using-PoC.git
cd Data-governace-using-PoC/data-governance-platform
```

### Step 2: Start the Demo Database

**Terminal 1 — PostgreSQL via Docker**

```bash
docker-compose up -d
```

This starts a PostgreSQL 15 container named `governance_postgres` with:
- **Database**: `financial_demo`
- **User**: `governance_user`
- **Password**: `governance_pass`
- **Port**: `5432`
- **Demo data**: 3 tables (`customer_accounts`, `transactions`, `fraud_alerts`) with 39 records

Verify the database is running:

```bash
docker ps
```

You should see a container named `governance_postgres` with status "Up".

### Step 3: Start the Backend API

**Terminal 2 — FastAPI Backend**

```bash
# From the data-governance-platform/ directory:

# 1. Create the virtual environment (one-time setup)
python3 -m venv venv

# 2. Activate it (required in every new terminal session)
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows PowerShell

# 3. Install all Python dependencies into the venv
pip install -r backend/requirements.txt

# 4. Change into the backend directory and start the server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> **Why `venv`?** The virtual environment isolates the backend's 17 Python packages from your system Python, preventing version conflicts. Everything installed via `pip install` stays inside `data-governance-platform/venv/` and never touches your global Python installation.

You should see output like:

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

The backend automatically:
- Creates a SQLite metadata database
- Initializes a Git repository in `backend/contracts/` for contract version control
- Loads all 25 governance policies from `backend/policies/`

**Quick check** — open a browser tab to: `http://localhost:8000/health`

You should see: `{"status": "healthy"}`

### Step 4: Start the Frontend

**Terminal 3 — React Frontend**

```bash
# From the data-governance-platform directory
cd frontend
npm install
npm run dev
```

You should see output like:

```
  VITE v5.x.x  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

> **Note**: The frontend runs on **port 3000** (configured in `vite.config.js`). All API requests to `/api/*` are automatically proxied to the backend at `localhost:8000`, so there are no CORS issues during development.

### Step 5: Verify Everything Is Running

Open these URLs in your browser:

| URL | What You Should See |
|-----|---------------------|
| `http://localhost:3000` | Role Selector screen with 4 role cards |
| `http://localhost:8000/health` | `{"status": "healthy"}` |
| `http://localhost:8000/api/docs` | Interactive Swagger API documentation |

If all three work, your platform is fully operational.

**Summary of running services:**

```
┌─────────────────────────────────────────────────┐
│  http://localhost:3000   →  React Frontend      │
│  http://localhost:8000   →  FastAPI Backend      │
│  localhost:5432          →  PostgreSQL Database   │
└─────────────────────────────────────────────────┘
```

---

## Part 2: Navigating the Web Application

### Role Selector

When you open `http://localhost:3000`, you see the **Role Selector** — four cards representing the personas in a data governance lifecycle:

| Role | Description | URL Path |
|------|-------------|----------|
| **Data Owner** | Registers and manages datasets | `/owner/dashboard` |
| **Data Consumer** | Browses the catalog and requests access | `/consumer/catalog` |
| **Data Steward** | Reviews and approves/rejects access requests | `/steward/approvals` |
| **Platform Admin** | Monitors compliance health and analytics | `/admin/dashboard` |

Click any card to enter that role's dedicated interface. You can switch roles at any time by clicking the **Switch Role** button in the sidebar (role-specific pages) or in the top navigation bar (legacy tool pages).

### Data Owner View

**Dashboard** (`/owner/dashboard`): Overview of your datasets — total count, published vs. draft, active violations, and recent activity.

**Dataset Registration Wizard** (`/owner/register`): A multi-step form to register a new dataset:
1. **Basic Info** — Name, domain, description, classification level
2. **Schema Import** — Connect to PostgreSQL and import the table schema automatically
3. **Review & Validate** — The policy engine runs all applicable policies and shows violations with remediation steps
4. **Publish** — Commit the data contract to Git

### Data Consumer View

**Data Catalog Browser** (`/consumer/catalog`): Browse all published datasets. Filter by classification (Public, Internal, Confidential, Restricted) and domain. Each dataset card shows its name, owner, classification, and compliance status.

**Subscription Request**: Click a dataset to view its details, then submit a subscription request specifying your SLA requirements (freshness targets, availability needs, quality thresholds).

### Data Steward View

**Approval Queue** (`/steward/approvals`): A queue of pending subscription requests. For each request, you can:
- View the consumer's details and SLA requirements
- Examine the underlying data contract
- **Approve** with comments (automatically generates a new contract version embedding the consumer's SLA terms)
- **Reject** with a reason

### Platform Admin View

**Compliance Dashboard** (`/admin/dashboard`): Analytics across all governed datasets:
- Compliance rate over time (area chart)
- Classification distribution (pie chart)
- Top violated policies (bar chart)
- Dataset growth trends
- Key metrics: total datasets, published datasets, active violations, PII-containing datasets

### Shared Pages

These pages are accessible from the sidebar regardless of your current role:

- **Dataset Catalog** — Grid view of all datasets with search and filtering
- **Dataset Detail** — Full details for any dataset, including schema, contract, and validation results
- **Git History** — Visual commit timeline showing every contract change, with file browser and commit details

---

## Role-Based API Quick Reference

Each role has a corresponding set of REST API endpoints. Use these `curl` snippets to interact with the platform programmatically, test individual features, or verify state after a UI action. All commands assume the backend is running on `http://localhost:8000`.

> **Tip**: Pipe any response through `| python3 -m json.tool` for pretty-printed JSON.

---

### Data Owner Commands

```bash
# ── 1. Discover available PostgreSQL tables to register ──────────────────
curl http://localhost:8000/api/v1/datasets/postgres/tables \
  | python3 -m json.tool
# Returns: ["customer_accounts", "transactions", "fraud_alerts"]

# ── 2. Preview the schema of a specific table ────────────────────────────
curl -X POST http://localhost:8000/api/v1/datasets/import-schema \
  -H "Content-Type: application/json" \
  -d '{"source_type": "postgres", "table_name": "customer_accounts"}' \
  | python3 -m json.tool
# Returns: column names, types, nullable flags, and auto-detected PII fields

# ── 3. Register a dataset (triggers full policy validation) ──────────────
curl -X POST http://localhost:8000/api/v1/datasets/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "customer_accounts",
    "domain": "Finance",
    "description": "Customer account records including personal and financial information",
    "classification": "confidential",
    "owner_name": "Finance Data Team",
    "owner_email": "finance-data@example.com",
    "source_type": "postgres",
    "table_name": "customer_accounts"
  }' | python3 -m json.tool
# Returns: dataset record with validation_results (violations + remediation steps)

# ── 4. List all registered datasets ─────────────────────────────────────
curl http://localhost:8000/api/v1/datasets/ | python3 -m json.tool

# ── 5. View a specific dataset and its current contract ──────────────────
curl http://localhost:8000/api/v1/datasets/1 | python3 -m json.tool

# ── 6. Re-run validation on an existing dataset ──────────────────────────
curl -X POST http://localhost:8000/api/v1/datasets/1/validate \
  | python3 -m json.tool
# Returns: full validation report with passed/warning/failed counts
```

**Expected output for dataset registration** (customer_accounts with intentional violations):

```json
{
  "id": 1,
  "name": "customer_accounts",
  "status": "draft",
  "validation_results": {
    "status": "failed",
    "passed": 8,
    "warnings": 4,
    "failures": 1,
    "violations": [
      {
        "policy_id": "SD001",
        "severity": "critical",
        "message": "PII fields require encryption documentation",
        "remediation": "Add encryption_details specifying algorithm (e.g., AES-256) and key management approach"
      }
    ]
  }
}
```

---

### Data Consumer Commands

```bash
# ── 1. Browse all published datasets ────────────────────────────────────
curl http://localhost:8000/api/v1/datasets/ | python3 -m json.tool

# ── 2. View a dataset's full schema and governance metadata ──────────────
curl http://localhost:8000/api/v1/datasets/1 | python3 -m json.tool

# ── 3. Submit a subscription request ────────────────────────────────────
curl -X POST http://localhost:8000/api/v1/subscriptions/ \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": 1,
    "consumer_name": "Analytics Team",
    "consumer_email": "analytics@example.com",
    "business_justification": "Monthly customer analytics reporting for Q1 business review",
    "use_case": "reporting",
    "sla_freshness_hours": 24,
    "sla_availability_percent": 99.5,
    "quality_completeness_threshold": 95.0,
    "requested_duration_months": 12
  }' | python3 -m json.tool
# Returns: subscription record with id and status "pending"

# ── 4. Check your subscription status ───────────────────────────────────
curl http://localhost:8000/api/v1/subscriptions/ | python3 -m json.tool

# ── 5. View a specific subscription ─────────────────────────────────────
curl http://localhost:8000/api/v1/subscriptions/1 | python3 -m json.tool
```

---

### Data Steward Commands

```bash
# ── 1. View all pending subscription requests ────────────────────────────
curl "http://localhost:8000/api/v1/subscriptions/?status=pending" \
  | python3 -m json.tool

# ── 2. View all subscriptions (any status) ──────────────────────────────
curl http://localhost:8000/api/v1/subscriptions/ | python3 -m json.tool

# ── 3. Approve a subscription (replace 1 with actual subscription ID) ────
curl -X PUT http://localhost:8000/api/v1/subscriptions/1/approve \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_name": "Jane Steward",
    "reviewer_notes": "Approved for monthly reporting. Data owner must resolve SD001 (PII encryption) before production use. Freshness SLA of 24h is acceptable."
  }' | python3 -m json.tool
# Returns: updated subscription (status "approved") + new contract version (v1.1.0)

# ── 4. Reject a subscription ─────────────────────────────────────────────
curl -X PUT http://localhost:8000/api/v1/subscriptions/1/reject \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_name": "Jane Steward",
    "reviewer_notes": "Insufficient business justification. Please resubmit with project code and data lineage plan."
  }' | python3 -m json.tool

# ── 5. View the Git commit history (full contract audit trail) ────────────
curl http://localhost:8000/api/v1/git/commits | python3 -m json.tool

# ── 6. View a specific Git commit ────────────────────────────────────────
curl http://localhost:8000/api/v1/git/commits/HEAD | python3 -m json.tool

# ── 7. Browse contracts on disk ──────────────────────────────────────────
ls -la data-governance-platform/backend/contracts/
cd data-governance-platform/backend/contracts && git log --oneline
```

---

### Platform Admin Commands

```bash
# ── 1. Compliance dashboard metrics ──────────────────────────────────────
curl http://localhost:8000/api/v1/policy/dashboard | python3 -m json.tool
# Returns: compliance rate, violation counts by severity, dataset stats

# ── 2. Policy violation report ───────────────────────────────────────────
curl http://localhost:8000/api/v1/policy/reports | python3 -m json.tool
# Returns: violations grouped by policy ID, with affected datasets

# ── 3. Run orchestrated validation with explicit strategy ─────────────────
# FAST: rule-based only (~100ms), good for low-risk data
curl -X POST http://localhost:8000/api/v1/orchestration/validate \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "strategy": "FAST"}' | python3 -m json.tool

# THOROUGH: all 25 policies including LLM (~24s, requires Ollama)
curl -X POST http://localhost:8000/api/v1/orchestration/validate \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "strategy": "THOROUGH"}' | python3 -m json.tool

# ADAPTIVE: auto-selects strategy based on risk assessment (recommended)
curl -X POST http://localhost:8000/api/v1/orchestration/validate \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": 1, "strategy": "ADAPTIVE"}' | python3 -m json.tool

# ── 4. Check semantic scanning availability ───────────────────────────────
curl http://localhost:8000/api/v1/semantic/status | python3 -m json.tool
# Returns: {"available": true/false, "model": "llama3.2", "endpoint": "..."}

# ── 5. Health check ───────────────────────────────────────────────────────
curl http://localhost:8000/health
# Returns: {"status": "healthy"}

# ── 6. Interactive API docs ───────────────────────────────────────────────
open http://localhost:8000/api/docs     # macOS: opens Swagger UI in browser
```

---

## Part 3: Complete Demo Walkthrough

This walkthrough demonstrates the full governance lifecycle using the included financial services demo data. It takes approximately 10-15 minutes.

### Scenario: Governing a Financial Customer Accounts Dataset

**The story**: Your organization has a `customer_accounts` table containing sensitive financial data with PII (email addresses, SSNs, phone numbers). A data owner needs to register it in the governance platform. The policy engine will catch compliance violations. A downstream analytics team (data consumer) wants access. A data steward reviews and approves the request. The platform admin monitors overall compliance.

**What you'll see in action**:
- Automatic schema import from PostgreSQL
- PII detection based on field naming patterns
- Policy validation catching real violations with remediation guidance
- Data contract generation in YAML and JSON
- Git-based version control and audit trail
- Subscription request and approval workflow

---

### Act 1 — Data Owner Registers a Dataset

1. **Open the application**: Navigate to `http://localhost:3000`

2. **Select the Data Owner role**: Click the "Data Owner" card

3. **Start registration**: Click "Register New Dataset" (or navigate to `/owner/register`)

4. **Fill in Basic Information**:
   - **Dataset Name**: `customer_accounts`
   - **Domain**: `Finance`
   - **Description**: `Customer account records including personal and financial information`
   - **Classification**: `Confidential`
   - **Owner**: `Finance Data Team`
   - **Contact**: `finance-data@example.com`

5. **Import Schema from PostgreSQL**: In the schema import step, the wizard connects to the demo PostgreSQL database and lists available tables:
   - `customer_accounts` (10 records)
   - `transactions` (23 records)
   - `fraud_alerts` (6 records)

   Select `customer_accounts`. The system imports the full schema and automatically detects PII fields based on naming patterns:

   | Field | Type | PII Detected |
   |-------|------|:------------:|
   | `account_id` | integer | |
   | `first_name` | varchar(100) | Yes |
   | `last_name` | varchar(100) | Yes |
   | `email` | varchar(255) | Yes |
   | `phone` | varchar(20) | Yes |
   | `ssn` | varchar(11) | Yes |
   | `account_type` | varchar(50) | |
   | `balance` | numeric(15,2) | |
   | `created_at` | timestamp | |
   | `status` | varchar(20) | |

   > The system flags 5 fields as PII (`first_name`, `last_name`, `email`, `phone`, `ssn`), which triggers sensitive data policies during validation.

6. **Proceed to validation**: Click "Next" to trigger policy validation.

**Quick verify via CLI** (confirm the dataset was registered):
```bash
curl http://localhost:8000/api/v1/datasets/ | python3 -m json.tool
# You should see "customer_accounts" with status "draft"
```

---

### Act 2 — Policy Engine Catches Violations

The policy engine validates the dataset contract against all applicable policies. For a Confidential dataset with PII, the orchestrator selects a thorough validation strategy.

**Expected violations** (these are intentionally present in the demo data):

| Policy | Severity | Violation | Remediation |
|--------|----------|-----------|-------------|
| **SD001** | Critical | PII fields lack encryption documentation | Add `encryption_details` specifying AES-256 and key management approach |
| **SD002** | Warning | No retention policy specified | Add `retention_policy` with retention period and deletion procedure |
| **SD003** | Warning | PII dataset missing compliance tags | Add `compliance_tags: ['SOX', 'PCI-DSS']` to the contract |
| **SD004** | Warning | Restricted use cases not documented | Add `restricted_uses` listing prohibited data uses |
| **DQ002** | Warning | No freshness SLA defined | Specify `freshness_sla` with `max_age_hours` based on consumer needs |
| **SG001** | Warning | Some fields lack descriptions | Add `description` to all schema fields |

> **Key Insight**: The critical violation (SD001) blocks publication. Warning-level violations allow publication but flag the dataset for review. This is the "prevention at borders" principle from the UN Peacekeeping model — violations are caught before they propagate.

7. **Review violations**: Each violation is displayed with:
   - The policy ID and name
   - A severity badge (Critical = red, Warning = orange)
   - A clear description of what's wrong
   - Step-by-step remediation instructions

8. **The contract is generated**: Even with violations, a data contract is generated and committed to Git:
   - `contracts/customer_accounts.yaml` (human-readable)
   - `contracts/customer_accounts.json` (machine-parseable)
   - Version: `1.0.0`
   - Status: `draft` (not published, due to critical violation)

> **What to point out in a demo**: The data owner doesn't need to guess what's wrong or consult a separate governance document. The platform tells them exactly what to fix and how to fix it, right at the point of creation.

**Quick verify via CLI** (confirm violations were caught):
```bash
curl http://localhost:8000/api/v1/datasets/1 | python3 -m json.tool
# Look for "validation_results" → "failures": 1 (SD001 — PII encryption)
# and "warnings": 4 (SD002, SD003, SD004, DQ002, SG001)

# Check the generated contract in Git
cd data-governance-platform/backend/contracts
git log --oneline   # should show "feat: register customer_accounts v1.0.0"
cat customer_accounts_v1.0.0.yaml 2>/dev/null || ls *.yaml
cd -   # return to previous directory
```

---

### Act 3 — Data Consumer Requests Access

9. **Switch roles**: Click the **Switch Role** button (sidebar footer) or navigate back to `http://localhost:3000` and select "Data Consumer"

10. **Browse the catalog**: The Data Catalog Browser (`/consumer/catalog`) shows all registered datasets. You'll see the `customer_accounts` dataset listed with its classification badge ("Confidential") and compliance status.

11. **View dataset details**: Click on `customer_accounts` to see:
    - Full schema with field types and PII flags
    - Current contract version and validation status
    - Data classification and owner information

12. **Submit a subscription request**: Click "Request Access" and fill in:
    - **Purpose**: `Monthly customer analytics reporting`
    - **SLA Requirements**:
      - Freshness: `24 hours` (data must be no older than 24 hours)
      - Availability: `99.5%`
      - Quality threshold: `95%` completeness
    - **Requested Duration**: `12 months`

13. **Request submitted**: The request enters a "Pending" state, waiting for steward approval.

> **What to point out in a demo**: The consumer specifies concrete SLA requirements upfront. These become part of the data contract when approved — creating a measurable agreement between producer and consumer.

**Quick verify via CLI** (confirm the subscription is pending):
```bash
curl http://localhost:8000/api/v1/subscriptions/ | python3 -m json.tool
# You should see the subscription with "status": "pending"
```

---

### Act 4 — Data Steward Reviews and Approves

14. **Switch roles**: Click the **Switch Role** button or navigate to `http://localhost:3000` and select "Data Steward"

15. **Open the Approval Queue** (`/steward/approvals`): You'll see the pending subscription request from the analytics team.

16. **Review the request**: Click to expand and examine:
    - **Who** is requesting access (the analytics team)
    - **What** they want (customer_accounts dataset)
    - **Why** (monthly analytics reporting)
    - **SLA terms** they're requesting (24h freshness, 99.5% availability, 95% quality)
    - **Current compliance status** of the dataset (violations present)

17. **Approve the request**: Click "Approve" and add a comment:
    > `Approved for monthly reporting. Note: data owner must resolve SD001 (PII encryption) before production use. Freshness SLA of 24h is acceptable for this use case.`

18. **What happens on approval**:
    - The subscription status changes to "Active"
    - A new contract version is generated (`1.1.0` — minor bump for additive change)
    - The consumer's SLA terms are embedded in the contract
    - The new contract version is committed to Git with the steward's approval comment

> **What to point out in a demo**: The steward doesn't just say "yes" or "no." The approval creates a versioned, auditable contract that both parties can reference. The SLA terms are now part of the data contract, not buried in an email thread.

**Quick verify via CLI** (confirm approval and new contract version):
```bash
# Check subscription is now approved
curl http://localhost:8000/api/v1/subscriptions/1 | python3 -m json.tool
# Look for "status": "approved" and "contract_version": "1.1.0"

# Check the new commit in Git
cd data-governance-platform/backend/contracts
git log --oneline   # should show v1.1.0 commit with approval comment
cd -
```

---

### Act 5 — Platform Admin Reviews Compliance

19. **Switch roles**: Click the **Switch Role** button or navigate to `http://localhost:3000` and select "Platform Admin"

20. **Open the Compliance Dashboard** (`/admin/dashboard`): View platform-wide analytics:

    - **Compliance Rate**: Percentage of datasets passing all critical policies
    - **Classification Breakdown**: Pie chart showing distribution across Public, Internal, Confidential, Restricted
    - **Top Violated Policies**: Bar chart highlighting which policies are most frequently violated (SD001 will be prominent)
    - **Dataset Growth**: Area chart showing datasets registered over time vs. violations
    - **Key Metrics**: Total datasets, published count, active violations, PII-containing datasets

> **What to point out in a demo**: The admin sees trends, not just snapshots. They can identify systemic issues (e.g., "teams consistently forget encryption documentation") and address them through training or tooling rather than one-off fixes.

**Quick verify via CLI** (pull the same metrics the dashboard displays):
```bash
curl http://localhost:8000/api/v1/policy/dashboard | python3 -m json.tool
# Returns: compliance_rate, total_datasets, active_violations, top_violated_policies

curl http://localhost:8000/api/v1/policy/reports | python3 -m json.tool
# Returns: violations grouped by policy ID with affected dataset names
```

---

### Act 6 — Examining the Audit Trail

21. **Navigate to Git History**: Click "Git History" in the sidebar (accessible from any role)

22. **View the commit timeline**: A visual timeline shows every contract change:
    - Initial contract creation for `customer_accounts` (v1.0.0)
    - Subscription approval generating new version (v1.1.0)
    - Each commit shows the author, timestamp, and message

23. **Click a commit**: View the full commit details:
    - Complete SHA hash
    - Author information
    - Timestamp
    - Full commit message describing what changed and why

24. **Browse contract files**: The sidebar lists all contract files. Click any file to see its history and content.

> **What to point out in a demo**: Every governance action is recorded in Git. There's no "who changed what and when?" ambiguity. This audit trail satisfies compliance requirements (SOX, GDPR, PCI-DSS) and makes governance transparent rather than opaque.

---

### Demo Summary

In this walkthrough, you demonstrated the complete governance lifecycle:

```
Data Owner                    Data Consumer
    │                              │
    ▼                              ▼
Register Dataset ──────►  Browse Catalog
    │                              │
    ▼                              ▼
Policy Validation          Request Access
(25 policies, violations        │
 caught with remediation)       │
    │                              │
    ▼                              ▼
Contract Generated ◄──── Steward Approves
(YAML + JSON, Git)         (SLA embedded)
    │                              │
    ▼                              ▼
Git Audit Trail ◄──────── New Contract Version
    │
    ▼
Admin Compliance Dashboard
(trends, metrics, analytics)
```

**Key messages to emphasize**:

1. **Prevention over detection** — Violations are caught at creation time, not after downstream breakage
2. **Actionable remediation** — Every violation includes step-by-step fix instructions
3. **Federated governance** — Central policies, local enforcement, mutual accountability (the UN Peacekeeping model)
4. **Everything is versioned** — Contracts, approvals, and SLA terms live in Git with full history
5. **Policy-as-Code** — Governance rules are YAML files that go through code review, not PDFs on SharePoint

---

## Stopping the Application

To shut everything down:

```bash
# Terminal 3 (Frontend):
# Press Ctrl+C (or Cmd+C on macOS) to stop Vite

# Terminal 2 (Backend):
# Press Ctrl+C (or Cmd+C on macOS) to stop Uvicorn
deactivate              # exit the Python virtual environment

# Terminal 1 (Database, from data-governance-platform/ directory):
docker-compose down     # stops and removes the container (data is preserved in Docker volume)
# docker-compose down -v   # full reset — also deletes the database volume and all demo data
```

> **macOS tip**: You can also stop all three services at once from a fourth terminal:
> ```bash
> cd data-governance-platform
> docker-compose down
> pkill -f "uvicorn app.main"
> pkill -f "vite"
> ```

---

## Troubleshooting

### macOS: `python3` not found or wrong version

```bash
# Check what version Homebrew installed
brew list | grep python
brew info python@3.12

# If multiple Python versions exist, use the explicit path
/opt/homebrew/bin/python3.12 -m venv venv
source venv/bin/activate
python3 --version   # should now show 3.12.x
```

### macOS: `node` not found after `brew install node@20`

```bash
# Homebrew installs node@20 as a "keg-only" formula — it isn't linked by default
brew link --force --overwrite node@20

# Or add it explicitly to your PATH
echo 'export PATH="/opt/homebrew/opt/node@20/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
node --version
```

### macOS: Docker Desktop not starting

Ensure Docker Desktop is running (whale icon in menu bar). If it isn't:
```bash
open /Applications/Docker.app
# Wait ~30 seconds for the daemon to start, then:
docker info   # should print system info without error
```

### Backend won't start

```bash
# Check Python version (must be 3.10+)
python3 --version

# Reinstall dependencies
pip install -r backend/requirements.txt --upgrade
```

### Frontend won't start

```bash
# Clear and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Database connection fails

```bash
# Check if container is running
docker ps | grep governance_postgres

# Restart the database
docker-compose down
docker-compose up -d

# Check logs for errors
docker logs governance_postgres
```

### API returns connection errors

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check if the PostgreSQL container is accessible
docker exec governance_postgres pg_isready -U governance_user
```

### Frontend shows blank page or API errors

```bash
# Verify the backend is running on port 8000
curl http://localhost:8000/api/v1/datasets/

# Check that vite proxy is configured (should show proxy to localhost:8000)
cat frontend/vite.config.js
```

### Optional: Enable Semantic Scanning

To enable the 8 LLM-powered semantic policies:

```bash
# Install Ollama (macOS)
brew install ollama

# Or download from ollama.com for other platforms

# Start Ollama and pull a model
ollama serve &
ollama pull llama3.2

# The backend auto-detects Ollama at http://localhost:11434
# Verify: curl http://localhost:8000/api/v1/semantic/status
```

---

*For more information, see the [project README](README.md), [Quick Start Guide](QUICKSTART.md), or the [interactive API docs](http://localhost:8000/api/docs).*
