---
title: "feat: Memory System Foundation"
type: feat
status: completed
date: 2026-06-17
origin: docs/brainstorms/2026-06-17-knap-framework-requirements.md
---

# Memory System Foundation

## Summary

Create the context layer (scope, conventions, structure, decisions), update scripts for OKF alignment (omit fields, tolerate missing fields), and refactor the index system to per-category indexes with a master index. The structural migration to `.knap/` is handled separately (`docs/plans/2026-06-18-003-feat-migration-to-knap-dir-plan.md`).

## Problem Frame

The migration to `.knap/` is handled separately (`docs/plans/2026-06-18-003-feat-migration-to-knap-dir-plan.md`). Two pieces remain: the context layer needs to be created, and the single `wiki/index.md` won't scale past a couple hundred documents. Both block further progress — the context layer defines conventions and structure for all downstream work, and the index will bloat context as content grows.

## Key Decisions

**Context layer is 4 files.** Replaces the mex-style `context/` directory with a structure that works for 80% of projects:
- `scope.md` — what this project is, why it exists, goals, boundaries
- `conventions.md` — rules, naming, hard constraints, workflow
- `structure.md` — directory layout, how pieces relate
- `decisions.md` — key choices and rationale (always present)

**Per-category indexes replace the single master index.** Each category gets `wiki/{category}/index.md`. A master `wiki/index.md` links to category indexes. Keeps individual files small and context-efficient.

**OKF alignment.** Soft preference — interoperability with OKF is preferred but not required. Knap's format aligns with Google's Open Knowledge Format (OKF) spec where practical. Same core structure (markdown + YAML frontmatter, index.md, log.md, standard markdown links). Key differences: we split AI-facing and human-facing content into separate directories, and we add category-specific fields.

**Fields can be omitted.** Drop the `"n/a"` convention. Unknown fields are simply absent from frontmatter. Aligns with OKF's permissive consumption. Scripts must tolerate missing fields gracefully.

## Requirements

**Context** (plan-local IDs; new requirements for context files)

- C1. `.knap/context/scope.md` defines project purpose, goals, and boundaries.
- C2. `.knap/context/conventions.md` defines rules, naming, hard constraints, workflow.
- C3. `.knap/context/structure.md` defines directory layout and relationships.
- C4. `.knap/context/decisions.md` records key choices with rationale.

**Index** (plan-local IDs; implement origin R13)

- I1. `ingest.py` generates per-category indexes (`wiki/{category}/index.md`) in addition to master index.
- I2. `lint.py` checks per-category indexes alongside master index.
- I3. Master `wiki/index.md` contains section headers that link to category index files.
- I4. Each category index (`wiki/{category}/index.md`) lists pages in that category.
- I5. `ingest.py` updates both the category index and the master index.

## Implementation Units

### U1. Create context layer

- **Goal:** Create the 4-file context structure under `.knap/context/`.
- **Requirements:** C1, C2, C3, C4
- **Dependencies:** Migration plan complete — `.knap/` directory exists, `.knap/context/conventions.md` and `.knap/context/architecture.md` already moved.
- **Files:**
  - `.knap/context/scope.md` — new: project purpose, goals, boundaries
  - `.knap/context/conventions.md` — update existing: replace "n/a" rule, update pipeline commands for `.knap/` paths
  - `.knap/context/structure.md` — new: absorb content from `.knap/context/architecture.md`, then delete `architecture.md`
  - `.knap/context/decisions.md` — new: key choices from the brainstorm/synthesis docs
- **Approach:** Create `scope.md` from the brainstorm's Problem Frame and the strategy doc's Core Values. Migrate `conventions.md` from current location, updating paths and replacing the "n/a" rule ("Missing values: use 'n/a' for unknown scalars. Never omit a field.") with "Fields may be omitted when unknown. Scripts tolerate missing fields." Absorb `.knap/context/architecture.md` content into `structure.md`. Create `structure.md` from the architecture doc. Create `decisions.md` by extracting key decisions from the synthesis doc and requirements doc. Update pipeline commands in conventions.md to use `.knap/` paths.
- **Test scenarios:**
  - All 4 files exist under `.knap/context/`
  - Each file has content relevant to its purpose
  - No old `context/` directory at repo root
