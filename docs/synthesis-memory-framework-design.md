# Memory Framework Design — Synthesis

A design document for brainstorming. Synthesized from five methodologies: Karpathy LLM Wiki, AppalachianHaul wiki, homelab-curriculum knowledge system, my_pos Personal Operating System, and mex scaffold pattern.

---

## The Problem

Every new project requires designing a memory system from scratch. Existing solutions are optimized for specific tasks and don't generalize. The result is wasted time, inconsistent patterns, and systems that work for one project but can't be reused. We need a **generic base layer** that any repo can extend with domain-specific customizations.

---

## Design Principles

These are non-negotiable. Every decision below is evaluated against them.

1. **General-purpose base.** The framework must work for any knowledge domain — a business wiki, a content production system, a homelab, a personal advisory board. Domain specifics are extensions, not core.

2. **Extensible.** Each repo customizes the base with its own categories, fields, workflows, and tooling. The base doesn't dictate domain logic.

3. **Script-first.** Automate everything that can be automated. Scripts are deterministic, repeatable, and don't consume tokens. The LLM handles judgment; scripts handle mechanics.

4. **Token-efficient.** Load only what's needed for the current task. Context windows are finite and expensive.

5. **Editor-agnostic.** Must work in Obsidian, VS Code, any markdown editor. No tool-specific syntax dependencies.

6. **Reliable across LLMs.** The system should work regardless of which LLM is driving it. Conventions and scripts enforce consistency; the LLM is a participant, not the sole operator.

---

## Architecture

Three layers, plus a routing mechanism and a scripted pipeline.

```
raw/              Immutable source documents
wiki/             LLM-maintained markdown pages
schema/           Framework conventions + domain definitions
router.md         Task-type → context-file routing table
scripts/          Automated pipeline (validate, fixup, ingest, lint)
```

### Layer 1: raw/

Immutable source documents. The LLM reads these but never modifies them. Organized by category subdirectories that the schema defines.

```
raw/
  {category}/
    {entity-slug}.md
```

Each raw file has YAML frontmatter with structured metadata. The schema defines required and category-specific fields. Missing values use `"n/a"` (never omit). Empty lists mean "none found."

```yaml
---
title: "Entity Name"
source_url: "https://..."
date_farmed: YYYY-MM-DD
category: "{category}"
# ... category-specific fields per schema ...
---
Body content — narrative notes, context, tables, caveats.
```

### Layer 2: wiki/

LLM-maintained markdown pages. Auto-generated stubs from raw frontmatter, with LLM-written judgment sections.

```
wiki/
  index.md          Content catalog (generated)
  log.md            Append-only chronological record
  {category}/
    {entity-slug}.md
```

Each wiki page has YAML frontmatter (generated from raw) plus rendered content. Mechanical data (hours, pricing, materials, services) is auto-generated from frontmatter by scripts. Only judgment sections (Summary, Analysis) require LLM writing.

```yaml
---
source: "raw/{category}/{entity-slug}.md"
date_ingested: YYYY-MM-DD
# ... copied from raw frontmatter ...
---
```

Cross-references use standard markdown links: `[Entity Name](../{category}/{slug}.md)`. This works in every markdown editor and is parseable by both humans and LLMs. Relative paths ensure links work regardless of where the repo is cloned.

### Layer 3: schema/

The framework conventions file (CLAUDE.md) plus domain-specific definitions.

```
schema/
  categories.yaml   Category definitions, required fields, analysis section labels
  CONVENTIONS.md    Framework-level conventions (link format, frontmatter rules, file naming)
```

`categories.yaml` is the single source of truth for the domain. Each repo defines its own categories:

```yaml
categories:
  landfill:
    required_fields: [accepted_materials, pricing, restrictions]
    analysis_label: "For Our Business"
    analysis_todo: "business implications, best use cases, caveats"
  competitor:
    required_fields: [services, pricing, areas_served]
    analysis_label: "Competitive Position"
    analysis_todo: "strengths, weaknesses, pricing position"
```

`CONVENTIONS.md` is the framework-level instruction file. It defines:
- Directory structure and naming conventions
- YAML frontmatter rules (required fields, n/a conventions, date formats)
- Cross-reference format (standard markdown links)
- Pipeline workflow (what scripts do in what order)
- LLM behavioral contract (what the LLM is responsible for)
- How to add new categories

