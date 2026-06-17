# Router

Read CLAUDE.md first. Then identify your task type below and load only the files listed.

## Routing Table

| Task type | Load |
|---|---|
| Ingesting new source | `schema/categories.yaml`, `context/conventions.md` |
| Synthesizing research | `schema/categories.yaml`, `context/conventions.md`, `wiki/index.md` |
| Writing wiki content | `schema/categories.yaml`, `context/conventions.md`, relevant raw + wiki files |
| Answering a query | `wiki/index.md`, then drill into relevant wiki pages |
| Health check | Run `scripts/lint.py` |
| Adding a category | `schema/categories.yaml`, `context/conventions.md` |
| Improving the system | `context/conventions.md`, relevant skills in `.claude/skills/` |

## Current Project State

<!-- Updated by GROW loop or manually -->
Last updated: 2026-06-17

Knap is an early-stage memory framework. Core architecture is in place: raw/wiki/schema structure, routing, transcript fetcher. Ingest and synthesize skills are being built. No content ingested yet.
