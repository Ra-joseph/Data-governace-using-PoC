# Data Governance Platform — Architecture Specs for Napkin.ai

Paste each section below individually into napkin.ai to generate separate ArchiMate diagrams.

---

## Diagram 1 — System Context

The Data Governance Platform is used by four types of actors: a Data Owner who registers datasets and monitors policy violations, a Data Consumer who browses the data catalog and requests access to datasets, a Data Steward who approves subscription requests and authors governance policies, and a Platform Admin who monitors compliance metrics across domains.

All four actors interact with the Data Governance Platform application via a React-based web frontend. The platform connects to three external systems: a PostgreSQL database used as a schema discovery source, an Ollama LLM server running locally that provides AI-powered semantic policy evaluation, and a Git repository that stores immutable versioned data contracts as the audit trail.

---

## Diagram 2 — Application Architecture (Three-Layer)

**Business Layer**

The platform supports four business roles: Data Owner, Data Consumer, Data Steward, and Platform Admin. These roles participate in three core business processes: Dataset Registration (owned by Data Owner), Subscription Approval (owned by Data Steward), and Policy Authoring (owned by Data Steward and Platform Admin). The Dataset Registration process produces a Data Contract business object. The Subscription Approval process consumes Subscription Requests and produces approved Data Contracts. The Policy Authoring process produces Governance Policies.

**Application Layer**

The application layer consists of a React Frontend and a FastAPI Backend.

The React Frontend exposes four application interfaces: the Dataset Registration Wizard for Data Owners, the Data Catalog Browser for Data Consumers, the Approval Queue for Data Stewards, and the Compliance Dashboard for Platform Admins.

The FastAPI Backend is composed of the following application components:
- Dataset & Subscription API: handles dataset CRUD, schema import, subscription lifecycle
- Policy Management API: handles policy authoring, dashboard, reports, exchange, exceptions, and domain governance
- Validation & Audit API: handles orchestration validation, semantic scanning, and Git contract history

The backend services layer contains:
- ContractService: coordinates contract creation, validation, versioning, and Git commit
- PolicyOrchestrator: performs risk scoring and selects a validation strategy (FAST, BALANCED, THOROUGH, or ADAPTIVE)
- AuthoredPolicyLoader: loads approved human-authored policies from the database into runtime validation
- PolicyConverter: transforms plain-English policy descriptions into YAML artifacts
- GitService: commits, tags, and diffs contract versions in the Git repository
- PostgresConnector: connects to external PostgreSQL to discover table schemas and detect PII fields

The policy engine layer contains:
- PolicyEngine: evaluates rule-based YAML policies deterministically; always active
- OdpsService: reads ODPS 4.1 data product descriptors and enforces quality thresholds
- SemanticPolicyEngine: evaluates contextual policies using an LLM; optional
- OllamaClient: HTTP client that calls the local Ollama server with response caching

**Technology Layer**

The technology layer contains:
- SQLite database (governance_metadata.db): stores datasets, contracts, policies, subscriptions, and users
- Git Contracts Repository (backend/contracts/): stores YAML contract files as immutable versioned artifacts
- YAML Policy Files (backend/policies/): four files containing 17 deterministic governance rules loaded at application startup
- ODPS Descriptor Files (backend/odps/): YAML data product specification files following the Linux Foundation ODPS 4.1 standard
- PostgreSQL database (financial_demo): external source database used for schema discovery
- Ollama server (localhost:11434): local LLM inference server running mistral:7b; optional dependency

---

## Diagram 3 — Policy Validation Flow

The PolicyOrchestrator receives a contract validation request. It performs risk scoring by examining the contract for PII fields, compliance tags, data classification level, and field count. Based on the risk score it selects one of four strategies: FAST for low-risk contracts with no PII (rule-based only), BALANCED for moderate-risk contracts (rule-based plus targeted semantic checks), THOROUGH for high-risk or PII-containing contracts (full rule-based plus full semantic), and ADAPTIVE for unknown or mixed-risk contracts where the strategy is determined at runtime.

For all strategies, the PolicyOrchestrator calls the PolicyEngine, which loads sensitive data policies (SD001–SD005), data quality policies (DQ001–DQ005), and schema governance policies (SG001–SG007) from YAML files. The PolicyEngine also calls OdpsService to retrieve quality thresholds from ODPS 4.1 descriptor files and applies them as additional quality gates.

For BALANCED, THOROUGH, and ADAPTIVE strategies, the PolicyOrchestrator also calls the SemanticPolicyEngine, which evaluates semantic policies (SEM001–SEM008) covering naming conventions, documentation quality, and business logic consistency. The SemanticPolicyEngine calls OllamaClient, which sends HTTP requests to the local Ollama server and caches responses.

In parallel, the AuthoredPolicyLoader queries the SQLite database for approved PolicyDraft records, converts them to runtime format, and merges them into the validation run alongside the static YAML policies.

The PolicyOrchestrator combines all results into a ValidationResult containing a compliance status, a list of violations, a severity breakdown, and remediation guidance. The ValidationResult is returned to ContractService, which persists it to the SQLite Contract record and triggers GitService to commit the contract YAML to the Git repository.

---

## Diagram 4 — Data Contract Lifecycle

A Data Owner submits a dataset registration through the Dataset Registration Wizard. The Dataset & Subscription API receives the request and calls ContractService. ContractService calls PostgresConnector to import the table schema from PostgreSQL if a source table is specified. PostgresConnector detects PII fields using keyword matching on column names and returns the enriched schema.

ContractService calls PolicyOrchestrator to validate the contract against all active governance policies. If validation passes, ContractService creates a Contract record in SQLite with status COMPLIANT and calls GitService to commit the contract YAML to the Git contracts repository with a semantic version tag. If validation fails, ContractService stores the violations in the Contract record with status VIOLATION and returns remediation guidance to the Data Owner.

A Data Consumer browses the Data Catalog Browser and submits a subscription request. The Dataset & Subscription API creates a Subscription record in SQLite with status PENDING. The Data Steward reviews the request in the Approval Queue. On approval, the API calls ContractService, which regenerates and re-validates the contract, increments the version, commits the new version to Git, and updates the Subscription status to APPROVED.

---

## Diagram 5 — Policy Authoring Lifecycle

A Data Steward opens the Policy Authoring interface and writes a new governance policy in plain English, submitting it as a PolicyDraft with status DRAFT stored in SQLite.

The Steward submits the draft for review, changing its status to SUBMITTED. A second Steward or Platform Admin reviews the draft in the Policy Review interface. On approval, the Policy Management API calls PolicyConverter, which uses keyword heuristics to generate a YAML policy artifact and a JSON representation. PolicyConverter stores the artifact as a PolicyArtifact record in SQLite linked to the PolicyDraft. The PolicyDraft status changes to APPROVED and an immutable PolicyApprovalLog entry is written.

On the next contract validation run, AuthoredPolicyLoader queries SQLite for all APPROVED PolicyDraft records, converts them to runtime policy format, and passes them to PolicyOrchestrator alongside the static YAML policies. The combined policy set is evaluated by PolicyEngine.

A policy can be revised (creating a new PolicyVersion record), deprecated (status changes to DEPRECATED and it is excluded from future validation runs), or rejected (status changes to REJECTED with a reason recorded in PolicyApprovalLog).
