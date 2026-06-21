---
title: "Comparison of Memory Methodologies"
category: reference
---

# Comparison of Memory Methodologies

A side-by-side analysis of the five memory systems reviewed.

---

## At a Glance

| Dimension | Karpathy LLM Wiki | AppalachianHaul | homelab-curriculum | my_pos | mex |
|-----------|-------------------|-----------------|-------------------|--------|-----|
| **Primary purpose** | General knowledge base | Business intelligence wiki | Content quality enforcement | Personal advisory system | Context-efficient agent scaffold |
| **Knowledge structure** | Flat wiki pages | Category-specific wiki pages | Voice + corrections + stats | Advisor profiles + conversation archive | Modular context/pattern files |
| **Retrieval method** | Index → drill into pages | Index → drill into pages | Pre-commit enforcement | 12-file load order | 3-tier routing (anchor → router → context) |
| **Cross-referencing** | Wikilinks | Wikilinks | Module IDs, URLs, stat IDs | Wikilinks, expertise tags | Frontmatter edges with conditions |
| **Validation** | None | Python pipeline (5 scripts) | Pre-commit hook (12 checks) | Drift checker (8 checks) | Drift detection (11 checkers) |
| **Knowledge evolution** | Manual lint | Skill-driven pipeline | Append-only corrections | Conversation synthesis + corrections | GROW loop (mandatory post-task) |
| **Context efficiency** | Low (reads index + all relevant) | Low (reads index + all relevant) | Medium (reads voice + corrections) | High (12-file load order) | Very high (3-tier routing, ~60% reduction) |
| **Human browsability** | Excellent (Obsidian) | Excellent (Obsidian) | Good (dashboard + files) | Good (advisor profiles) | Poor (LLM-oriented) |
| **Domain coupling** | None (generic) | High (hauling business) | Very high (K8s content) | High (career coaching) | Medium (software projects) |
| **Scaling ceiling** | ~100 sources | ~200 entities | ~50 articles | ~20 advisors | ~100 context files |

---

## Pattern Comparison

### Knowledge Storage

**Karpathy/AppalachianHaul**: Flat markdown files in category directories. Each file is a self-contained entity page with YAML frontmatter. The wiki is browsable by humans and navigable by the LLM via the index.

**homelab-curriculum**: Three separate stores (voice synthesis, corrections index, stat tracker). Knowledge is fragmented across formats (markdown, YAML, JSON). Not browsable as a unified wiki.

**my_pos**: Two tiers (raw transcripts + synthesized profiles). The conversation archive adds a temporal dimension — knowledge includes the history of how it was used and corrected.

**mex**: Modular files with frontmatter-driven routing. Knowledge is split into context (what is true) and patterns (how to do things). Each file participates in a graph via edges.

**Verdict**: Karpathy/AppalachianHaul is best for browsable, domain-specific knowledge. mex is best for context-efficient agent operation. my_pos is best for persona-based advisory systems.

### Cross-Referencing

**Karpathy/AppalachianHaul**: `[[wikilinks]]` — simple, human-readable, Obsidian-native. No typed relationships. A wikilink from a landfill page to a recycling page doesn't specify the relationship type.

**homelab-curriculum**: Module IDs (P1M1, P1M2) for structural references, URLs for cross-post links, stat IDs for deduplication. Multiple reference systems for different purposes.

**my_pos**: Wikilinks plus expertise tags on consultants. The consultation skill uses keyword matching against tags to auto-select relevant advisors.

**mex**: Frontmatter `edges` with conditions. Each edge specifies a target file and when to follow it (e.g., "when specific technology details are needed"). This creates a navigable graph with conditional traversal.

**Verdict**: mex's edge system is the most sophisticated. Wikilinks are the simplest and most human-readable. The AppalachianHaul approach (wikilinks + category-specific frontmatter) is the best balance for a business wiki.

### Validation and Quality