### Layer 4: router.md

A routing table that maps task types to specific files. The LLM reads this first, then loads only what's relevant. Borrowed from mex's 3-tier routing concept.

```markdown
# Router

## Session Bootstrap
Read this file. Identify the task type. Load the files listed under that type.
Do NOT load files for other task types.

## Routing Table

| Task type | Load |
|---|---|
| Ingesting new source | `schema/categories.yaml`, `raw/{category}/`, `wiki/index.md` |
| Answering a query | `wiki/index.md`, then drill into relevant wiki pages |
| Writing analysis | `wiki/{category}/{slug}.md`, `raw/{category}/{slug}.md` |
| Health check | `schema/categories.yaml`, run `scripts/lint.py` |
| Adding a category | `schema/categories.yaml`, `schema/CONVENTIONS.md` |

## Current Project State
<!-- Updated by GROW loop or manually -->
Last updated: YYYY-MM-DD
Brief description of current state and recent changes.
```

The router is the context-efficiency mechanism. Instead of loading the full index and all potentially relevant pages, the LLM identifies the task type and loads only the files for that task. This extends the scale ceiling from ~100 sources to ~1000+.

### Layer 5: scripts/

The automated pipeline. This is the core of the "script-first" principle. Scripts are deterministic, repeatable, and don't consume tokens.

```
scripts/
  schema.py           Single source of truth (imports from schema/categories.yaml)
  validate.py         Frontmatter validation (required fields, dates, categories)
  fixup.py            Add missing fields with defaults (n/a, [])
  standardize.py      Normalize placeholder text to canonical n/a
  ingest.py           Generate wiki stubs from frontmatter, update index + log
  lint.py             Structural checks (orphans, stale pages, index accuracy, etc.)
  bootstrap.py        Initialize a new repo from the base template
  find-stubs.py       List wiki pages with TODO markers
```

#### Pipeline Flow

```bash
# Full pipeline for a category:
python3 scripts/validate.py raw/{category}/ && \
  python3 scripts/fixup.py raw/{category}/ && \
  python3 scripts/standardize.py raw/{category}/ && \
  python3 scripts/validate.py raw/{category}/ && \
  python3 scripts/ingest.py raw/{category}/*.md && \
  python3 scripts/lint.py
```

#### What Scripts Do vs. What the LLM Does

| Step | Who | Why |
|------|-----|-----|
| Validate frontmatter | Script | Deterministic — check fields, dates, categories |
| Fix missing fields | Script | Deterministic — fill defaults |
| Standardize placeholders | Script | Deterministic — normalize text |
| Generate wiki stubs | Script | Deterministic — render from frontmatter |
| Update index | Script | Deterministic — insert into sorted list |
| Append log | Script | Deterministic — format and append |
| Run lint checks | Script | Deterministic — 8+ structural checks |
| Write Summary | LLM | Judgment — synthesize 2-4 sentences |
| Write Analysis | LLM | Judgment — category-specific business analysis |
| Research new entities | LLM | Judgment — web search, source evaluation |
| Cross-reference relationships | LLM | Judgment — decide what's related and why |
| Synthesize research questions | LLM | Judgment — multi-source analysis |

#### Lint Checks

1. Orphan wiki pages (broken source links)
2. Un-ingested raw files (no wiki page)
3. Stale wiki pages (raw newer than wiki)
4. Index accuracy (entries match real files)
5. Missing index entries (wiki pages not in index)
6. Frontmatter validation (required fields, dates, categories)
7. Duplicate frontmatter/body fields
8. Stale raw files (not updated in N days)
9. Log dedup (no duplicate entries)
10. Broken markdown links (cross-references resolve)

---

## Decision Points

These are the architectural choices that need discussion. Each is evaluated against the two questions:

- **Q1**: Does this make it more valuable as a general memory/knowledge base system?
- **Q2**: Does this make it more extensible for future projects to build domain-specific pieces on top?

---

### Decision 1: Cross-Reference Format

**Options:**

