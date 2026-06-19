---
title: "chore: CWD-Relative Path Resolution"
type: chore
status: completed
date: 2026-06-18
origin: docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md
---

# CWD-Relative Path Resolution

## Summary

Convert `schema.py`'s `_SCHEMA_PATH` from `__file__`-relative to CWD-relative resolution, matching the pattern all other production scripts already use. Verify consistency across all production scripts. Document the full convention in `conventions.md`, including the test file exclusion.

## Problem Frame

`schema.py` uses `__file__`-relative resolution (`Path(__file__).parent.parent / "schema" / "categories.yaml"`), while all other production scripts use CWD-relative paths (`Path("wiki/...")`, `Path("raw/...")`). This inconsistency is confusing — if a script is ever invoked from a different working directory, the `__file__`-relative path still resolves correctly, but CWD-relative paths break. The convention should be uniform. All scripts assume CWD = repo root (invocation: `python3 .knap/scripts/<name>.py`).

## Requirements

- R23. `schema.py` converts `_SCHEMA_PATH` from `__file__`-relative to CWD-relative (`Path(".knap/schema/categories.yaml")`).
- R24. All production scripts use the same path resolution pattern (CWD-relative). Test files are excluded — `__file__`-relative resolution is standard pytest practice.
- R25. `conventions.md` documents the CWD-relative path resolution convention.

## Implementation Units

### U1. Convert schema.py to CWD-relative path

- **Goal:** Change `_SCHEMA_PATH` to use CWD-relative resolution, matching all other scripts. Document the convention in `conventions.md`.
- **Requirements:** R23, R24, R25
- **Dependencies:** Migration plan complete (`.knap/` directory structure exists).
- **Files:**
  - `.knap/scripts/schema.py` — change `_SCHEMA_PATH` constant (line 10)
  - `.knap/context/conventions.md` — add "Script Path Resolution" section documenting the CWD-relative convention
- **Approach:** Change `_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "categories.yaml"` to `_SCHEMA_PATH = Path(".knap/schema/categories.yaml")`. This removes schema.py's CWD-agnostic resolution — all scripts will uniformly require CWD=repo-root. Add a conventions section documenting the full convention: all production scripts use CWD-relative paths and assume CWD = repo root; test files are excluded (`__file__`-relative resolution is standard pytest practice). Then verify all production scripts (`ingest.py`, `validate.py`, `lint.py`) use CWD-relative paths — they do (`"wiki"`, `"wiki/index.md"`, `"raw/..."` etc.).
- **Test scenarios:**
  - `python3 .knap/scripts/schema.py` loads `categories.yaml` successfully when CWD is repo root
  - `python3 .knap/scripts/ingest.py` still works end-to-end after the change (imports `schema.py`)
  - `python3 .knap/scripts/validate.py` still works after the change
  - `python3 .knap/scripts/lint.py` runs cleanly from repo root after the change
  - `conventions.md` contains a "Script Path Resolution" section with the CWD-relative convention
- **Verification:** All scripts run cleanly from repo root with consistent path resolution. Convention is documented.

## Scope Boundaries

**In scope:**
- `schema.py` path constant change
- Documenting the CWD-relative convention in `conventions.md`
- Verification that all scripts use consistent path resolution

**Out of scope:**
- Any other script changes except what is explicitly documented in this plan
- Changes to script invocation patterns (all assume CWD = repo root)
