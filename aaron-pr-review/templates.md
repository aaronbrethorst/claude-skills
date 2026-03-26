# Review Templates

Templates for writing PR review documents.

## Document Format

**Never include in the document:**
- References to CLAUDE.md or Claude Code
- Agent names or references to review agents (e.g., `[code-reviewer]`, `[silent-failure-hunter]`). The review must read as if written entirely by aaronbrethorst—agents are internal implementation details.
- Optional tasks—all feedback must be addressed
- Don't guess about the author's name. If it is not explicitly listed in their GitHub profile then refer to them by their GitHub username.
- Any mention of how many PRs the author has made (e.g., "first PR", "your Nth contribution", "welcome as a new contributor"). We never know or comment on the author's PR history.

**Always include at the bottom of every review document:**
```
---

Verdict: {Merge or Request Changes}
URL: {original PR URL}
```

**Verdict is a strict binary:**
- **Merge**: PR is ready to merge as-is. If there are issues that don't need to be resolved in the scope of this PR, create a GitHub issue tracking the remaining fixes (via `gh issue create`) and reference it in the review.
- **Request Changes**: PR has issues that must be resolved before merging. There is no "merge after this change"—if changes are needed before merge, the verdict is Request Changes.

**Priority levels for changes:**
- **Critical**: Blocks merge, must fix (bugs, security issues, broken functionality)
- **Important**: Should fix before merge (code quality, maintainability, missing tests)
- **Fit and Finish**: Polish items (naming, minor style, documentation gaps)

## Initial Review Template

Use when this is aaronbrethorst's first comment on the PR (NOT the author's first PR—never mention that):

```markdown
Hey {Author First Name}, thanks for taking the time to make this {change|fix|improvement} to {core purpose}. {Genuine compliment about the change}. Before we can merge this, I will need you to make a couple changes:

## Critical

{List critical items, or omit section if none}

## Important

{List important items, or omit section if none}

## Fit and Finish

{List polish items, or omit section if none}

{If the PR requires a rebase against main, develop, or another branch, refer the PR author to this blog post I wrote to help demystify rebasing: https://www.brethorsting.com/blog/2026/01/git-rebase-for-the-terrified/}

Thanks again, and I look forward to merging this change.

---

Verdict: {Merge or Request Changes}
URL: {PR URL}
```

## Subsequent Review Template

Use when aaronbrethorst has already posted review comments on the PR:

```markdown
Hey {Author First Name}, you're making great progress on {core purpose}. Before we can merge this, I need you to make a couple more changes:

## Critical

{List remaining critical items, or omit section if none}

## Important

{List remaining important items, or omit section if none}

## Fit and Finish

{List remaining polish items, or omit section if none}

Thanks again, and I look forward to merging this change.

---

Verdict: {Merge or Request Changes}
URL: {PR URL}
```

## Ready-to-Merge Format

When no changes are needed:

```markdown
Hey {Author First Name}, {acknowledge their work on this PR—mention what they did well}. {If this was a subsequent review, acknowledge they addressed all feedback.}

There's nothing left to change—this PR is ready to merge. {Closing thought about the contribution.}

---

Verdict: Merge
URL: {PR URL}
```

## Ready-to-Merge with Follow-Up Issues

When the PR is ready to merge but has minor issues that don't need to be resolved in the current PR's scope. Before writing this review, create a GitHub issue (via `gh issue create`) tracking the remaining fixes.

```markdown
Hey {Author First Name}, {acknowledge their work on this PR—mention what they did well}. {If this was a subsequent review, acknowledge they addressed all feedback.}

This PR is ready to merge. I noticed a few things that could be improved, but they don't need to be addressed here. I've opened {issue link} to track the follow-up work:

{Brief list of the items tracked in the issue}

{Closing thought about the contribution.}

---

Verdict: Merge
URL: {PR URL}
```
