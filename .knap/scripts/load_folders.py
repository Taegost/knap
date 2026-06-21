#!/usr/bin/env python3
"""Load folder classification from .knap/schema/folders.yaml.

Provides get_working_folders(), get_system_folders(), get_excluded_folders()
that return Path objects for each classification.

Usage:
    from load_folders import get_working_folders, get_system_folders, get_excluded_folders
"""

from pathlib import Path

from load_config import load_config

_FOLDERS_PATH = Path(".knap/schema/folders.yaml")
_TEMPLATE_PATH = Path(".knap/schema/templates/folders.yaml.template")


def _load_folders_config() -> dict:
    """Load folders.yaml, auto-creating from template if missing."""
    return load_config(_FOLDERS_PATH, _TEMPLATE_PATH)


def _get_folders(key: str) -> list[Path]:
    """Get folder list for a given key, returning Path objects."""
    config = _load_folders_config()
    raw = config.get(key, [])
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
