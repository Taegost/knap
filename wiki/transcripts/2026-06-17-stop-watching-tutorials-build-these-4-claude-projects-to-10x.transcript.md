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
<!-- TODO: paste verbatim prompt from video screenshot -->
The interview prompt tells Claude to pull context from you instead of guessing. Covers goals for 1, 5, 10 years.

**P2 — Skill identification (Project 2, ~3:20)**
> "Based on our recent back-and-forth, what skill(s), script(s), and/or document(s) can be created or updated to improve the process, reduce errors, and improve repeatability. Bias towards scripts whenever possible"

**P3 — Improve system (Project 4, ~11:35)**
After every output that needs correction, ask:
> "Is this a one-time fix or should this be in the skill forever?"
If forever, update the skill.

**P4 — Review chat for improvements (Project 4, ~10:09)**
> "Review the back and forth I just had after using this skill. Can we enhance the skill so this is handled automatically or we don't make the same mistake again?"

**P5–P8 — Other on-screen prompts**
<!-- TODO: paste verbatim prompts from video screenshots:
  - Board member suggestion prompt (Step 2, ~0:37)
  - Ingest YouTube data prompt (Step 3, ~1:12)
  - Ask the board skill creation prompt (Step 4, ~1:24)
  - Niche command center planning prompt (Step 2, ~4:41)
-->

## Key Takeaways

- **Interview before building.** The "interview me" pattern forces Claude to pull context from the user instead of making assumptions. Applicable to any new project setup.
- **Internal OS = knowledge + skills + projects + CLAUDE.md.** This is the structure Knap is based on. CLAUDE.md tells Claude how to use the system so you don't re-explain every session.
- **Bias towards scripts.** "If you can use code instead of AI, you should." Scripts are deterministic, cheaper, and repeatable. This is Knap's core principle.
- **Skills improve every session.** The "one-time fix or forever?" question is the self-improvement loop. Every correction is an opportunity to make the system better.
- **Build for yourself first.** The niche command center works because it solves a problem you have today, not a hypothetical one. Zero audience pressure means you can build fast.
