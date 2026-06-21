---
title: 'chore: Config File Defaults Template'
type: chore
status: deferred
date: 2026-06-20
---

# Config File Defaults Template

Deferred from the Orphan Content Checker plan. Knap config files (like `folders.yaml`, `categories.yaml`) should have a template with sensible defaults that gets created automatically if the config file doesn't exist.

## Problem Frame

Currently, config files are expected to exist but there's no mechanism to create them with defaults if missing. Scripts should gracefully handle missing configs, but having a template ensures users start with documented, working defaults.

## Requirements (TBD)

- A template system for config files with default values
- Scripts create config from template if file doesn't exist
- Defaults are documented and match the project's conventions

## Dependencies

- Orphan Content Checker plan (folder classification config pattern)
- `categories.yaml` existing pattern
