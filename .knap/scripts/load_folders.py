#!/usr/bin/env python3
"""Load folder classification from .knap/schema/folders.yaml.

Provides get_working_folders(), get_system_folders(), get_excluded_folders()
that return Path objects for each classification.

Usage:
    from load_folders import get_working_folders, get_system_folders, get_excluded_folders
"""

from pathlib import Path

import yaml

_FOLDERS_PATH = Path(".knap/schema/folders.yaml")

_DEFAULTS = {
    "working": ["wiki/"],
    "system": [".knap/"],
    "excluded": [
        ".claude",
        ".venv",
        ".git",
        "__pycache__",
        "docs/brainstorms",
        "docs/plans",
    ],
}


def _load_config() -> dict:
    """Load folders.yaml, returning defaults if missing or empty."""
    try:
        with open(_FOLDERS_PATH) as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            return _DEFAULTS
        return data
    except FileNotFoundError:
        return _DEFAULTS
    except Exception:
        return _DEFAULTS


def _get_folders(key: str) -> list[Path]:
    """Get folder list for a given key, returning Path objects."""
    config = _load_config()
    raw = config.get(key, _DEFAULTS.get(key, []))
    return [Path(p) for p in raw]


def get_working_folders() -> list[Path]:
    """Return list of working folder Paths."""
    return _get_folders("working")


def get_system_folders() -> list[Path]:
    """Return list of system folder Paths."""
    return _get_folders("system")


def get_excluded_folders() -> list[Path]:
    """Return list of excluded folder Paths."""
    return _get_folders("excluded")
