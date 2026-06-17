# Conventions

## File Naming

- Lowercase, hyphens, derived from content title
- Raw files: `raw/{category}/{slug}.md`
- Wiki files: `wiki/{category}/{slug}.md`
- Examples: `youtube-channel-name.md`, `research-topic.md`

## YAML Frontmatter

Every raw and wiki file has YAML frontmatter. Required fields are defined in `schema/categories.yaml`.

```yaml
---
title: "Title Here"
source_url: "https://..."
date_farmed: YYYY-MM-DD
category: "{category}"
---
```

Missing values: use `"n/a"` for unknown scalars, `[]` for "none found" lists. Never omit a field.

## Cross-References

Standard markdown links: `[Page Name](../path/to/page.md)`

Works in every markdown editor. Relative paths ensure links work regardless of clone location.

## Raw vs Wiki

- **Raw** = immutable source. The LLM reads but never modifies. Contains the full original content.
- **Wiki** = LLM-maintained page. Auto-generated stubs from frontmatter + LLM-written judgment sections (Summary, Analysis).

## Wiki Page Structure

```markdown
---
source: "raw/{category}/{slug}.md"
date_ingested: YYYY-MM-DD
---

# Title

## Summary
<!-- 2-4 sentence synthesis -->

## Details
<!-- Auto-generated from frontmatter by ingest.py -->

## Analysis
<!-- Category-specific judgment section -->
```

## Pipeline

```bash
python3 scripts/validate.py raw/{category}/
python3 scripts/ingest.py raw/{category}/*.md
python3 scripts/lint.py
```

## GROW Loop

After every task:
1. **Ground** — name what changed
2. **Record** — update relevant wiki pages, router state
3. **Orient** — create/update skill if task can recur
4. **Write** — bump timestamps, log to wiki/log.md
