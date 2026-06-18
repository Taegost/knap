---
title: "chore: CWD-Relative Path Resolution"
type: chore
status: deferred
date: 2026-06-18
origin: docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md
---

# CWD-Relative Path Resolution

Extracted from the Memory System Foundation plan. All scripts should use the same path resolution pattern.

## Problem Frame

`schema.py` uses `__file__`-relative resolution (`Path(__file__).parent.parent / "schema" / "categories.yaml"`), while other scripts use CWD-relative paths. This inconsistency is confusing and fragile — if a script is ever invoked from a different working directory, the `__file__`-relative path still resolves correctly, but CWD-relative paths break. The convention should be uniform.

## Requirements

- R23. `schema.py` converts `_SCHEMA_PATH` from `__file__`-relative to CWD-relative (`Path(".knap/schema/categories.yaml")`).
- R24. All scripts use the same path resolution pattern (CWD-relative).

## Implementation Notes

- `schema.py` line 10: change `_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "categories.yaml"` to `_SCHEMA_PATH = Path(".knap/schema / "categories.yaml")`
- Verify all other scripts already use CWD-relative paths (they do — `ingest.py`, `validate.py`, `lint.py` all use `Path("wiki/...")`, `Path("raw/...")` etc.)
- All scripts assume CWD = repo root (invocation: `python3 .knap/scripts/<name>.py`). This is the intended pattern.

## Scope

**In scope:**
- `schema.py` path constant change
- Verification that all scripts use consistent path resolution

**Out of scope:**
- Any other script changes
