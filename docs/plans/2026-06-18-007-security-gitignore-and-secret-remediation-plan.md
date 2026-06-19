---
title: "security: Gitignore and Secret Scanning Remediation"
type: fix
status: completed
date: 2026-06-18
---

# Gitignore and Secret Scanning Remediation

## Summary

GitHub secret scanning flagged 5 Google API key alerts. All are false positives — they exist in a third-party package's test file (`youtube_transcript_api/test/assets/youtube.html.static`) that was committed as part of a virtual environment. The venv was committed because `.knap/scripts/.venv/` was not in `.gitignore`. The `.gitignore` also has several other gaps and incorrect entries.

## Root Cause

1. **Venv committed to history.** Commit `0524076` ("feat: move framework files to .knap/ directory") added 712 files including `.knap/scripts/.venv/`. The `.gitignore` only covered `.knap/.venv/` (different path). The venv was later removed from tracking, but the commit remains in history.

2. **Incomplete .gitignore.** The current `.gitignore` covers only 6 patterns and has incorrect entries:
   - `scripts/__pycache__/` — should be `__pycache__/` (generic)
   - `scripts/.pytest_cache` — should be `.pytest_cache/` (generic, with trailing slash)
   - `.pytest_cache` — missing trailing slash
   - Missing: `.venv/`, `.knap/scripts/.venv/`, `.env`, `*.egg-info/`, `.mypy_cache/`, `.ruff_cache/`, etc. (Note: `.knap/scripts/.venv/` was deliberately removed in commit `47259b6` as a "stale entry" — this was incorrect because the venv still existed on disk.)

3. **No actual secrets exposed.** The flagged "secrets" are in a third-party package's test HTML file, not project API keys. No `.env` files or hardcoded secrets exist in the source code.

## Remediation Plan

### Step 1: Fix .gitignore

Replace the current `.gitignore` with a comprehensive version covering all Python, IDE, OS, and project-specific patterns.

**New `.gitignore`:**

```gitignore
# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
*.egg
dist/
build/
develop-eggs/
downloads/
eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.manifest
*.spec

# Virtual environments
.venv/
venv/
ENV/
env/
.knap/.venv/
.knap/scripts/.venv/

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/
*.cover

# Type checking / linting
.mypy_cache/
.ruff_cache/
.pytype/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment / secrets
.env
.env.*
!.env.example

# Logs
*.log
```

### Step 2: Remove any tracked files that match new .gitignore patterns

Check if any currently-tracked files should be removed based on the updated `.gitignore`. Run `git ls-files --cached` and compare against new patterns.

**Current status:** No venv or cache files are currently tracked (verified: 0 files in `.knap/scripts/.venv/` and `.knap/.venv/`). The venv was removed from tracking in a prior commit.

### Step 3: Resolve secret scanning alerts

All 5 alerts are in the same file: `.knap/scripts/.venv/lib/python3.12/site-packages/youtube_transcript_api/test/assets/youtube.html.static` (line 19). These are Google API keys embedded in a third-party package's test file — not project secrets. The file is no longer tracked (removed from git in a prior commit), but the alerts persist because the commit remains in history.

**Action:** Query actual alert IDs, then mark all as "false positive" via GitHub API:

```bash
# Get actual open alert IDs
ALERT_IDS=$(gh api repos/Taegost/knap/secret-scanning/alerts --jq '.[] | select(.state=="open") | .number')

# Resolve each alert
for id in $ALERT_IDS; do
  echo "Resolving alert $id..."
  gh api -X PATCH "repos/Taegost/knap/secret-scanning/alerts/$id" \
    -f state=resolved \
    -f resolution=false_positive \
    -f resolution_reason="Secret is in a third-party package test file (youtube_transcript_api), not a project secret" \
  || echo "FAILED: alert $id"
done
```

### Step 4: Commit changes

Commit the `.gitignore` update with a clear message:

```bash
git add .gitignore
git commit -m "fix: comprehensive .gitignore for Python, venv, IDE, and OS patterns

- Generic __pycache__/ instead of scripts/__pycache__/
- Proper .pytest_cache/ with trailing slash
- Cover all venv paths including .knap/scripts/.venv/
- Add .env, .mypy_cache, .ruff_cache, IDE files
- Addresses GitHub secret scanning false positives from committed venv"
```

## Verification

1. `.gitignore` covers all common Python, IDE, OS, and project patterns
2. No venv, cache, or env files are tracked by git
3. All 5 secret scanning alerts resolved as false positives
4. `git status` is clean after commit

## Files Modified

- `.gitignore` — comprehensive rewrite

## Out of Scope

- **Git history rewriting** (BFG, filter-branch). The venv commit (`0524076`) is in history but the files are no longer tracked. Rewriting history is destructive and requires force-push. Not recommended for this case since no actual secrets are exposed.
- **Rotating the flagged API keys.** The keys are in a third-party package's test file, not project credentials. No rotation needed.
