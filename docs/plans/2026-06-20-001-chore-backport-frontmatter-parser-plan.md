---
title: 'chore: Backport Frontmatter Parser'
type: chore
status: completed
date: 2026-06-20
origin: docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md
---

# Backport Frontmatter Parser

Deferred from the Orphan Content Checker plan (KTD-7). The shared `ParsedFile` class in `parse_frontmatter.py` needs to be backported to the remaining scripts that have inline frontmatter parsing.

## Problem Frame

Frontmatter parsing is duplicated across 4 scripts with 3 inconsistent return types. The Orphan Content Checker plan created `ParsedFile` as a shared class and adopted it in `check_index.py`, `find_orphans.py`, `add_frontmatter_link.py`, and partially in `lint.py`. The remaining scripts still have inline parsing with incompatible interfaces.

| Script | Current pattern | Return type |
|---|---|---|
| `ingest.py` | `parse_frontmatter(filepath)` | `dict` (raises `ValueError`) |
| `validate.py` | `parse_frontmatter(filepath)` | `tuple[dict\|None, str\|None]` |
| `convert_frontmatter.py` | `parse_frontmatter(content)` | `tuple[dict\|None, str\|None, str]` |
| `lint.py` `check_links()` | inline `yaml.safe_load` | N/A (inline) |

`plan_lint.py` is excluded — it uses simple key:value parsing for ce-plan linting and doesn't need full YAML.

## Requirements

- R1. Replace inline `parse_frontmatter()` in `ingest.py` with `ParsedFile` import
- R2. Replace inline `parse_frontmatter()` in `validate.py` with `ParsedFile` import
- R3. Replace inline `parse_frontmatter()` in `convert_frontmatter.py` with `ParsedFile` import
- R4. Replace inline `yaml.safe_load` in `lint.py` `check_links()` with `ParsedFile` import
- R5. No behavioral changes — all existing tests pass without modification to test logic
- R6. Remove dead `parse_frontmatter` function definitions from `ingest.py`, `validate.py`, and `convert_frontmatter.py`
- R7. Update `convert_frontmatter.py` to use `ParsedFile.from_content()` for frontmatter parsing instead of inline `parse_frontmatter()`

## Key Technical Decisions

### KTD-1. Caller adaptation: error-checking over exceptions

`ParsedFile` sets `self.error` on failure instead of raising. Each caller must adapt:

- **`ingest.py`**: Currently wraps `parse_frontmatter()` in `try/except (ValueError, yaml.YAMLError)`. Replace with `parsed = ParsedFile(path)` + `if parsed.error: ...`. The caller already handles errors gracefully; switching from exception to property check preserves behavior.
- **`validate.py`**: Currently unpacks `data, error = parse_frontmatter(filepath)`. Replace with `parsed = ParsedFile(filepath)` + `data, error = parsed.frontmatter, parsed.error`. Direct mapping.
- **`convert_frontmatter.py`**: Currently unpacks `data, error, body = parse_frontmatter(content)`. Replace with `parsed = ParsedFile.from_content(content)` + access `.frontmatter`, `.error`, `.body`. Uses `from_content()` classmethod because this script parses content strings, not filepaths (see KTD-2).

**Rationale:** Consistent with how `check_index.py`, `find_orphans.py`, and `add_frontmatter_link.py` already use `ParsedFile`. Exception-free error handling is simpler for callers that handle errors inline.

### KTD-2. convert_frontmatter.py: content-string adapter approach

`convert_frontmatter.py` parses from content strings (not filepaths) and needs raw body preservation (no newline stripping). `ParsedFile` takes filepaths and strips leading newlines from body. These are fundamentally incompatible interfaces.

**Decision:** Add a `ParsedFile.from_content(content: str)` classmethod that parses a content string without reading from disk, and does NOT strip leading newlines from body. This serves `convert_frontmatter.py`'s content-string use cases: `convert_file()` (initial parse), `verify_roundtrip()` (re-parse in-memory string), and `migrate_source_field()` (initial parse). The classmethod returns the same `ParsedFile` instance with `.frontmatter`, `.body`, `.error` populated.

