# Building a Data Governance Platform with Policy-as-Code: Lessons from the UN Peacekeeping Model

*How we built a federated data governance system that prevents compliance violations before they reach production*

---

Data governance is broken. Most organizations discover governance violations after the damage is done — a downstream dashboard displays stale data, a compliance audit reveals unencrypted PII, or a schema change silently breaks three consumer pipelines. The problem isn't a lack of rules. It's that the rules live in PDFs nobody reads, enforced by manual reviews that can't scale.

We set out to fix this. The result is an open-source **Policy-as-Code Data Governance Platform** that validates data contracts at creation time, provides actionable remediation guidance, and tracks every change in Git. And we borrowed the governance model from an unlikely source: the United Nations.

## The Problem with Traditional Data Governance

If you've worked in a data-intensive organization, you've likely seen this pattern:

1. A governance team writes policies in a Word document
2. The document lives on a SharePoint nobody visits
3. Data teams move fast and discover policies exist only when an audit fails
4. The fix is reactive — damage control after the fact

This creates a toxic cycle. Governance becomes synonymous with bureaucracy, data producers see it as a blocker, and compliance teams are always playing catch-up.

The root cause? **Governance policies are disconnected from the engineering workflow.** They aren't version-controlled, aren't testable, and aren't enforced at the point where violations are introduced.

## Enter the UN Peacekeeping Model

When designing our governance architecture, we drew inspiration from how the UN manages international peacekeeping:

- **Shared Policies**: A central body (the Security Council) defines universal standards that all member states agree to
- **Distributed Enforcement**: Peacekeepers operate locally, within each region, enforcing shared standards without overriding local authority
- **Local Autonomy**: Each nation retains sovereignty over its internal affairs
- **Neutral Arbiter**: The UN itself doesn't take sides — it validates objectively against agreed-upon standards
- **Prevention at Borders**: Conflicts are intercepted at boundaries before they cascade into wider crises

Translated to data governance:

| UN Concept | Data Governance Equivalent |
|---|---|
| Security Council | Central governance team defining policies |
| Member States | Domain data teams (finance, marketing, ops) |
| Peacekeepers | Policy engine validating at source |
| International Law | YAML policy definitions (Policy-as-Code) |
| Border Checkpoints | Contract validation before publication |

This model gave us a critical design principle: **prevent violations at the point of creation, not after they've propagated through the data ecosystem.**

## Architecture: What We Built

The platform is a full-stack application with a FastAPI backend, React frontend, and a multi-layered policy engine at its core.

```
┌──────────────────────────────────────────────────────────────┐
│                Frontend Layer (React 18 + Vite)               │
├──────────────┬──────────────┬──────────────┬─────────────────┤
│  Data Owner  │ Data Consumer│ Data Steward │ Platform Admin   │
│  • Register  │  • Browse    │  • Approve   │  • Metrics       │
│  • Manage    │  • Subscribe │  • Review    │  • Trends        │
│  • Remediate │  • Request   │  • Credential│  • Analytics     │
└──────────────┴──────────────┴──────────────┴─────────────────┘
                               ▲
                               │ REST API (30+ endpoints)
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              FastAPI Backend + Policy Engine                   │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │   Dataset    │ │   Contract   │ │ Subscription │         │
│  │   Registry   │ │  Management  │ │   Workflow   │         │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘         │
│         └────────────────┼────────────────┘                  │
│                    ┌─────▼─────┐                              │
│                    │ Policy    │   Intelligent Routing         │
│                    │Orchestratr│   4 Strategies                │
│                    └──┬────┬──┘                               │
│              ┌────────┘    └────────┐                         │
│        ┌─────▼─────┐         ┌─────▼─────┐                   │
│        │ Rule-Based│         │ Semantic  │                    │
│        │  Engine   │         │  Engine   │                    │
│        │ 17 YAML   │         │ 8 LLM    │                    │
│        │ Policies  │         │ Policies  │                    │
│        └───────────┘         └───────────┘                    │
│                    ┌───────────┐                              │
│                    │    Git    │   Version Control             │
│                    │  Service  │   Full Audit Trail            │
│                    └───────────┘                              │
└──────────────────────────────────────────────────────────────┘
```

### The Policy Engine: Heart of the System

