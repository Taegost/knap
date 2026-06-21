#!/usr/bin/env python3
"""Shared config loader with auto-creation from templates.

Templates are the single source of truth for config defaults.
No in-memory fallback — if a config file is missing or empty,
it's created from the template. If the template is also missing,
that's a hard error.

Usage:
    from load_config import load_config
    data = load_config(".knap/schema/folders.yaml", ".knap/schema/templates/folders.yaml.template")
"""

from pathlib import Path

import yaml


def load_config(path: str | Path, template_path: str | Path) -> dict:
    """Load a YAML config file, auto-creating from template if missing/empty.

    Args:
        path: Path to the config file.
        template_path: Path to the template file (single source of truth for defaults).

    Returns:
        Parsed config dict.

    Raises:
        ValueError: Config file contains malformed YAML.
        RuntimeError: Template is missing with concrete remediation steps.
    """
    path = Path(path)
    template_path = Path(template_path)

    # Try to read existing config
    if path.exists():
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            if data is not None:
                return data
            # Empty file — fall through to template creation
        except yaml.YAMLError as e:
            raise ValueError(
                f"Malformed YAML in {path}: {e}. "
                "Fix the file manually or delete it to recreate from template."
            ) from e

    # Config is missing or empty — load template
    return _create_from_template(path, template_path)


def _create_from_template(path: Path, template_path: Path) -> dict:
    """Create config file from template and return parsed content.

    Uses try/except FileExistsError scoped to the write call only,
    so concurrent creation is idempotent without masking other errors.
    """
    if not template_path.exists():
        raise RuntimeError(
            f"Template not found: {template_path}. "
            "Ensure the .knap/schema/templates/ directory exists; "
            "if you cloned this repo, try re-cloning or "
            "`git checkout -- .knap/schema/templates/`"
        )

    with open(template_path) as f:
        template_content = f.read()

    data = yaml.safe_load(template_content)

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write config file — handle concurrent creation gracefully
    try:
        path.write_text(template_content)
    except FileExistsError:
        # Another process created it — that's fine
        pass

    return data
