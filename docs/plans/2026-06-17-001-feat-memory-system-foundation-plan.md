---
title: "feat: Memory System Foundation"
type: feat
status: active
date: 2026-06-17
origin: docs/brainstorms/2026-06-17-knap-framework-requirements.md
---

# Memory System Foundation

## Summary

Restructure the Knap repository so all framework files live under `.knap/`, create the context layer (scope, conventions, structure, decisions), refactor the index system to per-category indexes with a master index, and ensure the memory pipeline (raw → wiki → index → log) works end-to-end in the new structure. This is the foundation that install scripts, the init skill, and self-improvement all build on.

## Problem Frame

The current repo structure is a temporary bootstrap. Framework files (ROUTER.md, context/, schema/, scripts/, skills) are scattered at the repo root alongside user content (raw/, wiki/). This works for development but doesn't match the target architecture where everything Knap-managed lives in `.knap/`. Additionally, the single `wiki/index.md` won't scale past a couple hundred documents. Both issues block further progress — install scripts can't be written until the canonical structure is settled, and the index will bloat context as content grows.

## Key Decisions

**CLAUDE.md stays at repo root.** It's the thin anchor the LLM loads first. It points to `.knap/ROUTER.md`. All other framework files live in `.knap/`.

**Context layer is 4 files.** Replaces the mex-style `context/` directory with a structure that works for 80% of projects:
- `scope.md` — what this project is, why it exists, goals, boundaries
- `conventions.md` — rules, naming, hard constraints, workflow
- `structure.md` — directory layout, how pieces relate
- `decisions.md` — key choices and rationale (always present)

**Skills are hyphenated and stay in `.claude/skills/`.** Claude Code discovers skills from `.claude/skills/`. Directories are named `knap-ingest`, `knap-synthesize`. The `name` field in SKILL.md matches. Hyphenated names are more system-agnostic than spaced names.

**Per-category indexes replace the single master index.** Each category gets `wiki/{category}/index.md`. A master `wiki/index.md` links to category indexes. Keeps individual files small and context-efficient.

**Venv lives in `.knap/.venv/`.** Namespaced with the rest of the framework.

**Migration is atomic.** Move files, create context layer, rename skills, update paths, refactor indexes — all in one pass.

**PyYAML added to requirements.txt.** Currently imported but not declared.

**OKF alignment.** Knap's format aligns with Google's Open Knowledge Format (OKF) spec. Same core structure (markdown + YAML frontmatter, index.md, log.md, standard markdown links). Key differences: we split AI-facing and human-facing content into separate directories, and we add typed links and category-specific fields.

**Tags field added.** Cross-cutting categorization via `tags: [tag1, tag2]` in frontmatter. Aligns with OKF.

**Fields can be omitted.** Drop the `"n/a"` convention. Unknown fields are simply absent from frontmatter. Aligns with OKF's permissive consumption. Scripts must tolerate missing fields gracefully.

**Optional typed links in frontmatter.** Frontmatter can include a `links` list with typed relationships:

```yaml
links:
  - target: wiki/other-page.md
    type: Related
  - target: wiki/another.md          # type is optional — untyped link
```

Body markdown links are also valid. Frontmatter links are for structured, machine-readable relationships. Body links are for narrative cross-references.

## Requirements

**Structure**

- R1. All framework files except CLAUDE.md live under `.knap/` (ROUTER.md, context/, schema/, scripts/).
- R2. CLAUDE.md stays at repo root as thin anchor pointing to `.knap/ROUTER.md`.
- R3. User content (raw/, wiki/) stays at repo root.
- R4. Venv at `.knap/.venv/` with all Python dependencies.
- R5. `scripts/requirements.txt` includes PyYAML explicitly.

**Context**

- R6. `.knap/context/scope.md` defines project purpose, goals, and boundaries.
- R7. `.knap/context/conventions.md` defines rules, naming, hard constraints, workflow.
- R8. `.knap/context/structure.md` defines directory layout and relationships.
- R9. `.knap/context/decisions.md` records key choices with rationale.

**Skills**

- R10. Skills renamed with hyphenated `/knap` prefix: `knap-ingest`, `knap-synthesize`.
- R11. Skills stay in `.claude/skills/` for Claude Code discovery.
- R12. Skills reference scripts via `.knap/scripts/` paths.
- R13. Skills reference schema via `.knap/schema/categories.yaml`.

