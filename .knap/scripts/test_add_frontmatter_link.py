#!/usr/bin/env python3
"""Tests for add_frontmatter_link.py."""

import pytest
import yaml
from pathlib import Path

from add_frontmatter_link import _write_frontmatter_link, add_frontmatter_link


def _make_file(path: Path, fm: dict, body: str = "\n# Test\n") -> str:
    """Create a markdown file with frontmatter."""
    content = f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---{body}"
    path.write_text(content)
    return str(path)


class TestWriteFrontmatterLink:
    def test_add_new_link_to_empty(self, tmp_path):
        """Adding a link to a file with no links creates the links list."""
        filepath = _make_file(tmp_path / "test.md", {"title": "Test"})
        modified = _write_frontmatter_link(filepath, "[Other](other.md)", "Related")
        assert modified is True
        data = yaml.safe_load((tmp_path / "test.md").read_text().split("---")[1])
        assert len(data["links"]) == 1
        assert data["links"][0]["target"] == "[Other](other.md)"
        assert data["links"][0]["type"] == "Related"

    def test_skip_existing_same_type(self, tmp_path):
        """Link with same target and type is a no-op."""
        fm = {"title": "Test", "links": [{"target": "[Other](other.md)", "type": "Related"}]}
        filepath = _make_file(tmp_path / "test.md", fm)
        modified = _write_frontmatter_link(filepath, "[Other](other.md)", "Related")
        assert modified is False

    def test_update_existing_different_type(self, tmp_path):
        """Link with same target but different type updates the type."""
        fm = {"title": "Test", "links": [{"target": "[Other](other.md)", "type": "Related"}]}
        filepath = _make_file(tmp_path / "test.md", fm)
        modified = _write_frontmatter_link(filepath, "[Other](other.md)", "Parent")
        assert modified is True
        data = yaml.safe_load((tmp_path / "test.md").read_text().split("---")[1])
        assert data["links"][0]["type"] == "Parent"

    def test_append_to_existing_links(self, tmp_path):
        """New link is appended to existing links list."""
        fm = {"title": "Test", "links": [{"target": "[A](a.md)", "type": "Related"}]}
        filepath = _make_file(tmp_path / "test.md", fm)
        modified = _write_frontmatter_link(filepath, "[B](b.md)", "Parent")
        assert modified is True
        data = yaml.safe_load((tmp_path / "test.md").read_text().split("---")[1])
        assert len(data["links"]) == 2
        assert data["links"][1]["target"] == "[B](b.md)"

    def test_preserves_body_content(self, tmp_path):
        """Body content is preserved after link addition."""
        body = "\n# Title\n\nSome body content.\n"
        filepath = _make_file(tmp_path / "test.md", {"title": "Test"}, body)
        _write_frontmatter_link(filepath, "[Other](other.md)", "Related")
        content = (tmp_path / "test.md").read_text()
        assert "# Title" in content
        assert "Some body content." in content