**Karpathy**: None. The LLM is trusted to produce consistent output.

**AppalachianHaul**: Python pipeline (validate → fixup → standardize → validate → ingest → lint). 8 lint checks. Schema enforcement via `schema.py`. The most robust pipeline for raw file quality.

**homelab-curriculum**: Pre-commit hook with 12 blocking checks. Voice pattern enforcement, em dash density, passive voice limits, heading hierarchy. The most sophisticated content quality enforcement.

**my_pos**: Drift checker with 8 checks on a 100-point scale. Staleness detection for STATE.md. The drift checker is manual (not automated via hooks).

**mex**: 11 drift checkers validating paths, commands, dependencies, versions, cross-file consistency, edges, staleness, index sync, script coverage, tool config sync, TODO/FIXME markers, and broken links. The most comprehensive verification system, but biased toward software projects.

**Verdict**: mex has the most checkers. homelab-curriculum has the best content quality enforcement. AppalachianHaul has the best raw file validation. my_pos has the best staleness detection. A combined system would use AppalachianHaul's pipeline for raw files, homelab-curriculum's pre-commit hooks for content quality, mex's drift detection for knowledge verification, and my_pos's staleness detection for live state.

### Knowledge Evolution

**Karpathy**: Manual lint. The LLM runs health checks when asked. No mandatory maintenance step.

**AppalachianHaul**: Skill-driven pipeline. The `/farm`, `/write-wiki`, and `/synthesize` skills define structured workflows. The Prime Directive mandates recording synthesized answers immediately. But the pipeline is manual — the LLM must remember to run each step.

**homelab-curriculum**: Append-only corrections index. New errors are added, never removed. The stat tracker auto-populates on content write. No mechanism for corrections to expire or for stale knowledge to be flagged.

**my_pos**: Conversation synthesis. The system records every consultation, synthesizes patterns, and maintains a "Corrections Board Must Remember" section. The most self-aware evolution pattern — the system remembers its own mistakes.

**mex**: GROW loop (mandatory post-task). Ground → Record → Orient → Write. The agent must update the scaffold after every task. Patterns are created when needed, not before. The most disciplined evolution pattern.

**Verdict**: mex's GROW loop is the most disciplined. my_pos's conversation synthesis is the most self-aware. AppalachianHaul's skill pipeline is the most structured. A combined system would use the GROW loop as the mandatory post-task step, the corrections index for error tracking, and the skill pipeline for structured workflows.

### Context Efficiency

**Karpathy**: Reads index, then reads all relevant pages. At 100 sources, the index is ~200 lines. At 500 sources, the index is ~1000 lines — too large to scan in context.

**AppalachianHaul**: Same as Karpathy. The index is the retrieval surface. No tiered loading.

**homelab-curriculum**: Reads VOICE.md + corrections.yaml before every write. Fixed overhead regardless of task. The pre-commit hook runs all 12 checks on every commit.

**my_pos**: 12-file load order for `/ask-the-board`. Fixed overhead of ~15 files. The blog status is fetched live, adding latency.

**mex**: 3-tier routing. Anchor (always loaded, ~50 lines) → Router (~85 lines) → Context files (loaded only when relevant). ~60% token reduction per session.

**Verdict**: mex wins decisively on context efficiency. The 3-tier routing loads only what's needed. The other systems load everything that might be relevant.

---

## Transferable Patterns

### From Karpathy/AppalachianHaul
- **Raw/wiki/schema split.** Immutable sources → LLM-maintained pages → instruction file. Universal.
- **Category-specific frontmatter.** Different entity types have different required fields. Makes the wiki machine-readable.
- **Index-first retrieval.** Read the index, drill into relevant pages. Simple and effective at moderate scale.
- **Skill-driven workflows.** Repeatable operations defined as skill files. The LLM follows structured processes.

