---
title: "Methodology 1: Karpathy LLM Wiki"
category: reference
---

# Methodology 1: Karpathy LLM Wiki

Source: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f (April 2026)

---

## Brief Summary

Andrej Karpathy proposes a pattern where an LLM builds and maintains a persistent, interlinked markdown wiki from raw source documents. Instead of RAG-style retrieval from raw files at query time, the LLM incrementally compiles knowledge into structured wiki pages that persist across sessions. The wiki is a "compounding artifact" — cross-references are pre-built, contradictions pre-flagged, and synthesis reflects all ingested material. Three layers: raw sources (immutable), wiki (LLM-owned), and schema (the instruction file that transforms a generic LLM into a disciplined wiki maintainer).

Two special files: `index.md` (content catalog with one-line summaries, organized by category) and `log.md` (append-only chronological record). Three operations: ingest (process new sources into wiki pages), query (read wiki to answer questions, with good answers filed back), and lint (health-check for contradictions, stale claims, orphans, missing cross-references).

The pattern works because "the tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping." LLMs don't get bored updating cross-references or maintaining consistency.

---

## My Thoughts

This is a genuinely elegant pattern. The key insight — that knowledge should be compiled once and kept current rather than re-derived on every query — solves a real problem with RAG approaches. At small scale (~100 sources, hundreds of pages), a flat index with wikilinks is surprisingly effective and avoids the complexity of vector databases or embedding pipelines.

The pattern is intentionally abstract, which is both its strength and its weakness. It's flexible enough to adapt to any domain, but it provides no guidance on schema design, validation, or what happens when the wiki grows beyond what fits in context. The "index first, then drill into pages" retrieval strategy works until the index itself becomes too large to scan.

The Obsidian-as-IDE metaphor is apt — the wiki is genuinely browsable in ways that a RAG pipeline isn't. Graph view, backlinks, and Dataview queries add real value on top of the LLM's work.

The community comments reveal a rich ecosystem of extensions: provenance tracking, contradiction preservation (rather than reconciliation), concept renaming, and relationship graphs. The most interesting critique is that treating contradiction as a defect breaks in humanities domains — a typed edge system that preserves contradictions would be more robust.

---

## Detailed Implementation

### Architecture

Three directories at repo root:

```
raw/          Immutable source documents. LLM reads, never modifies.
wiki/         LLM-maintained markdown pages. Cross-referenced with wikilinks.
CLAUDE.md     Schema and conventions. Co-evolved over time.
```

### The Schema (CLAUDE.md)

The schema file is the "key configuration" — it transforms a generic LLM into a wiki maintainer. It defines:
- Directory structure and naming conventions
- Page templates (what fields go where)
- Frontmatter conventions (YAML for structured metadata)
- Cross-referencing rules (wikilinks for all internal links)
- Ingest workflow (what the LLM does when processing a new source)
- Query workflow (how the LLM reads the wiki to answer questions)
- Lint workflow (what health checks to run)
- Index and log maintenance rules

The schema co-evolves — conventions are added as patterns emerge, not upfront.

### Index (index.md)

A content-oriented catalog. Every wiki page gets a one-line entry organized by category. The LLM reads this first when answering queries — it's the retrieval surface. Updated on every ingest.

Format:
```markdown
## Landfills
- [[carter-county-landfill]] — County-run, $45/ton, Mon-Fri 7-3:30

## Recycling
- [[davis-recycling-johnson-city]] — Copper, aluminum, steel; $3.60/lb copper
```

### Log (log.md)

Chronological, append-only. Consistent entry prefixes for unix tool parseability:
```
## [2026-04-02] ingest | Article Title
## [2026-04-02] query | Question asked
## [2026-04-02] lint | Health check
```

### Operations

**Ingest**: User drops source into raw/, tells LLM to process. LLM reads source, discusses takeaways, writes summary page, updates index, updates relevant entity/concept pages across wiki, appends log entry. A single source might touch 10-15 wiki pages.

**Query**: User asks questions. LLM reads index, drills into relevant pages, synthesizes cited answers. Good answers can be filed back as new wiki pages — "explorations compound in the knowledge base just like ingested sources do."

**Lint**: LLM health-checks for contradictions, stale claims, orphan pages, missing cross-references, data gaps fillable via web search.

### Retrieval

No embedding/RAG. The LLM reads `index.md` first, identifies relevant pages, reads those pages, then synthesizes. Works at moderate scale (~100 sources, hundreds of pages). For larger wikis, Karpathy suggests CLI search tools like `qmd` (hybrid BM25/vector search).

---

## What Works

- **Simplicity.** Three directories, two special files, three operations. No infrastructure beyond markdown and git.
- **Compounding knowledge.** Good queries become new wiki pages. Knowledge builds on itself rather than being re-derived.
- **Browsability.** Obsidian's graph view, backlinks, and Dataview queries make the wiki genuinely navigable by humans, not just the LLM.
- **Index-first retrieval.** Reading a flat index before drilling into pages is fast, predictable, and avoids RAG hallucination.
- **Git-native.** Version history, branching, and collaboration come free.
- **Low maintenance cost.** LLM handles all bookkeeping — cross-references, consistency, summaries. Human focuses on sourcing and questioning.

## What Doesn't Work

- **Scale ceiling.** The index-first retrieval pattern breaks when the index itself is too large for the LLM to scan in context. No guidance on what happens at 500+ pages.
- **No validation.** No schema enforcement, no frontmatter validation, no structural checks. The LLM can produce inconsistent pages and nothing catches it.
- **No drift detection.** No mechanism to detect when wiki claims have gone stale or when raw sources have been updated.
- **No conflict resolution strategy.** What happens when two sources contradict each other? The gist says "note contradictions" but provides no pattern for how.
- **Single-LLM assumption.** The pattern assumes one LLM maintaining one wiki. No guidance on concurrent edits, merge conflicts, or multi-agent maintenance.
- **Context window dependency.** All retrieval happens in-context. At scale, the LLM can't read the full index plus relevant pages plus the query in one pass.

## What Could Be Improved

- **Add schema validation.** Frontmatter should be enforced — required fields, valid categories, date formats. Catch errors at ingest time, not query time.
- **Add a lint pipeline.** Automated checks for orphans, broken wikilinks, stale pages, missing index entries. Run it before committing.
- **Add a fixup step.** When the LLM produces inconsistent frontmatter, a script should normalize it (fill defaults, standardize formats).
- **Typed cross-references.** Instead of plain `[[wikilinks]]`, use typed edges in frontmatter (e.g., `source:`, `related:`, `contradicts:`) to make relationships machine-readable.
- **Tiered retrieval.** For large wikis, add a search layer (BM25 or embeddings) on top of the index. The index remains the primary surface but a search fallback handles queries that don't match categories.
- **Separate concerns in the schema.** A single CLAUDE.md works at small scale but grows unwieldy. Split into: schema definition, workflow instructions, and domain-specific conventions.

## Other Thoughts

The community responses reveal that this pattern resonates broadly but needs adaptation per domain. The most important gap is the contradiction problem — in technical domains, contradictions are errors to fix; in research or humanities, contradictions are information to preserve. A mature implementation needs a relationship type system that handles both.

The Memex parallel is apt. Vannevar Bush's 1945 vision was "a personal, curated knowledge store with associative trails between documents." The missing piece was who does the maintenance. LLMs solve that.

The pattern's real value isn't the wiki itself — it's the discipline. The schema forces the LLM to follow a consistent process, and that consistency is what makes the wiki useful over time. Without the schema, the LLM produces chat history. With it, the LLM produces a compounding knowledge base.
