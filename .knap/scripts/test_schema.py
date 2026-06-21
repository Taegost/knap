#!/usr/bin/env python3
"""Tests for schema.py."""

import pytest
from pathlib import Path
import importlib

import yaml


class TestSchema:
    def test_existing_categories_yaml_populates_constants(self, tmp_path, monkeypatch):
        """Existing categories.yaml: all constants populated correctly."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()

        config = {
            "required_fields": ["title", "category"],
            "optional_fields": ["tags"],
            "categories": {
                "research": {
                    "required_fields": ["description"],
                    "analysis_label": "Analysis",
                    "analysis_todo": "findings",
                }
            },
        }
        (schema_dir / "categories.yaml").write_text(yaml.dump(config))
        (templates_dir / "categories.yaml.template").write_text(yaml.dump(config))

        import schema
        importlib.reload(schema)

        assert schema.REQUIRED_FIELDS == ["title", "category"]
        assert schema.OPTIONAL_FIELDS == ["tags"]
        assert "research" in schema.CATEGORIES
        assert schema.VALID_CATEGORIES == ["research"]
        assert schema.CATEGORY_FIELDS == {"research": ["description"]}

    def test_missing_categories_yaml_auto_creates(self, tmp_path, monkeypatch):
        """Missing categories.yaml: file auto-created from template, constants populated."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()

        template = {
            "required_fields": ["title", "source_url"],
            "categories": {
                "reference": {
                    "required_fields": ["description"],
                    "analysis_label": "Notes",
                    "analysis_todo": "key facts",
                }
            },
        }
        (templates_dir / "categories.yaml.template").write_text(yaml.dump(template))

        import schema
        importlib.reload(schema)

        assert schema.REQUIRED_FIELDS == ["title", "source_url"]
        assert "reference" in schema.CATEGORIES
        assert (schema_dir / "categories.yaml").exists()

    def test_missing_template_raises_runtime_error(self, tmp_path, monkeypatch):
        """Missing template: import raises RuntimeError with remediation steps."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        # No templates directory

        import schema
        with pytest.raises(RuntimeError, match="Template not found"):
            importlib.reload(schema)

    def test_auto_creation_from_template(self, tmp_path, monkeypatch):
        """Auto-creation: missing file is created from template with correct content."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()

        template = {
            "required_fields": ["title"],
            "categories": {"transcript": {"required_fields": ["channel"]}},
        }
        (templates_dir / "categories.yaml.template").write_text(yaml.dump(template))

        import schema
        importlib.reload(schema)

        created = yaml.safe_load((schema_dir / "categories.yaml").read_text())
        assert created == template

    def test_reload_after_edit(self, tmp_path, monkeypatch):
        """Reload after edit: constants update correctly."""
        monkeypatch.chdir(tmp_path)
        schema_dir = tmp_path / ".knap" / "schema"
        schema_dir.mkdir(parents=True)
        templates_dir = schema_dir / "templates"
        templates_dir.mkdir()

        config1 = {"required_fields": ["title"], "categories": {}}
        config2 = {"required_fields": ["title", "url"], "categories": {}}

        (schema_dir / "categories.yaml").write_text(yaml.dump(config1))
        (templates_dir / "categories.yaml.template").write_text(yaml.dump(config1))

        import schema
        importlib.reload(schema)
        assert schema.REQUIRED_FIELDS == ["title"]

        # Edit the file
        (schema_dir / "categories.yaml").write_text(yaml.dump(config2))
        schema.reload()
        assert schema.REQUIRED_FIELDS == ["title", "url"]
