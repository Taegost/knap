#!/usr/bin/env python3
"""Lint the wiki for structural issues.

Checks:
  1. Link validation (frontmatter and body links)
  2. Un-ingested raw files (no wiki page)
  3. Index accuracy (entries match real files)
  4. Frontmatter validation
  5. Orphan detection (files with no incoming links)

Usage:
    python3 .knap/scripts/lint.py
    python3 .knap/scripts/lint.py --skip-orphan-check
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml

from schema import REQUIRED_FIELDS, CATEGORY_FIELDS, VALID_CATEGORIES
from check_links import check_link as _check_link, extract_wikilinks, resolve_wikilink
from parse_frontmatter import ParsedFile
from load_folders import get_excluded_folders
from check_index import check_index as _check_index
from find_orphans import find_orphans as _find_orphans


def raw_to_wiki(raw_path: str, raw_dir: str, wiki_dir: str) -> str:
    rp = Path(raw_path)
    try:
        rel = rp.relative_to(raw_dir)
    except ValueError:
        return str(Path(wiki_dir) / rp.name)
    return str(Path(wiki_dir) / rel)


def check_links() -> list[str]:
    """Validate frontmatter and body links across all markdown files.

    Frontmatter internal link failures are errors; external URL failures are warnings.
    Body link failures are warnings (informational).
    """
    issues = []
    excluded = get_excluded_folders()
    repo_root = Path.cwd()

    def _is_excluded(path_parts: tuple[str, ...]) -> bool:
        """Check if path falls under any excluded folder."""
        for exc in excluded:
            exc_parts = exc.parts
            for i in range(len(path_parts) - len(exc_parts) + 1):
                if path_parts[i : i + len(exc_parts)] == exc_parts:
                    return True
        return False

    for md in sorted(repo_root.rglob("*.md")):
        # Skip excluded directories
        parts = md.relative_to(repo_root).parts
        if _is_excluded(parts):
            continue

        try:
            content = md.read_text()
        except Exception:
            continue

        if not content.startswith("---"):
            continue
        end = content.find("---", 3)
        if end == -1:
            continue

        fm_yaml = content[3:end]
        body = content[end + 3:]
        rel_path = str(md.relative_to(repo_root))

        # Check frontmatter links
        try:
            fm = yaml.safe_load(fm_yaml)
            if isinstance(fm, dict):
                links = fm.get("links", [])
                if isinstance(links, list):
                    for entry in links:
                        if isinstance(entry, dict) and "target" in entry:
                            target = entry["target"]
                            result = _check_link(target)
                            if not result.exists:
                                if result.is_external:
                                    issues.append(f"warning: {rel_path} — external link may be broken: {target}")
                                else:
                                    issues.append(f"error: {rel_path} — broken frontmatter link: {target}")
        except yaml.YAMLError:
            pass

        # Check body markdown links
        for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', body):
            target = m.group(2)
            # Skip anchors and heading links
            if target.startswith("#"):
                continue
            result = _check_link(target, relative_to=str(md))
            if not result.exists:
                issues.append(f"warning: {rel_path} — broken body link: {target}")

        # Check wikilinks
        for wikilink in extract_wikilinks(body):
            resolved = resolve_wikilink(wikilink, rel_path)
            if resolved is None:
                issues.append(f"warning: {rel_path} — broken wikilink: [[{wikilink}]]")

    return issues


def check_uningested(raw_dir: str, wiki_dir: str) -> list[str]:
    issues = []
    for md in sorted(Path(raw_dir).rglob("*.md")):
        wiki_path = raw_to_wiki(str(md), raw_dir, wiki_dir)
        if not Path(wiki_path).exists():
            issues.append(f"un-ingested: {md}")
    return issues


def check_frontmatter(raw_dir: str) -> list[str]:
    issues = []
    for md in sorted(Path(raw_dir).rglob("*.md")):
        parsed = ParsedFile(str(md))
        if parsed.error:
            issues.append(f"frontmatter: {md} — {parsed.error}")
            continue
        data = parsed.frontmatter
        if data is None:
            issues.append(f"frontmatter: {md} — missing or unparseable")
            continue
        for field in REQUIRED_FIELDS:
            if field not in data:
                issues.append(f"frontmatter: {md} — missing {field}")
        cat = data.get("category", "")
        if cat and cat not in VALID_CATEGORIES:
            issues.append(f"frontmatter: {md} — unknown category '{cat}'")
    return issues


def print_check(title: str, issues: list[str]) -> int:
    print(f"\n## {title} ({len(issues)})")
    for i in issues:
        print(f"  - {i}")
    if not issues:
        print("  ✓ none")
    return len(issues)


def main():
    parser = argparse.ArgumentParser(description="Lint the wiki for structural issues")
    parser.add_argument(
        "--skip-orphan-check",
        action="store_true",
        help="Skip orphan detection (files with no incoming links)",
    )
    args = parser.parse_args()

    raw_dir = Path("raw").resolve()
    wiki_dir = Path("wiki").resolve()

    total = 0
    total += print_check("Link validation", check_links())
    total += print_check("Un-ingested raw files", check_uningested(str(raw_dir), str(wiki_dir)))
    total += print_check("Frontmatter validation", check_frontmatter(str(raw_dir)))
    total += print_check("Index accuracy", _check_index())

    # Orphan check (L1: runs after index check)
    if not args.skip_orphan_check:
        orphans = _find_orphans()
        if orphans:
            print(f"\n## Orphaned files ({len(orphans)})")
            for o in orphans:
                print(f"  - {o}")

            if sys.stdin.isatty():
                # Interactive: present options (L3)
                print("\nOptions:")
                print("  1) Go through each orphan individually")
                print("  2) Defer to planning")
                print("  3) Ignore and continue")
                choice = input("\nChoice (1/2/3): ").strip()
                if choice == "1":
                    print("  → Individual review not yet implemented. Re-run with --skip-orphan-check.")
                    total += len(orphans)
                elif choice == "2":
                    print("  → Defer to planning. Re-run with --skip-orphan-check to continue.")
                    total += len(orphans)
                elif choice == "3":
                    print("  ⚠ Warning: leaving orphans can cause issues.")
                    print("  Re-running with --skip-orphan-check...")
                    # Re-run without orphan check
                    args.skip_orphan_check = True
                else:
                    print("  Invalid choice. Failing.")
                    total += len(orphans)
            else:
                # Non-interactive: fail (L4)
                total += len(orphans)

    print(f"\n── {total} issues total ──")
    sys.exit(0 if total == 0 else 1)


if __name__ == "__main__":
    main()
