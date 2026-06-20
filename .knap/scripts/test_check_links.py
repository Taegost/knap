#!/usr/bin/env python3
"""Tests for check_links.py."""

import pytest
from pathlib import Path

from check_links import check_link


class TestCheckLink:
    def test_existing_file_repo_root_relative(self, tmp_path, monkeypatch):
        """Resolves repo-root-relative paths correctly."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki" / "transcripts").mkdir(parents=True)
        (tmp_path / "wiki" / "transcripts" / "foo.md").write_text("# Foo")
        result = check_link("[Page](wiki/transcripts/foo.md)")
        assert result.exists is True
        assert result.is_external is False

    def test_nonexistent_file_repo_root_relative(self, tmp_path, monkeypatch):
        """Returns exists=False for missing files."""
        monkeypatch.chdir(tmp_path)
        result = check_link("[Page](wiki/nonexistent.md)")
        assert result.exists is False
        assert result.is_external is False

    def test_relative_to_file(self, tmp_path, monkeypatch):
        """Resolves relative to a given file's directory."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki" / "transcripts").mkdir(parents=True)
        (tmp_path / "wiki" / "transcripts" / "bar.md").write_text("# Bar")
        result = check_link(
            "[Page](bar.md)",
            relative_to="wiki/transcripts/other.md"
        )
        assert result.exists is True
        assert result.is_external is False

    def test_relative_to_with_parent_dir(self, tmp_path, monkeypatch):
        """Resolves ../ paths relative to a given file."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki" / "other").mkdir(parents=True)
        (tmp_path / "wiki" / "other" / "page.md").write_text("# Page")
        result = check_link(
            "[Page](../other/page.md)",
            relative_to="wiki/transcripts/bar.md"
        )
        assert result.exists is True
        assert result.is_external is False

    def test_external_url(self, tmp_path, monkeypatch):
        """External URLs return is_external=True."""
        monkeypatch.chdir(tmp_path)
        result = check_link("[Site](https://example.com)")
        assert result.is_external is True

    def test_external_url_http(self, tmp_path, monkeypatch):
        """HTTP URLs are also external."""
        monkeypatch.chdir(tmp_path)
        result = check_link("[Site](http://example.com)")
        assert result.is_external is True

    def test_plain_path_not_markdown_format(self, tmp_path, monkeypatch):
        """Non-markdown-link strings are treated as plain paths."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "test.md").write_text("# Test")
        result = check_link("wiki/test.md")
        assert result.exists is True
        assert result.is_external is False

    def test_markdown_link_extraction(self, tmp_path, monkeypatch):
        """Extracts URL correctly from markdown link format."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "page.md").write_text("# Page")
        result = check_link("[Any Name](wiki/page.md)")
        assert result.exists is True

    def test_nonexistent_relative_to(self, tmp_path, monkeypatch):
        """Returns exists=False when relative_to file's dir doesn't help."""
        monkeypatch.chdir(tmp_path)
        result = check_link(
            "[Page](nonexistent.md)",
            relative_to="wiki/transcripts/other.md"
        )
        assert result.exists is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
