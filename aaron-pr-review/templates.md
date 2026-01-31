# Review Templates

Templates for writing PR review documents.

## Document Format

**Never include in the document:**
- The verdict (redundant—user already heard it)
- References to CLAUDE.md or Claude Code
- Optional tasks—all feedback must be addressed

**Priority levels for changes:**
- **Critical**: Blocks merge, must fix (bugs, security issues, broken functionality)
- **Important**: Should fix before merge (code quality, maintainability, missing tests)
- **Fit and Finish**: Polish items (naming, minor style, documentation gaps)

## First-Time Review Template

Use when this is aaronbrethorst's first comment on the PR:

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
```

## Ready-to-Merge Format

When no changes are needed:

```markdown
Hey {Author First Name}, {acknowledge their work on this PR—mention what they did well}. {If this was a subsequent review, acknowledge they addressed all feedback.}

There's nothing left to change—this PR is ready to merge. {Closing thought about the contribution.}
```