The platform uses **25 governance policies** across two validation engines. The **rule-based engine** loads 17 policies from three YAML files for fast, deterministic validation (<100ms). The **semantic engine** adds 8 LLM-powered policies via local Ollama for context-aware analysis that catches what pattern matching cannot. An **orchestration layer** intelligently routes contracts to the right engine based on risk level and data characteristics, using one of four strategies: FAST (rule-based only), BALANCED (rules + targeted semantic), THOROUGH (all policies), or ADAPTIVE (auto-selects based on risk).

Here's what a policy definition looks like:

```yaml
- id: SD001
  name: PII Encryption Required
  category: sensitive_data
  severity: critical
  description: >
    All fields containing PII must have encryption
    documented in the contract
  condition: >
    If dataset contains PII fields AND classification
    is confidential or restricted, encryption_details
    must be specified
  remediation:
    - Add encryption_details to your contract
    - Specify encryption algorithm (e.g., AES-256)
    - Document key management approach
    - Reference your organization's encryption standards
```

Three things make this approach powerful:

1. **Policies are version-controlled.** Every change goes through code review, just like application code.
2. **Remediation is built-in.** Each policy includes step-by-step instructions for fixing violations. No more cryptic error codes.
3. **Severity levels drive workflow.** Critical violations block publication. Warnings allow it but flag for review.

### Dual-Format Data Contracts

Every dataset produces two contract formats:

- **YAML** for humans: readable, diffable, reviewable in pull requests
- **JSON** for machines: parseable by downstream systems, CI/CD pipelines, and monitoring tools

Both are committed to Git with semantic versioning. A SHA-256 hash of the schema enables instant change detection without full-text comparison.

### Four Roles, Four Interfaces

Rather than a one-size-fits-all dashboard, we built dedicated UIs for each persona in the data governance lifecycle:

**Data Owners** register datasets through a guided wizard. The system imports schemas directly from PostgreSQL (with automatic PII detection based on field naming patterns), validates against all 25 policies (rule-based and semantic), and displays violations with remediation steps inline.

**Data Consumers** browse a catalog, filter by classification and domain, and submit subscription requests with SLA requirements — freshness targets, availability needs, quality thresholds.

**Data Stewards** manage an approval queue. They review subscription requests, examine the data contract, and approve or reject with comments. Approval automatically triggers a new contract version with the consumer's SLA terms embedded.

**Platform Admins** monitor compliance health through an analytics dashboard — compliance rates over time, top violated policies, classification breakdowns, and trend analysis.

## The Key Insight: Prevention Over Detection

The most impactful architectural decision was validating contracts at creation time. Here's the workflow:

1. A data owner registers a dataset and provides metadata
2. The system imports the schema from the source database
3. A data contract is generated automatically (v1.0.0)
4. The policy orchestrator validates against applicable policies **immediately** (up to 25 policies based on risk level)
5. Violations are returned with severity, description, and remediation steps
6. The contract is committed to Git regardless of status — but only compliant datasets are marked "published"

This means a data owner sees exactly what's wrong and how to fix it **before** any consumer can depend on the dataset. No downstream breakage. No emergency Slack threads. No governance theater.

Consider this example from our financial services demo. When a `customer_accounts` table is registered, the policy engine catches:

- **SD001 (Critical)**: PII fields (email, SSN, phone) lack encryption documentation → *"Add encryption_details specifying AES-256 and key management approach"*
- **SD003 (Warning)**: PII dataset missing compliance tags → *"Add compliance_tags: ['SOX', 'PCI-DSS'] to your contract"*
- **DQ002 (Warning)**: No freshness SLA defined → *"Specify freshness_sla with max_age_hours based on consumer needs"*

The owner can fix these issues, re-submit, and watch violations clear in real time.

## Technical Decisions Worth Highlighting

### Git as the Contract Store

We chose Git over a traditional database for contract storage. This gave us:

- **Immutable history**: Every contract version is a commit. No silent overwrites.
- **Diffing for free**: Compare any two versions of a contract with standard Git tooling.
- **Familiar workflow**: Data engineers already know Git. No new tools to learn.
- **Branching**: Experimental contract changes can happen on branches before merging to main.

The trade-off is query complexity — you can't easily run SQL over Git history. We mitigate this by keeping contract metadata in SQLite/PostgreSQL while Git stores the full contract artifacts.

