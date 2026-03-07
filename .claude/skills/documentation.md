---
description: Document all changes made on the current branch vs. the base branch. Spawns parallel sub-agents to analyse each changed layer (models, schemas, services, routers, policies, frontend, tests), then synthesises findings into CHANGES_<branch>.md at the repo root. Run this at the end of every feature implementation.
allowed-tools: Bash, Read, Grep, Glob, Write, Edit, TodoWrite, Agent
---

# /documentation — Branch Change Documenter (Multi-Agent)

You are generating comprehensive documentation for all changes made on the current Git branch. You use a **multi-agent orchestration pattern**: you spawn parallel sub-agents — one per changed layer — to deeply analyse the codebase, then synthesise their findings into a structured `CHANGES_<branch>.md` file.

Follow every phase below in order. Do not skip phases.

---

## Phase 1 — Detect Branch and Scope

Run the following commands to understand what has changed:

```bash
# 1. Current branch name
git rev-parse --abbrev-ref HEAD

# 2. Identify base branch (try main first, fall back to master)
git show-ref --verify --quiet refs/heads/main && echo "main" || echo "master"

# 3. Find divergence point (merge base)
BASE=$(git show-ref --verify --quiet refs/heads/main && echo "main" || echo "master")
git merge-base HEAD $BASE

# 4. List all changed files since divergence
MERGE_BASE=$(git merge-base HEAD $BASE)
git diff --name-status $MERGE_BASE

# 5. Collect commit log since divergence
git log $MERGE_BASE..HEAD --oneline
```

From this output, record:
- `BRANCH_NAME`: current branch name
- `BASE_BRANCH`: `main` or `master`
- `MERGE_BASE_SHA`: the merge-base commit SHA (short form: first 8 chars)
- `CHANGED_FILES`: list of `(status, path)` pairs where status is A/M/D/R
- `COMMITS`: list of `(sha, message)` pairs

**Categorise every changed file into one or more layers:**

| Layer key | Path prefix(es) |
|-----------|----------------|
| `models` | `data-governance-platform/backend/app/models/` |
| `schemas` | `data-governance-platform/backend/app/schemas/` |
| `services` | `data-governance-platform/backend/app/services/` |
| `routers` | `data-governance-platform/backend/app/api/` |
| `policies` | `data-governance-platform/backend/policies/` |
| `frontend` | `data-governance-platform/frontend/src/` |
| `tests` | `data-governance-platform/backend/tests/`, `data-governance-platform/frontend/src/test/` |
| `config_docs` | all remaining files (`.md`, `.yaml`, `.json`, `requirements.txt`, `package.json`, root-level files, `.claude/`, etc.) |

Only layers with at least one changed file will have a sub-agent spawned.

---

## Phase 2 — Spawn Parallel Sub-Agents

**Launch all layer sub-agents in a single parallel batch** (use the `Agent` tool with `subagent_type: general-purpose` for each). Do not wait for one to finish before starting the next.

Pass each sub-agent:
1. Its layer name
2. The exact list of changed files in that layer (with Add/Modify/Delete status)
3. The merge-base SHA
4. The repo root absolute path
5. The analysis instructions for that layer (see below)

Each sub-agent must return a **structured markdown report** in this exact format:

```
## <Layer Name>

### Changed Files
- `relative/path/to/file` — Added | Modified | Deleted | Renamed

### What Changed
<bullet points: one per file, listing specific classes/functions/fields/rules/endpoints that were added, modified, or removed>

### New Public API Surface
<if applicable: table or bullets of new exported symbols, endpoints, schemas, policy IDs>
```

### Sub-Agent Instructions by Layer

#### Models Sub-Agent
Read each changed model file in `backend/app/models/`. For each file report:
- New or modified SQLAlchemy model classes (table name, new columns with types, new relationships)
- Modified existing fields (type changes, nullable changes, default changes)
- Deleted models or fields

#### Schemas Sub-Agent
Read each changed schema file in `backend/app/schemas/`. For each file report:
- New Pydantic schema classes (name, purpose — request vs. response)
- New or modified fields (name, type, whether required or optional)
- Deleted schemas or fields

#### Services Sub-Agent
Read each changed service file in `backend/app/services/`. For each file report:
- New public functions/methods (name, parameters, return type, one-sentence purpose)
- Modified functions (what logic changed)
- New external integrations or dependencies introduced

#### Routers Sub-Agent
Read each changed router file in `backend/app/api/`. For each file report:
- New endpoints: HTTP method, full path including prefix, request schema, response schema, one-sentence description
- Modified endpoints: what changed in the handler logic
- Use `Grep` to find the router prefix in `backend/app/main.py` if needed to construct full paths

#### Policies Sub-Agent
Read each changed policy YAML file in `backend/policies/`. For each file report:
- New policy entries: ID, name, severity, one-sentence rule summary, remediation summary
- Modified policies: what changed in rule or remediation
- Deleted policies

#### Frontend Sub-Agent
Read each changed file in `frontend/src/`. For each file report:
- New React pages or components (file path, component name, purpose)
- New routes added in `App.jsx`
- New API calls added in `services/api.js` (function name, HTTP method, endpoint path)
- New Zustand state added in `stores/index.js`
- Modified components: what UI behaviour changed

#### Tests Sub-Agent
Read each changed test file in `backend/tests/` and `frontend/src/test/`. For each file report:
- New test functions/cases: test name and one-sentence description of what it validates
- Count of net-new test functions added
- New pytest markers applied
- Modified assertions: what behaviour they now validate

