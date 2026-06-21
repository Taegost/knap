# Conventions

## File Naming

- Lowercase, hyphens, derived from content title
- Raw files: `raw/{category}/{slug}.md`
- Wiki files: `wiki/{category}/{slug}.md`
- Examples: `youtube-channel-name.md`, `research-topic.md`

## Folder Classification

Folders are classified in `.knap/schema/folders.yaml`:

- **working** — folders actively used by the user (content lives here). Default: `wiki/`
- **system** — folders used by the knap system (infrastructure lives here). Default: `.knap/`
- **excluded** — folders entirely excluded from processing. Default: `.claude`, `.venv`, `.git`, `__pycache__`, `docs/brainstorms`, `docs/plans`

Scripts read this config via `load_folders.py`. Non-system and non-working folders are implicitly excluded.

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

## Index Files

Index files (`wiki/{category}/index.md`, `wiki/index.md`, `.knap/ROUTER.md`) are wiki pages with special behavior:

**Frontmatter:** Every index file has frontmatter with:
- `Parent` link to its parent index (category → `wiki/index.md`, master → `.knap/ROUTER.md`, ROUTER has no parent)
- `description` field summarizing the index contents

**Child links in body:** Child links on indexes live in the body as simple title links (`- [Title](filename.md)`), not in frontmatter. This is the sole exception to the "all system-related links are in frontmatter" rule.

**Parent link convention:** Every wiki page has a `Parent` link in its frontmatter pointing to its category index. When `add_frontmatter_link()` adds a `Parent` link where the target is an index file, it adds the page to the index body instead of creating a Child frontmatter reciprocal.

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

## Unit Testing

Every script created or modified must have corresponding unit tests. This is a hard requirement.

- **Framework:** pytest
- **Test files:** colocated in `.knap/scripts/` as `test_<module>.py`
- **Fixtures:** `tmp_path` for temporary directories, `monkeypatch` for environment control
- **Setup pattern:** `_setup_repo(tmp_path)` creates `.knap/schema/` and copies `categories.yaml`, then `monkeypatch.chdir(tmp_path)` for CWD-relative testing
- **Run:** `pytest .knap/scripts/` from repo root

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
