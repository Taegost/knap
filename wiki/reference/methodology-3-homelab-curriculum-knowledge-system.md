---
title: "Methodology 3: Homelab Curriculum Knowledge System"
category: reference
---

# Methodology 3: Homelab Curriculum Knowledge System

Source: `~/_ws/homelab-k8s-curriculum`

---

## Brief Summary

A content production repository for a Kubernetes homelab blog. The knowledge system is built around three tiers: raw source documents (8 transcripts + resume), a synthesized voice reference document (VOICE.md), and a corrections index (corrections.yaml) plus stat deduplication tracker (used_stats.json). The system's primary purpose is not general knowledge management but ensuring content quality — consistent voice, factually correct claims, and no stat overuse.

The LLM reads VOICE.md before writing any article, scans corrections.yaml for known-wrong terms, and references curriculum_modules.csv for structural validation. A 30+ script pipeline enforces quality through a pre-commit hook with 12 blocking checks. A generated DASHBOARD.md tracks all module statuses. Knowledge is domain-specific: voice synthesis, corrections tracking, and stat deduplication are all tailored to the Kubernetes homelab curriculum.

---

## My Thoughts

This repo takes a fundamentally different approach from the Karpathy pattern. Instead of building a browsable wiki of interconnected pages, it builds a quality assurance system around content production. The "memory" isn't for retrieval — it's for enforcement. VOICE.md ensures the LLM writes like the human author. corrections.yaml ensures the LLM doesn't repeat known errors. used_stats.json ensures the LLM doesn't overuse the same statistics.

The voice synthesis pattern is the most novel contribution. Collecting real writing samples, synthesizing a voice reference, and then explicitly calling out what makes the writing detectable as human (vs AI-generated) is a sophisticated approach to the "AI slop" problem. The system doesn't just say "write in a human voice" — it specifies the exact patterns: comic fake-shock, parenthetical commentary, pop culture references, self-deprecating honesty, rhetorical questions, triple-tap emphasis, mantra callbacks, and concrete personal stories.

The corrections index is elegant in its simplicity. A YAML file mapping wrong terms to correct versions, checked by a script before every commit. This is a pattern any wiki could adopt — wrong prices, incorrect business hours, outdated phone numbers could all be tracked this way.

The stat deduplication tracker is clever but has implementation issues (SVG content contamination). The concept is sound: track every external statistic cited across all posts, prevent overuse, and auto-populate the tracker as content is written.

The main limitation is that this system is tightly coupled to one domain (Kubernetes homelab content) and one author (Mike Wheway). Adapting it to a different domain requires rebuilding all knowledge artifacts from scratch. The system also lacks the browsable, interlinked page structure that makes the Karpathy pattern useful for exploration.

---

## Detailed Implementation

### Architecture

```
knowledge/
  raw/mike-wheway/          8 source documents (blog posts, community pages, resume)
  wiki/mike-wheway/VOICE.md 325-line synthesized voice reference
  corrections.yaml          Known-wrong terms index (7 entries)
  used_stats.json           Stat deduplication tracker (~40 entries)

CLAUDE.md                   27K master instruction file
STRATEGY.md                 27K curriculum strategy
STANDARDS.md                8K SVG/K8s/visual standards
DASHBOARD.md                Generated status tracker (never manually edited)
curriculum_modules.csv      Master module registry (source of truth for IDs)

scripts/                    30+ validation and generation scripts
.claude/skills/             LLM workflows (blog brief, blog write, etc.)
```

### Voice Synthesis (VOICE.md)

The core knowledge artifact. 325 lines organized into 9 sections:

1. **Core Philosophy & Mantras** — "Just Do Something", "Failure Is Always an Option", "Trust But Verify", "Production-Grade Mindset"
2. **Vocabulary & Signature Phrases** — HIGH-FREQUENCY words, openings, closings, recurring idioms
3. **Stances & Positions** — technology opinions, content creation philosophy
4. **Recurring Stories & Anecdotes** — Docker-to-K8s migration, $1,000 homelab, SealedSecrets reveal
5. **Tone Mechanics** — conversational direct address, emphasis patterns, humor types, sentence rhythm
6. **Structural Patterns** — opening strategies, body organization, closing strategies
7. **Writing Quirks & Signatures** — pop culture touchpoints, branding, the 83 Rule
8. **Writing Guidelines** — DO/DON'T lists, AI-detectable patterns to preserve
9. **Source Index** — maps raw files to their synthesis contribution

Key design decision: the voice reference explicitly calls out what makes the writing detectable as *human* and preserves those patterns. This is a direct counter to the tendency of LLMs to produce generic, hedging, emoji-laden prose.

### Corrections Index (corrections.yaml)

