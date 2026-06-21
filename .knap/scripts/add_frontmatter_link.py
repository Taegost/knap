#!/usr/bin/env python3
"""Add typed links to markdown file frontmatter.

The sole entry point for writing frontmatter links. Handles deduplication,
type updates, and reciprocal link generation.

Usage:
    python3 .knap/scripts/add_frontmatter_link.py <file> "<link>" [type]
    python3 .knap/scripts/add_frontmatter_link.py wiki/transcripts/foo.md "[Bar](wiki/transcripts/bar.md)" Parent
"""

import argparse
import sys
from pathlib import Path

import yaml

from schema import LINK_TYPE_PAIRS
from check_links import check_link
from parse_frontmatter import ParsedFile


def _write_frontmatter_link(filepath: str, link: str, link_type: str) -> bool:
    """Add or update a link in a file's frontmatter.

    Returns True if the file was modified.
    """
    parsed = ParsedFile(filepath)
    if parsed.error or parsed.frontmatter is None:
        print(f"  ✗ {filepath}: {parsed.error}", file=sys.stderr)
        return False
    data = parsed.frontmatter
    body = parsed.body

    links = data.get("links", [])
    if not isinstance(links, list):
        links = []

    # Check for existing link with same target
    existing_idx = None
    for i, entry in enumerate(links):
        if isinstance(entry, dict) and entry.get("target") == link:
            existing_idx = i
            break

    if existing_idx is not None:
        # Link exists — check if type needs updating
        current_type = links[existing_idx].get("type", "Related")
        if current_type == link_type:
            return False  # Already correct
        links[existing_idx]["type"] = link_type
    else:
        # New link — append
        links.append({"target": link, "type": link_type})

    data["links"] = links

    # Serialize and write
    new_yaml = yaml.dump(data, default_flow_style=False, sort_keys=False)
    new_content = f"---\n{new_yaml}---\n{body}"

    with open(filepath, "w") as f:
        f.write(new_content)
    return True


def add_frontmatter_link(filepath: str, link: str, link_type: str) -> None:
    """Add a frontmatter link with optional reciprocal.

    This is the sole public entry point for adding frontmatter links.
    """
    # Verify target exists
    result = check_link(link)
    if not result.exists and not result.is_external:
        print(f"  ⚠ {filepath}: link target does not exist: {link}", file=sys.stderr)

    # Write primary link
    modified = _write_frontmatter_link(filepath, link, link_type)
    if modified:
        print(f"  ✓ {filepath}: added {link_type} → {link}")

    # Write reciprocal if type has a pair and target is a repo markdown file
    reciprocal_type = LINK_TYPE_PAIRS.get(link_type)
    if reciprocal_type:
        # Extract path from markdown link
        from check_links import _extract_url
        target_path = _extract_url(link)
        target_full = Path.cwd() / target_path
        if target_full.exists() and target_full.suffix == ".md":
            # Index files (index.md, ROUTER.md) are exempt from Child reciprocity.
            # They list children in their body, not frontmatter.
            target_name = target_full.name
            if reciprocal_type == "Child" and target_name in ("index.md", "ROUTER.md"):
                return
            # Build reciprocal link pointing back to source file
            source_rel = str(Path(filepath).resolve().relative_to(Path.cwd()))
            source_name = Path(filepath).stem
            reciprocal_link = f"[{source_name}]({source_rel})"
            rec_modified = _write_frontmatter_link(
                str(target_full), reciprocal_link, reciprocal_type
            )
            if rec_modified:
                print(f"  ✓ {target_path}: added {reciprocal_type} → {reciprocal_link}")


def main():
    parser = argparse.ArgumentParser(description="Add frontmatter link to a file")
    parser.add_argument("file", help="Markdown file to add link to")
    parser.add_argument("link", help="Link in markdown format [name](path)")
    parser.add_argument("type", nargs="?", default="Related", help="Link type (default: Related)")
    args = parser.parse_args()

    from schema import LINK_TYPES
    if args.type not in LINK_TYPES:
        print(f"✗ Invalid type '{args.type}' — valid: {', '.join(LINK_TYPES)}", file=sys.stderr)
        sys.exit(1)

    add_frontmatter_link(args.file, args.link, args.type)


if __name__ == "__main__":
    main()
