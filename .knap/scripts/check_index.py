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

# Import at module level for testing; callers can monkeypatch
_add_frontmatter_link = None


def _get_add_frontmatter_link():
    """Lazy import to avoid circular dependency."""
    global _add_frontmatter_link
    if _add_frontmatter_link is None:
        from add_frontmatter_link import add_frontmatter_link
        _add_frontmatter_link = add_frontmatter_link
    return _add_frontmatter_link


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
        # Parse body only — frontmatter may contain Parent links that are not index entries
        parsed = ParsedFile(str(cat_index))
        body = parsed.body if not parsed.error else cat_index.read_text()
        index_entries: set[str] = set()
        for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', body):
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
    # Parse body only — frontmatter may contain Parent links that are not index entries
    master_parsed = ParsedFile(str(master_index))
    master_body = master_parsed.body if not master_parsed.error else master_index.read_text()
    for cat_dir in sorted(wiki_path.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_index = cat_dir / "index.md"
        if cat_index.exists():
            cat_link = f"{cat_dir.name}/index.md"
            if cat_link not in master_body:
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


def fix_missing_parent_links() -> list[str]:
    """Auto-fix wiki pages that are missing Parent links.

    Calls check_index() to detect issues, then adds Parent links to pages
    that are missing them. The shared link module handles both the frontmatter
    write and the index body update (via index reciprocity).

    Returns:
        List of fix messages applied.
    """
    issues = check_index()
    fixes: list[str] = []
    add_link = _get_add_frontmatter_link()

    for issue in issues:
        if not issue.startswith("missing Parent link: "):
            continue

        # Extract file path from issue
        file_path = issue[len("missing Parent link: "):]
        md = Path(file_path)

        # Compute category index path: wiki/{category}/index.md
        cat_index = md.parent / "index.md"
        if not cat_index.exists():
            continue

        # Build Parent link string
        parent_link = f"[index]({cat_index})"

        # Add the Parent link
        add_link(file_path, parent_link, "Parent")
        fixes.append(f"fixed: {file_path} → added Parent link to {cat_index}")

    return fixes
