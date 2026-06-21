#!/usr/bin/env python3
"""Auto-fix module for unlisted pages.

Detects pages with Parent links pointing to an index but not listed in
that index, and adds them.

Usage:
    from fix_index import fix_index
    fixes = fix_index()
    python3 .knap/scripts/fix_index.py
"""

import os
import re
import sys
from pathlib import Path

import yaml

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


def _extract_url(link: str) -> str:
    """Extract URL from markdown link format [name](url)."""
    m = re.match(r'\[([^\]]*)\]\(([^)]+)\)', link)
    if m:
        return m.group(2)
    return link


def _is_index_file(path: Path) -> bool:
    """Check if a file is an index file."""
    return path.name in ("index.md", "ROUTER.md")


def _get_index_entries(index_path: Path) -> set[str]:
    """Extract all link targets from an index file's body."""
    content = index_path.read_text()
    entries: set[str] = set()
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        entries.add(m.group(2))
    return entries


def fix_index() -> list[str]:
    """Fix pages with Parent links pointing to an index but not listed in it.

    Scans all wiki pages, extracts Parent link targets, checks whether each
    page is listed in its target index, and adds missing entries.

    Returns:
        List of fix messages applied.
    """
    fixes: list[str] = []
    add_link = _get_add_frontmatter_link()
    wiki_path = Path("wiki")

    if not wiki_path.exists():
        return fixes

    # Collect all wiki pages
    for md in sorted(wiki_path.rglob("*.md")):
        if md.name == "index.md":
            continue

        parsed = ParsedFile(str(md))
        if parsed.error or parsed.frontmatter is None:
            continue

        links = parsed.frontmatter.get("links", [])
        if not isinstance(links, list):
            continue

        # Find Parent links
        for entry in links:
            if not isinstance(entry, dict) or entry.get("type") != "Parent":
                continue

            target_url = _extract_url(entry.get("target", ""))
            target_path = Path.cwd() / target_url

            # Only process index files
            if not _is_index_file(target_path):
                continue

            if not target_path.exists():
                continue

            # Check if page is already listed in the index
            index_entries = _get_index_entries(target_path)
            # Use os.path.relpath to handle relative/absolute path mixing
            rel_from_index = Path(os.path.relpath(md.resolve(), target_path.parent.resolve()))

            # Check if any entry matches this page
            already_listed = False
            for idx_entry in index_entries:
                # Normalize paths for comparison
                if idx_entry == str(rel_from_index) or idx_entry == md.name:
                    already_listed = True
                    break

            if already_listed:
                continue

            # Page is not listed — add it via add_frontmatter_link
            # This triggers the index body update via U1's reciprocity logic
            source_abs = str(md.resolve())
            parent_link = entry.get("target", "")
            add_link(str(md), parent_link, "Parent")
            fixes.append(f"fixed: {md} → added to {target_path.name}")

    return fixes


def main():
    """Run fix_index and print results."""
    fixes = fix_index()
    if fixes:
        for fix in fixes:
            print(f"  ✓ {fix}")
        print(f"\n── {len(fixes)} fixes applied ──")
    else:
        print("  No unlisted pages found.")


if __name__ == "__main__":
    main()
