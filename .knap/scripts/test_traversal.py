#!/usr/bin/env python3
"""Tests for traversal.py."""

import pytest
from pathlib import Path

import yaml

from traversal import traverse_files


def _setup_repo(tmp_path):
    """Create minimal repo structure with folders.yaml."""
    schema_dir = tmp_path / ".knap" / "schema"
    schema_dir.mkdir(parents=True)
    templates_dir = schema_dir / "templates"
    templates_dir.mkdir()
    config = {
        "working": ["wiki/"],
        "system": [".knap/"],
        "excluded": [".git", ".venv", "docs/brainstorms"],
    }
    (schema_dir / "folders.yaml").write_text(yaml.dump(config))
    (templates_dir / "folders.yaml.template").write_text(yaml.dump(config))


class TestTraverseFiles:
    def test_returns_all_files_in_working_and_system(self, tmp_path, monkeypatch):
        """traverse_files() returns all files in working + system folders."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)

        # Create files in working folder
        wiki_dir = tmp_path / "wiki" / "transcripts"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / "page.md").write_text("# Page")
        (wiki_dir / "other.md").write_text("# Other")

        # Create files in system folder
        knap_dir = tmp_path / ".knap" / "scripts"
        knap_dir.mkdir(parents=True)
        (knap_dir / "lint.py").write_text("# lint")

        result = traverse_files()
        paths = [str(p) for p in result]

        assert "wiki/transcripts/page.md" in paths
        assert "wiki/transcripts/other.md" in paths
        assert ".knap/scripts/lint.py" in paths

    def test_indexed_only_returns_files_from_folders_with_index(self, tmp_path, monkeypatch):
        """traverse_files(indexed_only=True) only returns from indexed folders."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)

        # Working folder with index
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / "index.md").write_text("# Index")
        (wiki_dir / "page.md").write_text("# Page")

        # System folder already has folders.yaml from _setup_repo; add ROUTER
        knap_dir = tmp_path / ".knap"
        (knap_dir / "ROUTER.md").write_text("# Router")
        (knap_dir / "script.py").write_text("# Script")

        result = traverse_files(indexed_only=True)
        paths = [str(p) for p in result]

        assert "wiki/index.md" in paths
        assert "wiki/page.md" in paths
        assert ".knap/ROUTER.md" in paths
        assert ".knap/script.py" in paths

    def test_indexed_only_skips_unindexed_folders(self, tmp_path, monkeypatch):
        """Folders without index are skipped when indexed_only=True."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)

        # Working folder WITHOUT index
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / "page.md").write_text("# Page")

        # System folder exists from _setup_repo but has no ROUTER.md
        result = traverse_files(indexed_only=True)
        assert result == []

    def test_excluded_folders_not_included(self, tmp_path, monkeypatch):
        """Excluded folders are not traversed."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)

        # Excluded folder
        git_dir = tmp_path / ".git"
        git_dir.mkdir(parents=True)
        (git_dir / "config").write_text("git config")

        # Working folder
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / "page.md").write_text("# Page")

        result = traverse_files()
        paths = [str(p) for p in result]
        assert ".git/config" not in paths
        assert "wiki/page.md" in paths

    def test_empty_directories_return_empty_list(self, tmp_path, monkeypatch):
        """Empty working dirs return no files (system has folders.yaml from setup)."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)

        (tmp_path / "wiki").mkdir(parents=True)

        result = traverse_files()
        # Only folders.yaml from _setup_repo should appear
        paths = [str(p) for p in result]
        assert "wiki/index.md" not in paths
        assert all("wiki/" not in p for p in paths)

    def test_nested_directories_traversed_recursively(self, tmp_path, monkeypatch):
        """Nested subdirectories are included."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)

        deep = tmp_path / "wiki" / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "deep.md").write_text("# Deep")

        result = traverse_files()
        paths = [str(p) for p in result]
        assert "wiki/a/b/c/deep.md" in paths

    def test_non_markdown_files_included(self, tmp_path, monkeypatch):
        """Non-.md files are included (all files, not just markdown)."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)

        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir(parents=True)
        (wiki_dir / "page.md").write_text("# Page")
        (wiki_dir / "data.json").write_text("{}")
        (wiki_dir / "image.png").write_text("png")

        result = traverse_files()
        paths = [str(p) for p in result]
        assert "wiki/data.json" in paths
        assert "wiki/image.png" in paths
