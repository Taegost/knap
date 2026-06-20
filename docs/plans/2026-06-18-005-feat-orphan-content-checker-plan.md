---
title: 'feat: Orphan Content Checker'
type: feat
status: deferred
date: 2026-06-18
origin: docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md
---

# Orphan Content Checker

Extracted from the Memory System Foundation plan. The orphan checker requires non-trivial refactoring of lint.py and warrants its own planning session.

## Problem Frame

lint.py's `check_index()` currently does a flat scan of `wiki/index.md` against all wiki pages. With per-category indexes (U3 of the foundation plan), page links live in `wiki/{category}/index.md`, not the master index. The current approach will report every wiki page as "index missing" because it won't find individual page links in the master index. Beyond the structural mismatch, there's no detection for category folders with content but no corresponding index entries — files that exist but aren't routed.

## Requirements

- O1. `check_index()` refactored into a two-level check: (1) category index ↔ pages in that category directory, (2) master index ↔ existing category index files.
- O2. New orphan detection: category folders with `.md` files but no `index.md` are flagged.
- O3. Category index listing a page that doesn't exist is flagged (index ghost).
- O4. Master index missing a link to an existing category index is flagged.
- O5. Existing `check_orphans()` (broken source links) and `check_uningested()` (raw files without wiki pages) remain unchanged.

## Implementation Notes

- `check_index()` (lines 86-108): rewrite from flat scan to two-level check
- Add new function for category-folder-without-index detection
- Category indexes are created on-demand (not eagerly), so missing index.md is only an issue when the folder has content
- The existing `check_orphans()` and `check_uningested()` are separate concerns

## Dependencies

- Per-category indexes must exist (foundation plan U3 complete)

## Open Questions

- Should the checker also validate that the master index doesn't link to category indexes for empty categories (ghost category links)?
- How should the checker handle symlinks or special files in wiki directories?
