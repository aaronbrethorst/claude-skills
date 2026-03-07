---
name: investigate-sentry
description: Investigate and fix production errors from Sentry. Use when given a Sentry issue URL, numeric issue ID, or short ID (e.g. VOTERLETTERS-9R). Fetches full issue data via the Sentry MCP, analyzes root cause, scores fix confidence, and applies a TDD red-to-green fix in the Rails app. Triggers on "fix this Sentry issue", "investigate PROJ-XX", any sentry.io URL, or requests to debug a production error from Sentry.
---

# Sentry Issue Investigation & Fix

Fetch a Sentry issue, analyze root cause, score confidence, and fix via TDD.

## Workflow

1. **Fetch** — Subagent retrieves all Sentry issue data, writes to tempfile
2. **Analyze** — Subagent scores the issue on three dimensions
3. **Decide** — Branch on scores to plan-only, plan-then-fix, or auto-fix
4. **Fix** — TDD red-to-green: write failing spec from Sentry data, then implement fix

## Phase 1: Fetch Sentry Data

Launch a **general-purpose** subagent with this prompt structure:

```
Retrieve all data for Sentry issue [INPUT].

Use the Sentry MCP tools:
- If INPUT is a full sentry.io URL: use get_issue_details with issueUrl parameter
- If INPUT looks like a short ID (e.g. VOTERLETTERS-9R): use get_issue_details with issueId and organizationSlug
- If INPUT is numeric: use get_issue_details with issueId and organizationSlug

If organizationSlug is unknown, call find_organizations first to discover it.

After getting issue details, also retrieve:
- Tag values for: environment, browser, url, release (use get_issue_tag_values)
- Recent events within the issue (use search_issue_events with "recent events")

Write ALL retrieved data as structured markdown to a tempfile at /tmp/sentry-issue-{SHORT_ID or ID}.md
Return the tempfile path.
```

The subagent returns the tempfile path.

## Phase 2: Analyze and Score

Launch a **general-purpose** subagent. Include `/rails-development` skill invocation and use context7 MCP for Rails documentation. Pass the tempfile path from Phase 1.

Prompt structure:

```
Read the Sentry issue data from [TEMPFILE_PATH].

Invoke the /rails-development skill for Rails conventions.
Use context7 MCP for any Rails/Ruby API questions.

Analyze the issue:
1. Parse the error class, message, and full stack trace
2. Identify the root cause file(s) and line(s) in the codebase
3. Read those files and surrounding code to understand the bug
4. Check for related specs that already exist
5. Determine what the fix would entail

Score on three dimensions (0-100 each):

| Dimension | 0 | 100 |
|-----------|---|-----|
| Simplicity | Very complex, multi-system | Trivial single-line fix |
| Root Cause Confidence | No idea what causes it | Certain of exact cause |
| Regression Safety | Fix will certainly break things | Fix is completely isolated |

Output format — return EXACTLY this structure:

SCORES:
simplicity: [N]
confidence: [N]
regression_safety: [N]
combined: [sum]

ROOT_CAUSE:
[1-3 sentence explanation]

AFFECTED_FILES:
[list of file paths]

PROPOSED_FIX:
[concise description of the fix]

FAILING_SPEC_STRATEGY:
[how to reproduce in RSpec using Sentry event data]
```

## Phase 3: Decision Tree

Parse the scores from the subagent response and branch:

### Path A: User Review Required
**Condition:** Any score <= 30 OR combined < 150

The issue is too risky or uncertain for autonomous fixing. Enter plan mode and present the analysis to the user for evaluation. Include the full score breakdown, proposed fix, and why confidence is low or risk is high.

### Path B: Auto-Fix
**Condition:** All three scores > 80

The issue is simple, well-understood, and safe. Proceed directly to Phase 4 (TDD Fix).

### Path C: Plan Then Fix
**Condition:** All other cases (scores between 30-80, combined >= 150)

Enter plan mode to create a detailed fix plan covering:
- Exact spec to write (with code outline)
- Exact production code change
- Which existing specs to run for regression check

Then proceed to Phase 4 to implement.

## Phase 4: TDD Fix (Red-to-Green)

Launch a **general-purpose** subagent with `/rails-development` skill and context7 MCP.

1. **Write the failing spec first.** Use error data from Sentry (error class, message, request params, user context) to construct a spec that reproduces the exact failure. Use RSpec with FactoryBot (check the project — if it uses Minitest, use that instead).

2. **Run the spec — confirm it fails (RED).** The spec MUST fail for the right reason (same error as Sentry). If it passes, the spec doesn't reproduce the issue — revise it.

3. **Implement the minimal fix.** Fix the root cause, not symptoms. Follow rails-development skill conventions.

4. **Run the spec — confirm it passes (GREEN).** The previously-failing spec now passes.

5. **Run the broader spec suite** for affected files to catch regressions:
   ```
   bundle exec rspec spec/models/[affected]_spec.rb spec/requests/[affected]_spec.rb
   ```

6. **Report results.** Summarize what was fixed, the spec added, and test results.

## Input Parsing

Accept any of these formats:
- Full URL: `https://sentry.io/organizations/org/issues/12345/` or `https://org.sentry.io/issues/PROJ-XX/`
- Short ID: `VOTERLETTERS-9R`, `PROJ-123`
- Numeric ID: `12345`
- Natural language: "fix the sentry issue VOTERLETTERS-9R" (extract the ID)
