---
title: "feat: Plan Lint"
type: feat
status: deferred
date: 2026-06-18
origin: meta (observed pattern during doc reviews)
---

# Plan Lint

A hybrid script + LLM skill that catches internal drift in planning documents. The script handles mechanical consistency checks; the LLM handles semantic judgment on flagged items.

## Problem Frame

Planning documents repeat concepts across Goal, Files, Approach, and Test Scenarios within each implementation unit. A change to one section rarely propagates to the others. During walkthrough reviews, per-finding edits fix the targeted section but miss sibling sections that describe the same concept. This has caused repeated drift — a user clarification gets applied to the Approach but not the Files section, or a renamed requirement ID gets updated in one unit but not another.

## Key Decisions

**Hybrid approach.** A Python script does deterministic extraction and structural checks. A Claude Code skill wraps the script and adds LLM judgment on flagged items. The script reduces the search space from "entire document" to "these N locations look inconsistent."

**Script handles structure, LLM handles semantics.** Requirement ID coverage, file path cross-references, dependency resolution — these are mechanical. Whether two differently-worded descriptions mean the same thing, whether a clarification propagated everywhere — these need judgment.

**Non-blocking by default.** The tool reports findings, it doesn't block. Integrate into the review workflow, not as a gate.

## Scriptable Checks

**S1. Requirement ID coverage.** Extract all IDs from the Requirements section using the definition pattern (`[A-Z]+\d+\. `). For each ID, verify it's referenced in at least one unit's Requirements line. References use a different format — comma-separated without periods (e.g., `C1, C2, C3, C4`) — so use a reference pattern (`[A-Z]+\d+`) when scanning unit Requirements lines. Flag unreferenced requirements.

**S2. Unit requirement references.** For each unit's Requirements line, verify every referenced ID exists in the Requirements section. Flag dangling references.

**S3. Unit dependency references.** For each unit's Dependencies line, verify every referenced U-ID exists. Flag dangling dependencies.

**S4. File path cross-reference.** For each unit, extract file paths from the Files section. Normalize each path to its filename component (e.g., `.knap/scripts/schema.py` → `schema.py`). Check whether the filename or full path appears as a substring in the Approach section. Treat phrases like "no change needed" or "unchanged" alongside a filename as a valid reference. Flag paths in Files that aren't mentioned in Approach.

**S5. Deferred item resolution.** For each item in "Deferred for later", verify the referenced plan/brainstorm file exists. Flag missing files.

**S6. Key term drift.** For each unit, extract significant terms from the Goal line (3+ word phrases, requirement IDs, file names). Check whether those terms appear in the Approach section. Flag Goal terms absent from Approach — may indicate the approach wasn't updated to match the goal.

**S7. Cross-unit terminology (heuristic pre-filter).** Extract significant multi-word phrases (2-4 words) from Goal, Files, and Approach sections across all units. For each phrase, check if it appears as a substring of a different phrase in another unit. If "required fields" appears in Unit A but "global required fields" appears in Unit B, flag it — the base term is shared but the modifier differs. This catches prefix/suffix drift (the most common pattern) without requiring semantic understanding. The LLM skill reviews flagged candidates to decide if the drift matters.

## LLM-Driven Checks

The skill runs the script first, then reviews flagged items:

- **Semantic equivalence.** Are two differently-worded descriptions actually saying the same thing? If so, normalize. If they're saying different things, flag as a contradiction.
- **Clarification propagation.** When a user clarification changes behavior in one section, check all sibling sections in the same unit for stale descriptions.
- **Intent vs. text.** Does the text match the author's stated intent, or did a mechanical edit leave drift?

## Implementation Units

### U1. Plan parser script

- **Goal:** Python script that parses a markdown plan document and extracts structural elements.
- **Dependencies:** None
- **Files:**
  - `.knap/scripts/plan_lint.py` — new: parses plan markdown, runs checks S1-S7, outputs structured report
- **Approach:** Parse the document by splitting on `## ` and `### ` headings. Extract: frontmatter (YAML), Requirements section IDs, each unit's Goal/Requirements/Dependencies/Files/Approach/Test Scenarios/Verification lines. Run each check and collect findings. For S7, extract 2-4 word phrases from Goal/Files/Approach across all units and flag substring overlaps (e.g., "required fields" vs "global required fields"). Output as structured text (grouped by check type, with file:line references). Error handling: if the document lacks frontmatter or an Implementation Units section, exit with a clear error message. If a unit lacks expected subsections, skip checks that depend on those subsections and note the skip in output.
- **Test scenarios:**
  - Parses a plan with 3+ units correctly
  - Detects a requirement ID referenced in a unit but not defined in Requirements
  - Detects a file path in Files but absent from Approach
  - Detects a dangling U-ID dependency
  - Detects cross-unit terminology drift (e.g., "required fields" vs "global required fields")
  - Reports no false positives on the current foundation plan (true positives about real drift are expected)
- **Verification:** `python3 .knap/scripts/plan_lint.py docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md` outputs a clean report.

### U2. LLM review skill

- **Goal:** Claude Code skill that runs plan_lint.py and reviews findings with LLM judgment.
- **Dependencies:** U1
- **Files:**
  - `.claude/skills/knap-plan-lint/SKILL.md` — new: skill definition
- **Approach:** The skill runs `python3 .knap/scripts/plan_lint.py <plan-file>`, reads the structured output, then applies LLM judgment to each flagged item: is it a real inconsistency or a false positive? Does it need a fix? Present findings grouped by severity (contradictions first, then drift, then style). Suggest fixes for real issues.
- **Test scenarios:**
  - `/knap-plan-lint docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md` runs cleanly
  - Catches the validate.py category field drift that was missed during the walkthrough
  - Produces zero false positives on well-formed plans
- **Verification:** Skill runs and produces actionable findings on the foundation plan.

### U3. Unit and smoke tests

- **Goal:** pytest test suite for plan_lint.py covering each check and edge cases.
- **Dependencies:** U1
- **Files:**
  - `.knap/scripts/test_plan_lint.py` — new: pytest tests
- **Approach:** Use pytest with fixture files (small markdown plan snippets) to test each check in isolation. Fixtures cover: well-formed plan (no findings), missing requirement reference, dangling U-ID dependency, file path in Files but absent from Approach, cross-unit terminology drift, malformed document (no frontmatter, no Implementation Units), unit with missing subsections. Smoke test: run `plan_lint.py` against all existing plans in `docs/plans/` and verify it doesn't crash.
- **Test scenarios:**
  - `pytest .knap/scripts/test_plan_lint.py` passes
  - Each check (S1-S7) has at least one positive and one negative test case
  - Malformed input produces clear error messages, not tracebacks
  - Smoke test against all existing plans completes without crashes
- **Verification:** `pytest .knap/scripts/test_plan_lint.py` returns 0 failures.

## Scope Boundaries

**In scope:**
- Structural consistency checks (IDs, paths, cross-references)
- Semantic drift detection via LLM review
- Integration as a Claude Code skill

**Deferred:**
- Auto-fix capability (report only for now)
- CI/CD integration
- Support for requirements docs (only plans for now)
- Cross-document consistency (plan ↔ origin requirements)

## Sources / Research

- Observed pattern: per-finding walkthrough edits don't propagate to sibling sections
- Existing lint.py pattern: script + CLI for structural checks
- ce-doc-review pattern: script + LLM for semantic judgment