**Pipeline**

- R14. `validate.py` reads schema from `.knap/schema/categories.yaml` via `schema.py`.
- R15. `ingest.py` generates per-category indexes (`wiki/{category}/index.md`) in addition to master index.
- R16. `lint.py` checks per-category indexes alongside master index.
- R17. `schema.py` loads from `.knap/schema/categories.yaml` relative to its own location.

**Index**

- R18. Master `wiki/index.md` contains section headers that link to category index files.
- R19. Each category index (`wiki/{category}/index.md`) lists pages in that category.
- R20. `ingest.py` updates both the category index and the master index.

## Implementation Units

### U1. Move framework files to `.knap/`

- **Goal:** Establish the canonical `.knap/` directory structure.
- **Requirements:** R1, R2, R3
- **Dependencies:** None
- **Files:**
  - `.knap/ROUTER.md` (moved from root)
  - `.knap/schema/categories.yaml` (moved from `schema/`)
  - `.knap/schema/corrections.yaml` (moved from `schema/`)
  - `.knap/scripts/schema.py` (moved from `scripts/`)
  - `.knap/scripts/validate.py` (moved from `scripts/`)
  - `.knap/scripts/ingest.py` (moved from `scripts/`)
  - `.knap/scripts/lint.py` (moved from `scripts/`)
  - `.knap/scripts/fetch_youtube_transcript.py` (moved from `scripts/`)
  - `.knap/scripts/requirements.txt` (moved from `scripts/`)
  - `.knap/scripts/setup_venv.sh` (moved from `scripts/`)
  - Root `CLAUDE.md` — rewrite as thin anchor: non-negotiables + "Read `.knap/ROUTER.md`"
  - Remove old `context/`, `schema/`, `scripts/` from root
- **Approach:** Move files with `git mv`. Rewrite root `CLAUDE.md` as a thin anchor (under 15 lines). Remove old directories.
- **Test scenarios:**
  - All framework files exist under `.knap/`
  - Root `CLAUDE.md` exists and points to `.knap/ROUTER.md`
  - No framework directories remain at repo root (except `.claude/`)
  - `raw/` and `wiki/` unchanged at repo root
- **Verification:** `ls .knap/` shows ROUTER.md, schema/, scripts/. Root `CLAUDE.md` is under 15 lines.

### U2. Create context layer

- **Goal:** Create the 4-file context structure under `.knap/context/`.
- **Requirements:** R6, R7, R8, R9
- **Dependencies:** U1
- **Files:**
  - `.knap/context/scope.md` — project purpose, goals, boundaries
  - `.knap/context/conventions.md` — rules, naming, hard constraints, workflow (content from current `context/conventions.md`, updated for new paths)
  - `.knap/context/structure.md` — directory layout, how pieces relate
  - `.knap/context/decisions.md` — key choices from the brainstorm/synthesis docs
- **Approach:** Create `scope.md` from the brainstorm's Problem Frame and the strategy doc's Core Values. Migrate `conventions.md` from current location, updating paths. Create `structure.md` from the architecture doc. Create `decisions.md` by extracting key decisions from the synthesis doc and requirements doc.
- **Test scenarios:**
  - All 4 files exist under `.knap/context/`
  - Each file has content relevant to its purpose
  - No old `context/` directory at repo root
- **Verification:** Files exist and contain project-specific content, not placeholder text.

### U3. Update all internal paths

- **Goal:** Scripts and skills reference the new `.knap/` locations.
- **Requirements:** R12, R13, R14, R17
- **Dependencies:** U1, U2
- **Files:**
  - `.knap/scripts/schema.py` — update `_SCHEMA_PATH`
  - `.knap/scripts/validate.py` — update import path
  - `.knap/scripts/ingest.py` — update import path, INDEX_PATH, LOG_PATH
  - `.knap/scripts/lint.py` — update import path
  - `.knap/ROUTER.md` — update file references to `.knap/context/` paths
  - `.knap/context/conventions.md` — update pipeline commands