```yaml
- wrong: "kube-vip"
  correct: "kube-vip (Cloudflare)"
  context: "kube-vip has two modes — Cloudflare and Equinix. Specify which."
  source: "docs/curriculum/..."
```

Checked by `scripts/check_corrections.py` which scans all briefs and content files for known-wrong terms. Append-only — corrections are never deleted.

### Stat Deduplication Tracker (used_stats.json)

```json
{
  "id": "stat-001",
  "canonical": "Kubernetes runs on 84% of production containers",
  "normalized": "kubernetes runs on 84% of production containers",
  "numeric_core": "84%",
  "source_label": "CNCF Survey 2025",
  "source_url": "https://...",
  "first_seen": "content/p1m1-why-kubernetes.md",
  "used_in": ["content/p1m1-why-kubernetes.md"]
}
```

Auto-populated by `check_cross_post_stats.py --update- tracker`. Prevents overuse of the same statistics across posts.

### Pre-Commit Hook

12 blocking checks + 3 soft warnings on every commit touching content or briefs:
- Module number references must match curriculum_modules.csv
- Cross-post URLs must use correct format
- Corrections index must be clean
- Voice patterns must not contain banned AI phrases
- Em dash density must be 5-8 per 1K words
- Passive voice must be 10-15%
- Heading hierarchy must be valid
- Dashboard must be up to date
- Frozen article status must be preserved
- Status fields must be preserved through rewrites

### Generated Dashboard (DASHBOARD.md)

Regenerated from curriculum_modules.csv + content frontmatter + filesystem state. Never manually edited. Shows module status, file links, and completion percentages.

---

## What Works

- **Voice synthesis.** The most sophisticated approach to the "write like a human" problem. Collecting real samples, synthesizing a reference, and explicitly preserving human-detectable patterns.
- **Corrections index.** Simple, append-only, script-enforced. The pattern of "wrong → correct → context → source" is universally applicable.
- **Stat deduplication.** Prevents the LLM from lazily reusing the same statistics across posts.
- **Pre-commit quality gates.** 12 blocking checks catch errors before they enter the repository. The quality enforcement is automated, not LLM-dependent.
- **Single source of truth.** curriculum_modules.csv is the master registry. Every validation script imports it. No duplication.
- **Generated dashboard.** A single file summarizes all module statuses without manual maintenance.

## What Doesn't Work

- **Domain coupling.** Voice synthesis, corrections, and stat tracking are all specific to one author and one domain. Adapting to a different project requires rebuilding everything.
- **No browsable wiki.** The knowledge is structured for enforcement, not exploration. You can't navigate from a Kubernetes concept to related articles the way you can navigate wiki pages with wikilinks.
- **Corrections index is unbounded.** No mechanism to expire or merge corrections. Over time, the section could grow large enough to impact context window usage.
- **Stat tracker contamination.** SVG content leaked into stat entries from inline attributes. Fixed by requiring standalone SVG files, but it reveals the fragility of text-based tracking.
- **Dashboard fragility.** `status_utils.py` extracts status from DASHBOARD.md by regex-matching table rows. If the dashboard format changes, frozen detection breaks.
- **No rollback.** If a correction is added in error or a stat entry is wrong, the only recovery is manual git revert.

## What Could Be Improved

- **Externalize corrections to a config.** Move the corrections YAML schema to a shared format that other repos could adopt. The "wrong → correct → context → source" pattern is universally useful.
- **Add correction expiration.** Add a `verified_date` field and a staleness threshold. Corrections older than N days should be flagged for re-verification.
- **Separate voice from domain.** The voice synthesis pattern could be extracted into a reusable template. Collect writing samples → synthesize reference → call out human-detectable patterns.
- **Add a wiki layer.** The enforcement system is strong but the knowledge isn't browsable. Adding a wiki layer on top (interlinked pages for concepts, entities, strategies) would make the knowledge useful for exploration, not just content production.
- **SQLite index for stats.** The JSON file is fine at 40 entries but won't scale. A SQLite database with full-text search would handle thousands of entries.

## Other Thoughts

This repo proves that "memory" doesn't have to mean "browsable wiki." Sometimes memory is about quality enforcement — making sure the LLM doesn't repeat errors, doesn't overuse the same data, and doesn't drift from the author's voice. The corrections index and stat tracker are forms of procedural memory: "don't do X" and "you already used Y."

The voice synthesis pattern is the most transferable idea. Any project where the LLM needs to write in a specific voice (marketing copy, technical docs, personal blog) could adopt this approach. The key insight is that you don't just tell the LLM to "write like a human" — you give it specific, concrete patterns to preserve and specific, concrete patterns to avoid.

The pre-commit hook is the right place to enforce quality. The LLM produces content; the scripts validate it. This separation of concerns (LLM creates, scripts verify) is more robust than trusting the LLM to self-validate.
