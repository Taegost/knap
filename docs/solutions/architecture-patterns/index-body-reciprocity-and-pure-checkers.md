---
title: "Index Body Reciprocity and Pure Diagnostic Checkers"
date: 2026-06-21
last_updated: 2026-06-21
category: docs/solutions/architecture-patterns
module: knap/scripts
problem_type: architecture_pattern
component: tooling
severity: medium
applies_when:
  - "Designing reciprocal link systems where some targets use body content instead of frontmatter"
  - "Keeping diagnostic functions pure while enabling auto-fix at the caller level"
  - "Modeling index hierarchies where each index has a Parent and lists Children in its body"
tags:
  - typed-links
  - index-reciprocity
  - pure-functions
  - auto-fix
  - frontmatter-links
  - index-hierarchy
---

# Index Body Reciprocity and Pure Diagnostic Checkers

## Context

When typed links were added to the knap system, `add_frontmatter_link()` handled reciprocal link generation for all link pairs. Index files (`index.md`, `ROUTER.md`) were exempted from Child reciprocals entirely (lines 93-94) because indexes list children in their body, not frontmatter. This created a gap: adding a `Parent` link to a wiki page never updated the index body, so indexes drifted out of sync.

Separately, `check_index.py`'s `_check_parent_links()` detected pages missing `Parent` links but had no mechanism to fix them. The temptation was to add auto-fix logic directly inside the checker, which would violate the single-use principle (a checker should check, not mutate).

The solution required two complementary patterns: extending the reciprocal logic to write to index bodies instead of skipping, and wiring auto-fix at the caller level so diagnostic functions stay pure.

## Guidance

### 1. Replace skip-on-index with write-to-index-body in reciprocal logic

When `add_frontmatter_link()` encounters an index file as a reciprocal target, instead of returning early, write the source page as a title link in the index body. The index type does not matter -- only the file path and the relative path computation.

```python
# Before (current code at lines 90-94):
target_name = target_full.name
if reciprocal_type == "Child" and target_name in ("index.md", "ROUTER.md"):
    return  # skip entirely -- index never learns about the page

# After:
target_name = target_full.name
if reciprocal_type == "Child" and target_name in ("index.md", "ROUTER.md"):
    _add_to_index_body(str(target_full), filepath)
    return
```

The `_add_to_index_body()` helper:
1. Reads the index file and extracts the title from the source file's frontmatter (or uses filename stem as fallback).
2. Computes the relative path from the index directory to the source page.
3. Checks for duplicates before appending.
4. Appends `- [{title}]({relative_path})` to the index body.

This is the sole mechanism for keeping indexes in sync with Parent link changes. No separate sync script. No direct writes to index bodies from other modules. Everything flows through `add_frontmatter_link()`.

### 2. Keep diagnostic functions pure -- fix at the caller level

A diagnostic function returns issues. It does not mutate state. This is non-negotiable because:
- Diagnostic functions run in `lint.py` which may be run in `--dry-run` mode.
- Mixing detection and mutation makes functions unpredictable and untestable.
- The caller (lint orchestrator or a dedicated fix script) decides whether to act on the issues.

```python
# check_index.py -- stays pure diagnostic
def _check_parent_links() -> list[str]:
    """Check that files in indexed categories have a Parent link.
    Returns list of issue strings. Does NOT fix anything."""
    issues: list[str] = []
    # ... detection logic ...
    if not has_parent:
        issues.append(f"missing Parent link: {rel}")
    return issues

# Caller level (lint.py or a fix script) -- decides whether to fix
def auto_fix_missing_parents(issues: list[str]) -> list[str]:
    """Fix missing Parent links by calling add_frontmatter_link()."""
    fixes = []
    for issue in issues:
        if not issue.startswith("missing Parent link: "):
            continue
        page_path = issue.removeprefix("missing Parent link: ")
        category = Path(page_path).parent.name
        parent_link = f"[index](wiki/{category}/index.md)"
        add_frontmatter_link(page_path, parent_link, "Parent")
        fixes.append(f"fixed: {page_path}")
    return fixes
```

The shared link module handles both the frontmatter write and the index body update (via the extended reciprocal logic). The caller just wires detection to action.

### 3. Index hierarchy follows actual containment, not hardcoded rules

The index hierarchy is: `.knap/ROUTER.md` (root) -> `wiki/index.md` (master) -> `wiki/{category}/index.md` (category). Each index's `Parent` link points to the index that contains it:

```yaml
# wiki/kubernetes/index.md frontmatter
---
links:
  - target: "[index](wiki/index.md)"
    type: Parent
description: "Kubernetes content"
---

# wiki/index.md frontmatter
---
links:
  - target: "[router](.knap/ROUTER.md)"
    type: Parent
description: "Master wiki index"
---

# .knap/ROUTER.md -- root, no Parent
---
description: "System router"
---
```

Do not hardcode that all indexes point to ROUTER.md. The hierarchy follows containment. Nested indices follow the same pattern -- each index's Parent points to whatever index contains it.

### 4. Index files have frontmatter with one exception

Index files get frontmatter like any other wiki page: `Parent` link, `description` field. The only deviation from "all system-related links are in frontmatter" is that Child links live in the body as simple title links (`- [{title}]({path})`). This is the sole exception. Do not extend it.

