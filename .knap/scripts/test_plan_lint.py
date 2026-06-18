#!/usr/bin/env python3
"""Tests for plan_lint.py."""

import pytest
from pathlib import Path

from plan_lint import (
    parse_frontmatter,
    parse_sections,
    parse_requirements_section,
    parse_unit_subsections,
    extract_requirement_refs,
    extract_uid_refs,
    extract_file_paths,
    extract_significant_terms,
    extract_multi_word_phrases,
    check_s1_requirement_coverage,
    check_s2_dangling_requirement_refs,
    check_s3_dangling_dependencies,
    check_s4_file_cross_reference,
    check_s5_deferred_items,
    check_s6_key_term_drift,
    check_s7_cross_unit_terminology,
    parse_plan,
)


# --- Fixtures ---

WELL_FORMED_PLAN = """---
title: "test: Well-formed plan"
type: feat
status: active
date: 2026-06-18
---

# Well-formed plan

## Summary

A well-formed plan for testing.

## Requirements

- C1. First requirement.
- C2. Second requirement.

## Implementation Units

### U1. First unit

- **Goal:** Implement first thing
- **Requirements:** C1
- **Dependencies:** None
- **Files:**
  - `src/first.py` — new: first module
- **Approach:** Create `src/first.py` with the first implementation.
- **Test scenarios:**
  - First test passes
- **Verification:** Tests pass.

### U2. Second unit

- **Goal:** Implement second thing
- **Requirements:** C1, C2
- **Dependencies:** U1
- **Files:**
  - `src/second.py` — new: second module
- **Approach:** Create `src/second.py` with the second implementation.
- **Test scenarios:**
  - Second test passes
- **Verification:** Tests pass.
"""

MISSING_REQ_REF_PLAN = """---
title: "test: Missing requirement reference"
type: feat
status: active
date: 2026-06-18
---

# Missing requirement reference

## Requirements

- C1. First requirement.
- C2. Second requirement.

## Implementation Units

### U1. First unit

- **Goal:** Implement first thing
- **Requirements:** C1, C2, C3
- **Dependencies:** None
- **Files:**
  - `src/first.py` — new: first module
- **Approach:** Create `src/first.py`.
- **Test scenarios:**
  - First test passes
- **Verification:** Tests pass.
"""

DANGLING_DEP_PLAN = """---
title: "test: Dangling dependency"
type: feat
status: active
date: 2026-06-18
---

# Dangling dependency

## Requirements

- C1. First requirement.

## Implementation Units

### U1. First unit

- **Goal:** Implement first thing
- **Requirements:** C1
- **Dependencies:** U2
- **Files:**
  - `src/first.py` — new: first module
- **Approach:** Create `src/first.py`.
- **Test scenarios:**
  - First test passes
- **Verification:** Tests pass.
"""

FILE_NOT_IN_APPROACH_PLAN = """---
title: "test: File not in approach"
type: feat
status: active
date: 2026-06-18
---

# File not in approach

## Requirements

- C1. First requirement.

## Implementation Units

### U1. First unit

- **Goal:** Implement first thing
- **Requirements:** C1
- **Dependencies:** None
- **Files:**
  - `src/first.py` — new: first module
  - `src/second.py` — new: second module
- **Approach:** Create `src/first.py` with the implementation.
- **Test scenarios:**
  - First test passes
- **Verification:** Tests pass.
"""

DRIFT_PLAN = """---
title: "test: Terminology drift"
type: feat
status: active
date: 2026-06-18
---

# Terminology drift

## Requirements

- C1. First requirement.

## Implementation Units

### U1. First unit

- **Goal:** Implement required fields validation
- **Requirements:** C1
- **Dependencies:** None
- **Files:**
  - `src/first.py` — new: first module
- **Approach:** Create `src/first.py` with global required fields handling.
- **Test scenarios:**
  - First test passes
- **Verification:** Tests pass.
"""

UNREFERENCED_REQ_PLAN = """---
title: "test: Unreferenced requirement"
type: feat
status: active
date: 2026-06-18
---

# Unreferenced requirement

## Requirements

- C1. First requirement.
- C2. Second requirement.
- C3. Third requirement.

## Implementation Units

### U1. First unit

- **Goal:** Implement first thing
- **Requirements:** C1
- **Dependencies:** None
- **Files:**
  - `src/first.py` — new: first module
- **Approach:** Create `src/first.py`.
- **Test scenarios:**
  - First test passes
- **Verification:** Tests pass.
"""

