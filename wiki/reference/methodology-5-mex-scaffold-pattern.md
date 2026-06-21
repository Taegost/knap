---
title: "Methodology 5: mex — Modular Scaffold Pattern"
category: reference
---

# Methodology 5: mex — Modular Scaffold Pattern

Source: https://github.com/theDakshJaitly/mex

---

## Brief Summary

mex replaces monolithic AI instruction files (like a single giant CLAUDE.md) with a modular scaffold — a directory of small, cross-referenced markdown files. The core insight is that context windows are finite and expensive, so only relevant context should be loaded for any given task. The architecture follows three tiers: an anchor file (tiny auto-loaded entry point), a router (routing table mapping task types to context files), and a context/patterns directory (the actual knowledge store).

The system uses YAML frontmatter with `edges` (cross-references with conditions) and `triggers` (keyword phrases that signal when a file should be loaded). A 5-step behavioral contract (CONTEXT → BUILD → VERIFY → DEBUG → GROW) ensures the scaffold evolves from real work. Three memory types: structural scaffold files (context and patterns), an append-only JSONL event log (decisions, notes, risks, todos), and an optional agent-memory mode with daily memory files and cleanup. An 11-checker drift detection system validates that scaffold claims match reality.

---

## My Thoughts

This is the most architecturally sophisticated of the five systems. The key insight — loading only task-relevant context instead of the full instruction file — solves the context window problem that the Karpathy pattern ignores. The 3-tier routing (anchor → router → context/patterns) is elegant: the anchor is tiny and always loaded, the router maps task types to specific files, and the context files are loaded only when relevant. Community testing showed ~60% average token reduction per session.

The GROW loop is the most important behavioral pattern. After every task, the agent must: Ground (name what changed), Record (update relevant files), Orient (create/update patterns), Write (bump timestamps, log decisions). This ensures the scaffold evolves from real work rather than upfront planning. "A pattern that turns out be obvious costs nothing" — patterns are created when they're needed, not before.

The frontmatter-driven cross-referencing is clever. Each file has `edges` that link to related files with conditions (e.g., "when specific technology details are needed, follow this edge to stack.md"). This creates a navigable knowledge graph that the LLM can traverse contextually. The `patterns/INDEX.md` serves as a lookup table — before starting any task, the agent checks if a matching pattern exists.

The drift detection system is the most robust of any of the five methodologies. 11 checkers validate paths, commands, dependencies, versions, cross-file consistency, edges, staleness, index sync, script coverage, tool config sync, TODO/FIXME markers, and broken links. The score starts at 100 and deducts per error/warning. This is real software engineering applied to knowledge management.

The main weakness is that the scaffold is designed for software projects, not general knowledge domains. The drift checkers validate file paths, package.json dependencies, and npm scripts — none of which apply to a business wiki or a content production repo. Adapting mex to a non-software domain requires disabling most of the drift detection.

---

## Detailed Implementation

### Architecture

```
.mex/
  AGENTS.md              Always-loaded operating contract (~50 lines)
  ROUTER.md              Session bootstrap + routing table (~85 lines)
  HEARTBEAT.md           Heartbeat check procedure
  SETUP.md               Population prompts for manual setup
  SYNC.md                Drift resync procedure
  config.json            scaffold_id, scaffold_name, aiTools config
  context/
    architecture.md      System overview and components
    stack.md             Technology choices and per-app patterns
    conventions.md       Naming, patterns, rules, safety habits
    decisions.md         Key decisions with reasoning
    setup.md             Dev environment and bootstrap
  events/
    decisions.jsonl      Append-only decision log
  patterns/
    INDEX.md             Pattern lookup table
    add-app.md           Deploy new app pattern
    add-database-app.md  Database-backed app pattern
    debug-sync-failure.md
    seal-secret.md
```

### The Three-Tier Routing System

**Tier 1 — Anchor-to-Router**: AGENTS.md (always auto-loaded) points to ROUTER.md. Hard redirect — no branching logic.

**Tier 2 — Router-to-Context**: ROUTER.md contains a routing table:
```markdown
| Task type | Load |
|---|---|
| System design | `context/architecture.md` |
| Technology decisions | `context/stack.md` |
| Writing/reviewing code | `context/conventions.md` |
| Design decisions | `context/decisions.md` |
| Environment setup | `context/setup.md` |
| Any specific task | `patterns/INDEX.md` |
```

**Tier 3 — Edge-Based Cross-Referencing**: Each file's YAML frontmatter contains `edges`:
```yaml
edges:
  - target: stack.md
    condition: "when specific technology details are needed"
  - target: decisions.md
    condition: "when understanding why the architecture is structured this way"
```

### The GROW Loop

5-step behavioral contract after every task:

1. **CONTEXT**: Load relevant files, check patterns/INDEX.md for matching pattern.
2. **BUILD**: Execute the work, following any matched pattern's steps.
3. **VERIFY**: Load conventions.md, run verification checklist.
4. **DEBUG**: If verification fails, check for debug patterns, fix, re-verify.
5. **GROW**:
   - **Ground**: Name what changed in reality.
   - **Record**: Update ROUTER.md's "Current Project State" if truth changed; surgically update relevant context/ files.
   - **Orient**: If the task can recur and no pattern exists, create one. If a pattern exists but a new gotcha was learned, update it.
   - **Write**: Bump `last_updated` on every changed file. Run `mex log --type decision` if the "why" matters.

### YAML Frontmatter Schema

```typescript
interface ScaffoldFrontmatter {
  name?: string;           // Matches filename without extension
  description?: string;    // When to load it
  edges?: FrontmatterEdge[]; // Cross-references with conditions
  last_updated?: string;   // YYYY-MM-DD
  triggers?: string[];     // Keyword phrases that signal when to load
}

interface FrontmatterEdge {
  target: string;          // Filename to link to
  condition?: string;      // When to follow this edge
}
```

