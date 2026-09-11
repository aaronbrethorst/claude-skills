# Merge mechanics and gh gotchas

Practical details for Step 3 (disposition). These are the things that bite in real
sweeps — read before merging anything. Every command that acts on a PR carries
`--repo <owner/repo>` so a sweep of a repo other than the cwd can't act on the wrong one.

## The CI gate — mandatory before every merge

`mergeable`/`mergeStateStatus` do NOT tell you whether CI passed. A PR with failing
non-required checks reports `MERGEABLE`/`UNSTABLE` and `gh pr merge` will happily merge
it (GitHub only hard-blocks failing *required* checks, and many repos require none).
So gate on the checks themselves:

```bash
gh pr checks <n> --repo <owner/repo>
# exit 0 = all passing → OK to merge
# exit 8 = checks still pending → wait or mark BLOCKED; do not merge
# other nonzero = failing checks → BLOCKED; do not merge, report which ones
```

A failing check is a BLOCKED disposition, not a request-changes — don't penalize a
contributor for a flaky or unrelated check; report what's red and move on.

## Reading the merge state

```bash
gh pr view <n> --repo <owner/repo> --json mergeable,mergeStateStatus,reviewDecision,isDraft
```

The `mergeStateStatus` values you'll actually see:

- `CLEAN` — mergeable, nothing in the way.
- `UNSTABLE` — mergeable but commit status is not passing. The dangerous one: the merge
  will succeed. Run the CI gate; almost always this is BLOCKED.
- `BLOCKED` — something is blocking: a changes-requested review, required checks,
  CODEOWNERS, or other ruleset requirements. Diagnose which (see below).
- `DIRTY` — merge conflicts (`mergeable: CONFLICTING`). Do not merge; ask for a rebase.
- `BEHIND` — head is out of date with base (matters under strict protection); needs an
  update/rebase before merging.
- `UNKNOWN` — GitHub hasn't computed mergeability yet. Common on the *first* query of a
  PR or after any base-branch change, not just after a merge; querying triggers the
  computation, so re-query a moment later rather than trusting it.

### Diagnosing BLOCKED

`BLOCKED` + `reviewDecision: CHANGES_REQUESTED` may be **your own** earlier
"changes requested" review — but confirm whose it is before acting:

```bash
gh pr view <n> --repo <owner/repo> --json reviews \
  -q '[.reviews[] | {author: .author.login, state}] | .[-6:]'
```

- If the change request is **yours** and the concern is addressed, a fresh `--approve`
  supersedes it (a reviewer's latest review replaces their prior state) and unblocks.
- If it's **someone else's**, your approval does not dismiss it — and merging over
  another reviewer's standing objection is not yours to do in a sweep. Mark the PR
  BLOCKED and note who is waiting on what.
- If approval doesn't clear BLOCKED, the cause is checks/CODEOWNERS/rulesets — run
  `gh pr checks` and check the repo's rulesets rather than forcing.

## Base branch sanity

Compare each PR's `baseRefName` (fetched in Step 0) against the repo's default branch.
A PR targeting a stale or wrong base (e.g. `main` in a develop-based repo) will merge
"successfully" into a branch nobody ships from. Flag it for retargeting
(`gh pr edit <n> --repo <owner/repo> --base <default>`) — with the author or user's
confirmation — instead of merging.

## Pick the merge method from the repo, not habit

```bash
gh repo view <owner/repo> --json mergeCommitAllowed,squashMergeAllowed,rebaseMergeAllowed
gh pr list --repo <owner/repo> --state merged --limit 5   # what does history show?
```

"Merge pull request #NNN" commits → merge commits (`--merge`); single collapsed commits
→ squash (`--squash`). Match the house style; if ambiguous, say which you chose in the
final summary so the user can correct it.

## Merge order matters within a sweep

PRs touching overlapping files conflict with each other once the first lands. Merge
smallest and most independent first, overlapping features last, and re-run the state
read + CI gate before each merge — never merge from a stale earlier query. Expect a
still-open feature PR that shared files to flip `DIRTY` after siblings land. That's a
rebase cost, not a defect: leave its approval standing and post:

> Approved on the merits. Heads up: now that sibling PRs (#X, #Y) landed on `<base>`
> and touched the same files, this branch has merge conflicts. Please merge/rebase
> `<base>` in and resolve; once it's mergeable it's good to go — no re-review needed
> unless the resolution changes behavior.

(`<base>` is the PR's actual `baseRefName` — don't assume a branch name.)

## Own PRs

`gh pr review --approve` and `--request-changes` fail on your own PRs ("Can not approve
your own pull request"), but `gh pr merge` succeeds — which is how a sweep accidentally
self-merges with no review on record. Step 0 partitions these out; report them with a
recommendation and touch them only on the user's explicit instruction.

## Per-PR merge sequence

For each READY PR, in order — no unconditional batch merging:

```bash
gh pr view $pr --repo <owner/repo> --json mergeable,mergeStateStatus -q '.mergeable+"/"+.mergeStateStatus'
gh pr checks $pr --repo <owner/repo>           # gate: only proceed on exit 0
gh pr merge $pr --repo <owner/repo> --merge    # or --squash, per house style
```

Then confirm outcomes for the whole batch (don't trust empty-output-means-success):

```bash
for pr in <list>; do
  gh pr view $pr --repo <owner/repo> --json state,mergedAt \
    -q '"#'$pr': "+.state+" merged="+(.mergedAt // "no")'
done
```

## Writing review bodies

Use `--body-file` with a temp file for `gh pr review` / `gh pr comment` bodies — inline
single-quoted bodies break on apostrophes, and real review prose always has them.

## Branch cleanup

Leave merged branches in place unless the user asks — `--delete-branch` is beyond what
a "review and merge" request covers.
