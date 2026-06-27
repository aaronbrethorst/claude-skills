---
name: fix-rails-issues
description: Batch-fix GitHub issues with a disciplined per-issue workflow. Use when the user wants to fix multiple GitHub issues in sequence (e.g. "fix issues #10-#15", "fix these issues", or lists of issue numbers). Chains with /rails-development for each fix. Applies TDD, linting, review, and simplification to every issue before committing, then runs a full suite and opens a single PR.
---

# Fix Issues

Batch-fix a range of GitHub issues using a structured, per-issue workflow.

## Input Parsing

Accept issue references in any of these forms:
- Range: `#10-#15`, `#10 - #15`, `issues 10 through 15`
- List: `#10, #12, #15` or `#10 #12 #15`
- Mixed: `#10-#12, #15`

Determine the repo from the current git remote (`gh repo view --json nameWithOwner -q .nameWithOwner`).

## Workflow

### 1. Build the task list

Fetch each issue via `gh issue view <number>` to get its title and body. Create a task list with one entry per issue, plus a final "suite + PR" task.

### 2. Per-issue loop

For each issue, execute these steps in order. Do not skip any step.

1. **Invoke /rails-development** to fix the issue. Use a red-to-green TDD approach whenever applicable: write a failing test first, then make it pass.
2. **Run Rubocop and RSpec** (`bin/rubocop && bundle exec rspec`) to verify nothing is broken.
3. **Run /pr-review-toolkit:review-pr** against the uncommitted changes.
4. **Run /simplify** against the changes.
5. **Run Rubocop and RSpec** one more time to confirm the review/simplify passes didn't break anything.
6. **Commit** the changes with a message referencing the issue number and title (e.g. `Fix #42: Prevent nil error in widget export`).

Mark the task complete before moving to the next issue.

### 3. Final verification and PR

After all issues are fixed and committed:

1. Run the full verification suite:
   - `bin/rubocop`
   - `bundle exec brakeman -q`
   - `bundle exec rspec` (full suite)
2. Fix any failures before proceeding.
3. Push the branch and open a single PR that references all fixed issues. Include each issue number in the PR body so they auto-close on merge.
