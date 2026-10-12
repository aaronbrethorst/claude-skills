---
name: pr-meta-sweep
description: >
  Run /pr-sweep across every git repo under the current directory. First work out which
  repos actually have open PRs awaiting the user's review, then show a toggleable checklist
  of those repos so the user can switch each one on or off, then sweep only the selected
  repos. Use this whenever the user wants a PR sweep that spans more than one repo:
  "do a /pr-sweep across subdirectories", "sweep all the repos", "which repos need a PR
  sweep?", "go through open PRs everywhere", "meta-sweep", "clear the PR backlog across
  ~/repos/onebusaway", or any PR-triage request made from a parent folder that holds
  several checkouts rather than from a single repo. For a single repo, use pr-sweep
  directly.
allowed-tools: ["Bash", "Read", "Skill", "Agent", "Task", "AskUserQuestion"]
argument-hint: "[root dir] [merge|review-only] [--include-drafts]"
---

# PR Meta-Sweep

This skill runs `pr-sweep` across many repos. It has three phases: **discover**,
**select**, and **sweep**. Discovery and selection are this skill's job; the sweep
itself follows `pr-sweep` unchanged. The user gets a short list of repos with real
work waiting and chooses which ones to sweep, so nothing is reviewed blind.

## Phase 1: Discover which repos need a sweep

Run the bundled script from the directory the user named (default: cwd):

```bash
python3 <skill-dir>/scripts/discover.py <root> --json <scratchpad>/meta-sweep.json
```

The script is read-only and uses only `gh` GraphQL queries. It:
- finds git checkouts one level down (`--depth 2` goes deeper);
- merges worktrees and duplicate clones that share a GitHub remote;
- queries each repo's open PRs in parallel.

A PR **needs review** when all of these hold:
- it is open;
- it is not a draft (`--include-drafts` overrides this);
- the user didn't author it;
- the user has no submitted review on the PR's current head commit;
- no reviewer's latest review is a change request on the current head commit.

Because of the last two rules, a PR drops out until the author pushes new commits. That
covers PRs the user already reviewed, and PRs where another maintainer asked for changes
that the author hasn't answered yet. Re-reviewing those wastes an agent and posts a
second review over a request that's still open. The user's own PRs, drafts,
already-reviewed PRs, and awaiting-author PRs are counted but not queued.

Summarize the result briefly. The script's stdout already ranks repos by queue size.
Mention repos the script couldn't query, repos with no GitHub remote, and repos where
`perm` is READ. On a READ-only repo the user can comment but cannot approve or merge, so
say so. If no repo needs a sweep, say so and stop. Don't widen the criteria to find work.

## Phase 2: Toggleable repo checklist

Show the repos that need a sweep as a multi-select checklist with `AskUserQuestion`
(`multiSelect: true`). Each checked repo is "on" and each unchecked repo is "off". This
checklist is the main reason the skill exists, so don't skip it, even when there's only
one candidate.

The tool allows at most 4 options per question and 4 questions per call. Pack the
candidates in ranked order into questions of up to 4 options each. That fits 16 repos in
one call. If there are more than 16, make a second call.
- **Question text:** "Sweep which repos? (group 1 of 3)". Use a `header` such as
  `Repos 1-4`.
- **Option label:** the repo's short name, like `maglev` or `onebusaway-android`. Keep it
  under about 30 characters.
- **Option description:** the queue size, the oldest PR's age, and the author count, plus
  any warning. Example: `24 PRs, oldest 213d, 14 authors`. Add warnings as needed:
  `READ-only: can't merge`, `archived`, or `uses maglev-pr-review`.

The tool can't pre-check boxes, so tell the user once, in the same turn: "check the repos
to sweep; leave a group empty to skip all of it." The automatic "Other" field lets them
add a repo, narrow one ("android: only the 8 PRs from this month"), or give a per-repo
instruction. Honor whatever they type there.

After they answer, repeat the final selection in one line: which repos are on, how many
PRs that is, and which repos are off. If the total is above about 15 PRs, `pr-sweep`'s
scope check is already covered, because the user just chose the scope. Don't ask again.

## Phase 3: Sweep the selected repos

Load the `pr-sweep` skill once with the Skill tool and follow it, with these adaptations
for multiple repos:

- **Mode is decided once, for the whole run**, from the user's original words, as
  `pr-sweep` describes. "Sweep" and "go through" mean review-only. "Merge the ready ones"
  means execute. Ticking a repo in the checklist is not consent to merge.
- **The worklist is the discovery output.** Use each selected repo's `needs_review` PRs
  from the JSON file instead of re-running `gh pr list`. That keeps the queue the user
  saw. Every command carries `--repo <owner/repo>`, because the cwd is the parent
  directory, not a checkout.
- **Repo-specific skills take precedence.** If a selected repo has its own review skill,
  use it for that repo's PRs instead of `pr-sweep`'s per-PR agent. For example, use
  `maglev-pr-review` for `OneBusAway/maglev`. Mark this in the checklist description so
  the user knows ahead of time.
- **Fan out across repos, not just within one.** Use `pr-sweep`'s waves of at most 6
  review agents, filled from the combined queue. Interleave repos so one large repo
  doesn't starve the others. Give each agent the local checkout path from `dirs` so it
  can read surrounding code.
- **Start every review agent with `references/review-agent-preamble.md`**, filled in.
  It wraps `pr-sweep`'s per-PR template with two overrides:
  - PRs with new commits since the user's last review get a real re-review, instead
    of being skipped as "already commented".
  - An agent that would recommend REQUEST CHANGES must not post "No issues found".

  The second rule matters because the comment goes out under the user's name, and
  contributors read an all-clear as approval. Without the rule, an agent's
  high-confidence-only filter can post "No issues found" on a PR the sweep then
  blocks.
- **Verification and disposition stay per PR**, exactly as in `pr-sweep`.
- **Merging in execute mode: use `scripts/merge-ready.sh`.** Auto mode usually blocks
  Claude's own `gh pr review --approve` and `gh pr merge`. If that happens, don't retry
  and don't look for a workaround; the user runs the script instead. Write:
  - one approval body file per READY PR;
  - a tab-separated queue file with these fields: `owner/repo`, number, the head SHA
    prefix you reviewed, the body file, and an optional new title (for example, when
    the PR title names something the PR removed).

  Order the queue so independent PRs come first and toolchain bumps and large PRs come
  last. Then hand the user one command:
  `! bash <skill-dir>/scripts/merge-ready.sh <queue-file>`.

  Before merging each PR, the script checks:
  - the head is still the commit you reviewed;
  - mergeability has resolved;
  - `gh pr checks` passes;
  - no other reviewer is blocking.

  It retries dropped connections, and it re-checks before retrying a write, so a
  network failure can't double-approve. It's safe to re-run. Afterwards, confirm each
  PR's `state` and `mergedAt` on GitHub rather than trusting the script's summary.

## Report

End with one table grouped by repo that accounts for:
- every PR in every selected repo, with the same disposition values as `pr-sweep`'s
  Step 5;
- one line per deselected repo marking it as skipped by the user;
- every repo that errored or was skipped.

Close with the totals: repos swept, PRs reviewed, merged or ready to merge, changes
requested, and blocked.
