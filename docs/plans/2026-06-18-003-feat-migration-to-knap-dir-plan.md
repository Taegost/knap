---
title: "feat: Migration to .knap/ Directory"
type: feat
status: completed
date: 2026-06-18
origin: docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md
---

# Migration to .knap/ Directory

Extracted from the Memory System Foundation plan. This plan covers the structural migration: moving framework files to `.knap/`, updating all script paths, renaming skills, and setting up the venv. Context layer creation and index refactoring remain in the foundation plan.

## Problem Frame

The current repo structure is a temporary bootstrap. Framework files (ROUTER.md, context/, schema/, scripts/, skills) are scattered at the repo root alongside user content (raw/, wiki/). This works for development but doesn't match the target architecture where everything Knap-managed lives in `.knap/`. This blocks further progress — install scripts can't be written until the canonical structure is settled.

## Key Decisions

**CLAUDE.md stays at repo root.** It's the thin anchor the LLM loads first. It points to `.knap/ROUTER.md`. All other framework files live in `.knap/`.

**Skills are hyphenated and stay in `.claude/skills/`.** Claude Code discovers skills from `.claude/skills/`. Directories are named `knap-ingest`, `knap-synthesize`. The `name` field in SKILL.md matches.

**Venv lives in `.knap/.venv/`.** Namespaced with the rest of the framework.

**PyYAML added to requirements.txt.** Currently imported but not declared.

## Requirements

