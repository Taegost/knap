#!/usr/bin/env python3
"""Add frontmatter to index files that lack it.

Scans wiki/*/index.md, wiki/index.md, and .knap/ROUTER.md.
Adds frontmatter with Parent link and description field if missing.

Usage:
    python3 .knap/scripts/migrate_index_frontmatter.py
    python3 .knap/scripts/migrate_index_frontmatter.py --dry-run
"""

import argparse
import sys
from pathlib import Path

import yaml

from parse_frontmatter import ParsedFile


def _has_frontmatter(filepath: Path) -> bool:
    """Check if a file already has frontmatter."""
    parsed = ParsedFile(str(filepath))
    return parsed.frontmatter is not None and parsed.error is None


def _build_index_frontmatter(parent_target: str | None, description: str) -> dict:
    """Build frontmatter dict for an index file."""
    fm = {"description": description}
    if parent_target:
        fm["links"] = [{"target": parent_target, "type": "Parent"}]
    return fm


def _add_frontmatter_to_file(filepath: Path, fm: dict) -> str:
    """Add frontmatter to a file that has none.

    Returns the new content string.
    """
    content = filepath.read_text()
    yaml_str = yaml.dump(fm, default_flow_style=False, sort_keys=False).rstrip()
    return f"---\n{yaml_str}---\n\n{content}"


def migrate_index_frontmatter(*, dry_run: bool = False) -> list[str]:
    """Add frontmatter to index files that lack it.

    Returns:
        List of action messages (what was done or would be done).
    """
    actions: list[str] = []
    wiki_path = Path("wiki")
    knap_path = Path(".knap")

    # Category indexes: wiki/*/index.md
    if wiki_path.exists():
        for cat_dir in sorted(wiki_path.iterdir()):
            if not cat_dir.is_dir():
                continue
            cat_index = cat_dir / "index.md"
            if not cat_index.exists():
                continue

            if _has_frontmatter(cat_index):
                actions.append(f"skip: {cat_index} (already has frontmatter)")
                continue

            fm = _build_index_frontmatter(
                parent_target="[wiki index](wiki/index.md)",
                description=f"Catalog of {cat_dir.name} pages.",
            )
            if dry_run:
                actions.append(f"would add frontmatter to: {cat_index}")
            else:
                new_content = _add_frontmatter_to_file(cat_index, fm)
                cat_index.write_text(new_content)
                actions.append(f"added frontmatter to: {cat_index}")

    # Master index: wiki/index.md
    master_index = wiki_path / "index.md"
    if master_index.exists():
        if _has_frontmatter(master_index):
            actions.append(f"skip: {master_index} (already has frontmatter)")
        else:
            fm = _build_index_frontmatter(
                parent_target="[router](.knap/ROUTER.md)",
                description="Master wiki index.",
            )
            if dry_run:
                actions.append(f"would add frontmatter to: {master_index}")
            else:
                new_content = _add_frontmatter_to_file(master_index, fm)
                master_index.write_text(new_content)
                actions.append(f"added frontmatter to: {master_index}")

    # Root index: .knap/ROUTER.md
    router = knap_path / "ROUTER.md"
    if router.exists():
        if _has_frontmatter(router):
            actions.append(f"skip: {router} (already has frontmatter)")
        else:
            fm = _build_index_frontmatter(
                parent_target=None,  # Root has no parent
                description="Root router and index.",
            )
            if dry_run:
                actions.append(f"would add frontmatter to: {router}")
            else:
                new_content = _add_frontmatter_to_file(router, fm)
                router.write_text(new_content)
                actions.append(f"added frontmatter to: {router}")

    return actions


def main():
    parser = argparse.ArgumentParser(description="Add frontmatter to index files")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    actions = migrate_index_frontmatter(dry_run=args.dry_run)
    for action in actions:
        print(f"  {action}")
    print(f"\n── {len(actions)} files processed ──")


if __name__ == "__main__":
    main()