`convert_file()` continues to read the file manually with `open(filepath, newline="")` for line-ending detection, then passes the content to `ParsedFile.from_content(content)` for parsing. This preserves Windows line-ending handling. `verify_roundtrip()` passes the reconstructed content string to `ParsedFile.from_content()` — no disk write needed. `migrate_source_field()` can use either `ParsedFile(filepath)` or `ParsedFile.from_content(content)` depending on whether it already has the content in memory.

**Rationale:** Keeps `ParsedFile` as the single parsing interface without sacrificing content-string use cases or raw body preservation. The classmethod is a lightweight addition — it reuses `_parse()` logic but operates on a string instead of reading from disk.

### KTD-3. lint.py check_links(): use ParsedFile consistently

`lint.py` already imports `ParsedFile` and uses it in `check_frontmatter()`. The `check_links()` function (lines 60-97) has inline `yaml.safe_load` parsing. Replace with `ParsedFile(str(md))` and access `.frontmatter` and `.body`. This eliminates the duplicate file read+parse cycle.

**Rationale:** Consistency within the same module. `ParsedFile` reads the file once; the current code reads it separately for frontmatter and body extraction.

## Implementation Units

### U1. Backport frontmatter parsing to ingest.py

**Goal:** Replace inline `parse_frontmatter()` with `ParsedFile` import.

**Requirements:** R1, R5, R6

**Dependencies:** None

**Files:**
- `.knap/scripts/ingest.py` — modify: remove `parse_frontmatter()`, import `ParsedFile`, update callers
- `.knap/scripts/test_ingest_links.py` — verify existing tests pass

**Approach:** Remove the `parse_frontmatter()` function (lines 137-148). Add `from parse_frontmatter import ParsedFile` at the top. Update the caller at line 246 from:
```python
fm = parse_frontmatter(str(raw))
```
to:
```python
parsed = ParsedFile(str(raw))
if parsed.error:
    raise ValueError(parsed.error)
fm = parsed.frontmatter
```
This preserves the existing `try/except (ValueError, yaml.YAMLError)` error handling at the call site. The `yaml.YAMLError` except clause becomes dead code after migration (ParsedFile catches YAML errors internally and returns them as strings). Simplify the except clause to `except ValueError`. Keep `import yaml` — `build_wiki_page` uses `yaml.dump` at line 108.

**Test scenarios:**
- Existing `test_ingest_links.py` tests pass unchanged
- `ParsedFile` is imported from `parse_frontmatter` module
- `parse_frontmatter` function no longer exists in `ingest.py`

**Verification:** `pytest .knap/scripts/test_ingest_links.py` passes.

### U2. Backport frontmatter parsing to validate.py

**Goal:** Replace inline `parse_frontmatter()` with `ParsedFile` import.

**Requirements:** R2, R5, R6

**Dependencies:** None

**Files:**
- `.knap/scripts/validate.py` — modify: remove `parse_frontmatter()`, import `ParsedFile`, update callers
- `.knap/scripts/test_validate_links.py` — verify existing tests pass

**Approach:** Remove the `parse_frontmatter()` function (lines 19-33). Add `from parse_frontmatter import ParsedFile` at the top. Update the caller at line 38 from:
```python
data, error = parse_frontmatter(filepath)
```
to:
```python
parsed = ParsedFile(filepath)
data, error = parsed.frontmatter, parsed.error
```
The rest of `validate_file()` uses `data` and `error` identically. Remove `import yaml` — it is only used inside `parse_frontmatter()`.

**Test scenarios:**
- Existing `test_validate_links.py` tests pass unchanged
- `ParsedFile` is imported from `parse_frontmatter` module
- `parse_frontmatter` function no longer exists in `validate.py`

