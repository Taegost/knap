---
title: 'feat: Corrections Lint Checker'
type: feat
status: deferred
date: 2026-06-21
---

# Corrections Lint Checker

Deferred from the Config File Defaults plan. A lint checker that validates content against a corrections index — known-wrong terms mapped to correct versions.

## Problem Frame

`corrections.yaml` exists in `.knap/schema/` as a placeholder. It's designed to hold known-wrong terms (misspellings, deprecated names, style violations) that scripts would check before commit. Currently it's empty (`[]`) and no script reads it. This plan would implement the actual checker.

## What Exists Today

**File:** `.knap/schema/corrections.yaml`

```yaml
# Corrections index
# Known-wrong terms mapped to correct versions.
# Checked by scripts before commit.
# Format:
#   - wrong: "incorrect term"
#     correct: "correct term"
#     context: "why the original was wrong"
#     source: "where the correction was found"
#     added: YYYY-MM-DD

[]
```

The file has a documented format but no loader and no consumer. It's the only config file in `.knap/schema/` with no associated script.

## Context from Related Work

- The **Config File Defaults plan** (`docs/plans/2026-06-20-002-chore-config-file-defaults-plan.md`) is building a shared config-loading module. That module will handle `folders.yaml` and `categories.yaml`. Once it exists, adding `corrections.yaml` support is straightforward — the loader pattern is already generalized.
- The **Modular Lint Checker System** (`docs/solutions/architecture-patterns/modular-lint-checker-system.md`) documents how lint checks are composed: `lint.py` orchestrates individual check modules. A corrections checker would follow this pattern.
- The **Orphan Content Checker plan** (`docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md`) is the most recent lint checker added — use it as a reference for structure and testing patterns.

## Requirements (TBD)

- A corrections checker module that reads `corrections.yaml` and scans content for known-wrong terms
- Integration with `lint.py` orchestration
- The checker should scan both frontmatter and body content
- Matching strategy (exact word, substring, regex) needs to be decided
- Whether the checker runs on raw files only or also wiki pages

## Dependencies

- Config File Defaults plan (shared config-loading module) — should be completed first
- `corrections.yaml` format is already documented in the file header

## Scope Boundaries

**Deferred from:** Config File Defaults plan — corrections.yaml has no consumer yet, so adding a loader for it alone provides no value until the checker exists.

**Out of scope:**
- Auto-correction or auto-fix (the checker reports, it doesn't fix)
- Integration with git hooks (that's a separate concern)
