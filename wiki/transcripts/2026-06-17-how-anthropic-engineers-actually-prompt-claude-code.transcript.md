---
source: "[2026-06-17-how-anthropic-engineers-actually-prompt-claude-code.transcript.md](../raw/transcripts/2026-06-17-how-anthropic-engineers-actually-prompt-claude-code.transcript.md)"
date_ingested: "2026-06-17"
channel: "Austin Marchese"
format: "YouTube video transcript"
---

# How Anthropic Engineers ACTUALLY Prompt Claude Code

## Summary

Austin Marchese distills four rules from how Anthropic engineers actually use Claude Code: prompt skills not Claude, skills have three layers (description + instructions + tools), build composable skills not monolithic ones, and skills improve every session. The key insight is that most people obsess over prompts but neglect the tools layer — scripts, APIs, and reference files that make skills deterministic and repeatable. The "is this a one-time fix or forever?" question after every skill run is the self-improvement mechanism.

## Details

### The Four Rules

1. **Prompt skills, not Claude.** Stop writing new prompts for everything. Create reusable skills for repetitive tasks. Claude auto-invokes skills based on their description — no need to manually call them.
2. **Skills are more than prompts.** Three layers:
   - Description (when to use it — Claude checks this automatically)
   - Instructions (step-by-step playbook)
   - Tools (scripts, APIs, reference files — where the leverage lives)
3. **Composable, not custom.** Small, focused, reusable skills that chain together. One monolithic skill becomes unmanageable. Benefits: issues are easy to spot, improvements compound, reuse instead of rebuilding.
4. **Skills improve every session.** After every skill run, ask: "Is this a one-time fix or should this be in the skill forever?" If forever, update the skill. Chat history is the reference for improvement.

### Key Prompts

Prompts shown on screen during the video (timestamps noted). Verbatim text below — use these as-is or adapt.

**P1 — Skill identification (~1:51)**

> Based on my recent sessions, what tasks am I doing repeatedly that should be skills instead of one-off prompts?
> For each one, suggest a skill name and what context it would need.

Helps identify which skills are worth creating based on your recent sessions.

**P2 — Build skills with verification (~4:24)**

> Find a task where I'm doing manual checking, lookup, or verification after AI gives me an output.
> Build a skill that does both: generates the answer AND verifies it.
> Show me the SKILL.md with description, when-to-trigger examples, and the verification step.
> Identify any tools that are needed to help this skill provide a better output.

Forces the skill to include a verification layer instead of relying on the user to manually check outputs.

**P3 — Audit skill setup (~8:18)**

> Audit my Claude Skills for:
> 1. Visibility:
>    - Skills with high risk side effects (deploy, commit, send messages): add disable-model-invocation: true so Claude can't auto-fire.
>    - Skills that are pure background knowledge users would never /run themselves: add user-invocable: false to hide from /menu.
> 
> 2. Deterministic vs non-deterministic:
>    - Find any step inside a skill where AI is interpreting something that's actually a fixed, repeatable operation.
>    - Suggest replacing those steps with a script saved inside the skill folder. Code = same result every time, no tokencost.
>    - Keep AI for the steps that need judgment.
> 
> 3. Composability:
>    - Flag any skill that duplicates logic another skill already has. Suggest extracting shared logic into a callable script or a smaller > composable skill.
> 
> Show me the rewrites with a changelog of what changed and why.

Audits your setup to make sure you're properly applying the three-layer pattern (description + instructions + tools).

**P4 — Review chat for improvements (~10:09)**
> "Review the back and forth I just had after using this skill. Can we enhance the skill so this is handled automatically or we don't make the same mistake again?"

**P5 — The self-improvement question**
After every skill run, ask:
> "Is this a one-time fix or should this be in the skill forever?"
If forever, update the skill. Add the rule, the example, the edge case.

### Key Patterns

- **Save scripts inside skills.** Claude kept rewriting the same Python script every session. Saving it as a tool inside the skill made it deterministic, cheaper, and repeatable. "Trading AI tokens for code compute."
- **Control who invokes what.** Two flags: `user_invocable: false` (hides from slash menu, agent-only) and `disable_model_invocation: true` (user-only, for high-risk actions).
- **Layer 3 is where leverage lives.** Most people stop at instructions (layer 2). The tools layer is what makes skills actually powerful.

## Key Takeaways

- **"If you can use code instead of AI, you should."** Scripts are deterministic, cheaper, and repeatable. This validates Knap's script-first principle.
- **Skills have three layers, not one.** Description + instructions + tools. The tools layer (scripts, APIs) is where most of the leverage lives but most people skip it.
- **Composable over monolithic.** Small focused skills that chain together. One big skill becomes unmanageable. This is why Knap has separate /ingest and /synthesize skills.
- **The self-improvement question.** "Is this a one-time fix or forever?" After every skill run, if the correction is permanent, update the skill. This is the compounding loop.
- **Chat history = improvement reference.** "Review the back-and-forth I just had after using this skill. Can we enhance the skill so this is handled automatically?"
