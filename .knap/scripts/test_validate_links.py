#!/usr/bin/env python3
"""Tests for links validation in validate.py."""

import pytest
import tempfile
import os

from validate import validate_file


def _write_temp(content: str, tmp_path) -> str:
    """Write content to a temp file and return its path."""
    path = tmp_path / "test.md"
    path.write_text(content)
    return str(path)


BASE_FM = """---
title: Test
source_url: https://example.com
date_farmed: 2026-01-01
category: transcript
channel: test
format: video
"""


class TestLinksValidation:
    def test_valid_links_with_type(self, tmp_path):
        content = BASE_FM + 'links:\n  - target: "[Other](wiki/other.md)"\n    type: Related\n---\n'
        issues = validate_file(_write_temp(content, tmp_path))
        assert issues == []

    def test_valid_links_without_type(self, tmp_path):
        content = BASE_FM + 'links:\n  - target: "[Other](wiki/other.md)"\n---\n'
        issues = validate_file(_write_temp(content, tmp_path))
        assert issues == []

    def test_valid_links_blank_type(self, tmp_path):
        content = BASE_FM + 'links:\n  - target: "[Other](wiki/other.md)"\n    type: ""\n---\n'
        issues = validate_file(_write_temp(content, tmp_path))
        assert issues == []

    def test_invalid_type_value(self, tmp_path):
        content = BASE_FM + 'links:\n  - target: "[Other](wiki/other.md)"\n    type: BadType\n---\n'
        issues = validate_file(_write_temp(content, tmp_path))
        assert len(issues) == 1
        assert issues[0][0] == "error"
        assert "BadType" in issues[0][1]

    def test_missing_target_key(self, tmp_path):
        content = BASE_FM + "links:\n  - type: Related\n---\n"
        issues = validate_file(_write_temp(content, tmp_path))
        assert len(issues) == 1
        assert issues[0][0] == "error"
        assert "missing required key: target" in issues[0][1]

    def test_non_string_target(self, tmp_path):
        content = BASE_FM + "links:\n  - target: 123\n---\n"
        issues = validate_file(_write_temp(content, tmp_path))
        assert len(issues) == 1
        assert issues[0][0] == "error"
        assert "target must be a string" in issues[0][1]

    def test_links_not_a_list(self, tmp_path):
        content = BASE_FM + "links: not-a-list\n---\n"
        issues = validate_file(_write_temp(content, tmp_path))
        assert len(issues) == 1
        assert issues[0][0] == "error"
        assert "links must be a list" in issues[0][1]

    def test_empty_links_list(self, tmp_path):
        content = BASE_FM + "links: []\n---\n"
        issues = validate_file(_write_temp(content, tmp_path))
        assert issues == []

    def test_no_links_field(self, tmp_path):
        content = BASE_FM + "---\n"
        issues = validate_file(_write_temp(content, tmp_path))
        assert issues == []

    def test_entry_not_a_dict(self, tmp_path):
        content = BASE_FM + "links:\n  - not-a-dict\n---\n"
        issues = validate_file(_write_temp(content, tmp_path))
        assert len(issues) == 1
        assert issues[0][0] == "error"
        assert "must be a dict" in issues[0][1]

    def test_multiple_links_mixed_validity(self, tmp_path):
        content = (
            BASE_FM
            + 'links:\n'
            + '  - target: "[Good](wiki/good.md)"\n'
            + '    type: Parent\n'
            + '  - target: "[Bad](wiki/bad.md)"\n'
            + '    type: InvalidType\n'
            + '---\n'
        )
        issues = validate_file(_write_temp(content, tmp_path))
        assert len(issues) == 1
        assert "InvalidType" in issues[0][1]

    def test_all_valid_link_types(self, tmp_path):
        from schema import LINK_TYPES
        for link_type in LINK_TYPES:
            content = (
                BASE_FM
                + f'links:\n  - target: "[Test](wiki/test.md)"\n    type: {link_type}\n---\n'
            )
            issues = validate_file(_write_temp(content, tmp_path))
            assert issues == [], f"Type {link_type} should be valid"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
