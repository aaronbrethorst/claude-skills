#!/usr/bin/env python3
"""Transitland v2 API client (stdlib only).

API key: read from the TRANSITLAND_API_KEY environment variable and sent as
the `apikey` HTTP header (never put it in a URL or on the command line).

Subcommands
  agencies [SEARCH] [filters] [--names FILE] [--format json|jsonl|csv|table]
      Find transit operators and describe the GTFS, GTFS-RT and GBFS feeds each
      one publishes: URLs, realtime message types, whether a key is needed,
      license, and how current the schedule is.
  feeds [SEARCH] [--spec gtfs|gtfs-rt|gbfs] [filters] [--format ...]
      Search feeds directly. Use this for GBFS (bike/scooter share), which is
      usually not attached to a transit operator.
  feed ONESTOP_ID [...]        Normalized detail for specific feeds.
  rest PATH [key=value ...] [--all]   Raw GET https://transit.land/api/v2/rest/PATH
  graphql QUERY_OR_FILE [--vars JSON]  Raw POST https://transit.land/api/v2/query (paid plans only)

Examples
  tl.py agencies "king county metro"
  tl.py agencies --state US-WA --has gtfs-rt --format table
  tl.py agencies --near 47.61,-122.33 --radius 20000
  tl.py agencies --state US-WA --names names.txt --format csv --out feeds.csv
  tl.py agencies --names names.txt          # no geo filter: searches each name
  tl.py feeds --spec gbfs --near 45.52,-122.68 --radius 10000
  tl.py feed f-twin~cities~minnesota~rt

Each operator's feed details cost one request per feed (cached within a run).
Pass --brief to skip them when you only need names, IDs and feed lists.
"""
import argparse, csv, datetime, difflib, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

BASE = "https://transit.land/api/v2"
UA = "transitland-skill/2.0"
PAUSE = 0.5  # free tier rate limit is low; seconds between requests

RT_URL_KEYS = (("realtime_trip_updates", "TripUpdates"),
               ("realtime_vehicle_positions", "VehiclePositions"),
               ("realtime_alerts", "Alerts"))
ROUTE_TYPES = {0: "tram", 1: "subway", 2: "rail", 3: "bus", 4: "ferry", 5: "cable_tram",
               6: "aerial_lift", 7: "funicular", 11: "trolleybus", 12: "monorail"}


# ---------------------------------------------------------------- HTTP

def key():
    k = os.environ.get("TRANSITLAND_API_KEY", "").strip()
    if not k:
        sys.exit("Set TRANSITLAND_API_KEY in the environment first.")
    return k


_last_request = 0.0


