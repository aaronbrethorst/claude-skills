---
name: rocketsim
description: "Use the `rocketsim` CLI on PATH to inspect and interact with iOS Simulator apps via the rs/1 JSON envelope. Read visible accessibility elements as a compact agent snapshot, then tap, activate, long-press, type, swipe, scroll, focus, press hardware buttons, or answer Face ID prompts by ephemeral element id (stable within a single snapshot) with race protection via screen hashes. Use when: (1) the user mentions RocketSim, the rocketsim command, or RocketSim CLI, (2) interacting with an app in the iOS Simulator, (3) navigating or testing a simulator app with AI, (4) reading visible UI state or accessibility elements, (5) tapping, activating, long-pressing, swiping, scrolling, typing, handling Face ID, or pressing simulator buttons, (6) using RocketSim instead of ad-hoc simulator automation."
---

# RocketSim Agent Skill

`rocketsim` is a CLI on `PATH` that talks to the running RocketSim app via the
`rs/1` JSON protocol for reads and interactions. Use it to inspect and interact
with iOS Simulator apps reliably and with low token cost. It does not build,
install, or launch apps from source; use the host IDE or build tooling for that,
then use RocketSim once the app is running in the Simulator.

## Setup

Resolve the CLI once before the first command:

1. Prefer `command -v rocketsim`.
2. If that fails, try common symlink locations:
   `/opt/homebrew/bin/rocketsim`, `/usr/local/bin/rocketsim`, and
   `~/.local/bin/rocketsim`.
3. If those fail, try the bundled app helper:
   `/Applications/RocketSim.app/Contents/Helpers/rocketsim` and
   `~/Applications/RocketSim.app/Contents/Helpers/rocketsim`.
4. If any candidate exists and is executable, use that path for all RocketSim
   commands in this session. The agent shell may have a different `PATH` than
   the user's Terminal.
5. Only after all candidates fail, ask the user to open **RocketSim -> Settings
   -> CLI & Agent** and click **Install Command Line Tool**.

In examples below, `rocketsim` means the resolved CLI command. If setup resolved
an absolute path, substitute that absolute path anywhere an example starts with
`rocketsim`.

If this skill is missing in Xcode's built-in coding assistant, ask the user to
open **RocketSim -> Settings -> CLI & Agent** and install **Agentic Coding in
Xcode**. Xcode uses its own Coding Assistant skill folder, separate from
`~/.claude/skills`; restart Xcode after installing or repairing the skill.

If RocketSim is not installed, link to
<https://apps.apple.com/app/apple-store/id1504940162>.

Do not run `rocketsim doctor` before routine navigation or interaction tasks.
Start with `rocketsim screen` or `rocketsim elements --agent --agent-mode nav`;
those reads prove the usable path with less noise.

Use `rocketsim doctor` only when setup appears broken: the CLI cannot connect to
RocketSim, IPC is unreachable, no simulator can be found, or perception and
interactions fail unexpectedly. It emits a `{checks, summary}` envelope and
exits non-zero on any `fail`.

## The rs/1 Envelope

Most agent-facing `rocketsim` commands write a single `rs/1` JSON envelope to
stdout. Parse it; never read plain text.

```json
{"rs":"1","ok":true,"data":{}}
```

```json
{"rs":"1","ok":false,"error":{
  "code":"snapshot_changed",
  "message":"Screen has moved past the snapshot you targeted.",
  "recovery_suggestion":"Re-run rocketsim elements --agent --agent-mode act and retry with the new id and hash.",
  "context":{"expected_screen":"a1b2c3d4","current_screen":"e5f6a7b8","current_seq":"43"}
}}
```

Branch on `ok`. On failure, switch on `error.code` and follow
`recovery_suggestion`.

Exceptions:

- `rocketsim snapshot` streams raw PNG bytes to stdout. Redirect stdout to a
  file; rs/1 envelope errors are written to stderr.
- `rocketsim screenshot` streams raw PNG bytes to stdout. Redirect stdout to a
  file; rs/1 envelope errors are written to stderr.
- `rocketsim video record` records until `Ctrl+C`, then streams raw MP4 bytes
  to stdout. Redirect stdout to a file; progress and rs/1 envelope errors are
  written to stderr.
- `rocketsim doctor` prints an unwrapped `{checks, summary}` JSON object and
  exits non-zero when any check fails.

## The Agent Loop

