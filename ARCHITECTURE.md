# Architecture & Design Document
## Data Governance Platform — Policy-as-Code PoC

**Version:** 1.0.0
**Date:** 2026-03-13
**Branch:** `claude/architecture-design-doc-y1s1H`

---

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Component Architecture](#4-component-architecture)
5. [Data Model](#5-data-model)
6. [Policy System Design](#6-policy-system-design)
7. [Roles & Access Model](#7-roles--access-model)
8. [Process & Information Flow by Role](#8-process--information-flow-by-role)
   - [8.1 Data Owner](#81-data-owner)
   - [8.2 Data Consumer](#82-data-consumer)
   - [8.3 Data Steward](#83-data-steward)
   - [8.4 Platform Admin](#84-platform-admin)
9. [End-to-End Subscription Workflow](#9-end-to-end-subscription-workflow)
10. [Contract Versioning & Git Integration](#10-contract-versioning--git-integration)
11. [Validation Pipeline](#11-validation-pipeline)
12. [API Surface](#12-api-surface)
13. [Frontend Architecture](#13-frontend-architecture)
14. [Security Model](#14-security-model)
15. [Deployment Architecture](#15-deployment-architecture)
16. [Design Decisions & Trade-offs](#16-design-decisions--trade-offs)

---

## 1. Overview

The Data Governance Platform is a production-ready proof-of-concept (PoC) implementing **federated data governance** using the UN Peacekeeping model — shared policies with distributed enforcement. The system prevents governance violations **before** they reach production by validating data contracts at publication time.

### Core Design Principles

| Principle | Implementation |
|-----------|---------------|
| **Prevention over detection** | Contracts are validated before publishing; violations are surfaced with actionable remediation |
| **Policy-as-Code** | All governance rules are version-controlled YAML files, not database records |
| **Federated enforcement** | A central policy engine enforces rules across independently registered datasets |
| **Immutable audit trail** | Every contract version is Git-committed; nothing is ever overwritten |
| **Intelligent orchestration** | Risk scoring selects between fast rule-based and deep semantic (LLM) validation |

### Key Capabilities

- **Policy-as-Code**: YAML-defined governance policies with automated rule-based and LLM-powered validation
- **Prevention at Borders**: Contracts validated before publication; violations surfaced with actionable remediation guidance
- **Intelligent Orchestration**: Four routing strategies (FAST, BALANCED, THOROUGH, ADAPTIVE) that select rule-based vs. semantic validation based on risk
- **End-to-End Subscription Workflow**: Data Owners register datasets → Data Consumers subscribe → Data Stewards approve → Contracts auto-generated and Git-versioned
- **Multi-Role Frontend**: Dedicated React UIs for Data Owners, Consumers, Stewards, and Platform Admins

---

## 2. System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (React + Vite)                    │
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐ │
│  │  Data Owner  │ │Data Consumer │ │ Data Steward │ │   Admin   │ │
│  │     UI       │ │     UI       │ │     UI       │ │    UI     │ │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬─────┘ │
│         └────────────────┴────────────────┴───────────────┘        │
│                              services/api.js (Axios)               │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │  HTTP /api/v1/*
┌──────────────────────────────────▼──────────────────────────────────┐
│                       BACKEND (FastAPI)                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    API Layer (Routers)                       │   │
│  │  datasets │ subscriptions │ git │ semantic │ orchestration   │   │
│  │  policy_authoring │ policy_dashboard │ policy_reports        │   │
│  │  policy_exchange  │ domain_governance │ policy_conflicts     │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                             │                                       │
│  ┌──────────────────────────▼──────────────────────────────────┐   │
│  │                   Service Layer                              │   │
│  │  ┌─────────────────┐  ┌──────────────────────────────────┐  │   │
│  │  │ ContractService │  │     PolicyOrchestrator           │  │   │
│  │  │   (481 LoC)     │  │         (538 LoC)                │  │   │
│  │  └────────┬────────┘  └───────┬──────────────────────────┘  │   │
│  │           │                   │                              │   │
│  │  ┌────────▼────────┐  ┌───────▼──────────────────────────┐  │   │
│  │  │   GitService    │  │  PolicyEngine  SemanticEngine     │  │   │
│  │  │   (317 LoC)     │  │   (342 LoC)     (461 LoC)        │  │   │
│  │  └────────┬────────┘  └───────┬──────────────────────────┘  │   │
│  └───────────┼───────────────────┼──────────────────────────────┘   │
│              │                   │                                   │
│  ┌───────────▼──────┐  ┌────────▼────────────────────────────┐     │
│  │  Git Contracts   │  │  Policy YAML Files                  │     │
│  │  backend/        │  │  backend/policies/                  │     │
│  │  contracts/      │  │  ├── sensitive_data_policies.yaml   │     │
│  │  (auto-managed)  │  │  ├── data_quality_policies.yaml     │     │
│  └──────────────────┘  │  ├── schema_governance_policies.yaml│     │
│                         │  └── semantic_policies.yaml         │     │
│  ┌──────────────────┐  └─────────────────────────────────────┘     │
│  │  SQLite (meta)   │                                               │
│  │  governance_     │  ┌─────────────────────────────────────┐     │
│  │  metadata.db     │  │  Ollama (LLM) — optional            │     │
│  └──────────────────┘  │  localhost:11434                    │     │
│                         │  mistral:7b (default)               │     │
│  ┌──────────────────┐  └─────────────────────────────────────┘     │
│  │  PostgreSQL 15   │                                               │
│  │  (demo dataset   │                                               │
│  │   schema source) │                                               │
│  └──────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────┘
```

### Layered Architecture Pattern

```
HTTP Request
    │
    ▼
FastAPI Router (api/)         — thin; validates Pydantic schema, calls service
    │
    ▼
Service Layer (services/)     — ALL business logic, policy enforcement, integrations
    │
    ▼
ORM Models (models/)          — pure SQLAlchemy; no business logic
    │
    ▼
Database (SQLite)             — metadata storage
    │
   also
    ▼
Policy Engine (policies/)     — rule-based YAML evaluation
    ▼
Semantic Engine (Ollama)      — optional LLM validation (disabled by default)
    ▼
Git Service (contracts/)      — contract version control
```

---

## 3. Technology Stack

### Backend

| Component | Technology | Version | Role |
|-----------|-----------|---------|------|
| Framework | FastAPI | 0.109.0 | REST API |
| Metadata DB | SQLite | bundled | Governance metadata storage |
| Demo DB | PostgreSQL | 15-alpine | Source schema introspection |
| ORM | SQLAlchemy | 2.0.25 | Database abstraction |
| Validation | Pydantic v2 | 2.5.3 | Request/response schemas |
| Config | pydantic-settings | 2.1.0 | Environment variable management |
| Git integration | GitPython | 3.1.41 | Contract version control |
| Policy files | PyYAML | 6.0.1 | Policy definition parsing |
| LLM client | Ollama (local) | — | Semantic policy evaluation |
| HTTP | httpx | 0.26.0 | Internal HTTP client |
| Server | uvicorn[standard] | 0.27.0 | ASGI server |
| Testing | pytest | 7.4.4 | 628 tests across 26 files |

### Frontend

| Component | Technology | Version | Role |
|-----------|-----------|---------|------|
| Framework | React | 18.2.0 | Component-based UI |
| Build tool | Vite | 5.0.8 | Dev server and bundler |
| State | Zustand | 4.4.7 | Global state management |
| HTTP client | Axios | 1.6.2 | API communication |
| Routing | React Router | 6.21.0 | Client-side navigation |
| Charts | Recharts | 2.10.3 | Compliance dashboards |
| Animation | Framer Motion | 10.16.16 | UI transitions |
| Icons | Lucide React | 0.303.0 | Icon set |
| Testing | Vitest + RTL | 1.0.4 / 14.1.2 | 92 frontend tests |

---

## 4. Component Architecture

### Backend Components

```
backend/
├── app/
│   ├── main.py              ← FastAPI app factory; registers all 11 routers
│   ├── config.py            ← Pydantic Settings; all env vars with defaults
│   ├── database.py          ← SQLAlchemy engine, session, DB init & seed data
│   ├── api/                 ← Route handlers (thin — delegate to services)
│   │   ├── datasets.py             Dataset CRUD + PostgreSQL schema import
│   │   ├── subscriptions.py        Subscription lifecycle + approval workflow
│   │   ├── git.py                  Git history & contract retrieval
│   │   ├── semantic.py             LLM semantic policy endpoints
│   │   ├── orchestration.py        Intelligent policy routing
│   │   ├── policy_authoring.py     Create/update authored policies
│   │   ├── policy_dashboard.py     Compliance metrics
│   │   ├── policy_reports.py       Reporting endpoints
│   │   ├── policy_exchange.py      Import/export
│   │   ├── policy_conflicts.py     Exception management
│   │   └── domain_governance.py    Domain-level governance
│   ├── models/              ← SQLAlchemy ORM models (no business logic)
│   │   ├── dataset.py              Data asset model
│   │   ├── contract.py             Contract + Git versioning model
│   │   ├── subscription.py         Access request model
│   │   ├── user.py                 User + role model
│   │   ├── policy_draft.py         Draft policy model
│   │   ├── policy_version.py       Policy version history model
│   │   ├── policy_artifact.py      Policy artifact model
│   │   └── policy_approval_log.py  Policy approval audit trail
│   ├── schemas/             ← Pydantic request/response schemas
│   │   ├── dataset.py              Dataset CRUD schemas + FieldSchema
│   │   ├── contract.py             Contract schemas
│   │   ├── subscription.py         Subscription schemas + SLA enums
│   │   └── policy.py               Policy schemas
│   └── services/            ← Business logic (all complexity lives here)
│       ├── contract_service.py        Contract generation + Git versioning (481 LoC)
│       ├── policy_engine.py           Rule-based YAML policy validation (342 LoC)
│       ├── semantic_policy_engine.py  LLM validation via Ollama (461 LoC)
│       ├── policy_orchestrator.py     Intelligent routing + risk scoring (538 LoC)
│       ├── postgres_connector.py      Schema introspection from PostgreSQL (557 LoC)
│       ├── git_service.py             Git operations — commit, tag, diff (317 LoC)
│       ├── ollama_client.py           HTTP client for local Ollama (237 LoC)
│       ├── authored_policy_loader.py  Load/manage authored policies (258 LoC)
│       └── policy_converter.py        YAML ↔ JSON format conversion (204 LoC)
├── policies/                ← YAML policy definitions (edit to change rules)
│   ├── sensitive_data_policies.yaml    5 PII/encryption policies (SD001–SD005)
│   ├── data_quality_policies.yaml      5 quality policies (DQ001–DQ005)
│   ├── schema_governance_policies.yaml 7 schema policies (SG001–SG007)
│   └── semantic_policies.yaml          8 LLM policies (SEM001–SEM008)
└── contracts/               ← Auto-managed Git repo for contract versions
```

### Frontend Components

```
frontend/src/
├── App.jsx                      ← Root router + AuthProvider
├── contexts/
│   └── AuthContext.jsx          ← Role-based auth context (login, logout, hasRole)
├── stores/
│   └── index.js                 ← Zustand stores (datasets, contracts, subscriptions, policies, git)
├── services/
│   └── api.js                   ← Single Axios instance; all API calls go here
├── pages/
│   ├── RoleSelector.jsx         ← Demo landing page; role picker
│   ├── Dashboard.jsx            ← Main metrics dashboard
│   ├── DataOwner/
│   │   ├── DatasetRegistrationWizard.jsx  ← 4-step registration form
│   │   └── OwnerDashboard.jsx             ← Violations & metrics view
│   ├── DataConsumer/
│   │   └── DataCatalogBrowser.jsx         ← Catalog browse + subscription flow
│   ├── DataSteward/
│   │   └── ApprovalQueue.jsx              ← Approval workflow queue
│   └── Admin/
│       └── ComplianceDashboard.jsx        ← Analytics + Recharts
├── components/
│   ├── Layout.jsx               ← Sidebar navigation layout
│   ├── TopNavLayout.jsx         ← Top navigation layout
│   ├── ErrorBoundary.jsx
│   ├── SkeletonLoader.jsx
│   ├── EmptyState.jsx
│   ├── CopyButton.jsx
│   └── PolicyAuthoring/         ← Policy editor components
│       ├── PolicyForm.jsx
│       ├── PolicyList.jsx
│       ├── PolicyDetail.jsx
│       ├── PolicyReview.jsx
│       ├── PolicyDashboard.jsx
│       ├── PolicyTimeline.jsx
│       ├── PolicyConflicts.jsx
│       ├── PolicyExchange.jsx
│       ├── DomainGovernance.jsx
│       └── ComplianceReport.jsx
└── test/
    ├── AuthContext.test.jsx     ← Role-based auth tests
    ├── api.test.js              ← Axios client tests
    ├── stores.test.js           ← Zustand store tests
    └── setup.js                 ← Test configuration
```

---

## 5. Data Model

### Entity Relationship Overview

```
User ─────────────────────────────────────────────────┐
  │  (owner)                                           │
  │                                                    │
  ▼                                                    │
Dataset ──────────────────────────────────────────┐   │
  │  (1 dataset : many contracts)                  │   │
  │  (1 dataset : many subscriptions)              │   │
  ▼                                                │   │
Contract ◄────────────────────── Subscription ────┘   │
  │  (versioned in Git)           │ (1 subscription :  │
  │  (approved_by FK → User) ─────┘   1 contract FK)   │
  │                               │                    │
  │                               └── consumer FK → User
  │
  └── approved_by FK → User (Steward)
```

### Core Entity Descriptions

#### Dataset
Represents a data asset registered on the platform.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Primary key |
| `name` | String | Dataset name |
| `description` | Text | Human-readable description |
| `owner_id` | FK → User | Owning user |
| `owner_name` | String | Owner display name |
| `owner_email` | String | Owner contact email |
| `source_type` | Enum | postgresql, csv, api, azure_blob, etc. |
| `classification` | Enum | public / internal / confidential / restricted |
| `contains_pii` | Boolean | PII presence flag |
| `compliance_tags` | JSON | [GDPR, CCPA, HIPAA, ...] |
| `schema_definition` | JSON | Array of `FieldSchema` objects |
| `status` | Enum | draft / published / deprecated |
| `created_at` | DateTime | Creation timestamp |
| `published_at` | DateTime | Publication timestamp |

#### Contract
Represents a versioned governance contract for a dataset.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Primary key |
| `dataset_id` | FK → Dataset | Parent dataset |
| `version` | String | Semantic version (e.g., 1.2.0) |
| `human_readable` | Text | YAML format for humans |
| `machine_readable` | JSON | Parsed JSON for systems |
| `schema_hash` | String | Hash to detect schema changes |
| `governance_rules` | JSON | Active policy rules |
| `quality_rules` | JSON | Quality thresholds |
| `sla_requirements` | JSON | Consumer SLA requirements |
| `validation_status` | Enum | PASSED / WARNING / FAILED |
| `validation_results` | JSON | Detailed violation list |
| `git_commit_hash` | String | Git commit SHA |
| `git_file_path` | String | Path in contracts repo |
| `approved_by` | FK → User | Approving steward |
| `approved_at` | DateTime | Approval timestamp |

#### Subscription
Represents a data consumer's access request.

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Primary key |
| `dataset_id` | FK → Dataset | Target dataset |
| `contract_id` | FK → Contract | Linked contract |
| `consumer_id` | FK → User | Requesting consumer |
| `consumer_name` | String | Consumer display name |
| `consumer_team` | String | Consumer's team |
| `purpose` | Text | Stated data use purpose |
| `use_case` | Enum | analytics / ml_training / reporting / etc. |
| `sla_freshness` | Enum | real-time / 1h / 6h / 24h / weekly / monthly |
| `sla_availability` | Enum | Availability SLA |
| `quality_completeness` | Float | Minimum completeness % required |
| `status` | Enum | pending / approved / rejected / cancelled |
| `approved_by` | FK → User | Approving steward |
| `access_endpoint` | String | Granted access endpoint |
| `expires_at` | DateTime | Access expiry time |

#### User

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Primary key |
| `email` | String (unique) | Login email |
| `username` | String (unique) | Display username |
| `role` | Enum | data_owner / data_consumer / data_steward / admin |
| `team` | String | Organizational team |
| `department` | String | Organizational department |
| `is_active` | Boolean | Active flag |

---

## 6. Policy System Design

### Policy Architecture

The platform implements a **four-tier policy system** combining deterministic and semantic validation:

```
┌─────────────────────────────────────────────────────────────┐
│                     Policy System                            │
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │   Rule-Based Engine   │  │     Semantic Engine (LLM)    │ │
│  │   PolicyEngine        │  │   SemanticPolicyEngine       │ │
│  │                       │  │   (disabled by default)      │ │
│  │  SD001–SD005 (5)     │  │                              │ │
│  │  DQ001–DQ005 (5)     │  │   SEM001–SEM008 (8)         │ │
│  │  SG001–SG007 (7)     │  │   via Ollama/mistral:7b      │ │
│  │                       │  │                              │ │
│  │  17 deterministic     │  │   8 context-aware policies   │ │
│  │  YAML rules           │  │   LLM prompt templates       │ │
│  └──────────┬────────────┘  └─────────────┬────────────────┘ │
│             └──────────────┬──────────────┘                  │
│                            ▼                                  │
│              ┌─────────────────────────┐                     │
│              │   PolicyOrchestrator    │                     │
│              │   Intelligent Routing   │                     │
│              │   Risk Scoring (0-100)  │                     │
│              └─────────────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

### Policy Categories

#### Sensitive Data Policies (SD001–SD005)

| ID | Name | Severity | Rule Summary |
|----|------|----------|-------------|
| SD001 | pii_encryption_required | Critical | PII fields → encryption_required: true |
| SD002 | retention_policy_required | Critical | confidential/restricted → retention_days must be set |
| SD003 | pii_compliance_tags | Warning | PII fields → compliance_tags must not be empty |
| SD004 | restricted_use_cases | Critical | restricted classification → approved_use_cases must be set |
| SD005 | cross_border_pii | Critical | PII + multi-region → data_residency must be specified |

#### Data Quality Policies (DQ001–DQ005)

| ID | Name | Severity | Rule Summary |
|----|------|----------|-------------|
| DQ001 | critical_data_completeness | Critical | confidential/restricted → completeness ≥ 95% |
| DQ002 | freshness_sla_required | Warning | Temporal datasets → freshness_sla should be set |
| DQ003 | uniqueness_specification | Warning | Key fields → uniqueness_fields should be set |
| DQ004 | accuracy_threshold_alignment | Warning | restricted → accuracy ≥ 99%; confidential → ≥ 95% |
| DQ005 | completeness_threshold_defined | Warning | All datasets → completeness_threshold should be defined |

**Quality Tiers:**

| Tier | Completeness | Accuracy | Freshness |
|------|-------------|---------|-----------|
| Gold (mission-critical) | ≥ 99% | ≥ 99% | 1h |
| Silver (standard business) | ≥ 95% | ≥ 95% | 24h |
| Bronze (raw/exploratory) | ≥ 90% | ≥ 90% | weekly |

#### Schema Governance Policies (SG001–SG007)

| ID | Name | Severity | Rule Summary |
|----|------|----------|-------------|
| SG001 | field_documentation_required | Warning | All fields → description must not be empty |
| SG002 | required_field_consistency | Critical | required: true → nullable must be false |
| SG003 | dataset_ownership_required | Critical | owner_name + owner_email must be set |
| SG004 | string_field_constraints | Warning | String fields → max_length should be set |
| SG005 | enum_value_specification | Warning | Enum fields → enum_values should be listed |
| SG006 | breaking_schema_changes | Critical | Breaking changes → major version bump required |
| SG007 | numeric_field_constraints | Warning | Integer/float fields → min/max values should be set |

#### Semantic Policies (SEM001–SEM008)

| ID | Name | Severity | What the LLM Checks |
|----|------|----------|---------------------|
| SEM001 | sensitive_data_context_detection | Critical | Context-aware PII detection beyond name patterns |
| SEM002 | business_logic_consistency | Warning | Logical inconsistencies in governance rules |
| SEM003 | security_pattern_detection | Critical | Schema patterns suggesting security vulnerabilities |
| SEM004 | compliance_intent_verification | Critical | Whether stated compliance tags actually apply |
| SEM005 | data_quality_semantic_validation | Warning | Whether quality thresholds make semantic sense |
| SEM006 | field_relationship_analysis | Warning | Field combinations that together become sensitive |
| SEM007 | naming_convention_analysis | Info | Clarity and consistency of naming |
| SEM008 | use_case_appropriateness | Warning | Whether use cases are appropriate for classification |

### Orchestration Strategies

The `PolicyOrchestrator` routes each validation request through a risk-scoring pipeline:

```
Contract → Risk Analysis → Strategy Selection → Execution → Result Combining
              │
              ├── classification (restricted = higher risk)
              ├── PII presence (+20 risk points)
              ├── compliance frameworks (+10 per framework)
              └── field count (complexity score)
```

| Strategy | Trigger | Engines Used | Approx. Time |
|----------|---------|-------------|-------------|
| FAST | Low risk, no PII, public data | Rule-based only | ~0.1s |
| BALANCED | Moderate risk | Rule-based + targeted semantic | ~3s |
| THOROUGH | High risk, PII, restricted | Rule-based + all semantic | ~24s |
| ADAPTIVE | Unknown/mixed (default) | Risk-based dynamic selection | Variable |

---

## 7. Roles & Access Model

### Role Definitions

The platform defines four distinct roles, each with dedicated UI views and API access patterns:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Role Hierarchy                               │
│                                                                     │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐  ┌─────────┐ │
│  │ Data Owner  │   │Data Consumer│   │Data Steward │  │  Admin  │ │
│  │             │   │             │   │             │  │         │ │
│  │ Registers   │   │ Discovers   │   │ Approves    │  │ Views   │ │
│  │ datasets    │   │ datasets    │   │ subscriptions│  │ global  │ │
│  │             │   │             │   │             │  │ metrics │ │
│  │ Manages     │   │ Subscribes  │   │ Rejects     │  │         │ │
│  │ schema      │   │ for access  │   │ requests    │  │ Reports │ │
│  │             │   │             │   │             │  │         │ │
│  │ Views       │   │ Views own   │   │ Generates   │  │ Policy  │ │
│  │ violations  │   │ contracts   │   │ contracts   │  │ mgmt    │ │
│  └─────────────┘   └─────────────┘   └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Role Capabilities Matrix

| Capability | Data Owner | Data Consumer | Data Steward | Admin |
|-----------|:----------:|:-------------:|:------------:|:-----:|
| Register dataset | ✓ | — | — | ✓ |
| Edit own dataset | ✓ | — | — | ✓ |
| Import PostgreSQL schema | ✓ | — | — | ✓ |
| View dataset catalog | ✓ | ✓ | ✓ | ✓ |
| View dataset details | ✓ | ✓ | ✓ | ✓ |
| Create subscription request | — | ✓ | — | — |
| Approve/reject subscription | — | — | ✓ | ✓ |
| View subscription queue | — | Own only | All | All |
| View contracts | ✓ | Own only | All | All |
| View Git history | ✓ | — | ✓ | ✓ |
| View compliance dashboard | — | — | — | ✓ |
| Manage policies | — | — | — | ✓ |
| Export/import policies | — | — | — | ✓ |
| View violation reports | ✓ (own) | — | All | All |

---

## 8. Process & Information Flow by Role

### 8.1 Data Owner

**Who:** Team or individual responsible for a data asset. Registers datasets, maintains schema accuracy, and acts on governance violations.

#### Process Flow

```
Data Owner
    │
    ▼
1. SELECT ROLE
   RoleSelector.jsx → login as DataOwner
   Navigate to /owner/register
    │
    ▼
2. REGISTER DATASET (DatasetRegistrationWizard.jsx — 4 steps)
   Step 1: Basic Info (name, description, classification, source type)
   Step 2: Schema Definition (field names, types, PII flags, constraints)
   Step 3: Governance Rules (encryption, retention, compliance tags, use cases)
   Step 4: Quality Rules (completeness %, accuracy %, freshness SLA)
    │
    ▼
3. POST /api/v1/datasets/
   → datasets.py router
   → ContractService.create_contract_from_dataset()
   → PolicyEngine.validate() [runs 17 rule-based checks]
   → PolicyOrchestrator.validate_contract() [optional: semantic checks]
    │
    ▼
4. AUTOMATIC CONTRACT GENERATION
   ContractService generates YAML + JSON contract
   GitService commits contract to backend/contracts/{name}_v1.0.0.yaml
   Contract is stored in DB with validation_status = PASSED/WARNING/FAILED
    │
    ▼
5. VIEW VIOLATIONS (OwnerDashboard.jsx)
   GET /api/v1/policy-dashboard/ → compliance metrics
   Violations displayed with:
     - Policy ID (e.g., SD001)
     - Severity (critical/warning)
     - Description of the violation
     - Remediation steps
    │
    ▼
6. REMEDIATE & RE-PUBLISH
   Owner corrects schema/governance fields
   PUT /api/v1/datasets/{id}
   → ContractService creates new version (e.g., v1.1.0)
   → New Git commit
   → Re-validation
```

#### Information Flow for Data Owner

```
Owner Input (Form)
    │
    │  dataset name, classification, schema fields (name, type, pii flag),
    │  governance (encryption, retention, compliance tags),
    │  quality_rules (completeness_threshold, freshness_sla)
    ▼
POST /api/v1/datasets/
    │
    │  DatasetCreate schema (Pydantic validation)
    ▼
datasets.py router
    │
    │  calls ContractService.create_contract_from_dataset(dataset, db)
    ▼
ContractService
    │
    │  builds contract dict from dataset attributes
    │  serializes to YAML (human_readable) + JSON (machine_readable)
    │  generates schema_hash for change detection
    ▼
PolicyEngine.validate(contract)
    │
    │  reads all 17 YAML policies
    │  evaluates each rule against contract fields
    │  returns: { status, violations: [{id, severity, message, remediation}] }
    ▼
PolicyOrchestrator (if ADAPTIVE/THOROUGH)
    │
    │  risk_score = f(classification, pii_presence, compliance_tags, field_count)
    │  if risk > threshold: SemanticPolicyEngine.validate(contract)
    │    └── Ollama HTTP POST → LLM response → parsed violations
    ▼
ContractService stores contract in DB
    │
    │  Contract record created with validation_status, validation_results
    ▼
GitService.commit_contract(name, version, yaml_content)
    │
    │  writes {dataset_name}_v{version}.yaml to backend/contracts/
    │  git add, git commit with author + timestamp
    │  returns git_commit_hash
    ▼
API Response → DatasetResponse schema
    │
    │  { id, name, status, contracts: [{version, validation_status, violations}] }
    ▼
Frontend OwnerDashboard renders violations with remediation guidance
```

---

### 8.2 Data Consumer

**Who:** Analyst, data scientist, or application team wanting access to a dataset. Browses the catalog, requests subscriptions, and receives access credentials.

#### Process Flow

```
Data Consumer
    │
    ▼
1. SELECT ROLE
   RoleSelector.jsx → login as DataConsumer
   Navigate to /consumer/catalog
    │
    ▼
2. BROWSE CATALOG (DataCatalogBrowser.jsx)
   GET /api/v1/datasets/ → list all published datasets
   Filters: classification, contains_pii, search text
   View: name, description, owner, classification badge, schema preview
    │
    ▼
3. VIEW DATASET DETAILS
   GET /api/v1/datasets/{id} → full dataset info
   View: schema fields (types, PII flags), governance rules, quality SLAs,
         compliance tags, current contract version
    │
    ▼
4. REQUEST SUBSCRIPTION
   POST /api/v1/subscriptions/
   Consumer fills:
     - purpose (free text)
     - use_case (analytics / ml_training / reporting / compliance / other)
     - sla_freshness, sla_availability, sla_query_performance
     - quality_completeness, quality_accuracy
   Status set to: PENDING
    │
    ▼
5. AWAIT APPROVAL
   Subscription enters Data Steward's queue
   Consumer can view status at /consumer/subscriptions (own only)
    │
    ▼
6. ACCESS GRANTED (on approval)
   Consumer receives:
     - access_endpoint
     - access_credentials (connection string / API key)
     - contract link (version tied to their subscription)
     - expires_at (access expiry)
```

#### Information Flow for Data Consumer

```
Consumer browses
    │
    │  GET /api/v1/datasets/ with query filters
    ▼
DatasetResponse[] → frontend renders catalog cards
    │
    │  Consumer clicks dataset → GET /api/v1/datasets/{id}
    ▼
Full DatasetResponse (schema, governance, quality_rules, contracts[])
    │
    │  Consumer fills subscription form
    ▼
POST /api/v1/subscriptions/
    │  { dataset_id, purpose, use_case, sla_freshness, ... }
    ▼
subscriptions.py router → Subscription record created (status=pending)
    │
    │  notification path: subscription appears in steward queue
    ▼
Consumer polls GET /api/v1/subscriptions/?consumer_id=me
    │
    │  On approval: SubscriptionResponse includes access_endpoint + credentials
    ▼
Consumer reads ContractViewer:
    GET /api/v1/git/contracts → list all versioned contracts
    GET /api/v1/git/contracts/{name}/history → full version history
```

---

### 8.3 Data Steward

**Who:** Governance officer or data team lead who reviews subscription requests, approves or rejects access, and ensures contracts meet compliance requirements.

#### Process Flow

```
Data Steward
    │
    ▼
1. SELECT ROLE
   RoleSelector.jsx → login as DataSteward
   Navigate to /steward/approvals
    │
    ▼
2. VIEW APPROVAL QUEUE (ApprovalQueue.jsx)
   GET /api/v1/subscriptions/?status=pending
   Queue shows: consumer name, dataset, purpose, use_case, SLA requirements
    │
    ▼
3. REVIEW SUBSCRIPTION REQUEST
   View: consumer's team, stated purpose, requested SLA
   View: dataset's current contract + validation status
   View: any open violations on the dataset
    │
    ▼
4a. APPROVE
    PUT /api/v1/subscriptions/{id}/approve
    Steward provides:
      - approved: true
      - approval_comments (optional)
      - access_credentials (connection string / API key)
      - access_endpoint
    │
    ▼
    CONTRACT VERSION CREATED
    ContractService.enrich_contract_with_slas(contract, subscription)
    ContractService.add_subscription_to_contract()
    New contract version committed to Git (e.g., v1.2.0)
    Subscription status → APPROVED, access_granted = true
    │
    ▼
4b. REJECT
    PUT /api/v1/subscriptions/{id}/approve
    Steward provides:
      - approved: false
      - rejection_reason (required)
    Subscription status → REJECTED
    Consumer is informed via subscription status update
```

#### Information Flow for Data Steward

```
GET /api/v1/subscriptions/?status=pending
    │
    │  SubscriptionResponse[] (all pending requests)
    ▼
ApprovalQueue renders queue with consumer + dataset context

Steward reviews:
    GET /api/v1/datasets/{dataset_id} → current schema + governance
    GET /api/v1/git/contracts/{name}/history → version history
    GET /api/v1/policy-dashboard/ → compliance score
    │
    ▼
PUT /api/v1/subscriptions/{id}/approve
    │  SubscriptionApproval { approved, comments, credentials, endpoint }
    ▼
subscriptions.py router
    │
    │  updates subscription: status=approved, access_granted=true,
    │  access_credentials, access_endpoint, approved_by, approved_at
    │
    │  calls ContractService.add_subscription_to_contract()
    ▼
ContractService
    │
    │  loads current contract version
    │  enriches with subscription SLA requirements
    │  increments version (1.0.0 → 1.1.0 for minor additions)
    │  serializes new YAML + JSON
    ▼
GitService.commit_contract(name, new_version, yaml)
    │
    │  writes new contract file to backend/contracts/
    │  commits with message: "Add subscription {id} to {dataset} contract"
    │  returns new git_commit_hash
    ▼
Contract record in DB updated with:
    new version, git_commit_hash, approved_by=steward.id, approved_at=now
    │
    ▼
API Response → 200 OK with updated SubscriptionResponse
    │
    │  Consumer sees: status=approved, access_endpoint, credentials
```

---

### 8.4 Platform Admin

**Who:** Platform engineering or data governance lead responsible for platform-wide compliance metrics, policy management, and reporting.

#### Process Flow

```
Platform Admin
    │
    ▼
1. SELECT ROLE
   RoleSelector.jsx → login as Admin
   Navigate to /admin/compliance
    │
    ▼
2. VIEW COMPLIANCE DASHBOARD (ComplianceDashboard.jsx)
   GET /api/v1/policy-dashboard/ → compliance metrics
   Recharts visualizations:
     - Overall compliance score (%)
     - Violations by severity (critical/warning)
     - Violations by policy category (SD/DQ/SG)
     - Trend over time
    │
    ▼
3. VIEW DETAILED REPORTS
   GET /api/v1/policy-reports/ → detailed violation reports
   Filters: by dataset, by policy, by severity, date range
   Export: CSV / JSON
    │
    ▼
4. MANAGE POLICIES (PolicyManager.jsx)
   GET /api/v1/policy-authoring/ → all authored policies
   Admin can:
     - Create new policies (POST /api/v1/policy-authoring/)
     - Edit existing policies
     - View policy version timeline
     - Manage policy exceptions/conflicts
    │
    ▼
5. IMPORT / EXPORT POLICIES
   POST /api/v1/policy-exchange/export → download policy bundle
   POST /api/v1/policy-exchange/import → upload policy bundle
   Share governance rules across environments/teams
    │
    ▼
6. DOMAIN GOVERNANCE
   GET /api/v1/domain-governance/ → domain-level metrics
   View governance health per organizational domain
   Identify domains with high violation rates
    │
    ▼
7. POLICY CONFLICTS / EXCEPTIONS
   GET /api/v1/policy-conflicts/ → active exceptions
   Review datasets where policy exceptions have been granted
   Approve or reject exception requests
```

#### Information Flow for Platform Admin

```
GET /api/v1/policy-dashboard/
    │
    │  { total_datasets, compliant_count, violation_count,
    │    violations_by_severity, violations_by_category,
    │    compliance_score_percent }
    ▼
ComplianceDashboard renders Recharts graphs

GET /api/v1/policy-reports/
    │
    │  { datasets: [{ id, name, violations: [{policy_id, severity, message}] }] }
    ▼
Admin can drill into individual dataset reports

POST /api/v1/policy-authoring/
    │  { id, name, severity, rule, remediation, category }
    ▼
policy_authoring.py → AuthoredPolicyLoader stores new policy
    │
    │  Policy versioned in DB (policy_version table)
    │  Approval audit trail written (policy_approval_log table)
    ▼
New policy is active for all future validations

GET /api/v1/domain-governance/
    │
    │  { domains: [{ name, dataset_count, compliance_score, top_violations }] }
    ▼
Admin identifies governance hot spots by domain
```

---

## 9. End-to-End Subscription Workflow

This is the core workflow of the platform — a fully lifecycle-managed process from dataset discovery to access granting with an immutable audit trail.

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Data Owner  │     │ Data Consumer│     │Data Steward │     │   Platform  │
│             │     │             │     │             │     │  (System)   │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       │ 1. Register       │                   │                   │
       │    Dataset        │                   │                   │
       ├──────────────────────────────────────────────────────────►│
       │                   │                   │           Auto-validate
       │                   │                   │           contract
       │                   │                   │           (PolicyEngine)
       │◄──────────────────────────────────────────────────────────┤
       │   Violations      │                   │                   │
       │   surfaced        │                   │                   │
       │                   │                   │                   │
       │ 2. Remediate      │                   │                   │
       │    & Re-publish   │                   │                   │
       ├──────────────────────────────────────────────────────────►│
       │                   │                   │           New contract
       │                   │                   │           committed to Git
       │◄──────────────────────────────────────────────────────────┤
       │   Contract v1.0.0 │                   │                   │
       │   PASSED          │                   │                   │
       │                   │                   │                   │
       │                   │ 3. Browse Catalog │                   │
       │                   ├──────────────────────────────────────►│
       │                   │◄──────────────────────────────────────┤
       │                   │   Dataset list    │                   │
       │                   │                   │                   │
       │                   │ 4. Request        │                   │
       │                   │    Subscription   │                   │
       │                   ├──────────────────────────────────────►│
       │                   │                   │           Subscription
       │                   │                   │           created: PENDING
       │                   │                   │◄──────────────────┤
       │                   │                   │   Queue updated   │
       │                   │                   │                   │
       │                   │                   │ 5. Review &       │
       │                   │                   │    Approve        │
       │                   │                   ├──────────────────►│
       │                   │                   │           Contract enriched
       │                   │                   │           with SLAs
       │                   │                   │           New version committed
       │                   │                   │           to Git (v1.1.0)
       │                   │                   │◄──────────────────┤
       │                   │                   │   Subscription    │
       │                   │                   │   APPROVED        │
       │                   │◄──────────────────┼───────────────────┤
       │                   │   Access granted  │                   │
       │                   │   Credentials     │                   │
       │                   │   Contract link   │                   │
       │                   │                   │                   │
```

### Workflow State Machine

```
Subscription States:
                    ┌─────────┐
                    │ PENDING │
                    └────┬────┘
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
         ┌──────────┐         ┌──────────┐
         │ APPROVED │         │ REJECTED │
         └────┬─────┘         └──────────┘
              │
              ▼
         ┌──────────┐
         │CANCELLED │  (consumer can cancel)
         └──────────┘

Contract Versions generated at:
  - Dataset registration    → v1.0.0
  - Schema update           → v1.1.0 (minor) or v2.0.0 (breaking)
  - Subscription approval   → minor version bump + SLA requirements added
```

---

## 10. Contract Versioning & Git Integration

### Contract Version Control Architecture

```
backend/contracts/  (auto-initialized Git repo)
    │
    ├── customer_accounts_v1.0.0.yaml    ← initial registration
    ├── customer_accounts_v1.1.0.yaml    ← after first subscription approval
    ├── customer_accounts_v1.2.0.yaml    ← after second subscription
    ├── transaction_ledger_v1.0.0.yaml
    └── ...
```

Every contract file contains:

```yaml
# customer_accounts_v1.1.0.yaml
dataset_name: customer_accounts
version: 1.1.0
classification: confidential
owner: Jane Smith <jane@company.com>
schema:
  - name: account_id
    type: integer
    required: true
    nullable: false
  - name: ssn
    type: string
    pii: true
governance:
  encryption_required: true
  retention_days: 2555
  compliance_tags: [GDPR, CCPA]
quality_rules:
  completeness_threshold: 99
  accuracy_threshold: 99
  freshness_sla: "24h"
sla_requirements:  # added by subscription approval
  - consumer_team: analytics
    freshness: 24h
    availability: 99.9%
validation:
  status: PASSED
  validated_at: 2026-03-13T10:00:00Z
  policy_version: 1.0.0
```

### Git Commit Strategy

| Event | Git Action | Commit Message Pattern |
|-------|-----------|----------------------|
| Dataset registered | `git commit` | `Add contract for {dataset} v{version}` |
| Schema updated | `git commit` | `Update contract for {dataset} v{version}` |
| Subscription approved | `git commit` | `Add subscription {id} to {dataset} contract` |
| Policy validated | `git tag` | `{dataset}-v{version}-validated` |

---

## 11. Validation Pipeline

### Full Validation Flow

```
Contract Input (YAML or dict)
         │
         ▼
┌────────────────────────┐
│  PolicyOrchestrator    │
│  validate_contract()   │
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│  _analyze_contract()   │   Computes:
│                        │   - risk_level (LOW/MEDIUM/HIGH/CRITICAL)
│                        │   - has_pii (boolean)
│                        │   - compliance_frameworks (list)
│                        │   - complexity_score (0-100)
└────────┬───────────────┘
         │
         ▼
┌────────────────────────┐
│ _make_orchestration_   │   Selects:
│    decision()          │   - strategy (FAST/BALANCED/THOROUGH/ADAPTIVE)
│                        │   - which semantic policies to run
│                        │   - whether to use LLM at all
└────────┬───────────────┘
         │
         ▼
┌────────────────────────────────────────────────────┐
│              _execute_validation()                  │
│                                                    │
│  ┌─────────────────────┐  ┌──────────────────────┐ │
│  │  PolicyEngine       │  │ SemanticPolicyEngine  │ │
│  │  .validate()        │  │  .validate()          │ │
│  │                     │  │  (if LLM enabled)     │ │
│  │  17 YAML rules      │  │  8 Ollama prompts     │ │
│  │  evaluated in order │  │  evaluated in order   │ │
│  └──────────┬──────────┘  └──────────┬────────────┘ │
│             └─────────────────────────┘              │
└────────────────────────┬───────────────────────────┘
                         │
                         ▼
               ┌──────────────────────┐
               │ _combine_results()   │
               │                     │
               │ - Deduplicate        │
               │ - Prioritize by      │
               │   severity           │
               │ - Apply exceptions   │
               └──────────┬──────────┘
                          │
                          ▼
               ValidationResult {
                 status: PASSED|WARNING|FAILED,
                 violations: [{
                   policy_id, severity,
                   message, remediation
                 }],
                 strategy_used,
                 execution_time_ms
               }
```

### Violation Severity Definitions

| Severity | Meaning | Action Required |
|----------|---------|----------------|
| `critical` | Dataset cannot be published until resolved | Block publication |
| `warning` | Dataset can be published but should be addressed | Alert owner |
| `info` | Informational recommendation | Log only |

---

## 12. API Surface

All routes are prefixed with `/api/v1`.

### Dataset Endpoints

| Method | Path | Description | Primary Role |
|--------|------|-------------|-------------|
| `POST` | `/datasets/` | Register dataset (triggers validation + contract gen) | Data Owner |
| `GET` | `/datasets/` | List all datasets with optional filters | All |
| `GET` | `/datasets/{id}` | Get dataset details | All |
| `PUT` | `/datasets/{id}` | Update dataset (creates new contract version) | Data Owner |
| `DELETE` | `/datasets/{id}` | Soft-delete dataset | Data Owner |
| `POST` | `/datasets/import-schema` | Import schema from PostgreSQL | Data Owner |
| `POST` | `/datasets/{id}/refresh-schema` | Re-import schema from PostgreSQL | Data Owner |
| `GET` | `/datasets/postgres/tables` | List PostgreSQL tables | Data Owner |

### Subscription Endpoints

| Method | Path | Description | Primary Role |
|--------|------|-------------|-------------|
| `POST` | `/subscriptions/` | Create subscription request | Data Consumer |
| `GET` | `/subscriptions/` | List subscriptions (filtered) | All |
| `GET` | `/subscriptions/{id}` | Get subscription details | All |
| `PUT` | `/subscriptions/{id}/approve` | Approve or reject request | Data Steward |
| `PUT` | `/subscriptions/{id}` | Update pending subscription | Data Consumer |
| `DELETE` | `/subscriptions/{id}` | Cancel subscription | Data Consumer |

### Contract & Git Endpoints

| Method | Path | Description | Primary Role |
|--------|------|-------------|-------------|
| `GET` | `/git/contracts` | List all versioned contracts | All |
| `GET` | `/git/contracts/{name}/history` | Contract version history | All |
| `GET` | `/git/diff` | Diff between two commits | Data Steward, Admin |

### Policy & Compliance Endpoints

| Method | Path | Description | Primary Role |
|--------|------|-------------|-------------|
| `POST` | `/semantic/scan` | Run LLM semantic policy scan | Admin |
| `POST` | `/orchestration/validate` | Validate via intelligent orchestrator | Admin |
| `GET` | `/policy-dashboard/` | Compliance metrics summary | Admin |
| `GET` | `/policy-reports/` | Detailed compliance reports | Admin |
| `POST` | `/policy-authoring/` | Create authored policy | Admin |
| `POST` | `/policy-exchange/export` | Export policies | Admin |
| `POST` | `/policy-exchange/import` | Import policies | Admin |
| `GET` | `/domain-governance/` | Domain-level governance rules | Admin |
| `GET` | `/policy-conflicts/` | List policy exceptions | Admin |

---

## 13. Frontend Architecture

### State Management Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend State                            │
│                                                             │
│  ┌──────────────────────────────────┐                       │
│  │        AuthContext               │  (React Context)       │
│  │  user { id, name, email, role }  │                       │
│  │  login(), logout(), hasRole()    │                       │
│  └──────────────────────────────────┘                       │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Zustand Stores                       │ │
│  │                                                        │ │
│  │  useDatasetStore    useContractStore                   │ │
│  │  { datasets,        { contracts,                       │ │
│  │    currentDataset,    currentContract,                 │ │
│  │    loading, error }   validationResult }               │ │
│  │                                                        │ │
│  │  useSubscriptionStore  usePolicyStore  useGitStore     │ │
│  │  { subscriptions,      { policies }    { history,      │ │
│  │    approveSubscription  loading }        contracts,    │ │
│  │    rejectSubscription }                  currentDiff } │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌──────────────────────────────────┐                       │
│  │         services/api.js          │  (Axios singleton)    │
│  │  datasetAPI, contractAPI,        │                       │
│  │  subscriptionAPI, policyAPI,     │                       │
│  │  gitAPI, policyAuthoringAPI...   │                       │
│  └──────────────────────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Navigation Structure by Role

```
Role: DataOwner → /owner/*
  /owner/register          DatasetRegistrationWizard
  /owner/dashboard         OwnerDashboard (violations, metrics)
  /owner/datasets          DatasetCatalog (own datasets)
  /owner/datasets/:id      DatasetDetail
  /owner/git               GitHistory (own dataset contracts)

Role: DataConsumer → /consumer/*
  /consumer/catalog        DataCatalogBrowser
  /consumer/datasets/:id   DatasetDetail
  /consumer/subscriptions  SubscriptionQueue (own only)
  /consumer/contracts      ContractViewer (own only)

Role: DataSteward → /steward/*
  /steward/approvals       ApprovalQueue
  /steward/datasets        DatasetCatalog (all)
  /steward/contracts       ContractViewer (all)
  /steward/git             GitHistory

Role: Admin → /admin/*
  /admin/compliance        ComplianceDashboard (Recharts)
  /admin/policies          PolicyManager
  /admin/reports           ComplianceReport
  /admin/domains           DomainGovernance
  /admin/conflicts         PolicyConflicts
  /admin/exchange          PolicyExchange
  /admin/datasets          DatasetCatalog (all)
```

### API Communication Pattern

All components communicate with the backend exclusively through `services/api.js`:

```
Component
    │
    │  import { datasetAPI } from '../../services/api'
    │  const data = await datasetAPI.getAll()
    ▼
services/api.js (Axios instance)
    │
    │  Interceptor adds: Authorization: Bearer {token}
    │  Base URL: http://localhost:8000
    ▼
FastAPI Backend /api/v1/*
    │
    │  Response interceptor: 401 → redirect to /login
    ▼
Component updates state via Zustand store
```

---

## 14. Security Model

### Authentication

The current PoC uses **simulated role-based authentication**:
- `RoleSelector.jsx` sets the user role on login
- `AuthContext.jsx` persists user + token to `localStorage`
- All API requests include `Authorization: Bearer {token}` header
- Backend validates role-based access at the router level

> **Production note:** Replace simulated auth with OAuth 2.0 / OIDC (e.g., Keycloak, Auth0) for production deployment. The `User` model is pre-wired for `hashed_password` and JWT tokens.

### Data Classification Security Controls

| Classification | Encryption Required | Retention Required | Compliance Tags | Use Cases Required |
|---------------|:------------------:|:-----------------:|:---------------:|:------------------:|
| Public | — | — | — | — |
| Internal | — | — | — | — |
| Confidential | ✓ | ✓ | ✓ | — |
| Restricted | ✓ | ✓ | ✓ | ✓ |

### LLM Security Considerations

- Semantic engine is **disabled by default** (`ENABLE_LLM_VALIDATION=false`)
- Ollama runs **locally** — no data leaves the network
- LLM prompts include only schema metadata (field names, types) — **not actual data values**
- Confidence threshold (70%) filters low-confidence LLM assertions

---

## 15. Deployment Architecture

### Development Environment

```
Browser (localhost:3000)
    │
    │  Vite dev server (proxies /api → localhost:8000)
    ▼
React App
    │
    │  HTTP /api/v1/*
    ▼
FastAPI (uvicorn, localhost:8000)
    │
    ├── SQLite (governance_metadata.db)
    ├── Git (backend/contracts/)
    ├── YAML policies (backend/policies/)
    └── PostgreSQL (Docker, localhost:5432) [optional]
    └── Ollama (localhost:11434) [optional]
```

### Environment Variables

| Variable | Default | Override For |
|----------|---------|-------------|
| `SQLALCHEMY_DATABASE_URL` | `sqlite:///governance_metadata.db` | Production DB |
| `POSTGRES_HOST` | `localhost` | Demo schema source |
| `GIT_CONTRACTS_REPO_PATH` | `backend/contracts` | Contract storage location |
| `POLICIES_PATH` | `backend/policies` | Policy YAML directory |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Production origins |
| `ENABLE_LLM_VALIDATION` | `False` | Enable semantic validation |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama endpoint |
| `OLLAMA_MODEL` | `mistral:7b` | LLM model selection |

---

## 16. Design Decisions & Trade-offs

### SQLite for Metadata Storage

**Decision:** SQLite instead of PostgreSQL for governance metadata.
**Rationale:** PoC simplicity; zero configuration; portable single-file DB.
**Trade-off:** Not suitable for concurrent writes at scale; replace with PostgreSQL for production.

### Git for Contract Versioning

**Decision:** Application-level Git commits (GitPython) for contract audit trail.
**Rationale:** Provides immutable history, diff capability, and human-readable YAML artifacts for free.
**Trade-off:** Git repo can grow large over time; consider archival strategy for production.

### Policy-as-Code in YAML Files

**Decision:** Policies defined in version-controlled YAML, not database records.
**Rationale:** Enables GitOps workflows — policy changes go through code review; YAML is human-readable.
**Trade-off:** Adding a new policy requires a code deployment (restart), not just a database insert.

### LLM Validation Disabled by Default

**Decision:** Semantic engine (`ENABLE_LLM_VALIDATION=false`) is opt-in.
**Rationale:** Ollama adds latency (3–24s per validation) and requires local infrastructure. Rule-based checks catch 90% of violations deterministically.
**Trade-off:** Nuanced context-aware issues (SEM001–SEM008) are not caught unless enabled.

### Four-Role Architecture

**Decision:** Exactly four roles (Owner, Consumer, Steward, Admin) with hard-coded UI paths.
**Rationale:** Clear separation of concerns matches real data governance organizational models.
**Trade-off:** Rigid; adding a fifth role requires UI and routing changes. RBAC middleware would be more flexible.

### Federated Enforcement Model

**Decision:** Single central policy engine validates all datasets across domains.
**Rationale:** Consistent enforcement prevents policy drift; mirrors UN Peacekeeping model of shared rules.
**Trade-off:** A single validation failure blocks all datasets in the affected domain; could be too strict for some organizations. Exception management (`policy_conflicts` endpoints) provides an escape valve.

---

*Document generated: 2026-03-13 | Branch: `claude/architecture-design-doc-y1s1H`*
