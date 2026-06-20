---
title: 'feat: Typed Links'
type: feat
status: completed
date: 2026-06-18
origin: docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md
---

# Typed Links

## Summary

Add typed links to wiki page frontmatter — a `links` list with `target` (markdown link format: `[name](path)`) and optional `type` (predefined set, defaults to `Related`). Replace the hardcoded `source` field with `IngestedFrom` or `SynthesizedFrom` links. Add `check_links` as a helper module for link validation, `add_frontmatter_link` as the sole entry point for writing frontmatter links, and integrate link validation into `lint.py`.

## Problem Frame

The current system has two cross-reference mechanisms that overlap: a hardcoded `source` field in wiki frontmatter (a markdown link pointing to the raw file it was ingested from) and body markdown links (narrative cross-references). Neither supports typed relationships. The `source` field is inflexible — it only tracks ingestion provenance and can't express richer relationships like "supersedes" or "synthesized from." The `links` field was declared as an optional field in `categories.yaml` during the Memory System Foundation work but deferred to this plan for implementation.

---

## Key Decisions

**Predefined link types.** Nine types with bidirectional pairs:

- `Related` (default when type is blank/missing)
- `Parent` / `Child` — hierarchical relationships
- `Supersedes` / `SupersededBy` — version/replacement tracking
- `IngestedFrom` / `IngestedTo` — raw-to-wiki ingestion provenance
- `SynthesizedFrom` / `SynthesizedTo` — synthesis provenance

Types are extensible per-repo. `LINK_TYPES` in `schema.py` defines the valid set. Additional domain-specific types can be added to `categories.yaml` and will be loaded into `LINK_TYPES` at runtime.

**Links field structure.** Frontmatter `links` is a list of `{target, type}` objects. `target` is a markdown link (`[name](path)`) where the path is repo-root-relative for file paths, or a full URI for external resources. `type` is optional — missing or blank defaults to `Related`.

```yaml
links:
  - target: "[Other Page](wiki/other-page.md)"
    type: Related
  - target: "[Another Page](wiki/another.md)"  # type defaults to Related
  - target: "[Example](https://example.com)"    # external URI
  - target: "[Paper](raw/research/some-paper.pdf)"  # any file in repo
```

The markdown link format in `target` allows markdown IDEs (VS Code, Obsidian) to traverse the link structure natively.

**Frontmatter links use markdown link format.** All frontmatter link targets are `[name](path)` strings. This is a deliberate format decision, not a configurable option. Body markdown links follow standard markdown conventions and can use either wikilinks or standard markdown links, relative to the file or repo root — body link format is out of scope for this plan and already decided (see conventions.md).

**Replace `source` with `IngestedFrom` or `SynthesizedFrom`.** The current `source` frontmatter field in wiki pages (a markdown link back to the raw file) is replaced by an `IngestedFrom` or `SynthesizedFrom` entry in the `links` field. `IngestedFrom` is used when the wiki page was created by `ingest.py`. `SynthesizedFrom` is used when the wiki page was created by the synthesize skill. Existing `source` fields are migrated to `IngestedFrom` by the migration script.

**Frontmatter links are repo-root-relative.** Body markdown links can be either repo-root-relative or file-relative — both are valid. Frontmatter `links` targets are always resolved from repo root.

**Frontmatter link failures are errors; body link failures are warnings.** Matches R22 from the origin document. Frontmatter links are structured and intentional — a broken one is a real problem. Body markdown links are narrative — a broken one is informational.

**Single entry point for frontmatter link writes.** All scripts that add frontmatter links must use `add_frontmatter_link()`. This function handles deduplication, type updates, and reciprocal link generation. No script should write to the `links` field directly.

**Serialization follows established patterns.** Frontmatter serialization uses the patterns defined in the markdown-first converter plan (`2026-06-19-001-feat-markdown-first-converter-plan.md` R2 and R3). These requirements are documented in conventions.md and must be referenced whenever frontmatter is written.

---

## Requirements