Default to a **single-process RocketSim command stream** using the CLI command
resolved during setup (`rocketsim` or an absolute path). Every line you run
should start with that command and stay self-contained: no `|`, no
`$(rocketsim ...)`, no `jq`. Hosts that gate Bash on a per-binary allowlist
(Claude Code, Cursor, Codex CLI, Gemini CLI) can then "Don't ask again" the
`rocketsim` binary once and stop prompting.

1. Pick a target by **selector first** (`--label`, optionally `--type`).
   Resolve by `--id` only when a selector is ambiguous.
2. Use `--screen latest` for the race-window guard. The server resolves the
   sentinel against the current snapshot — you do not need to extract a hash.
3. Batch two or more steps with `rocketsim do --step "..."` so the whole
   sequence runs in one process and one approval prompt.
4. Read the `interact` delta from the response. If it reports `next_screen`,
   `screen_changed`, or useful `appeared` ids, use that result instead of an
   extra `wait` plus another snapshot.
5. Re-snapshot only when the next target is unknown, the delta is insufficient,
   or an error recovery suggestion asks for a fresh read. Write the snapshot
   to a file (`rocketsim elements ... > /tmp/rs-snap.json`) and use your
   host's built-in file-read tool to inspect it instead of a shell pipeline.

Speed rules:

- Use `rocketsim do` for two or more sequential steps. One batched command is
  faster than multiple shell calls and shares one approval prompt.
- Do not add sleeps between commands. Use `wait` only for a real precondition:
  navigation, keyboard visibility, network/auth completion, or a specific
  element appearing.
- For normal UI animations, use short waits such as `--timeout 1` or
  `--timeout 2`. Reserve `--timeout 5` or longer for network, sign-in, or
  install-time work.
- Prefer `--screen latest` and `--from latest` over hash extraction. Use an
  explicit 8-hex screen hash only when you genuinely need to anchor to a
  snapshot you observed earlier (e.g. across an external pause).

Snapshot modes:

| Mode | Use when | Body |
| --- | --- | --- |
| `nav` | Deciding what screen you are on or where to act. | Headings, tabs, nav bars, top-level controls. |
| `act` | About to tap, type, swipe, or scroll a known element. | Interactive elements with id, label, role, frame. |
| `debug` | An action failed or an element looks wrong. | Full tree with parent ids, traits, raw frames. |

Compact `--agent` `nav` and `act` modes return `{mode, rows, screen, ...}`;
`rows[]` are pipe-delimited strings such as `id|role|label` or
`id|role|label|value|state`. Use `--agent-mode debug` or `elements` without
`--agent` when you need structured `elements[]` objects or
`data.scrollables[]`; that JSON snapshot form costs more tokens but includes
scrollable container metadata. The JSON snapshot also carries
`data.canvasSize` ([width, height] in device points) describing the full
screen the frames were laid out in — useful when scaling element frames onto a
rendered screenshot or overlay. Add `--since <hash>` to get an empty body when
the screen hash is unchanged.

Rows prefixed with `!` are metadata, not tap targets:

- `!ambiguous|role|label|...` means multiple visible controls share a label.
  Use ids or visual context instead of guessing.
- `!perception|webview_sparse|...` means web content is visible but sparse in
  Accessibility. Use `rocketsim screenshot` for visual reasoning, then tap
  visible controls by coordinates when no semantic element exists.

`screen.data.app` is optional. Some host builds can return an empty app field
while still providing a useful title, keyboard state, role counts, and
scrollable hints.

## Interactions

Default to a label selector with `--screen latest` so each command is one
self-contained `rocketsim` invocation:

```bash
rocketsim interact tap        --label "Sign In"  --screen latest
rocketsim interact activate   --label "Debug"    --screen latest
rocketsim interact long-press --label "Photo"    --duration 1.5 --screen latest
rocketsim interact long-press --label "Debug"    --touches 2 --duration 1.0 --screen latest
rocketsim interact focus      --label Email      --screen latest
rocketsim interact swipe      --label Carousel   --direction left --screen latest
```

Fall back to an `--id` from a JSON snapshot when a selector is ambiguous (the
`!ambiguous` row tells you when to switch). Ids are resolved against the same
race-window guard:

