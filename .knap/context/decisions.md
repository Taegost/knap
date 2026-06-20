# Decisions

Key architectural choices and their rationale.

## Cross-Reference Format

**Decision:** Standard markdown links (`[Page Name](../path/to/page.md)`)

**Rationale:** Editor-agnostic. Works in Obsidian, VS Code, any markdown editor. Parseable by both humans and LLMs. Relative paths ensure links work regardless of clone location.

**Trade-off:** Wikilinks are more concise and Obsidian-native. If Obsidian becomes the primary editor and cross-editor portability is less important, wikilinks could be reconsidered.

**Frontmatter vs body:** Frontmatter links use repo-root-relative paths. Body links can use either repo-root-relative or file-relative.

## Typed Links

**Decision:** Frontmatter `links` field with typed relationships replaces the hardcoded `source` field.

**Rationale:** The `source` field only tracked ingestion provenance. Typed links support richer relationships: `Parent`/`Child` for hierarchy, `Supersedes`/`SupersededBy` for versioning, `IngestedFrom`/`IngestedTo` and `SynthesizedFrom`/`SynthesizedTo` for provenance. `Related` is the default type.

**Link type set:** 9 base types with bidirectional pairs. Extensible per-repo via `categories.yaml` `link_types` key.

**Single entry point:** `add_frontmatter_link()` is the sole entry point for writing frontmatter links. It handles deduplication, type updates, and reciprocal link generation. No script writes to the `links` field directly.

**Format:** `[name](path)` markdown link format for targets. Allows markdown IDEs to traverse links natively.

**source → IngestedFrom:** The `source` frontmatter field is replaced by an `IngestedFrom` entry in `links`. Existing wiki pages are migrated by `convert_frontmatter.py --migrate-source`.

## Retrieval Strategy

**Decision:** Hybrid — router + index + search fallback

**Rationale:** No single retrieval strategy works at all scales. The router handles common tasks efficiently. The index handles browsing and exploration. A search fallback handles queries that don't match categories.

**Scale tiers:**
- <200 pages: Router + index
- 200-1000 pages: Router + index + grep search
- 1000+ pages: Router + index + BM25/embeddings

## Script-First Architecture

**Decision:** Scripts handle all mechanics; LLM only writes judgment sections

**Rationale:** Scripts are deterministic, repeatable, and don't consume tokens. The LLM handles judgment (synthesis, analysis, research). Scripts handle everything else (validation, ingest, indexing, logging, linting). "If you can use code instead of AI, you should."

**What gets scripted:** Frontmatter validation, wiki stub generation, index updates, log updates, structural lint checks.

**What the LLM does:** Research, write Summary and Analysis sections, decide cross-references, run GROW loop.

## Schema Definition

**Decision:** `categories.yaml` (YAML) as single source of truth

**Rationale:** Human-readable, script-parseable, editor-agnostic. Scripts can read it with `yaml.safe_load()`. Humans can edit it in any text editor. The schema defines categories, required fields, and analysis labels.

## Per-Category Indexes

**Decision:** Each category gets `wiki/{category}/index.md`, master `wiki/index.md` links to them

**Rationale:** Keeps individual index files small and context-efficient at scale. Master index provides overview without bloating context.

## Fields Can Be Omitted

**Decision:** Unknown fields are simply absent from frontmatter (no `"n/a"` convention)

**Rationale:** Aligns with OKF's permissive consumption. Scripts tolerate missing fields gracefully. Cleaner frontmatter.

## Context Layer Structure

**Decision:** 4 files — `scope.md`, `conventions.md`, `structure.md`, `decisions.md`

**Rationale:** Covers 80% of projects without over-engineering. Each file has a clear purpose: scope defines what/why, conventions define rules, structure defines layout, decisions records choices.
