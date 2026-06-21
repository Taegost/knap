---
title: "Methodology 2: AppalachianHaul Wiki (Karpathy Pattern Implementation)"
category: reference
---

# Methodology 2: AppalachianHaul Wiki (Karpathy Pattern Implementation)

Source: This repository (`~/_ws/wiki-AppalachianHaul`)

---

## Brief Summary

An implementation of the Karpathy LLM Wiki pattern for a truck-based hauling business in the Tri-Cities area of Tennessee. The wiki tracks landfills, recycling centers, competitors, equipment rentals, appliance resale, rent-to-own stores, and business strategies. Three layers: `raw/` (immutable source documents), `wiki/` (LLM-maintained pages), and `CLAUDE.md` (schema and conventions).

What distinguishes this from the bare Karpathy pattern is the addition of a Python tooling pipeline: `validate.py` → `fixup.py` → `standardize.py` → `ingest.py` → `lint.py`. Three skills (`/farm`, `/write-wiki`, `/synthesize`) define repeatable workflows. The schema defines 8 categories with specific required fields per category, YAML frontmatter for structured metadata, and conventions for cross-referencing.

---

## My Thoughts

This is the most direct implementation of the Karpathy pattern, and it adds exactly the right things: schema enforcement and a tooling pipeline. The Karpathy gist is intentionally abstract — it says "your LLM can figure out the rest." This repo actually figures it out, and the result is a system that's more robust than the original pattern while staying true to its simplicity.

The Python pipeline is the key addition. The Karpathy pattern trusts the LLM to produce consistent output. This repo doesn't trust the LLM — it validates, fixes, standardizes, and checks. That's the right call. As the repo's own issues demonstrate (duplicate log entries, incomplete stubs, index gaps), LLMs make mistakes. The tooling catches them.

The category-specific schema is also well-designed. Instead of a generic "page" type, each category (landfill, recycling, competitor, etc.) has its own required fields. This makes the wiki machine-readable — you could build a price comparison tool, a map view, or a competitive analysis dashboard on top of the frontmatter.

The three skills (`/farm`, `/write-wiki`, `/synthesize`) are a good decomposition of the Karpathy operations. `/farm` handles entity discovery (the ingest operation). `/write-wiki` handles the judgment sections (Summary + Analysis). `/synthesize` handles research questions (the query operation, but recorded).

The main weakness is that the system was built with DeepSeek, which struggled with the multi-step pipeline. The result is incomplete wiki pages, duplicate log entries, and index gaps. The tooling pipeline should have caught these — either the linter has bugs or DeepSeek skipped running it.

---

## Detailed Implementation

### Architecture

```
raw/                    Immutable source files, organized by category
  landfills/            7 files
  recycling/            10 files
  competitors/          6 files
  strategies/           5 files
  equipment-rental/     4 files
  appliance-resale/     5 files
  rent-to-own/          5 files
  maintenance/          1 file

wiki/                   LLM-maintained pages, mirroring raw/ structure
  index.md              Content catalog (82 lines, 8 sections)
  log.md                Append-only chronological record

scripts/                Python tooling pipeline
  schema.py             Single source of truth for categories and fields
  validate.py           Frontmatter validation (required fields, dates, categories)
  fixup.py              Adds missing fields with defaults (n/a, [])
  standardize.py        Normalizes placeholder text to canonical n/a
  ingest.py             Generates wiki stubs from frontmatter, updates index + log
  lint.py               8 structural checks (orphans, un-ingested, stale, index, etc.)
  find-stubs.py         Lists wiki pages with TODO markers

.claude/skills/         Repeatable LLM workflows
  farm.md               Research → raw files → full pipeline
  write-wiki.md         Fill in Summary + Analysis sections
  synthesize.md         Research question → raw + wiki + index + log
```

### Schema (schema.py)

Single source of truth for all categories and fields:

```python
REQUIRED_FIELDS = ["title", "source_url", "date_farmed", "category"]
OPTIONAL_FIELDS = ["website", "address", "phone", "hours", "email"]

CATEGORY_FIELDS = {
    "landfill": ["accepted_materials", "pricing", "restrictions"],
    "recycling": ["accepted_materials", "pricing", "restrictions"],
    "competitor": ["services", "pricing", "areas_served"],
    "lead": ["description", "contact_info", "estimated_value", "posted_date"],
    "strategy": ["description"],
    "equipment-rental": ["equipment_types", "pricing", "rental_periods", "areas_served"],
    "appliance-resale": ["accepted_appliances", "pricing", "pickup_available", "restrictions"],
    "rent-to-own": ["services", "pricing", "areas_served"],
}
```

Each category has specific analysis section labels: "For Our Business" (landfills, recycling), "Competitive Position" (competitors), "Strategy Notes" (strategies), etc.

### Raw File Template

YAML frontmatter with structured metadata. Missing values use `"n/a"` (never omit). Empty lists mean "none found."

```yaml
---
title: "Kingsport Demolition Landfill"
source_url: "https://www.kingsporttn.gov/..."
date_farmed: 2026-06-07
category: landfill
address: "1921 Brookside Lane, Kingsport, TN 37660"
phone: "(423) 224-2475"
hours: "Mon-Fri 7:30 AM - 3:30 PM"
accepted_materials:
  - Brick, block, rock, dirt/soil
  - Ferrous metals
pricing: "See body for price table"
restrictions:
  - "NO household garbage"
---
Body content — narrative notes, context, price tables.
```

### Wiki Page Template