| Option | Format | Editor support | LLM parseable | Concise |
|--------|--------|----------------|---------------|---------|
| A. Wikilinks | `[[page-name]]` | Obsidian, Logseq, some editors | Yes | Most concise |
| B. Standard markdown links | `[Page Name](../path/to/page.md)` | All editors | Yes | Verbose |
| C. Both (wikilinks in body, standard in frontmatter) | Mixed | Depends | Yes | Medium |

**Evaluation:**

| Option | Q1: General value | Q2: Extensible |
|--------|-------------------|----------------|
| A | No — breaks in non-Obsidian editors | No — tool dependency |
| B | Yes — universal portability | Yes — works everywhere |
| C | No — two formats to maintain, confusion about which to use | No — increases complexity |

**Decision: B — Standard markdown links.**

Rationale: The requirement is editor-agnostic. Standard markdown links work in every editor and are parseable by both humans and LLMs. The verbosity cost is acceptable for portability. Relative paths ensure links work regardless of clone location.

**Trade-off acknowledged:** Wikilinks are more concise and Obsidian-native. If the user decides Obsidian is the primary editor and cross-editor portability is less important, wikilinks could be reconsidered.

---

### Decision 2: Retrieval Strategy

**Options:**

| Option | How the LLM finds relevant knowledge |
|--------|--------------------------------------|
| A. Flat index | Read `index.md` (all pages listed), drill into relevant ones |
| B. Tiered router | Read `router.md` (task-type routing), load only relevant files |
| C. Search-based | Run a search script (grep, BM25, or embeddings) against the wiki |
| D. Hybrid (router + index + search fallback) | Router for common tasks, index for browsing, search for scale |

**Evaluation:**

| Option | Q1: General value | Q2: Extensible |
|--------|-------------------|----------------|
| A | Yes at small scale (<200 pages), no at large scale | No — index grows linearly, no routing |
| B | Yes — loads only what's needed, ~60% token reduction | Yes — task types are extensible |
| C | Yes — scales to any size | Yes — search is domain-agnostic |
| D | Yes — covers all scale points | Yes — each layer is independent |

**Decision: D — Hybrid (router + index + search fallback).**

Rationale: No single retrieval strategy works at all scales. The router handles common tasks efficiently. The index handles browsing and exploration. A search fallback (grep-based at minimum, BM25 or embeddings at scale) handles queries that don't match categories. Each layer is independent — add search when the index gets too large, not before.

**Implementation:**
- **<200 pages**: Router + index. The LLM reads the router, identifies the task, reads the index if needed, drills into pages.
- **200-1000 pages**: Router + index + grep search. Add a `search.py` script that greps frontmatter and body text.
- **1000+ pages**: Router + index + BM25/embeddings. Add a search index that the LLM queries programmatically.

---

### Decision 3: Knowledge Evolution Mechanism

**Options:**

| Option | How the wiki stays current |
|--------|---------------------------|
| A. Manual lint | LLM runs health checks when asked |
| B. Skill-driven pipeline | Repeatable workflows (farm, write-wiki, synthesize) |
| C. GROW loop | Mandatory post-task: Ground → Record → Orient → Write |
| D. Pre-commit hook | Blocking validation before any commit |
| E. All of the above | Layered enforcement |

**Evaluation:**

| Option | Q1: General value | Q2: Extensible |
|--------|-------------------|----------------|
| A | No — relies on LLM remembering | No — no enforcement |
| B | Yes — structured workflows | Yes — skills are customizable |
| C | Yes — mandatory maintenance | Yes — GROW is domain-agnostic |
| D | Yes — catches errors before commit | Yes — hooks are extensible |
| E | Yes — layered defense | Yes — each layer is independent |

**Decision: E — All of the above, layered.**

Rationale: No single mechanism is sufficient. Skills define structured workflows. The GROW loop ensures post-task maintenance. Pre-commit hooks catch errors before they enter the repo. Manual lint handles ad-hoc health checks. Each layer catches what the others miss.

**Layered enforcement:**
1. **Skills** define the structured workflows (what the LLM does for each operation)
2. **GROW loop** runs after every task (mandatory knowledge maintenance)
3. **Pre-commit hooks** run before every commit (blocking validation)
4. **Manual lint** runs on demand (ad-hoc health checks)

