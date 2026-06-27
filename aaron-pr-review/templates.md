# Review Templates

How I write PR review comments. The structural rules at the bottom are load-bearing; the Voice section is the part that actually keeps reviews readable.

## Voice

Write the review the way you'd say it to the person if they were sitting next to you. A real engineer read their code and has a few things to say — that's the whole feeling we're after.

- **Keep it short.** Most reviews are a paragraph of context and a short list of changes. If it's running long, you're probably explaining things the author already knows.
- **One honest compliment, not a performance.** Say the true thing you noticed and move on. Drop "genuinely," "a model of," "exactly right," "precisely" — they read as filler.
- **Don't bold words mid-sentence.** Let the sentence carry the emphasis. Bold is for the priority headers and nothing else.
- **Go easy on em-dashes.** One per paragraph, tops.
- **Don't list every edge case you can imagine.** Pick what matters for this change and leave the rest.
- **Point to `file:line`, then explain it plainly.** No three-level-deep nested sub-points.
- **Assume the author knows what they're doing.** You're flagging things, not teaching a course.

The test: read it out loud. If it sounds like a memo or a lint report, rewrite it until it sounds like you.

## Document rules

**Never include:**
- References to CLAUDE.md or Claude Code.
- Agent names or references to review agents. The review reads as if I wrote all of it.
- Optional tasks — all feedback must be addressed.
- A guess at the author's name. If it isn't on their GitHub profile, use their username.
- Anything about the author's PR history (no "first PR," "your Nth contribution," "welcome as a new contributor"). We don't know it and we don't comment on it.

**Always end with:**
```
---

Verdict: {Merge or Request Changes}
URL: {original PR URL}
```

**Verdict is a strict binary:**
- **Merge** — ready to merge as-is. If there's leftover work that doesn't belong in this PR's scope, open a tracking issue (`gh issue create`) and link it.
- **Request Changes** — has issues that must be fixed before merging. There is no "merge after this change." If something needs fixing first, the verdict is Request Changes.

**Priority levels:**
- **Critical** — blocks merge (bugs, security, broken functionality).
- **Important** — should fix before merge (code quality, maintainability, missing tests).
- **Fit and Finish** — polish (naming, minor style, doc gaps).

A misleading or incorrect comment is never a merge blocker. The code is what ships; a wrong comment is at most Fit and Finish, and usually a follow-up. Flag it, but don't hold the PR over it.

## Initial review

My first comment on the PR:

```markdown
Hey {First Name}, thanks for taking this on. {One true sentence about what's good.} A few things before I can merge it:

## Critical
{items, or drop the section}

## Important
{items, or drop the section}

## Fit and Finish
{items, or drop the section}

{If it needs a rebase, point them at https://www.brethorsting.com/blog/2026/01/git-rebase-for-the-terrified/}

Thanks — looking forward to merging this.

---

Verdict: {Merge or Request Changes}
URL: {PR URL}
```

## Subsequent review

When I've already commented on the PR:

```markdown
Hey {First Name}, good progress. A couple more things before this is ready:

## Critical
{remaining items, or drop the section}

## Important
{remaining items, or drop the section}

## Fit and Finish
{remaining items, or drop the section}

Thanks — looking forward to merging this.

---

Verdict: {Merge or Request Changes}
URL: {PR URL}
```

## Ready to merge

Nothing to change:

```markdown
Hey {First Name}, {what they did well, in a sentence or two}. {If this was a follow-up review, note they addressed everything.}

Nothing left to change — this is ready to merge. {One closing thought.}

---

Verdict: Merge
URL: {PR URL}
```

## Ready to merge, with follow-ups

Ready to merge, but with minor things that don't belong in this PR. Open the tracking issue (`gh issue create`) before writing the review.

```markdown
Hey {First Name}, {what they did well}. {If a follow-up review, note they addressed everything.}

This is ready to merge. A few things I'd tidy up eventually, but none of them belong here — I've opened {issue link} to track them:

{Short list of what's in the issue, one line each.}

{One closing thought.}

---

Verdict: Merge
URL: {PR URL}
```