### Three Memory Types

**A. Structural Memory (Scaffold Files)**
- context/*.md and patterns/*.md
- YAML frontmatter with edges, triggers, last_updated
- Updated surgically by the GROW loop

**B. Event Memory (JSONL Log)**
- events/decisions.jsonl
- Four event kinds: decision, note, risk, todo
- Each entry: timestamp, kind, message, files, cwd, optional trace/source/status
- Written via `mex log "<message>" --type decision|note|risk|todo`

**C. Agent-Memory Mode (Daily Files)**
- memory/ directory at project root
- Daily files named YYYY-MM-DD.md
- memory/.last-cleanup.json tracks cleanup
- Heartbeat system checks: stale scaffold files, cleanup due, old daily files
- When cleanup is due, promotes durable insights to MEMORY.md

### Drift Detection

11 checkers validate scaffold claims:

| Checker | What It Validates |
|---------|-------------------|
| path | Do referenced paths exist? |
| command | Do referenced commands exist? |
| dependency | Do dependencies exist in package.json? |
| version | Are versions consistent across files? |
| cross-file | Do multiple files agree on the same claim? |
| edges | Do frontmatter edge targets exist? |
| staleness | Are files updated within threshold? |
| index-sync | Is patterns/INDEX.md in sync with actual pattern files? |
| script-coverage | Are all package.json scripts documented? |
| tool-config-sync | Are AI tool configs in sync? |
| todo-fixme | Are there unresolved markers? |
| broken-link | Do local markdown links resolve? |

Score starts at 100, deducts 10 per error, 3 per warning, 1 per info.

---

## What Works

- **Context-efficient routing.** Loading only task-relevant context instead of the full instruction file. ~60% token reduction per session.
- **GROW loop.** The 5-step behavioral contract ensures the scaffold evolves from real work. Patterns are created when needed, not before.
- **Frontmatter-driven cross-referencing.** Edges with conditions create a navigable knowledge graph. The LLM follows contextual links rather than scanning everything.
- **Drift detection.** 11 checkers validate that scaffold claims match reality. The most robust verification system of any methodology reviewed.
- **Pattern categories.** Common tasks, integration patterns, debug/diagnosis, deploy/release. Patterns are created from real work, not upfront planning.
- **Append-only event log.** JSONL format for decisions, notes, risks, todos. Machine-parseable, append-only, no merge conflicts.
- **Incremental growth.** The scaffold is designed to grow incrementally. Setup seeds 2-5 critical patterns; the GROW loop creates the rest.

## What Doesn't Work

- **Software-project bias.** Drift checkers validate file paths, package.json dependencies, and npm scripts. None of these apply to non-software domains. Adapting to a business wiki or content repo requires disabling most checks.
- **Scaffold overhead.** YAML frontmatter with edges arrays, trigger lists, and last_updated dates adds structural weight. Each context file has 5-10 lines of frontmatter before the content starts.
- **No domain-specific schema.** The scaffold doesn't define category-specific fields (like the AppalachianHaul wiki's `accepted_materials` for landfills). Every context file is generic.
- **GROW compliance depends on the LLM.** The behavioral contract is an instruction, not enforcement. If the LLM skips the GROW step, the scaffold goes stale. The drift checker catches staleness but only when explicitly run.
- **Event log is flat.** JSONL with four event kinds. No hierarchy, no tagging, no filtering by context file. At scale, the log becomes noisy.
- **No browsable wiki layer.** The scaffold is designed for LLM navigation, not human browsing. There's no graph view, no backlinks, no Obsidian integration.

## What Could Be Improved

- **Domain-specific drift checkers.** Add checkers for non-software domains: frontmatter field validation, wikilink resolution, category-specific required fields. The checker framework is extensible — new checkers can be added without changing the core.
- **Add a browsable wiki layer.** The scaffold's edges create a graph. Expose that graph as wikilinks in a human-readable wiki layer. Obsidian could render the scaffold as a navigable knowledge base.
- **Typed edges.** Currently edges are generic "related to" links. Adding types (source, contradicts, supersedes, requires) would make relationships machine-readable and enable conflict detection.
- **Hierarchical event log.** Add context-file tags to event entries. Enable filtering by domain (e.g., "show all decisions related to auth").
- **Auto-trigger GROW.** Instead of relying on the LLM to remember the GROW loop, add a post-task hook that prompts the agent to update the scaffold.
- **Merge with Karpathy pattern.** The scaffold's routing and edges could enhance the Karpathy wiki pattern. Add a router to the AppalachianHaul wiki; add frontmatter edges to wiki pages.

## Other Thoughts

The mex pattern and the Karpathy pattern solve different problems. Karpathy optimizes for browsability — the wiki is a human-readable, interlinked knowledge base. mex optimizes for context efficiency — the scaffold loads only what's needed for the current task. A combined approach would be powerful: a browsable wiki with frontmatter-driven routing that loads only relevant pages.

The GROW loop is the most transferable behavioral pattern. Any system where an LLM maintains knowledge over time would benefit from the Ground → Record → Orient → Write cycle. The key insight is that knowledge maintenance should be a mandatory step after every task, not an occasional cleanup.

The drift detection system is the most transferable technical pattern. The claim extraction (extract structured claims from markdown) and checker framework (validate claims against reality) could be adapted to any domain. Add domain-specific checkers and you have a universal knowledge verification system.

The 60% token reduction is the killer metric. Context windows are the bottleneck for LLM-powered knowledge management. Loading only relevant context instead of the full instruction file is a fundamental improvement over the Karpathy pattern's "read the index, then read everything relevant" approach.
