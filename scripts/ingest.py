#!/usr/bin/env python3
"""Ingest raw files into the wiki.

Creates wiki page stubs from raw source files, updates wiki/index.md,
and appends to wiki/log.md. Category-agnostic — derives paths from
frontmatter and location.

Usage:
    python3 scripts/ingest.py raw/transcripts/*.md
    python3 scripts/ingest.py --dry-run raw/transcripts/*.md
    python3 scripts/ingest.py --force raw/transcripts/*.md
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import yaml

from schema import ANALYSIS_SECTION, CATEGORY_FIELDS, FIELD_DEFAULTS

WIKI_DIR = "wiki"
INDEX_PATH = "wiki/index.md"
LOG_PATH = "wiki/log.md"

INDEX_CATEGORY_MARKER = "<!-- {category} pages -->"
LOG_ENTRY_TEMPLATE = "## [{date}] ingest | {title}\n{raw_path} → {wiki_path}\n"


def _val(v):
    if v is None:
        return None
    if isinstance(v, str) and v.strip().lower() == "n/a":
        return None
    if isinstance(v, list) and len(v) == 0:
        return None
    return v


def _fmt_list(items: list) -> str:
    if not items:
        return ""
    return "\n".join(f"- {item}" for item in items)


def _fmt_table(rows: list[tuple[str, str]]) -> str:
    if not rows:
        return ""
    lines = ["|  |  |", "|---|---|"]
    for k, v in rows:
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def _fmt_pricing(pricing) -> str:
    if isinstance(pricing, str):
        return pricing
    if isinstance(pricing, list):
        rows = []
        for item in pricing:
            if isinstance(item, dict):
                for k, v in item.items():
                    rows.append((k.replace("_", " ").title(), str(v)))
            elif isinstance(item, str):
                return _fmt_list(pricing)
        if rows:
            return _fmt_table(rows)
    return str(pricing)


def _fmt_contact(fm: dict) -> str:
    parts = []
    for field in ["phone", "email", "website", "address"]:
        if _val(fm.get(field)):
            label = field.replace("_", " ").title()
            parts.append(f"- **{label}:** {fm[field]}")
    return "\n".join(parts)


def build_wiki_page(fm: dict, raw_path: str, date_ingested: str) -> str:
    """Build a wiki page stub from raw file frontmatter."""
    title = fm.get("title", Path(raw_path).stem)
    category = fm.get("category", "unknown")

    # Frontmatter
    wiki_fm = {
        "source": f"[{Path(raw_path).name}](../{raw_path})",
        "date_ingested": date_ingested,
    }
    for field in ["website", "address", "phone", "hours", "email", "channel", "format"]:
        val = _val(fm.get(field))
        if val:
            wiki_fm[field] = val

    # List fields
    for field in ["accepted_materials", "services", "areas_served", "tags"]:
        val = _val(fm.get(field))
        if val:
            wiki_fm[field] = val

    lines = ["---"]
    for key, value in wiki_fm.items():
        if isinstance(value, list):
            if value:
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: []")
        else:
            lines.append(f'{key}: "{value}"')
    lines.append("---")
    lines.append("")

    lines.extend([f"# {title}", "", "## Summary", "", "<!-- TODO: write 2-4 sentence summary -->", ""])

    # Contact info
    contact = _fmt_contact(fm)
    if contact:
        lines.extend(["## Contact", "", contact, ""])

    # Details section
    lines.append("## Details")

    pricing = _val(fm.get("pricing"))
    if pricing:
        lines.extend(["", "### Pricing", "", _fmt_pricing(pricing)])

    restrictions = _val(fm.get("restrictions"))
    if restrictions:
        lines.extend(["", "### Restrictions", "", _fmt_list(restrictions)])

    # Analysis section
    section_label, todo = ANALYSIS_SECTION.get(category, ("Notes", "<!-- TODO -->"))
    lines.extend(["", f"## {section_label}", "", todo])

    return "\n".join(lines) + "\n"


def parse_frontmatter(filepath: str) -> dict:
    with open(filepath) as f:
        content = f.read()
    if not content.startswith("---"):
        raise ValueError(f"{filepath}: missing frontmatter")
    end = content.find("---", 3)
    if end == -1:
        raise ValueError(f"{filepath}: unclosed frontmatter")
    data = yaml.safe_load(content[3:end])
    if not isinstance(data, dict):
        raise ValueError(f"{filepath}: frontmatter is not a mapping")
    return data


def raw_to_wiki_path(raw_path: str) -> str:
    p = Path(raw_path)
    parts = p.parts
    if parts[0] == "raw":
        parts = ("wiki",) + parts[1:]
    return str(Path(*parts))


def update_index(category: str, wiki_path: str, title: str) -> None:
    index = Path(INDEX_PATH)
    if not index.exists():
        return

    lines = index.read_text().splitlines()
    marker = INDEX_CATEGORY_MARKER.format(category=category)
    entry = f"- [{title}]({wiki_path.replace('wiki/', '')})"

    marker_idx = None
    for i, line in enumerate(lines):
        if marker in line:
            marker_idx = i
            break

    if marker_idx is None:
        print(f"⚠  no section for category '{category}' in index.md — skipping")
        return

    for line in lines:
        if entry in line:
            print(f"  index.md: entry already exists for {title}")
            return

    # Insert after last existing entry in this section
    for i in range(marker_idx + 1, len(lines)):
        if lines[i].startswith("- ["):
            continue
        lines.insert(i, entry)
        break
    else:
        lines.append(entry)

    index.write_text("\n".join(lines) + "\n")
    print(f"  index.md: added {title}")


def append_log(raw_path: str, wiki_path: str, title: str) -> None:
    log = Path(LOG_PATH)
    today = date.today().isoformat()
    entry = LOG_ENTRY_TEMPLATE.format(date=today, title=title, raw_path=raw_path, wiki_path=wiki_path)

    if log.exists():
        content = log.read_text()
        if not content.endswith("\n"):
            content += "\n"
        log.write_text(content + entry + "\n")
    else:
        log.write_text("# Wiki Log\n\n" + entry + "\n")
    print(f"  log.md: appended entry")


def ingest(raw_path: str, *, dry_run: bool = False, force: bool = False) -> bool:
    raw = Path(raw_path)
    if not raw.exists():
        print(f"✗ {raw_path}: not found", file=sys.stderr)
        return False

    print(f"\n── {raw_path} ──")

    try:
        fm = parse_frontmatter(str(raw))
    except (ValueError, yaml.YAMLError) as e:
        print(f"✗ {e}", file=sys.stderr)
        return False

    title = fm.get("title", raw.stem)
    category = fm.get("category", "unknown")
    date_ingested = date.today().isoformat()
    wiki_path = raw_to_wiki_path(str(raw))
    wiki = Path(wiki_path)

    if wiki.exists() and not force:
        print(f"⚠  {wiki_path} exists — use --force to overwrite")
        return False

    page_content = build_wiki_page(fm, str(raw), date_ingested)

    if dry_run:
        print(f"  [dry-run] would create: {wiki_path}")
        return True

    wiki.parent.mkdir(parents=True, exist_ok=True)
    wiki.write_text(page_content)
    print(f"  created: {wiki_path}")

    update_index(category, wiki_path, title)
    append_log(str(raw), wiki_path, title)
    return True


def main():
    parser = argparse.ArgumentParser(description="Ingest raw files into wiki")
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    success = skipped = 0
    for p in args.paths:
        if ingest(p, dry_run=args.dry_run, force=args.force):
            success += 1
        else:
            skipped += 1
    print(f"\n── {success} ingested, {skipped} skipped ──")


if __name__ == "__main__":
    main()
