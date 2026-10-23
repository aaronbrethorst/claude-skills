#!/usr/bin/env python3
"""Query wwdcnotes.com via its llms.txt indexes and fetch full notes with images.

Commands:
  llms                      Print the site's llms.txt (the entry point).
  search [TERMS...]         Rank notes using nav-index.json + search-index.json.
  page SLUG_OR_URL          Fetch a live note page as Markdown and download its images.

Stdlib only. Indexes are cached in ~/.cache/wwdcnotes for 24h (--refresh to force).
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

SITE = "https://wwdcnotes.com"
LLMS_URL = SITE + "/llms.txt"
CACHE = os.path.expanduser(os.environ.get("WWDCNOTES_CACHE", "~/.cache/wwdcnotes"))
TTL = 24 * 3600
UA = "wwdcnotes-skill/1.0 (+https://wwdcnotes.com/llms.txt)"
STUB_MARKER = "No Overview Available"


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def cached(name, url, refresh=False):
    path = os.path.join(CACHE, name)
    if not refresh and os.path.exists(path) and time.time() - os.path.getmtime(path) < TTL:
        with open(path, encoding="utf-8") as f:
            return f.read()
    text = fetch(url)
    os.makedirs(CACHE, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return text


def index_urls(refresh=False):
    """Discover the nav and full-text index URLs from llms.txt."""
    llms = cached("llms.txt", LLMS_URL, refresh)
    links = dict(re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", llms))
    nav = next((u for t, u in links.items() if "nav" in t.lower()), SITE + "/assets/nav-index.json")
    full = next((u for t, u in links.items() if "search" in t.lower()), SITE + "/assets/search-index.json")
    return nav, full


def load_indexes(refresh=False):
    nav_url, full_url = index_urls(refresh)
    nav = json.loads(cached("nav-index.json", nav_url, refresh))
    full = json.loads(cached("search-index.json", full_url, refresh))
    text = {e["slug"]: e.get("text", "") for e in full}
    docs = []
    for a in nav["articles"]:
        slug = a["slug"]
        m = re.match(r"wwdc(\d{2})-(\d+)-", slug)
        docs.append({
            "slug": slug,
            "title": html.unescape(a.get("title", "")),
            "summary": html.unescape(a.get("summary", "")),
            "url": urllib.parse.urljoin(SITE, a["url"]),
            "year": 2000 + int(m.group(1)) if m else None,
            "session": m.group(2) if m else None,
            "text": text.get(slug, ""),
        })
    for d in docs:
        d["stub"] = d["session"] is not None and STUB_MARKER in d["text"]
    return docs


QUOTES = str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"'})


def fold(s):
    return s.lower().translate(QUOTES)


def norm_year(y):
    y = re.sub(r"\D", "", y)
    return int(y) if len(y) == 4 else 2000 + int(y)


def snippet(text, terms, width=160):
    low = fold(text)
    hits = [low.find(t) for t in terms if low.find(t) >= 0]
    if not hits:
        return ""
    start = max(0, min(hits) - width // 3)
    s = text[start:start + width].strip()
    return ("…" if start else "") + s + "…"


def cmd_search(args):
    docs = load_indexes(args.refresh)
    terms = [fold(t) for t in args.terms]
    phrase = " ".join(terms)
    years = {norm_year(y) for y in args.year} if args.year else None
    results = []
    for d in docs:
        if not args.all_pages and d["session"] is None:
            continue
        if years and d["year"] not in years:
            continue
        if d["stub"] and not args.include_stubs:
            continue
        title, summary, body = fold(d["title"]), fold(d["summary"]), fold(d["text"])
        if terms and not all(t in title or t in summary or t in body for t in terms):
            continue
        score = 0
        for t in terms:
            score += 10 * (t in title) + 3 * (t in summary) + min(body.count(t), 20)
        if len(terms) > 1:
            score += 25 * (phrase in title) + 8 * (phrase in summary) + 4 * (phrase in body)
        if not d["stub"]:
            score += 1
        results.append((score, d))
    results.sort(key=lambda r: (-r[0], -(r[1]["year"] or 0)))
    total = len(results)
    results = results[: args.limit]
    if args.json:
        out = [{k: d[k] for k in ("slug", "title", "year", "session", "url", "stub", "summary")}
               | {"score": s, "note_chars": len(d["text"])} for s, d in results]
        print(json.dumps({"total": total, "results": out}, indent=2, ensure_ascii=False))
        return
    print(f"{total} match(es){' — showing ' + str(len(results)) if total > len(results) else ''}\n")
    for s, d in results:
        if d["stub"]:
            flag = " [STUB: no notes yet]"
        elif len(d["text"]) < 100:
            flag = " [IMAGE-ONLY: content is in images, run `page`]"
        else:
            flag = f" [{len(d['text'])} chars of notes]"
        print(f"- {d['title']} — WWDC{str(d['year'])[2:] if d['year'] else '?'} #{d['session'] or '-'}{flag}")
        print(f"  slug: {d['slug']}")
        print(f"  {d['url']}")
        if d["summary"]:
            print(f"  {d['summary'][:220]}{'…' if len(d['summary']) > 220 else ''}")
        snip = snippet(d["text"], terms) if terms and not d["stub"] else ""
        if snip:
            print(f"  match: {snip}")
        print()


# --- page -> markdown -------------------------------------------------------

BLOCK = {"p", "div", "section", "figure", "header", "ul", "ol", "blockquote", "table", "tr"}
SKIP = {"script", "style", "svg", "button", "nav", "noscript", "template"}
VOID = {"img", "br", "hr", "source", "meta", "link", "input", "wbr"}


class ArticleParser(HTMLParser):
    """Converts the <article> of a WWDCNotes page into Markdown."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.stack = []          # open tag names inside the article
        self.in_article = False
        self.skip_depth = 0
        self.pre = False
        self.lists = []          # ["ul"|"ol", counter]
        self.link = None
        self.images = []         # (src, alt, srcset)
        self.videos = []
        self.meta = {"title": "", "abstract": "", "watch": None, "authors": [], "related": []}
        self.capture = None      # (key, buffer) for meta fields
        self.related_href = None
        self.mode = None         # None | "body"
        self.empty = False       # page renders the "No notes available yet" placeholder

    def emit(self, s):
        if self.capture is not None:
            self.capture[1].append(s)
        elif self.mode == "body":
            self.out.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag == "article" and "sk-docc-article" in cls:
            self.in_article = True
        if not self.in_article:
            return
        if tag not in VOID:
            self.stack.append((tag, cls))
        if self.skip_depth or tag in SKIP:
            if tag not in VOID:
                self.skip_depth += 1
            return

        if "sk-docc-title" in cls:
            self.capture = ("title", [])
        elif "sk-docc-abstract" in cls:
            self.capture = ("abstract", [])
        elif "sk-docc-watch" in cls:
            self.meta["watch"] = a.get("href")
            self.capture = ("watch_text", [])
        elif "sk-docc-wb-name" in cls:
            self.capture = ("author", [])
        elif "sk-docc-relitem-title" in cls:
            self.capture = ("related", [])
        elif "sk-docc-empty" in cls.split():
            self.empty = True
        elif "sk-article-body" in cls:
            self.mode = "body"
        elif "sk-docc-related" in cls or "sk-docc-writtenby" in cls or "sk-docc-corrections" in cls:
            self.mode = None
        if tag == "a" and "sk-docc-relitem" in cls.split():
            self.related_href = a.get("href")

        if self.mode != "body" or self.capture is not None:
            return
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.emit("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "pre":
            self.pre = True
            self.emit("\n\n```")
            self._pending_lang = True
        elif tag == "code":
            if self.pre and getattr(self, "_pending_lang", False):
                m = re.search(r"language-(\S+)", cls)
                self.emit((m.group(1) if m else "") + "\n")
                self._pending_lang = False
            elif not self.pre:
                self.emit("`")
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
            self.emit("\n")
        elif tag == "li":
            kind = self.lists[-1] if self.lists else ["ul", 0]
            kind[1] += 1
            indent = "  " * (len(self.lists) - 1)
            self.emit(f"\n{indent}{str(kind[1]) + '.' if kind[0] == 'ol' else '-'} ")
        elif tag == "blockquote":
            self.emit("\n\n> ")
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i") and not cls.startswith("fa-"):
            self.emit("_")
        elif tag == "a":
            self.link = urllib.parse.urljoin(SITE, a.get("href", ""))
            self.emit("[")
        elif tag == "br":
            self.emit("  \n")
        elif tag == "hr":
            self.emit("\n\n---\n\n")
        elif tag == "img":
            src = a.get("src", "")
            if "avatar" in cls or "/theme/" in src or not src:
                return
            n = len(self.images)
            self.images.append((urllib.parse.urljoin(SITE, src), a.get("alt", ""), a.get("srcset", "")))
            self.emit(f"\n\n{{{{IMG{n}}}}}\n\n")
        elif tag == "source" and "video" in a.get("type", ""):
            url = urllib.parse.urljoin(SITE, a.get("src", ""))
            self.videos.append(url)
            self.emit(f"\n\n[video: {url}]\n\n")
        elif tag in ("th", "td"):
            self.emit(" | ")
        elif tag == "tr":
            self.emit("\n")
        elif tag == "p" and self._in_li():
            self.emit(" ")
        elif tag in BLOCK:
            self.emit("\n\n")

    def handle_endtag(self, tag):
        if not self.in_article:
            return
        if tag == "article":
            self.in_article = False
            return
        if not self.stack:
            return
        open_tag, cls = self.stack.pop()
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if self.capture is not None:
            ends = {"title": "sk-docc-title", "abstract": "sk-docc-abstract", "watch_text": "sk-docc-watch",
                    "author": "sk-docc-wb-name", "related": "sk-docc-relitem-title"}[self.capture[0]]
            if ends in cls:
                key, buf = self.capture
                text = re.sub(r"\s+", " ", "".join(buf)).strip()
                self.capture = None
                if key == "author":
                    self.meta["authors"].append(text)
                elif key == "related":
                    self.meta["related"].append((text, urllib.parse.urljoin(SITE, self.related_href or "")))
                else:
                    self.meta[key] = text
            return
        if self.mode != "body":
            return
        if "sk-article-body" in cls:
            self.mode = None
            return
        if open_tag == "pre":
            self.pre = False
            self.emit("\n```\n\n")
        elif open_tag == "code" and not self.pre:
            self.emit("`")
        elif open_tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
            self.emit("\n")
        elif open_tag in ("strong", "b"):
            self.emit("**")
        elif open_tag in ("em", "i") and not cls.startswith("fa-"):
            self.emit("_")
        elif open_tag == "a" and self.link is not None:
            self.emit(f"]({self.link})")
            self.link = None
        elif open_tag == "p" and self._in_li():
            pass
        elif open_tag in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "blockquote", "figure"):
            self.emit("\n\n")

    def _in_li(self):
        # stack[-1] is the <p> itself on start, its parent on end
        for tag, _ in reversed(self.stack[:-1] if self.stack and self.stack[-1][0] == "p" else self.stack):
            if tag == "li":
                return True
            if tag in ("div", "section", "blockquote", "article"):
                return False
        return False

    def handle_data(self, data):
        if not self.in_article or self.skip_depth:
            return
        if self.pre:
            self.emit(data)
        else:
            self.emit(re.sub(r"\s+", " ", data))


