---
title: 'chore: Config File Defaults and Template Framework'
type: chore
status: active
date: 2026-06-20
---

# Config File Defaults and Template Framework

## Summary

Build a shared config-loading module with auto-creation from templates, define template files for each config, and migrate the existing per-file loaders to use it. Templates are the single source of truth for config defaults — no in-memory fallback. This eliminates inconsistent config handling where `load_folders.py` gracefully falls back but `schema.py` crashes on missing files.

## Problem Frame

Knap has three config files in `.knap/schema/`: `folders.yaml`, `categories.yaml`, and `corrections.yaml`. Each has a different loading pattern:

- `load_folders.py` has embedded defaults and gracefully handles missing/empty/malformed files — this was designed for the Orphan Content Checker.
- `schema.py` does a bare `open()` with no error handling — if `categories.yaml` is missing, every script that imports from `schema` crashes.
- `corrections.yaml` has no loader at all (deferred to `docs/plans/2026-06-21-001-feat-corrections-lint-plan.md`).

There's no mechanism to auto-create config files with defaults when missing. There's no template framework providing a reference for expected config structure.

## Requirements

**Shared config module:**
- R1. A shared `load_config.py` module that any script can use to load YAML config files
- R2. The module auto-creates config files from templates when they don't exist on disk
- R3. No in-memory fallback for malformed files — templates are the single source of truth. If a config file is missing or empty and its template exists, the module creates the config from the template and loads it. If the config file is malformed YAML, raise an error regardless of template availability. If the config is missing/empty and the template is also missing, raise an error with concrete remediation steps (e.g., "ensure the .knap/schema/templates/ directory exists; if you cloned this repo, try re-cloning or `git checkout -- .knap/schema/templates/`")
- R4. `load_config.py` performs no module-level loading — config is loaded fresh on each call. Consumers (like `schema.py`) may load at module level if their API requires constants-on-import, as long as they handle the error `load_config()` raises when the template is missing (see U3 for the schema.py pattern)

**Template framework:**
- R5. Template files in `.knap/schema/templates/` define the default content for each config file
- R6. Templates serve as documentation of expected config structure (comments, format examples)

**Migration:**
- R7. `load_folders.py` migrated to use `load_config.py` for loading, keeping its domain-specific getter functions
- R8. `schema.py` migrated to use `load_config.py` for loading, with error handling when `categories.yaml` is missing
- R9. All existing tests continue to pass after migration
- R10. All refactored code paths are covered by unit tests

## Key Technical Decisions

**KTD-1: Generalize the `load_folders.py` pattern.**
The `load_folders.py` approach (embedded defaults, graceful fallback, fresh load per call) is the proven starting point. The shared module replaces embedded defaults with template-based creation — templates are the single source of truth.

**KTD-2: Templates are the single source of truth.**
Template files in `.knap/schema/templates/` define the default config content. There are no in-memory defaults in the loader — if a config file doesn't exist, it's created from the template. If the template is also missing, that's a hard error (the repo hasn't been initialized properly). This eliminates the dual-source-of-truth maintenance risk.

**KTD-3: Auto-create on first access, not on module import.**
When a config file is missing, the loader creates it from the template and then reads it. This happens at the point of use, not at import time. This avoids import-time side effects and matches the `load_folders.py` "load fresh on each call" pattern.

**KTD-4: Thin wrapper migration, not import rewiring.**
`load_folders.py` and `schema.py` become thin wrappers around `load_config.py`. They keep their existing public API (`get_working_folders()`, `REQUIRED_FIELDS`, etc.) so no downstream scripts need import changes. This minimizes migration risk.

## Implementation Units

### U1. Shared config loader module

**Goal:** Create `load_config.py` — the shared module that all config loaders will use.

**Requirements:** R1, R2, R3, R4

**Dependencies:** None

**Files:**
- `.knap/scripts/load_config.py` (create)
- `.knap/scripts/test_load_config.py` (create)

