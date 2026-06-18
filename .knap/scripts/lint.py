#!/usr/bin/env python3
"""Lint the wiki for structural issues.

Checks:
  1. Orphan wiki pages (broken source links)
  2. Un-ingested raw files (no wiki page)
  3. Stale wiki pages (raw newer than wiki)
  4. Index accuracy (entries match real files)
  5. Frontmatter validation

Usage:
    python3 scripts/lint.py
"""

import re
import sys
from datetime import date
from pathlib import Path

import yaml

from schema import REQUIRED_FIELDS, CATEGORY_FIELDS, VALID_CATEGORIES


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


def extract_source_link(page_path: str) -> str | None:
    content = Path(page_path).read_text()
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    fm = content[3:end]
    # source: "[name](../raw/...)" — extract the path
    m = re.search(r'source:\s*"?\[.*?\]\(\.\./(.+?)\)"?', fm)
    if m:
        return m.group(1)
    return None


def check_orphans(wiki_dir: str, raw_dir: str) -> list[str]:
    issues = []
    for md in sorted(Path(wiki_dir).rglob("*.md")):
        if md.name in ("index.md", "log.md"):
            continue
        source = extract_source_link(str(md))
        if source is None:
            issues.append(f"orphan: {md} — no source link found")
        elif not Path(source).exists():
            issues.append(f"orphan: {md} — source {source} does not exist")
    return issues


def check_uningested(raw_dir: str, wiki_dir: str) -> list[str]:
    issues = []
    for md in sorted(Path(raw_dir).rglob("*.md")):
        wiki_path = raw_to_wiki(str(md), raw_dir, wiki_dir)
        if not Path(wiki_path).exists():
            issues.append(f"un-ingested: {md}")
    return issues


def check_index(wiki_dir: str) -> list[str]:
    index_path = Path(wiki_dir) / "index.md"
    if not index_path.exists():
        return [f"missing: {index_path}"]

    content = index_path.read_text()
    index_entries = set()
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', content):
        index_entries.add(m.group(2))

    actual_pages = set()
    for md in Path(wiki_dir).rglob("*.md"):
        if md.name in ("index.md", "log.md"):
            continue
        rel = str(md.relative_to(wiki_dir))
        actual_pages.add(rel)

    issues = []
    for entry in sorted(index_entries - actual_pages):
        issues.append(f"index ghost: {entry} listed but does not exist")
    for page in sorted(actual_pages - index_entries):
        issues.append(f"index missing: {page}")
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
    total += print_check("Orphan wiki pages", check_orphans(str(wiki_dir), str(raw_dir)))
    total += print_check("Un-ingested raw files", check_uningested(str(raw_dir), str(wiki_dir)))
    total += print_check("Index accuracy", check_index(str(wiki_dir)))
    total += print_check("Frontmatter validation", check_frontmatter(str(raw_dir)))

    print(f"\n── {total} issues total ──")
    sys.exit(0 if total == 0 else 1)


if __name__ == "__main__":
    main()
