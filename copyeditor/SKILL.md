---
name: copyeditor
description: Review and edit prose for clarity, concision, and force using rules from Strunk & White and George Orwell. Use when the user asks to copyedit, tighten, edit, review, or improve a piece of writing, blog post, essay, email, or documentation. Triggers on "copyedit this", "tighten this up", "edit my writing", "review this post", or any request to improve prose quality.
---

# Copyeditor

## Workflow

1. Read the piece in full before making any changes.
2. Read [references/rules.md](references/rules.md) to load the rules.
3. Make a first pass identifying violations. For each, note the rule violated and why the original is weaker.
4. Present findings as a numbered list of suggested edits. For each:
   - Quote the original text
   - State which rule applies
   - Propose a revision
   - Briefly explain why the revision is stronger
5. After presenting edits, ask the user which to apply. Apply only approved changes.

## Principles

- Preserve the author's voice. Fix the mechanics, not the personality.
- Favor surgical edits over rewrites. Change the minimum needed.
- When two rules conflict, Orwell's sixth rule wins: break any rule sooner than say anything barbarous.
- Do not add words. The goal is nearly always fewer words, not more.
- Do not flag stylistic choices that are clearly intentional (sentence fragments for emphasis, informal tone in blog posts, etc.).
- Group related edits together rather than flagging the same pattern ten times.
