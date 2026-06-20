---
title: 'feat: Typed Links'
type: feat
status: active
date: 2026-06-18
origin: docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md
prerequisites:
- Markdown-first frontmatter converter script (converts existing wiki pages to yaml.dump()-formatted
  frontmatter)
---

# Typed Links

## Summary

Add structured, machine-readable relationships between wiki pages via an optional `links` field in frontmatter. Each link has a `target` (repo-relative path to another wiki page) and an optional `type` (e.g., "Related", "Parent", "SynthesizedFrom"). A pure helper script checks whether a given URI exists; the lint workflow orchestrates link extraction and validation. A separate file-rename hook updates links when files move.

## Problem Frame

Wiki pages currently have no way to express typed relationships to other pages. Body markdown links serve narrative cross-references, but there's no structured, machine-readable surface for relationships like "related to", "parent of", or "synthesized from". This blocks graph-based features, automated relationship traversal, and richer wiki output that surfaces connections between pages.

The `links` field name is already reserved in `.knap/schema/categories.yaml` as an optional field, but has no structural definition, no validation, and is silently dropped during ingestion.

## Requirements

- R21. Frontmatter `links` field with typed relationships is supported by schema, validated, and rendered in wiki output. The `type` field on each link is optional.
- R22. Link validation: frontmatter link targets are verified (errors on broken links). Body markdown link targets in regular pages (excluding `log.md`) are verified (warnings only, informational). Body links in index files are verified as errors (system-maintained content).
- R23. File-rename hook: when a file is renamed or moved, all references to it (frontmatter `links` targets, body `[text](target)` links, and body `[[target]]` wiki-links) are updated automatically.

## Key Technical Decisions

**KTD-1: Optional typed links in frontmatter.** Frontmatter can include a `links` list with typed relationships:

```yaml
links:
  - target: wiki/other-page.md
    type: Related
  - target: wiki/another.md          # type is optional — untyped link
```

Body markdown links are also valid. Frontmatter links are for structured, machine-readable relationships. Body links are for narrative cross-references. Rationale: separating the two surfaces keeps frontmatter clean for tooling while preserving markdown's natural link syntax for prose.

**KTD-2: `links` field is canonical for machine-readable relationships.** Frontmatter `links` is the authoritative source for structured relationships. It renders in wiki page frontmatter for downstream consumers (AI agents, index generators, graph tools). Body markdown links stay in body — they're supporting examples and human use. Rationale: single source of truth for structured data; no duplication between frontmatter and body.

**KTD-3: Frontmatter link failures are errors; body link failures are warnings (except index files).** Frontmatter links are explicit, intentional declarations — a broken one is a bug. Body markdown links in regular pages are narrative — a broken one is informational (warnings). Body links in index files (`index.md`) are system-maintained — a broken one is an error. The lint workflow enforces this split. Rationale: structured data and system-maintained content should be correct; prose links in user-authored pages are softer.

**KTD-4: `check_links.py` is a pure helper with two calling modes.** `check_links.py` does one thing: given a path, check whether the file exists on disk. Two calling conventions via a single function with an optional parameter:
- `check_link(link)` — assumes `link` is repo-relative, resolves from repo root
- `check_link(link, path_to_file)` — assumes `link` is file-relative, resolves from `path_to_file`'s parent directory

It does not parse frontmatter, extract links, traverse files, or make decisions about error vs. warning. Another script (the lint workflow) handles orchestration. Rationale: single-responsibility; the two modes cover both frontmatter (repo-relative) and body (file-relative) path conventions without the helper needing to know which context it's in.

**KTD-5: Path resolution differs by link source.** Frontmatter link targets are repo-relative paths (e.g., `wiki/other-page.md`), resolved from repo root. Body `[text](target)` links are file-relative paths (e.g., `../other-page.md`), resolved from the file's parent directory. Only `[text](target)` syntax is validated — `[[target]]` wiki-link syntax is not checked by the link validator. Rationale: frontmatter links are machine-authored with stable repo-relative paths; body links follow markdown's natural relative-path convention; `[[target]]` links are commonly used to reference pages that may not exist yet and provide low validation value.

**KTD-6: Link type vocabulary.** The `type` field accepts free-text, but the following types are recommended conventions:

- `Related` — general association
- `Parent` / `Child` — hierarchical relationship
- `Supersedes` / `SupersededBy` — replacement chain
- `IngestedFrom` / `IngestedTo` — raw-to-wiki provenance
- `SynthesizedFrom` / `SynthesizedTo` — synthesis provenance

These are recommendations, not enforcement. No validation that `type` values come from this list. Rationale: gives users consistent vocabulary without constraining them; enables future graph features to interpret common relationship types.

**KTD-7: Order of operations — link checking is last.** Link validation runs after all other pipeline steps (ingestion, index updates, etc.) are complete. This ensures all wiki pages exist before their links are checked. Frontmatter `links` that reference files that haven't been ingested yet are errors — the linked file must exist first. Rationale: checking links before ingestion completes would produce false positives for links to files that are about to be created.

