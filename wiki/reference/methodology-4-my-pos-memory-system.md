---
title: "Methodology 4: my_pos — Personal Operating System Memory"
category: reference
---

# Methodology 4: my_pos — Personal Operating System Memory

Source: `~/_ws/my_pos`

---

## Brief Summary

A Personal Operating System (POS) — a git-backed knowledge management system that gives an LLM persistent memory across sessions. Combines a career coaching profile (user identity, ADHD wiring, goals), a virtual advisory board (5 synthesized advisors from YouTube/podcast transcripts), a consultant pool (domain-specific SMEs), a conversation archive with pattern synthesis, and a real-time state file (STATE.md). Every interaction, decision, correction, and piece of external knowledge is captured in files on disk. The LLM reads these files at the start of every session to reconstruct context.

The system has three distinct layers: raw sources (immutable transcripts), synthesized wiki pages (advisor profiles, conversation patterns), and operational files (STATE.md, corrections board, skill definitions). Two consultation skills (`/ask-the-board` and `/ask-consultants`) define how the LLM retrieves and applies stored knowledge. A drift checker (`drift_check.py`) validates documentation health with 8 checks on a 100-point scale.

---

## My Thoughts

This is the most ambitious memory system of the four. It's not just storing knowledge — it's simulating a team of advisors with distinct voices and expertise. The "virtual advisory board" concept (Dan Koe for motivation, Dr. K for psychology, Techworld with Nana for technical strategy, Mark Cuban for business, Chris Koerner for execution) is creative and genuinely useful. Each advisor has a synthesized wiki profile, a defined voice, and specific areas of expertise. When the user asks for advice, the system consults the appropriate advisors and synthesizes their perspectives.

The conversation archive is the most novel feature. By recording every consultation and synthesizing patterns across conversations, the system builds a memory of its own behavior — what advice it gave, what corrections were made, what commitments were stated. The "Corrections Board Must Remember" section is particularly valuable: when the board makes a factual error, that correction is recorded so it's never repeated. This is a form of institutional memory.

The STATE.md file is a clever solution to the "what's happening right now" problem. Instead of relying on the LLM's training data or a static profile, the system maintains a live state file that tracks current projects, income, decisions pending, and key personal context. The staleness detection (>3 days triggers a flag) prevents the board from operating on outdated information.

The main limitation is complexity. Two-tier system (board vs consultants), two parallel skill files, two parallel index files, two parallel directory trees. The system has accumulated enough moving parts that it's hard to reason about what's in context at any given time. The 12-file load order for `/ask-the-board` is a lot of context to consume before the first word of advice is generated.

---

## Detailed Implementation

### Architecture

```
career-coach-profile.md         Core file: user identity, ADHD wiring, goals, board members
consultants-profile.md          Consultant pool roster with expertise tags
STATE.md                        Live state: current projects, income, decisions pending

knowledge/
  INDEX.md                      Master index: all board members, source counts, wiki dates
  raw/
    dan-koe/                    7 transcript files
    dr-k-HealthyGamerGG/        4 transcripts
    techworld-with-nana/        4 transcripts
    mark-cuban/                 10 transcripts
    chris-koerner/              8 transcripts
    ali-abdaal/                 4 transcripts (archived)
    conversations/              Board consultation raw files
  wiki/
    dan-koe.md                  Synthesized from 7 raw sources
    dr-k-HealthyGamerGG.md
    techworld-with-nana.md
    mark-cuban.md
    chris-koerner.md
    ali-abdaal.md
    washer-dryer-rental-business.md   Cross-advisor domain synthesis
    mike-wheway-resume.md             Career history
    conversations/
      INDEX.md                  Conversation archive index
      conversations-synthesis.md  Pattern synthesis across all conversations
  consultants/
    INDEX.md                    Consultant pool index
    raw/kyler-liston/           4 raw transcripts
    wiki/kyler-liston.md        Synthesized consultant wiki

scripts/
  fetch_youtube_transcript.py   YouTube transcript fetcher (no API key)
  fetch_blog_status.py          Live WordPress blog status
  extract_epub.py               Extract text from epubs
  drift_check.py                Documentation health checker (8 checks, 100-point scale)

.claude/skills/
  ask-the-board/SKILL.md        Full board consultation skill
  ask-consultants/SKILL.md      Selective expert consultation skill
  advisor-ingest/SKILL.md       Content ingestion pipeline
```

### The Advisory Board

Five synthesized advisors, each built from YouTube/podcast transcripts:

| Advisor | Domain | Source Material |
|---------|--------|-----------------|
| Dan Koe | Motivation, personal brand, creator economy | 7 transcripts |
| Dr. K (HealthyGamerGG) | Psychology, ADHD, mental health | 4 transcripts |
| Techworld with Nana | Technical strategy, DevOps, career | 4 transcripts |
| Mark Cuban | Business, entrepreneurship, mindset | 10 transcripts |
| Chris Koerner | Execution, side hustles, real-world tactics | 8 transcripts |

Each advisor has a synthesized wiki with: Core Identity, Vocabulary, Products, Gaps, Relevance.

### The Consultation Skill (`/ask-the-board`)

Before answering, loads 12 files in order:
1. STATE.md (current context)
2. conversations-synthesis.md (past patterns + corrections)
3. conversations/INDEX.md (quick lookup)
4. career-coach-profile.md (user identity)
5. 5 individual advisor wiki files
6. washer-dryer-rental-business.md (if relevant)
7. mike-wheway-resume.md (career history)
8. Blog status (fetched live via Python script)

