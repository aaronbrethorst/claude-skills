#!/usr/bin/env bash
# Gated, idempotent approve + merge for PRs a sweep marked READY.
#
# Usage: merge-ready.sh QUEUE_FILE
#
# QUEUE_FILE has one PR per line, fields separated by tabs; lines starting with # are skipped:
#   owner/repo  number  reviewed-head-sha-prefix  approval-body-file  [new-title]
# Relative body-file paths resolve against the queue file's directory. List PRs in merge
# order: independent ones first, then toolchain bumps and large PRs last.
#
# Each PR is merged only if all of these hold:
#   - it is open, and its head still starts with the SHA that was reviewed;
#   - its mergeability has resolved to MERGEABLE (UNKNOWN is polled);
#   - `gh pr checks` exits 0;
#   - no other reviewer's latest review is CHANGES_REQUESTED.
# Then it applies the optional new title, approves (skipped if you already approved the
# current head), and merges with a merge commit.
#
# Transient network errors are retried with backoff. A write that may have landed is
# re-checked before it is retried, so a dropped connection can't produce a second
# approval or a second merge attempt. Safe to re-run: merged PRs are reported, not
# retried.
set -u
QUEUE_FILE="${1:?usage: merge-ready.sh QUEUE_FILE}"
QDIR="$(cd "$(dirname "$QUEUE_FILE")" && pwd)"

transient() { grep -qiE 'EOF|reset by peer|timeout|TLS handshake|connection refused|50[234]|i/o timeout'; }

# gh_read ARGS... : run a read-only gh command, retrying transient failures.
gh_read() {
  local out i
  for i in 1 2 3 4 5; do
    if out=$(gh "$@" 2>&1); then printf '%s' "$out"; return 0; fi
    printf '%s' "$out" | transient || { printf '%s\n' "$out" >&2; return 1; }
    sleep $((i * 3))
  done
  printf '%s\n' "$out" >&2; return 1
}

ME=$(gh_read api user -q .login) || { echo "Cannot reach GitHub (gh api user failed). Nothing was changed." >&2; exit 2; }
[ -n "$ME" ] || { echo "Could not determine the gh user. Nothing was changed." >&2; exit 2; }

approved_head() {  # prints "yes" if $ME's latest APPROVED review is on the current head
  local repo=$1 n=$2 head=$3
  gh_read api "repos/$repo/pulls/$n/reviews" --paginate \
    -q "[.[] | select(.user.login==\"$ME\" and .state==\"APPROVED\" and .commit_id==\"$head\")] | if length>0 then \"yes\" else \"no\" end"
}

RESULTS=()
while IFS=$'\t' read -r repo n want body title; do
  [ -z "${repo:-}" ] && continue
  [[ "$repo" == \#* ]] && continue
  tag="$repo#$n"
  [[ "$body" = /* ]] || body="$QDIR/$body"
  echo "== $tag"

  st=$(gh_read pr view "$n" --repo "$repo" --json state,headRefOid -q '.state+" "+.headRefOid') \
    || { RESULTS+=("$tag ERROR could not read PR (network?); re-run"); continue; }
  state=${st%% *}; head=${st#* }
  if [ "$state" = "MERGED" ]; then RESULTS+=("$tag already merged"); continue; fi
  if [ "$state" != "OPEN" ]; then RESULTS+=("$tag SKIP state=$state"); continue; fi
  if [[ "$head" != "$want"* ]]; then RESULTS+=("$tag SKIP head moved to ${head:0:7} since review"); continue; fi

  ms=UNKNOWN
  for i in 1 2 3 4 5 6; do
    ms=$(gh_read pr view "$n" --repo "$repo" --json mergeable -q .mergeable) || ms=ERROR
    [ "$ms" != "UNKNOWN" ] && break; sleep 5
  done
  if [ "$ms" != "MERGEABLE" ]; then RESULTS+=("$tag SKIP mergeable=$ms"); continue; fi

  # `gh pr checks` exits 8 for pending and 1 for failing; only retry network errors.
  if ! out=$(gh pr checks "$n" --repo "$repo" 2>&1); then
    if printf '%s' "$out" | transient && gh_read pr checks "$n" --repo "$repo" >/dev/null; then :; else
      RESULTS+=("$tag SKIP checks not all passing"); continue; fi
  fi

  others=$(gh_read api "repos/$repo/pulls/$n/reviews" --paginate -q \
    "[.[] | select(.state==\"APPROVED\" or .state==\"CHANGES_REQUESTED\" or .state==\"DISMISSED\")] | group_by(.user.login) | map(last) | map(select(.state==\"CHANGES_REQUESTED\" and .user.login!=\"$ME\") | .user.login) | join(\",\")") \
    || { RESULTS+=("$tag ERROR could not read reviews; re-run"); continue; }
  if [ -n "$others" ]; then RESULTS+=("$tag SKIP changes requested by $others"); continue; fi

  if [ -n "${title:-}" ]; then
    gh_read pr edit "$n" --repo "$repo" --title "$title" >/dev/null || { RESULTS+=("$tag ERROR retitle failed; re-run"); continue; }
  fi

  # Approve once. On failure, check whether it landed before trying again.
  for i in 1 2 3; do
    [ "$(approved_head "$repo" "$n" "$head")" = "yes" ] && break
    gh pr review "$n" --repo "$repo" --approve --body-file "$body" >/dev/null 2>&1 || sleep $((i * 3))
  done
  if [ "$(approved_head "$repo" "$n" "$head")" != "yes" ]; then RESULTS+=("$tag ERROR approve failed; re-run"); continue; fi

  # Merge once. On failure, check whether it merged before trying again.
  merged=no
  for i in 1 2 3; do
    gh pr merge "$n" --repo "$repo" --merge >/dev/null 2>&1 && { merged=yes; break; }
    sleep $((i * 3))
    [ "$(gh_read pr view "$n" --repo "$repo" --json state -q .state)" = "MERGED" ] && { merged=yes; break; }
  done
  if [ "$merged" = yes ]; then RESULTS+=("$tag MERGED"); else RESULTS+=("$tag ERROR merge failed (approved); re-run"); fi
done < "$QUEUE_FILE"

echo; echo "===== summary ====="
printf '%s\n' "${RESULTS[@]}"
