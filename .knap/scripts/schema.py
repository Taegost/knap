"""Single source of truth for wiki categories and frontmatter fields.

Reads from schema/categories.yaml. Import this module from other scripts
instead of hardcoding category definitions.
"""

import yaml
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent.parent / "schema" / "categories.yaml"


def _load_schema() -> dict:
    """Load schema from categories.yaml."""
    with open(_SCHEMA_PATH) as f:
        return yaml.safe_load(f)


def _save_schema(data: dict) -> None:
    """Save schema to categories.yaml."""
    with open(_SCHEMA_PATH, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# Load on import
_schema = _load_schema()

# Fields required on every raw file
REQUIRED_FIELDS: list[str] = _schema.get("required_fields", ["title", "source_url", "date_farmed", "category"])

# Optional fields that can appear on any raw file
OPTIONAL_FIELDS: list[str] = _schema.get("optional_fields", ["website", "address", "phone", "hours", "email"])

# Category-specific fields and metadata
CATEGORIES: dict[str, dict] = _schema.get("categories", {})

# Valid category values
VALID_CATEGORIES: list[str] = list(CATEGORIES.keys())

# Category-specific required fields (flattened)
CATEGORY_FIELDS: dict[str, list[str]] = {
    cat: meta.get("required_fields", []) for cat, meta in CATEGORIES.items()
}

# Analysis section labels per category
ANALYSIS_SECTION: dict[str, tuple[str, str]] = {
    cat: (meta.get("analysis_label", "Notes"), meta.get("analysis_todo", "<!-- TODO -->"))
    for cat, meta in CATEGORIES.items()
}

# Default values for fields
FIELD_DEFAULTS: dict[str, str | list] = {
    "description": "n/a",
    "channel": "n/a",
    "format": "n/a",
}


def reload() -> None:
    """Reload schema from disk. Call after editing categories.yaml."""
    global _schema, REQUIRED_FIELDS, OPTIONAL_FIELDS, CATEGORIES
    global VALID_CATEGORIES, CATEGORY_FIELDS, ANALYSIS_SECTION
    _schema = _load_schema()
    REQUIRED_FIELDS = _schema.get("required_fields", REQUIRED_FIELDS)
    OPTIONAL_FIELDS = _schema.get("optional_fields", OPTIONAL_FIELDS)
    CATEGORIES = _schema.get("categories", CATEGORIES)
    VALID_CATEGORIES = list(CATEGORIES.keys())
    CATEGORY_FIELDS = {cat: meta.get("required_fields", []) for cat, meta in CATEGORIES.items()}
    ANALYSIS_SECTION = {
        cat: (meta.get("analysis_label", "Notes"), meta.get("analysis_todo", "<!-- TODO -->"))
        for cat, meta in CATEGORIES.items()
    }
