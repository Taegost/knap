#!/usr/bin/env python3
"""Tests for check_index.py."""

import pytest
from pathlib import Path

import yaml

from check_index import check_index, fix_missing_parent_links


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
    # Create categories.yaml template for schema.py
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


class TestCheckIndex:
    def test_master_index_missing_returns_error(self, tmp_path, monkeypatch):
        """Missing master index is an error."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        (tmp_path / "wiki").mkdir(parents=True)
        issues = check_index()
        assert any("missing" in i and "index.md" in i for i in issues)

    def test_category_with_pages_but_no_index_returns_error(self, tmp_path, monkeypatch):
        """Category dir with pages but no index.md is an error."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n")
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir()
        (cat_dir / "page.md").write_text("# Page")
        issues = check_index()
        assert any("missing" in i and "transcripts/index.md" in i for i in issues)

    def test_category_index_ghost_entry_returns_error(self, tmp_path, monkeypatch):
        """Category index listing a page that doesn't exist is flagged."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        (cat_dir / "index.md").write_text("# Transcripts\n- [Ghost](ghost.md)\n")
        issues = check_index()
        assert any("index ghost" in i and "ghost.md" in i for i in issues)

    def test_category_with_unlisted_page_returns_error(self, tmp_path, monkeypatch):
        """Page exists but not listed in category index is flagged."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        (cat_dir / "index.md").write_text("# Transcripts\n")
        (cat_dir / "page.md").write_text("# Page")
        issues = check_index()
        assert any("index missing" in i and "page.md" in i for i in issues)

    def test_master_index_missing_link_to_category_index(self, tmp_path, monkeypatch):
        """Master index missing link to category index is flagged."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n")
        (cat_dir / "index.md").write_text("# Transcripts\n")
        issues = check_index()
        assert any("master index missing link" in i for i in issues)

    def test_file_without_parent_link_returns_error(self, tmp_path, monkeypatch):
        """File in indexed category without Parent link is flagged (I6)."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_wiki_file(cat_dir / "index.md", "Index")
        _make_wiki_file(cat_dir / "page.md", "Page")  # No Parent link
        issues = check_index()
        assert any("missing Parent link" in i for i in issues)

    def test_file_with_parent_link_passes(self, tmp_path, monkeypatch):
        """File with Parent link passes the check (I6)."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_wiki_file(cat_dir / "index.md", "Index")
        _make_wiki_file(
            cat_dir / "page.md", "Page",
            links=[{"target": "[Index](wiki/transcripts/index.md)", "type": "Parent"}],
        )
        issues = check_index()
        parent_issues = [i for i in issues if "Parent" in i]
        assert parent_issues == []

    def test_all_checks_pass_on_clean_wiki(self, tmp_path, monkeypatch):
        """Clean wiki returns empty issue list."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        (cat_dir / "index.md").write_text("# Transcripts\n- [Page](page.md)\n")
        _make_wiki_file(
            cat_dir / "page.md", "Page",
            links=[{"target": "[Index](wiki/transcripts/index.md)", "type": "Parent"}],
        )
        issues = check_index()
        assert issues == []

    def test_index_exempt_from_parent_requirement(self, tmp_path, monkeypatch):
        """Index files are exempt from the Parent link requirement."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_wiki_file(cat_dir / "index.md", "Index")  # No Parent link — exempt
        issues = check_index()
        parent_issues = [i for i in issues if "Parent" in i and "index.md" in i]
        assert parent_issues == []


class TestFixMissingParentLinks:
    def test_fixes_missing_parent_link(self, tmp_path, monkeypatch):
        """Auto-fix adds Parent link to page missing it."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_wiki_file(cat_dir / "index.md", "Index")
        _make_wiki_file(cat_dir / "page.md", "Page")  # No Parent link

        fixes = fix_missing_parent_links()

        assert len(fixes) == 1
        assert "fixed" in fixes[0]
        # Verify the link was added
        import yaml
        data = yaml.safe_load((cat_dir / "page.md").read_text().split("---")[1])
        assert any(l["type"] == "Parent" for l in data.get("links", []))

    def test_fixes_multiple_missing_parent_links(self, tmp_path, monkeypatch):
        """Auto-fix adds Parent links to multiple pages."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_wiki_file(cat_dir / "index.md", "Index")
        _make_wiki_file(cat_dir / "page1.md", "Page 1")
        _make_wiki_file(cat_dir / "page2.md", "Page 2")

        fixes = fix_missing_parent_links()

        assert len(fixes) == 2

    def test_no_fixes_when_all_have_parent(self, tmp_path, monkeypatch):
        """No fixes when all pages already have Parent links."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_wiki_file(cat_dir / "index.md", "Index")
        _make_wiki_file(
            cat_dir / "page.md", "Page",
            links=[{"target": "[Index](wiki/transcripts/index.md)", "type": "Parent"}],
        )

        fixes = fix_missing_parent_links()

        assert fixes == []

    def test_fix_adds_page_to_index_body(self, tmp_path, monkeypatch):
        """Auto-fix also adds page to index body (via index reciprocity)."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_wiki_file(cat_dir / "index.md", "Index")
        _make_wiki_file(cat_dir / "page.md", "Page")

        fix_missing_parent_links()

        # Verify page appears in index body
        body = (cat_dir / "index.md").read_text()
        assert "- [Page](page.md)" in body
