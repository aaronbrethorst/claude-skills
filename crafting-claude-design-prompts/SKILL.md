---
name: crafting-claude-design-prompts
description: Use when the user wants to generate UI, prototypes, dashboards, presentations, or other design artifacts via Claude Design (claude.ai/design) and asks for help shaping the prompt — especially when the artifact must reflect project data models, multi-step flows, brand systems, or domain context. Triggers on phrases like "write a Claude Design prompt", "draft a prompt for claude.ai/design", "I want to mock this up in Claude Design".
---

# Crafting Claude Design Prompts

## Overview

Claude Design (claude.ai/design) generates designs, interactive prototypes, and presentations from a chat description. It accepts text, screenshots, competitor URLs, wireframes, slide decks, and linked code repos, and applies the org's brand system automatically.

Prompt quality dominates output quality. Vague prompts produce generic AI aesthetic; structured prompts with cardinality, mock data, and a narrow first cut produce something the user can actually react to.

This skill conducts a short interview, pulls relevant project context (Rails models, components, routes), and assembles a copy-paste prompt for the canvas.

## When to Use

Use when the user asks to draft, shape, or improve a Claude Design prompt — or wants Claude Design to mock up something specific from this project.

Do NOT use for:
- Generating UI in code directly — use a frontend-design skill instead.
- One-line clarifications of an existing Claude Design prompt the user already has.

## The Interview

Ask these questions one at a time. If the user already volunteered an answer, skip and confirm. After each answer, paraphrase back in one line so the user can correct.

1. **Goal.** One sentence: what artifact? (e.g. "interactive prototype of a 4-step wizard", "dashboard with filters", "5-slide internal pitch deck")
2. **Audience and tone.** Who uses this and how should it feel?
3. **Fidelity.** Low-fi wireframe, mid-fi clickable prototype, or hi-fi production-ready?
4. **Flow / layout.** Walk me screen-by-screen. For each: what does the user see, what can they click, what advances them?
5. **Data model.** Are there backing records or domain objects? Name them. (Triggers Auto-Context below.)
6. **Mock data.** Give 1–2 realistic example values per entity. If the user is hazy, propose values grounded in the project.
7. **Style and brand.** Which design system? Name specific components (sidebar, command bar, modal). If a Claude Design brand system is set, name it.
8. **Reference material.** Any screenshots, competitor URLs, wireframes, decks to attach? If none, suggest 1–3 well-known products with similar UIs the user could screenshot.
9. **Out of scope.** What should Claude Design NOT try to build? (mobile, auth, real backend, a11y audit, etc.)
10. **First cut.** What's the *minimum* the first iteration must show so we can react? Narrow this aggressively.

Don't ask all 10 if the user has already covered most. Aim for the smallest set that lets you fill every section of the template below.

## Auto-Context

When the user names domain objects, pull context — but distill, don't dump.

- **Rails models named** → Read each `app/models/*.rb`. Extract: `belongs_to`/`has_many` (with `optional:` flags), key validations, enums + allowed transitions, `attribute :foo, …` typed attributes, and any methods that visibly affect UI (e.g. `custom_domain_name`, `provisioned?`). Produce a 4–10 line relationship sketch.
- **Components named** → Locate under `app/components/` or `app/views/`. Note slots, named regions, and key Tailwind utility patterns.
- **Routes mentioned** → Skim `config/routes.rb` for the relevant resources to confirm naming.

What lands in the prompt: entity names, relationships with cardinality, 3–6 fields per entity, and any constraints that visibly affect UI (enum values, required fields, validation rules across associations). Never paste full source.

## The Prompt Template

After the interview, output the filled template inside a single fenced ` ```markdown ` block so the user can copy-paste cleanly.

```markdown
## Goal
[One sentence from Q1.]

## Audience and tone
[From Q2.]

## Fidelity
[From Q3 — e.g. "Hi-fi clickable prototype. Production-ready visuals; mock data; no real backend."]

## Data model
[Cardinality lines + per-entity fields. Example:

- Organization 1—N AppDatabase
- Organization 1—N AppConfig (belongs_to AppConfigTemplate; optional AppDatabase)
- AppConfig 1—N AppService

**AppDatabase** — name (required), description, render plan
**AppConfig** — name (required), description, env vars (repeater, KEY format), dockerfile_config (only when template is OBA API)
**AppService** — name (required), branch (default `main`), docker_image_url, status (enum: uninitialized → deploying → deployed/failed)
]

## Flow
[Numbered steps. For each: what the user sees, what they can do, what advances them.]

## Mock data
[Specific values, not placeholders. Example: org slug `king-county-metro`; template `OBA API`; database name `king_county_metro_oba`; computed domain `api.king-county-metro.obacloud.org`.]

## Style and brand
[Design system + named components + density + light/dark.]

## Reference material
[Attached files / linked URLs. If none: "No attachments — take density from Linear, form layout from Stripe Billing, status pills from Render."]

## Out of scope
[Always non-empty.]

## First cut
[The minimum slice for iteration 1. Be explicit: "Build step 1 (template picker) and step 2 (database form) fully clickable. Stub steps 3–5 as static frames. We'll iterate on 3–5 next."]
```

After the block, add one line: which references to attach when pasting (or "no attachments needed; the prompt is self-contained").

## Quality Checklist

Run this before printing the final prompt. If any item fails, ask one more interview question instead of shipping.

- [ ] Goal is one sentence and names a concrete artifact
- [ ] Data model uses cardinality notation (`1—1`, `1—N`, `N—N`), not prose
- [ ] Each entity lists 3–6 fields, including enums and required flags
- [ ] Flow is numbered; each step states what advances it
- [ ] Mock data has real-looking values, not `<placeholders>`
- [ ] Style section names a design system AND specific components
- [ ] Reference section is filled (attachments OR named visual anchors)
- [ ] Out of scope is non-empty
- [ ] First cut narrows to one iteration's work — not the whole artifact

## Common Mistakes

| Mistake | Why it hurts | Fix |
|---|---|---|
| Data model in prose | Claude Design re-derives relationships, often wrong | Cardinality lines: `A 1—N B` |
| "Build the whole thing" first cut | Output too unfocused to react to | Always narrow First cut to one slice |
| "Modern, clean design" | Generic AI aesthetic | Name a real product or design system |
| Lorem-ipsum mock data | Hard to demo, hard to spot bugs | 1–2 real values per entity |
| Listing fields without constraints | Forms ignore enums, required flags | Surface enums + required fields |
| References without intent | Claude Design copies the wrong attribute | "From X take density. From Y take pill style." |
| Skipping fidelity | Unclear if wireframe or hi-fi expected | Always declare in Fidelity section |

## Red Flags — Stop and Ask

- User wants a wizard but hasn't named the data model → ask Q5, then auto-context.
- User says "match our design system" but doesn't name it → ask for a name or screenshot.
- Flow has 5+ steps and no first-cut narrowing → ask Q10 explicitly.
- User mentions models you can't find on disk → ask before guessing fields.
- User wants real backend behavior → remind them Claude Design produces prototypes; backend goes through Claude Code handoff.
