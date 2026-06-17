---
source: "[2026-06-17-stop-watching-tutorials-build-these-4-claude-projects-to-10x.transcript.md](../raw/transcripts/2026-06-17-stop-watching-tutorials-build-these-4-claude-projects-to-10x.transcript.md)"
date_ingested: "2026-06-17"
channel: "Austin Marchese"
format: "YouTube video transcript"
---

# Stop Watching Tutorials - Build These 4 Claude Projects to 10x Output

## Summary

Austin Marchese presents four Claude Code projects that build on each other: a board of advisors (clone experts from public content), a niche command center (build a tool for something you already do), an AI-optimized public profile (personal website), and an internal operating system (knowledge/skills/projects structure with improvement loops). The interview-first approach — letting Claude ask you questions before building — is the recurring pattern. The internal OS structure (knowledge/, skills/, projects/ + CLAUDE.md as the brain) directly influenced Knap's architecture.

## Details

### The Four Projects

1. **Board of Advisors** — Clone professional experts by ingesting their public content (YouTube works best). Create a skill to consult the board. Interview prompt lets Claude understand your goals first.
2. **Niche Command Center** — Build a tool for something you already do (finance tracker, content planner). Plan before building. Use it immediately, iterate as needed.
3. **AI-Optimized Public Profile** — Personal website with "Ask AI about me" links that preload prompts about you into AI chatbots.
4. **Internal Operating System** — Three folders (knowledge, skills, projects) + CLAUDE.md as the brain. The `/improve system` skill captures feedback so the system improves over time.

### Key Prompts

Prompts shown on screen during the video (timestamps noted). Verbatim text below — use these as-is or adapt.

**P1 — Interview me (Project 1, ~0:11)**

> Interview me to build a personal career coach. Ask me 10 questions one at a time covering: my current role, what I'm building toward, my  strengths, my blockers, and the people I trust for advice. After the back and forth, save it as md file in this directory and reference it to when it's needed.

The interview prompt tells Claude to pull context from you instead of guessing. Covers goals for 1, 5, 10 years.

**P2 — Board of directors (Project 1, ~0:35)**

> Based on what you learned about me, recommend 2 experts who'd make a phenomenal advisory board for my specific situation. Bias toward YouTube creators. For each: why they fit + their best 5 pieces of content I should ingest.

Claude suggests board members based on your goals. Biasing toward YouTube creators ensures their full body of work is accessible as training data.

**P3 — Ingest board member data (Project 1, ~1:11)**

> Ingest the content I'm pasting below (transcripts, articles, posts, notes, whatever) as training data for [PERSON NAME] — save each piece as a raw file under knowledge/raw/[person-slug]/, then generate a synthesis wiki at knowledge/wiki/[person-slug].md covering their core ideas, vocabulary, stances, and recurring stories.

Pipe-delimited ingestion: paste content, Claude saves raw files and generates synthesis wiki.

**P4 — Ask the board skill (Project 1, ~1:35)**

> In this project I have created a Board of Advisors. When I ask a question, give me each advisor's take in their own voice, flag where they agree and disagree, then synthesize what I should actually do. Create a custom skill called /ask-the-board which will automatically get their opinion on a decision I'm making.

Creates a skill that consults all board members, finds consensus and disagreement, and synthesizes actionable advice.

**P5 — What should I do with AI? (Project 1, ~1:49)**

> Based on everything you know about me, what should I do to capitalize on AI?

Example question to test the board. The board's value is in personalized advice grounded in your ingested context.

**P6–P8 — Unverified (not yet reviewed)**
<!-- These prompts are from earlier notes but have not been verified against the video past ~1:49.
  - Improve system (Project 4, ~11:35): "Is this a one-time fix or should this be in the skill forever?"
  - Review chat for improvements (Project 4, ~10:09): "Review the back and forth I just had after using this skill. Can we enhance the skill so this is handled automatically or we don't make the same mistake again?"
  - Niche command center planning prompt (Project 2)
  - Internal OS setup prompt (Project 4)
-->

## Key Takeaways

- **Interview before building.** The "interview me" pattern forces Claude to pull context from the user instead of making assumptions. Applicable to any new project setup.
- **Internal OS = knowledge + skills + projects + CLAUDE.md.** This is the structure Knap is based on. CLAUDE.md tells Claude how to use the system so you don't re-explain every session.
- **Bias towards scripts.** "If you can use code instead of AI, you should." Scripts are deterministic, cheaper, and repeatable. This is Knap's core principle.
- **Skills improve every session.** The "one-time fix or forever?" question is the self-improvement loop. Every correction is an opportunity to make the system better.
- **Build for yourself first.** The niche command center works because it solves a problem you have today, not a hypothetical one. Zero audience pressure means you can build fast.