- R1. All framework files except CLAUDE.md live under `.knap/` (ROUTER.md, context/, schema/, scripts/).
- R2. CLAUDE.md stays at repo root as thin anchor pointing to `.knap/ROUTER.md`.
- R3. User content (raw/, wiki/) stays at repo root.
- R4. Venv at `.knap/.venv/` with all Python dependencies.
- R5. `.knap/scripts/requirements.txt` includes PyYAML explicitly.
- R10. Skills renamed with hyphenated `/knap` prefix: `knap-ingest`, `knap-synthesize`.
- R11. Skills stay in `.claude/skills/` for Claude Code discovery.
- R12. Skills reference scripts via `.knap/scripts/` paths.
- R13. Skills reference schema via `.knap/schema/categories.yaml`.
- R14. `validate.py` reads schema from `.knap/schema/categories.yaml` via `schema.py`.
- R17. `schema.py` loads from `.knap/schema/categories.yaml` relative to its own location.

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
  - `.knap/context/conventions.md` (moved from `context/`)
  - `.knap/context/architecture.md` (moved from `context/`)
  - Root `CLAUDE.md` — rewrite as thin anchor: non-negotiables + "Read `.knap/ROUTER.md"` (drop the n/a rule — frontmatter conventions now live in conventions.md)
  - Remove old `schema/`, `scripts/` from root
- **Approach:** Move files with `git mv`. Move `context/` as-is to `.knap/context/` — no content changes, just aligning folder structure. Rewrite root `CLAUDE.md` as a thin anchor (under 15 lines). Remove old `schema/` and `scripts/` directories. Content updates to context/ files (absorbing architecture.md, updating conventions) are handled by the foundation plan.
- **Test scenarios:**
  - All framework files exist under `.knap/`
  - Root `CLAUDE.md` exists and points to `.knap/ROUTER.md`
  - No framework directories remain at repo root (except `.claude/`)
  - `raw/` and `wiki/` unchanged at repo root
- **Verification:** `ls .knap/` shows ROUTER.md, schema/, scripts/. Root `CLAUDE.md` is under 15 lines.

### U2. Update paths, schema, and scripts

- **Goal:** Scripts reference new `.knap/` locations.
- **Requirements:** R14, R17
- **Dependencies:** U1
- **Files:**
  - `.knap/scripts/schema.py` — no change needed (`_SCHEMA_PATH` uses `__file__`-relative resolution, already correct after move)
  - `.knap/scripts/validate.py` — update import path
  - `.knap/scripts/ingest.py` — update import path, INDEX_PATH, LOG_PATH
  - `.knap/scripts/lint.py` — update import path
  - `.knap/ROUTER.md` — update all routing table paths: `schema/categories.yaml` → `.knap/schema/categories.yaml` (4 occurrences), `context/conventions.md` → `.knap/context/conventions.md` (5 occurrences), `scripts/lint.py` → `.knap/scripts/lint.py` (1 occurrence)
  - `.knap/context/conventions.md` — update pipeline commands: `scripts/validate.py` → `.knap/scripts/validate.py`, `scripts/ingest.py` → `.knap/scripts/ingest.py`, `scripts/lint.py` → `.knap/scripts/lint.py` (3 occurrences on lines 59-61)
- **Approach:** All scripts assume CWD = repo root (invocation: `python3 .knap/scripts/<name>.py`). ROUTER.md paths are instructions to the LLM, which also operates from repo root CWD — therefore `.knap/` prefix is required (paths are not resolved relative to ROUTER.md's own location). Path constants like `WIKI_DIR`, `INDEX_PATH`, `LOG_PATH` are relative to CWD, not to the script location. Existing wiki source links (`../raw/...`) are unchanged since `raw/` and `wiki/` remain at root. Scripts use bare `from schema import ...` (not relative imports) — Python adds the script's directory to sys.path when invoked directly. This is the intended invocation pattern; do not switch to relative imports or module invocation. `schema.py` uses `Path(__file__).parent.parent / "schema" / "categories.yaml"` — this is `__file__`-relative and resolves correctly after the move (no change needed now; conversion to CWD-relative is deferred to the foundation plan). ROUTER.md reflects `.knap/` paths. Pipeline commands become `python3 .knap/scripts/validate.py raw/{category}/`.
- **Test scenarios:**
  - `python3 .knap/scripts/validate.py raw/transcripts/` passes
  - `python3 .knap/scripts/ingest.py --dry-run raw/transcripts/*.md` shows correct paths
  - `python3 .knap/scripts/lint.py` passes
- **Verification:** Full pipeline runs with `.knap/` paths: validate → ingest → lint.

### U3. Rename skills to `/knap` prefix

- **Goal:** Namespace skills under `/knap` with hyphenated names.
- **Requirements:** R10, R11, R12, R13
- **Dependencies:** U1
- **Files:**
  - `.claude/skills/knap-ingest/SKILL.md` (renamed from `.claude/skills/ingest/`)
  - `.claude/skills/knap-synthesize/SKILL.md` (renamed from `.claude/skills/synthesize/`)
- **Approach:** Rename skill directories with `git mv`. Update `name` field in SKILL.md frontmatter to match directory name. Update script paths in skill instructions to use `.knap/scripts/` paths. Skills stay in `.claude/skills/` for Claude Code discovery. Path-change checklist:
  - `ingest/SKILL.md` (8 replacements): `source scripts/.venv/bin/activate` → `source .knap/.venv/bin/activate`, `python scripts/fetch_youtube_transcript.py` → `python .knap/scripts/fetch_youtube_transcript.py`, `python scripts/validate.py` → `python .knap/scripts/validate.py`, `python scripts/ingest.py` → `python .knap/scripts/ingest.py`, `python scripts/lint.py` → `python .knap/scripts/lint.py`, `schema/categories.yaml` → `.knap/schema/categories.yaml` (3 occurrences)
  - `synthesize/SKILL.md` (3 updates): `python scripts/validate.py` → `python .knap/scripts/validate.py`, `python scripts/ingest.py` → `python .knap/scripts/ingest.py`, `python scripts/lint.py` → `python .knap/scripts/lint.py`
- **Test scenarios:**
  - `/knap-ingest` and `/knap-synthesize` appear in slash menu
  - Script paths in skills resolve correctly
  - No collision with user-defined skills
- **Verification:** Skills load and their script references resolve.

### U4. Set up Python venv

- **Goal:** Isolate Python dependencies in a venv under `.knap/`.
- **Requirements:** R4, R5
- **Dependencies:** U1
- **Files:**
  - `.knap/.venv/` — created by setup script
  - `.knap/scripts/requirements.txt` — add PyYAML
  - `.knap/scripts/setup_venv.sh` — update paths
  - `.gitignore` — add `.knap/.venv/`
- **Approach:** Update `setup_venv.sh` to create venv at `.knap/.venv/`. Fix echo message: `source scripts/.venv/bin/activate` → `source .knap/.venv/bin/activate`. Add `PyYAML` to `requirements.txt`. Add `.knap/.venv/` to `.gitignore`.
- **Test scenarios:**
  - `bash .knap/scripts/setup_venv.sh` creates `.knap/.venv/`
  - `source .knap/.venv/bin/activate && python3 -c "import yaml"` succeeds
  - `.knap/.venv/` is in `.gitignore`
- **Verification:** Fresh venv install + full pipeline runs clean.

### U5. Verify end-to-end pipeline

- **Goal:** Confirm the full memory pipeline works in the new structure.
- **Requirements:** R1, R2, R3, R10, R11, R12, R13, R14, R17
- **Dependencies:** U1, U2, U3, U4
- **Files:** None (verification only)
- **Approach:** Run the complete pipeline on existing content:
  1. `python3 .knap/scripts/validate.py raw/` (also accepts category-scoped paths like `raw/transcripts/`)
  2. `python3 .knap/scripts/ingest.py --force raw/transcripts/*.md`
  3. `python3 .knap/scripts/lint.py`
  4. Verify wiki pages, skills load, script paths resolve
- **Test scenarios:**
  - Full pipeline passes with zero errors
  - Wiki pages have correct content
  - Skills load and reference correct paths
- **Verification:** `lint.py` returns 0 issues.

## Scope Boundaries

**In scope:**
- `.knap/` directory migration
- Path updates across all scripts and skills
- Python venv setup
- Skill renaming

**Deferred for later (remains in foundation plan):**
- Context layer (scope, conventions, structure, decisions)
- Per-category indexes
- Typed links — separate plan (`docs/plans/2026-06-18-002-feat-typed-links-plan.md`)
- Convert schema.py `_SCHEMA_PATH` from `__file__`-relative to CWD-relative — all scripts should use the same path resolution pattern

## Sources / Research

- `docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md` — origin plan
- `docs/brainstorms/2026-06-17-knap-framework-requirements.md` — requirements
- `docs/strategy.md` — development principles
