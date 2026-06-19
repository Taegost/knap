# Scope

## Purpose

Knap is a generic, extensible framework for LLM-powered knowledge management and self-improvement. It installs as skills + scripts + hooks into any repo, giving the LLM persistent memory across sessions and a mechanism to improve its own tools over time.

## Problem

Every new project requires designing a memory system from scratch. Existing solutions are optimized for specific tasks and don't generalize. The result is wasted time, inconsistent patterns, and systems that work for one project but can't be reused.

## Goals

- **Persistent memory across sessions.** The LLM stops forgetting things between sessions.
- **Script-first automation.** Scripts handle mechanics; the LLM handles judgment. Deterministic, repeatable, token-efficient.
- **Generic base layer.** Works for any knowledge domain. Domain specifics are extensions, not core.
- **Invisible operation.** The user shouldn't have to think about the memory system. It works in the background.
- **Self-improvement.** Every session makes the system better — skills get sharper, scripts get more capable, corrections get baked in.

## Boundaries

**In scope:**
- Memory pipeline (raw sources → wiki pages → index → log)
- Core scripts (validate, ingest, lint)
- Context layer (scope, conventions, structure, decisions)
- Schema system (categories, fields, analysis labels)
- Per-category indexes

**Out of scope:**
- RAG, embeddings, vector databases
- Multi-agent support
- GUI/dashboard
- Specific domain knowledge (that's each repo's job)
- Self-improvement loop mechanism (separate brainstorm)
- Update mechanism for existing installations (separate brainstorm)

## Target User

Someone new to AI coding tools — coming from ChatGPT/Claude web interface, familiar with hallucinations and context but not with tokens, skills, or session management. They need the AI to stop forgetting things between sessions, and they need the system to get better with every use.
