---
name: aaron-pr-review
description: |
  Review GitHub pull requests with Aaron's specific workflow and feedback format. Use when:
  - User says "/aaron-pr-review" followed by a PR URL, or "review this PR"
  - User provides a GitHub PR URL and wants a code review
  - User asks for PR feedback in Aaron's style

  This skill produces markdown review documents written from aaronbrethorst's perspective with prioritized feedback (critical, important, fit-and-finish) and a kind but firm tone.

  Includes specialized review agents for deep analysis:
  - code-reviewer: General code quality and CLAUDE.md compliance
  - code-simplifier: Code clarity and maintainability
  - comment-analyzer: Comment accuracy and documentation quality
  - pr-test-analyzer: Test coverage quality and completeness
  - silent-failure-hunter: Error handling and silent failures
  - type-design-analyzer: Type design and invariants
allowed-tools: ["Bash", "Glob", "Grep", "Read", "Task"]
argument-hint: "[PR URL or number]"
---

# Aaron's PR Review Workflow

## Setup

Before starting the review, perform these setup steps:

1. **Clean up previous reviews**: Delete any existing `pr-*.md` files in the current directory:
   ```bash
   rm -f pr-*.md
   ```

2. **Ensure latest commits**: To guarantee you're reviewing the latest code, refresh the PR branch:
   ```bash
   # Get the PR branch name from the PR URL/number
   PR_BRANCH=$(gh pr view <number> --json headRefName -q .headRefName)

   # Stash any uncommitted changes
   git stash push -m "aaron-pr-review: auto-stash before branch refresh"

   # Switch to main, delete local branch, fetch, and checkout fresh
   git checkout main
   git branch -D "$PR_BRANCH" 2>/dev/null || true
   git fetch origin
   git checkout "$PR_BRANCH"

   # Restore stashed changes
   git stash pop 2>/dev/null || true
   ```

## Pre-Review Analysis

Before reviewing code changes, **always check existing PR comments first**:

1. Use `gh pr view <number> --comments` to scan for prior feedback from aaronbrethorst
2. If prior feedback exists:
   - Identify which items the author has addressed
   - Check if author provided clarifications for items they chose not to address
   - Focus your review on new/unaddressed changes
   - Treat author explanations with courtesy—they likely have good reasons

## Code Review Process

1. Fetch PR details: `gh pr view <number> --json title,body,author,files,additions,deletions`
2. Get the diff: `gh pr diff <number>`
3. Read changed files to understand context
4. Run tests if applicable: `make test` or equivalent
5. Check lint/format: `make lint` or equivalent
6. Identify file types to determine which agents apply

## Agent Applicability Assessment

**MANDATORY**: Before launching agents, assess each one's applicability to this PR. Assign confidence scores (0-100) and use agents scoring **≥ 80**.

Output format:
```
## Agent Applicability Assessment

| Agent | Confidence | Rationale | Use? |
|-------|------------|-----------|------|
| code-reviewer | [0-100] | [Brief reason] | [Yes/No] |
| silent-failure-hunter | [0-100] | [Brief reason] | [Yes/No] |
| pr-test-analyzer | [0-100] | [Brief reason] | [Yes/No] |
| comment-analyzer | [0-100] | [Brief reason] | [Yes/No] |
| type-design-analyzer | [0-100] | [Brief reason] | [Yes/No] |
| code-simplifier | [0-100] | [Brief reason] | [Yes/No] |
```

For detailed scoring guidelines and examples, see [applicability.md](applicability.md).

## Launch Review Agents

After assessment, launch all agents marked "Yes" via the Task tool.

**Sequential**: One agent at a time—easier to understand, good for interactive review.

**Parallel**: Launch all simultaneously—faster for comprehensive review (user can request with `parallel`).

For agent descriptions and invocation details, see [agents.md](agents.md).

## Aggregate Results

After agents complete, summarize findings:

```markdown
# PR Review Summary

## Critical Issues (X found)
- [agent-name]: Issue description [file:line]

## Important Issues (X found)
- [agent-name]: Issue description [file:line]

## Suggestions (X found)
- [agent-name]: Suggestion [file:line]

## Strengths
- What's well-done in this PR

## Recommended Action
1. Fix critical issues first
2. Address important issues
3. Consider suggestions
4. Re-run review after fixes
```

## Review Output

When finished, provide:

1. **Verbal verdict**: Tell the user "merge" or "request changes"
2. **Written review**: Create `pr-{id}.md` in the current directory

For review document templates (first-time, subsequent, ready-to-merge), see [templates.md](templates.md).

## Post-Review

After writing the review document, ask: "Would you like me to copy the markdown to your clipboard?"

When user confirms, run:
```bash
cat pr-{id}.md | pbcopy
```

## Style Guidelines

- **Tone**: Kind but firm. Be encouraging while being clear about requirements.
- **Uniqueness**: Put a unique spin on the greeting/compliment for each PR—avoid robotic repetition.
- **Specificity**: Reference actual code, file names, and line numbers where relevant.
- **Author's name**: Use their first name from the PR author info.
- **Never mention PR count**: Do not reference how many PRs the author has made. Never say "first PR", "welcome as a new contributor", "your Nth contribution", or anything similar. Focus on the code, not the author's contribution history.

## Additional Resources

- For review templates, see [templates.md](templates.md)
- For agent descriptions, see [agents.md](agents.md)
- For applicability guidelines, see [applicability.md](applicability.md)
- For usage examples, see [examples.md](examples.md)
- For iOS code reviews, use the sosumi MCP server to fetch official Apple documentation as needed.