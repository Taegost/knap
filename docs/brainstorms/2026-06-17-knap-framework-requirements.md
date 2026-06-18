---
date: 2026-06-17
topic: knap-framework
---

# Knap Framework Requirements

## Summary

Knap is a generic, extensible framework for LLM-powered knowledge management and self-improvement. It installs as skills + scripts + hooks into any repo, giving the LLM persistent memory across sessions and a mechanism to improve its own tools over time. Script-first architecture: scripts handle mechanics, the LLM handles judgment. Two-step setup: platform-specific install script scaffolds the repo, `/knap init` customizes it through an interview. All skills are namespaced under `/knap`.

## Problem Frame

Every new project requires designing a memory system from scratch. Existing solutions are optimized for specific tasks and don't generalize. The result is wasted time, inconsistent patterns, and systems that work for one project but can't be reused. The target user is someone new to AI coding tools — coming from ChatGPT/Claude web interface, familiar with hallucinations and context but not with tokens, skills, or session management. They need the AI to stop forgetting things between sessions, and they need the system to get better with every use. Config files, firewalls, and complicated binaries are barriers. Install-and-go is the goal.

## Key Decisions

**Two-step installation.** Platform-specific install script (`.sh` for Mac/Linux, `.ps1` for Windows) handles file scaffolding and dependency checking — no user interaction. `/knap init` handles customization — interview, CLAUDE.md generation, content review. Separation keeps the installer usable across projects.

**Install script cleans up after itself.** Clones Knap repo, copies needed files into the target repo, removes the clone. Only the install script itself remains in the target repo. No leftover Knap source directories.

**Installed files live in `.knap/`.** All Knap-managed files (skills, scripts, schema, router, context) live in a `.knap/` directory inside the repo. Raw and wiki content lives in `raw/` and `wiki/` at the repo root.

**Script-first over LLM-first.** Scripts are deterministic, repeatable, and don't consume tokens. The LLM handles judgment (synthesis, analysis, research). Scripts handle everything else (validation, ingest, indexing, linting). "If you can use code instead of AI, you should."

**Python with venv.** All scripts are Python. A venv is created during installation to isolate dependencies and ensure reproducibility.

**Namespaced skills.** All skills are prefixed with `/knap` (e.g., `/knap init`, `/knap ingest`, `/knap synthesize`). Prevents collision with user-defined or plugin skills.

**Interview-first setup.** The `/knap init` skill interviews the user to understand the repo's purpose, existing conventions, and what matters. Responses are saved as a raw transcript.

**Existing CLAUDE.md is preserved and ingested.** Backed up, then parsed for hard requirements (e.g., "no secrets in source control"). Hard requirements are carried into the new CLAUDE.md. The rest becomes raw source material.

**Existing content review is user-choice.** For repos with existing content, `/knap init` asks: auto (review everything), plan (produce a review plan), or interview (ask what matters). Same options as the review step — respects the user's comfort level.

**Self-improvement loop deferred.** The mechanism for skills to improve every session is a separate design question. This requirements doc covers the memory and installation layers. The self-improvement loop gets its own brainstorm.

**Updates deferred.** How existing installations get Knap improvements is a separate design question. Marked for further discussion.

**Standard markdown links.** `[Page Name](../path/to/page.md)` for cross-references. Works in every markdown editor. Portable across machines and tools.

**YAML schema for categories.** `.knap/schema/categories.yaml` defines categories, required fields, and analysis labels. Each repo extends with its own domain. Single source of truth for both scripts and the LLM.

**Per-category indexes.** Each category gets its own `wiki/{category}/index.md`. A master `wiki/index.md` links to category indexes. Keeps individual index files small and context-efficient at scale.

## Key Flows

- F1. **Install** — User runs piped curl/wget (Mac/Linux) or irm/iex (Windows). Script clones Knap, checks Python + deps, creates venv, scaffolds `.knap/` + `raw/` + `wiki/` + `schema/`, copies skills and scripts, removes clone. Only the install script remains.
- F2. **Init** — User runs `/knap init`. Backs up existing CLAUDE.md. If existing content: asks auto/plan/interview. Interviews user (questions saved as raw transcript). Parses existing CLAUDE.md for hard requirements. Generates minimal CLAUDE.md with non-negotiables + router pointer. Reviews existing repo content per user's chosen mode. Ingests all raw data.
- F3. **Ingest** — User runs `/knap ingest <url>`. Fetches content, validates frontmatter, generates wiki stub, writes Summary and Analysis, updates index + log.
- F4. **Synthesize** — User runs `/knap synthesize <question>`. Researches from multiple sources, records as raw + wiki + index + log.
- F5. **Session startup** — LLM reads CLAUDE.md → ROUTER.md → loads only task-relevant files.

