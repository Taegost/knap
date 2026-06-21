#!/usr/bin/env python3
"""Tests for find_orphans.py."""

import pytest
from pathlib import Path

import yaml

from find_orphans import find_orphans


def _setup_repo(tmp_path):
    """Create minimal repo structure with folders.yaml."""
    schema_dir = tmp_path / ".knap" / "schema"
    schema_dir.mkdir(parents=True)
    config = {
        "working": ["wiki/"],
        "system": [".knap/"],
        "excluded": [".git", ".venv"],
    }
    (schema_dir / "folders.yaml").write_text(yaml.dump(config))


def _make_file(path: Path, fm: dict, body: str = "\n# Test\n"):
    """Create a markdown file with frontmatter."""
    content = f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestFindOrphans:
    def test_file_with_frontmatter_link_to_it_is_not_orphan(self, tmp_path, monkeypatch):
        """File that another file links to via frontmatter is not an orphan."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_file(cat_dir / "index.md", {"title": "Index"})
        # source.md links to target.md via frontmatter
        _make_file(
            cat_dir / "source.md",
            {"title": "Source", "links": [{"target": "[Target](wiki/transcripts/target.md)", "type": "Related"}]},
        )
        _make_file(cat_dir / "target.md", {"title": "Target"})
        orphans = find_orphans()
        assert "wiki/transcripts/target.md" not in orphans

    def test_file_with_body_markdown_link_is_not_orphan(self, tmp_path, monkeypatch):
        """File with body markdown link pointing to it is not an orphan."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_file(cat_dir / "index.md", {"title": "Index"})
        _make_file(cat_dir / "source.md", {"title": "Source"}, body="\n[Link](target.md)\n")
        _make_file(cat_dir / "target.md", {"title": "Target"})
        orphans = find_orphans()
        assert "wiki/transcripts/target.md" not in orphans

    def test_file_with_wikilink_is_not_orphan(self, tmp_path, monkeypatch):
        """File with wikilink pointing to it is not an orphan."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_file(cat_dir / "index.md", {"title": "Index"})
        _make_file(cat_dir / "source.md", {"title": "Source"}, body="\n[[Target]]\n")
        _make_file(cat_dir / "Target.md", {"title": "Target"})
        orphans = find_orphans()
        assert "wiki/transcripts/Target.md" not in orphans

    def test_file_with_no_incoming_links_is_orphan(self, tmp_path, monkeypatch):
        """File with no incoming links is an orphan."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_file(cat_dir / "index.md", {"title": "Index"})
        _make_file(cat_dir / "orphan.md", {"title": "Orphan"})
        orphans = find_orphans()
        assert "wiki/transcripts/orphan.md" in orphans

    def test_excluded_folder_files_not_flagged(self, tmp_path, monkeypatch):
        """Files in excluded folders are not flagged as orphans."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n")
        # Excluded folder
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")
        orphans = find_orphans()
        assert not any(".git" in o for o in orphans)

    def test_empty_wiki_returns_no_orphans(self, tmp_path, monkeypatch):
        """Empty wiki returns no orphans."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n")
        orphans = find_orphans()
        assert orphans == []
