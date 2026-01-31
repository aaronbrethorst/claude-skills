# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains Claude Code skills - reusable workflows that extend Claude's capabilities through structured prompts and sub-agent orchestration.

## Architecture

Each skill follows a standard structure:
- `SKILL.md` - Main skill definition with YAML frontmatter (name, description, allowed-tools) and workflow instructions
- Supporting markdown files - Additional context, templates, and sub-agent instructions

### Skills

**localizer/** - Software localization using dual-translation verification
- Uses three sub-agents: `translator-alpha`, `translator-beta`, and `translator-adjudicator`
- Auto-detects localization frameworks (React i18n, iOS .strings, Android XML, Rails YAML, etc.)
- Workflow: detect project → validate language code → dual translate → adjudicate → output

**aaron-pr-review/** - GitHub PR review with specialized analysis agents
- `agents/` - Six specialized review agents (code-reviewer, code-simplifier, comment-analyzer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer)
- Agents are launched via Task tool based on applicability scoring (≥80 threshold)
- Produces structured review documents with prioritized feedback (critical/important/suggestions)

## Skill File Format

```yaml
---
name: skill-name
description: When to invoke this skill
allowed-tools: ["Bash", "Read", "Task"]  # Optional
argument-hint: "[optional args]"          # Optional
---

# Skill Title

Workflow instructions in markdown...
```

## Development Notes

- Skills reference sub-documents via relative paths (e.g., `[TRANSLATOR_INSTRUCTIONS.md](TRANSLATOR_INSTRUCTIONS.md)`)
- Sub-agents are invoked via the Task tool with specific subagent_type
- Skills can specify which tools they're allowed to use in the frontmatter