def _req(url, data=None, tries=5):
    global _last_request
    headers = {"apikey": key(), "User-Agent": UA, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for i in range(tries):
        wait = PAUSE - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        try:
            r = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(r, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < tries - 1:
                time.sleep(2 ** i * 2)
                continue
            body = e.read().decode("utf-8", "replace")[:500]
            hint = " (proxy or sandbox may be blocking transit.land)" if e.code == 403 and "transit" not in body.lower() else ""
            raise SystemExit(f"HTTP {e.code} for {url.split('?')[0]}{hint}: {body}")
        except urllib.error.URLError as e:
            if i < tries - 1:
                time.sleep(2 ** i)
                continue
            raise SystemExit(f"Network error for {url.split('?')[0]}: {e.reason}")


def rest(path, params=None, all_pages=False, max_items=None):
    params = {k: v for k, v in (params or {}).items() if v not in (None, "")}
    url = f"{BASE}/rest/{path.lstrip('/')}"
    out, listkey = None, None
    while True:
        q = urllib.parse.urlencode(params)
        page = _req(url + ("?" + q if q else ""))
        if not all_pages:
            return page
        if out is None:
            out = page
            listkey = next((k for k, v in page.items() if isinstance(v, list)), None)
            if listkey is None:
                return out
        else:
            out[listkey].extend(page.get(listkey, []))
        after = (page.get("meta") or {}).get("after")
        done = max_items is not None and len(out[listkey]) >= max_items
        if done or not after or not page.get(listkey):
            out.pop("meta", None)
            if max_items is not None:
                del out[listkey][max_items:]
            return out
        params["after"] = after


def graphql(query, variables=None):
    data = json.dumps({"query": query, "variables": variables or {}}).encode()
    res = _req(f"{BASE}/query", data=data)
    if res.get("errors"):
        raise SystemExit("GraphQL errors: " + json.dumps(res["errors"])[:1000])
    return res["data"]


# ---------------------------------------------------------------- normalizing

def spec_of(f):
    s = (f.get("spec") or "").lower().replace("_", "-")
    return s if s in ("gtfs", "gtfs-rt", "gbfs") else (s or "other")


def compact(d):
    """Drop empty values so output only shows what Transitland actually has."""
    return {k: v for k, v in (d or {}).items() if v not in (None, "", [], {})}


_feed_cache = {}


def feed_detail(osid):
    if osid not in _feed_cache:
        fs = rest(f"feeds/{urllib.parse.quote(osid)}").get("feeds") or []
        _feed_cache[osid] = fs[0] if fs else {}
    return _feed_cache[osid]


def normalize_feed(f):
    """Turn a full Transitland feed record into the fields people ask about."""
    spec = spec_of(f)
    urls = f.get("urls") or {}
    auth = f.get("authorization") or {}
    out = {"onestop_id": f.get("onestop_id"), "name": f.get("name"), "spec": spec}

    if spec == "gtfs":
        out["url"] = urls.get("static_current") or ""
    elif spec == "gtfs-rt":
        out["realtime_types"] = [label for k, label in RT_URL_KEYS if urls.get(k)]
        out["urls"] = {label: urls[k] for k, label in RT_URL_KEYS if urls.get(k)}
    elif spec == "gbfs":
        out["url"] = urls.get("gbfs_auto_discovery") or ""
    else:
        out["urls"] = compact(urls)

    t = auth.get("type") or ""
    out["access"] = "unknown" if "authorization" not in f else "open" if not t else "key_required"
    if t:
        out["auth"] = compact({"type": t, "param_name": auth.get("param_name"), "info_url": auth.get("info_url")})
    out["license"] = compact(f.get("license"))

    versions = f.get("feed_versions") or []
    latest = versions[0] if versions else ((f.get("feed_state") or {}).get("feed_version") or {})
    if spec == "gtfs" and latest:
        end = latest.get("latest_calendar_date")
        out["latest_version"] = compact({
            "fetched_at": latest.get("fetched_at"),
            "sha1": latest.get("sha1"),
            "service_start": latest.get("earliest_calendar_date"),
            "service_end": end,
        })
        if end:
            out["service_status"] = "expired" if end < datetime.date.today().isoformat() else "current"
    state = f.get("feed_state") or {}
    for k in ("last_fetch_error", "last_successful_fetch_at"):
        if state.get(k):
            out[k] = state[k]
    out["transitland_url"] = f"https://www.transit.land/feeds/{f.get('onestop_id')}"
    return compact(out)


def normalize_operator(op, details=True):
    feeds = {"gtfs": [], "gtfs-rt": [], "gbfs": [], "other": []}
    for stub in op.get("feeds") or []:
        if details:
            f = normalize_feed(feed_detail(stub["onestop_id"]) or stub)
        else:
            f = compact({"onestop_id": stub.get("onestop_id"), "name": stub.get("name"), "spec": spec_of(stub)})
        feeds.get(f["spec"], feeds["other"]).append(f)

    places, modes = [], set()
    for a in op.get("agencies") or []:
        for p in a.get("places") or []:
            label = ", ".join(x for x in (p.get("city_name"), p.get("adm1_name"), p.get("adm0_name")) if x)
            if p.get("city_name") and label not in places:
                places.append(label)
        for rt in a.get("route_types_basic") or a.get("route_types") or []:
            modes.add(ROUTE_TYPES.get(rt, str(rt)))
    if not places:  # no city-level match; fall back to state/country
        for a in op.get("agencies") or []:
            for p in a.get("places") or []:
                label = ", ".join(x for x in (p.get("adm1_name"), p.get("adm0_name")) if x)
                if label and label not in places:
                    places.append(label)

    rt_types = sorted({t for f in feeds["gtfs-rt"] for t in f.get("realtime_types", [])})
    summary = {
        "static_gtfs": bool(feeds["gtfs"]),
        "gtfs_rt": bool(feeds["gtfs-rt"]),
        "gbfs": bool(feeds["gbfs"]),
    }
    if details:
        summary["gtfs_rt_types"] = rt_types
        summary["gtfs_rt_access"] = sorted({f["access"] for f in feeds["gtfs-rt"]})
        ends = [f["latest_version"]["service_end"] for f in feeds["gtfs"]
                if f.get("latest_version", {}).get("service_end")]
        summary["gtfs_service_end"] = max(ends) if ends else None

    return compact({
        "onestop_id": op.get("onestop_id"),
        "name": op.get("name"),
        "short_name": op.get("short_name"),
        "website": op.get("website"),
        "places": places,
        "modes": sorted(modes),
        "gtfs_agencies": [compact({"agency_id": a.get("agency_id"), "agency_name": a.get("agency_name")})
                          for a in op.get("agencies") or []],
        "tags": compact({k: v for k, v in (op.get("tags") or {}).items() if k in ("us_ntd_id", "wikidata_id")}),
        "summary": compact(summary) | {k: summary[k] for k in ("static_gtfs", "gtfs_rt", "gbfs")},
        "feeds": {k: v for k, v in feeds.items() if v},
        "transitland_url": f"https://www.transit.land/operators/{op.get('onestop_id')}",
    })


def has_spec(op, wanted):
    return any(spec_of(f) == wanted for f in op.get("feeds") or [])


# ---------------------------------------------------------------- name matching

STOPWORDS = {"the", "of", "and", "public", "transportation", "transit", "authority", "system",
             "services", "service", "district", "agency", "inc", "co", "company"}


def norm(s):
    s = (s or "").lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(w for w in s.split() if w not in STOPWORDS)


def best_match(name, ops):
    nn = norm(name)
    best, score = None, 0.0
    for op in ops:
        labels = [op.get("name"), op.get("short_name")] + [a.get("agency_name") for a in op.get("agencies") or []]
        for label in filter(None, labels):
            cn = norm(label)
            s = difflib.SequenceMatcher(None, nn, cn).ratio()
            if nn and cn and (nn in cn or cn in nn):
                s = max(s, 0.9)
            if s > score:
                best, score = op, s
    return best, round(score, 2)


# ---------------------------------------------------------------- filters

def geo_params(args):
    p = {}
    if getattr(args, "state", None):
        p["adm1_iso" if re.fullmatch(r"[A-Za-z]{2}-[A-Za-z0-9]{1,3}", args.state) else "adm1_name"] = args.state
    if getattr(args, "country", None):
        p["adm0_iso" if re.fullmatch(r"[A-Za-z]{2}", args.country) else "adm0_name"] = args.country
    if getattr(args, "city", None):
        p["city_name"] = args.city
    if args.near:
        try:
            lat, lon = (float(x) for x in args.near.split(","))
        except ValueError:
            sys.exit("--near takes LAT,LON, e.g. --near 47.61,-122.33")
        p.update(lat=lat, lon=lon, radius=args.radius)
    if args.bbox:
        p["bbox"] = args.bbox
    if args.redistribution:
        p["license_redistribution_allowed"] = args.redistribution
    return p


# ---------------------------------------------------------------- output

def csv_row_operator(o):
    s, f = o.get("summary", {}), o.get("feeds", {})
    rt, gtfs, gbfs = f.get("gtfs-rt", []), f.get("gtfs", []), f.get("gbfs", [])
    j = lambda xs: "; ".join(dict.fromkeys(x for x in xs if x))
    return {
        "operator_onestop_id": o.get("onestop_id"),
        "operator_name": o.get("name"),
        "short_name": o.get("short_name", ""),
        "gtfs_agencies": j(a.get("agency_name") for a in o.get("gtfs_agencies", [])),
        "places": j(o.get("places", [])),
        "modes": ", ".join(o.get("modes", [])),
        "website": o.get("website", ""),
        "static_gtfs": "Yes" if s.get("static_gtfs") else "No",
        "static_gtfs_urls": j(x.get("url") for x in gtfs),
        "static_access": j(x.get("access") for x in gtfs),
        "gtfs_service_end": s.get("gtfs_service_end", ""),
        "gtfs_rt": "Yes" if s.get("gtfs_rt") else "No",
        "gtfs_rt_types": ", ".join(s.get("gtfs_rt_types", [])),
        "gtfs_rt_access": j(s.get("gtfs_rt_access", [])),
        "gtfs_rt_redistribution": j(x.get("license", {}).get("redistribution_allowed") for x in rt),
        "gtfs_rt_key_info_url": j(x.get("auth", {}).get("info_url") for x in rt),
        "gtfs_rt_urls": " | ".join(f"{t}: {u}" for x in rt for t, u in x.get("urls", {}).items()),
        "gbfs": "Yes" if s.get("gbfs") else "No",
        "gbfs_urls": j(x.get("url") for x in gbfs),
        "feed_onestop_ids": ", ".join(x["onestop_id"] for fs in f.values() for x in fs),
        "transitland_url": o.get("transitland_url"),
    }


def csv_row_feed(x):
    lv = x.get("latest_version", {})
    return {
        "feed_onestop_id": x.get("onestop_id"),
        "name": x.get("name", ""),
        "spec": x.get("spec"),
        "url": x.get("url", ""),
        "realtime_types": ", ".join(x.get("realtime_types", [])),
        "realtime_urls": " | ".join(f"{t}: {u}" for t, u in x.get("urls", {}).items()),
        "access": x.get("access"),
        "auth_type": x.get("auth", {}).get("type", ""),
        "key_info_url": x.get("auth", {}).get("info_url", ""),
        "redistribution_allowed": x.get("license", {}).get("redistribution_allowed", ""),
        "commercial_use_allowed": x.get("license", {}).get("commercial_use_allowed", ""),
        "spdx_identifier": x.get("license", {}).get("spdx_identifier", ""),
        "service_end": lv.get("service_end", ""),
        "service_status": x.get("service_status", ""),
        "transitland_url": x.get("transitland_url"),
    }


def table_operator(o):
    s = o.get("summary", {})
    rt = ",".join(t.replace("TripUpdates", "TU").replace("VehiclePositions", "VP").replace("Alerts", "AL")
                  for t in s.get("gtfs_rt_types", [])) or ("yes" if s.get("gtfs_rt") else "-")
    acc = "/".join(a.replace("key_required", "key") for a in s.get("gtfs_rt_access", []))
    return [o.get("name", ""), o.get("onestop_id", ""), "yes" if s.get("static_gtfs") else "-",
            s.get("gtfs_service_end", "") or "", rt + (f" ({acc})" if acc else ""), "yes" if s.get("gbfs") else "-"]


def table_feed(x):
    detail = ",".join(x.get("realtime_types", [])) or x.get("url", "")
    return [x.get("onestop_id", ""), x.get("spec", ""), x.get("access", ""),
            x.get("license", {}).get("redistribution_allowed", ""), x.get("latest_version", {}).get("service_end", ""),
            detail[:70]]


def emit(items, fmt, out, kind):
    fh = open(out, "w", newline="") if out else sys.stdout
    try:
        if fmt == "json":
            json.dump(items, fh, indent=2)
            fh.write("\n")
        elif fmt == "jsonl":
            for it in items:
                fh.write(json.dumps(it) + "\n")
        elif fmt == "csv":
            rows = []
            for it in items:
                match = {k: it.pop(k) for k in ("input_name", "match_score") if k in it}
                body = (csv_row_operator(it) if it.get("onestop_id") else {}) if kind == "operator" else csv_row_feed(it)
                rows.append(match | body)
            fields = list(dict.fromkeys(k for r in rows for k in r)) or ["empty"]
            w = csv.DictWriter(fh, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
        else:
            if kind == "operator":
                head = ["name", "onestop_id", "gtfs", "service_end", "gtfs_rt", "gbfs"]
                rows = [([it["input_name"], str(it["match_score"])] if "input_name" in it else [])
                        + (table_operator(it) if it.get("onestop_id") else ["(no match)"] + [""] * 5) for it in items]
                if items and "input_name" in items[0]:
                    head = ["input_name", "score"] + head
            else:
                head = ["onestop_id", "spec", "access", "redistrib", "service_end", "detail"]
                rows = [table_feed(it) for it in items]
            widths = [min(48, max(len(str(c)) for c in col)) for col in zip(head, *rows)]
            for r in [head] + rows:
                fh.write("  ".join(str(c)[:w].ljust(w) for c, w in zip(r, widths)).rstrip() + "\n")
    finally:
        if out:
            fh.close()
    if out:
        print(f"Wrote {len(items)} {kind}s to {out} ({len(_feed_cache)} feed lookups)", file=sys.stderr)


# ---------------------------------------------------------------- commands

def cmd_agencies(args):
    names = [l.strip() for l in open(args.names) if l.strip()] if args.names else None
    params = geo_params(args)
    if args.search:
        params["search"] = args.search
    if args.feed:
        params["feed_onestop_id"] = args.feed

    if args.id:
        ops = []
        for osid in args.id:
            ops += rest(f"operators/{urllib.parse.quote(osid)}").get("operators") or []
    elif names and not params:
        ops = None  # search each name separately
    elif params:
        ops = rest("operators", params | {"limit": 100}, all_pages=True, max_items=args.limit)["operators"]
    else:
        sys.exit("Give a search term, --id, a geographic filter (--state/--country/--city/--near/--bbox), or --names.")

    if names:
        results = []
        for n in names:
            pool = ops if ops is not None else rest("operators", {"search": n, "limit": 20}).get("operators") or []
            best, score = best_match(n, pool)
            if best and has_spec_ok(best, args.has) and score >= args.min_score:
                results.append({"input_name": n, "match_score": score} | normalize_operator(best, not args.brief))
            else:
                results.append({"input_name": n, "match_score": score})
    else:
        results = [normalize_operator(op, not args.brief) for op in ops if has_spec_ok(op, args.has)]
    emit(results, args.format, args.out, "operator")


def has_spec_ok(op, wanted):
    return not wanted or all(has_spec(op, w) for w in wanted)


def cmd_feeds(args):
    params = geo_params(args)
    if args.search:
        params["search"] = args.search
    if args.spec:
        params["spec"] = args.spec
    if not params:
        sys.exit("Give a search term, --spec, or a geographic filter.")
    feeds = rest("feeds", params | {"limit": 100}, all_pages=True, max_items=args.limit)["feeds"]
    emit([normalize_feed(f) for f in feeds], args.format, args.out, "feed")


def cmd_feed(args):
    emit([normalize_feed(feed_detail(i)) for i in args.onestop_id if feed_detail(i)] , args.format, args.out, "feed")
    missing = [i for i in args.onestop_id if not feed_detail(i)]
    if missing:
        print("Not found: " + ", ".join(missing), file=sys.stderr)


def main():
    global PAUSE
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pause", type=float, default=PAUSE, help="seconds between requests (default 0.5)")
    sp = p.add_subparsers(dest="cmd", required=True)

    def common(sub, geo=True):
        if geo:
            sub.add_argument("--state", help="US-WA (ISO 3166-2) or a name like Washington")
            sub.add_argument("--country", help="US (ISO 3166-1) or a name")
            sub.add_argument("--city")
            sub.add_argument("--near", metavar="LAT,LON")
            sub.add_argument("--radius", type=float, default=10000, help="meters, with --near (default 10000)")
            sub.add_argument("--bbox", metavar="MINLON,MINLAT,MAXLON,MAXLAT")
            sub.add_argument("--redistribution", choices=["yes", "no", "unknown", "exclude_no"],
                             help="filter by license redistribution_allowed")
            sub.add_argument("--limit", type=int, help="stop after this many results")
        sub.add_argument("--format", choices=["json", "jsonl", "csv", "table"], default="json")
        sub.add_argument("--out", help="write to this file instead of stdout")

    a = sp.add_parser("agencies", help="find operators and describe their feeds")
    a.add_argument("search", nargs="?", help="full-text search on operator name")
    a.add_argument("--id", nargs="+", metavar="O-ONESTOP_ID", help="specific operator Onestop IDs")
    a.add_argument("--feed", metavar="F-ONESTOP_ID", help="operators attached to this feed")
    a.add_argument("--has", nargs="+", choices=["gtfs", "gtfs-rt", "gbfs"], help="only operators with these feed types")
    a.add_argument("--names", metavar="FILE", help="agency names, one per line; returns the best match for each")
    a.add_argument("--min-score", type=float, default=0.6, help="with --names, blank out matches below this")
    a.add_argument("--brief", action="store_true", help="skip per-feed detail lookups (fewer requests)")
    common(a)

    f = sp.add_parser("feeds", help="search feeds directly (good for GBFS)")
    f.add_argument("search", nargs="?")
    f.add_argument("--spec", choices=["gtfs", "gtfs-rt", "gbfs"])
    common(f)

    d = sp.add_parser("feed", help="normalized detail for specific feeds")
    d.add_argument("onestop_id", nargs="+")
    common(d, geo=False)

    r = sp.add_parser("rest", help="raw REST GET")
    r.add_argument("path"); r.add_argument("params", nargs="*"); r.add_argument("--all", action="store_true")
    g = sp.add_parser("graphql", help="raw GraphQL POST (paid plans)")
    g.add_argument("query"); g.add_argument("--vars", default="{}")

    args = p.parse_args()
    PAUSE = args.pause
    if args.cmd == "rest":
        params = dict(kv.split("=", 1) for kv in args.params)
        print(json.dumps(rest(args.path, params, args.all), indent=2))
    elif args.cmd == "graphql":
        q = open(args.query).read() if os.path.exists(args.query) else args.query
        print(json.dumps(graphql(q, json.loads(args.vars)), indent=2))
    else:
        {"agencies": cmd_agencies, "feeds": cmd_feeds, "feed": cmd_feed}[args.cmd](args)


if __name__ == "__main__":
    main()