---

### Decision 4: How Much to Script vs. LLM

**Options:**

| Option | Boundary |
|--------|----------|
| A. Script everything possible | Scripts handle all mechanics; LLM only writes judgment sections |
| B. Script validation only | Scripts check; LLM creates and maintains |
| C. LLM-first with script assist | LLM drives; scripts help with specific tasks |
| D. Fully automated pipeline | Scripts handle everything including synthesis (no LLM judgment) |

**Evaluation:**

| Option | Q1: General value | Q2: Extensible |
|--------|-------------------|----------------|
| A | Yes — deterministic, repeatable, token-efficient | Yes — scripts are domain-agnostic at the base layer |
| B | Partially — validation is good but LLM creates inconsistency | Partially — scripts are narrow |
| C | No — LLM-driven means inconsistent across LLMs | No — LLM behavior varies |
| D | No — synthesis requires judgment that scripts can't do | No — automation can't replace analysis |

**Decision: A — Script everything possible.**

Rationale: The design principles say "script-first" and "reliable across LLMs." Scripts are deterministic, repeatable, and don't consume tokens. The LLM handles judgment (synthesis, analysis, research). Scripts handle everything else (validation, fixup, standardization, ingest, indexing, logging, linting).

**What gets scripted:**
- Frontmatter validation
- Missing field fixup
- Placeholder standardization
- Wiki stub generation
- Index updates
- Log updates
- Structural lint checks
- Search (when needed)
- Bootstrap (new repo initialization)
- Corrections checking (if adopted)