def best_src(src, srcset, hires):
    if hires and srcset:
        cands = [c.strip().split() for c in srcset.split(",") if c.strip()]
        if cands:
            return urllib.parse.urljoin(SITE, cands[-1][0])
    return src


def resolve_slug(arg):
    if arg.startswith("http"):
        path = urllib.parse.urlparse(arg).path
    elif arg.startswith("/"):
        path = arg
    else:
        path = f"/documentation/{arg.strip('/').lower()}/"
    if not path.endswith("/"):
        path += "/"
    slug = path.rstrip("/").split("/")[-1]
    return slug, urllib.parse.urljoin(SITE, path)


def cmd_page(args):
    slug, url = resolve_slug(args.target)
    try:
        page = fetch(url)
    except Exception as e:
        sys.exit(f"error: could not fetch {url}: {e}\nTip: run `search` first to get a valid slug.")
    p = ArticleParser()
    p.feed(page)
    body = "".join(p.out)

    img_dir = os.path.abspath(os.path.expanduser(args.out or os.path.join(CACHE, "images", slug)))
    lines = []
    for n, (src, alt, srcset) in enumerate(p.images):
        remote = best_src(src, srcset, args.hires)
        ref = f"![{alt}]({remote})"
        if not args.no_images:
            os.makedirs(img_dir, exist_ok=True)
            local = os.path.join(img_dir, os.path.basename(urllib.parse.urlparse(remote).path))
            try:
                if not os.path.exists(local):
                    with open(local, "wb") as f:
                        f.write(fetch(remote, binary=True))
                ref = f"![{alt}]({local})"
                lines.append(local)
            except Exception as e:
                ref += f" <!-- download failed: {e} -->"
        body = body.replace(f"{{{{IMG{n}}}}}", ref)

    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"^(\s*(?:-|\d+\.)) +", r"\1 ", body, flags=re.M)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    m = p.meta
    head = [f"# {m['title'] or slug}", "", f"Source: {url}"]
    if m["watch"]:
        length = m.get("watch_text", "").replace("Watch Video", "").strip(" ()")
        head.append(f"Video: {m['watch']}" + (f" ({length})" if length else ""))
    if m["authors"]:
        head.append("Written by: " + ", ".join(m["authors"]))
    if m["abstract"]:
        head += ["", f"> {m['abstract']}"]
    if p.empty or STUB_MARKER in body:
        head += ["", "**Note: this page is a stub — nobody has written notes for this session yet.**"]
    out = "\n".join(head) + "\n\n" + body + "\n"
    if m["related"]:
        out += "\n## Related sessions\n\n" + "".join(f"- [{t}]({u})\n" for t, u in m["related"])
    if p.images:
        out += f"\n## Images ({len(p.images)})\n\n"
        if args.no_images:
            out += "Not downloaded (--no-images). Image URLs are inline above.\n"
        else:
            out += f"Downloaded to {img_dir}\n" + "".join(f"- {l}\n" for l in lines)
    if p.videos:
        out += f"\n## Videos ({len(p.videos)}, not downloaded)\n\n" + "".join(f"- {v}\n" for v in p.videos)
    print(out)


