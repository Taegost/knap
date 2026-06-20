---
title: Skill Identification Prompt
source_url: n/a
date_farmed: 2026-06-17
category: prompt
description: Prompt to identify skills, scripts, and documents that should be created
  or updated based on recent work
---

## Prompt

Based on our recent back-and-forth, what skill(s), script(s), and/or document(s) can be created or updated to improve the process, reduce errors, and improve repeatability. Bias towards scripts whenever possible.

## Usage

Run after a session where you've been doing repetitive work or fixing the same issues. Claude reviews the conversation and suggests concrete improvements to the system.

## Adaptation

The original version from the user:
> "Based on my recent sessions, what tasks am I doing repeatedly that should be skills instead of one-off prompts? For each one, suggest a skill name and what context it would need."

The adapted version biases toward scripts (deterministic, cheaper, repeatable) over skills (LLM-driven, variable).
