#!/usr/bin/env python3
"""Tests for migrate_index_frontmatter.py."""

import pytest
import yaml
from pathlib import Path

from migrate_index_frontmatter import migrate_index_frontmatter, _has_frontmatter


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


def _make_index(path: Path, has_fm: bool = False):
    """Create an index file with or without frontmatter."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if has_fm:
        fm = {"title": "Index", "description": "Test"}
        content = f"---\n{yaml.dump(fm)}---\n\n# Index\n"
    else:
        content = "# Index\n\nSome content.\n"
    path.write_text(content)


class TestMigrateIndexFrontmatter:
    def test_adds_frontmatter_to_category_index(self, tmp_path, monkeypatch):
        """Category index without frontmatter gets it added."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        _make_index(cat_dir / "index.md")

        actions = migrate_index_frontmatter()

        assert any("added frontmatter" in a for a in actions)
        parsed = yaml.safe_load((cat_dir / "index.md").read_text().split("---")[1])
        assert parsed is not None
        assert "description" in parsed
        assert any(l["type"] == "Parent" for l in parsed.get("links", []))

    def test_category_index_parent_points_to_master(self, tmp_path, monkeypatch):
        """Category index Parent link points to wiki/index.md."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        _make_index(cat_dir / "index.md")

        migrate_index_frontmatter()

        parsed = yaml.safe_load((cat_dir / "index.md").read_text().split("---")[1])
        parent_links = [l for l in parsed.get("links", []) if l["type"] == "Parent"]
        assert len(parent_links) == 1
        assert "wiki/index.md" in parent_links[0]["target"]

    def test_adds_frontmatter_to_master_index(self, tmp_path, monkeypatch):
        """Master index without frontmatter gets it added."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        _make_index(wiki / "index.md")

        actions = migrate_index_frontmatter()

        assert any("wiki/index.md" in a and "added" in a for a in actions)
        parsed = yaml.safe_load((wiki / "index.md").read_text().split("---")[1])
        assert parsed is not None

    def test_master_index_parent_points_to_router(self, tmp_path, monkeypatch):
        """Master index Parent link points to .knap/ROUTER.md."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        _make_index(wiki / "index.md")

        migrate_index_frontmatter()

        parsed = yaml.safe_load((wiki / "index.md").read_text().split("---")[1])
        parent_links = [l for l in parsed.get("links", []) if l["type"] == "Parent"]
        assert len(parent_links) == 1
        assert ".knap/ROUTER.md" in parent_links[0]["target"]

    def test_adds_frontmatter_to_router(self, tmp_path, monkeypatch):
        """ROUTER.md without frontmatter gets it added (no Parent link)."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        knap_dir = tmp_path / ".knap"
        knap_dir.mkdir(parents=True, exist_ok=True)
        _make_index(knap_dir / "ROUTER.md")

        actions = migrate_index_frontmatter()

        assert any("ROUTER.md" in a and "added" in a for a in actions)
        parsed = yaml.safe_load((knap_dir / "ROUTER.md").read_text().split("---")[1])
        assert parsed is not None
        # ROUTER has no Parent link (it's the root)
        assert "links" not in parsed or not any(
            l["type"] == "Parent" for l in parsed.get("links", [])
        )

    def test_skips_index_with_existing_frontmatter(self, tmp_path, monkeypatch):
        """Index with frontmatter is skipped."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        _make_index(cat_dir / "index.md", has_fm=True)

        actions = migrate_index_frontmatter()

        assert any("skip" in a for a in actions)
        assert not any("added" in a for a in actions)

    def test_dry_run_shows_preview(self, tmp_path, monkeypatch):
        """Dry-run shows what would be done without writing."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        _make_index(cat_dir / "index.md")

        actions = migrate_index_frontmatter(dry_run=True)

        assert any("would add" in a for a in actions)
        # Verify file was NOT modified
        content = (cat_dir / "index.md").read_text()
        assert not content.startswith("---")

    def test_preserves_existing_body_content(self, tmp_path, monkeypatch):
        """Existing body content is preserved after adding frontmatter."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        cat_index = cat_dir / "index.md"
        cat_index.write_text("# Transcripts\n\nSome existing content.\n")

        migrate_index_frontmatter()

        content = cat_index.read_text()
        assert "# Transcripts" in content
        assert "Some existing content." in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