The skill defines precise voice profiles for each advisor, enforces faithful representation grounded in actual wiki content, and mandates immediate persistence of the consultation to disk before anything else.

### Conversation Archive

After every board consultation:
1. Raw file written to `knowledge/raw/conversations/{YYYY-MM-DD}-{slug}.md`
2. One line appended to `knowledge/wiki/conversations/INDEX.md`
3. Periodically, `conversations-synthesis.md` is updated with:
   - Recurring topics
   - Decisions made
   - Commitments stated
   - **Corrections the board must remember** (most critical section)
   - Follow-through tracking

Example corrections:
- "Job date is June 15, 2026. Not 'late June.' Not 'two weeks.'"
- "Mike uses AI orchestration. Claude does the work. Do not evaluate as manual effort."
- "Mike was in survival mode for 6 years, not ADHD novelty-seeking."

### STATE.md — The "Now" Layer

Tracks:
- This week's activity (blog posts, model switches, audits)
- Active projects table (status + next step)
- Current income sources
- Key personal context the board must know
- Financial priorities
- Decisions pending

Staleness detection: if STATE.md is >3 days old, the board flags it and asks for an update before proceeding.

### Drift Checker (`drift_check.py`)

8 health checks on a 100-point scale:
1. Stale files (configurable thresholds)
2. Broken markdown links
3. File path references that don't resolve
4. INDEX.md entries vs actual files on disk
5. Conversation INDEX vs raw files
6. STATE.md consistency
7. Duplicate content within files
8. Stale AI model name references

---

## What Works

- **Virtual advisory board.** Distinct advisor voices with synthesized expertise. The board gives more nuanced advice than a single LLM persona.
- **Corrections memory.** The "Corrections Board Must Remember" section is the most valuable memory feature. When the board makes an error, that correction is recorded and never repeated.
- **STATE.md.** A live state file solves the "what's happening right now" problem. The staleness detection prevents operating on outdated information.
- **Conversation synthesis.** Recording consultations and synthesizing patterns across conversations builds institutional memory. The system remembers what it advised, what was corrected, and what commitments were made.
- **Write-before-anything-else.** The consultation skill mandates persisting the raw conversation to disk within 30 seconds. Session crashes lose nothing.
- **YouTube transcript fetching.** No API key needed. The `youtube-transcript-api` library pulls transcripts directly. Lowers the barrier to ingesting new source material.
- **Drift checker.** 8 health checks with a scored report. The 100-point scale makes documentation health quantifiable.

## What Doesn't Work

- **Complexity.** Two-tier system (board vs consultants), two parallel skill files, two parallel index files. The 12-file load order for `/ask-the-board` is a lot of context.
- **No project-level CLAUDE.md.** Relies on `~/.claude/CLAUDE.md` (global) plus skill files. The LLM infers conventions from existing files rather than following explicit schema rules.
- **Raw files lack structured metadata.** `save_raw.py` generates markdown headers, not YAML frontmatter. No machine-readable `date_farmed`, `source_url`, `category` fields.
- **Index generation is filesystem-dependent.** `index.py` counts `.md` files in raw directories but doesn't validate that wikis reference their raw sources correctly.
- **No validation pipeline.** Only `drift_check.py` for health checks. No schema validation, no frontmatter enforcement, no automated fixup.
- **Corrections are unbounded.** No mechanism to expire or merge corrections. The section could grow large enough to impact context window usage.
- **No deduplication across raw sources.** Multiple transcripts from the same advisor may cover overlapping content. No tooling detects duplicate content.
- **`name_map` in index.py is hardcoded.** New advisors won't get proper display names in the generated index unless the code is updated.

## What Could Be Improved

- **Add a project-level CLAUDE.md.** Define schema conventions, required fields, and workflow rules explicitly rather than relying on inference.
- **Use YAML frontmatter for raw files.** Replace markdown headers with YAML frontmatter. Add `date_farmed`, `source_url`, `category`, `advisor` fields. Enable machine-readable queries.
- **Add a validation pipeline.** Schema validation for raw files, frontmatter enforcement, automated fixup. Catch errors at ingest time.
- **Extract the corrections pattern.** The "wrong → correct → context" format is universally useful. Make it a reusable template.
- **Add correction expiration.** Add a `verified_date` field and a staleness threshold. Corrections older than N days should be flagged for re-verification.
- **Reduce load order.** The 12-file load order for `/ask-the-board` is expensive. Consider tiered loading: always-load (STATE.md, career-coach-profile.md) → topic-specific (relevant advisor wikis) → on-demand (conversation synthesis, consultants).
- **Add a wiki layer for advisors.** Currently advisor wikis are synthesis documents. Adding interlinked pages (concepts, frameworks, quotes) would make the knowledge more granular and reusable.

## Other Thoughts

This repo proves that "memory" can be more than stored facts. The conversation archive is a form of institutional memory — it remembers not just what was said, but what was wrong, what was corrected, and what commitments were made. The advisory board is a form of persona memory — it stores not just knowledge, but perspectives and voices.

The "corrections" pattern is the most transferable idea. Any system where an LLM interacts with a user over time would benefit from a corrections file that captures factual errors the LLM made. The key insight is that corrections are higher-value data than the original advice — they represent ground truth that the user provided.

The STATE.md pattern is also valuable. Any long-running project would benefit from a live state file that tracks current status, pending decisions, and key context. The staleness detection ensures the LLM doesn't operate on outdated information.

The main lesson is that memory systems need to be opinionated. This repo doesn't try to store everything — it stores what matters for the specific use case (career coaching, side hustles, content creation). The advisor voices, the corrections board, and the state file are all tailored to the user's needs. A generic memory system would be less useful.
