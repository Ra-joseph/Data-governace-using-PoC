# Stop Sharing Files. Start Sharing Data Recipes with Contracts.

**Your pipelines are not broken. Your coordination model is. Contracts, events, and open standards are how enterprise data teams finally fix it.**

*Inspired by and building on Andrew Jones’s foundational work at GoCardless and Animesh Kumar’s value assessment framework at [Modern Data 101](https://moderndata101.substack.com/p/using-data-contracts-as-a-value-assessment). Full credit at the close of this article.*

-----

It is 9:07 on a Tuesday morning. Sarah opens her laptop to build the weekly executive dashboard. The source file is not there.

She checks the pipeline logs. Nothing useful. She messages the data engineering channel. No response yet. She messages the platform team. Someone suggests the issue might be upstream. She messages the finance data team.

At 2:14 that morning, a source system pushed a batch with a null customer_id column on 3 percent of records. A quality check flagged it and moved on. The dependent job ran anyway because it was scheduled, not reactive. It produced output. That output fed two other jobs. One of those jobs was supposed to produce the file Sarah is waiting for, but the second dependency had its own problem at 3am and never arrived.

Nobody knows the full dependency graph. Nobody was alerted. Nobody can say what broke or how far the damage spread.

This is not a technology failure. It is a coordination failure.

Some version of this plays out at nearly every enterprise data organisation, regardless of whether the storage layer is NFS file shares, Parquet on object storage, or Delta tables in a lakehouse. The storage technology improved. The coordination model did not.

In 2026, with the EU Data Act fully applicable since September 2025, AI pipelines demanding governed data, and IBM paying $11 billion to acquire Confluent to build what it calls a smart data platform, the cost of leaving that coordination model unchanged has never been higher. Data pipeline failures now cost enterprises an average of $3 million per month in business exposure, according to Fivetran’s 2026 Enterprise Data Infrastructure Benchmark across 500 enterprise leaders. The same report found that engineering teams spend 53 percent of their capacity on pipeline maintenance and troubleshooting rather than building new capability.

The problem is not tooling. The problem is a missing contract layer between producers and consumers.

-----

> **IMAGE PROMPT 1 — Opening visual: the coordination failure**
> 
> *Copilot Designer prompt:* “A clean technical infographic in a dark navy and amber colour scheme. Left side shows a traditional file-sharing pipeline: three stacked boxes labelled ‘Source System’, ‘Scheduled Job’, ‘Dashboard Consumer’ connected by simple arrows with small clock icons showing ‘1am’, ‘3am’, ‘5am’. A red X crosses one of the arrows. Right side shows a question mark cloud labelled ‘Who broke what?’ with tangled lines representing unknown dependencies. Style: editorial data visualisation, flat design, no gradients, white text on dark background. No people, no stock imagery. Width-dominant landscape format suitable for a Medium article hero image.”*

-----

## We Modernised Storage and Left Coordination in 2005

The shift to data lakehouses brought real architectural gains. Cheap scalable storage, columnar formats with schema evolution, time-travel queries, compute-storage separation. These improvements are genuine and lasting.

What did not change is the way teams hand data to each other. The dominant pattern across the industry is still physical artifact transfer: scheduled file drops, API snapshots pulled on a cron, nightly exports into shared directories. One team produces something. Another team picks it up. The coupling between producer and consumer is implicit, temporal, and fragile.

We gave everyone a faster printer and called it a digital transformation.

The consequences compound over time. Duplication spreads because there is no authoritative version of a shared dataset. Every team that needs clean customer data builds its own copy. Data becomes siloed not by design but by default, as each team accumulates its own slightly stale version of shared entities with undocumented transformation logic and no accountability to anyone else. Data governance teams try to solve this with documentation. It does not work. You cannot document your way out of a structural incentive to copy data.

Dependencies become invisible. The dependency graph lives in engineers’ heads and in job scheduling configurations. It is not a property of the system. When something breaks, figuring out what is affected is a manual social process. One person knows 60 percent of the graph. Three others know overlapping 30 percent slices. The blast radius of any change is unknown until the change is made.

Monte Carlo’s platform telemetry across 11 million monitored tables found data quality incidents resolving to an average of 15-plus hours of engineer time. A field name change at one financial services company resulted in $10 million in lost transaction volume before anyone traced the root cause. These are not edge cases. They are the operational norm for organisations without a contract layer.

Every handoff is a synchronisation point. Every synchronisation point is latency. Teams spend more time waiting for and validating files than using them.

-----

## The Dependency Problem Is Worse Than It Looks

Consider a standard executive dashboard and its upstream dependencies.

```
Executive Dashboard
 └── Revenue by Customer (weekly)
     ├── Customers Clean
     │   └── Customers Raw (source system export)
     └── Transactions Clean
         ├── Transactions Raw (source system export)
         └── FX Rates (third-party feed)
```

In a file-sharing model, every dependency in that graph is a scheduled job built on an implicit assumption: the upstream input will be ready before this job runs. That assumption is encoded as a time offset. Customers Raw lands at midnight, so Customers Clean runs at 1am, so Revenue by Customer runs at 3am, so the dashboard runs at 5am. The entire pipeline is a timing contract held together by sleep statements.

Now introduce a failure anywhere. FX Rates is late. Transactions Clean runs anyway and produces either an error or partial output, depending on how it was written. Revenue by Customer runs against that stale output. The dashboard renders numbers that are wrong. Sarah receives a file, but the file is lying to her.

The latency in that system is not primarily technical. It is coordination latency. Which job produced this file? Is this the right version? Did the schema change since last week? Who should I contact? These questions take hours to answer because the answers do not live in any system. They live in people.

The dependency graph exists in everyone’s heads and nowhere in the system. That is the core architectural failure.

Animesh Kumar at Modern Data 101 frames this precisely: data contracts are not documentation. They are enforceable agreements. The difference is the same as the difference between describing a law and enforcing it. A description changes nobody’s behaviour. An enforceable commitment with consequences changes the system.

-----

> **IMAGE PROMPT 2 — The dependency graph problem**
> 
> *Copilot Designer prompt:* “A clean technical diagram on a white background with slate grey and red accents. Shows a tree-structured dependency graph with six nodes: ‘Executive Dashboard’ at top, branching down through ‘Revenue by Customer’, ‘Customers Clean’, ‘Transactions Clean’, ‘Customers Raw’, ‘Transactions Raw’, ‘FX Rates’. The ‘FX Rates’ node has a red warning icon. Arrows from ‘FX Rates’ upward are shown as dashed red lines labelled ‘stale data propagates’. A small clock icon sits next to each node showing artificial schedule times. Style: precise technical line art, editorial flat design, no 3D effects. Caption space at bottom. Medium article body width format.”*

-----

## From Data as Artifact to Data as Recipe

The conceptual shift that changes everything is this: instead of sharing outputs, share the recipe.

A team’s data product is not the file it produces on a schedule. It is the transformation logic — the SQL, the dbt model, the Python pipeline — combined with a declared set of source dependencies and a schema contract. Consumers do not receive files. They declare dependencies. The platform resolves them.

This is exactly how software build systems work. When you run a build in Bazel or Make, nothing rebuilds unless its inputs have changed and are verified. The system knows what depends on what because every target declares its dependencies explicitly. Bazel’s own documentation draws the parallel to functional programming: outputs are deterministic functions of their inputs, not artifacts of timing.

DVC (Data Version Control) makes the analogy literal: it is described as a Makefile system for data pipelines. dbt’s very name — data build tool — frames SQL transformations as a build process, with `ref()` calls that make dependencies explicit and a DAG that is a first-class property of the system rather than an afterthought in a scheduling tool. Dagster’s Software-Defined Assets operate on the same declarative principles as Bazel targets: define what something is, declare what it depends on, and let the platform determine when and whether to recompute it.

We consider this table stakes for software delivery. We have never applied the same principle to data delivery at scale.

The important difference from a tool like Airflow is not the DAG. It is who owns the dependency declaration. In Airflow, a central team hardcodes the graph. In a contract-driven model, each dataset declares its own inputs. The graph emerges from the contracts rather than being imposed on them. This is the difference between a city planning office drawing every road and a city where each neighbourhood connects itself to the network using a shared standard.

-----

> **IMAGE PROMPT 3 — Data as recipe vs data as artifact**
> 
> *Copilot Designer prompt:* “A split-panel comparison diagram in a clean editorial style. Left panel labelled ‘Old Model: Data as Artifact’ shows a producer pushing a file into a shared folder, with a consumer pulling it on a schedule. Both sides have clock icons. The coupling is implicit. Right panel labelled ‘New Model: Data as Recipe’ shows a consumer declaring a dependency to a contract registry, which triggers materialisation when upstream conditions are met. An event message icon sits between them. Colour scheme: left panel warm muted amber, right panel cool teal-green. Bold sans-serif labels. White background, black text. No people. Horizontal diptych format for Medium body width.”*

-----

## The Contract Layer

The mechanism that makes this work is the machine-readable contract. Not a wiki page. Not a README. A structured, versioned, enforceable specification that the platform can reason about programmatically.

Two complementary open standards now provide the foundation for this.

The **Open Data Contract Standard (ODCS) v3.1.0**, released December 7, 2025 by the Bitol project under the Linux Foundation, is the enforcement layer. It specifies schema, quality thresholds, SLA commitments, and cross-dataset relationships. Version 3.1.0 introduced three capabilities that make contracts genuinely executable rather than aspirational. First, executable SLAs: latency, retention, availability, and freshness commitments can now be scheduled via cron expressions and validated by tooling. Second, cross-dataset relationships: foreign keys and composite keys can reference columns in other contracts using dot notation, allowing the platform to reason about referential integrity across domain boundaries. Third, strict JSON Schema validation means no undefined fields pass validation — contracts are precise specifications, not flexible templates. The `datacontract-cli`, maintained by Entropy Data and now the reference implementation for ODCS, made v3.1.0 its default format in December 2025, formally deprecating the previous Data Contract Specification.

The **Open Data Product Specification (ODPS)** operates one level up as the product wrapper. Two specifications share the acronym — a naming collision the community acknowledges openly. Dr. Jarkko Moilanen’s ODPS v4.1 covers business concerns: pricing models, licensing, discoverability, ethics declarations, and portfolio prioritisation. Bitol’s Open Data Product Standard v1.0.0, released September 2025, is more engineering-focused: it defines input and output ports with mandatory contract references, lifecycle states, and team governance structures aligned with ODCS. Jean-Georges Perrin (Actian, Bitol TSC chair, author of *Implementing Data Mesh*) frames the relationship as ODCS is to ODPS as HTML is to CSS — ODCS defines structure, ODPS defines presentation and context.

A practical contract for a customers dataset looks like this:

```yaml
# customers_clean.odcs.yaml — ODCS v3.1.0
apiVersion: v3.1.0
kind: DataContract
id: urn:datacontract:finance:customers-clean:v1.8
info:
  title: Customers Clean
  version: 1.8.0
  owner: finance-domain@company.com
  domain: finance
  status: active

schema:
  - name: customers
    physicalName: finance.customers_clean
    columns:
      - name: customer_id
        dataType: string
        required: true
        unique: true
      - name: email
        dataType: string
        classification: PII
      - name: country_code
        dataType: string
        pattern: "^[A-Z]{2}$"

quality:
  - type: notNull
    column: customer_id
    mustBeLessThan: 0.001      # max 0.1% null rate
  - type: rowCount
    mustBeGreaterThan: 10000
    mustBeLessThan: 5000000
  - type: referentialIntegrity
    column: country_code
    references: reference.country_codes.code

sla:
  availability: 99.5%
  freshness:
    threshold: 26h
    schedule: "0 2 * * *"     # must be fresh by 2am daily
  retention: 7 years

relationships:
  - type: derivedFrom
    from: finance.customers_raw
    contractId: urn:datacontract:finance:customers-raw:v2.3
    compatibility: ">=2.0.0 <3.0.0"

servers:
  production:
    type: bigquery
    project: company-prod
    dataset: finance
```

The version compatibility semantics matter more than most architects initially appreciate. Consumers declare dependency ranges rather than exact versions, using the same semver conventions that package managers have used for decades. A consumer might declare a dependency on Customers Clean at versions 1.5.0 through 2.0.0. Minor improvements propagate automatically. Breaking changes require a deprecation window during which the producer maintains the old version while consumers migrate. The platform enforces these windows. This is not a new idea — it is npm and pip applied to data.

Quality gates are first-class citizens in this model. A `DatasetVersionAvailableEvent` is not published when a pipeline finishes running. It is published when a pipeline finishes running **and** passes its quality contract: row count within the expected range, null rates below threshold, referential integrity checks passing, schema matching the declared contract. Quality is a precondition for the dependency chain, not an afterthought applied at the consumer’s end.

A contract is not documentation. It is an executable agreement. The platform enforces it so that people do not have to.

-----

> **IMAGE PROMPT 4 — The contract as executable specification**
> 
> *Copilot Designer prompt:* “A technical illustration showing a YAML contract document icon in the centre, surrounded by six connected capability icons in a hexagon arrangement: ‘Schema’ (grid icon), ‘Quality Gates’ (checkmark shield), ‘SLA’ (clock with percentage), ‘Versioning’ (git branch), ‘Ownership’ (person with key), ‘Cross-dataset Links’ (chain link). Each icon connected to the centre with a clean line. Dark charcoal background with electric blue accent lines and white text. Precision technical aesthetic, like a system architecture reference card. No gradients, flat icons. Square format for Medium inline image.”*

-----

## The Event Flow: How Dependencies Resolve

The event-driven resolution model is what turns individual contracts into a functioning platform. When Customers Raw v2.3 passes its quality gates, the resolver identifies which downstream contracts list it as an input at a compatible version range and triggers their materialisation in parallel. When Customers Clean v1.8 passes, the resolver checks Revenue by Customer. One input is satisfied. The other is not. Revenue by Customer waits. The system knows exactly why, and it can tell you.

```
[Customers Raw v2.3 — quality gates PASSED]
         │
         ▼
  Dependency Resolver
         │
  ├── Customers Clean depends on Customers Raw >=2.0 <3.0 ✓
  │   → trigger materialisation
  │
  └── Customer Cohort Model depends on Customers Raw >=2.0 <3.0 ✓
      → trigger materialisation (parallel)

[Customers Clean v1.8 — quality gates PASSED]
         │
         ▼
  Dependency Resolver
         │
  └── Revenue by Customer depends on:
      Customers Clean >=1.5 <2.0  ✓
      Transactions Clean >=3.1 <4.0  ✗ NOT YET SATISFIED
      → wait
```

Every state change is observable. Every blocked dependency is explainable. Every quality failure is attributed to the dataset that caused it.

The full event flow from source to consumer looks like this:

```
Source system batch arrives
         │
         ▼
  Ingestion pipeline runs
         │
         ▼
  Quality gate engine evaluates contract thresholds
         │
    ─────┴─────
    │          │
   PASS       FAIL
    │          │
    ▼          ▼
DatasetVersion   DatasetVersion
Available        Failed
Event            Event published
published        │
    │            → alert owning team
    │            → block downstream
    ▼
Dependency Resolver evaluates
which downstream contracts are now satisfiable
    │
    ▼
Materialisation triggered per satisfiable consumer
    │
    ▼
Consumer publishes its own Available or Failed event
```

This model has precedent at scale. Uber’s D3 framework monitors 300-plus Tier 1 datasets for data drift, reducing time-to-detect from 45 days to approximately 2 days with 95 percent accuracy. LinkedIn DataHub, now used by over 3,000 organisations including Netflix, Apple, Visa, and Klarna, implements data contracts as verifiable assertions on physical data assets with AI-powered contract suggestion and automated observability. Uber treats data as code: *“Data is treated as code and is managed in a similar way to software.”* The principle is the same across every mature implementation. The dependency graph must be a property of the system, not a property of people’s memory.

-----

> **IMAGE PROMPT 5 — Event-driven dependency resolution flow**
> 
> *Copilot Designer prompt:* “A vertical flowchart diagram on a dark slate background with neon green and white accents. Top node: ‘Source System Batch’ with a downward arrow. Then ‘Ingestion Pipeline’, arrow down to ‘Quality Gate Engine’ which splits into two paths: left path with green checkmark labelled ‘PASS → DatasetVersionAvailable Event’, right path with red X labelled ‘FAIL → DatasetVersionFailed Event → Alert + Block’. The green PASS path continues down to ‘Dependency Resolver’ which fans out to three consumer nodes with ‘satisfied’ (solid green arrows) and ‘waiting’ (dashed grey arrows) states. Clean monochrome-plus-accent style, precision technical aesthetic. Tall portrait format suitable for Medium article mid-body placement.”*

-----

## Why 2026 Is the Inflection Point

Three developments have moved this architecture from best practice to near-compliance necessity.

The EU Data Act became fully applicable on September 12, 2025. Articles 3, 33, and 36 collectively mandate machine-readable data formats, interoperable data exchange mechanisms, and the technical means to automate data sharing agreements. Article 33(1)(d) specifically requires *means to enable the interoperability of tools for automating the execution of data sharing agreements*. The EU is not mandating data contracts by name. It is describing data contracts precisely. For architects who need to justify investment to leadership, this is the budget conversation. The European Commission has also developed Model Contractual Terms for data sharing — the data governance equivalent of GDPR Standard Contractual Clauses, and likely to have the same reach beyond their nominal jurisdiction.

The EU AI Act’s Article 10, applicable from August 2, 2026 for high-risk AI systems, mandates formal data governance for training datasets: documented collection methodology, preparation operations, bias examination processes, and statistical property validation. Every team building AI on ungoverned data is accumulating regulatory risk. A contract-driven platform is not just a technical convenience for AI pipelines — it is the documented governance trail that Article 10 requires.

IBM’s acquisition of Confluent for $11 billion, announced December 8, 2025 at $31 per share, closed March 17, 2026. IBM’s stated rationale was explicit: Arvind Krishna called it foundational infrastructure for *“trusted communication and data flow between environments, applications and APIs”* for enterprise generative AI. Forrester titled their analysis *“Why IBM Paid $11B For Real-Time AI, Not Kafka”* — the event streaming substrate, not the message broker, was the strategic asset. When the largest enterprise software company in the world pays that price for an event-reactive platform, the event-driven component of this architecture stops being a forward-looking pattern and becomes mainstream infrastructure direction.

KPMG’s Q3 2025 AI Pulse Survey (130 C-suite leaders at $1B-plus revenue organisations) found that AI agent deployment had nearly quadrupled in two quarters — from 11 percent to 42 percent of organisations deploying at least some agents. In that same period, data quality emerged as the top barrier, with 82 percent citing it as critical, up from 56 percent the prior quarter. A 26-percentage-point jump in a single quarter is not a gradual trend. It is organisations realising at scale that you cannot build reliable AI on unreliable data.

The infrastructure exists. The regulatory mandate exists. The market signal exists. What remains is the organisational decision to change the collaboration model.

-----

> **IMAGE PROMPT 6 — The 2026 inflection point: three market signals**
> 
> *Copilot Designer prompt:* “An editorial-style triple-panel infographic on a clean white background. Three equal vertical columns each with a bold icon and stat. Left column: EU flag icon, title ‘EU Data Act’, subtext ‘Machine-readable data exchange — legally required September 2025’. Centre column: IBM + Confluent logos rendered as abstract shapes (no actual logos), title ‘$11B Signal’, subtext ‘Event-reactive infrastructure is now mainstream enterprise direction’. Right column: bar chart showing 11% to 42% bars, title ‘KPMG 2025’, subtext ‘AI agent adoption nearly quadrupled in two quarters’. Thin dividers between columns. Navy and amber professional colour scheme. No gradients. Landscape format.”*

-----

## The Data Mesh Lesson

Data mesh is in Gartner’s Trough of Disillusionment. A December 2025 Medium post described a two-year data mesh implementation as a four-million-dollar disaster — domain ownership had degenerated into dozens of competing silos, 27 data products nobody used, and infrastructure costs that tripled. Thoughtworks, the firm that originated the data mesh concept, published their 2026 assessment with blunt clarity: *“The greatest obstacles are changing organizational and individual behaviors, not technologies and architectures.”*

The architecture proposed here inherits data mesh vocabulary — domain ownership, data as a product, federated governance. That requires an explicit explanation of why this is different.

The failure mode of data mesh is the absence of enforcement. Domains own data products with no machine-readable contracts, no quality gate enforcement, and no version compatibility governance. The result is the same duplication and invisible dependency problem described at the start of this article, but distributed across more teams and more expensive to untangle.

Contracts provide the enforcement layer that data mesh principles assume but do not specify. Thoughtworks’ 2026 assessment describes the synthesis emerging in mature implementations: centralised fabric for the platform plumbing — storage, compute, identity, observability — with domain teams following mesh principles for ownership and accountability, all mediated by contract-driven consumption. This is not a return to a centralised data warehouse. It is domain ownership made enforceable.

The Bitol Technical Steering Committee includes practitioners from organisations who have built this for real: GoCardless (where Andrew Jones originated modern data contract practice), PayPal (which open-sourced the Data Contract Template that became ODCS), Springer Nature, Lidl, and Quantyca. These are not research projects. They are production systems.

-----

## Domain Ownership with Central Rails

The division of responsibility is clear. Domain teams own their golden sources. They write the ingestion logic, define the quality thresholds, maintain the schema contracts, and are accountable for their SLA commitments. The platform team owns the infrastructure: the event broker, the contract registry, the dependency resolver, the compute layer, the quality gate engine, and the observability stack.

The platform provides infrastructure. Domains provide logic.

The moment a platform team starts writing transformation SQL for a domain to unblock a delivery, the model begins to degrade. Every exception erodes the boundary. Within a year the platform team has become a data engineering team with a different name.

-----

## The Hardest Part Is Not Technical: Golden Source Designation

Declaring one version of customer data as authoritative is a political act. Every MDM and data governance practitioner who has attempted it will confirm this. Teams that have maintained their own version of a shared dataset for years have built workflows, reports, and institutional habits around it. Telling them their version is no longer authoritative is not a technical migration. It is a change management programme.

Verdantis frames the core question: who owns the customer data — marketing, sales, or customer service? Who decides how product information should be structured — merchandising or the supply chain team? No technology answers these questions. Leadership does.

The practical pattern that works is incremental designation by domain rather than enterprise-wide declaration. Agree on one golden source for one entity — customers, products, accounts — with a named owner, a documented quality commitment, and a platform-backed SLA. Get one team to depend on it successfully. Let the incentive structure do the adoption work. When the platform provides something more reliable than what teams would build themselves, the motivation to maintain a private copy diminishes.

Any architect who describes golden source designation as primarily a technology problem is avoiding the conversation that actually needs to happen. It requires executive sponsorship, a named data owner with real accountability, and a platform that teams trust enough to replace what they are giving up.

-----

> **IMAGE PROMPT 7 — Golden source designation as political and technical problem**
> 
> *Copilot Designer prompt:* “A Venn diagram style illustration on a warm cream background. Two large overlapping circles: left circle labelled ‘Organisational Problem’ containing icons for ‘Executive Sponsorship’, ‘Change Management’, ‘Domain Ownership Negotiation’. Right circle labelled ‘Technical Problem’ containing icons for ‘Contract Registry’, ‘SLA Enforcement’, ‘Quality Gates’. The overlapping centre is labelled ‘Golden Source Designation’ in bold. Small text beneath: ‘Cannot solve one without the other.’ Clean editorial illustration style, warm amber and slate palette, no gradients. Square format.”*

-----

## Retrofitting an Existing Platform

Most organisations are not starting from a blank slate. They have hundreds of existing pipelines, scheduling configurations accumulated over years, datasets with undocumented lineage, and teams with established ways of working. The retrofit does not require a rewrite.

The first step is to observe without changing anything. Run lineage scanners against existing jobs to reconstruct the dependency graph automatically. Most modern orchestration tools — Airflow, Dagster, dbt — expose enough metadata to build a reasonable first approximation. This produces the map before any furniture is moved.

The second step is to wrap existing pipelines in contracts without changing their behaviour. Emit availability events at the end of existing jobs. Register schemas in the contract registry. Add quality checks as non-blocking observers first, then promote them to gates once confidence is established. Pipelines continue running on their existing schedules and simply begin participating in the contract infrastructure.

The third step is to migrate domain by domain, starting with the datasets that have the highest number of downstream consumers. Bringing a high-fanout dataset into the contract model immediately propagates value to every consumer that depends on it.

The four maturity tiers that guide adoption are as follows.

**Tier 1: Register.** Add the dataset to the contract registry with schema and ownership information. No behaviour changes. The organisation gains discoverability and lineage tracing.

**Tier 2: Observe.** Add quality checks to the existing pipeline as non-blocking observers. The platform begins tracking quality history. The organisation gains quality visibility without disrupting existing schedules.

**Tier 3: Emit.** Publish availability events when the dataset is ready. Consumers can now react to the output rather than scheduling against it. This is the first step toward event-reactive consumption.

**Tier 4: Declare.** Add upstream dependency declarations to the contract. The platform manages trigger conditions. The organisation gains full reactive materialisation and impact analysis.

Each tier unlocks additional platform capabilities. The incentive structure does the adoption work without requiring anyone to be convinced by argument alone. A team that sees their Tier 3 dataset being consumed reactively by three downstream teams with zero coordination overhead will not need to be persuaded to move to Tier 4.

Set realistic timelines. Eighteen months to first real traction — multiple domains publishing quality-gated versioned contracts with reactive consumers — is an honest target. Anyone promising six months is either scoping something smaller than expected or selling something. The technology is not the constraint. Organisational alignment is.

-----

> **IMAGE PROMPT 8 — The four maturity tiers as a progression**
> 
> *Copilot Designer prompt:* “A horizontal four-stage progression bar on a dark charcoal background. Four connected stages with upward-pointing blocks like stairs. Stage 1 labelled ‘Tier 1: Register’ with icon for a database plus tag, subtext ‘Schema + ownership visible’. Stage 2 ‘Tier 2: Observe’ with eye icon, subtext ‘Quality history tracked’. Stage 3 ‘Tier 3: Emit’ with broadcast signal icon, subtext ‘Event-reactive consumers’. Stage 4 ‘Tier 4: Declare’ with dependency graph icon, subtext ‘Full reactive materialisation’. Left-to-right arrow beneath the stages. Colour progression from muted grey to electric teal as stages advance. Bold sans-serif labels. Wide landscape format for Medium article.”*

-----

## What the Model Unlocks

When the model is working, several capabilities emerge that were not possible before.

Impact analysis becomes a system query rather than a social investigation. When a schema change is proposed to customers_raw, the platform immediately returns every downstream dataset that declared a dependency on that schema at a compatible version range. The blast radius is known before the change is made, not after.

Reproducibility becomes deterministic. Every materialised dataset is version-locked to exact snapshots of its upstream inputs. Any historical output can be reconstructed by replaying the contract execution against archived source versions. This is useful for debugging and is something auditors find straightforward to verify — particularly relevant for EU AI Act Article 10 compliance documentation.

Duplication collapses over time. When a published, quality-gated, SLA-backed golden source exists for a shared entity, the incentive to maintain a private copy disappears. Teams stop building redundant pipelines because the platform provides something more reliable than what they would build themselves.

The architecture is AI-ready by design. AI agents require governed, fresh, and semantically clear data. A contract-driven event-reactive platform provides exactly that: versioned datasets with documented quality profiles, dependency lineage, and machine-readable schema. KPMG found that data quality concerns among AI-deploying organisations jumped 26 percentage points in a single quarter in 2025. The organisations with contract-driven data infrastructure will be able to onboard AI reliably. The organisations still operating on scheduled file drops will not.

-----

## Sarah’s Tuesday, Rebuilt

Sarah’s Tuesday morning looks different in this model.

Instead of a missing file with no explanation, she receives a notification at 2:17am that customers_raw version 2.3 failed its quality gates because the null customer_id rate was 3.2 percent against a contract threshold of 0.1 percent. Four downstream datasets are blocked as a result. The owning team has been paged automatically. The dependency resolver has suspended materialisation of Revenue by Customer because one of its two required inputs has not cleared quality gates. The contract registry shows exactly which version of each input the last successful dashboard run consumed.

Sarah still cannot run her dashboard. But she is not spending three hours reconstructing what broke. She knows what broke, who owns it, what the threshold violation was, and what the estimated resolution time is based on the owning team’s SLA commitment. She can tell the executive team something precise rather than something apologetic.

That is the difference between a coordination failure and a coordination model.

-----

## The Diagnostic Question

Look at the last significant data incident in your organisation. Trace it back to root cause.

Was it a technology failure — a database that went down, a compute job that ran out of memory?

Or was it a coordination failure — a dependency that nobody knew about, a schema change that went undocumented, a pipeline that assumed something that was no longer true?

In most organisations, for most incidents, it is the coordination failure. Monte Carlo’s root cause telemetry across millions of monitored assets shows that intentional but uncommunicated changes — schema changes, model updates, upstream modifications — account for a substantial fraction of data incidents. No amount of better storage, faster compute, or more capable tooling fixes a coordination problem. Only a coordination solution does.

The gap between good data infrastructure and great data infrastructure is rarely a technology gap. It is a contract gap.

Every component described here exists as production-grade open source today. ODCS v3.1.0 and the datacontract-cli. Delta-format storage with time-travel. Apache Kafka or Confluent for event brokering. DataHub for the contract registry and lineage graph. dbt for transformation logic with explicit dependency declaration. The transformation required is not technical. It is behavioural. Producers become responsible not just for running a job but for maintaining a contract. Consumers become responsible for declaring their needs explicitly rather than consuming whatever arrives.

Software teams arrived at this model through package managers, CI/CD pipelines, and API contracts. Data teams are roughly five years behind, not because the technology was unavailable, but because the organisational will to change the collaboration model was not there.

The question worth sitting with is whether it is there now.

-----

## Build It Yourself

If the architecture described here resonates, a working implementation of it is available as open source. The Data Governance Platform PoC at [github.com/Ra-joseph/Data-governance-using-PoC](https://github.com/Ra-joseph/Data-governace-using-PoC) implements the policy-as-code governance layer, the contract registry, and the quality gate engine on a local stack using open-source tooling. It is not a finished product. It is a working proof that this architecture can be operationalised without a proprietary platform. The code and architecture decision records are there. Pull it apart, critique it, or fork it.

-----

## Credit and Context

This article builds on two foundational bodies of work that deserve explicit acknowledgment.

**Andrew Jones** originated modern data contract practice at GoCardless, documented it publicly, co-founded what became the ODCS specification, and authored *Driving Data Quality with Data Contracts* (Packt, 2023). His Substack, [Modern Data 101](https://moderndata101.substack.com), is the best single source for contract-driven platform thinking written for practitioners.

**Animesh Kumar’s** article *[Using Data Contracts as a Value Assessment Framework for Data or AI Efforts](https://moderndata101.substack.com/p/using-data-contracts-as-a-value-assessment)* (Modern Data 101, April 2026) provides the philosophical and measurement-framework layer that this article deliberately does not replicate. Where this article asks how to build the platform, Kumar’s asks how to assess its value and what it means for AI initiative viability. Both are worth your time. The framing here — that a contract without consequence is decorative — is his.

The open standards referenced throughout: [ODCS v3.1.0](https://github.com/bitol-io/open-data-contract-standard), [ODPS v4.1](https://opendataproducts.org/v4.1/), [Bitol ODPS v1.0.0](https://bitol.io/announcing-odps-v1-0-0-building-the-language-of-data-products/), [datacontract-cli](https://github.com/datacontract/datacontract-cli).

-----

*Tags: #DataContracts #DataEngineering #DataGovernance #DataMesh #DataArchitecture #EventDrivenArchitecture #ODCS #EnterpriseData*
