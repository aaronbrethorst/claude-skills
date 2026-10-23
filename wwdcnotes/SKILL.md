---
name: wwdcnotes
description: Search and read community notes on Apple WWDC sessions (2010–present) from wwdcnotes.com, without a local checkout. Starts from the site's llms.txt and its machine-readable indexes to find sessions, then fetches the live note page as Markdown and downloads its images (diagrams, slides, sketchnotes) so you can view them for the full picture. Use when the user asks what a WWDC session covered, which sessions discuss an API or framework (SwiftData, App Intents, visionOS…), wants notes, takeaways, or code from a WWDC talk, asks "what's new in X" across WWDC years, or mentions WWDCNotes or wwdcnotes.com.
compatibility: Requires python3 (stdlib only) and network access to https://wwdcnotes.com.
allowed-tools: Bash Read
argument-hint: "[topic, API, or session]"
---

# WWDCNotes

wwdcnotes.com publishes community notes for WWDC sessions. Its `llms.txt` points to two indexes, and the script uses both:

- `nav-index.json` has the title, summary and URL of each page.
- `search-index.json` has the plain text of each note. Code is flattened and images are missing.

The indexes are good for finding notes. For the actual content, fetch the live page. Many notes carry key information only in images: architecture diagrams, slides, screenshots, and whole sketchnotes.

All commands go through `scripts/wwdcnotes.py`. Always run it as `python3 -I`. It caches the indexes and `llms.txt` in `~/.cache/wwdcnotes` for 24 hours. Pass `--refresh` if the user says a note was just published.

```sh
W="python3 -I ~/.claude/skills/wwdcnotes/scripts/wwdcnotes.py"
```

## Workflow

### 1. Orient (optional)

`$W llms` prints the site's `llms.txt`. Read it once if something seems off, such as an index URL that moved or a new feed. The script finds the index URLs from it automatically.

### 2. Find sessions

```sh
$W search swiftdata                        # every term must match (case-insensitive)
$W search "app intents" --year 24 --year 25
$W search --year 26 --limit 50             # list a year's notes
$W search widgets --include-stubs          # also show sessions nobody has written up
$W search observable --json                # machine-readable results
```

- A quoted argument is matched as one phrase. Separate words must each appear somewhere in the note.
- Titles score highest, then summaries, then the note body. Each hit shows a `match:` snippet from the note text.
- Stubs are hidden by default. About two-thirds of sessions have no notes yet, only a placeholder. For "which sessions cover X", rerun with `--include-stubs` and keep stubs in a separate list, because a stub only tells you the session exists.
- Results are tagged in three ways:
  - `[N chars of notes]` gives a rough idea of depth.
  - `[IMAGE-ONLY]` means the note is a sketchnote or images only. The text index has nothing for it, so go to step 3 and look at the images.
  - `[STUB]` means there are no notes yet.
- Contributor pages and year index pages are excluded unless you pass `--all-pages`.

### 3. Read the full note, including images

```sh
$W page wwdc24-10210-bring-your-apps-core-features-to-users-with-app-intents
$W page https://wwdcnotes.com/documentation/wwdc23-10187-meet-swiftdata/
$W page <slug> --hires       # 2x images, for dense diagrams or small text
$W page <slug> --no-images   # text only, faster
```

The output is Markdown with these parts:
- a header with the title, source URL, Apple video link and length, note authors, and Apple's abstract
- the note body, with headings, lists, links and fenced code blocks with a language
- images inline as `![alt](/Users/…/.cache/wwdcnotes/images/<slug>/file.png)`, already downloaded at the 900px-wide variant
- `## Related sessions` with links
- `## Images` listing the local paths, and `## Videos` listing the remote mp4 URLs, which are not downloaded

**Then look at the images.** Open each image path from the `## Images` list with the Read tool. This is the main reason to fetch the page instead of using the text index:
- A note marked `[IMAGE-ONLY]`, or one whose body is mostly images, can't be answered without them.
- When the alt text is missing, empty, or `None`, which is common, the image is the only source for what it shows.
- If a diagram is hard to read, re-run with `--hires`.
- On a page with many images, read the ones near the sections that matter for the question. You don't need every screenshot.

Don't download the videos unless the user asks. They're short looping animations, and mentioning the URL is usually enough.

### 4. Answer

- Cite each session as **title (WWDCyy #id)** and link to its wwdcnotes.com page, plus the Apple video link when it helps.
- Say clearly when something comes from an image, such as "the session's architecture diagram shows…", and when a session is only a stub.
- When you compare across years ("what's new in SwiftData since 2023"), search each year, then fetch the pages for the sessions that matter.
- Community notes vary in quality and may be out of date for later OS releases. For API details that matter, check them against Apple's documentation.

## Notes

- Slugs look like `wwdc<yy>-<session id>-<kebab-title>`. Year index pages are `/documentation/wwdc24/`.
- Images stay in `~/.cache/wwdcnotes/images/<slug>/` and are reused on later runs. Pass `--out DIR` to put them somewhere else, for example a scratchpad.
- A `page` call that returns HTTP 404 means the slug is wrong. Run `search` again and copy the slug exactly.
