# Structure

Knap is a generic, extensible framework for LLM-powered knowledge management and self-improvement. It blends mex-style routing (small anchor + router + context files) with a Karpathy-style raw-to-wiki pipeline (immutable sources → LLM-maintained pages).

Two pillars:
- **Memory** — retains knowledge across sessions (raw sources → wiki pages → index)
- **Self-improvement** — skills, scripts, and conventions get better with every use (GROW loop, feedback capture, script-first automation)

## Directory Layout

```
.knap/
  ROUTER.md           Task-type routing table + current project state
  context/            Framework documentation
    scope.md          Project purpose, goals, boundaries
    conventions.md    Rules, naming, hard constraints, workflow
    structure.md      This file — directory layout, how pieces relate
    decisions.md      Key choices and rationale
  schema/
    categories.yaml   Category definitions, required fields, analysis labels
  scripts/
    schema.py         Single source of truth (imports from categories.yaml)
    validate.py       Frontmatter validation
    ingest.py         Generate wiki stubs, update index + log
    lint.py           Structural checks
  .venv/              Python virtual environment

raw/                  Immutable source documents (organized by category)
  {category}/
    {slug}.md

wiki/                 LLM-maintained pages (mirrors raw/ structure)
  index.md            Master index — links to category indexes
  log.md              Append-only chronological record
  {category}/
    index.md          Per-category index
    {slug}.md

CLAUDE.md             Thin anchor — non-negotiables + router pointer
```

## How the Layers Interact

1. LLM reads CLAUDE.md (always) → ROUTER.md (task routing)
2. Router directs to relevant context/ files and wiki/index.md
3. Raw sources are processed through scripts into wiki pages
4. Schema defines categories, required fields, and conventions
5. Per-category indexes keep individual files small and context-efficient

## Design Principles

1. **General-purpose base.** Works for any knowledge domain. Domain specifics are extensions.
2. **Extensible.** Each repo customizes with its own categories, fields, workflows.
3. **Script-first.** Automate everything possible. LLM handles judgment; scripts handle mechanics.
4. **Token-efficient.** Load only what's needed for the current task.
5. **Editor-agnostic.** Works in any markdown editor. Standard markdown links.
6. **Reliable across LLMs.** Conventions and scripts enforce consistency.

## Raw vs Wiki

- **Raw** = immutable source. The LLM reads but never modifies. Contains the full original content.
- **Wiki** = LLM-maintained page. Auto-generated stubs from frontmatter + LLM-written judgment sections (Summary, Analysis).
