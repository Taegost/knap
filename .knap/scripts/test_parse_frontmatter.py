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