**KTD-8: `[[target]]` wiki-link syntax is deliberately not validated.** The link validator only checks `[text](target)` syntax (both frontmatter and body). `[[target]]` wiki-links are not validated because they commonly reference pages that may not exist yet (users routinely pre-populate wiki-links to planned pages). The rename hook (`update_links_on_rename.py`) does update `[[target]]` links when files move. Rationale: validating `[[target]]` links would produce excessive false positives in workflows where users plan content structure before creating all pages.

## Implementation Units

### U1. Add `links` structure to schema

- **Goal:** Define the structural schema for the `links` field so validation and ingestion can enforce it.
- **Requirements:** R21
- **Dependencies:** None
- **Files:**
  - `.knap/scripts/schema.py` — add `LINK_SCHEMA` constant defining the expected structure (`target` required string, `type` optional string)
- **Approach:** Add a `LINK_SCHEMA` dict or similar structure to `schema.py` that defines the shape of a single link entry: `target` (required, string) and `type` (optional, string). This is consumed by `validate.py` and `ingest.py` — not by `categories.yaml` (which already has `links` as an optional field name). Keep it in Python since the structure is simple and version-controlled alongside the scripts that use it.
- **Test scenarios:**
  - Happy path: `LINK_SCHEMA` is importable and contains `target` (required) and `type` (optional) keys
  - Edge case: importing `schema.py` does not break existing `REQUIRED_FIELDS`, `OPTIONAL_FIELDS`, or `CATEGORIES` loading
- **Verification:** `python3 -c "from schema import LINK_SCHEMA; print(LINK_SCHEMA)"` succeeds and shows the expected structure.

### U2. Validate `links` structure in `validate.py`

- **Goal:** Frontmatter `links` entries are validated for correct structure — each must have a `target` string, and `type` (if present) must be a string.
- **Requirements:** R21
- **Dependencies:** U1
- **Files:**
  - `.knap/scripts/validate.py` — add `links` structure validation to `validate_file()`
- **Approach:** After existing field validation, if `links` is present in frontmatter, check that it's a list. For each entry, verify `target` exists and is a string. If `type` is present, verify it's a string. Report structural errors (missing `target`, wrong types) as validation errors. Do not check whether targets exist here — that's the lint workflow's job.
- **Test scenarios:**
  - Happy path: a file with valid `links` (each has `target`, optional `type`) passes validation
  - Edge case: a file with `links: []` (empty list) passes validation
  - Error path: a file with a link entry missing `target` produces an error
  - Error path: a file with a link entry where `target` is not a string produces an error
  - Error path: a file with `links` as a string (not a list) produces an error
  - Edge case: a file with no `links` field passes validation (field is optional)
- **Verification:** `python3 .knap/scripts/validate.py` passes on files with valid links and reports errors on files with invalid link structure.

### U3. Pass `links` field through ingestion

- **Goal:** When raw frontmatter has a `links` field, it's preserved in wiki page frontmatter.
- **Requirements:** R21
- **Dependencies:** U1
- **Files:**
  - `.knap/scripts/ingest.py` — add `links` to the field copy list in `build_wiki_page()`
- **Approach:** Replace the manual string-based serialization (lines 96-99) with `yaml.dump()` for all frontmatter output. The current `f"  - {item}"` pattern produces Python repr for dicts and doesn't follow markdown-first conventions. Use `yaml.dump()` to serialize the entire frontmatter dict as valid YAML. This handles `links` (list-of-dict) and all other fields uniformly. Ensure the output is valid YAML that round-trips through `yaml.safe_load()`. **Prerequisite:** a markdown-first converter script must be implemented first to convert existing wiki pages to `yaml.dump()`-formatted frontmatter.
- **Test scenarios:**
  - Happy path: ingesting a raw file with `links` produces a wiki page with the same `links` in frontmatter
  - Edge case: ingesting a raw file without `links` produces a wiki page without `links` (no empty field injected)
  - Edge case: ingesting a raw file with `links: []` produces a wiki page with `links: []` or omits it
  - Integration: the serialized `links` YAML is valid and re-parseable
- **Verification:** Ingest a test file with links, then read the wiki page and confirm the `links` field is present and structurally identical to the raw source.

### U4. Create `check_links.py` pure helper

- **Goal:** A minimal helper script that checks whether a single file path exists on disk, supporting both repo-relative and file-relative resolution.
- **Requirements:** R22
- **Dependencies:** None
- **Files:**
  - `.knap/scripts/check_links.py` — new: pure link-checking helper
- **Approach:** Expose a `check_link(link, path_to_file=None)` function. When `path_to_file` is None, resolve `link` from repo root (for frontmatter targets). When `path_to_file` is provided, resolve `link` from `path_to_file`'s parent directory (for body targets). CLI interface: `python3 check_links.py <link> [path_to_file]`. Exit 0 if the file exists, exit 1 if it does not. No frontmatter parsing, no link extraction, no file traversal, no error-vs-warning decisions — the calling script handles all orchestration. Targets starting with `http://`, `https://`, or `#` are the caller's responsibility to filter before calling.
- **Test scenarios:**
  - Happy path: `check_link("wiki/transcripts/index.md")` exits 0 (repo-relative, file exists)
  - Error path: `check_link("wiki/nonexistent.md")` exits 1 (repo-relative, file missing)
  - Happy path: `check_link("../other-page.md", "wiki/transcripts/page.md")` exits 0 (file-relative, file exists)
  - Error path: `check_link("../missing.md", "wiki/transcripts/page.md")` exits 1 (file-relative, file missing)
  - Edge case: checking a path with spaces exits correctly