**Approach:**
The module exports a primary function `load_config(path, template_path)` that:
1. Tries to read and parse the YAML file at `path`
2. If the file is missing or empty: loads the template from `template_path`, creates the config file at `path` with the template content, then returns the parsed template
3. If the file is malformed YAML: raises an error (no in-memory fallback — user must fix the file manually)
4. If the config is missing/empty and the template is also missing: raises an error with concrete remediation steps (e.g., "ensure .knap/schema/templates/ exists; try re-cloning or `git checkout -- .knap/schema/templates/`")
5. If the file is valid: returns the parsed dict as-is

No `defaults` parameter — templates are the single source of truth.

Auto-creation uses `try/except FileExistsError` scoped to the file-write call only (not the entire function) so concurrent creation is idempotent (handles parallel test runs) without masking permission errors or other filesystem issues.

**Test scenarios:**
- Happy path: valid config file returns parsed values
- Missing config with template: file is created from template, template content returned
- Missing config without template: raises error with concrete remediation steps
- Empty config with template: treated as missing — file is created from template, template content returned
- Empty config without template: raises error with concrete remediation steps
- Malformed YAML: raises error (no fallback — user must fix the file)
- Template copy preserves comments and structure
- Concurrent creation: second call doesn't clobber first (FileExistsError handled)

**Verification:** `load_config.py` can be imported and used independently. All test scenarios pass.

### U2. Template files

**Goal:** Create template files for each config that define the default content.

**Requirements:** R5, R6

**Dependencies:** None (parallel with U1)

**Files:**
- `.knap/schema/templates/folders.yaml.template` (create)
- `.knap/schema/templates/categories.yaml.template` (create)

**Approach:**
Template files are YAML with comments documenting the structure and each field's purpose. They contain the definitive default content for each config file.

The templates match the current config files' structure:
- `folders.yaml.template`: working/system/excluded folder classifications with comments explaining each category
- `categories.yaml.template`: categories, required fields, analysis labels, link types with comments explaining the schema

No bootstrap utility — bootstrapping/init is a separate concern for a future plan.

**Test scenarios:**
- Template content is valid YAML
- Template comments document the structure
- Template content matches expected config structure for the project

**Verification:** Template files exist and contain valid, well-documented YAML.

### U3. Migrate schema.py to shared module

**Goal:** Make `schema.py` use `load_config.py` so missing `categories.yaml` auto-creates from template instead of crashing.

**Requirements:** R8, R9, R10

**Dependencies:** U1

**Files:**
- `.knap/scripts/schema.py` (modify)
- `.knap/scripts/test_schema.py` (create)

**Approach:**
Replace the bare `open()` in `_load_schema()` with a call to `load_config()`. Pass `template_path` pointing to `.knap/schema/templates/categories.yaml.template`. Wrap the call in a try/except that catches the `load_config()` template-missing error and re-raises as a `RuntimeError` with a clear message about ensuring the `.knap/schema/templates/` directory exists.

