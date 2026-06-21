# Concepts

Shared domain vocabulary for this project — entities, named processes, and status concepts with project-specific meaning. Seeded with core domain vocabulary, then accretes as ce-compound and ce-compound-refresh process learnings; direct edits are fine. Glossary only, not a spec or catch-all.

## Content Types

**Raw file** — Immutable source content. The LLM reads but never modifies raw files. Contains the full original content with YAML frontmatter. Lives under `raw/{category}/`.

**Wiki page** — LLM-maintained page with auto-generated stubs from frontmatter plus LLM-written analysis sections (Summary, Analysis). Lives under `wiki/{category}/`. Every raw file should have a corresponding wiki page after ingestion.

**Index file** — A file (typically `index.md` or `ROUTER.md`) that lists and links to the pages in its directory. Category indexes list pages in their body; the master index links to category indexes. Index files have frontmatter (Parent link to their containing index, description field). The sole deviation from frontmatter-based links: Child links live in the body as simple title links, not in frontmatter. When `add_frontmatter_link()` writes a Parent link targeting an index, it adds the page to the index body automatically.

## Link Concepts

**Frontmatter link** — A typed link in a file's YAML `links` field. Each link has a `target` (markdown link format `[name](path)`) and a `type` (e.g., `Related`, `Parent`, `Child`, `IngestedFrom`). Types come in bidirectional pairs: writing one side auto-generates the reciprocal.

**Wikilink** — An Obsidian-style `[[Page Name]]` link in body content. Without a pipe, resolves to an exact filename match with `.md` extension in the same category folder (case-sensitive). With a pipe (`[[path|display]]`), the path portion follows standard link resolution.

## Validation Concepts

**Orphan** — A file in a working or system folder that has no incoming links from any other file. Detected by scanning all frontmatter links, body markdown links, and wikilinks. Index files are structural and exempt from orphan checks.

**Index ghost** — A category index entry that points to a page file that doesn't exist on disk. The index lists it but the file is missing.

**Folder classification** — The scheme that categorizes directories for script processing. Three types: **working** (user content, e.g., `wiki/`), **system** (knap infrastructure, e.g., `.knap/`), and **excluded** (skipped entirely, e.g., `.git`, `docs/brainstorms`). Defined in `.knap/schema/folders.yaml`.
