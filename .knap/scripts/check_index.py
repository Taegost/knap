#!/usr/bin/env python3
"""Index validation helper.

Checks master index, category indexes, and index-to-file consistency.
Extracted from lint.py per the orphan content checker plan.

Usage:
    from check_index import check_index
    issues = check_index()
"""

import re
from pathlib import Path

from parse_frontmatter import ParsedFile
from traversal import traverse_files


def check_index() -> list[str]:
    """Check master index, category indexes, and index entries.

    Checks:
      - Master index exists (I1)
      - Category indexes exist for categories with pages (I1)
      - Category index entries match actual pages (ghosts and missing) (I3)
      - Master index links to each category index (I4)
      - Files in indexed categories have Parent link in frontmatter (I6)

    Returns:
        List of issue strings. Empty list means all checks passed.
    """
    issues: list[str] = []
    wiki_path = Path("wiki")

    # Check master index exists
    master_index = wiki_path / "index.md"
    if not master_index.exists():
        issues.append(f"missing: {master_index}")
        return issues

    # Check category indexes
    for cat_dir in sorted(wiki_path.iterdir()):
        if not cat_dir.is_dir():
            continue

        cat_index = cat_dir / "index.md"
        cat_name = cat_dir.name

        # Check category index exists
        if not cat_index.exists():
            pages = [f for f in cat_dir.glob("*.md") if f.name != "index.md"]
            if pages:
                issues.append(f"missing: {cat_index}")
            continue

        # Check entries in category index match actual pages (I3)
        content = cat_index.read_text()
        index_entries: set[str] = set()
        for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
            index_entries.add(m.group(2))

        actual_pages: set[str] = set()
        for md in cat_dir.glob("*.md"):
            if md.name == "index.md":
                continue
            actual_pages.add(md.name)

        for entry in sorted(index_entries - actual_pages):
            issues.append(f"index ghost: {cat_name}/{entry} listed but does not exist")
        for page in sorted(actual_pages - index_entries):
            issues.append(f"index missing: {cat_name}/{page}")

    # Check master index links to category indexes (I4)
    master_content = master_index.read_text()
    for cat_dir in sorted(wiki_path.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_index = cat_dir / "index.md"
        if cat_index.exists():
            cat_link = f"{cat_dir.name}/index.md"
            if cat_link not in master_content:
                issues.append(f"master index missing link to: {cat_link}")

    # Check Parent link requirement for files in indexed categories (I6)
    issues.extend(_check_parent_links())

    return issues


def _check_parent_links() -> list[str]:
    """Check that files in indexed categories have a Parent link to their index.

    Index files (index.md, ROUTER.md) are exempt — they don't need Parent links.

    Returns:
        List of issue strings.
    """
    issues: list[str] = []
    wiki_path = Path("wiki")

    for cat_dir in sorted(wiki_path.iterdir()):
        if not cat_dir.is_dir():
            continue

        cat_index = cat_dir / "index.md"
        if not cat_index.exists():
            continue

        for md in sorted(cat_dir.glob("*.md")):
            if md.name == "index.md":
                continue

            parsed = ParsedFile(md)
            if parsed.error:
                continue

            links = parsed.frontmatter.get("links", []) if parsed.frontmatter else []
            if not isinstance(links, list):
                links = []

            has_parent = any(
                isinstance(entry, dict) and entry.get("type") == "Parent"
                for entry in links
            )

            if not has_parent:
                rel = str(md)
                issues.append(f"missing Parent link: {rel}")

    return issues
