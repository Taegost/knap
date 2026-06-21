#!/usr/bin/env python3
"""Tests for parse_frontmatter.py."""

import pytest
from pathlib import Path

from parse_frontmatter import ParsedFile


class TestParsedFile:
    def test_valid_frontmatter_with_body(self, tmp_path):
        """frontmatter is dict, body is content, error is None."""
        f = tmp_path / "test.md"
        f.write_text("---\ntitle: Hello\ncategory: research\n---\n\nBody content here.\n")
        parsed = ParsedFile(f)
        assert parsed.error is None
        assert parsed.frontmatter == {"title": "Hello", "category": "research"}
        assert parsed.body == "Body content here.\n"

    def test_valid_frontmatter_no_body(self, tmp_path):
        """frontmatter is dict, body is empty string, error is None."""
        f = tmp_path / "test.md"
        f.write_text("---\ntitle: Hello\n---\n")
        parsed = ParsedFile(f)
        assert parsed.error is None
        assert parsed.frontmatter == {"title": "Hello"}
        assert parsed.body == ""

    def test_missing_frontmatter(self, tmp_path):
        """frontmatter is None, error describes the issue."""
        f = tmp_path / "test.md"
        f.write_text("# Just a heading\n\nNo frontmatter here.\n")
        parsed = ParsedFile(f)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "Missing frontmatter" in parsed.error

    def test_unclosed_frontmatter(self, tmp_path):
        """frontmatter is None, error describes the issue."""
        f = tmp_path / "test.md"
        f.write_text("---\ntitle: Hello\nNo closing delimiter\n")
        parsed = ParsedFile(f)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "Unclosed frontmatter" in parsed.error

    def test_invalid_yaml(self, tmp_path):
        """frontmatter is None, error describes the issue."""
        f = tmp_path / "test.md"
        f.write_text("---\ntitle: [unclosed\n---\n")
        parsed = ParsedFile(f)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "YAML error" in parsed.error

    def test_empty_file(self, tmp_path):
        """frontmatter is None, error describes the issue."""
        f = tmp_path / "test.md"
        f.write_text("")
        parsed = ParsedFile(f)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "Empty file" in parsed.error

    def test_file_not_found(self, tmp_path):
        """frontmatter is None, error describes the issue."""
        parsed = ParsedFile(tmp_path / "nonexistent.md")
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "File not found" in parsed.error

    def test_body_without_trailing_newline(self, tmp_path):
        """Body captured correctly when no trailing newline."""
        f = tmp_path / "test.md"
        f.write_text("---\ntitle: Hello\n---\nBody")
        parsed = ParsedFile(f)
        assert parsed.error is None
        assert parsed.body == "Body"

    def test_frontmatter_is_not_dict(self, tmp_path):
        """Error when frontmatter parses to a non-dict (e.g. a list)."""
        f = tmp_path / "test.md"
        f.write_text("---\n- item1\n- item2\n---\n")
        parsed = ParsedFile(f)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "not a mapping" in parsed.error

    def test_path_stored(self, tmp_path):
        """ParsedFile stores the Path object."""
        f = tmp_path / "test.md"
        f.write_text("---\ntitle: X\n---\n")
        parsed = ParsedFile(f)
        assert parsed.path == f


class TestFromContent:
    def test_valid_frontmatter_with_body(self):
        """from_content returns correct frontmatter, body, error."""
        content = "---\ntitle: Hello\ncategory: research\n---\n\nBody content here.\n"
        parsed = ParsedFile.from_content(content)
        assert parsed.error is None
        assert parsed.frontmatter == {"title": "Hello", "category": "research"}
        assert parsed.body == "\n\nBody content here.\n"

    def test_valid_frontmatter_no_body(self):
        """from_content returns empty body when no body present."""
        content = "---\ntitle: Hello\n---\n"
        parsed = ParsedFile.from_content(content)
        assert parsed.error is None
        assert parsed.frontmatter == {"title": "Hello"}
        assert parsed.body == "\n"

    def test_missing_frontmatter(self):
        """from_content returns error on missing frontmatter."""
        content = "# Just a heading\n\nNo frontmatter here.\n"
        parsed = ParsedFile.from_content(content)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "Missing frontmatter" in parsed.error

    def test_unclosed_frontmatter(self):
        """from_content returns error on unclosed frontmatter."""
        content = "---\ntitle: Hello\nNo closing delimiter\n"
        parsed = ParsedFile.from_content(content)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "Unclosed frontmatter" in parsed.error

    def test_invalid_yaml(self):
        """from_content returns error on invalid YAML."""
        content = "---\ntitle: [unclosed\n---\n"
        parsed = ParsedFile.from_content(content)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "YAML error" in parsed.error

    def test_empty_content(self):
        """from_content returns error on empty string."""
        parsed = ParsedFile.from_content("")
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "Empty file" in parsed.error

    def test_body_not_stripped(self):
        """from_content does NOT strip leading newlines from body."""
        content = "---\ntitle: Hello\n---\n\n\nBody"
        parsed = ParsedFile.from_content(content)
        assert parsed.error is None
        # raw body includes all content after closing ---, no stripping
        assert parsed.body == "\n\n\nBody"

    def test_body_available_on_yaml_error(self):
        """from_content sets body even when YAML parsing fails."""
        content = "---\ntitle: [unclosed\n---\nBody still here\n"
        parsed = ParsedFile.from_content(content)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert parsed.body == "\nBody still here\n"

    def test_path_is_none(self):
        """from_content sets path to None."""
        parsed = ParsedFile.from_content("---\ntitle: X\n---\n")
        assert parsed.path is None

    def test_frontmatter_is_not_dict(self):
        """from_content returns error when frontmatter is not a dict."""
        content = "---\n- item1\n- item2\n---\n"
        parsed = ParsedFile.from_content(content)
        assert parsed.frontmatter is None
        assert parsed.error is not None
        assert "not a mapping" in parsed.error
