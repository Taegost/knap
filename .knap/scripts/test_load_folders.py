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
        config = {
            "working": ["wiki/"],
            "system": [".knap/"],
            "excluded": [".git", ".venv"],
        }
        (schema_dir / "folders.yaml").write_text(yaml.dump(config))

        assert get_working_folders() == [Path("wiki/")]
        assert get_system_folders() == [Path(".knap/")]
        assert get_excluded_folders() == [Path(".git"), Path(".venv")]

    def test_missing_config_returns_defaults(self, tmp_path, monkeypatch):
        """Missing folders.yaml returns default values."""
        monkeypatch.chdir(tmp_path)

        working = get_working_folders()
        system = get_system_folders()
        excluded = get_excluded_folders()

        assert Path("wiki/") in working
        assert Path(".knap/") in system
        assert Path(".git") in excluded
        assert Path(".venv") in excluded

    def test_empty_config_returns_defaults(self, tmp_path, monkeypatch):
        """Empty folders.yaml returns default values."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        (schema_dir / "folders.yaml").write_text("")

        working = get_working_folders()
        assert Path("wiki/") in working

    def test_custom_values_override_defaults(self, tmp_path, monkeypatch):
        """Custom values are returned instead of defaults."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        config = {
            "working": ["content/", "notes/"],
            "system": [".system/"],
            "excluded": [".cache"],
        }
        (schema_dir / "folders.yaml").write_text(yaml.dump(config))

        assert get_working_folders() == [Path("content/"), Path("notes/")]
        assert get_system_folders() == [Path(".system/")]
        assert get_excluded_folders() == [Path(".cache")]

    def test_returns_path_objects(self, tmp_path, monkeypatch):
        """Functions return Path objects, not strings."""
        monkeypatch.chdir(tmp_path)

        for folder_list in [get_working_folders(), get_system_folders(), get_excluded_folders()]:
            for p in folder_list:
                assert isinstance(p, Path)