- **Verification:** Files exist and contain project-specific content, not placeholder text.

### U2. Update scripts for OKF alignment

- **Goal:** Scripts tolerate missing fields, omit "n/a" defaults, enforce only required fields.
- **Requirements:** Supersedes origin R11 ("Missing values use n/a, never omitted") — scripts now omit absent fields
- **Dependencies:** Migration plan complete — scripts already at `.knap/` paths.
- **Files:**
  - `.knap/scripts/schema.py` — remove FIELD_DEFAULTS entirely (dead code — imported by ingest.py but never referenced in `build_wiki_page`)
  - `.knap/scripts/validate.py` — enforce all required fields (global and category-specific) as errors; optional fields produce no output
  - `.knap/scripts/ingest.py` — remove FIELD_DEFAULTS import; update `_val()` to treat actual None values as skip (currently only filters 'n/a' strings)
- **Approach:** FIELD_DEFAULTS is unused — `ingest.py` imports it but `build_wiki_page` never references it. Remove from `schema.py` entirely. `validate.py` currently reports missing category-specific required fields as warnings. Change these to errors to match the "enforce all required fields as errors" policy. Optional fields produce no output. `ingest.py`'s `_val()` function already filters None values and 'n/a' strings — no change needed to `_val()` itself. Remove the FIELD_DEFAULTS import since it is unused.
- **Test scenarios:**
  - `python3 .knap/scripts/validate.py raw/transcripts/` passes with no warnings for missing optional fields
  - A raw file with only required fields (no optional) validates and ingests cleanly
- **Verification:** Pipeline runs cleanly with OKF-aligned schema.

### U3. Refactor to per-category indexes

- **Goal:** Replace single master index with per-category indexes + master index.
- **Requirements:** I1, I2, I3, I4, I5
- **Dependencies:** Migration plan complete (scripts at `.knap/` paths), U2 (OKF alignment done)
- **Files:**
  - `.knap/scripts/ingest.py` — refactor `update_index()` to write category index + master
  - `.knap/scripts/lint.py` — add checks for category indexes
  - `wiki/index.md` — restructure to link to category indexes
  - `wiki/transcripts/index.md` — new per-category index
  - `wiki/prompts/index.md` — new per-category index (if prompts exist)
- **Approach:** Category folders, files, and index entries are created on-demand — no pre-creation for empty categories. `update_index()` writes to `wiki/{category}/index.md` first, then updates master `wiki/index.md` to ensure the category link exists. Master index contains section headers with links to category index files. Category indexes contain actual page links. All checks validate only existing content.
- **Test scenarios:**
  - Ingesting a file creates/updates `wiki/{category}/index.md`
  - Master `wiki/index.md` links to category indexes
  - `lint.py` checks both master and category indexes
  - Existing pages appear in correct category index
- **Verification:** `lint.py` passes with new index structure.

## Scope Boundaries

**In scope:**
- Context layer (scope, conventions, structure, decisions)
- Per-category indexes

**Deferred for later (in other plans):**
- Orphan content checker — `docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md`
- CWD-relative path resolution for `schema.py` — `docs/plans/2026-06-18-004-chore-cwd-relative-paths.md`
- Structural migration to `.knap/` — `docs/plans/2026-06-18-003-feat-migration-to-knap-dir-plan.md`
- Typed links — `docs/plans/2026-06-18-002-feat-typed-links-plan.md`
- Install scripts (`install.sh`, `install.ps1`) — separate plan
- Windows setup — separate plan
- `/knap init` skill — separate plan
- Self-improvement loop — separate brainstorm
- Update mechanism — separate brainstorm
- Pre-commit hooks
- Search fallback (BM25/embeddings)
- `patterns/` — procedural knowledge for recurring tasks. Investigate later.
- `events/` — structured JSONL log for Knap internals. Separate from wiki/log.md.
- Session state ingestion and tags field — `docs/brainstorms/2026-06-18-session-state-and-tags.md`

## Sources / Research

- `docs/brainstorms/2026-06-17-knap-framework-requirements.md` — origin document
- `docs/strategy.md` — development principles and checklist
- `docs/synthesis-memory-framework-design.md` — architecture decisions
- `.knap/context/conventions.md` — operational conventions