```bash
rocketsim interact tap        --id 7  --screen latest
rocketsim interact activate   --id 8  --screen latest
rocketsim interact long-press --id 12 --duration 1.5 --screen latest
rocketsim interact long-press --id 12 --touches 2 --duration 1.0 --screen latest
rocketsim interact type "user@example.com" --id 4 --screen latest
rocketsim interact type --stdin            --id 4 --screen latest < message.txt
rocketsim interact type --file ./body.txt  --id 4 --screen latest
rocketsim interact swipe  --id 9 --direction up --screen latest
rocketsim interact scroll --id 9 --direction up --pages 1 --screen latest
rocketsim interact focus  --id 4 --screen latest
```

Raw coordinates and hardware buttons stay simple and need no guard:

```bash
rocketsim interact tap 200 540
rocketsim interact swipe  --from "200,400" --to "200,100"
rocketsim interact button --name home
rocketsim interact button --name lock --duration 1.5
rocketsim interact biometric match
```

`interact type` takes the text as a positional argument, not `--text`.
`interact scroll --id <N>` auto-resolves to the nearest scrollable ancestor
when `<N>` is a child element.
Use `--touches 2` (or `--number-of-touches 2`) with `tap` or `long-press`
when an app requires a two-finger gesture. The default is one touch.
Use `interact activate` when an element exists in Accessibility but is not
hittable by coordinates, such as invisible controls or controls that ignore
hit-testing. It performs an accessibility press (`AXPress`) on the resolved
element instead of sending a HID tap. If you target by selector, RocketSim
presses the first live accessibility element that satisfies all provided
selector fields; prefer `--id` with `--screen` when duplicate labels exist.
Raw coordinate interactions use the simulator screenshot coordinate space:
origin at the top-left, x to the right, y downward. Do not pass `--screen` with
raw coordinate taps; the race guard applies to element ids and selectors, not
pixels.

RocketSim keeps the rs/1 element coordinate contract portrait-normalized even
when the Simulator is portrait upside down. Continue choosing ids and reading
annotated snapshots normally; RocketSim maps element taps, gestures, and badges
to the active simulator orientation before dispatching HID events or drawing the
PNG.

Pass an explicit 8-hex hash (`--screen a3f291bc`) only when you must anchor
to a snapshot you observed earlier — for example, after a long external
pause where the screen may have changed under you. `--screen latest` is the
right default for the next-action case.

Toggles and switches appear as `role=checkBox` with `value="0"` or
`value="1"`. Tap them like any other element; the server verifies the value
flipped and returns an error if it did not.

When a LocalAuthentication Face ID prompt blocks progress, answer it directly:
use `rocketsim interact biometric match` for a successful Face ID scan, or
`rocketsim interact biometric nomatch` when testing the failure path. This is a
simulator biometric event, so it does not take `--screen` and does not require a
target element.

## Network Conditions

Use Network Speed Control when the task explicitly asks you to test offline or
poor-network handling. This feature requires RocketSim Pro and the RocketSim
Network Extension to have been approved once in System Settings.

```bash
rocketsim network set airplane
rocketsim network set 3g
rocketsim network set 100-loss --bundle-id com.example.app
rocketsim network status
rocketsim network off
```

Without `--bundle-id`, RocketSim targets the current recent builds and the
helper daemons needed for Simulator URLSession traffic. If `network set` fails
with `network_extension_not_ready`, ask the user to open RocketSim's Networking
window once and approve the Network Extension; agents cannot approve the macOS
System Settings prompt headlessly. Always turn the condition off when the
offline test is complete.

## Blocking Primitives

```bash
rocketsim wait screen-changed --from latest --timeout 1
rocketsim wait element --label "Done" --timeout 2
rocketsim wait keyboard --state hidden --timeout 1
rocketsim wait element --label "Done" --timeout 1 --poll-interval-ms 50
```

`--from latest` binds to the snapshot the server already has and waits for
the next swap. Use `--from <8-hex>` only when you genuinely need to anchor to
an earlier snapshot you observed.

Use `--poll-interval-ms 50` only when you are actively waiting on a fast UI
animation. Keep the default cadence for longer network/auth waits.

Batch sequential steps with `do`, which re-snapshots and re-validates between
each step. Prefer this whenever you already know the next few actions — one
`do` invocation is one process, one approval prompt, and one round trip:

```bash
rocketsim do \
  --refresh-policy smart \
  --step "interact tap --label 'Sign In' --screen latest" \
  --step "wait element --label Email --timeout 2" \
  --step "interact type 'user@example.com' --label Email --screen latest" \
  --step "interact tap --label Submit --screen latest"
```