class TestAddFrontmatterLink:
    def test_reciprocal_writes_to_target(self, tmp_path, monkeypatch):
        """Reciprocal link is written to the target file."""
        monkeypatch.chdir(tmp_path)
        source = _make_file(tmp_path / "source.md", {"title": "Source"})
        _make_file(tmp_path / "target.md", {"title": "Target"})
        add_frontmatter_link(source, "[Target](target.md)", "Parent")
        # Check source has Parent link
        data = yaml.safe_load((tmp_path / "source.md").read_text().split("---")[1])
        assert any(l["type"] == "Parent" for l in data["links"])
        # Check target has Child reciprocal
        data2 = yaml.safe_load((tmp_path / "target.md").read_text().split("---")[1])
        assert any(l["type"] == "Child" for l in data2["links"])

    def test_no_reciprocal_for_non_repo_target(self, tmp_path, monkeypatch):
        """No reciprocal when target is not a markdown file in repo."""
        monkeypatch.chdir(tmp_path)
        source = _make_file(tmp_path / "source.md", {"title": "Source"})
        add_frontmatter_link(source, "[External](https://example.com)", "Related")
        # Source should have the link
        data = yaml.safe_load((tmp_path / "source.md").read_text().split("---")[1])
        assert len(data["links"]) == 1

    def test_no_reciprocal_for_nonexistent_target(self, tmp_path, monkeypatch):
        """No reciprocal when target file doesn't exist."""
        monkeypatch.chdir(tmp_path)
        source = _make_file(tmp_path / "source.md", {"title": "Source"})
        add_frontmatter_link(source, "[Missing](missing.md)", "Parent")
        # Source should still have the link (with warning)
        data = yaml.safe_load((tmp_path / "source.md").read_text().split("---")[1])
        assert len(data["links"]) == 1

    def test_ingested_from_no_reciprocal(self, tmp_path, monkeypatch):
        """IngestedFrom has no reciprocal (IngestedTo) on raw files by default."""
        monkeypatch.chdir(tmp_path)
        source = _make_file(tmp_path / "source.md", {"title": "Source"})
        _make_file(tmp_path / "target.md", {"title": "Target"})
        # IngestedFrom → IngestedTo is a valid pair, but target is a wiki file
        # so it should still write reciprocal
        add_frontmatter_link(source, "[Target](target.md)", "IngestedFrom")
        data = yaml.safe_load((tmp_path / "target.md").read_text().split("---")[1])
        assert any(l["type"] == "IngestedTo" for l in data["links"])

    def test_parent_link_to_index_adds_body_entry(self, tmp_path, monkeypatch):
        """Adding Parent link to index.md adds page to index body, not Child reciprocal."""
        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        source = _make_file(wiki_dir / "page.md", {"title": "Page"})
        _make_file(wiki_dir / "index.md", {"title": "Index"}, "\n# Index\n")
        add_frontmatter_link(source, "[Index](wiki/transcripts/index.md)", "Parent")
        # Source should have Parent link
        data = yaml.safe_load((wiki_dir / "page.md").read_text().split("---")[1])
        assert any(l["type"] == "Parent" for l in data["links"])
        # Index should NOT have Child reciprocal
        data2 = yaml.safe_load((wiki_dir / "index.md").read_text().split("---")[1])
        links = data2.get("links", [])
        assert not any(l.get("type") == "Child" for l in links)
        # Index body should contain the page entry
        body = (wiki_dir / "index.md").read_text()
        assert "- [Page](page.md)" in body

    def test_parent_link_to_router_adds_body_entry(self, tmp_path, monkeypatch):
        """Adding Parent link to ROUTER.md adds page to ROUTER body, not Child reciprocal."""
        monkeypatch.chdir(tmp_path)
        knap_dir = tmp_path / ".knap"
        knap_dir.mkdir(parents=True)
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir(parents=True)
        source = _make_file(wiki_dir / "page.md", {"title": "Page"})
        _make_file(knap_dir / "ROUTER.md", {"title": "Router"}, "\n# Router\n")
        add_frontmatter_link(source, "[Router](.knap/ROUTER.md)", "Parent")
        # Index should NOT have Child reciprocal
        data = yaml.safe_load((knap_dir / "ROUTER.md").read_text().split("---")[1])
        links = data.get("links", [])
        assert not any(l.get("type") == "Child" for l in links)
        # ROUTER body should contain the page entry
        body = (knap_dir / "ROUTER.md").read_text()
        assert "- [Page](../wiki/page.md)" in body

    def test_index_body_entry_uses_title_from_frontmatter(self, tmp_path, monkeypatch):
        """Index body entry uses page title from frontmatter."""
        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        source = _make_file(wiki_dir / "my-page.md", {"title": "My Custom Title"})
        _make_file(wiki_dir / "index.md", {"title": "Index"}, "\n# Index\n")
        add_frontmatter_link(source, "[Index](wiki/transcripts/index.md)", "Parent")
        body = (wiki_dir / "index.md").read_text()
        assert "- [My Custom Title](my-page.md)" in body

    def test_index_body_entry_falls_back_to_filename(self, tmp_path, monkeypatch):
        """Index body entry uses filename stem when title is missing."""
        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        source = _make_file(wiki_dir / "my-page.md", {})
        _make_file(wiki_dir / "index.md", {"title": "Index"}, "\n# Index\n")
        add_frontmatter_link(source, "[Index](wiki/transcripts/index.md)", "Parent")
        body = (wiki_dir / "index.md").read_text()
        assert "- [my-page](my-page.md)" in body

    def test_no_duplicate_index_body_entry(self, tmp_path, monkeypatch):
        """Page already listed in index body does not get a duplicate entry."""
        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        source = _make_file(wiki_dir / "page.md", {"title": "Page"})
        _make_file(wiki_dir / "index.md", {"title": "Index"}, "\n# Index\n- [Page](page.md)\n")
        add_frontmatter_link(source, "[Index](wiki/transcripts/index.md)", "Parent")
        body = (wiki_dir / "index.md").read_text()
        assert body.count("- [Page](page.md)") == 1

    def test_related_link_to_index_no_reciprocal(self, tmp_path, monkeypatch):
        """Adding Related link to index file has no reciprocal (Related has no pair)."""
        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        source = _make_file(wiki_dir / "page.md", {"title": "Page"})
        _make_file(wiki_dir / "index.md", {"title": "Index"})
        add_frontmatter_link(source, "[Index](wiki/transcripts/index.md)", "Related")
        # Source should have the link
        data = yaml.safe_load((wiki_dir / "page.md").read_text().split("---")[1])
        assert any(l["type"] == "Related" for l in data["links"])
        # Index should NOT have a reciprocal (Related has no pair)
        data2 = yaml.safe_load((wiki_dir / "index.md").read_text().split("---")[1])
        links = data2.get("links", [])
        assert len(links) == 0

    def test_parent_link_to_master_index_adds_body_entry(self, tmp_path, monkeypatch):
        """Adding Parent link to wiki/index.md adds page to master index body."""
        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir(parents=True)
        cat_dir = wiki_dir / "transcripts"
        cat_dir.mkdir()
        source = _make_file(cat_dir / "page.md", {"title": "Page"})
        _make_file(wiki_dir / "index.md", {"title": "Wiki Index"}, "\n# Wiki Index\n")
        add_frontmatter_link(source, "[Wiki Index](wiki/index.md)", "Parent")
        body = (wiki_dir / "index.md").read_text()
        assert "- [Page](transcripts/page.md)" in body

    def test_supersedes_reciprocal_still_works_for_index(self, tmp_path, monkeypatch):
        """Adding Supersedes link to index file still generates reciprocal (only Child is exempt)."""
        monkeypatch.chdir(tmp_path)
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        source = _make_file(wiki_dir / "page.md", {"title": "Page"})
        _make_file(wiki_dir / "index.md", {"title": "Index"})
        add_frontmatter_link(source, "[Index](wiki/transcripts/index.md)", "Supersedes")
        # Index should have SupersededBy reciprocal (only Child is exempt)
        data = yaml.safe_load((wiki_dir / "index.md").read_text().split("---")[1])
        assert any(l["type"] == "SupersededBy" for l in data.get("links", []))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
