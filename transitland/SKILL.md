---
name: "transitland"
description: "Find transit agencies and describe the GTFS, GTFS-Realtime and GBFS feeds they publish (URLs, realtime message types, whether a key is needed, license, schedule currency) using the Transitland v2 API. Also raw REST/GraphQL queries for operators, feeds, routes, stops and departures."
---

# Transitland API

Use when the user asks which transit agencies exist somewhere, what GTFS / GTFS-RT / GBFS feeds an agency publishes, feed URLs, licenses, whether realtime needs a key, or routes/stops/departures, and Transitland is the source.

## Access
- API key comes from the `TRANSITLAND_API_KEY` environment variable, sent as the `apikey` **header**. Never put the key in a URL, a file, the chat, or a command line. If the variable is missing, ask the user to set it in their shell; don't ask them to paste it.
- REST: `GET https://transit.land/api/v2/rest/...`. The free tier allows about 10,000 requests a month at a low rate; the script pauses 0.5s between calls and backs off on 429.
- GraphQL: `POST https://transit.land/api/v2/query` with `{"query","variables"}`. **Paid plans only**, so use REST first. Schema: `schema/graphql/schema.graphqls` in github.com/interline-io/transitland-lib.
- Some sandboxes block transit.land at the network level (proxy 403). If so, don't work around it: give the user the exact `tl.py` command to run on their machine, then work from the output they send back.

## The script: `scripts/tl.py`
Stdlib-only Python 3.9+. Run it from this skill's directory (`python3 <skill dir>/scripts/tl.py ...`). Every command takes `--format json|jsonl|csv|table` (default json) and `--out FILE`. Use `table` to show the user a quick overview, json when you need to reason about the details, csv for spreadsheets.

### `agencies`: find operators and describe their feeds
Pick one way to choose operators:
- `agencies "king county metro"`: full-text search on name.
- `--state US-WA` (or `--state Washington`), `--country US`, `--city Seattle`, `--near 47.61,-122.33 [--radius 20000]` (meters, default 10000), `--bbox minlon,minlat,maxlon,maxlat`. These can be combined with a search term.
- `--id o-9zv-metrotransit [...]`: specific operators. `--feed f-...`: operators attached to a feed.
- `--names names.txt` (one agency name per line): returns the best match per name with `input_name` and `match_score`. With a geographic filter it matches within that set (one listing, best for a whole state). Without one it searches each name separately (one request per name).

Narrow with `--has gtfs-rt` (any of `gtfs gtfs-rt gbfs`, all must be present), `--redistribution yes|no|unknown|exclude_no`, `--limit N`.

Each operator comes back as:
- `onestop_id`, `name`, `short_name`, `website`, `places` (city, state, country), `modes` (bus, tram, rail, ferry...), `gtfs_agencies` (`agency_id`, `agency_name`), `tags` (`us_ntd_id`, `wikidata_id`), `transitland_url`.
- `summary`: `static_gtfs`, `gtfs_rt`, `gbfs` (booleans), `gtfs_rt_types`, `gtfs_rt_access`, `gtfs_service_end` (latest service date across static feeds).
- `feeds.gtfs` / `feeds["gtfs-rt"]` / `feeds.gbfs`: one entry per feed, as described under `feed` below.

Per-feed details cost one request per feed (cached for the run). `--brief` skips them and returns only names, IDs and feed lists. Use it for big areas, then run `feed` on the ones that matter.

### `feeds`: search feeds directly
`feeds --spec gbfs --near 45.52,-122.68 --radius 10000`, or `feeds caltrain --spec gtfs`. Same geographic and `--redistribution` filters. **Use this for GBFS** (bike and scooter share): those systems are usually their own operators or not attached to one, so `agencies` for a city's transit agency often shows `gbfs: false` even when the city has bike share.

### `feed ONESTOP_ID [...]`
Normalized detail per feed: `spec`; `url` (static GTFS zip or GBFS auto-discovery) or `realtime_types` and `urls` (TripUpdates, VehiclePositions, Alerts); `access` (`open`, `key_required`, `unknown`) with `auth` (`type`, `param_name`, `info_url`); `license` (only fields Transitland has); for GTFS, `latest_version` (`fetched_at`, `sha1`, `service_start`, `service_end`) and `service_status` (`current`/`expired`).

### Raw access
- `rest PATH [key=value ...] [--all]`, e.g. `rest routes operator_onestop_id=o-9zv-metrotransit --all`, `rest stops/<stop_key>/departures`, `rest feeds/<id>/download_latest_rt/trip_updates.json`.
- `graphql QUERY_OR_FILE [--vars JSON]` (paid plans).
- Other REST endpoints: `/agencies`, `/routes`, `/stops`, `/stops/{stop_key}/departures`, `/trips`. Lists come back as `{"<collection>": [...], "meta": {"after": N}}`; `--all` follows `after`.

## Interpreting the results
- **Does the agency publish GTFS-RT?** `summary.gtfs_rt`. `gtfs_rt_types` says which messages; OBA needs TripUpdates or VehiclePositions, so Alerts-only isn't enough.
- **Is it public?** `access: open` means no key. `key_required` means public but you register for a key; `auth.info_url` says where, `auth.type` says how it's sent (`header`, `query_param`, `basic_auth`, `path_segment`, `replace_url`).
- **Can we rehost it** (e.g. OneBusAway/OBACloud)? `license.redistribution_allowed` (`yes`/`no`; missing means unknown). Check `commercial_use_allowed` too.
- **Is the schedule current?** `service_status: expired` or a `gtfs_service_end` in the past means the last fetched GTFS has no future service. Check the agency's site before relying on it.
- **Not in Transitland ≠ none.** If there's no RT feed, report "not in Transitland" and suggest checking the agency's site or vendor (Swiftly, TripShot, Passio, DoubleMap, ETA, Clever).
- Contracted intercity lines and small human-service providers often aren't listed as their own operator. Regional aggregate feeds can list the same agency twice; compare `gtfs_agencies`.
- With `--names`, review every `match_score` under 0.8 by hand and fix mismatches with `agencies "<name>"` or `--id`.

## Workflow: enrich an agency list
1. Put agency names one per line in `names.txt`.
2. `python3 scripts/tl.py agencies --state US-WA --names names.txt --format csv --out feeds.csv`
3. Review low `match_score` rows; re-run individual names with `agencies "<name>" --format table`.
4. Merge the columns into the user's spreadsheet.