Avoid a separate `wait screen-changed --from latest` after every tap. The
`interact` delta already tells you whether the screen changed, and by the
time a wait step runs the snapshot store has already been refreshed past the
tap, so `--from latest` would bind to the new screen and wait for an
*additional* swap. Wait for a concrete postcondition instead — `wait element
--label "..."` for an expected control, `wait keyboard --state hidden` for a
dismissal — or trust the interact delta. Reserve explicit
`wait screen-changed --from <8-hex>` for the case where you observed a
specific snapshot earlier and need to confirm it has moved.
Use `--refresh-policy smart` when a batch mixes interactions with read/wait
steps; it keeps pre-refreshes before interactions but skips redundant refreshes
after an interact delta has already produced a fresh screen.
`--screen latest` and `--from latest` are evaluated *per step* by the server,
so each step in a batch automatically anchors to its own current snapshot. Do
not paste the same explicit 8-hex hash across multiple batched steps.

Annotated screenshot for visual reasoning:

```bash
rocketsim snapshot --agent-mode act > /tmp/state.png
rocketsim snapshot --agent-mode act --label "Photo" --scale 2 --screen latest > /tmp/zoom.png
rocketsim snapshot --agent-mode act --type button --scale 2 --screen latest > /tmp/buttons.png
rocketsim snapshot --agent-mode act --ids "23,24,25,26,27,28" --scale 2 > /tmp/grid.png
rocketsim snapshot --agent-mode act --crop "120,240,300,300" --scale 2 > /tmp/zoom.png
```

Plain screenshot fallback for sparse accessibility trees such as web views:

```bash
rocketsim screenshot > /tmp/state.png
rocketsim screenshot --background transparent --bezel simulator > /tmp/framed.png
rocketsim video record --fps 60 --touches --bezel device > /tmp/recording.mp4
rocketsim screenshot --show-floating-thumbnail
rocketsim video record --show-floating-thumbnail
```

Use `snapshot` when numbered accessibility badges help connect pixels to ids.
Use `screenshot` when you only need the simulator framebuffer. For sparse
webviews, prefer the plain screenshot: annotated snapshots can show only native
chrome and a large empty web area because badges follow Accessibility richness,
not DOM content.
Use `video record` when you need motion or touch timing; stop it with `Ctrl+C`
and keep stdout redirected so binary MP4 bytes do not print in the terminal.
Pass `--show-floating-thumbnail` when the user wants RocketSim to keep the
capture in its floating thumbnail UI instead of writing binary media to stdout.

For visual target-finding, **lead with the selector**: pass `--label`
(optionally narrowed by `--type`/`--value`) so the server resolves the
matching elements server-side, unions their frames, adds a small context
margin (default 16 px, tunable via `--padding N`), clamps to image bounds,
crops, and only draws badges for those elements. One PNG, no shell loop, no
prior `elements --agent` round-trip:

```bash
rocketsim snapshot --label "Photo" --scale 2 --screen latest > /tmp/zoom.png
rocketsim snapshot --type button --scale 2 --screen latest > /tmp/buttons.png
```

`--screen latest` resolves against the snapshot store, which is seeded by
any earlier `rocketsim screen`, `elements --agent`, `interact`, or `wait`
call in the session. In a fresh session where nothing has touched the store
yet, `--screen latest` fails with `invalid_argument` / `reason: no_snapshot`
— either issue a one-shot `rocketsim screen` first to seed the store, or
omit `--screen latest` from the very first call (you lose the race-window
guard but the snapshot itself still captures cleanly):

```bash
rocketsim screen >/dev/null   # seed the snapshot store on cold start
rocketsim snapshot --label "Photo" --scale 2 --screen latest > /tmp/zoom.png
```

Selector resolution uses the same matcher as `interact tap --label`
(case-insensitive equals or contains for `--label`/`--value`;
case-insensitive *equals only* for `--type`, so `--type button` won't
match `multiButton`/`buttonGroup`) and binds to the snapshot the PNG was
captured from when paired with `--screen latest`. Multi-match selectors
behave like `--ids "<id1>,<id2>,…"`: every match contributes to the union
bbox.

Fall back to `--ids "23,24,…"` only when a selector is genuinely ambiguous
and you have already inspected `elements --agent --agent-mode act` to pick
the right ids:

