#!/usr/bin/env python3
"""Find which git repos under a directory have open PRs awaiting the viewer's review.

Usage: discover.py [ROOT] [--depth N] [--include-drafts] [--prs] [--json OUT]

Scans subdirectories of ROOT (default: cwd) for git checkouts (including worktrees),
dedupes them by GitHub remote, and queries each repo's open PRs in parallel.

A PR "needs review" when it is open, not a draft (unless --include-drafts), not authored
by the viewer, the viewer has no submitted review on its current head commit, and no
reviewer's latest review is a CHANGES_REQUESTED on that head commit. The last two rules
mean a PR drops out until the author pushes again: either you already reviewed it, or
someone else asked for changes and the author hasn't responded ("awaiting author").

Prints a one-line-per-repo summary to stdout (--prs adds one line per PR); --json OUT
writes the full per-PR detail.
Read-only: makes only gh GraphQL queries.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

QUERY = """
query($owner:String!, $name:String!) {
  repository(owner:$owner, name:$name) {
    nameWithOwner isArchived viewerPermission
    pullRequests(states:OPEN, first:50, orderBy:{field:UPDATED_AT, direction:DESC}) {
      totalCount
      nodes {
        number title url isDraft createdAt updatedAt baseRefName headRefOid
        reviewDecision mergeable
        author { login }
        reviews(last:30) { nodes { author { login } state submittedAt commit { oid } } }
      }
    }
  }
}
"""

GH_REMOTE = re.compile(r"github\.com[:/]([^/]+)/([^/\s]+?)(?:\.git)?/?$")


def sh(*args, cwd=None):
    r = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def find_checkouts(root, depth):
    found = []
    root = os.path.abspath(root)
    for dirpath, dirnames, _ in os.walk(root):
        rel_depth = dirpath[len(root):].count(os.sep)
        if dirpath != root and os.path.exists(os.path.join(dirpath, ".git")):
            found.append(dirpath)
            dirnames[:] = []  # don't descend into a checkout
            continue
        if rel_depth >= depth:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "node_modules"]
    return sorted(found)


def remote_for(path):
    code, out, _ = sh("git", "remote", "get-url", "origin", cwd=path)
    if code != 0 or not out:
        return None
    m = GH_REMOTE.search(out)
    return f"{m.group(1)}/{m.group(2)}" if m else None


def age_days(ts):
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).days


def query_repo(slug, viewer, include_drafts):
    owner, name = slug.split("/", 1)
    code, out, err = sh("gh", "api", "graphql", "-f", f"query={QUERY}",
                        "-F", f"owner={owner}", "-F", f"name={name}")
    if code != 0:
        return {"repo": slug, "error": err.splitlines()[-1] if err else "gh failed"}
    repo = json.loads(out)["data"]["repository"]
    prs = repo["pullRequests"]["nodes"]
    needs, own, drafts, reviewed, awaiting = [], [], [], [], []
    for pr in prs:
        author = (pr["author"] or {}).get("login", "ghost")
        reviewed_head = any(
            (r["author"] or {}).get("login") == viewer
            and r["state"] != "PENDING"
            and (r["commit"] or {}).get("oid") == pr["headRefOid"]
            for r in pr["reviews"]["nodes"]
        )
        latest = {}
        for r in pr["reviews"]["nodes"]:
            login = (r["author"] or {}).get("login")
            if login and r["state"] in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
                latest[login] = r
        blockers = sorted(
            login for login, r in latest.items()
            if r["state"] == "CHANGES_REQUESTED"
            and (r["commit"] or {}).get("oid") == pr["headRefOid"]
        )
        entry = {
            "number": pr["number"], "title": pr["title"], "url": pr["url"],
            "author": author, "age_days": age_days(pr["createdAt"]),
            "idle_days": age_days(pr["updatedAt"]), "base": pr["baseRefName"],
            "review_decision": pr["reviewDecision"], "mergeable": pr["mergeable"],
            "changes_requested_at_head_by": blockers,
        }
        if author == viewer:
            own.append(entry)
        elif pr["isDraft"] and not include_drafts:
            drafts.append(entry)
        elif reviewed_head:
            reviewed.append(entry)
        elif blockers:
            awaiting.append(entry)
        else:
            needs.append(entry)
    return {
        "repo": slug,
        "archived": repo["isArchived"],
        "permission": repo["viewerPermission"],
        "can_merge": repo["viewerPermission"] in ("ADMIN", "MAINTAIN", "WRITE"),
        "open_total": repo["pullRequests"]["totalCount"],
        "needs_review": needs,
        "own": own,
        "drafts": drafts,
        "already_reviewed": reviewed,
        "awaiting_author": awaiting,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--depth", type=int, default=1)
    ap.add_argument("--include-drafts", action="store_true")
    ap.add_argument("--prs", action="store_true", help="list each PR under its repo")
    ap.add_argument("--json", dest="json_out")
    a = ap.parse_args()

    code, viewer, err = sh("gh", "api", "user", "-q", ".login")
    if code != 0:
        sys.exit(f"gh not authenticated: {err}")

    checkouts = find_checkouts(a.root, a.depth)
    by_repo, no_remote = {}, []
    for path in checkouts:
        slug = remote_for(path)
        if slug:
            by_repo.setdefault(slug, []).append(os.path.relpath(path, a.root))
        else:
            no_remote.append(os.path.relpath(path, a.root))

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda s: query_repo(s, viewer, a.include_drafts), by_repo))
    for r in results:
        r["dirs"] = by_repo[r["repo"]]

    results.sort(key=lambda r: (-len(r.get("needs_review", [])), r["repo"].lower()))
    report = {"viewer": viewer, "root": os.path.abspath(a.root),
              "repos": results, "no_github_remote": no_remote}
    if a.json_out:
        with open(a.json_out, "w") as f:
            json.dump(report, f, indent=2)

    print(f"viewer: {viewer}   checkouts: {len(checkouts)}   unique GitHub repos: {len(by_repo)}\n")
    print("NEEDS SWEEP")
    any_need = False
    for r in results:
        if r.get("needs_review"):
            any_need = True
            n = r["needs_review"]
            authors = sorted({p["author"] for p in n})
            flags = []
            if not r["can_merge"]:
                flags.append(f"perm={r['permission']}")
            if r["archived"]:
                flags.append("archived")
            print(f"  {r['repo']:<45} {len(n):>2} PR(s)  oldest {max(p['age_days'] for p in n)}d  "
                  f"{len(authors)} author(s)  dir={r['dirs'][0]}  {' '.join(flags)}")
            for p in (n if a.prs else []):
                print(f"      #{p['number']:<5} {p['title'][:70]}  (@{p['author']}, {p['age_days']}d)")
    if not any_need:
        print("  (none)")
    print("\nNOTHING TO SWEEP")
    for r in results:
        if "error" in r:
            print(f"  {r['repo']:<45} ERROR: {r['error']}")
        elif not r["needs_review"]:
            extra = []
            if r["already_reviewed"]:
                extra.append(f"{len(r['already_reviewed'])} already reviewed at head")
            if r["awaiting_author"]:
                extra.append(f"{len(r['awaiting_author'])} awaiting author")
            if r["own"]:
                extra.append(f"{len(r['own'])} yours")
            if r["drafts"]:
                extra.append(f"{len(r['drafts'])} draft")
            print(f"  {r['repo']:<45} {r['open_total']} open" + (f" ({'; '.join(extra)})" if extra else ""))
    if no_remote:
        print(f"\nNo GitHub remote (skipped): {', '.join(no_remote)}")


if __name__ == "__main__":
    main()