def cmd_llms(args):
    print(cached("llms.txt", LLMS_URL, args.refresh))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--refresh", action="store_true", help="ignore the 24h cache and refetch")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("llms", parents=[common], help="print llms.txt")

    s = sub.add_parser("search", parents=[common], help="search notes")
    s.add_argument("terms", nargs="*", help="all terms must match (case-insensitive)")
    s.add_argument("--year", action="append", help="24, 2024 or wwdc24; repeatable")
    s.add_argument("--limit", type=int, default=15)
    s.add_argument("--include-stubs", action="store_true", help="include sessions with no notes yet")
    s.add_argument("--all-pages", action="store_true", help="include contributor and year index pages")
    s.add_argument("--json", action="store_true")

    p = sub.add_parser("page", parents=[common], help="fetch one note as Markdown and download its images")
    p.add_argument("target", help="slug (wwdc24-10210-...), /documentation/... path, or full URL")
    p.add_argument("--no-images", action="store_true", help="don't download images")
    p.add_argument("--hires", action="store_true", help="download the largest (2x) image variant")
    p.add_argument("--out", help="image directory (default: ~/.cache/wwdcnotes/images/<slug>)")

    args = ap.parse_args()
    {"llms": cmd_llms, "search": cmd_search, "page": cmd_page}[args.cmd](args)


if __name__ == "__main__":
    main()