MISSING_FRONTMATTER_PLAN = """# No frontmatter

## Requirements

- C1. First requirement.

## Implementation Units

### U1. First unit

- **Goal:** Implement first thing
- **Requirements:** C1
"""

MISSING_UNITS_PLAN = """---
title: "test: No units"
type: feat
status: active
date: 2026-06-18
---

# No units

## Requirements

- C1. First requirement.
"""


# --- Parser tests ---

class TestParseFrontmatter:
    def test_parses_yaml_frontmatter(self):
        content = "---\ntitle: test\nstatus: active\n---\n# Content"
        result = parse_frontmatter(content)
        assert result == {"title": "test", "status": "active"}

    def test_returns_none_without_frontmatter(self):
        content = "# No frontmatter"
        assert parse_frontmatter(content) is None

    def test_returns_none_unclosed_frontmatter(self):
        content = "---\ntitle: test\n# Content"
        assert parse_frontmatter(content) is None


class TestParseSections:
    def test_splits_by_headings(self):
        content = "## First\nBody 1\n## Second\nBody 2"
        sections = parse_sections(content)
        assert "First" in sections
        assert "Second" in sections
        assert sections["First"].strip() == "Body 1"
        assert sections["Second"].strip() == "Body 2"

    def test_handles_h3_headings(self):
        content = "### U1. First unit\nBody"
        sections = parse_sections(content)
        assert "U1. First unit" in sections


class TestParseRequirementsSection:
    def test_extracts_ids(self):
        text = "- C1. First requirement.\n- C2. Second requirement."
        ids = parse_requirements_section(text)
        assert ids == ["C1", "C2"]

    def test_ignores_references(self):
        text = "- C1, C2, C3 — references"
        ids = parse_requirements_section(text)
        assert ids == []


class TestParseUnitSubsections:
    def test_extracts_subsections(self):
        text = "**Goal:** Do something\n**Requirements:** C1\n**Dependencies:** None"
        subs = parse_unit_subsections(text)
        assert subs["Goal"] == "Do something"
        assert subs["Requirements"] == "C1"
        assert subs["Dependencies"] == "None"


class TestExtractRequirementRefs:
    def test_extracts_comma_separated(self):
        text = "C1, C2, C3"
        refs = extract_requirement_refs(text)
        assert refs == ["C1", "C2", "C3"]

    def test_extracts_from_text(self):
        text = "Supersedes origin R11 — scripts now omit absent fields"
        refs = extract_requirement_refs(text)
        assert refs == ["R11"]


class TestExtractUidRefs:
    def test_extracts_uids(self):
        text = "Migration plan complete, U2 (OKF alignment done)"
        refs = extract_uid_refs(text)
        assert refs == ["U2"]

    def test_returns_empty_for_none(self):
        text = "None"
        refs = extract_uid_refs(text)
        assert refs == []


class TestExtractFilePaths:
    def test_extracts_backtick_paths(self):
        text = "- `src/first.py` — new: first module\n- `src/second.py` — update"
        paths = extract_file_paths(text)
        assert paths == ["src/first.py", "src/second.py"]

    def test_ignores_non_paths(self):
        text = "- Just text without paths"
        paths = extract_file_paths(text)
        assert paths == []


# --- Check tests ---

class TestCheckS1RequirementCoverage:
    def test_no_issues_when_all_referenced(self):
        units = {"U1": {"Requirements": "C1, C2"}}
        findings = check_s1_requirement_coverage(["C1", "C2"], units)
        assert findings == []

    def test_flags_unreferenced(self):
        units = {"U1": {"Requirements": "C1"}}
        findings = check_s1_requirement_coverage(["C1", "C2"], units)
        assert len(findings) == 1
        assert "C2" in findings[0]


class TestCheckS2DanglingRequirementRefs:
    def test_no_issues_when_valid(self):
        units = {"U1": {"Requirements": "C1, C2"}}
        findings = check_s2_dangling_requirement_refs(["C1", "C2"], units)
        assert findings == []

    def test_flags_dangling_ref(self):
        units = {"U1": {"Requirements": "C1, C3"}}
        findings = check_s2_dangling_requirement_refs(["C1", "C2"], units)
        assert len(findings) == 1
        assert "C3" in findings[0]


class TestCheckS3DanglingDependencies:
    def test_no_issues_when_valid(self):
        units = {"U1": {"Dependencies": "None"}, "U2": {"Dependencies": "U1"}}
        findings = check_s3_dangling_dependencies(units)
        assert findings == []

    def test_flags_dangling_dep(self):
        units = {"U1": {"Dependencies": "U2"}}
        findings = check_s3_dangling_dependencies(units)
        assert len(findings) == 1
        assert "U2" in findings[0]


