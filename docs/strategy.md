---
date: 2026-06-17
---

# Knap Strategy

## Core Values

**Simplicity over perfection.** Good enough for 80% of use cases with almost no effort beats a perfect system that requires configuration. The target user is "me 2 months ago" — new to AI coding tools, frustrated by amnesia, just wants it to work.

**Script-first.** If a script can do it, let the script do it. Scripts are deterministic, repeatable, and don't consume tokens. The LLM handles judgment; scripts handle mechanics. "If you can use code instead of AI, you should."

**Memory is invisible.** The user shouldn't have to think about the memory system. It works in the background. Knowledge is captured automatically during normal use. The user focuses on their work; Knap handles the bookkeeping.

**Self-improvement is the loop.** Every session makes the system better. Skills get sharper. Scripts get more capable. Corrections get baked in. The system on day 30 is better than the system on day 1.

**Portable by default.** Works in any markdown editor, any AI tool, any repo. No tool-specific dependencies. Standard markdown links. YAML frontmatter. Plain text files.

## Development Principles

**Plan the "what" and "why." Fail fast on the "how."** Requirements docs and strategy are deliberate and thorough — they define what we're building and why. Implementation is disposable and iterative — build the minimum, test it, see what breaks, fix it. The plan tells us where to aim; failing fast tells us how to get there. Code is cheap to change. Direction is expensive to change.

**Build from the ground up.** Start with the smallest useful thing. Add complexity only when the simple version proves insufficient.

**Namespace everything.** Skills are prefixed with `/knap`. Files live in `.knap/`. No collisions with user-defined or plugin content.

**Cross-platform from day one.** Separate install scripts per platform. Python for all scripts (no shell-specific logic in the tooling). venv for dependency isolation.

## Deferred Items

These are tracked here until they get their own brainstorm/planning session.

**Self-improvement loop** — How skills improve every session. The "one-time fix or forever?" question. Feedback capture. Skill versioning. Needs its own brainstorm.

**Update mechanism** — How existing installations receive Knap improvements. Pull from repo? Piped installer re-run? Manual copy? Needs its own brainstorm.

**Pre-commit hooks** — Automated lint/validation before commit. Deferred until the core pipeline is stable.

**Search fallback** — BM25 or embeddings for scale beyond what the index can handle. Deferred until the index proves insufficient.

**Corrections checking** — Script + YAML file for known-wrong terms. Deferred until we have enough content to need it.

**Per-category index generation** — The current `ingest.py` updates a single master index. Needs refactoring for per-category indexes + master index.

**Install script** — `install.sh` and `install.ps1` for cross-platform installation. Not yet built.

**`/knap init` skill** — Interview + CLAUDE.md generation + content review. Not yet built.

## Checklist

### Foundation (current phase)

- [x] CLAUDE.md (thin anchor)
- [x] ROUTER.md (task routing)
- [x] context/architecture.md
- [x] context/conventions.md
- [x] schema/categories.yaml
- [x] schema/corrections.yaml (empty)
- [x] scripts/schema.py
- [x] scripts/validate.py
- [x] scripts/ingest.py
- [x] scripts/lint.py
- [x] scripts/fetch_youtube_transcript.py
- [x] .claude/skills/ingest/SKILL.md
- [x] .claude/skills/synthesize/SKILL.md
- [x] wiki/index.md (master)
- [x] wiki/log.md
- [x] First content ingested (2 YouTube transcripts)

### Next up

- [ ] Strategy doc (this file) — finalize
- [ ] Rename skills to `/knap` prefix (ingest → knap-ingest, synthesize → knap-synthesize)
- [ ] Move framework files to `.knap/` directory structure
- [ ] Update scripts to read schema from `.knap/schema/`
- [ ] Per-category indexes + master index refactor
- [ ] Python venv setup in install flow

### Installation

- [ ] `install.sh` (Mac/Linux) — clone, copy, clean up, venv, deps
- [ ] `install.ps1` (Windows) — same
- [ ] Test on clean repos (empty, existing content, existing CLAUDE.md)

### Skills

- [ ] `/knap init` skill — interview + CLAUDE.md generation + content review
- [ ] Update `/knap ingest` — prompt extraction for transcripts
- [ ] Update `/knap synthesize` — verify it works with new directory structure

### Self-Improvement (separate brainstorm)

- [ ] Brainstorm session for self-improvement loop
- [ ] Feedback capture mechanism
- [ ] Skill versioning
- [ ] "One-time fix or forever?" integration

### Updates (separate brainstorm)

- [ ] Brainstorm session for update mechanism
- [ ] How existing installations get improvements

### Windows (separate plan)

- [ ] `install.ps1` (Windows PowerShell installer)
- [ ] Verify Python venv works on Windows
- [ ] Test skill/script paths on Windows

### Patterns (investigate later)

- [ ] `patterns/` — procedural knowledge for recurring tasks
- [ ] Task-specific runbooks with gotchas, steps, verification checklists
- [ ] Separate from context layer — different concern

### Events (investigate later)

- [ ] `events/` — structured JSONL log for Knap internals
- [ ] Separate from `wiki/log.md` (prose log for end-user content)
- [ ] Decision, note, risk, todo event types
