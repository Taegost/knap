#!/usr/bin/env python3
"""Tests for link validation in lint.py."""

import pytest
import shutil
import yaml
from pathlib import Path

from lint import check_links


def _make_file(path: Path, fm: dict, body: str = "\n# Test\n") -> str:
    """Create a markdown file with frontmatter."""
    content = f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---{body}"
    path.write_text(content)
    return str(path)


def _setup_repo(tmp_path):
    """Set up minimal repo structure with schema for CWD-relative imports."""
    knap_dir = tmp_path / ".knap" / "schema"
    knap_dir.mkdir(parents=True)
    templates_dir = knap_dir / "templates"
    templates_dir.mkdir()
    shutil.copy(
        Path(__file__).resolve().parent.parent / "schema" / "categories.yaml",
        knap_dir / "categories.yaml",
    )
    shutil.copy(
        Path(__file__).resolve().parent.parent / "schema" / "templates" / "categories.yaml.template",
        templates_dir / "categories.yaml.template",
    )
    shutil.copy(
        Path(__file__).resolve().parent.parent / "schema" / "templates" / "folders.yaml.template",
        templates_dir / "folders.yaml.template",
    )


class TestCheckLinks:
    def test_valid_frontmatter_link(self, tmp_path, monkeypatch):
        """Valid frontmatter link produces no issues."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki" / "test"
        wiki.mkdir(parents=True)
        target = wiki / "target.md"
        target.write_text("# Target")
        fm = {"title": "Test", "links": [{"target": "[Target](wiki/test/target.md)", "type": "Related"}]}
        _make_file(wiki / "source.md", fm)
        issues = check_links()
        assert issues == []

    def test_broken_frontmatter_link_error(self, tmp_path, monkeypatch):
        """Broken frontmatter internal link produces an error."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        fm = {"title": "Test", "links": [{"target": "[Missing](wiki/nonexistent.md)", "type": "Related"}]}
        _make_file(wiki / "source.md", fm)
        issues = check_links()
        assert any("error" in i and "broken frontmatter link" in i for i in issues)

    def test_broken_body_link_warning(self, tmp_path, monkeypatch):
        """Broken body link produces a warning, not an error."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        body = "\n[Missing](wiki/nonexistent.md)\n"
        _make_file(wiki / "source.md", {"title": "Test"}, body)
        issues = check_links()
        assert any("warning" in i and "broken body link" in i for i in issues)

    def test_no_frontmatter_links(self, tmp_path, monkeypatch):
        """Files without links field produce no issues."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        _make_file(wiki / "test.md", {"title": "Test"})
        issues = check_links()
        assert issues == []

    def test_excludes_claude_dir(self, tmp_path, monkeypatch):
        """Files in .claude/ are excluded."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        claude = tmp_path / ".claude"
        claude.mkdir(parents=True)
        fm = {"title": "Test", "links": [{"target": "[Missing](wiki/nonexistent.md)", "type": "Related"}]}
        _make_file(claude / "test.md", fm)
        issues = check_links()
        assert issues == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