**Verification:** `pytest .knap/scripts/test_validate_links.py` passes.

### U3. Add ParsedFile.from_content() and backport to convert_frontmatter.py

**Goal:** Add a `ParsedFile.from_content()` classmethod for content-string parsing, then replace inline `parse_frontmatter()` in `convert_frontmatter.py`.

**Requirements:** R3, R5, R6, R7

**Dependencies:** None

**Files:**
- `.knap/scripts/parse_frontmatter.py` — modify: add `ParsedFile.from_content(content: str)` classmethod
- `.knap/scripts/test_parse_frontmatter.py` — modify: add tests for `from_content()`
- `.knap/scripts/convert_frontmatter.py` — modify: remove `parse_frontmatter()`, import `ParsedFile`, update callers
- `.knap/scripts/test_convert_frontmatter.py` — modify: update `from convert_frontmatter import parse_frontmatter` to `from parse_frontmatter import ParsedFile` and adapt `TestParseFrontmatter` class to use `ParsedFile.from_content()`

**Approach:**

Step 1: Add `ParsedFile.from_content()` to `parse_frontmatter.py`:
```python
@classmethod
def from_content(cls, content: str) -> "ParsedFile":
    """Parse frontmatter from a content string (no file read)."""
    instance = cls.__new__(cls)
    instance.path = None
    instance.frontmatter = None
    instance.body = ""
    instance.error = None
    instance._parse_content(content)
    return instance
```
Extract the parsing logic from `_parse()` into a `_parse_content(content)` method. Both `_parse()` and `from_content()` call `_parse_content()`. `from_content()` does NOT strip leading newlines from body (unlike `_parse()` which calls `.lstrip("\n")`) — this preserves the raw body that `convert_frontmatter.py` needs for round-trip fidelity.

Step 2: Refactor `convert_frontmatter.py`:
- Remove `parse_frontmatter()` function (lines 105-136)
- Add `from parse_frontmatter import ParsedFile`
- `convert_file()`: keep `open(filepath, newline="")` for `detect_line_ending()`, then `parsed = ParsedFile.from_content(content)` for parsing. Access `parsed.frontmatter`, `parsed.body`, `parsed.error`.
- `verify_roundtrip()`: replace `parse_frontmatter(new_content)` with `ParsedFile.from_content(new_content)`. Access `.frontmatter` and `.error`.
- `migrate_source_field()`: replace `parse_frontmatter(content)` with `ParsedFile.from_content(content)`. Access `.frontmatter`, `.body`, `.error`.

Step 3: Update `test_convert_frontmatter.py`:
- Change import from `from convert_frontmatter import ..., parse_frontmatter, ...` to `from parse_frontmatter import ParsedFile`
- Update `TestParseFrontmatter` class: replace `parse_frontmatter(content)` calls with `ParsedFile.from_content(content)`, update assertions to use `.frontmatter`, `.error`, `.body` properties
- This is a test update, not a behavioral change — the tests verify the same parsing behavior through the new interface

**Test scenarios:**
- `ParsedFile.from_content(valid_content)` returns correct frontmatter, body, error=None
- `ParsedFile.from_content(missing_frontmatter)` returns frontmatter=None, error set
- `ParsedFile.from_content(unclosed_frontmatter)` returns frontmatter=None, error set
- `ParsedFile.from_content(invalid_yaml)` returns frontmatter=None, error set
- Body is NOT stripped of leading newlines (unlike `ParsedFile(filepath)`)
- Existing `test_convert_frontmatter.py` tests pass with updated imports
- `parse_frontmatter` function no longer exists in `convert_frontmatter.py`

**Verification:** `pytest .knap/scripts/test_parse_frontmatter.py` passes. `pytest .knap/scripts/test_convert_frontmatter.py` passes.

### U4. Backport frontmatter parsing to lint.py check_links()

**Goal:** Replace inline `yaml.safe_load` in `check_links()` with `ParsedFile`.

**Requirements:** R4, R5

