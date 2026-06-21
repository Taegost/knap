#!/usr/bin/env python3
"""Tests for load_folders.py."""

import pytest
from pathlib import Path

import yaml

from load_folders import (
    get_working_folders,
    get_system_folders,
    get_excluded_folders,
    _FOLDERS_PATH,
)


class TestLoadFolders:
    def test_loading_config_returns_correct_lists(self, tmp_path, monkeypatch):
        """Config file values are returned correctly."""
        monkeypatch.chdir(tmp_path)
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

        assert get_working_folders() == [Path("wiki/")]
        assert get_system_folders() == [Path(".knap/")]
        assert get_excluded_folders() == [Path(".git"), Path(".venv")]

    def test_missing_config_auto_creates_from_template(self, tmp_path, monkeypatch):
        """Missing folders.yaml auto-creates from template and returns template content."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()

        template = {
            "working": ["wiki/"],
            "system": [".knap/"],
            "excluded": [".git", ".venv"],
        }
        (templates_dir / "folders.yaml.template").write_text(yaml.dump(template))

        working = get_working_folders()
        system = get_system_folders()
        excluded = get_excluded_folders()

        assert Path("wiki/") in working
        assert Path(".knap/") in system
        assert Path(".git") in excluded
        assert Path(".venv") in excluded
        # Verify file was created
        assert (schema_dir / "folders.yaml").exists()

    def test_empty_config_auto_creates_from_template(self, tmp_path, monkeypatch):
        """Empty folders.yaml treated as missing, auto-creates from template."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()

        template = {"working": ["wiki/"], "system": [".knap/"], "excluded": []}
        (templates_dir / "folders.yaml.template").write_text(yaml.dump(template))

        (schema_dir / "folders.yaml").write_text("")

        working = get_working_folders()
        assert Path("wiki/") in working

    def test_custom_values_override_defaults(self, tmp_path, monkeypatch):
        """Custom values are returned instead of template defaults."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()
        config = {
            "working": ["content/", "notes/"],
            "system": [".system/"],
            "excluded": [".cache"],
        }
        (schema_dir / "folders.yaml").write_text(yaml.dump(config))
        (templates_dir / "folders.yaml.template").write_text(yaml.dump(config))

        assert get_working_folders() == [Path("content/"), Path("notes/")]
        assert get_system_folders() == [Path(".system/")]
        assert get_excluded_folders() == [Path(".cache")]

    def test_returns_path_objects(self, tmp_path, monkeypatch):
        """Functions return Path objects, not strings."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()

        config = {"working": ["wiki/"], "system": [".knap/"], "excluded": [".git"]}
        (schema_dir / "folders.yaml").write_text(yaml.dump(config))
        (templates_dir / "folders.yaml.template").write_text(yaml.dump(config))

        for folder_list in [get_working_folders(), get_system_folders(), get_excluded_folders()]:
            for p in folder_list:
                assert isinstance(p, Path)

    def test_missing_template_raises_error(self, tmp_path, monkeypatch):
        """Missing template raises RuntimeError with remediation steps."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        # No templates directory

        with pytest.raises(RuntimeError, match="Template not found"):
            get_working_folders()

    def test_malformed_config_raises_error(self, tmp_path, monkeypatch):
        """Malformed YAML raises ValueError regardless of template."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()

        (schema_dir / "folders.yaml").write_text("{{invalid}}")
        (templates_dir / "folders.yaml.template").write_text("working:\n  - wiki/\n")

        with pytest.raises(ValueError, match="Malformed YAML"):
            get_working_folders()
