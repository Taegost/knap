#!/usr/bin/env python3
"""Tests for lint.py orchestration."""

import pytest
from pathlib import Path
from unittest.mock import patch, call

import yaml

import lint


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


def _make_file(path: Path, fm: dict, body: str = "\n# Test\n"):
    """Create a markdown file with frontmatter."""
    content = f"---\n{yaml.dump(fm, default_flow_style=False, sort_keys=False)}---{body}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


class TestLintOrchestration:
    def test_skip_orphan_check_flag(self, tmp_path, monkeypatch, capsys):
        """--skip-orphan-check prevents orphan checking."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n")

        monkeypatch.setattr("sys.argv", ["lint.py", "--skip-orphan-check"])
        with pytest.raises(SystemExit) as exc_info:
            lint.main()
        # Should exit 0 (no issues) — orphan check was skipped
        assert exc_info.value.code == 0

    def test_index_check_runs_before_orphan_check(self, tmp_path, monkeypatch):
        """Index check completes before orphan check starts."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n")

        call_order = []
        original_check_index = lint._check_index
        original_find_orphans = lint._find_orphans

        def mock_check_index():
            call_order.append("check_index")
            return original_check_index()

        def mock_find_orphans():
            call_order.append("find_orphans")
            return original_find_orphans()

        monkeypatch.setattr(lint, "_check_index", mock_check_index)
        monkeypatch.setattr(lint, "_find_orphans", mock_find_orphans)
        monkeypatch.setattr("sys.argv", ["lint.py"])

        with pytest.raises(SystemExit):
            lint.main()

        assert "check_index" in call_order
        assert "find_orphans" in call_order
        idx_pos = call_order.index("check_index")
        orphan_pos = call_order.index("find_orphans")
        assert idx_pos < orphan_pos

    def test_uses_parsedfile_from_new_module(self, tmp_path, monkeypatch):
        """lint.py uses ParsedFile from parse_frontmatter module."""
        # Verify the import is from the new module
        assert hasattr(lint, "ParsedFile")
        assert lint.ParsedFile.__module__ == "parse_frontmatter"

    def test_non_interactive_fails_on_orphans(self, tmp_path, monkeypatch):
        """Non-interactive context (no TTY) fails with exit code 1 on orphans."""
        monkeypatch.chdir(tmp_path)
        _setup_repo(tmp_path)
        wiki = tmp_path / "wiki"
        cat_dir = wiki / "transcripts"
        cat_dir.mkdir(parents=True)
        (wiki / "index.md").write_text("# Wiki\n- [Transcripts](transcripts/index.md)\n")
        _make_file(cat_dir / "index.md", {"title": "Index"})
        _make_file(cat_dir / "orphan.md", {"title": "Orphan"})

        monkeypatch.setattr("sys.argv", ["lint.py"])
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)

        with pytest.raises(SystemExit) as exc_info:
            lint.main()
        assert exc_info.value.code == 1
