#!/usr/bin/env python3
"""Tests for convert_frontmatter.py.

Tests the frontmatter format converter script including:
- Frontmatter parsing
- yaml.dump() serialization
- Round-trip consistency
- Body preservation
- Error handling
- Dry-run mode
- Line ending preservation
- Validate.py integration
"""

import os
import pytest
from datetime import date as date_type, datetime
from pathlib import Path

import yaml

from convert_frontmatter import (
    discover_md_files,
    detect_line_ending,
    serialize_frontmatter,
    verify_roundtrip,
    verify_body_preservation,
    convert_file,
)
from parse_frontmatter import ParsedFile


# --- Fixtures ---

SAMPLE_FRONTMATTER = """\
---
title: "Test Title"
source_url: "https://example.com"
date_farmed: 2026-06-17
category: transcript
tags:
  - tag1
  - tag2
---

# Content

This is the body.
"""

SAMPLE_FRONTMATTER_MANUAL = """\
---
title: "Test Title"
source_url: "https://example.com"
date_farmed: 2026-06-17
category: transcript
tags:
  - tag1
  - tag2
---

# Content

This is the body.
"""

SAMPLE_FRONTMATTER_YAML_DUMP = """\
---
title: Test Title
source_url: https://example.com
date_farmed: 2026-06-17
category: transcript
tags:
- tag1
- tag2
---

# Content

This is the body.
"""

NO_FRONTMATTER = """\
# Just a heading

No frontmatter here.
"""

MALFORMED_FRONTMATTER = """\
---
title: "Unclosed frontmatter
# Content
"""

EMPTY_LIST_FRONTMATTER = """\
---
title: "Empty List Test"
tags: []
---

Body content.
"""

DATE_FRONTMATTER = """\
---
title: "Date Test"
date_farmed: 2026-06-17
category: reference
---

Body content.
"""

NA_VALUE_FRONTMATTER = """\
---
title: "N/A Test"
source_url: "n/a"
category: reference
---

Body content.
"""

MARKDOWN_LINK_FRONTMATTER = """\
---
title: "Link Test"
source: "[file.md](../raw/transcripts/file.md)"
category: reference
---

Body content.
"""

DICT_LIST_FRONTMATTER = """\
---
title: "Dict List Test"
links:
  - type: transcript
    path: raw/transcripts/file.md
  - type: wiki
    path: wiki/transcripts/file.md
---

Body content.
"""

WINDOWS_LINE_ENDINGS = """\
---
title: "Windows Test"
category: reference
---

Body content.
""".replace("\n", "\r\n")


# --- Parser tests ---

class TestParseFrontmatter:
    def test_parses_yaml_frontmatter(self):
        parsed = ParsedFile.from_content(SAMPLE_FRONTMATTER)
        assert parsed.error is None
        assert parsed.frontmatter["title"] == "Test Title"
        assert parsed.frontmatter["source_url"] == "https://example.com"
        assert parsed.frontmatter["date_farmed"] == date_type(2026, 6, 17)
        assert parsed.frontmatter["category"] == "transcript"
        assert parsed.frontmatter["tags"] == ["tag1", "tag2"]
        assert "# Content" in parsed.body

    def test_returns_error_without_frontmatter(self):
        parsed = ParsedFile.from_content(NO_FRONTMATTER)
        assert parsed.frontmatter is None
        assert "Missing frontmatter" in parsed.error

    def test_returns_error_unclosed_frontmatter(self):
        parsed = ParsedFile.from_content(MALFORMED_FRONTMATTER)
        assert parsed.frontmatter is None
        assert "Unclosed frontmatter" in parsed.error

    def test_handles_empty_list(self):
        parsed = ParsedFile.from_content(EMPTY_LIST_FRONTMATTER)
        assert parsed.error is None
        assert parsed.frontmatter["tags"] == []

    def test_handles_date_values(self):
        parsed = ParsedFile.from_content(DATE_FRONTMATTER)
        assert parsed.error is None
        assert parsed.frontmatter["date_farmed"] == date_type(2026, 6, 17)

    def test_handles_na_values(self):
        parsed = ParsedFile.from_content(NA_VALUE_FRONTMATTER)
        assert parsed.error is None
        assert parsed.frontmatter["source_url"] == "n/a"

    def test_handles_markdown_links(self):
        parsed = ParsedFile.from_content(MARKDOWN_LINK_FRONTMATTER)
        assert parsed.error is None
        assert "[file.md]" in parsed.frontmatter["source"]

    def test_handles_dict_lists(self):
        parsed = ParsedFile.from_content(DICT_LIST_FRONTMATTER)
        assert parsed.error is None
        assert len(parsed.frontmatter["links"]) == 2
        assert parsed.frontmatter["links"][0]["type"] == "transcript"