Auto-generated by `ingest.py` from frontmatter. Mechanical data (hours, pricing, materials, restrictions, contact) is rendered automatically. Only Summary and Analysis sections remain as `<!-- TODO -->` markers for the LLM to fill.

```markdown
---
source: "[[raw/landfills/kingsport-demolition-landfill.md]]"
date_ingested: "2026-06-07"
address: "1921 Brookside Lane, Kingsport, TN 37660"
---

# Kingsport Demolition Landfill

## Summary
<!-- TODO: write 2-4 sentence summary -->

## Details
### Pricing
| Rate | $65.00/ton (pro-rated) |
| Under 1000 Lbs | $30.00 flat |

### Restrictions
- NO household garbage, cardboard, or paper products

## For Our Business
<!-- TODO: business implications, best use cases, caveats -->
```

### Tooling Pipeline

The full pipeline runs in sequence:

```bash
python3 scripts/validate.py raw/{category}/    # Check required fields, dates, categories
python3 scripts/fixup.py raw/{category}/        # Add missing fields with defaults
python3 scripts/standardize.py raw/{category}/  # Normalize placeholders to n/a
python3 scripts/validate.py raw/{category}/     # Re-validate (must pass clean)
python3 scripts/ingest.py raw/{category}/*.md   # Generate wiki stubs, update index + log
python3 scripts/lint.py                         # 8 structural checks
```

### Lint Checks (lint.py)

8 automated checks:
1. **Orphan wiki pages** — wiki page with broken source link
2. **Un-ingested raw files** — raw .md with no matching wiki page
3. **Stale wiki pages** — wiki page older than its raw source
4. **Index accuracy** — entries in index.md that don't match real files
5. **Missing index entries** — wiki pages not listed in index.md
6. **Frontmatter validation** — same checks as validate.py across all raw/
7. **Duplicate frontmatter/body fields** — fields in both frontmatter and body subsections
8. **Stale raw files** — raw files not updated in 90+ days

### Skills

**`/farm {category}`** — End-to-end entity discovery. Web-search for entities, create raw files, run full pipeline, write Summary + Analysis sections.

**`/write-wiki {category}`** — Fill in judgment sections. Find stubs with TODOs, read raw source + wiki stub, write Summary (2-4 sentences) and Analysis (category-specific).

**`/synthesize {question}`** — Research question from multiple sources. Present findings, create raw + wiki + index + log.

---

## What Works

- **Schema enforcement.** The Python pipeline catches missing fields, bad dates, invalid categories. LLM mistakes are caught at ingest time, not query time.
- **Category-specific fields.** Each entity type has its own required data. Landfills need accepted_materials; competitors need areas_served. This makes the wiki machine-readable.
- **Auto-generated stubs.** `ingest.py` renders mechanical data from frontmatter. The LLM only needs to write Summary and Analysis — the judgment sections.
- **Single source of truth.** `schema.py` defines all categories and fields in one place. Adding a category means editing one file.
- **Rich stubs.** Wiki pages aren't empty templates — they have all mechanical data pre-rendered. The LLM sees pricing tables, material lists, and contact info before writing analysis.
- **Three-skill decomposition.** `/farm`, `/write-wiki`, `/synthesize` map cleanly to the Karpathy operations (ingest, maintain, query).

## What Doesn't Work

- **LLM execution.** DeepSeek struggled with the multi-step pipeline. Duplicate log entries, incomplete stubs, and index gaps are all evidence of the LLM losing track mid-process.
- **Log dedup.** `ingest.py` doesn't check for existing entries before appending. Re-running ingest on the same file creates duplicates.
- **Lint `--fix` unimplemented.** Advertised in `--help` but just prints a warning.
- **No automated triggers.** The LLM must manually run each pipeline step. There's no single-command "process this raw file end-to-end" that handles validation, fixup, standardization, ingest, and lint in one shot.
- **Stale log entries.** When categories were restructured, old log entries pointed to wrong paths. The log is append-only with no correction mechanism.
- **Category rigidity.** Adding a new category requires editing `schema.py`, `CLAUDE.md`, and potentially `ingest.py`. The system doesn't discover new categories dynamically.

## What Could Be Improved

- **Single-command pipeline.** A `process.py` script that chains validate → fixup → standardize → validate → ingest → lint. The LLM runs one command instead of six.
- **Log dedup.** Check for existing entries before appending. Hash the raw path + title and skip if it exists.
- **Implement `--fix`.** The linter should auto-fix simple issues (missing index entries, broken source links).
- **Test suite.** The scripts have no tests. A broken change to `schema.py` or `ingest.py` could silently corrupt the wiki.
- **Frontmatter search.** At scale, scanning the index won't be enough. A simple grep-based search or SQLite index over frontmatter would handle larger wikis.
- **Version tracking in frontmatter.** Add a `last_updated` field to wiki pages so staleness detection is based on content, not file mtime.

## Other Thoughts

This repo demonstrates both the power and the fragility of LLM-driven pipelines. The architecture is sound — the Python tooling adds exactly the right level of enforcement. The problem is that the LLM (DeepSeek) couldn't reliably execute the pipeline. Switching to a more capable model (Claude) should fix the execution issues, but the pipeline should also be more forgiving of partial completion. If the LLM crashes mid-pipeline, the next run should be able to pick up where it left off without creating duplicates or leaving incomplete state.

The category-specific schema is the most transferable pattern. Generic wikis treat every page the same. This repo treats landfills differently from competitors differently from strategies. That domain specificity is what makes the wiki useful for actual business decisions — you can compare landfill prices, map competitor coverage areas, or calculate pickup profitability because the data is structured, not just narrated.