### YAML Policies, Not a Rules Engine

We deliberately chose plain YAML files over a specialized rules engine (like OPA/Rego or Drools). Why?

- **Lower barrier to entry**: Anyone who can read YAML can understand the policies
- **No vendor lock-in**: Policies are portable text files
- **Code-review friendly**: YAML diffs are readable in pull requests
- **Good enough**: For 17 rule-based policies, a simple Python validation loop outperforms the complexity of deploying and maintaining a rules engine

We later added a **semantic policy engine** (8 LLM-powered policies via Ollama) for context-aware validation that catches issues pattern matching cannot — like detecting PII based on business context, validating that compliance tags actually apply, or identifying security vulnerabilities in schema design. An **orchestration layer** routes contracts to the right engine based on risk, keeping validation fast for low-risk data while ensuring critical datasets get thorough analysis.

### Semantic Versioning for Contracts

Contracts follow semver rules:

- **MAJOR** (2.0.0): Breaking schema changes (removed fields, type changes)
- **MINOR** (1.1.0): Additive changes (new fields, new consumer SLAs)
- **PATCH** (1.0.1): Metadata-only updates (descriptions, tags)

The system detects the appropriate version bump by hashing the schema and comparing against the previous version's hash. Breaking changes trigger a major bump automatically, preventing accidental backwards-incompatible releases.

## What We'd Do Differently

**Authentication from day one.** Our PoC uses a role-selection screen instead of proper OAuth2/JWT authentication. In a real deployment, identity management should be foundational, not bolted on.

**More connectors earlier.** We built a robust PostgreSQL connector with PII detection and type mapping. But in most enterprises, data lives across Snowflake, S3, Delta Lake, and dozens of other systems. The connector architecture is extensible, but we underestimated how much of the value proposition depends on supporting the actual sources teams use.

**Policy testing framework.** We have policies and a validation engine, but no dedicated framework for testing policies themselves — writing unit tests that verify a policy catches specific contract shapes and passes others. This is essential for teams iterating on governance rules.

## Getting Started

The platform runs locally with minimal setup:

```bash
# Clone the repository
git clone https://github.com/Ra-joseph/Data-governace-using-PoC.git
cd Data-governace-using-PoC/data-governance-platform

# Start the backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Start the frontend (separate terminal)
cd frontend
npm install
npm run dev
```

The backend starts with an embedded SQLite database and auto-initializes a Git repository for contracts. A Docker Compose file is included for spinning up a PostgreSQL demo database with sample financial data.

Visit `http://localhost:5173` to see the role-selection screen, then explore each persona's workflow.

## Where This Is Heading

The platform has evolved significantly from its initial backend-only design. The multi-role frontend, complete subscription workflow, semantic scanning, and intelligent orchestration are all production-ready. The roadmap now focuses on:

- **Authentication & authorization** — replacing the demo role-selector with proper OAuth2/JWT and RBAC
- **Data lineage tracking** — understanding how governed datasets flow through transformation pipelines
- **Real-time monitoring** — alerting when a published dataset's actual behavior drifts from its contract (freshness violations, quality degradation)
- **CI/CD integration** — running policy validation as a step in data pipeline deployments, blocking merges that introduce violations
- **Additional connectors** — extending beyond PostgreSQL to support Snowflake, S3, Azure Data Lake, and more

## The Bigger Picture

Policy-as-Code isn't just a technical pattern — it's a cultural shift. When governance rules are code, they become:

- **Testable**: You can verify policies before deploying them
- **Reviewable**: Changes go through pull requests, not email threads
- **Versionable**: You can track how governance evolves over time
- **Automatable**: Enforcement happens without human bottlenecks
- **Transparent**: Everyone can read the rules that apply to them

The UN Peacekeeping model adds a second cultural shift: governance doesn't have to be top-down command-and-control. It can be federated — central standards, local enforcement, mutual accountability.

If your organization is struggling with data governance that feels like overhead rather than enablement, consider this: the problem might not be your policies. It might be that your policies aren't code.

---

*The full source code is available on [GitHub](https://github.com/Ra-joseph/Data-governace-using-PoC). Contributions and feedback are welcome.*

---

**Tags:** Data Governance, Policy-as-Code, Data Engineering, Data Contracts, FastAPI, React, LLM, Semantic Scanning, Open Source
