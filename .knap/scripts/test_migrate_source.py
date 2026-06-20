#!/usr/bin/env python3
"""Tests for source → IngestedFrom migration in convert_frontmatter.py."""

import pytest
import shutil
import yaml
from pathlib import Path

from convert_frontmatter import migrate_source_field


def _make_file(path: Path, fm: dict, body: str = "\n# Test\n") -> str:
    """Create a markdown file with frontmatter."""
    content = f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---{body}"
    path.write_text(content)
    return str(path)


def _setup_repo(tmp_path):
    """Set up minimal repo structure with schema for CWD-relative imports."""
    knap_dir = tmp_path / ".knap" / "schema"
    knap_dir.mkdir(parents=True)
    shutil.copy(
        Path(__file__).resolve().parent.parent / "schema" / "categories.yaml",
        knap_dir / "categories.yaml",
    )


class TestMigrateSourceField:
    def test_converts_source_to_ingested_from(self, tmp_path, monkeypatch):
        """source field is converted to IngestedFrom link."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        raw = tmp_path / "raw" / "transcripts"
        raw.mkdir(parents=True)
        (raw / "test.md").write_text("# Raw")
        wiki = tmp_path / "wiki" / "transcripts"
        wiki.mkdir(parents=True)
        fm = {"title": "Test", "source": "[test.md](../raw/transcripts/test.md)"}
        filepath = _make_file(wiki / "test.md", fm)
        status, detail = migrate_source_field(filepath)
        assert status == "migrated"
        data = yaml.safe_load(Path(filepath).read_text().split("---")[1])
        assert "source" not in data
        assert any(l["type"] == "IngestedFrom" for l in data["links"])

    def test_no_source_field(self, tmp_path, monkeypatch):
        """Files without source field are unchanged."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        filepath = _make_file(tmp_path / "test.md", {"title": "Test"})
        status, detail = migrate_source_field(filepath)
        assert status == "unchanged"

    def test_dry_run_shows_preview(self, tmp_path, monkeypatch):
        """Dry run shows what would change without writing."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        raw = tmp_path / "raw"
        raw.mkdir()
        (raw / "test.md").write_text("# Raw")
        fm = {"title": "Test", "source": "[test.md](../raw/test.md)"}
        filepath = _make_file(tmp_path / "test.md", fm)
        status, detail = migrate_source_field(filepath, dry_run=True)
        assert status == "would_migrate"
        # File should be unchanged
        data = yaml.safe_load(Path(filepath).read_text().split("---")[1])
        assert "source" in data

    def test_malformed_source_field(self, tmp_path, monkeypatch):
        """Malformed source field is reported as failed."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        fm = {"title": "Test", "source": "not-a-markdown-link"}
        filepath = _make_file(tmp_path / "test.md", fm)
        status, detail = migrate_source_field(filepath)
        assert status == "failed"
        assert "Malformed" in detail

    def test_preserves_body_content(self, tmp_path, monkeypatch):
        """Body content is preserved after migration."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        raw = tmp_path / "raw"
        raw.mkdir()
        (raw / "test.md").write_text("# Raw")
        body = "\n# Title\n\nBody content here.\n"
        fm = {"title": "Test", "source": "[test.md](../raw/test.md)"}
        filepath = _make_file(tmp_path / "test.md", fm, body)
        migrate_source_field(filepath)
        content = Path(filepath).read_text()
        assert "# Title" in content
        assert "Body content here." in content

    def test_idempotent(self, tmp_path, monkeypatch):
        """Running twice produces no changes on second run."""
        _setup_repo(tmp_path)
        monkeypatch.chdir(tmp_path)
        raw = tmp_path / "raw"
        raw.mkdir()
        (raw / "test.md").write_text("# Raw")
        fm = {"title": "Test", "source": "[test.md](../raw/test.md)"}
        filepath = _make_file(tmp_path / "test.md", fm)
        migrate_source_field(filepath)
        status, detail = migrate_source_field(filepath)
        assert status == "unchanged"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