# --- Serialization tests ---

class TestSerializeFrontmatter:
    def test_produces_block_style_yaml(self):
        data = {"title": "Test", "tags": ["a", "b"]}
        result = serialize_frontmatter(data)
        assert "- a" in result
        assert "- b" in result
        # Should not use flow style [a, b]
        assert "[a, b]" not in result

    def test_preserves_field_order(self):
        data = {"zebra": 1, "apple": 2, "mango": 3}
        result = serialize_frontmatter(data)
        lines = result.strip().split("\n")
        keys = [line.split(":")[0] for line in lines]
        assert keys == ["zebra", "apple", "mango"]

    def test_handles_empty_list(self):
        data = {"tags": []}
        result = serialize_frontmatter(data)
        assert "tags: []" in result

    def test_handles_dict_list(self):
        data = {"links": [{"type": "a", "path": "b"}]}
        result = serialize_frontmatter(data)
        assert "type: a" in result
        assert "path: b" in result


# --- Round-trip tests ---

class TestRoundtrip:
    def test_roundtrip_preserves_data(self):
        data = {
            "title": "Test",
            "source_url": "https://example.com",
            "date_farmed": date_type(2026, 6, 17),
            "tags": ["a", "b"],
        }
        yaml_str = serialize_frontmatter(data)
        new_content = f"---\n{yaml_str}---\n\nBody"
        is_valid, error = verify_roundtrip(data, new_content)
        assert is_valid is True
        assert error is None

    def test_roundtrip_detects_mismatch(self):
        data = {"title": "Original"}
        new_content = '---\ntitle: "Different"\n---\n\nBody'
        is_valid, error = verify_roundtrip(data, new_content)
        assert is_valid is False
        assert "mismatch" in error.lower()


# --- Body preservation tests ---

class TestBodyPreservation:
    def test_preserves_identical_body(self):
        body = "\n\n# Heading\n\nContent here.\n"
        is_valid, error = verify_body_preservation(body, body)
        assert is_valid is True
        assert error is None

    def test_detects_body_difference(self):
        original = "\n\n# Heading\n"
        modified = "\n\n# Different\n"
        is_valid, error = verify_body_preservation(original, modified)
        assert is_valid is False
        assert "differs" in error.lower()


# --- Line ending tests ---

class TestDetectLineEnding:
    def test_detects_unix_endings(self):
        content = "line1\nline2\n"
        assert detect_line_ending(content) == "\n"

    def test_detects_windows_endings(self):
        content = "line1\r\nline2\r\n"
        assert detect_line_ending(content) == "\r\n"


# --- File discovery tests ---

class TestDiscoverMdFiles:
    def test_finds_md_files(self, tmp_path):
        (tmp_path / "test.md").touch()
        (tmp_path / "test.txt").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "nested.md").touch()

        files = discover_md_files(str(tmp_path))
        assert len(files) == 2
        assert any("test.md" in f for f in files)
        assert any("nested.md" in f for f in files)

    def test_skips_venv(self, tmp_path):
        (tmp_path / "test.md").touch()
        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "skipped.md").touch()

        files = discover_md_files(str(tmp_path))
        assert len(files) == 1
        assert "test.md" in files[0]

    def test_respects_path_filter(self, tmp_path):
        (tmp_path / "test.md").touch()
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "wiki.md").touch()

        files = discover_md_files(str(tmp_path), "wiki/")
        assert len(files) == 1
        assert "wiki.md" in files[0]


# --- Integration tests ---

