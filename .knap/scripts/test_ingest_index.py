#!/usr/bin/env python3
"""Tests for index frontmatter creation in ingest.py."""

import pytest
import yaml
from pathlib import Path

from ingest import _ensure_category_index, build_wiki_page


class TestEnsureCategoryIndex:
    def test_creates_index_with_frontmatter(self, tmp_path):
        """New index file has frontmatter with Parent link and description."""
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        wiki_path = str(wiki_dir / "test.md")

        _ensure_category_index("transcripts", wiki_path)

        index = wiki_dir / "index.md"
        assert index.exists()
        content = index.read_text()
        assert content.startswith("---")
        parsed = yaml.safe_load(content.split("---")[1])
        assert "description" in parsed
        assert "links" in parsed
        parent_links = [l for l in parsed["links"] if l["type"] == "Parent"]
        assert len(parent_links) == 1
        assert "wiki/index.md" in parent_links[0]["target"]

    def test_description_populated_with_category(self, tmp_path):
        """Description field uses category name."""
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        wiki_path = str(wiki_dir / "test.md")

        _ensure_category_index("transcripts", wiki_path)

        index = wiki_dir / "index.md"
        parsed = yaml.safe_load(index.read_text().split("---")[1])
        assert "transcripts" in parsed["description"].lower()

    def test_parent_link_points_to_master_index(self, tmp_path):
        """Category index Parent link points to wiki/index.md."""
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        wiki_path = str(wiki_dir / "test.md")

        _ensure_category_index("transcripts", wiki_path)

        index = wiki_dir / "index.md"
        parsed = yaml.safe_load(index.read_text().split("---")[1])
        parent = [l for l in parsed["links"] if l["type"] == "Parent"][0]
        assert "wiki/index.md" in parent["target"]

    def test_existing_index_not_overwritten(self, tmp_path):
        """Existing index file is not modified."""
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        index = wiki_dir / "index.md"
        original = "# Original\n"
        index.write_text(original)
        wiki_path = str(wiki_dir / "test.md")

        _ensure_category_index("transcripts", wiki_path)

        assert index.read_text() == original


class TestIngestParentLink:
    def test_ingest_adds_parent_link_to_wiki_page(self, tmp_path, monkeypatch):
        """Ingested wiki page gets a Parent link to category index."""
        monkeypatch.chdir(tmp_path)
        # Setup minimal schema
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
            "optional_fields": [],
            "categories": {
                "transcript": {
                    "required_fields": ["channel"],
                    "analysis_label": "Notes",
                    "analysis_todo": "<!-- TODO -->",
                }
            },
        }
        (templates_dir / "categories.yaml.template").write_text(yaml.dump(categories))

        # Create raw file
        raw_dir = tmp_path / "raw" / "transcripts"
        raw_dir.mkdir(parents=True)
        raw = raw_dir / "test.md"
        raw_fm = {
            "title": "Test Page",
            "source_url": "https://example.com",
            "date_farmed": "2026-06-21",
            "category": "transcript",
            "channel": "Test Channel",
        }
        raw.write_text(f"---\n{yaml.dump(raw_fm)}---\n\n# Test\n")

        # Create master index
        (tmp_path / "wiki").mkdir()
        (tmp_path / "wiki" / "index.md").write_text("# Wiki\n")

        # Ingest using relative path (how the CLI would call it)
        from ingest import ingest
        result = ingest("raw/transcripts/test.md")

        assert result is True
        # Verify wiki page has Parent link
        wiki = tmp_path / "wiki" / "transcripts" / "test.md"
        data = yaml.safe_load(wiki.read_text().split("---")[1])
        parent_links = [l for l in data.get("links", []) if l.get("type") == "Parent"]
        assert len(parent_links) == 1
        assert "index.md" in parent_links[0]["target"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
