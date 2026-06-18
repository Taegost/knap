---
name: knap-synthesize
description: "Research a question from multiple sources, synthesize findings, and record as a wiki page."
user_invocable: true
---

# Synthesize Skill

Researches a question from multiple sources, synthesizes findings, and records the result as a wiki page with raw source + wiki page + index + log.

## Usage

```
/knap-synthesize <question or topic>
/knap-synthesize what are the best practices for X
/knap-synthesize how does Y compare to Z
```

## Process

### 1. Research

Search the question from multiple angles. Minimum 3 independent sources.

**Check existing knowledge first:**
- Read `wiki/index.md` for existing pages that may be relevant
- Read those pages before researching externally

**Source quality hierarchy:**
1. Official/primary data
2. Industry reference guides
3. Community sources (Reddit, forums)

### 2. Synthesize answer

Present findings to the user. Include:
- Direct answer with numbers/data
- Breakdown by category/type
- Key caveats
- Cross-references to existing wiki pages using markdown links

### 3. Record (auto-trigger)

After presenting findings, immediately:
1. Create raw file at `raw/{category}/{slug}.md` with full research data
2. Run ingest pipeline:
   ```bash
   python .knap/scripts/validate.py raw/{category}/{slug}.md
   python .knap/scripts/ingest.py raw/{category}/{slug}.md
   ```
3. Write Summary and Analysis sections on the wiki page
4. Run lint:
   ```bash
   python .knap/scripts/lint.py
   ```

Do NOT ask whether to record. Synthesized answers MUST be recorded.

### 4. Update router state

If the research changed what we know about the project, update `.knap/ROUTER.md`'s Current Project State section.

## When NOT to synthesize

- Simple factual questions that don't need permanent recording
- Content already covered in existing wiki pages — update the existing page instead
- Speculation without data — flag as needing verification
