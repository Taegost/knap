---
title: "feat: Typed Links"
type: feat
status: deferred
date: 2026-06-18
origin: docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md
---

# Typed Links

Deferred from the Memory System Foundation plan. The links feature was discovered to have potential conflicts with the index file guidance and needs its own planning session.

## Key Decisions

**Optional typed links in frontmatter.** Frontmatter can include a `links` list with typed relationships:

```yaml
links:
  - target: wiki/other-page.md
    type: Related
  - target: wiki/another.md          # type is optional — untyped link
```

Body markdown links are also valid. Frontmatter links are for structured, machine-readable relationships. Body links are for narrative cross-references.

**Links rendering.** Frontmatter `links` field is canonical links to other wiki pages + AI/system use (rendered in wiki page frontmatter). Body markdown links are supporting examples and human use (stay in body).

## Requirements (deferred)

- R21. Frontmatter `links` field with typed relationships is supported by schema, validated, and rendered in wiki output. The `type` field on each link is optional.
- R22. Link validation: frontmatter link targets are verified (errors on broken links). Body markdown link targets are verified (warnings only, informational).

## Implementation Notes

- `schema.py`: add `links` field structure definition
- `validate.py`: validate `links` structure if present
- `ingest.py`: include `links` field in wiki page frontmatter when present
- `check_links.py`: new script — general-purpose link validator. Accepts a markdown file path, extracts all links (frontmatter `links` field + body markdown links), verifies each target exists relative to the file. Frontmatter link failures are errors (exit 1). Body link failures are informational warnings only (exit 0). Callers (lint.py, check_index()) handle aggregation and reporting.

## Open Questions

- Should links be rendered in the category index files?
- How do links interact with the per-category index structure?
- Should `check_links.py` validate relative paths, absolute paths, or both?