```bash
rocketsim elements --agent --agent-mode act > /tmp/rs-snap.json
# Inspect the file to find the candidate id range, then substitute the real
# ids — the values below are illustrative and will fail with
# `element_not_found` if they don't match your snapshot:
rocketsim snapshot --ids "23,24,25,26,27,28" --scale 2 --screen latest > /tmp/grid.png
```

`--label`/`--type`/`--value`, `--ids`, and `--crop` are mutually exclusive —
all three specify a crop rectangle from different inputs, so the server
rejects any combination with `invalid_argument` / `reason: mutually_exclusive`.
Reach for `--crop x,y,w,h` only when reasoning about pixel regions that have
no AX representation (sparse webview content, native canvas drawings, etc.).

A few `--ids` shape rules worth remembering before you write the command:

- **Off-screen ids** (e.g. scrolled-out content still in the AX tree with a
  negative y-origin) are rejected with `invalid_argument` and
  `reason: ids_offscreen`. Scroll the target into view, re-snapshot, and
  retry. Mixed visible/off-screen ids succeed — you get a crop covering the
  visible portion with badges only for the on-screen ids; treat a missing
  badge as a signal to scroll.
- **Zero-area ids** (decorative containers, collapsed rows whose
  width or height is `0`) are rejected with `invalid_argument` and
  `reason: ids_zero_area`. Scrolling won't fix this — pick a different
  id from the same `elements --agent` read that points to a real
  visual target.
- `--padding` near image edges is silently clamped to image bounds, so a
  request for `--padding 64` against an element flush with the status bar
  may produce less padding on that side than asked. The clamp never produces
  an error, just a smaller margin.

## Settings And System Apps

iOS Settings labels and page hierarchy can vary by iOS version. Navigate from a
fresh `screen` or `elements --agent --agent-mode nav` read instead of hard-coding
paths. Also keep host diagnostics separate from simulated Settings: a
`doctor` Accessibility warning is about macOS permissions for RocketSim or its
host process, not an iOS Settings page to visit inside the simulator.

## Error Taxonomy

| Code | When | Do |
| --- | --- | --- |
| `snapshot_changed` | `--screen` is older than the previous snapshot. | Re-snapshot; retry with the new id and hash. |
| `element_not_found` | No element matches the id or selector. | Re-snapshot and target a current id. |
| `multiple_matches` | A label or selector matched more than one element. | Use `--id` instead, or refine the selector. |
| `keyboard_obscures_target` | The software keyboard covers the target frame. | Dismiss the keyboard or scroll the target into view. |
| `wait_timeout` | A wait did not resolve within `--timeout`. | Increase the timeout or reconsider the precondition. |
| `invalid_argument` | A flag combination or value is rejected client-side. | Read `error.message`; fix the flags and retry. |
| `pro_required` | Network Speed Control was requested without RocketSim Pro. | Tell the user the feature requires RocketSim Pro. |
| `network_extension_not_ready` | The Network Extension is not approved, installed, or running. | Ask the user to open RocketSim's Networking window and approve the extension. |
| `duration_not_supported` | The action does not accept the supplied `--duration`. | Drop `--duration`, or use the action that supports holds. |
| `internal_error` | Server-side bug or unexpected state. | Retry once; otherwise surface to the user with `message`. |

## End-to-End Example

Default flow — single batched call, label selectors, `--screen latest` for the
race-window guard, concrete element waits for postconditions, no shell
pipelines:

```bash
rocketsim do \
  --refresh-policy smart \
  --step "interact tap --label 'Sign In' --screen latest" \
  --step "wait element --label Email --timeout 2" \
  --step "interact type 'user@example.com' --label Email --screen latest" \
  --step "interact tap --label Submit --screen latest"
```

When you need to inspect the snapshot before deciding (e.g. labels are
ambiguous and you want to pick an id), write the JSON to a file and read it
with your host's built-in file-read tool — no `jq`, no command substitution:

```bash
rocketsim elements --agent --agent-mode act > /tmp/rs-snap.json
# Use your host's file-read tool on /tmp/rs-snap.json to find the id you
# want, then continue with `rocketsim interact ... --id <N> --screen latest`.
```

Both styles keep every command line as a single `rocketsim` invocation, so a
host that prompts for Bash approval only has to see and approve `rocketsim`
once.

## Reference

Canonical long-form `rs/1` protocol reference:
<https://www.rocketsim.app/docs/features/agentic-development/>.
