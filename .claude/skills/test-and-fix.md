---
description: Run the full test suite (backend pytest + frontend Vitest), analyze failures, and suggest targeted fixes with file paths and line numbers. Optionally apply fixes automatically.
allowed-tools: Bash, Read, Grep, Glob, Edit, TodoWrite, AskUserQuestion
---

# /test-and-fix — Test Runner & Fix Suggester

You are running the Data Governance Platform test suite and diagnosing any failures. Follow every step below in order. Do not skip steps.

---

## Step 1: Run Backend Tests

From the `data-governance-platform/backend/` directory, activate the virtualenv (if present) and run pytest:

```bash
cd /home/user/Data-governace-using-PoC/data-governance-platform/backend
source venv/bin/activate 2>/dev/null || true
python -m pytest tests/ -v --tb=short 2>&1
```

Capture the full output. Identify:
- Total tests collected, passed, failed, errored, skipped
- Each failing/erroring test: file, class, function name, error type, and the relevant traceback lines

If the virtualenv does not exist, install dependencies first:
```bash
pip install -r requirements.txt
```

---

## Step 2: Run Frontend Tests

From the `data-governance-platform/frontend/` directory, run Vitest in single-pass (non-watch) mode:

```bash
cd /home/user/Data-governace-using-PoC/data-governance-platform/frontend
npm test -- --run 2>&1
```

Capture the full output. Identify:
- Total test suites and test cases: passed, failed, skipped
- Each failing test: file, `describe` block, `it`/`test` name, assertion error, and stack trace

If `node_modules` is missing, install first:
```bash
npm install
```

---

## Step 3: Summarize Results

Print a concise summary table to the user:

```
Backend Tests
=============
Total:   <N>
Passed:  <N>
Failed:  <N>
Errors:  <N>
Skipped: <N>

Frontend Tests
==============
Total:   <N>
Passed:  <N>
Failed:  <N>
Skipped: <N>
```

If **all tests pass**, congratulate the user and stop here. Do not fabricate failures.

If there are failures, continue to Step 4.

---

## Step 4: Diagnose Each Failure

For **every** failing test, perform the following analysis:

### 4a. Locate the source of failure

Read the traceback to find the exact file and line number where the assertion or exception originates. Use the `Read` tool to open that file at the relevant lines. Also read the test file itself to understand what behavior is expected.

Key paths:
- Backend source: `data-governance-platform/backend/app/`
- Backend tests: `data-governance-platform/backend/tests/`
- Frontend source: `data-governance-platform/frontend/src/`
- Frontend tests: `data-governance-platform/frontend/src/test/`
- Policy files: `data-governance-platform/backend/policies/`

### 4b. Classify the failure

Classify each failure as one of:
- **Implementation bug** — the source code does not do what the test expects
- **Test bug** — the test assertion is wrong or outdated relative to the current implementation
- **Missing fixture/dependency** — a required fixture, mock, or external service is absent
- **Import/config error** — a module cannot be imported or config is wrong
- **Environment issue** — a dependency version mismatch or missing package

### 4c. Determine the root cause

State clearly:
> "The test `<test_name>` fails because `<root cause>`. The implementation at `<file>:<line>` does `<actual>` but the test expects `<expected>`."

---

## Step 5: Suggest Fixes

For each failure, produce a **specific, actionable fix suggestion** in the following format:

---
**Failure:** `tests/test_<file>.py::<TestClass>::<test_function>`
**Classification:** <Implementation bug | Test bug | Missing fixture | Import error | Environment issue>
**Root cause:** <one sentence>

**Fix location:** `<relative/path/to/file.py>:<line_number>`

**Current code:**
```python
# (paste the problematic lines)
```

**Suggested fix:**
```python
# (paste the corrected lines)
```

**Why this fixes it:** <one sentence explanation>

---

Rules for fix suggestions:
- Only suggest changes to one file per failure unless the fix absolutely requires touching multiple files.
- For **test bugs**: fix the test assertion, not the implementation, and explain why the test was wrong.
- For **implementation bugs**: fix the implementation and confirm the fix does not break other passing tests (check by searching for usages with `Grep`).
- For **import/config errors**: show the exact missing import or config key.
- For **environment issues**: give the exact `pip install` or `npm install` command needed.
- Never suggest deleting tests. Never suggest suppressing errors with `try/except`.
- Reference exact `file_path:line_number` for every code location mentioned.

---

## Step 6: Apply Fixes (Optional)

After presenting all fix suggestions, ask the user:

> "I found <N> fix(es). Would you like me to apply them automatically?"

Options to offer:
- **Apply all fixes** — use the `Edit` tool to apply every suggested change
- **Apply specific fixes** — ask which ones to apply by number
- **Show diffs only** — show what each edit would look like without applying
- **Skip** — leave the suggestions as-is for the user to apply manually

If applying fixes, use the `Edit` tool for each change. After applying, re-run the relevant tests to confirm the fix works:

```bash
# Backend — run only the affected test file
python -m pytest tests/test_<file>.py -v --tb=short 2>&1

# Frontend — re-run all tests
npm test -- --run 2>&1
```

Report whether the re-run confirms the fix.

---

## Step 7: Final Report

Output a final summary:

```
Fix Report
==========
Failures found:   <N>
Fixes suggested:  <N>
Fixes applied:    <N>
Tests now passing: <N>/<total>
```

If any failures remain unresolved (e.g., environment issues requiring manual action), list them explicitly with the manual steps needed.

---

## Important Constraints

- **Do not modify** files under `data-governance-platform/backend/contracts/` — these are auto-managed by the Git service.
- **Do not modify** files under `data-governance-platform/demo/` — these are reference SQL files.
- **Do not add** `try/except` blocks to suppress test failures.
- **Do not skip** or mark tests as `xfail` unless the failure is a known, documented limitation.
- Follow the coding conventions in `CLAUDE.md`: `snake_case` for Python functions/variables, `PascalCase` for classes, imperative docstrings.
- Backend pytest markers (`unit`, `api`, `service`, `integration`) must not be added or removed without reason.
- When fixing a Pydantic schema mismatch (HTTP 422 errors), always check both the schema in `backend/app/schemas/` and the API call in `frontend/src/services/api.js`.

---

## Quick Reference: Test Commands

| Command | Purpose |
|---------|---------|
| `python -m pytest tests/ -v --tb=short` | All backend tests |
| `python -m pytest tests/ -m unit` | Unit tests only |
| `python -m pytest tests/ -m api` | API endpoint tests only |
| `python -m pytest tests/test_<file>.py -v` | Single test file |
| `python -m pytest tests/test_file.py::TestClass::test_fn -v` | Single test function |
| `python -m pytest tests/ --cov=app --cov-report=term-missing` | With coverage |
| `npm test -- --run` | All frontend tests (single pass) |
| `npm run test:coverage` | Frontend with coverage report |
