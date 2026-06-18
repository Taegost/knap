#!/usr/bin/env python3
"""Validate raw file frontmatter against schema/categories.yaml.

Usage:
    python3 scripts/validate.py raw/{category}/
    python3 scripts/validate.py raw/transcripts/
"""

import argparse
import sys
from datetime import date as date_type, datetime
from pathlib import Path

import yaml

from schema import REQUIRED_FIELDS, OPTIONAL_FIELDS, CATEGORY_FIELDS, VALID_CATEGORIES


def parse_frontmatter(filepath: str) -> tuple[dict | None, str | None]:
    """Extract YAML frontmatter. Returns (data, error)."""
    with open(filepath) as f:
        content = f.read()
    if not content.startswith("---"):
        return None, "Missing frontmatter (---)"
    end = content.find("---", 3)
    if end == -1:
        return None, "Unclosed frontmatter"
    try:
        data = yaml.safe_load(content[3:end])
        return (data if isinstance(data, dict) else None), None
    except yaml.YAMLError as e:
        return None, f"YAML error: {e}"


def validate_file(filepath: str) -> list[tuple[str, str]]:
    """Validate one raw file. Returns list of (level, message)."""
    issues = []
    data, error = parse_frontmatter(filepath)
    if error:
        issues.append(("error", error))
        return issues

    for field in REQUIRED_FIELDS:
        if field not in data or (isinstance(data[field], str) and not data[field].strip()):
            issues.append(("error", f"missing required field: {field}"))

    category = data.get("category", "")
    if category and category not in VALID_CATEGORIES:
        issues.append(("error", f"invalid category '{category}' — valid: {', '.join(VALID_CATEGORIES)}"))

    date_farmed = data.get("date_farmed")
    if date_farmed:
        if isinstance(date_farmed, str):
            try:
                datetime.strptime(date_farmed, "%Y-%m-%d")
            except ValueError:
                issues.append(("error", f"invalid date_farmed '{date_farmed}' — expected YYYY-MM-DD"))

    if category in CATEGORY_FIELDS:
        for field in CATEGORY_FIELDS[category]:
            if field not in data:
                issues.append(("warning", f"missing {category} field: {field}"))

    known = set(REQUIRED_FIELDS + OPTIONAL_FIELDS + CATEGORY_FIELDS.get(category, []))
    for key in data:
        if key not in known:
            issues.append(("warning", f"unknown field: {key}"))

    return issues


def collect_files(paths: list[str]) -> list[str]:
    files = set()
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix == ".md":
            files.add(str(path.resolve()))
        elif path.is_dir():
            for md in sorted(path.rglob("*.md")):
                files.add(str(md.resolve()))
    return sorted(files)


def main():
    parser = argparse.ArgumentParser(description="Validate raw file frontmatter")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    files = collect_files(args.paths)
    if not files:
        print("No .md files found.", file=sys.stderr)
        sys.exit(1)

    errors = warnings = clean = 0
    for filepath in files:
        issues = validate_file(filepath)
        if issues:
            short = filepath.replace(str(Path.cwd()) + "/", "")
            print(f"\n{short}")
            for level, msg in issues:
                prefix = "  ✗" if level == "error" else "  ⚠"
                print(f"{prefix} {msg}")
                if level == "error":
                    errors += 1
                else:
                    warnings += 1
        else:
            clean += 1

    print(f"\n── {len(files)} files: {clean} clean, {errors} errors, {warnings} warnings ──")
    if args.strict and warnings > 0:
        sys.exit(1)
    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
