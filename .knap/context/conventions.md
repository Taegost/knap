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

**Frontmatter links** use repo-root-relative paths (e.g., `[name](raw/transcripts/file.md)`).
**Body markdown links** can use either repo-root-relative or file-relative paths — both are valid.

## Frontmatter Links

Wiki and raw files support typed links in frontmatter via the `links` field.

```yaml
links:
  - target: "[Other Page](wiki/other-page.md)"
    type: Related
  - target: "[Another Page](wiki/another.md)"  # type defaults to Related
  - target: "[Paper](raw/research/some-paper.pdf)"
```

**Link types:** `Related` (default), `Parent`/`Child`, `Supersedes`/`SupersededBy`, `IngestedFrom`/`IngestedTo`, `SynthesizedFrom`/`SynthesizedTo`. Extensible via `categories.yaml` `link_types` key.

**Target format:** `[name](path)` — markdown link format. Paths are repo-root-relative for internal files, full URIs for external resources.

**Entry point:** All scripts that add frontmatter links must use `add_frontmatter_link()`. It handles deduplication, type updates, and reciprocal link generation.

## Serialization

Frontmatter serialization uses `yaml.dump(data, default_flow_style=False, sort_keys=False)`. This follows the patterns from the markdown-first converter plan. Manual string formatting is not used — it breaks on dict-in-list structures like `links`.

## Raw vs Wiki

- **Raw** = immutable source. The LLM reads but never modifies. Contains the full original content.
- **Wiki** = LLM-maintained page. Auto-generated stubs from frontmatter + LLM-written judgment sections (Summary, Analysis).

## Wiki Page Structure

```markdown
---
links:
  - target: "[slug.md](raw/{category}/{slug}.md)"
    type: IngestedFrom
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

## Script Path Resolution

All production scripts (`.knap/scripts/*.py`) use **CWD-relative paths** and assume CWD = repo root. Invocation: `python3 .knap/scripts/<name>.py` from the repo root.

- Paths are plain strings wrapped in `Path()`: `Path("wiki/index.md")`, `Path("raw/...")`, `Path(".knap/schema/categories.yaml")`
- No `__file__`-relative resolution in production scripts
- **Test files are excluded** — `__file__`-relative resolution is standard pytest practice

## GROW Loop

After every task:
1. **Ground** — name what changed
2. **Record** — update relevant wiki pages, session state, router state
3. **Orient** — create/update skill if task can recur
4. **Write** — bump timestamps, log to wiki/log.md
