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

- **Interview prompt** (Project 1): "Interview me about my goals" — Claude pulls context from you instead of guessing
- **Skill identification** (Project 2): "Based on our recent back-and-forth, what skill(s), script(s), and/or document(s) can be created or updated to improve the process, reduce errors, and improve repeatability. Bias towards scripts whenever possible"
- **Improve system** (Project 4): After every output that needs correction, ask "is this a one-time fix or should this be in the skill forever?" If forever, update the skill.

## Key Takeaways

- **Interview before building.** The "interview me" pattern forces Claude to pull context from the user instead of making assumptions. Applicable to any new project setup.
- **Internal OS = knowledge + skills + projects + CLAUDE.md.** This is the structure Knap is based on. CLAUDE.md tells Claude how to use the system so you don't re-explain every session.
- **Bias towards scripts.** "If you can use code instead of AI, you should." Scripts are deterministic, cheaper, and repeatable. This is Knap's core principle.
- **Skills improve every session.** The "one-time fix or forever?" question is the self-improvement loop. Every correction is an opportunity to make the system better.
- **Build for yourself first.** The niche command center works because it solves a problem you have today, not a hypothetical one. Zero audience pressure means you can build fast.
