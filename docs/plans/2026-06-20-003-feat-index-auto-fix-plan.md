---
title: 'feat: Index Auto-Fix'
type: feat
status: deferred
date: 2026-06-20
---

# Index Auto-Fix

Deferred from the Orphan Content Checker plan. lint.py is a pure diagnostic tool — it reports issues but does not fix them. This plan covers a separate script that auto-fixes index gaps.

## Problem Frame

When check_index finds pages that exist but aren't listed in their category index, the user currently has to fix them manually. An auto-fix script would handle the mechanical case: add the missing index entry so the page is properly routed.

## Requirements (TBD)

- Separate script (e.g., `fix_index.py`) — not part of lint.py
- Reads check_index output (or re-runs the same checks)
- Adds missing entries to the appropriate index file:
  - Wiki pages → category index (`wiki/{category}/index.md`)
  - System folder files → their associated index (e.g., `.knap/context/ROUTER.md`)
- Index entries are body markdown links, written directly to the index file body
- Does not handle orphan fixing — that's a separate concern
- Supports `--dry-run` to preview changes before applying

## Dependencies

- Orphan Content Checker plan (check_index module must exist)
- Folder classification config (to determine which index to update)