- R21. Frontmatter `links` field with typed relationships is supported by schema, validated, and rendered in wiki output. The `type` field on each link is optional.
- R22. Link validation: frontmatter link targets are verified — internal file paths error on broken links, external URLs warn on broken links. Body markdown link targets are verified (warnings only, informational).
- R23. `source` frontmatter field is replaced by `IngestedFrom` or `SynthesizedFrom` link. Existing wiki pages are migrated. `ingest.py` generates `IngestedFrom` links instead of `source`.
- R24. `check_links` is a helper module with two functions for link validation (per strategy doc principle: "A link validator validates links. A linter orchestrates checks.").
- R25. `add_frontmatter_link` is the sole entry point for writing frontmatter links. It handles deduplication, type updates, and reciprocal link generation.
- R26. Frontmatter serialization follows the patterns in `2026-06-19-001-feat-markdown-first-converter-plan.md` R2 and R3, documented in conventions.md.

---

## Implementation Units

### U1. Define link structure in schema.py

**Goal:** Export link type constants and structure definition so other scripts can import them.

**Requirements:** R21

**Dependencies:** None

**Files:**
- `.knap/scripts/schema.py` — add `LINK_TYPES` constant and `LINK_TYPE_PAIRS` reverse mapping

**Approach:** Add a `LINK_TYPES` list and `LINK_TYPE_PAIRS` dict. `Related` is the default (used when type is missing/blank). The pairs dict maps each type to its reverse (e.g., `IngestedFrom` → `IngestedTo`). Load additional types from `categories.yaml` if a `link_types` key exists, allowing per-repo extension. Update `reload()` to include `LINK_TYPES` and `LINK_TYPE_PAIRS`.

**Test scenarios:**
- `LINK_TYPES` contains all 9 base types
- `LINK_TYPE_PAIRS` has correct bidirectional mappings
- Importing `LINK_TYPES` and `LINK_TYPE_PAIRS` from schema.py works
- Additional types from `categories.yaml` are loaded when present

**Verification:** `python3 -c "from schema import LINK_TYPES, LINK_TYPE_PAIRS; print(LINK_TYPES)"` prints the 9 types.

### U2. Validate links structure in validate.py

**Goal:** Validate the `links` field structure when present in raw file frontmatter.

**Requirements:** R21

**Dependencies:** U1

**Files:**
- `.knap/scripts/validate.py` — add links structure validation

**Approach:** In `validate_file()`, if `links` is present, validate: (1) it's a list, (2) each entry is a dict, (3) each entry has a `target` key with a string value, (4) if `type` is present, it's a valid type from `LINK_TYPES`. Missing `type` or blank `type` is not an error (defaults to `Related`). Unknown `type` values are errors. Import `LINK_TYPES` from schema.py. Per R26, use the established serialization patterns when writing frontmatter.