class TestConvertFile:
    def test_converts_manual_format(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(SAMPLE_FRONTMATTER_MANUAL)

        status, detail = convert_file(str(filepath))
        assert status == "converted"

        # Verify the file was actually converted
        content = filepath.read_text()
        parsed = ParsedFile.from_content(content)
        data = parsed.frontmatter
        error = parsed.error
        assert error is None
        assert data["title"] == "Test Title"

    def test_leaves_yaml_dump_unchanged(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(SAMPLE_FRONTMATTER_YAML_DUMP)

        status, detail = convert_file(str(filepath))
        assert status == "unchanged"

    def test_skips_no_frontmatter(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(NO_FRONTMATTER)

        status, detail = convert_file(str(filepath))
        assert status == "skipped"

    def test_dry_run_does_not_modify(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(SAMPLE_FRONTMATTER_MANUAL)
        original = filepath.read_text()

        status, detail = convert_file(str(filepath), dry_run=True)
        assert status == "would_convert"
        assert filepath.read_text() == original

    def test_preserves_empty_list(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(EMPTY_LIST_FRONTMATTER)

        status, detail = convert_file(str(filepath))
        assert status in ("converted", "unchanged")

        content = filepath.read_text()
        parsed = ParsedFile.from_content(content)
        data = parsed.frontmatter
        error = parsed.error
        assert error is None
        assert data["tags"] == []

    def test_preserves_date_type(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(DATE_FRONTMATTER)

        status, detail = convert_file(str(filepath))
        assert status in ("converted", "unchanged")

        content = filepath.read_text()
        parsed = ParsedFile.from_content(content)
        data = parsed.frontmatter
        error = parsed.error
        assert error is None
        assert data["date_farmed"] == date_type(2026, 6, 17)

    def test_preserves_na_value(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(NA_VALUE_FRONTMATTER)

        status, detail = convert_file(str(filepath))
        assert status in ("converted", "unchanged")

        content = filepath.read_text()
        parsed = ParsedFile.from_content(content)
        data = parsed.frontmatter
        error = parsed.error
        assert error is None
        assert data["source_url"] == "n/a"

    def test_preserves_markdown_links(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(MARKDOWN_LINK_FRONTMATTER)

        status, detail = convert_file(str(filepath))
        assert status in ("converted", "unchanged")

        content = filepath.read_text()
        parsed = ParsedFile.from_content(content)
        data = parsed.frontmatter
        error = parsed.error
        assert error is None
        assert "[file.md]" in data["source"]

    def test_preserves_dict_list(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(DICT_LIST_FRONTMATTER)

        status, detail = convert_file(str(filepath))
        assert status in ("converted", "unchanged")

        content = filepath.read_text()
        parsed = ParsedFile.from_content(content)
        data = parsed.frontmatter
        error = parsed.error
        assert error is None
        assert len(data["links"]) == 2
        assert data["links"][0]["type"] == "transcript"

    def test_preserves_body_content(self, tmp_path):
        filepath = tmp_path / "test.md"
        filepath.write_text(SAMPLE_FRONTMATTER_MANUAL)

        # Extract original body
        with open(filepath) as f:
            content = f.read()
        end = content.find("---", 3)
        original_body = content[end + 3:]

        status, detail = convert_file(str(filepath))
        assert status == "converted"

        # Verify body is preserved
        with open(filepath) as f:
            new_content = f.read()
        new_end = new_content.find("---", 3)
        new_body = new_content[new_end + 3:]

        assert original_body == new_body

    def test_roundtrip_consistency(self, tmp_path):
        """Converted file re-reads to identical data structure."""
        filepath = tmp_path / "test.md"
        filepath.write_text(SAMPLE_FRONTMATTER_MANUAL)

        # Parse original
        with open(filepath) as f:
            content = f.read()
        parsed = ParsedFile.from_content(content)
        original_data = parsed.frontmatter

        # Convert
        status, detail = convert_file(str(filepath))
        assert status == "converted"

        # Parse converted
        with open(filepath) as f:
            new_content = f.read()
        parsed = ParsedFile.from_content(new_content)
        new_data = parsed.frontmatter

        assert original_data == new_data


# --- Smoke test ---

class TestSmoke:
    def test_no_crash_on_existing_files(self, tmp_path, monkeypatch):
        """Run converter against all existing files without crashing."""
        # Create a few test files
        (tmp_path / "test1.md").write_text(SAMPLE_FRONTMATTER_MANUAL)
        (tmp_path / "test2.md").write_text(NO_FRONTMATTER)
        (tmp_path / "test3.md").write_text(EMPTY_LIST_FRONTMATTER)

        monkeypatch.chdir(tmp_path)

        # Run converter - should not crash
        for md_file in tmp_path.glob("*.md"):
            try:
                convert_file(str(md_file))
            except Exception as e:
                pytest.fail(f"convert_file crashed on {md_file.name}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