## Why This Matters

**The skip-on-index pattern creates silent data loss.** When `add_frontmatter_link()` returns early for index targets, the index body never gets updated. Pages added via manual Parent link edits are invisible to the index until someone manually adds them. Replacing the skip with a body write closes this gap using existing infrastructure.

**Mixing detection and mutation breaks the dry-run contract.** `lint.py` supports `--dry-run`. If a checker mutates state, dry-run is a lie. Keeping checkers pure and fixing at the caller level preserves the ability to preview changes without side effects.

**Hardcoded hierarchy creates brittle assumptions.** If every index is told to point to ROUTER.md, adding an intermediate index (e.g., `wiki/devops/index.md` containing `wiki/kubernetes/index.md`) requires changing the hardcoded rule. Following actual containment means the hierarchy adapts automatically.

**Index frontmatter enables orphan detection.** Without Parent links on index files, the orphan checker cannot trace the index hierarchy. Indexes with no incoming links appear orphaned even though they are structurally necessary. Frontmatter on indexes makes them visible to the link graph.

## When to Apply

- When a reciprocal link system needs to handle targets that store their relationships differently (frontmatter vs. body content)
- When diagnostic/checker functions need to coexist with auto-fix capabilities without violating single-use principles
- When modeling hierarchical indexes where each level has a parent and lists its children
- When extending an existing reciprocal mechanism rather than building a parallel sync system

## Examples

### Before: Index never learns about pages added via Parent links

```python
# add_frontmatter_link.py -- lines 90-94
target_name = target_full.name
if reciprocal_type == "Child" and target_name in ("index.md", "ROUTER.md"):
    return  # index body is never updated
```

User adds `Parent` link to `wiki/kubernetes/pod-security.md` pointing at `wiki/kubernetes/index.md`. The frontmatter link is written. The index body is untouched. `check_index.py` reports the page as "index missing" even though the Parent link exists.

### After: Index body is updated via the reciprocal mechanism

```python
# add_frontmatter_link.py
target_name = target_full.name
if reciprocal_type == "Child" and target_name in ("index.md", "ROUTER.md"):
    _add_to_index_body(str(target_full), filepath)
    return
```

Same scenario. The frontmatter link is written AND `wiki/kubernetes/index.md` body gets `- [Pod Security](pod-security.md)` appended (if not already present). The index stays in sync automatically.

### Before: Auto-fix inside the checker

```python
# check_index.py -- WRONG: mixing detection and mutation
def _check_parent_links() -> list[str]:
    issues: list[str] = []
    for md in cat_dir.glob("*.md"):
        if not has_parent:
            add_frontmatter_link(str(md), parent_link, "Parent")  # mutates!
            issues.append(f"fixed: {rel}")
    return issues
```

Running `lint.py --dry-run` would still write files. The checker is no longer a checker -- it is a checker-and-fixer hybrid that violates the dry-run contract.

### After: Checker returns issues, caller decides to fix

```python
# check_index.py -- pure diagnostic
def _check_parent_links() -> list[str]:
    issues: list[str] = []
    for md in cat_dir.glob("*.md"):
        if not has_parent:
            issues.append(f"missing Parent link: {rel}")
    return issues

# Caller (lint.py or fix script) -- applies fixes
missing = [i for i in issues if i.startswith("missing Parent link: ")]
for issue in missing:
    page = issue.removeprefix("missing Parent link: ")
    cat = Path(page).parent.name
    add_frontmatter_link(page, f"[index](wiki/{cat}/index.md)", "Parent")
```

The checker is testable in isolation. The fix logic is testable in isolation. `--dry-run` can skip the fix step entirely.

### Before: Hardcoded hierarchy

```python
# Every index points to ROUTER.md
PARENT_TARGET = ".knap/ROUTER.md"
```

This breaks when `wiki/kubernetes/index.md` should point to `wiki/index.md`, not `.knap/ROUTER.md`.

### After: Hierarchy follows containment

```python
# Category index -> master index
# Master index -> ROUTER.md
# ROUTER.md -> no parent (root)
PARENT_MAP = {
    "wiki/*/index.md": "wiki/index.md",
    "wiki/index.md": ".knap/ROUTER.md",
}
```

Or better: derive the parent from the directory structure. The category index is in `wiki/{cat}/`, so its parent is `wiki/index.md`. The master index is in `wiki/`, so its parent is `.knap/ROUTER.md`. No mapping table needed.

## Related

- Plan: `docs/plans/2026-06-18-009-feat-category-index-links-plan.md` (Category Index Links)
- Deferred: `docs/plans/2026-06-20-003-feat-index-auto-fix-plan.md` (lint workflow integration for fix_index.py)
- Solution: `docs/solutions/architecture-patterns/modular-lint-checker-system.md` (modular checker architecture)
- Code: `.knap/scripts/add_frontmatter_link.py` (lines 90-94: current skip-on-index logic)
- Code: `.knap/scripts/check_index.py` (`_check_parent_links()`: pure diagnostic)
- Conventions: `.knap/context/conventions.md` (frontmatter link conventions)
