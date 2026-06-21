#!/usr/bin/env python3
"""Orphan detection helper.

Finds files in working/system folders that have no incoming links from
any other file. Uses frontmatter links, body markdown links, and wikilinks.

Usage:
    from find_orphans import find_orphans
    orphans = find_orphans()
"""

import re
from pathlib import Path

from parse_frontmatter import ParsedFile
from check_links import _extract_url, resolve_wikilink, extract_wikilinks
from traversal import traverse_files


def find_orphans() -> list[str]:
    """Find files with no incoming links from any other file.

    A file is orphaned if no other file links to it via:
      - Frontmatter links[].target
      - Body markdown links [text](url)
      - Wikilinks [[name]] or [[path|display]]

    Index files (index.md, ROUTER.md) are not checked for incoming links —
    they are structural and linked from master indexes or ROUTER references.

    Returns:
        List of repo-root-relative paths of orphaned files.
    """
    all_files = traverse_files(indexed_only=True)

    # Build set of all incoming link targets
    incoming: set[str] = set()

    for f in all_files:
        parsed = ParsedFile(f)
        if parsed.error:
            continue

        # Frontmatter links
        if parsed.frontmatter:
            links = parsed.frontmatter.get("links", [])
            if isinstance(links, list):
                for entry in links:
                    if isinstance(entry, dict) and "target" in entry:
                        target_url = _extract_url(entry["target"])
                        # Resolve to absolute path for comparison
                        try:
                            target_path = Path(target_url)
                            if not target_path.is_absolute():
                                target_path = Path.cwd() / target_path
                            incoming.add(str(target_path.resolve()))
                        except (OSError, ValueError):
                            pass

        # Body markdown links
        for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', parsed.body):
            target = m.group(2)
            if target.startswith("#"):
                continue
            # Resolve relative to source file
            source_dir = Path(f).parent
            resolved = (source_dir / target)
            try:
                resolved = resolved.resolve()
                incoming.add(str(resolved))
            except (OSError, ValueError):
                pass

        # Wikilinks
        for wikilink in extract_wikilinks(parsed.body):
            resolved = resolve_wikilink(wikilink, str(f))
            if resolved:
                incoming.add(str(resolved))

    # Also add all index files as "linked" — they are structural
    for f in all_files:
        if Path(f).name in ("index.md", "ROUTER.md"):
            incoming.add(str(Path(f).resolve()))

    # A file is orphaned if its resolved path is not in the incoming set
    orphans: list[str] = []
    for f in all_files:
        resolved = str(Path(f).resolve())
        if resolved not in incoming:
            orphans.append(str(f))

    return sorted(orphans)
