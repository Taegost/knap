#!/usr/bin/env python3
"""Tests for fix_index.py."""

import pytest
import yaml
from pathlib import Path

from fix_index import fix_index


def _setup_repo(tmp_path):
    """Create minimal repo structure with folders.yaml."""
    schema_dir = tmp_path / ".knap" / "schema"
    schema_dir.mkdir(parents=True)
    templates_dir = schema_dir / "templates"
    templates_dir.mkdir()
    config = {
        "working": ["wiki/"],
        "system": [".knap/"],
        "excluded": [".git", ".venv"],
    }
    (schema_dir / "folders.yaml").write_text(yaml.dump(config))
    (templates_dir / "folders.yaml.template").write_text(yaml.dump(config))
    categories = {
        "required_fields": ["title", "source_url", "date_farmed", "category"],
        "optional_fields": ["website", "address", "phone", "hours", "email"],
        "categories": {
            "transcript": {
                "required_fields": ["channel"],
                "analysis_label": "Notes",
                "analysis_todo": "<!-- TODO -->",
            }
        },
    }
    (templates_dir / "categories.yaml.template").write_text(yaml.dump(categories))


def _make_wiki_file(path: Path, title: str = "Test", links: list | None = None):
    """Create a wiki file with frontmatter."""
    fm = {"title": title, "category": "transcript"}
    if links:
        fm["links"] = links
    content = f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---\n\n# {title}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestFixIndex:
    def test_fixes_unlisted_page(self, tmp_path, monkeypatch):
        """Page with Parent link to index but not listed gets added."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        # Index has no entry for page
        (cat_dir / "index.md").write_text("# Transcripts\n")
        # Page has Parent link to index
        _make_wiki_file(
            cat_dir / "page.md", "Page",
            links=[{"target": "[Index](wiki/transcripts/index.md)", "type": "Parent"}],
        )

        fixes = fix_index()

        assert len(fixes) == 1
        assert "fixed" in fixes[0]
        # Verify page is now in index body
        body = (cat_dir / "index.md").read_text()
        assert "- [Page](page.md)" in body

    def test_no_fix_for_already_listed_page(self, tmp_path, monkeypatch):
        """Page already listed in index is not fixed."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        # Index already has entry for page
        (cat_dir / "index.md").write_text("# Transcripts\n- [Page](page.md)\n")
        _make_wiki_file(
            cat_dir / "page.md", "Page",
            links=[{"target": "[Index](wiki/transcripts/index.md)", "type": "Parent"}],
        )

        fixes = fix_index()

        assert fixes == []

    def test_fixes_multiple_unlisted_pages(self, tmp_path, monkeypatch):
        """Multiple unlisted pages are all fixed."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        (cat_dir / "index.md").write_text("# Transcripts\n")
        _make_wiki_file(
            cat_dir / "page1.md", "Page 1",
            links=[{"target": "[Index](wiki/transcripts/index.md)", "type": "Parent"}],
        )
        _make_wiki_file(
            cat_dir / "page2.md", "Page 2",
            links=[{"target": "[Index](wiki/transcripts/index.md)", "type": "Parent"}],
        )

        fixes = fix_index()

        assert len(fixes) == 2

    def test_skips_page_with_parent_to_non_index(self, tmp_path, monkeypatch):
        """Page with Parent link to non-index file is skipped."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n")
        # Parent link points to another page, not an index
        _make_wiki_file(
            cat_dir / "page.md", "Page",
            links=[{"target": "[Other](wiki/transcripts/other.md)", "type": "Parent"}],
        )
        _make_wiki_file(cat_dir / "other.md", "Other")

        fixes = fix_index()

        assert fixes == []

    def test_empty_wiki_returns_no_fixes(self, tmp_path, monkeypatch):
        """Empty wiki returns no fixes."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        (tmp_path / "wiki").mkdir()

        fixes = fix_index()

        assert fixes == []

    def test_page_without_parent_link_skipped(self, tmp_path, monkeypatch):
        """Page without Parent link is skipped."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n")
        (cat_dir / "index.md").write_text("# Transcripts\n")
        _make_wiki_file(cat_dir / "page.md", "Page")  # No links

        fixes = fix_index()

        assert fixes == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
