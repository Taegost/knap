#!/usr/bin/env python3
"""Lint the wiki for structural issues.

Checks:
  1. Link validation (frontmatter and body links)
  2. Un-ingested raw files (no wiki page)
  3. Index accuracy (entries match real files)
  4. Frontmatter validation

Usage:
    python3 .knap/scripts/lint.py
"""

import re
import sys
from datetime import date
from pathlib import Path

import yaml

from schema import REQUIRED_FIELDS, CATEGORY_FIELDS, VALID_CATEGORIES
from check_links import check_link as _check_link


def parse_frontmatter(filepath: str) -> dict | None:
    try:
        with open(filepath) as f:
            content = f.read()
        if not content.startswith("---"):
            return None
        end = content.find("---", 3)
        if end == -1:
            return None
        data = yaml.safe_load(content[3:end])
        return data if isinstance(data, dict) else None
    except Exception:
        return None


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
    skip_dirs = {".claude", ".venv", ".git", "__pycache__"}
    repo_root = Path.cwd()

    for md in sorted(repo_root.rglob("*.md")):
        # Skip non-content directories
        parts = md.relative_to(repo_root).parts
        if any(p in skip_dirs for p in parts):
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

    return issues


def check_uningested(raw_dir: str, wiki_dir: str) -> list[str]:
    issues = []
    for md in sorted(Path(raw_dir).rglob("*.md")):
        wiki_path = raw_to_wiki(str(md), raw_dir, wiki_dir)
        if not Path(wiki_path).exists():
            issues.append(f"un-ingested: {md}")
    return issues


def check_index(wiki_dir: str) -> list[str]:
    """Check master index links to category indexes, and category indexes are accurate."""
    issues = []
    wiki_path = Path(wiki_dir)

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
            # Only require index if category has wiki pages
            pages = [f for f in cat_dir.glob("*.md") if f.name != "index.md"]
            if pages:
                issues.append(f"missing: {cat_index}")
            continue

        # Check entries in category index match actual pages
        content = cat_index.read_text()
        index_entries = set()
        for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
            index_entries.add(m.group(2))

        actual_pages = set()
        for md in cat_dir.glob("*.md"):
            if md.name == "index.md":
                continue
            actual_pages.add(md.name)

        for entry in sorted(index_entries - actual_pages):
            issues.append(f"index ghost: {cat_name}/{entry} listed but does not exist")
        for page in sorted(actual_pages - index_entries):
            issues.append(f"index missing: {cat_name}/{page}")

    # Check master index links to category indexes
    master_content = master_index.read_text()
    for cat_dir in sorted(wiki_path.iterdir()):
        if not cat_dir.is_dir():
            continue
        cat_index = cat_dir / "index.md"
        if cat_index.exists():
            cat_link = f"{cat_dir.name}/index.md"
            if cat_link not in master_content:
                issues.append(f"master index missing link to: {cat_link}")

    return issues


def check_frontmatter(raw_dir: str) -> list[str]:
    issues = []
    for md in sorted(Path(raw_dir).rglob("*.md")):
        data = parse_frontmatter(str(md))
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
    raw_dir = Path("raw").resolve()
    wiki_dir = Path("wiki").resolve()

    total = 0
    total += print_check("Link validation", check_links())
    total += print_check("Un-ingested raw files", check_uningested(str(raw_dir), str(wiki_dir)))
    total += print_check("Index accuracy", check_index(str(wiki_dir)))
    total += print_check("Frontmatter validation", check_frontmatter(str(raw_dir)))

    print(f"\n── {total} issues total ──")
    sys.exit(0 if total == 0 else 1)


if __name__ == "__main__":
    main()
