---
title: "Modular Lint Checker System with Shared Utilities"
date: 2026-06-21
category: docs/solutions/architecture-patterns
module: knap/scripts
problem_type: architecture_pattern
component: tooling
severity: medium
applies_when:
  - "Building multi-checker lint/validation systems"
  - "Extracting monolithic validation into composable modules"
  - "Adding config-driven folder classification to file-processing scripts"
tags:
  - lint
  - modular-architecture
  - shared-utilities
  - frontmatter-parsing
  - folder-classification
  - orphan-detection
---

# Modular Lint Checker System with Shared Utilities

## Context

lint.py had a monolithic `check_index()` function (lines 120-175) that did a flat scan of `wiki/index.md` against all wiki pages. With per-category indexes introduced by the foundation plan, page links live in `wiki/{category}/index.md`, not the master index. The flat scan approach broke — it couldn't detect category index ghost entries, missing entries, or files without Parent links.

Beyond the structural mismatch, frontmatter parsing was duplicated across 5 scripts with 3 different return types (`dict|None`, `tuple[dict|None, str|None]`, `tuple[dict|None, str|None, str]`). Folder exclusion was hardcoded as `skip_dirs` sets in each script. There was no orphan detection (files with no incoming links).

The solution required extracting shared utilities, creating config-driven folder classification, and building a modular checker system that lint.py orchestrates.

## Guidance

### 1. Extract shared frontmatter parsing into a class, not a function

The original plan used a 3-tuple return `(dict|None, str|None, str)` from `parse_frontmatter()`. This mixed concerns — why does a frontmatter parser return body content? The better pattern is a class:

```python
class ParsedFile:
    """Read a markdown file once and expose frontmatter, body, and error."""
    def __init__(self, filepath: str | Path):
        self.path = Path(filepath)
        self.frontmatter: dict | None = None
        self.body: str = ""
        self.error: str | None = None
        self._parse()
```

**Why a class:** Reads the file once on instantiation. Properties eliminate return-type confusion. Callers access what they need: `parsed.frontmatter`, `parsed.body`, `parsed.error`. No tuple unpacking, no ignoring unused positions.

### 2. Config-driven folder classification instead of hardcoded skip_dirs

Every script was hardcoding its own `skip_dirs` set. This creates drift — one script excludes `docs/brainstorms`, another doesn't. The pattern:

```yaml
# .knap/schema/folders.yaml
working:
  - wiki/
system:
  - .knap/
excluded:
  - .claude
  - .venv
  - .git
  - __pycache__
  - docs/brainstorms
  - docs/plans
```

```python
# load_folders.py
def get_excluded_folders() -> list[Path]:
    config = _load_config()
    return [Path(p) for p in config.get("excluded", _DEFAULTS["excluded"])]
```

**Multi-component paths require subsequence matching.** A naive `if p in excluded` check fails for paths like `docs/brainstorms` because individual components (`docs`, `brainstorms`) never equal the full path. Use subsequence matching:

```python
def _is_excluded(path_parts: tuple[str, ...], excluded: list[Path]) -> bool:
    for exc in excluded:
        exc_parts = exc.parts
        for i in range(len(path_parts) - len(exc_parts) + 1):
            if path_parts[i : i + len(exc_parts)] == exc_parts:
                return True
    return False
```

### 3. Shared traversal module with indexed_only flag

Both check_index and find_orphans need to discover files in working/system folders. Extract this into a shared module:

```python
def traverse_files(indexed_only: bool = False) -> list[Path]:
    """Traverse all files in working and system folders.
    
    When indexed_only=True, only returns files from folders that have
    an associated index (index.md for working, ROUTER.md for system).
    """
```

### 4. Extract checkers into separate modules

Each checker (check_index, find_orphans) becomes its own module with a single public function returning `list[str]`:

```python
# check_index.py
def check_index() -> list[str]:
    """Check master index, category indexes, and index entries."""
    
# find_orphans.py
def find_orphans() -> list[str]:
    """Find files with no incoming links."""
```

lint.py orchestrates: `check_links()` → `check_frontmatter()` → `check_uningested()` → `check_index()` → `find_orphans()`. Index check MUST run before orphan check — orphan detection is only meaningful when the index is confirmed accurate.

### 5. Wikilink resolution: exact filename match

Wikilinks `[[Birthday Party]]` resolve to `Birthday Party.md` in the same category folder, case-sensitive. Wikilinks with pipe `[[path|display]]` follow standard markdown rules. The resolution checks against the file list already built during traversal — no filesystem globbing needed.

### 6. Index files exempt from Child reciprocity

Index files (`index.md`, `ROUTER.md`) list children in their body, not frontmatter. When `add_frontmatter_link()` generates reciprocal links, it skips writing `Child` reciprocals to index files:

```python
if reciprocal_type == "Child" and target_name in ("index.md", "ROUTER.md"):
    return
```

Other link types (Related, Supersedes, etc.) still generate reciprocals to index files.

## Why This Matters

**Modular checkers prevent context degradation.** A monolithic lint.py with 5 inline checkers grows until it's unreadable. Extracted modules can be tested, understood, and modified independently.

**Config-driven classification prevents drift.** When 5 scripts each hardcode their own skip_dirs, they inevitably diverge. A single config file with a shared loader ensures consistency.

**Shared frontmatter parsing eliminates the "which return type" problem.** Five scripts with three different return types means every caller has to know which variant it's importing. A class with properties is unambiguous.

**The execution-order constraint is critical.** Running orphan detection before index validation produces false positives — a file might appear orphaned simply because its index entry is missing. The orchestrator enforces: index check completes first, then orphan check runs.

## When to Apply

- Building any multi-checker lint/validation system where checks share common utilities
- Extracting monolithic validation into composable modules
- Adding config-driven behavior to file-processing scripts that currently hardcode paths or exclusions
- When frontmatter/metadata parsing is duplicated across multiple scripts with inconsistent return types

## Examples

### Before: Monolithic lint.py with inline checkers

```python
# lint.py — everything inline
def parse_frontmatter(filepath):  # returns dict|None
    ...

def check_index(wiki_dir):  # hardcoded wiki/ path
    ...

def check_links():  # hardcoded skip_dirs
    skip_dirs = {".claude", ".venv", ".git", "__pycache__"}
    ...

def main():
    check_links()
    check_index("wiki")
```

### After: Modular system with shared utilities

```python
# parse_frontmatter.py — shared module
class ParsedFile:
    def __init__(self, filepath):
        self.frontmatter, self.body, self.error = None, "", None
        self._parse()

# load_folders.py — config-driven
def get_excluded_folders() -> list[Path]:
    return _get_folders("excluded")

# traversal.py — shared file discovery
def traverse_files(indexed_only=False) -> list[Path]:
    ...

# check_index.py — extracted checker
def check_index() -> list[str]:
    ...

# find_orphans.py — new checker
def find_orphans() -> list[str]:
    ...

# lint.py — orchestrator
from check_index import check_index
from find_orphans import find_orphans
from load_folders import get_excluded_folders

def main():
    check_links()           # uses get_excluded_folders()
    check_frontmatter()
    check_uningested()
    check_index()           # runs before orphans
    if not args.skip_orphan_check:
        find_orphans()      # only meaningful after index check
```

## Related

- Plan: `docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md`
- Deferred: `docs/plans/2026-06-20-001-chore-backport-frontmatter-parser-plan.md` (backport ParsedFile to remaining scripts)
- Deferred: `docs/plans/2026-06-20-003-feat-index-auto-fix-plan.md` (auto-fix for unlisted pages)
- Conventions: `.knap/context/conventions.md` (unit testing requirements, folder classification)
