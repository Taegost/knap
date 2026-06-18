---
title: "feat: Memory System Foundation"
type: feat
status: active
date: 2026-06-17
origin: docs/brainstorms/2026-06-17-knap-framework-requirements.md
---

# Memory System Foundation

## Summary

Create the context layer (scope, conventions, structure, decisions), update scripts for OKF alignment (omit fields, tolerate missing fields), and refactor the index system to per-category indexes with a master index. The structural migration to `.knap/` is handled separately (`docs/plans/2026-06-18-003-feat-migration-to-knap-dir-plan.md`).

## Problem Frame

The current repo structure is a temporary bootstrap. After the migration to `.knap/` completes (separate plan), two pieces remain: the context layer needs to be created, and the single `wiki/index.md` won't scale past a couple hundred documents. Both block further progress — the context layer defines conventions and structure for all downstream work, and the index will bloat context as content grows.

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

**Context**

- R6. `.knap/context/scope.md` defines project purpose, goals, and boundaries.
- R7. `.knap/context/conventions.md` defines rules, naming, hard constraints, workflow.
- R8. `.knap/context/structure.md` defines directory layout and relationships.
- R9. `.knap/context/decisions.md` records key choices with rationale.

**Index**

- R15. `ingest.py` generates per-category indexes (`wiki/{category}/index.md`) in addition to master index.
- R16. `lint.py` checks per-category indexes alongside master index.
- R18. Master `wiki/index.md` contains section headers that link to category index files.
- R19. Each category index (`wiki/{category}/index.md`) lists pages in that category.
- R20. `ingest.py` updates both the category index and the master index.

## Implementation Units

### U1. Create context layer

- **Goal:** Create the 4-file context structure under `.knap/context/`.
- **Requirements:** R6, R7, R8, R9
- **Dependencies:** Migration plan complete (`.knap/` directory exists)
- **Files:**
  - `.knap/context/scope.md` — project purpose, goals, boundaries
  - `.knap/context/conventions.md` — rules, naming, hard constraints, workflow (content from current `context/conventions.md`, updated for new paths)
  - `.knap/context/structure.md` — directory layout, how pieces relate
  - `.knap/context/decisions.md` — key choices from the brainstorm/synthesis docs
- **Approach:** Create `scope.md` from the brainstorm's Problem Frame and the strategy doc's Core Values. Migrate `conventions.md` from current location, updating paths and replacing the "n/a" rule ("Missing values: use 'n/a' for unknown scalars. Never omit a field.") with "Fields may be omitted when unknown. Scripts tolerate missing fields." Absorb `context/architecture.md` content into `structure.md`. Create `structure.md` from the architecture doc. Create `decisions.md` by extracting key decisions from the synthesis doc and requirements doc. Update pipeline commands in conventions.md to use `.knap/` paths.
- **Test scenarios:**
  - All 4 files exist under `.knap/context/`
  - Each file has content relevant to its purpose
  - No old `context/` directory at repo root
- **Verification:** Files exist and contain project-specific content, not placeholder text.

### U2. Update scripts for OKF alignment

- **Goal:** Scripts tolerate missing fields, omit "n/a" defaults, enforce only required fields.
- **Requirements:** R14, R17
- **Dependencies:** Migration plan complete (scripts at `.knap/` paths)
- **Files:**
  - `.knap/scripts/schema.py` — remove "n/a" from FIELD_DEFAULTS
  - `.knap/scripts/validate.py` — only check required fields (stop flagging missing category fields as warnings)
  - `.knap/scripts/ingest.py` — handle missing fields gracefully (omit from wiki output instead of rendering "n/a")
- **Approach:** Remove "n/a" from FIELD_DEFAULTS — scripts omit absent fields instead of filling defaults. `validate.py` checks only global required fields + category-specific required fields; missing optional fields are not warnings. `ingest.py` skips fields that are absent rather than rendering "n/a".
- **Test scenarios:**
  - `python3 .knap/scripts/validate.py raw/transcripts/` passes with no warnings for missing optional fields
  - A raw file with only required fields (no optional) validates and ingests cleanly
- **Verification:** Pipeline runs cleanly with OKF-aligned schema.

### U3. Refactor to per-category indexes

- **Goal:** Replace single master index with per-category indexes + master index.
- **Requirements:** R15, R16, R18, R19, R20
- **Dependencies:** Migration plan complete, U2 (scripts at `.knap/` paths, OKF alignment done)
- **Files:**
  - `.knap/scripts/ingest.py` — refactor `update_index()` to write category index + master
  - `.knap/scripts/lint.py` — add checks for category indexes
  - `wiki/index.md` — restructure to link to category indexes
  - `wiki/transcripts/index.md` — new per-category index
  - `wiki/prompts/index.md` — new per-category index (if prompts exist)
- **Approach:** `update_index()` writes to `wiki/{category}/index.md` first, then updates master `wiki/index.md` to ensure the category link exists. Master index contains section headers with links to category index files. Category indexes contain actual page links.
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

**CWD-relative paths everywhere.** All scripts should use CWD-relative path resolution. `schema.py` currently uses `__file__`-relative (`Path(__file__).parent.parent / "schema" / "categories.yaml"`) — this should be converted to CWD-relative to match the other scripts.

**Deferred for later (in other plans):**
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

## Discussion Items

**Session state ingestion.** Session state (`raw/reference/session-state-*.md`) is a living document updated as we go, not at session end. Needs discussion:
- Should session state be a dedicated category or stay as `reference`?
- Should the ingest skill handle session state updates, or is it a separate concern?
- How does the next session discover the current session state? (Currently: ROUTER.md links to it.)
- Should old session states be archived or overwritten?
- Should session state trigger re-ingestion of wiki pages automatically?

**Tags field.** Cross-cutting categorization via `tags: [tag1, tag2]` in frontmatter. Added to schema as optional. Aligns with OKF. Need to decide:
- Should tags be auto-generated by scripts or manually curated?
- Should the index support tag-based filtering?

## Sources / Research

- `docs/brainstorms/2026-06-17-knap-framework-requirements.md` — origin document
- `docs/strategy.md` — development principles and checklist
- `docs/synthesis-memory-framework-design.md` — architecture decisions
- `context/conventions.md` — operational conventions