- **Verification:** CLI calls with both modes produce correct exit codes.

### U5. Add link checking to lint workflow

- **Goal:** `lint.py` checks all frontmatter `links` targets and body `[text](target)` links, using `check_links.py` as a helper.
- **Requirements:** R22, KTD-3, KTD-7
- **Dependencies:** U1, U4
- **Files:**
  - `.knap/scripts/lint.py` — add link checking step
- **Approach:** Add a `check_links` step that runs last (after all other checks, per KTD-7). For each wiki page (excluding `log.md`): parse frontmatter, extract `links` field entries, call `check_link(target)` for each frontmatter target — report failures as errors. Extract body `[text](target)` links via regex, call `check_link(target, page_path)` for each body target — report failures as warnings for regular pages, errors for index files (per KTD-3). Skip `http://`, `https://`, and `#` targets. `[[target]]` links are not checked (per KTD-8). Import `check_link` from `check_links.py` as a function (not via subprocess). Add a `warnings` counter alongside `total` in `main()` — only count errors toward the exit code; warnings are informational and should not cause a non-zero exit.
- **Test scenarios:**
  - Happy path: `lint.py` passes on a wiki with no broken links
  - Integration: `lint.py` reports broken frontmatter links as errors (counted in total)
  - Integration: `lint.py` reports broken body `[text](target)` links as warnings for regular pages
  - Integration: `lint.py` reports broken body `[text](target)` links as errors for index files
  - Edge case: wiki pages with no `links` field and no body links are clean
  - Edge case: body `[[target]]` links are not checked (KTD-8 decision)
  - Edge case: external URLs and anchor links are skipped
  - Order: link checking runs after all other lint checks
- **Verification:** `python3 .knap/scripts/lint.py` includes link checking in its output, runs last, and correctly reports broken links with appropriate severity.

### U6. Create file-rename hook script

- **Goal:** When a file is renamed or moved, update all references to it across the wiki — both frontmatter `links` targets and body `[text](target)` links.
- **Requirements:** R23
- **Dependencies:** None
- **Files:**
  - `.knap/scripts/update_links_on_rename.py` — new: file-rename link updater
- **Approach:** Accept old path and new path as repo-relative arguments. Scan all `.md` files in the wiki directory. For each file: parse frontmatter and update any `links` entries whose `target` matches the old path (exact string match against repo-relative targets). Scan body for `[text](old-path)` patterns — handle both file-relative paths (e.g., `../other-page.md`, computed from each wiki page's directory to the old target) and root-relative paths (e.g., `wiki/other-page.md`). Also scan for `[[old-path]]` wiki-link patterns and replace with `[[new-path]]` (the rename hook handles both syntaxes even though the validator only checks `[]()`). Note: `log.md` is included in the rename hook even though it's excluded from link validation. Print a summary of files updated. Exit 0 on success, exit 1 on error. This is a standalone script — not integrated into the lint workflow. It's invoked manually or by a git hook when a rename is detected.
- **Test scenarios:**
  - Happy path: renaming a file updates frontmatter `links` targets in all wiki pages that reference it
  - Happy path: renaming a file updates body `[text](target)` links in all wiki pages that reference it
  - Happy path: renaming a file updates body `[[target]]` wiki-links in all wiki pages that reference it
  - Edge case: a file with no references to the renamed file is unchanged
  - Edge case: a file with multiple references to the renamed file updates all of them
  - Edge case: the renamed file itself is not modified (only other files that reference it)
- **Verification:** Rename a test file, run `update_links_on_rename.py`, confirm all references in other wiki pages are updated.

## Scope Boundaries

**In scope:**
- `links` structure definition in schema
- `links` validation in `validate.py`
- `links` passthrough in `ingest.py`
- `check_links.py` pure helper (URI → exists/not)
- Link checking orchestration in `lint.py`
- File-rename hook script

**Deferred for later:**
- Rendering links in category index files — category indexes list pages; links are page-level metadata. If graph-based index views are needed later, that's a separate feature.
- Bidirectional link detection — checking that if page A links to page B, page B links back. Deferred to a future graph feature.

**Deliberately excluded:**
- `[[target]]` wiki-link validation — not validated because users routinely pre-populate wiki-links to pages that don't exist yet. See KTD-8.

## Sources / Research

- `.knap/schema/categories.yaml` — `links` already listed as optional field
- `.knap/scripts/schema.py` — field loading infrastructure to extend
- `.knap/scripts/validate.py` — validation patterns to follow
- `.knap/scripts/ingest.py` — field passthrough patterns (lines 90-99)
- `.knap/scripts/lint.py` — check integration patterns to follow
- `docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md` — origin plan, deferred this feature
