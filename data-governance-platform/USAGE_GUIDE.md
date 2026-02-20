# Usage Guide: Hosting & Demo Walkthrough

## Table of Contents

- [Prerequisites](#prerequisites)
- [Part 1: Hosting on Your Laptop](#part-1-hosting-on-your-laptop)
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

---

## Part 1: Hosting on Your Laptop

You will open **three terminal windows** — one each for the database, backend, and frontend.

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
# Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate          # Windows

# Install dependencies
cd backend
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

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

Click any card to enter that role's dedicated interface. You can switch roles at any time using the sidebar navigation.

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

---

### Act 3 — Data Consumer Requests Access

9. **Switch roles**: Use the sidebar or navigate back to `http://localhost:3000` and select "Data Consumer"

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

---

### Act 4 — Data Steward Reviews and Approves

14. **Switch roles**: Navigate to `http://localhost:3000` and select "Data Steward"

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

---

### Act 5 — Platform Admin Reviews Compliance

19. **Switch roles**: Navigate to `http://localhost:3000` and select "Platform Admin"

20. **Open the Compliance Dashboard** (`/admin/dashboard`): View platform-wide analytics:

    - **Compliance Rate**: Percentage of datasets passing all critical policies
    - **Classification Breakdown**: Pie chart showing distribution across Public, Internal, Confidential, Restricted
    - **Top Violated Policies**: Bar chart highlighting which policies are most frequently violated (SD001 will be prominent)
    - **Dataset Growth**: Area chart showing datasets registered over time vs. violations
    - **Key Metrics**: Total datasets, published count, active violations, PII-containing datasets

> **What to point out in a demo**: The admin sees trends, not just snapshots. They can identify systemic issues (e.g., "teams consistently forget encryption documentation") and address them through training or tooling rather than one-off fixes.

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
# Terminal 3 (Frontend): Press Ctrl+C

# Terminal 2 (Backend): Press Ctrl+C
deactivate    # exit the Python virtual environment

# Terminal 1 (Database):
docker-compose down       # stops and removes the container
# docker-compose down -v  # also removes the database volume (full reset)
```

---

## Troubleshooting

### Backend won't start

```bash
# Check Python version (must be 3.10+)
python3 --version

# Reinstall dependencies
cd backend
pip install -r requirements.txt --upgrade
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