**Dependencies:** None

**Files:**
- `.knap/scripts/lint.py` — modify: refactor `check_links()` to use `ParsedFile`, remove `import yaml`
- `.knap/scripts/test_lint_links.py` — verify existing tests pass

**Approach:** In `check_links()` (lines 60-97), the current code extracts body content independently of frontmatter parsing success — body links and wikilinks are checked even when YAML is malformed. `ParsedFile` sets body only on successful frontmatter parse. To preserve behavior:

Replace the inline parsing block (lines 66-97):
```python
try:
    content = md.read_text()
except Exception:
    continue
if not content.startswith("---"):
    continue
end = content.find("---", 3)
if end == -1:
    continue
fm_yaml = content[3:end]
body = content[end + 3:]
rel_path = str(md.relative_to(repo_root))
try:
    fm = yaml.safe_load(fm_yaml)
    if isinstance(fm, dict):
        links = fm.get("links", [])
        # ... check frontmatter links
except yaml.YAMLError:
    pass
# body link checking continues below
```
with:
```python
parsed = ParsedFile(str(md))
if not parsed.body and parsed.error:
    continue  # file unreadable
rel_path = str(md.relative_to(repo_root))
if parsed.frontmatter:
    links = parsed.frontmatter.get("links", [])
    # ... check frontmatter links
# body link checking continues below using parsed.body
```
Key behavioral preservation: `ParsedFile` sets `body` even when frontmatter fails (the body extraction happens before YAML parsing in `_parse_content()`). If the file is unreadable (FileNotFoundError, OSError), both body and frontmatter are empty/None — skip. If frontmatter is malformed but file is readable, body is populated — continue to body link checks. `ParsedFile` is already imported on line 26. Remove `import yaml` (no other uses in lint.py).

**Test scenarios:**
- Existing `test_lint_links.py` tests pass unchanged
- `check_links()` uses `ParsedFile` instead of inline parsing
- Files with missing frontmatter are skipped (same behavior)
- Files with malformed YAML frontmatter still get body links checked (behavioral preservation)
- Body link extraction still works

**Verification:** `pytest .knap/scripts/test_lint_links.py` passes.

### U5. Verify no regressions across all tests

**Goal:** Run the full test suite to confirm no behavioral changes.

**Requirements:** R5

**Dependencies:** U1, U2, U3, U4

**Files:** None (verification only)

**Approach:** Run `pytest .knap/scripts/` to execute all tests. Verify all pass. Run `python3 .knap/scripts/lint.py` to verify the lint script works end-to-end.

**Test scenarios:**
- All existing tests pass
- `lint.py` runs without errors

**Verification:** `pytest .knap/scripts/` exits 0. `python3 .knap/scripts/lint.py` runs successfully.

---

## Scope Boundaries

**In scope:**
- Backport `ParsedFile` to `ingest.py`, `validate.py`, `convert_frontmatter.py`, `lint.py` `check_links()`
- Remove dead `parse_frontmatter()` function definitions
- Update callers to use `ParsedFile` interface
- Verify existing tests pass

**Deferred to follow-up work:**
- `plan_lint.py` — excluded per user decision (simple key:value parsing, ce-plan specific)

**Outside this scope:**
- Changes to `ParsedFile` class beyond adding `from_content()` classmethod
- New features or behavioral changes
- Changes to scripts already using `ParsedFile`

---

## Sources & Research

- Origin: `docs/plans/2026-06-18-005-feat-orphan-content-checker-plan.md` KTD-7 defines the shared module pattern
- Learning: `docs/solutions/architecture-patterns/modular-lint-checker-system.md` documents the `ParsedFile` pattern and return-type consolidation rationale
- Reference: `.knap/scripts/parse_frontmatter.py` — the `ParsedFile` class
- Reference: `.knap/scripts/check_index.py`, `find_orphans.py`, `add_frontmatter_link.py` — existing `ParsedFile` adoption patterns