The module-level loading stays (this is how `schema.py` works — constants are available on import). If the config file is missing or empty, `load_config()` creates it from the template. If the template is also missing, the wrapped error provides actionable guidance — this is the expected behavior (the repo isn't properly set up).

The `_save_schema()` function stays as-is (write operation, not delegating to load_config). The `reload()` function is updated to use `load_config()` for the read portion.

**Test scenarios:**
- Existing categories.yaml: all constants populated correctly (regression)
- Missing/empty categories.yaml: file auto-created from template, constants populated
- Missing template: import raises RuntimeError with concrete remediation steps
- Auto-creation: missing file is created from template with correct content
- Reload after edit: constants update correctly

**Verification:** `from schema import REQUIRED_FIELDS` works when `categories.yaml` exists. When both config and template are missing, the error message is clear about what to do. All existing scripts that import from `schema` continue to work.

### U4. Migrate load_folders.py to shared module

**Goal:** Make `load_folders.py` use `load_config.py` for loading, eliminating duplicate fallback logic.

**Requirements:** R7, R9, R10

**Dependencies:** U1

**Files:**
- `.knap/scripts/load_folders.py` (modify)
- `.knap/scripts/test_load_folders.py` (modify)

**Approach:**
Replace the inline `_load_config()` function with a call to `load_config()`. Remove the `_DEFAULTS` dict — templates are the single source of truth. Pass `template_path` pointing to `.knap/schema/templates/folders.yaml.template`.

**Test migration note:** Existing tests `test_missing_config_returns_defaults` and `test_empty_config_returns_defaults` must be rewritten. The new behavior is: missing/empty config + template present = auto-create and return; missing/empty config + template missing = raise error; malformed YAML = always raise error. Both tests should set up templates in `tmp_path` and verify auto-creation, or test the error-on-missing-template path.

The public API (`get_working_folders()`, `get_system_folders()`, `get_excluded_folders()`) stays unchanged. The `_get_folders()` helper stays (it does the dict-to-Path conversion).

**Test scenarios:**
- Existing tests pass after updating `test_missing_config_returns_defaults` and `test_empty_config_returns_defaults` (see test migration note above)
- Missing/empty config with template: file auto-created from template, template content returned
- Missing/empty config without template: raises error with concrete remediation steps
- Malformed config: raises error regardless of template availability
- Auto-created file matches expected structure

**Verification:** All existing tests pass. The module delegates to `load_config.py` with no duplicate fallback logic.

### U5. Test coverage for refactored code paths

**Goal:** Ensure all refactored code paths in `load_config.py`, `schema.py`, and `load_folders.py` are covered by unit tests.

**Requirements:** R9, R10

**Dependencies:** U1, U3, U4

**Files:**
- `.knap/scripts/test_load_config.py` (modify)
- `.knap/scripts/test_schema.py` (modify)
- `.knap/scripts/test_load_folders.py` (modify)

**Approach:**
Audit all code paths in the refactored modules and ensure each has a corresponding test:
- `load_config.py`: all branches (valid file, missing file + template exists, missing file + template missing, empty file, malformed YAML, concurrent creation)
- `schema.py`: module-level loading with template-based auto-creation, reload, error on missing template
- `load_folders.py`: all getter functions with template-based loading, error on missing template, updated tests for missing/empty config behavior

Use the `tmp_path` + `monkeypatch.chdir(tmp_path)` pattern established in `test_load_folders.py`.

**Test scenarios:**
- Every branch in `load_config()` has at least one test
- `schema.py` module-level loading works with and without existing config
- `load_folders.py` getters work with and without existing config
- Error messages are tested (missing template case)

**Verification:** `pytest .knap/scripts/` passes with all refactored modules having full branch coverage.

---

## Scope Boundaries

**In scope:**
- Shared config-loading module with auto-creation from templates
- Template files for `folders.yaml` and `categories.yaml` defining default content and config format
- Migration of `load_folders.py` and `schema.py`
- Unit test coverage for all refactored code paths

**Deferred to follow-up work:**
- Corrections lint checker — `docs/plans/2026-06-21-001-feat-corrections-lint-plan.md` (corrections.yaml has no consumer yet; adding a loader provides no value until the checker exists)
- Bootstrap/init utility — creating a CLI tool for repo initialization (separate plan)

**Outside this scope:**
- Migration of scripts that import from `schema` or `load_folders` (no import changes needed — thin wrapper approach)
- Git hooks or pre-commit integration

## Sources & Research

- `load_folders.py` — the proven pattern to generalize (graceful fallback, fresh load per call)
- `schema.py` — the problem case (bare `open()`, import-time crash risk)
- Orphan Content Checker plan (`docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md`) — established the `load_folders.py` pattern and deferred this plan
- Decisions doc (`.knap/context/decisions.md`) — "Config-Driven Folder Classification" decision documents the intent: "Scripts create config from template with defaults if file doesn't exist"
- Modular Lint Checker System solution (`docs/solutions/architecture-patterns/modular-lint-checker-system.md`) — architecture patterns for shared utilities
