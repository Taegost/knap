---
title: 'chore: Backport Frontmatter Parser'
type: chore
status: deferred
date: 2026-06-20
---

# Backport Frontmatter Parser

Deferred from the Orphan Content Checker plan. The shared frontmatter parsing module (`parse_frontmatter.py`) created in that plan needs to be backported to the remaining scripts that have inline parsing.

## Problem Frame

Frontmatter parsing is duplicated across 5 scripts with inconsistent return types. The Orphan Content Checker plan creates `parse_frontmatter.py` as a shared module and uses it in the scripts it touches. The remaining scripts still have inline parsing.

## Scripts to Update

- `.knap/scripts/ingest.py` — has inline `parse_frontmatter()` returning `tuple[dict | None, str | None]`
- `.knap/scripts/validate.py` — has inline `parse_frontmatter()` returning `dict | None`
- `.knap/scripts/convert_frontmatter.py` — has inline frontmatter parsing
- `.knap/scripts/plan_lint.py` — has inline frontmatter parsing

## Requirements (TBD)

- Replace inline parsing with import from `parse_frontmatter.py`
- Ensure return type compatibility or add adapter functions
- Update tests to use shared module
- Verify no behavioral changes

## Dependencies

- Orphan Content Checker plan U1 (parse_frontmatter.py creation)
