---
name: go
description: End-of-task wrap-up sequence — exercise the change end-to-end, simplify, run a PR review, and open a pull request. Use when the user types /go, says "ship it", "wrap up", "send it", or otherwise signals the implementation is done and ready to ship.
---

# Go

## Overview

The user has finished implementing something and wants it shipped. Run these four steps in order. **Halt on red:** if any step uncovers a problem the user must decide on, stop and report — don't push broken code or skip steps.

Invoking `/go` is the user's authorization to push the branch and open a PR. Don't ask for separate confirmation before the push; do flag anything destructive or unexpected (force-push, branch rename, secrets in diff, etc.) and stop.

## Preflight — Refuse to run on `develop` or `main`

Before doing anything else, run `git rev-parse --abbrev-ref HEAD`. If the current branch is `develop` or `main`, **stop immediately** and report the error. Do not exercise the change, do not run simplify, do not push.

A PR from `main` into `main` is meaningless; the user almost certainly meant to be on a feature branch and forgot to create one. Tell them what branch they're on and let them decide whether to `git checkout -b <name>` or abort.

## Step 1 — Exercise the change end-to-end

Pick the testing surface that matches what was built. Don't substitute a unit test run for actual exercise of the feature.

| What changed | How to exercise it |
|---|---|
| Backend / CLI / library code | Bash: invoke the CLI, hit the endpoint with `curl`, run a script that drives the new code path. |
| Web UI / frontend | Browser via the `example-skills:webapp-testing` skill (Playwright). Boot the dev server, click through the golden path, watch the console. |
| Native desktop app | Computer use: drive the app via screenshots + clicks. |
| Pure refactor with no behavior change | Run the project's test suite **and** spot-check one real entry point — refactors are exactly where silent breakage hides. |

Test the golden path **and** at least one edge case. Watch for regressions in adjacent features the user didn't ask about. If you can't actually exercise the feature in this environment, say so explicitly — don't claim success based on a green test run alone.

If something fails: stop, report what broke, and ask how to proceed. Do not move to step 2.

## Step 2 — Run /simplify

Invoke the `/simplify` skill via the Skill tool. It reviews changed code for reuse, quality, and efficiency, and applies fixes. Let it run to completion and apply its changes.

If simplify edits files, re-run the relevant verification from step 1 against the simplified code — simplification can break things.

## Step 3 — Run /code-review --fix until a round finds no blockers

Run `/code-review --fix` in a loop. Always run at least one round. After each round, count how many of the issues it found and fixed are **merge blockers**. If that count is above zero, run another round. Stop when a round fixes zero blockers.

```
loop {
  blocking_fixed = run_code_review_fix()
  if blocking_fixed == 0: break
}
```

Fixing a blocker changes the code, and the fix itself can add a new bug. That's why the loop runs again until a full round turns up nothing that blocks merge.

**What counts as a blocker:** anything a reasonable code reviewer would refuse to approve the PR over. Examples: correctness bugs, crashes, data loss or corruption, security holes, broken or missing error handling that hides failures, regressions in existing behavior, and tests that fail or don't test what they claim. Style nits, naming, small simplifications, comment fixes, and optional refactors are **not** blockers. Fixing only those doesn't trigger another round.

**Each round:**
1. Invoke `/code-review --fix` via the Skill tool. It reviews the current diff and applies its fixes.
2. Read the findings and sort each one:
   - **Fixed blocker.** Counts toward `blocking_fixed`.
   - **Fixed non-blocker.** Note it. It doesn't count.
   - **Not fixed, judgment call or substantive** (architecture, scope creep, test gaps that need new fixtures). Don't count it. Surface it to the user: list it under Review notes in the PR description. If it looks blocking and the fix isn't clear, stop and ask the user before pushing.
3. If the round edited files, re-run the relevant verification from step 1 against the new code.
4. State the round number and how many blockers it fixed, e.g. "Round 2: fixed 1 blocker (null deref in `parseFeed`), 2 nits."

**Safety cap:** if you hit 5 rounds and the latest round still fixed a blocker, stop. Report to the user what each round fixed and ask how to proceed. A loop that keeps finding blockers usually means the fixes are fighting each other or the change has a deeper design problem.

Do not silently ignore review findings.

## Step 4 — Open the PR

Follow the standard PR workflow from the system prompt:

1. `git status`, `git diff` against the base branch, `git log` of the branch's commits — in parallel.
2. If there are uncommitted changes from steps 1–3, commit them first with a message describing the wrap-up work (e.g. `simplify: tighten X helper after review`).
3. Push the branch (`-u` if it has no upstream).
4. `gh pr create` with a short title (<70 chars) and a HEREDOC body containing:
   - **Summary** — 1–3 bullets on what changed and why, drawn from the *full* commit range, not just the latest commit.
   - **Test plan** — the specific things you exercised in step 1, as a checklist.
   - **Review notes** (optional) — any non-blocking findings from step 3 the reviewer should weigh in on.

Return the PR URL when done.

### Don'ts

- Don't `--force` push unless the user has explicitly asked.
- Don't skip hooks (`--no-verify`).
- Don't commit `.env`, credentials, or large binaries — warn the user if the diff contains them and stop.
- Don't open the PR against `main`/`master` if the repo's default branch is something else (check `gh repo view --json defaultBranchRef`).
