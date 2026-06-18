---
name: knap-plan-lint
description: "Lint planning documents for internal consistency. Runs structural checks and applies LLM judgment."
user_invocable: true
---

# Plan Lint Skill

A hybrid script + LLM skill that catches internal drift in planning documents. The script handles mechanical consistency checks; the LLM handles semantic judgment on flagged items.

## Usage

```
/knap-plan-lint <plan-file>
/knap-plan-lint docs/plans/2026-06-17-001-feat-memory-system-foundation-plan.md
```

## Process

### 1. Run structural checks

```bash
source .knap/.venv/bin/activate
python3 .knap/scripts/plan_lint.py <plan-file>
```

The script checks:
- **S1.** Requirement ID coverage — all defined IDs referenced in units
- **S2.** Unit requirement references — all referenced IDs exist in Requirements
- **S3.** Unit dependency references — all U-IDs exist
- **S4.** File path cross-reference — Files paths mentioned in Approach
- **S5.** Deferred item resolution — referenced files exist
- **S6.** Key term drift — Goal terms appear in Approach
- **S7.** Cross-unit terminology — substring overlaps between units

### 2. Review findings with LLM judgment

Read the script's output. For each flagged item, determine:

- **False positive?** — The check caught a pattern that isn't actually a problem (e.g., a file path mentioned in a different format)
- **Real drift?** — A section was updated but sibling sections weren't propagated
- **Contradiction?** — Two sections say different things about the same concept

### 3. Present findings grouped by severity

1. **Contradictions** — Sections that say different things (highest priority)
2. **Drift** — Sections that should match but don't
3. **Style** — Inconsistent terminology or formatting

For each real issue, suggest a fix:
- Which section needs updating
- What the corrected text should say
- Whether the change affects other units

### 4. Output format

```
## Plan Lint: <filename>

### Contradictions
- U2 Requirements says "C1, C2" but Goal only mentions C1

### Drift
- U1 Files lists `schema.py` but Approach doesn't mention it
- U3 Goal says "required fields" but U1 says "global required fields"

### Style
- S7: "required fields" vs "global required fields" (between U1 and U3)

### Summary
- X contradictions, Y drift items, Z style notes
- Recommended fixes: [list]
```

## When to use

- After editing a planning document
- Before presenting a plan for review
- When you suspect internal drift in a plan
- As part of the planning workflow (`/ce-plan`)

## Limitations

- Only checks markdown plans (not HTML)
- Requires Implementation Units section
- S7 cross-unit check is heuristic (may produce false positives)
- No auto-fix capability (report only)
