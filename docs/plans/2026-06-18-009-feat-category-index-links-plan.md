---
title: 'feat: Category Index Links'
type: feat
status: deferred
date: 2026-06-18
origin: docs/plans/2026-06-18-002-feat-typed-links-plan.md
---

# Category Index Links

Deferred from the Typed Links plan. The interaction between typed links and category index files needs its own planning session.

## Problem Frame

The Typed Links plan defines a `links` field in frontmatter with typed relationships. Category index files (`wiki/{category}/index.md`) currently list pages as simple title links. How typed links should interact with category indexes is unresolved — should index files show each page's links? Should index files use typed links themselves?

## Relevant Decisions from Typed Links Plan

- Body links in index files are considered Parent/Child implicitly (the index is a parent listing its children), but do not need to be explicitly declared as such.
- Body link format (wikilinks vs markdown links) is already decided and out of scope.
- Frontmatter links use markdown link format (`[name](path)`) with repo-root-relative paths.

## Requirements (TBD)

- TBD. Requirements will be defined during the planning session.

## Open Questions

- Should category index files render the `links` field for each page they list?
- If so, which link types should be shown? All types, or a filtered subset?
- Should the master index (`wiki/index.md`) also render link information?
- How does link rendering affect index file size and readability at scale?
- Should `ingest.py` update category index files when a page's links change (not just when pages are added/removed)?

## Dependencies

- Typed Links plan must be complete (links field exists and is validated)
- Per-category indexes must exist (foundation plan U3 complete)

## Notes from Orphan Content Checker Plan

The orphan content checker plan (`docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md`) made the following decisions that affect this plan:

- **I7.** A link from within the body of an index is considered a `Child` link type for reciprocity purposes
- **I8.** Index files (`index.md`, `ROUTER.md`) are exempt from the reciprocity rule — they don't need `Child` links in their frontmatter for pages they list in their body
- **KTD-7.** The `add_frontmatter_link()` function has been updated to skip `Child` reciprocal writes to index files

These decisions establish that index body links are the canonical child listing and frontmatter Child links on indexes are not required. This plan must account for that when deciding how typed links interact with category indexes.