### From homelab-curriculum
- **Voice synthesis from raw samples.** Collect real writing samples, synthesize a voice reference, preserve human-detectable patterns.
- **Corrections index.** "Wrong → correct → context → source." Append-only, script-enforced.
- **Stat deduplication.** Track cited statistics across posts to prevent overuse.
- **Pre-commit quality gates.** Blocking validation before any commit touches content.

### From my_pos
- **Conversation archive.** Record consultations, synthesize patterns, maintain corrections. Institutional memory.
- **STATE.md.** Live state file with staleness detection. Solves the "what's happening now" problem.
- **Write-before-anything-else.** Persist raw data to disk immediately. Session crashes lose nothing.
- **Corrections as high-priority data.** When the user corrects the LLM, that correction is more valuable than the original advice.

### From mex
- **3-tier routing.** Anchor → Router → Context. Load only relevant context. ~60% token reduction.
- **GROW loop.** Ground → Record → Orient → Write. Mandatory post-task knowledge maintenance.
- **Frontmatter edges with conditions.** Cross-references that specify when to follow them. Creates a navigable graph.
- **Drift detection.** Extract structured claims from markdown, validate against reality. The most robust verification approach.
- **Pattern categories.** Common tasks, integration patterns, debug/diagnosis, deploy/release. Patterns from real work, not upfront planning.

---

## Recommendations for This Wiki

The AppalachianHaul wiki is a solid implementation of the Karpathy pattern. To scale beyond ~200 entities, consider:

1. **Add mex-style routing.** A thin router file that maps query types to specific wiki categories. Instead of reading the full index, the LLM reads the router, identifies the relevant category, and reads only that category's pages. This extends the scale ceiling from ~200 to ~1000+ entities.

2. **Add frontmatter edges.** Currently wikilinks are untyped. Adding `edges` to frontmatter (e.g., `related: [[davis-recycling]]`, `cheaper_than: [[omnisource]]`) makes relationships machine-readable and enables the LLM to follow contextual links.

3. **Adopt the corrections index.** Wrong prices, incorrect business hours, outdated phone numbers — these should be tracked in a corrections file and checked before every write. The homelab-curriculum pattern is directly applicable.

4. **Add a GROW loop.** After every `/farm`, `/write-wiki`, or `/synthesize` operation, the LLM should: Ground (what changed), Record (update relevant pages), Orient (create/update patterns if the task can recur), Write (bump timestamps, log to decisions.jsonl).

5. **Implement the full lint pipeline.** The `--fix` flag should be implemented. Log dedup should be added to `ingest.py`. The linter should run automatically via a pre-commit hook.

6. **Add a browsable wiki layer.** The wiki is already browsable in Obsidian. Adding mex-style edges and a router would make it navigable by both humans and LLMs.

7. **Consider mex's agent-memory mode.** For tracking business state (current leads, active projects, income), a STATE.md-like file with staleness detection would keep the wiki grounded in current reality.

---

## The Bottom Line

There is no single best methodology. Each solves a different problem:

- **Karpathy/AppalachianHaul**: Best for building browsable, domain-specific knowledge bases. Simple, human-readable, Obsidian-native.
- **homelab-curriculum**: Best for content quality enforcement. Voice synthesis, corrections tracking, stat deduplication, pre-commit hooks.
- **my_pos**: Best for persona-based advisory systems. Conversation archive, corrections memory, live state tracking.
- **mex**: Best for context-efficient agent operation. 3-tier routing, GROW loop, drift detection.

The right approach depends on what you're optimizing for. If you want a wiki you can browse in Obsidian, use the Karpathy pattern. If you want an LLM that writes in your voice, use homelab-curriculum. If you want a personal board of advisors, use my_pos. If you want an agent that loads only what it needs, use mex.

For this wiki, the Karpathy/AppalachianHaul pattern is the right foundation. The additions to consider are: mex-style routing for scale, corrections index for accuracy, GROW loop for evolution, and frontmatter edges for richer cross-referencing.