class TestCheckS4FileCrossReference:
    def test_no_issues_when_mentioned(self):
        units = {
            "U1": {
                "Files": "`src/first.py` — new",
                "Approach": "Create src/first.py with the implementation."
            }
        }
        findings = check_s4_file_cross_reference(units)
        assert findings == []

    def test_flags_unmentioned_file(self):
        units = {
            "U1": {
                "Files": "`src/first.py` — new\n`src/second.py` — new",
                "Approach": "Create src/first.py with the implementation."
            }
        }
        findings = check_s4_file_cross_reference(units)
        assert len(findings) == 1
        assert "second.py" in findings[0]

    def test_accepts_unchanged_pattern(self):
        units = {
            "U1": {
                "Files": "`src/first.py` — unchanged",
                "Approach": "No change needed for existing module."
            }
        }
        findings = check_s4_file_cross_reference(units)
        assert findings == []


class TestCheckS5DeferredItems:
    def test_no_issues_when_files_exist(self, tmp_path):
        sections = {"Deferred for later": "- `existing.md` — test"}
        (tmp_path / "existing.md").touch()
        import os
        os.chdir(tmp_path)
        findings = check_s5_deferred_items(sections)
        assert findings == []

    def test_flags_missing_file(self):
        sections = {"Deferred for later": "- `docs/plans/nonexistent.md` — test"}
        findings = check_s5_deferred_items(sections)
        assert len(findings) == 1
        assert "nonexistent.md" in findings[0]


class TestCheckS6KeyTermDrift:
    def test_no_issues_when_terms_present(self):
        units = {
            "U1": {
                "Goal": "Implement required fields validation",
                "Approach": "Create module for required fields validation."
            }
        }
        findings = check_s6_key_term_drift(units)
        assert findings == []

    def test_flags_missing_term(self):
        units = {
            "U1": {
                "Goal": "Implement `required fields` validation",
                "Approach": "Create module with validation."
            }
        }
        findings = check_s6_key_term_drift(units)
        assert len(findings) >= 1
        assert any("required fields" in f for f in findings)


class TestCheckS7CrossUnitTerminology:
    def test_no_issues_when_distinct(self):
        units = {
            "U1": {
                "Goal": "Implement user authentication",
                "Files": "`auth.py`",
                "Approach": "Create auth module."
            },
            "U2": {
                "Goal": "Implement data validation",
                "Files": "`validate.py`",
                "Approach": "Create validation module."
            }
        }
        findings = check_s7_cross_unit_terminology(units)
        assert findings == []

    def test_flags_substring_overlap(self):
        units = {
            "U1": {
                "Goal": "Implement required fields",
                "Files": "`fields.py`",
                "Approach": "Create fields module."
            },
            "U2": {
                "Goal": "Implement global required fields",
                "Files": "`global.py`",
                "Approach": "Create global module."
            }
        }
        findings = check_s7_cross_unit_terminology(units)
        assert len(findings) >= 1
        assert any("required fields" in f for f in findings)


# --- Integration tests ---

class TestParsePlan:
    def test_parses_well_formed_plan(self, tmp_path):
        plan_file = tmp_path / "test.md"
        plan_file.write_text(WELL_FORMED_PLAN)
        frontmatter, defined_ids, units = parse_plan(str(plan_file))
        assert frontmatter["title"] == "test: Well-formed plan"
        assert defined_ids == ["C1", "C2"]
        assert "U1" in units
        assert "U2" in units

    def test_exits_on_missing_frontmatter(self, tmp_path):
        plan_file = tmp_path / "test.md"
        plan_file.write_text(MISSING_FRONTMATTER_PLAN)
        with pytest.raises(SystemExit):
            parse_plan(str(plan_file))

    def test_exits_on_no_units(self, tmp_path):
        plan_file = tmp_path / "test.md"
        plan_file.write_text(MISSING_UNITS_PLAN)
        with pytest.raises(SystemExit):
            parse_plan(str(plan_file))


# --- Smoke test ---

class TestSmoke:
    def test_no_crash_on_existing_plans(self):
        """Run plan_lint against all existing plans without crashing."""
        plan_dir = Path("docs/plans")
        if not plan_dir.exists():
            pytest.skip("docs/plans/ not found")

        for plan_file in plan_dir.glob("*.md"):
            # Should not raise
            parse_plan(str(plan_file))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