#### Config/Docs Sub-Agent
Read each changed file not covered by the above layers. Report:
- New or modified environment variables (from `config.py`, `.env.example`, `CLAUDE.md`)
- New or modified Python/Node dependencies (from `requirements.txt`, `package.json`)
- New or modified documentation sections (from `.md` files — describe the section, not the full content)
- New or modified Docker/CI config

---

## Phase 3 — Synthesise and Write Documentation

After **all** sub-agents have returned their reports, the orchestrator:

### 3a. Determine output file path

```
SAFE_BRANCH=$(echo "$BRANCH_NAME" | sed 's/\//-/g')
OUTPUT_FILE="<repo_root>/CHANGES_${SAFE_BRANCH}.md"
```

### 3b. Write `CHANGES_<branch>.md`

Use the `Write` tool to create the file at the path above with the following structure. Populate every section from sub-agent reports. If a layer had no changes, omit that section entirely.

```markdown
# Changes: <BRANCH_NAME>

**Base branch:** <BASE_BRANCH> | **Diverged at:** `<MERGE_BASE_SHA_SHORT>`
**Generated:** <YYYY-MM-DD>

---

## Summary

<Write 3–5 sentences synthesising what this feature/fix does, based on the commit messages and sub-agent reports. Focus on the "what and why" — what capability was added or fixed, and why it matters for the platform.>

---

## Commits

<bullet list of all commits from git log, format: `- <sha> <message>`>

---

## Changes by Layer

### Models
<paste Models sub-agent "What Changed" section>

### Schemas
<paste Schemas sub-agent "What Changed" section>

### Services
<paste Services sub-agent "What Changed" section>

### Routers / API Endpoints
<paste Routers sub-agent "What Changed" section>

#### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
<populate from Routers sub-agent "New Public API Surface"; one row per new endpoint>

### Policies
<paste Policies sub-agent "What Changed" section>

#### New / Modified Policies

| ID | Name | Severity | Change |
|----|------|----------|--------|
<populate from Policies sub-agent "New Public API Surface"; one row per new/modified policy>

### Frontend
<paste Frontend sub-agent "What Changed" section>

### Tests
<paste Tests sub-agent "What Changed" section>

**Net-new test functions added:** <N>

### Configuration & Documentation
<paste Config/Docs sub-agent "What Changed" section>

---

## How to Test These Changes

Run the full regression suite to validate all changes:

```bash
# Backend — all tests
cd data-governance-platform/backend
source venv/bin/activate
python -m pytest tests/ -v --tb=short

# Frontend — all tests
cd data-governance-platform/frontend
npm test -- --run
```

<If only specific layers changed, also add targeted commands:>
<e.g., if only backend/app/services/policy_engine.py changed:>
```bash
# Targeted: policy engine tests
python -m pytest tests/test_policy_engine.py -v --tb=short
```

---

## Files Changed Summary

| Layer | Added | Modified | Deleted | Renamed |
|-------|-------|----------|---------|---------|
<one row per layer that had changes; count files per status>
| **Total** | <N> | <N> | <N> | <N> |
```

### 3c. Report to user

After writing the file, output:

```
Documentation generated: CHANGES_<branch>.md
==============================================
Layers analysed:  <comma-separated list of layers with changes>
Files changed:    <total count>
Commits included: <N>

To commit this documentation file:
  git add CHANGES_<branch>.md
  git commit -m "Docs: add change documentation for <branch>"
```

---

## Important Constraints

- **Read-only during analysis**: sub-agents only read files — they do not edit or write anything.
- **Only the orchestrator writes**: the orchestrator writes the single `CHANGES_<branch>.md` output file.
- **Do not modify** files under `data-governance-platform/backend/contracts/` — auto-managed by the Git service.
- **Do not include secrets**: if a changed file contains API keys or passwords, reference the file but do not quote the secret values.
- **No hallucination**: only document changes that are actually present in the diff. If a sub-agent finds no meaningful changes in its layer, it returns a short "No significant changes" note — do not fabricate content.
- **Overwrite is safe**: if `CHANGES_<branch>.md` already exists, overwrite it — it is always regenerated fresh from the current branch state.
- Follow repo naming conventions: `snake_case` for Python, `PascalCase` for React components, `UPPER_SNAKE_CASE` for constants.

---

## Quick Reference: Key Paths

| What | Where |
|------|-------|
| Backend models | `data-governance-platform/backend/app/models/` |
| Backend schemas | `data-governance-platform/backend/app/schemas/` |
| Backend services | `data-governance-platform/backend/app/services/` |
| Backend routers | `data-governance-platform/backend/app/api/` |
| Policy YAMLs | `data-governance-platform/backend/policies/` |
| Router registration | `data-governance-platform/backend/app/main.py` |
| Frontend pages | `data-governance-platform/frontend/src/pages/` |
| Frontend components | `data-governance-platform/frontend/src/components/` |
| Frontend API client | `data-governance-platform/frontend/src/services/api.js` |
| Frontend store | `data-governance-platform/frontend/src/stores/index.js` |
| Frontend routes | `data-governance-platform/frontend/src/App.jsx` |
| Backend tests | `data-governance-platform/backend/tests/` |
| Frontend tests | `data-governance-platform/frontend/src/test/` |
| Output file | `<repo_root>/CHANGES_<sanitised-branch-name>.md` |
