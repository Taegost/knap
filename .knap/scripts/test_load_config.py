#!/usr/bin/env python3
"""Tests for load_config.py."""

import pytest

import yaml

from load_config import load_config


class TestLoadConfig:
    def test_valid_config_returns_parsed_values(self, tmp_path):
        """Valid config file returns parsed values."""
        config = {"working": ["wiki/"], "system": [".knap/"]}
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))

        result = load_config(config_path, tmp_path / "template.yaml")
        assert result == config

    def test_missing_config_with_template_creates_file(self, tmp_path):
        """Missing config with template: file is created from template, content returned."""
        template = {"working": ["wiki/"], "system": [".knap/"]}
        template_path = tmp_path / "template.yaml"
        template_path.write_text(yaml.dump(template))

        config_path = tmp_path / "config.yaml"
        result = load_config(config_path, template_path)

        assert result == template
        assert config_path.exists()
        assert yaml.safe_load(config_path.read_text()) == template

    def test_missing_config_without_template_raises_error(self, tmp_path):
        """Missing config without template: raises RuntimeError with remediation steps."""
        config_path = tmp_path / "config.yaml"
        template_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(RuntimeError, match="Template not found"):
            load_config(config_path, template_path)

    def test_empty_config_with_template_creates_file(self, tmp_path):
        """Empty config with template: treated as missing, file created from template."""
        template = {"working": ["wiki/"]}
        template_path = tmp_path / "template.yaml"
        template_path.write_text(yaml.dump(template))

        config_path = tmp_path / "config.yaml"
        config_path.write_text("")

        result = load_config(config_path, template_path)
        assert result == template

    def test_empty_config_without_template_raises_error(self, tmp_path):
        """Empty config without template: raises RuntimeError."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("")
        template_path = tmp_path / "nonexistent.yaml"

        with pytest.raises(RuntimeError, match="Template not found"):
            load_config(config_path, template_path)

    def test_malformed_yaml_raises_error(self, tmp_path):
        """Malformed YAML: raises ValueError, no fallback."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("{{invalid yaml}}")

        with pytest.raises(ValueError, match="Malformed YAML"):
            load_config(config_path, tmp_path / "template.yaml")

    def test_template_copy_preserves_comments(self, tmp_path):
        """Template content including comments is preserved in created config."""
        template_content = "# This is a comment\nworking:\n  - wiki/\n"
        template_path = tmp_path / "template.yaml"
        template_path.write_text(template_content)

        config_path = tmp_path / "config.yaml"
        load_config(config_path, template_path)

        assert config_path.read_text() == template_content

    def test_concurrent_creation_idempotent(self, tmp_path):
        """Second call doesn't clobber first (FileExistsError handled)."""
        template = {"working": ["wiki/"]}
        template_path = tmp_path / "template.yaml"
        template_path.write_text(yaml.dump(template))

        config_path = tmp_path / "config.yaml"

        # First call creates the file
        result1 = load_config(config_path, template_path)

        # Second call should succeed without error
        result2 = load_config(config_path, template_path)

        assert result1 == result2 == template

    def test_nested_config_preserved(self, tmp_path):
        """Nested config structures are preserved."""
        config = {
            "categories": {
                "transcript": {"required_fields": ["channel", "format"]},
                "research": {"required_fields": ["description"]},
            }
        }
        config_path = tmp_path / "config.yaml"
        config_path.write_text(yaml.dump(config))

        result = load_config(config_path, tmp_path / "template.yaml")
        assert result == config

    def test_creates_parent_directories(self, tmp_path):
        """Config file creation creates parent directories if needed."""
        template = {"key": "value"}
        template_path = tmp_path / "template.yaml"
        template_path.write_text(yaml.dump(template))

        config_path = tmp_path / "deep" / "nested" / "config.yaml"
        result = load_config(config_path, template_path)

        assert result == template
        assert config_path.exists()