**Test scenarios:**
- Valid links (with type) passes validation
- Valid links (without type) passes validation
- Valid links (blank type) passes validation
- Invalid type value produces error
- Missing `target` key produces error
- Non-string `target` produces error
- `links` is not a list produces error
- Empty `links` list passes validation
- No `links` field passes validation (it's optional)

**Verification:** `python3 .knap/scripts/validate.py` passes on files with valid links.

### U3. Generate IngestedFrom links in ingest.py

**Goal:** `build_wiki_page()` copies the `links` field to wiki frontmatter and adds an `IngestedFrom` link pointing to the raw source file. Remove `source` field generation.

**Requirements:** R21, R23, R26

**Dependencies:** U1

**Files:**
- `.knap/scripts/ingest.py` — update `build_wiki_page()` to handle `links` field, remove `source` generation

**Approach:** Refactor `build_wiki_page()` to build the wiki frontmatter as a dict and serialize with `yaml.dump(wiki_fm, default_flow_style=False, sort_keys=False)` — replacing the current manual string formatting loop (lines 101-112) which produces Python repr for dict objects. After building the dict: (1) copy `links` from raw frontmatter if present, (2) prepend an `IngestedFrom` entry with `target` as a markdown link using repo-root-relative path: `[raw filename](raw_path)` where `raw_path` is repo-root-relative (e.g., `raw/transcripts/file.md`, not `../raw/transcripts/file.md`). Remove the `source` field generation entirely (line 87-88). Per R26, use the established serialization patterns from the markdown-first converter plan — this matches the pattern in `convert_frontmatter.py`'s `serialize_frontmatter()`.

**Test scenarios:**
- Wiki page with `links` in raw frontmatter includes `links` in wiki frontmatter
- Wiki page without `links` in raw frontmatter has `IngestedFrom` link only
- `IngestedFrom` target is a markdown link pointing to the correct raw file
- `links` entries are serialized correctly (not as raw strings)
- Wiki page no longer has `source` field

**Verification:** Ingest a test file and verify the wiki page frontmatter contains `links` with `IngestedFrom` and no `source` field.

### U4. Create check_links helper

**Goal:** A helper module with two functions that validate whether a link target exists.

**Requirements:** R24

**Dependencies:** U1

**Files:**
- `.knap/scripts/check_links.py` — new helper module

**Approach:** One function with two modes via optional parameter:

- `check_link(link, relative_to=None)` — Extracts the URL from the markdown link format `[name](url)` before resolving. If the link is not in markdown link format, treat the entire string as the path/URI. When `relative_to` is `None` (default), resolve the path repo-root-relative. When `relative_to` is provided (a file path), resolve relative to that file's directory. Returns a result object with `exists` (bool) and `is_external` (bool) — callers use `is_external` to decide severity (errors for internal, warnings for external). For absolute URIs (http://, https://, smb://, etc.), attempt validation and set `is_external=True`.

**Test scenarios:**
- `check_link("[Page](wiki/transcripts/foo.md)")` returns exists=True, is_external=False
- `check_link("[Page](wiki/nonexistent.md)")` returns exists=False, is_external=False
- `check_link("[Site](https://example.com)")` returns exists=True, is_external=False (or exists=False if unreachable)
- `check_link("[Page](foo.md)", "wiki/transcripts/bar.md")` resolves relative to `wiki/transcripts/`
- `check_link("[Page](../other.md)", "wiki/transcripts/bar.md")` resolves correctly

**Verification:** Import and call against known files.

### U5. Create add_frontmatter_link script

**Goal:** The sole entry point for adding frontmatter links to files. Handles deduplication, type updates, and reciprocal link generation.

**Requirements:** R25, R26

**Dependencies:** U1, U4

**Files:**
- `.knap/scripts/add_frontmatter_link.py` — new script

**Approach:** Two functions:

- `_write_frontmatter_link(file, link, type)` — Private. Performs the actual frontmatter check and write/update logic: parse frontmatter, check if `link` already exists in `links` (match on `target`), if it exists and type matches skip, if it exists and type differs update the type, if it doesn't exist append to end. Per R26, use the established serialization patterns.
- `add_frontmatter_link(file, link, type)` — Public entry point. Calls `_write_frontmatter_link` for the primary link. Then, if the link points to a markdown file inside the repo AND the type has a reciprocal (e.g., Parent→Child, IngestedFrom→IngestedTo), calls `_write_frontmatter_link` again with the target file, the source file as the link, and the reciprocal type. Uses `check_link()` from U4 to verify the target exists before writing.

Import `LINK_TYPE_PAIRS` from schema.py for reciprocal lookups. Import `check_link` from check_links.py for existence checks.

**CLI:** `python3 .knap/scripts/add_frontmatter_link.py <file> "<link>" [type]`

**Test scenarios:**
- Adding a new link to a file with no existing links
- Adding a link that already exists (same type) — skips
- Adding a link that already exists (different type) — updates type
- Adding a link with a reciprocal type — writes to both files
- Adding a link to a non-markdown target — no reciprocal
- Invalid type produces error
- Link target doesn't exist — produces error

**Verification:** Run against a test file and verify frontmatter is updated correctly.

### U6. Migrate source fields to IngestedFrom links

**Goal:** Extend the existing `convert_frontmatter.py` migration script to convert `source` frontmatter fields to `IngestedFrom` links. Run against all markdown files in the repo.

**Requirements:** R23, R25, R26

**Dependencies:** U3, U5

**Files:**
- `.knap/scripts/convert_frontmatter.py` — extend with source-to-IngestedFrom migration logic

**Approach:** Extend the existing idempotent migration script with a new pass that: (1) finds all `.md` files in the repo (excluding `.claude/`), (2) for each file with a `source` field, extracts the raw path from the markdown link and converts to repo-root-relative (`[name](../raw/...)` → `raw/...` by stripping the `../` prefix), (3) calls `add_frontmatter_link()` to add the `IngestedFrom` link with repo-root-relative path (which handles deduplication and reciprocals), (4) removes the `source` field. If the `source` field has unexpected format, error and skip (don't corrupt data). Verify the link exists before appending — if it doesn't exist, append anyway (broken links are caught by lint.py). Support `--dry-run` to preview changes before applying.

**Execution order:** Run `--dry-run` first, review output, then run without `--dry-run` to apply. This is the last step of U6 — the migration runs against the live repo.

**Test scenarios:**
- File with `source` field converts to `IngestedFrom` link
- File with existing `links` field appends `IngestedFrom` (no overwrite)
- File with no `source` field is skipped
- `--dry-run` shows changes without writing
- Body content is preserved (only frontmatter changes)
- File with malformed `source` field logs error and skips
- Reciprocal `IngestedTo` link is written to the raw file
- Running twice produces no changes (idempotent)

**Verification:** Run migration, then verify all wiki pages have `IngestedFrom` links and no `source` fields. `lint.py` passes clean.

### U7. Integrate link validation into lint.py

**Goal:** Replace source-link checking with general-purpose link validation in lint.py.

**Requirements:** R22, R24

**Dependencies:** U4, U6

**Files:**
- `.knap/scripts/lint.py` — replace `extract_source_link()` and source-based checks with link validation

**Approach:** Remove `extract_source_link()` function entirely. Remove `check_orphans()` function — orphan checking is being re-designed in `docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md` and will use `IngestedFrom` links instead of the removed `source` field. Add a new `check_links()` function that: (1) iterates all markdown files (excluding `.claude/`), (2) for each file, extracts all links from frontmatter `links` field AND body markdown links, (3) passes each link to `check_link()` from U4, (4) frontmatter internal file link failures are errors, frontmatter external URL failures are warnings, body link failures are warnings. Import `check_link` from check_links.py rather than shelling out — per the strategy doc's "composed scripts call smaller ones" principle.

**Test scenarios:**
- Wiki page with valid `IngestedFrom` link passes
- Wiki page with broken frontmatter link fails (error)
- Wiki page with broken body link reports warning
- `lint.py` reports link validation issues alongside existing checks
- Files in `.claude/` are excluded from link validation

**Verification:** `python3 .knap/scripts/lint.py` passes with the new link checking.

### U8. Update documentation

**Goal:** Update conventions.md and decisions.md to reflect typed links, serialization patterns, and the deprecation of `source`.

**Requirements:** R23, R26

**Dependencies:** U6, U7

**Files:**
- `.knap/context/conventions.md` — add link types, update cross-references section, add serialization reference
- `.knap/context/decisions.md` — add typed links decision, update cross-reference format entry

**Approach:** In `conventions.md`, add a "Frontmatter Links" section documenting the `links` field structure, valid link types, markdown link format for targets, and the `add_frontmatter_link` entry point. Add a "Serialization" section referencing the markdown-first converter plan's R2 and R3 requirements. Update the "Cross-References" section to note that frontmatter links use repo-root-relative paths while body links can use either format. In `decisions.md`, add a "Typed Links" decision recording the link type set, the `source` → `IngestedFrom`/`SynthesizedFrom` migration, and the single-entry-point pattern. Update the "Cross-Reference Format" decision to note the frontmatter vs body distinction.

**Test scenarios:**
- conventions.md documents link types and serialization patterns
- decisions.md records typed links decision

**Verification:** Documentation is accurate and references the correct files.

---

## Scope Boundaries

**In scope:**
- Link type constants and structure in schema.py
- Links validation in validate.py
- Links handling in ingest.py (IngestedFrom generation, links field copy, source removal)
- check_links helper module
- add_frontmatter_link script (sole entry point for link writes)
- Migration of `source` fields to `IngestedFrom` links
- lint.py link validation integration
- Documentation updates (conventions.md, decisions.md)

**Deferred to follow-up work:**
- Orphan page checking — currently in lint.py's `check_orphans()`, deferred to `docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md`. The `source` field removal means orphan checking needs a new approach (checking `IngestedFrom` links). That plan's dependency section has been updated to note this.
- Category index link rendering — deferred to a separate plan. Track as `docs/plans/2026-06-18-009-feat-category-index-links-plan.md`. See Open Questions for relevant details.
- `SynthesizedTo` / `IngestedTo` on raw files — raw files are immutable except for frontmatter metadata. Reciprocal links on raw files are desired and handled by `add_frontmatter_link` automatically when the target is a markdown file in the repo.

**Outside this scope:**
- Body link format — already decided (wikilinks and markdown links both valid, relative and root paths both valid). Not deferred; this is settled and documented in conventions.md.
- Changes to the `source_url` required field on raw files (different from the `source` wiki field being removed)
- OKF format alignment for links (OKF doesn't define typed links)

---

## Open Questions

_(No open questions — all resolved.)_
