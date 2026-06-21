---
title: 'feat: Category Index Links'
type: feat
status: completed
date: 2026-06-18
origin: docs/plans/Completed/2026-06-18-002-feat-typed-links-plan.md
---

# Category Index Links

Deferred from the Typed Links plan. The interaction between typed links and category index files needs its own planning session.

## Problem Frame

The Typed Links plan defines a `links` field in frontmatter with typed relationships. Category index files (`wiki/{category}/index.md`) currently list pages as simple title links in their body. `ingest.py` creates wiki pages with `IngestedFrom` links but does not create `Parent` links pointing to the category index. `add_frontmatter_link()` skips Child reciprocals to index files entirely (line 93-94), meaning when someone adds a `Parent` link to a wiki page pointing at an index, the index never learns about the page. Index files also lack frontmatter — no `Parent` link to their parent index, no description field.

The index hierarchy is: `.knap/ROUTER.md` (root) → `wiki/index.md` (master wiki index) → `wiki/{category}/index.md` (category indexes). ROUTER.md is an index for all intents and purposes. Nested indices are possible — the hierarchy is not limited to three levels.

---

## Requirements

### Index Behavior

- R1. Category index body links remain simple title links (`[Title](filename.md)`). No typed link metadata is rendered in indexes.
- R2. Index files have frontmatter: a `Parent` link to their parent index and a `description` field. The Parent target follows the actual index hierarchy: category indexes → `wiki/index.md`, master index → `.knap/ROUTER.md`, `.knap/ROUTER.md` has no parent (it's the root). Nested indices follow the same pattern — each index's Parent points to the index that contains it.
- R3. The only index deviation from the "all system-related links are in frontmatter" rule is that Child links live in the body, not the frontmatter.

### Parent Link Generation

- R4. `ingest.py` adds a `Parent` link to wiki page frontmatter pointing to the category index during page creation.
- R5. The `Parent` link target uses repo-root-relative path format: `[index](wiki/{category}/index.md)`.

### Index Update via Shared Link Module

- R6. When `add_frontmatter_link()` adds a `Parent` link to a page where the target is an index file, it adds the page to the index body as a title link instead of skipping the reciprocal. This is the sole mechanism for keeping indexes in sync with Parent link changes.
- R7. All link creation flows through `add_frontmatter_link()`. No script writes to the `links` field or index body directly.

### Auto-Fix for Missing Parent Links

- R8. `check_index.py` auto-fixes wiki pages that are missing `Parent` links by calling `add_frontmatter_link()` to add them. This replaces a separate migration script for missing Parent links — the existing check logic detects the gap and the shared link module fixes it. Index frontmatter migration (adding Parent and description to index files themselves) is handled by U3.

### Auto-Fix for Unlisted Pages

- R9. A module for auto-fixing unlisted pages (pages with a Parent link pointing to an index but not listed in that index) is created in this plan. Integration of `fix_index.py` into the lint workflow (calling it from `lint.py`) is deferred to `docs/plans/2026-06-20-003-feat-index-auto-fix-plan.md`.

---

## Key Technical Decisions

### KTD-1. Index reciprocity in add_frontmatter_link()

When `add_frontmatter_link()` adds a `Parent` link where the target is an index file (`index.md` or `.knap/ROUTER.md`), instead of skipping the Child reciprocal (current behavior), it adds the source page to the index body as a title link. The body entry format is the same for all index types — `- [{title}]({relative_path})` — with only the target index file path varying.

**Rationale:** The current code (line 93-94) skips Child reciprocals to index files entirely. This means adding a `Parent` link to a page never updates the index. The fix is to extend the existing reciprocal logic in `add_frontmatter_link()` to write to the index body instead of skipping. No new helper module — the existing function handles it. `ingest.py` calls `add_frontmatter_link()` to add the `Parent` link after page creation, triggering the index body update automatically.

### KTD-2. Auto-fix via existing check + link modules

`check_index.py`'s `_check_parent_links()` already detects missing Parent links. Instead of a separate migration script, the calling function uses the detection results to call `add_frontmatter_link()` and fix the gap. The shared module handles the link write AND the index body update (via KTD-1). `_check_parent_links()` stays pure diagnostic per the single-use principle.

**Rationale:** The detection logic exists. The fix logic exists in `add_frontmatter_link()`. Wiring them together at the caller level is the minimal change. No new script needed.

### KTD-3. Index frontmatter structure

Index files get frontmatter with a `Parent` link to their parent index and a `description` field. The Parent target follows the actual index hierarchy: category indexes → `wiki/index.md`, master index → `.knap/ROUTER.md`. `.knap/ROUTER.md` has no parent — it's the root index. Nested indices are possible; each index's Parent points to whatever index contains it. Child links remain in the body — this is the sole exception to frontmatter-based links.

**Rationale:** Indexes are wiki pages too. They need `Parent` links for the orphan checker and link validation to work correctly. The `description` field provides context about what the index contains. ROUTER.md is treated as an index, not a special case.

---

## Implementation Units

### U1. Update add_frontmatter_link() for index reciprocity

**Goal:** When adding a `Parent` link to a page where the target is an index file, add the page to the index body instead of skipping the reciprocal.

**Requirements:** R6, R7

**Dependencies:** None

**Files:**
- `.knap/scripts/add_frontmatter_link.py` — modify reciprocal logic (lines 82-103)
- `.knap/scripts/test_add_frontmatter_link.py` — add index reciprocity tests

**Approach:** In `add_frontmatter_link()`, replace the early return on line 93-94 (`if reciprocal_type == "Child" and target_name in ("index.md", "ROUTER.md"): return`) with logic that adds the source page to the index body as a title link. Extract the title from the source file's frontmatter (or use filename stem as fallback). Compute the relative path from the index directory to the source page. Check for duplicates before appending. The index type doesn't matter — only the file path and the relative path computation. This extends the existing reciprocal logic; no new helper module needed. `ingest.py`'s `ingest()` function calls `add_frontmatter_link()` after creating the wiki page to add the `Parent` link, which triggers the index body update automatically.

**Test scenarios:**
- Adding `Parent` link to wiki page where target is category `index.md` → page added to index body
- Adding `Parent` link to wiki page where target is `wiki/index.md` (master index) → page added to master index body
- Adding `Parent` link to wiki page where target is `.knap/ROUTER.md` → page added to ROUTER.md body
- Adding `Parent` link to non-index file → standard reciprocal Child link written (existing behavior)
- Adding `Related` link to index file → standard reciprocal written (only Child triggers body update)
- Page already listed in index → no duplicate entry
- Index entry uses page title from frontmatter when available
- Index entry falls back to filename stem when title missing

**Verification:** `pytest .knap/scripts/test_add_frontmatter_link.py` passes. Manually add a `Parent` link to a wiki page pointing at its category index, verify the page appears in the index body.

### U2. Auto-fix missing Parent links via check_index.py caller

**Goal:** `check_index.py`'s main function (or `lint.py`) calls `add_frontmatter_link()` to fix pages that `_check_parent_links()` reports as missing `Parent` links.

**Requirements:** R8

**Dependencies:** U1

**Files:**
- `.knap/scripts/check_index.py` — add auto-fix logic in the calling function (not in `_check_parent_links()`)
- `.knap/scripts/test_check_index.py` — add auto-fix test scenarios

**Approach:** `_check_parent_links()` remains a pure diagnostic — it returns a list of issues. The calling function in `check_index.py` (or `lint.py`) iterates the missing Parent link issues, computes the category index path (`wiki/{category}/index.md`), builds the Parent link string (`[index](wiki/{category}/index.md)`), and calls `add_frontmatter_link()` to add it. The shared module handles both the frontmatter write and the index body update (via KTD-1). Return both the original issue and a "fixed" message so `lint.py` can report the auto-fix.

**Test scenarios:**
- `_check_parent_links()` returns missing Parent link issues (existing behavior, unchanged)
- Calling function calls `add_frontmatter_link()` for each missing Parent link
- Auto-fix adds page to index body (via U1's index reciprocity)
- `index.md` and `ROUTER.md` files are skipped by `_check_parent_links()` (existing behavior)
- Auto-fix output is distinguishable from issue output

**Verification:** `pytest .knap/scripts/test_check_index.py` passes. Remove a `Parent` link from a wiki page, run `check_index.py`, verify it's re-added and the page stays in the index.

### U3. Add frontmatter to index files

**Goal:** Index files get frontmatter with a `Parent` link and `description` field.

**Requirements:** R2, R3

**Dependencies:** U1

**Files:**
- `.knap/scripts/ingest.py` — modify `_update_category_index()` to include frontmatter in new index template
- `.knap/scripts/migrate_index_frontmatter.py` — new: add frontmatter to existing index files
- `.knap/scripts/test_migrate_index_frontmatter.py` — new: unit tests
- `.knap/scripts/test_ingest_index.py` — new: tests for index frontmatter creation

**Approach:** In `_update_category_index()`, when creating a new index file (lines 157-159), include frontmatter with `Parent` link to `wiki/index.md` and a `description` field. Create a migration script that adds frontmatter to existing index files that lack it. The migration scans `wiki/*/index.md`, `wiki/index.md`, and `.knap/ROUTER.md`, adds frontmatter if missing. Category indexes get `Parent` → `[index](wiki/index.md)`. Master index (`wiki/index.md`) gets `Parent` → `[router](.knap/ROUTER.md)`. ROUTER.md has no parent (it's the root). Support `--dry-run`.

**Test scenarios:**
- New index created by `_update_category_index()` has frontmatter with `Parent` and `description`
- Existing index without frontmatter gets frontmatter added by migration
- Existing index with frontmatter is skipped by migration
- `--dry-run` shows changes without writing
- Category index gets `Parent` → `wiki/index.md`
- Master index gets `Parent` → `.knap/ROUTER.md`
- ROUTER.md has no `Parent` link (root)
- `description` field is populated with sensible default

**Verification:** `pytest .knap/scripts/test_migrate_index_frontmatter.py` passes. Run migration, verify all index files have frontmatter.

### U4. Create auto-fix module for unlisted pages

**Goal:** A module that detects pages with `Parent` links pointing to an index but not listed in that index, and adds them.

**Requirements:** R9

**Dependencies:** U1

**Files:**
- `.knap/scripts/fix_index.py` — new: auto-fix module for unlisted pages
- `.knap/scripts/test_fix_index.py` — new: unit tests

**Approach:** Export `fix_index() -> list[str]` that scans all wiki pages, extracts `Parent` link targets, checks whether each page is listed in its target index, and calls `add_frontmatter_link()` to add the page to the index body (which triggers the index body update via U1's reciprocity logic). Returns a list of fixes applied. This is the module that `docs/plans/2026-06-20-003-feat-index-auto-fix-plan.md` will integrate into `lint.py`.

**Test scenarios:**
- Page with `Parent` link to index but not listed → added to index body
- Page with `Parent` link to index and already listed → no action
- Page with `Parent` link to non-index file → skipped
- Multiple unlisted pages → all added
- Empty wiki → no fixes

**Verification:** `pytest .knap/scripts/test_fix_index.py` passes. Create a wiki page with a `Parent` link manually (without ingesting), run `fix_index.py`, verify it appears in the index.

### U5. Update tests and documentation

**Goal:** Reflect index frontmatter, Parent link convention, and auto-fix behavior in conventions.md and existing tests.

**Requirements:** R1, R4, R5

**Dependencies:** U1, U2, U3, U4

**Files:**
- `.knap/context/conventions.md` — document index frontmatter, Parent link convention
- `.knap/scripts/test_check_index.py` — verify existing tests pass with new behavior
- `.knap/scripts/test_ingest_links.py` — verify existing tests pass with new behavior

**Approach:** In conventions.md, add notes that: (1) every wiki page has a `Parent` link to its category index, (2) index files have frontmatter with `Parent` and `description`, (3) Child links on indexes live in the body. Verify all existing tests still pass after U1-U4 changes. New test creation is covered by U1-U4 individually.

**Test expectation:** none — documentation updates and existing test verification only. New tests are in U1-U4.

**Verification:** `conventions.md` documents the new conventions. `pytest .knap/scripts/` passes.

---

## Scope Boundaries

**In scope:**
- Index reciprocity in `add_frontmatter_link()` (Parent link → index body update)
- Auto-fix for missing Parent links in `check_index.py`
- Index frontmatter (Parent link, description)
- Auto-fix module for unlisted pages (`fix_index.py`)
- Tests and documentation

**Deferred to follow-up work:**
- Integration of `fix_index.py` into the lint workflow — `docs/plans/2026-06-20-003-feat-index-auto-fix-plan.md`

**Outside this scope:**
- Typed link metadata in index body links (indexes stay as simple title links)
- Re-rendering index entries when a page's non-Parent links change
- Changes to orphan checker behavior (index body links already count as incoming links)
- Nested index support beyond one level — each index applies to its directly relevant files only. When nested indices are created, the same patterns apply at that level.

---

## Dependencies

- Typed Links plan complete (`links` field, `add_frontmatter_link()`, `LINK_TYPES`) — verified, status: completed
- Orphan Content Checker plan complete (`check_index.py` extraction, index reciprocity exceptions) — verified, status: completed
- Per-category indexes exist — verified

---

## Open Questions

_(No open questions — all resolved by user decisions.)_
