# Conventions

## File Naming

- Lowercase, hyphens, derived from content title
- Raw files: `raw/{category}/{slug}.md`
- Wiki files: `wiki/{category}/{slug}.md`
- Examples: `youtube-channel-name.md`, `research-topic.md`

## YAML Frontmatter

Every raw and wiki file has YAML frontmatter. Required fields are defined in `.knap/schema/categories.yaml`.

```yaml
---
title: "Title Here"
source_url: "https://..."
date_farmed: YYYY-MM-DD
category: "{category}"
---
```

Fields may be omitted when unknown. Scripts tolerate missing fields gracefully. Use `[]` for "none found" lists.

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
python3 .knap/scripts/validate.py raw/{category}/
python3 .knap/scripts/ingest.py raw/{category}/*.md
python3 .knap/scripts/lint.py
```

## Session State

Session state lives at `raw/reference/session-state-*.md`. It's a living document — update it as significant decisions are made or state changes, not just at session end. ROUTER.md links to it. The next session reads ROUTER.md → follows the link → knows where we left off.

## GROW Loop

After every task:
1. **Ground** — name what changed
2. **Record** — update relevant wiki pages, session state, router state
3. **Orient** — create/update skill if task can recur
4. **Write** — bump timestamps, log to wiki/log.md
