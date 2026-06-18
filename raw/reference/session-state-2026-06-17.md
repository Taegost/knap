---
title: "Session State — 2026-06-17"
source_url: "n/a"
date_farmed: 2026-06-17
category: reference
description: "Current project state, key decisions, and what's next. Updated at end of each session."
tags: [session-state, meta]
---

## What Knap Is

Framework for LLM-powered knowledge management and self-improvement. Two pillars: memory (retain knowledge across sessions) and self-improvement (skills/scripts get better with every use). Script-first — scripts handle mechanics, LLM handles judgment. OKF-aligned.

## What's Built

- CLAUDE.md (thin anchor) + ROUTER.md (task routing)
- context/architecture.md, context/conventions.md
- schema/categories.yaml (4 categories: transcript, research, reference, prompt)
- scripts: schema.py, validate.py, ingest.py, lint.py, fetch_youtube_transcript.py
- Skills: ingest, synthesize (in .claude/skills/)
- 2 YouTube transcripts ingested (Austin Marchese videos with verbatim prompts)
- 7 methodology docs in docs/
- Strategy doc with checklist
- Requirements doc from brainstorm
- Implementation plan (7 units) in docs/plans/

## Key Decisions

- CLAUDE.md stays at repo root, everything else moves to .knap/
- Context layer: scope.md, conventions.md, structure.md, decisions.md
- Skills hyphenated: knap-ingest, knap-synthesize (stay in .claude/skills/)
- Per-category indexes + master index
- Python venv in .knap/.venv/
- OKF alignment (Google Open Knowledge Format)
- Tags field for cross-cutting categorization
- Fields can be omitted (drop "n/a" convention)
- Optional typed links in frontmatter (links list with target + optional type)
- Body markdown links still valid alongside frontmatter links
- Link types: Parent, Child, Related, Superseded By, Supersedes, Source

## What's Next

1. Execute the plan — U1 (move to .knap/) first
2. Self-improvement loop — separate brainstorm (deferred)
3. Install scripts — separate plan (deferred)
4. /knap init skill — separate plan (deferred)
5. Patterns/, Events/ — investigate later

## Important Context

- Target user: "me 2 months ago" — beginner-friendly, no config, install and go
- "Good enough for 80% of use cases with almost no effort"
- "Plan the what/why. Fail fast on the how."
- Skills stay in .claude/skills/ for Claude Code discovery
- User's adapted skill-identification prompt saved in raw/prompts/skill-identification.md