**What the LLM does:**
- Research new entities (web search, source evaluation)
- Write Summary sections (2-4 sentence synthesis)
- Write Analysis sections (category-specific business judgment)
- Synthesize research questions (multi-source analysis)
- Decide cross-references (what's related and why)
- Run GROW loop (Ground → Record → Orient → Write)

---

### Decision 5: Frontmatter Schema Definition

**Options:**

| Option | Where categories and fields are defined |
|--------|----------------------------------------|
| A. In CLAUDE.md (inline) | Schema defined in the instruction file |
| B. In schema.py (Python) | Schema defined in a Python module |
| C. In categories.yaml (YAML) | Schema defined in a YAML file |
| D. In a JSON schema file | Schema defined in a JSON Schema |

**Evaluation:**

| Option | Q1: General value | Q2: Extensible |
|--------|-------------------|----------------|
| A | Partially — easy to read but hard to parse programmatically | No — changes require editing the instruction file |
| B | Yes — scripts can import it | Partially — Python-specific, not human-readable |
| C | Yes — human-readable, script-parseable, editor-agnostic | Yes — any tool can read YAML |
| D | Yes — machine-readable, validated | Partially — verbose, not human-friendly |

**Decision: C — categories.yaml.**

Rationale: YAML is human-readable, script-parseable, and editor-agnostic. Scripts can read it with `yaml.safe_load()`. Humans can edit it in any text editor. It's the format already used for raw file frontmatter, so the tooling already supports it. The schema file becomes the single source of truth that both scripts and the LLM reference.

**Schema structure:**

```yaml
# schema/categories.yaml

# Framework-level settings
framework:
  link_format: "markdown"  # "markdown" or "wikilinks"
  n/a_value: "n/a"
  date_format: "YYYY-MM-DD"
  log_format: "## [{date}] {operation} | {title}"

# Required fields on every raw file
required_fields:
  - title
  - source_url
  - date_farmed
  - category

# Optional fields on any raw file
optional_fields:
  - website
  - address
  - phone
  - hours
  - email

# Category definitions
categories:
  landfill:
    required_fields: [accepted_materials, pricing, restrictions]
    analysis_label: "For Our Business"
    analysis_todo: "business implications, best use cases, caveats"
  recycling:
    required_fields: [accepted_materials, pricing, restrictions]
    analysis_label: "For Our Business"
    analysis_todo: "business implications, best use cases, comparison to other yards"
  competitor:
    required_fields: [services, pricing, areas_served]
    analysis_label: "Competitive Position"
    analysis_todo: "strengths, weaknesses, pricing position, market gaps"
```

Each repo extends `categories.yaml` with its own domain. The base framework provides the structure; the repo provides the content.

---

### Decision 6: Corrections / Known-Wrong Tracking

**Options:**

| Option | How known errors are tracked |
|--------|------------------------------|
| A. No tracking | Errors are fixed when found, not tracked |
| B. Corrections file (YAML) | "Wrong → correct → context → source" in a YAML file |
| C. Conversation archive | Record all interactions, synthesize corrections over time |
| D. Git history only | Errors are fixed in commits, history is the record |

**Evaluation:**

| Option | Q1: General value | Q2: Extensible |
|--------|-------------------|----------------|
| A | No — errors recur | No — no mechanism |
| B | Yes — simple, append-only, script-enforced | Yes — format is domain-agnostic |
| C | Partially — rich but complex, high maintenance | Partially — tightly coupled to interaction model |
| D | No — git history doesn't prevent recurrence | No — no prevention mechanism |

**Decision: B — Corrections file (YAML).**

Rationale: The homelab-curriculum pattern is simple, append-only, and script-enforced. A YAML file maps wrong terms to correct versions, with context and source. A script checks all content against the corrections file before commit. This prevents known errors from recurring. The format is domain-agnostic — any repo can adopt it.

**Format:**

```yaml
# schema/corrections.yaml

- wrong: "Old Business Name"
  correct: "New Business Name"
  context: "Business rebranded in 2025"
  source: "raw/competitors/business.md"
  added: 2026-06-17

- wrong: "$45/ton"
  correct: "$65/ton"
  context: "Price increased January 2026"
  source: "raw/landfills/kingsport-demolition-landfill.md"
  added: 2026-06-17
```

**Script integration:** `check_corrections.py` scans all raw and wiki files for known-wrong terms. Added to the pre-commit hook pipeline.

---

### Decision 7: Bootstrap / New Repo Setup

**Options:**

| Option | How a new repo gets a memory system |
|--------|-------------------------------------|
| A. Manual setup | Copy files, edit schema, create directories by hand |
| B. Template repo | GitHub template repo with pre-built structure |
| C. Bootstrap script | `bootstrap.py` that creates directories, schema, scripts, router |
| D. CLI tool | `mex`-style CLI that initializes and manages the scaffold |

**Evaluation:**

| Option | Q1: General value | Q2: Extensible |
|--------|-------------------|----------------|
| A | No — error-prone, tedious, inconsistent | No — each setup is different |
| B | Partially — works for GitHub users, rigid | Partially — template is one-size-fits-all |
| C | Yes — deterministic, repeatable, customizable | Yes — script accepts parameters for domain |
| D | Yes — full lifecycle management | Yes — CLI is extensible |

**Decision: C — Bootstrap script (with B as a complement).**

Rationale: A bootstrap script is deterministic and repeatable. It creates the directory structure, copies the base scripts, generates the initial schema template, creates the router, and initializes the index and log. Parameters customize it for the domain (category names, analysis labels). A template repo can complement this for users who prefer GitHub's template feature.

**Bootstrap script interface:**

```bash
# Initialize a new memory system:
python3 scripts/bootstrap.py \
  --categories landfill,recycling,competitor,strategy \
  --name "My Project Wiki" \
  --link-format markdown

# This creates:
#   raw/{category}/ directories
#   wiki/{category}/ directories
#   schema/categories.yaml (with provided categories)
#   schema/CONVENTIONS.md (framework conventions)
#   schema/corrections.yaml (empty)
#   router.md (task-type routing table)
#   wiki/index.md (generated from categories)
#   wiki/log.md (initialized)
#   scripts/ (copied from base template)
#   CLAUDE.md (thin anchor pointing to router)
```

---

### Decision 8: State Tracking (Now Layer)

**Options:**

| Option | How current state is tracked |
|--------|------------------------------|
| A. No state tracking | Wiki pages are the only knowledge |
| B. STATE.md | Live file tracking current projects, decisions pending, key context |
| C. Git history | Commit messages and diffs are the state record |
| D. Event log (JSONL) | Append-only log of decisions, notes, risks, todos |

**Evaluation:**

| Option | Q1: General value | Q2: Extensible |
|--------|-------------------|----------------|
| A | No — no "what's happening now" layer | No — no mechanism |
| B | Yes — solves the "now" problem, staleness detection | Yes — file is domain-agnostic |
| C | Partially — history is not current state | No — git doesn't track "pending" |
| D | Yes — structured, append-only, machine-parseable | Yes — event types are extensible |

**Decision: B + D — STATE.md for current state, event log for history.**

Rationale: STATE.md tracks "what's happening now" — current projects, decisions pending, key context. The event log tracks "what happened" — decisions made, notes recorded, risks identified. They serve different purposes and are complementary. STATE.md is human-readable and browsable. The event log is machine-parseable and append-only.

**STATE.md staleness detection:** If STATE.md is older than N days (configurable in categories.yaml), the LLM flags it and asks for an update before proceeding. Scripted check via `check_state_freshness.py`.

**Event log format (JSONL):**

```jsonl
{"timestamp": "2026-06-17T14:30:00Z", "kind": "decision", "message": "Switched recycling yard from OmniSource to Davis Recycling", "files": ["raw/recycling/davis-recycling-johnson-city.md"]}
{"timestamp": "2026-06-17T15:00:00Z", "kind": "note", "message": "Kingsport landfill closed for lunch 11:30-12:00", "files": ["raw/landfills/kingsport-demolition-landfill.md"]}
```

---

## Putting It All Together

### What a New Project Gets

1. Run `bootstrap.py` with domain-specific categories
2. Get a complete directory structure, scripts, schema, router, index, and log
3. Start farming raw sources, writing wiki pages, synthesizing research
4. The system grows incrementally — no upfront planning required

### What the LLM Does Each Session

1. Read `router.md` (always)
2. Identify task type
3. Load only the files for that task type
4. Execute the task (following skills if defined)
5. Run the GROW loop (update wiki, router state, create patterns if needed)
6. Run pre-commit validation before committing

### What Scripts Do

| Script | When | What |
|--------|------|------|
| `bootstrap.py` | Once (new repo) | Create directory structure, schema, scripts |
| `validate.py` | Before ingest | Check frontmatter (required fields, dates, categories) |
| `fixup.py` | Before ingest | Add missing fields with defaults |
| `standardize.py` | Before ingest | Normalize placeholder text |
| `ingest.py` | After raw files created | Generate wiki stubs, update index + log |
| `lint.py` | Before commit | 10 structural checks |
| `check_corrections.py` | Before commit | Scan for known-wrong terms |
| `check_state_freshness.py` | On session start | Flag stale STATE.md |
| `find-stubs.py` | During write-wiki | List pages with TODO markers |
| `search.py` | On query (when needed) | Grep/BM25 search across wiki |

### What Stays Per-Repo

- Category definitions in `categories.yaml`
- Domain-specific validation rules
- Custom workflow skills
- State tracking (STATE.md content)
- Corrections (corrections.yaml content)
- The router's "Current Project State" section

---

## Open Questions for Discussion

1. **Link format**: Are standard markdown links the right call, or is the verbosity cost too high? Should we support both formats via a config flag?

2. **Search timing**: Should `search.py` be added from day one (even if just grep), or only when the index gets too large? What's the threshold?

3. **Event log vs. git history**: Is the JSONL event log redundant with git commit messages? Should we rely on git for history and only use STATE.md for current state?

4. **GROW loop enforcement**: Should the GROW loop be a script that prompts the LLM (like mex's HEARTBEAT.md), or an instruction in the skill files that the LLM follows? Scripts are more reliable but less flexible.

5. **Schema migration**: When `categories.yaml` changes (new category, renamed field), how do we handle existing raw/wiki files? A migration script? Manual updates?

6. **Multi-project sharing**: Should corrections.yaml and the bootstrap template live in a shared location (like `~/.claude/memory-framework/`) so all repos can reference them? Or should each repo have its own copy?

7. **Voice/style synthesis**: The homelab-curriculum pattern of synthesizing a voice reference from raw samples is powerful. Should this be part of the base framework, or a domain-specific extension?

8. **Pre-commit hooks**: Should the pre-commit hook be part of the bootstrap (every repo gets it), or optional? It adds friction but catches errors early.