## Requirements

**Installation**

- R1. Separate install scripts per platform: `install.sh` (Mac/Linux) and `install.ps1` (Windows). No unified script — no reliable cross-platform shell exists.
- R2. Install script checks for Python 3.10+ and required packages. Creates a venv and installs deps into it.
- R3. Install script scaffolds the repo: creates `.knap/` (skills, scripts, schema, router, context), `raw/`, `wiki/` at repo root. Copies core skills and scripts. Does not touch CLAUDE.md.
- R4. Install script clones Knap repo to a temp location, copies files, then removes the clone. Only the install script remains in the target repo.

**Initialization**

- R5. `/knap init` backs up existing CLAUDE.md before modifying anything.
- R6. `/knap init` detects existing repo content. If content exists, asks: auto (review everything), plan (produce review plan), or interview (ask what matters). If empty, proceeds directly to interview.
- R7. `/knap init` interviews the user. Questions cover: repo purpose, what the user wants the LLM to remember, existing conventions, hard rules. Responses are saved as a raw transcript.
- R8. `/knap init` parses existing CLAUDE.md for hard requirements (non-negotiable rules). Carries them into the new CLAUDE.md.
- R9. `/knap init` generates a minimal CLAUDE.md with non-negotiables + router pointer. Keeps it under 30 lines.
- R10. Review findings are saved as raw files and ingested into the wiki.

**Memory**

- R11. Raw files have YAML frontmatter with required fields (title, source_url, date_farmed, category). Missing values use `"n/a"`, never omitted.
- R12. Wiki pages are auto-generated from raw frontmatter. Mechanical data (contact info, pricing, materials) is rendered by scripts. Judgment sections (Summary, Analysis) are written by the LLM.
- R13. Each category gets its own `wiki/{category}/index.md`. A master `wiki/index.md` links to category indexes.
- R14. `wiki/log.md` is append-only. Every operation gets a timestamped entry.
- R15. Lint script checks for orphans, un-ingested files, index accuracy, and frontmatter validity.

**Self-Improvement (deferred — separate brainstorm)**

- R16. Placeholder: skills improve every session. Mechanism TBD.

**Updates (deferred — separate brainstorm)**

- R17. Placeholder: mechanism for existing installations to receive Knap improvements. TBD.

## Scope Boundaries

**In scope:**
- Install scripts (per-platform)
- `/knap init` skill (interview + CLAUDE.md generation + content review)
- Memory pipeline (raw → wiki → index → log)
- Core scripts (validate, ingest, lint)
- Core skills (init, ingest, synthesize)
- YAML schema for categories
- Per-category indexes
- Python venv setup

**Deferred for later:**
- Self-improvement loop (separate brainstorm)
- Update mechanism (separate brainstorm)
- Pre-commit hooks
- Search fallback (BM25/embeddings) for scale
- Corrections checking (script + YAML file)

**Outside this framework's identity:**
- RAG, embeddings, vector databases
- Multi-agent support
- GUI/dashboard
- Specific domain knowledge (that's each repo's job)

## Outstanding Questions

**Deferred to planning:**
- OQ1. What's the minimal set of skills Knap ships with? (init, ingest, synthesize — anything else?)
- OQ2. Should the install script set up a git hook for lint, or leave that to the user?
- OQ3. How does the venv get activated? Automatic in skills, or manual instruction?

## Sources / Research

- `docs/synthesis-memory-framework-design.md` — synthesized from 5 methodologies
- `docs/methodology-1-karpathy-llm-wiki.md` through `docs/methodology-5-mex-scaffold-pattern.md` — individual reviews
- `raw/transcripts/` — Austin Marchese YouTube videos (board of advisors pattern, skill architecture, self-improvement loop)
- `~/_ws/wiki-AppalachianHaul` — Karpathy wiki implementation with Python pipeline
- `~/_ws/my_pos` — Personal Operating System with conversation archive
- `~/_ws/homelab-k8s` — mex integration branch (ROUTER.md, context/, GROW loop)
