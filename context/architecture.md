# Architecture

Knap is a generic, extensible memory framework for LLM-powered knowledge management. It blends mex-style routing (small anchor + router + context files) with a Karpathy-style raw-to-wiki pipeline (immutable sources → LLM-maintained pages).

## Design Principles

1. **General-purpose base.** Works for any knowledge domain. Domain specifics are extensions.
2. **Extensible.** Each repo customizes with its own categories, fields, workflows.
3. **Script-first.** Automate everything possible. LLM handles judgment; scripts handle mechanics.
4. **Token-efficient.** Load only what's needed for the current task.
5. **Editor-agnostic.** Works in any markdown editor. Standard markdown links.
6. **Reliable across LLMs.** Conventions and scripts enforce consistency.

## Directory Structure

```
CLAUDE.md           Thin anchor — non-negotiables + router pointer
ROUTER.md           Task-type routing table + current project state
context/            Framework documentation (architecture, conventions)
raw/                Immutable source documents (organized by category)
wiki/               LLM-maintained pages (mirrors raw/ structure)
  index.md          Content catalog (generated)
  log.md            Append-only chronological record
schema/             Categories, corrections, conventions
scripts/            Automated pipeline (validate, ingest, lint)
.claude/skills/     LLM workflows (ingest, synthesize, improve)
```

## How the Layers Interact

1. LLM reads CLAUDE.md (always) → ROUTER.md (task routing)
2. Router directs to relevant context/ files and wiki/index.md
3. Raw sources are processed through scripts into wiki pages
4. Skills define structured workflows for common operations
5. Schema defines categories, required fields, and conventions
