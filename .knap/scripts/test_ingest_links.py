#!/usr/bin/env python3
"""Tests for IngestedFrom link generation in ingest.py."""

import pytest
import yaml

from ingest import build_wiki_page


class TestBuildWikiPageLinks:
    def test_ingested_from_link_present(self):
        """Wiki page always has an IngestedFrom link."""
        fm = {"title": "Test", "category": "transcript"}
        result = build_wiki_page(fm, "raw/transcripts/test.md", "2026-06-20")
        data = yaml.safe_load(result.split("---")[1])
        assert "links" in data
        ingested = [l for l in data["links"] if l.get("type") == "IngestedFrom"]
        assert len(ingested) == 1
        assert "test.md" in ingested[0]["target"]
        assert "raw/transcripts/test.md" in ingested[0]["target"]

    def test_no_source_field(self):
        """Wiki page no longer has a source field."""
        fm = {"title": "Test", "category": "transcript"}
        result = build_wiki_page(fm, "raw/transcripts/test.md", "2026-06-20")
        data = yaml.safe_load(result.split("---")[1])
        assert "source" not in data

    def test_copies_links_from_raw(self):
        """Links from raw frontmatter are copied to wiki frontmatter."""
        fm = {
            "title": "Test",
            "category": "transcript",
            "links": [
                {"target": "[Other](wiki/other.md)", "type": "Related"}
            ],
        }
        result = build_wiki_page(fm, "raw/transcripts/test.md", "2026-06-20")
        data = yaml.safe_load(result.split("---")[1])
        assert len(data["links"]) == 2
        # First is IngestedFrom
        assert data["links"][0]["type"] == "IngestedFrom"
        # Second is the copied link
        assert data["links"][1]["target"] == "[Other](wiki/other.md)"
        assert data["links"][1]["type"] == "Related"

    def test_no_links_in_raw(self):
        """Wiki page with no links in raw has IngestedFrom only."""
        fm = {"title": "Test", "category": "transcript"}
        result = build_wiki_page(fm, "raw/transcripts/test.md", "2026-06-20")
        data = yaml.safe_load(result.split("---")[1])
        assert len(data["links"]) == 1
        assert data["links"][0]["type"] == "IngestedFrom"

    def test_ingested_from_uses_repo_root_relative_path(self):
        """IngestedFrom target uses repo-root-relative path, not ../raw/."""
        fm = {"title": "Test", "category": "transcript"}
        result = build_wiki_page(fm, "raw/transcripts/test.md", "2026-06-20")
        data = yaml.safe_load(result.split("---")[1])
        target = data["links"][0]["target"]
        assert "../" not in target
        assert "raw/transcripts/test.md" in target

    def test_multiple_raw_links_preserved(self):
        """Multiple links from raw are all preserved after IngestedFrom."""
        fm = {
            "title": "Test",
            "category": "transcript",
            "links": [
                {"target": "[A](wiki/a.md)", "type": "Parent"},
                {"target": "[B](wiki/b.md)", "type": "Child"},
            ],
        }
        result = build_wiki_page(fm, "raw/transcripts/test.md", "2026-06-20")
        data = yaml.safe_load(result.split("---")[1])
        assert len(data["links"]) == 3
        assert data["links"][0]["type"] == "IngestedFrom"
        assert data["links"][1]["type"] == "Parent"
        assert data["links"][2]["type"] == "Child"

    def test_serialization_produces_valid_yaml(self):
        """The entire frontmatter block is valid YAML."""
        fm = {
            "title": "Test",
            "category": "transcript",
            "links": [
                {"target": "[Page](wiki/page.md)", "type": "Related"},
            ],
        }
        result = build_wiki_page(fm, "raw/transcripts/test.md", "2026-06-20")
        # Extract frontmatter between --- markers
        parts = result.split("---")
        assert len(parts) >= 3
        data = yaml.safe_load(parts[1])
        assert isinstance(data, dict)
        assert isinstance(data["links"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