- **Approach:** `schema.py` uses `Path(__file__).parent.parent / "schema" / "categories.yaml"`. Other scripts import from same directory. ROUTER.md and conventions.md reflect `.knap/` paths. Pipeline commands become `python3 .knap/scripts/validate.py raw/{category}/`.
- **Test scenarios:**
  - `python3 .knap/scripts/validate.py raw/transcripts/` passes
  - `python3 .knap/scripts/ingest.py --dry-run raw/transcripts/*.md` shows correct paths
  - `python3 .knap/scripts/lint.py` passes
- **Verification:** Full pipeline runs with `.knap/` paths: validate → ingest → lint.

### U4. Rename skills to `/knap` prefix

- **Goal:** Namespace skills under `/knap` with hyphenated names.
- **Requirements:** R10, R11, R12, R13
- **Dependencies:** U1
- **Files:**
  - `.claude/skills/knap-ingest/SKILL.md` (renamed from `.claude/skills/ingest/`)
  - `.claude/skills/knap-synthesize/SKILL.md` (renamed from `.claude/skills/synthesize/`)
- **Approach:** Rename skill directories with `git mv`. Update `name` field in SKILL.md frontmatter to match directory name. Update script paths in skill instructions to use `.knap/scripts/` paths. Skills stay in `.claude/skills/` for Claude Code discovery.
- **Test scenarios:**
  - `/knap-ingest` and `/knap-synthesize` appear in slash menu
  - Script paths in skills resolve correctly
  - No collision with user-defined skills
- **Verification:** Skills load and their script references resolve.

### U5. Refactor to per-category indexes

- **Goal:** Replace single master index with per-category indexes + master index.
- **Requirements:** R15, R16, R18, R19, R20
- **Dependencies:** U3
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

### U6. Set up Python venv

- **Goal:** Isolate Python dependencies in a venv under `.knap/`.
- **Requirements:** R4, R5
- **Dependencies:** U1
- **Files:**
  - `.knap/.venv/` — created by setup script
  - `.knap/scripts/requirements.txt` — add PyYAML
  - `.knap/scripts/setup_venv.sh` — update paths
  - `.gitignore` — add `.knap/.venv/`
- **Approach:** Update `setup_venv.sh` to create venv at `.knap/.venv/`. Add `PyYAML` to `requirements.txt`. Add `.knap/.venv/` to `.gitignore`.
- **Test scenarios:**
  - `bash .knap/scripts/setup_venv.sh` creates `.knap/.venv/`
  - `source .knap/.venv/bin/activate && python3 -c "import yaml"` succeeds
  - `.knap/.venv/` is in `.gitignore`
- **Verification:** Fresh venv install + full pipeline runs clean.

### U7. Verify end-to-end pipeline

- **Goal:** Confirm the full memory pipeline works in the new structure.
- **Requirements:** All
- **Dependencies:** U1, U2, U3, U4, U5, U6
- **Files:** None (verification only)
- **Approach:** Run the complete pipeline on existing content:
  1. `python3 .knap/scripts/validate.py raw/`
  2. `python3 .knap/scripts/ingest.py --force raw/transcripts/*.md`
  3. `python3 .knap/scripts/lint.py`
  4. Verify wiki pages, category indexes, master index, skills
- **Test scenarios:**
  - Full pipeline passes with zero errors
  - Wiki pages have correct content
  - Indexes are structured correctly
  - Skills load and reference correct paths
- **Verification:** `lint.py` returns 0 issues.

## Scope Boundaries

**In scope:**
- `.knap/` directory migration
- Context layer (scope, conventions, structure, decisions)
- Per-category indexes
- Python venv setup
- Skill renaming
- Path updates across all scripts and skills

**Deferred for later:**
- Install scripts (`install.sh`, `install.ps1`) — separate plan
- Windows setup — separate plan
- `/knap init` skill — separate plan
- Self-improvement loop — separate brainstorm
- Update mechanism — separate brainstorm
- Pre-commit hooks
- Search fallback (BM25/embeddings)
- `patterns/` — procedural knowledge for recurring tasks. Investigate later.
- `events/` — structured JSONL log for Knap internals. Separate from wiki/log.md.

## Sources / Research

- `docs/brainstorms/2026-06-17-knap-framework-requirements.md` — origin document
- `docs/strategy.md` — development principles and checklist
- `docs/synthesis-memory-framework-design.md` — architecture decisions
- `context/conventions.md` — operational conventions
