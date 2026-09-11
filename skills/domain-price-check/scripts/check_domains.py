#!/usr/bin/env python3
"""
Check domain availability, registry premium tier, and launch-phase pricing.

Three providers, tried in this order unless --provider forces one:

  gandi-api   Documented GET /v5/domain/check. Needs GANDI_API_KEY (free
              Personal Access Token). Returns availability + premium tier +
              per-phase prices. This is the only supported API that prices a
              TLD before it reaches General Availability.
  rdap        Free, universal, no key. Availability ONLY (no prices).

Usage:
  check_domains.py --names signhere,meetme --tlds here
  check_domains.py --names-file names.txt --tlds here,com,io --json
  check_domains.py --tld-info here
"""

import argparse
import json
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

GANDI_API = "https://api.gandi.net/v5/domain/check"
RDAP_BOOTSTRAP = "https://data.iana.org/rdap/dns.json"
_BOOTSTRAP = None
UA = "domain-price-check/1.0"

# Phase names a registry may report. "golive" is General Availability - the
# price a normal buyer eventually pays, and so the one worth sorting on.
GA_PHASES = ("golive", "ga", "general", "open")


def _get(url, headers=None, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", "replace")


_AUTH_WARNING = None


class AuthError(RuntimeError):
    """Bad or missing credentials - retrying cannot help, so fail loudly."""


def _retry(fn, tries=5, delay=0.7):
    """The API returns sporadic 503s under light load; those are worth retrying."""
    last = None
    for i in range(tries):
        try:
            return fn()
        except AuthError:
            raise
        except Exception as e:  # noqa: BLE001 - transport errors are retryable
            last = e
            time.sleep(delay * (i + 1))
    raise last


def _pick(products, process):
    for p in products or []:
        if p.get("process") == process:
            return p
    return None


def _phase_price(product):
    """
    Map each price to its launch phase.

    The prices[] and periods[]/phases[] arrays look parallel but are NOT - the
    registry returns prices in arbitrary order and tags each one with
    options.phase. Zipping by index silently mis-reports the whole EAP ladder
    (it only appears to work because golive often lands last), so key on the
    tag and fall back to positional order only when the tag is absent.
    """
    prices = product.get("prices") or []
    metas = product.get("periods") or product.get("phases") or []
    ladder = {}
    for i, pr in enumerate(prices):
        name = (pr.get("options") or {}).get("phase")
        if not name and i < len(metas):
            name = metas[i].get("name")
        if name:
            ladder[name] = pr.get("price")
    if metas:  # present them in the registry's own chronological order
        ladder = {m["name"]: ladder[m["name"]]
                  for m in metas if m.get("name") in ladder}

    ga = next((ladder[k] for k in GA_PHASES if k in ladder), None)
    if ga is None:
        ga = prices[0].get("price") if prices else None
    ptype = "premium" if any(p.get("type") == "premium" for p in prices) else (
        prices[0].get("type") if prices else None)
    return ga, ptype, ladder, metas


def _shape(fqdn, currency, create, renew, available, premium, reserved):
    ga, ctype, ladder, metas = _phase_price(create) if create else (None, None, {}, [])
    rn, rtype, _, _ = _phase_price(renew) if renew else (None, None, {}, [])
    ptype = ctype or rtype
    return {
        "domain": fqdn,
        "available": available,
        "premium": bool(premium) or ptype == "premium",
        "reserved": bool(reserved),
        "currency": currency,
        "first_year": ga,
        "renewal": rn,
        "phases": ladder,
        "phase_dates": {m.get("name"): m.get("starts_at") for m in metas if m.get("name")},
        "tier": "premium" if (premium or ptype == "premium") else "standard",
    }


def via_gandi_api(fqdn, key, currency, country):
    q = urllib.parse.urlencode(
        [("name", fqdn), ("processes", "create"), ("processes", "renew"),
         ("currency", currency), ("country", country)]
    )
    hdr = {"Authorization": f"Bearer {key}", "Accept": "application/json"}

    def call():
        try:
            st, body = _get(f"{GANDI_API}?{q}", hdr)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise AuthError(
                    f"Gandi rejected the API key (HTTP {e.code}). Check that "
                    "GANDI_API_KEY holds a current Personal Access Token and "
                    "that its organisation has domain access.") from e
            raise
        if st != 200:
            raise RuntimeError(f"HTTP {st}")
        return json.loads(body)

    data = _retry(call)
    products = data.get("products") or []
    create, renew = _pick(products, "create"), _pick(products, "renew")
    status = (create or {}).get("status") or (products[0].get("status") if products else "unknown")
    avail = status in ("available", "available_reserved")
    prices = (create or {}).get("prices") or []
    premium = any(p.get("type") == "premium" for p in prices)
    return _shape(fqdn, data.get("currency", currency), create, renew, avail,
                  premium, status == "unavailable_reserved")


def _rdap_servers():
    """
    TLD -> authoritative RDAP base URL, from IANA's bootstrap registry.

    This matters for correctness, not speed. A generic proxy like rdap.org
    returns 404 both for "this name is unregistered" and for "I have no server
    for this TLD", and roughly 300 TLDs - .io among them - have no RDAP service
    at all. Reading those 404s as "available" reports registered domains as free:
    google.io comes back 404. So resolve the real server, and when a TLD has
    none, report unknown rather than guessing.
    """
    global _BOOTSTRAP
    if _BOOTSTRAP is not None:
        return _BOOTSTRAP
    cache = os.path.join(tempfile.gettempdir(), "rdap-bootstrap.json")
    body = None
    try:
        if os.path.exists(cache) and time.time() - os.path.getmtime(cache) < 7 * 86400:
            body = open(cache).read()
    except OSError:
        body = None
    if body is None:
        _, body = _get(RDAP_BOOTSTRAP, {"Accept": "application/json"}, timeout=30)
        try:
            with open(cache, "w") as fh:
                fh.write(body)
        except OSError:
            pass
    servers = {}
    for entry in json.loads(body).get("services", []):
        tlds, urls = (entry + [[], []])[:2]
        if not urls:
            continue
        for t in tlds:
            servers[t.lower().lstrip(".")] = urls[0].rstrip("/") + "/"
    _BOOTSTRAP = servers
    return servers


def _rdap_unknown(fqdn, note):
    return {"domain": fqdn, "available": None, "premium": None, "reserved": None,
            "currency": None, "first_year": None, "renewal": None, "phases": {},
            "phase_dates": {}, "tier": "unknown", "note": note}


def via_rdap(fqdn):
    tld = fqdn.rsplit(".", 1)[-1].lower()
    try:
        base = _rdap_servers().get(tld)
    except Exception as e:  # noqa: BLE001 - bootstrap unreachable
        return _rdap_unknown(fqdn, f"RDAP bootstrap unavailable: {e}")
    if not base:
        return _rdap_unknown(fqdn, f".{tld} has no RDAP service - availability "
                                   "cannot be determined without a registrar API")
    try:
        st, _ = _get(base + "domain/" + fqdn,
                     {"Accept": "application/rdap+json"}, timeout=20)
        registered = st == 200
    except urllib.error.HTTPError as e:
        if e.code == 404:
            registered = False
        elif e.code in (403, 429, 501):
            return _rdap_unknown(fqdn, f"RDAP server returned {e.code}")
        else:
            raise
    return {"domain": fqdn, "available": not registered, "premium": None,
            "reserved": None, "currency": None, "first_year": None,
            "renewal": None, "phases": {}, "phase_dates": {}, "tier": "unknown"}


def check_one(fqdn, provider, key, currency, country):
    order = [provider] if provider != "auto" else (
        ["gandi-api", "rdap"] if key else ["rdap"]
    )
    errs = []
    for p in order:
        try:
            if p == "gandi-api":
                if not key:
                    raise RuntimeError("GANDI_API_KEY not set")
                r = via_gandi_api(fqdn, key, currency, country)
            else:
                r = via_rdap(fqdn)
            r["provider"] = p
            return r
        except AuthError as e:
            global _AUTH_WARNING
            _AUTH_WARNING = str(e)
            errs.append(f"{p}: {e}")
        except Exception as e:  # noqa: BLE001 - fall through to the next provider
            errs.append(f"{p}: {e}")
    return {"domain": fqdn, "available": None, "premium": None, "reserved": None,
            "currency": None, "first_year": None, "renewal": None, "phases": {},
            "tier": "error", "provider": None, "error": "; ".join(errs)}


def tld_info(tld, currency, country, key, provider="auto"):
    """Launch-phase ladder for a TLD, probed with a name unlikely to be premium."""
    probe = f"zq7x{int(time.time()) % 9973}probe.{tld.lstrip('.')}"
    r = check_one(probe, provider, key, currency, country)
    return {"tld": "." + tld.lstrip("."), "probe": probe,
            "standard_first_year": r.get("first_year"), "standard_renewal": r.get("renewal"),
            "currency": r.get("currency"), "phases": r.get("phases", {}),
            "phase_dates": r.get("phase_dates", {}),
            "provider": r.get("provider"), "error": r.get("error")}


def fmt(rows, currency_hint=""):
    if not rows:
        return "(no results)"
    cur = next((r["currency"] for r in rows if r.get("currency")), currency_hint or "")
    w = max(len(r["domain"]) for r in rows) + 2
    out = [f"{'DOMAIN'.ljust(w)}{'STATUS'.ljust(12)}{'TIER'.ljust(11)}"
           f"{('1ST YR ' + cur).ljust(13)}{('RENEWAL ' + cur).ljust(13)}"]
    out.append("-" * len(out[0]))
    for r in rows:
        if r.get("tier") == "error":
            status = "error"
        elif r["available"] is None:
            status = "unknown"
        elif r["available"]:
            status = "available"
        else:
            status = "taken"
        if r.get("reserved"):
            status = "reserved"
        tier = r.get("tier") or "-"
        if status in ("taken", "error", "unknown"):
            tier = "-"
        fy = "-" if r.get("first_year") is None else f"{r['first_year']:,.2f}"
        rn = "-" if r.get("renewal") is None else f"{r['renewal']:,.2f}"
        out.append(f"{r['domain'].ljust(w)}{status.ljust(12)}"
                   f"{tier.ljust(11)}{fy.ljust(13)}{rn.ljust(13)}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--names", help="comma-separated labels, e.g. signhere,meetme")
    ap.add_argument("--names-file", help="file with one label (or full domain) per line")
    ap.add_argument("--tlds", default="com", help="comma-separated TLDs (default: com)")
    ap.add_argument("--tld-info", help="show the launch-phase ladder for one TLD")
    ap.add_argument("--provider", default="auto",
                    choices=["auto", "gandi-api", "rdap"])
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--country", default="US", help="ISO country, affects tax display")
    ap.add_argument("--concurrency", type=int, default=3,
                    help="keep low; the API 503s sporadically when pushed")
    ap.add_argument("--available-only", action="store_true")
    ap.add_argument("--standard-only", action="store_true",
                    help="hide registry-premium names")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    key = os.environ.get("GANDI_API_KEY")
    if not key and a.provider == "auto":
        print("No GANDI_API_KEY set - availability only, no prices or premium "
              "tiers.\n  Get a free key: gandi.net -> User Settings -> "
              "Authentication options -> Personal Access Token, then\n"
              "  export GANDI_API_KEY=...\n", file=sys.stderr)

    if a.tld_info:
        info = tld_info(a.tld_info, a.currency, a.country, key, a.provider)
        if a.json:
            print(json.dumps(info, indent=2))
            return
        print(f"{info['tld']}  (standard tier, via {info['provider'] or 'n/a'})")
        if info.get("error"):
            print(f"  error: {info['error']}")
        print(f"  first year : {info['standard_first_year']} {info['currency'] or ''}")
        print(f"  renewal    : {info['standard_renewal']} {info['currency'] or ''}")
        if info["phases"]:
            dates = info.get("phase_dates") or {}
            by_price = {}
            for k, v in info["phases"].items():
                by_price.setdefault(v, []).append(k)
            print(f"  launch phases (price to register during each, "
                  f"{info['currency'] or ''}):")
            for k, v in info["phases"].items():
                when = (dates.get(k) or "")[:16].replace("T", " ")
                same = by_price.get(v, [])
                flag = "  <- same price as " + ", ".join(x for x in same if x != k) \
                    if len(same) > 1 and k != same[0] else ""
                print(f"    {k:<9} {str(v):>10}   {when}{flag}")
            eap = {k: v for k, v in info["phases"].items() if k.startswith("eap")}
            if eap:
                cheapest = min(eap.values())
                first = next(k for k, v in eap.items() if v == cheapest)
                ga = info["standard_first_year"]
                print(f"\n  Cheapest early-access rung is {cheapest} at {first} "
                      f"({(dates.get(first) or '')[:16].replace('T', ' ')}).")
                if ga:
                    print(f"  That is a one-off surcharge of ~{round(cheapest - ga, 2)} "
                          f"over the {ga} general-availability price, and it buys a "
                          f"head start, not a guarantee.")
                print("  Register on the FIRST day of a rung - later days in the same "
                      "rung cost identically and buy less exclusivity.")
        elif info["standard_first_year"] is not None:
            print("  (no launch phases - TLD is in general availability)")
        return

    labels = []
    if a.names:
        labels += [x.strip() for x in a.names.split(",") if x.strip()]
    if a.names_file:
        with open(a.names_file) as fh:
            labels += [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]
    if not labels:
        ap.error("need --names, --names-file or --tld-info")

    tlds = [t.strip().lstrip(".") for t in a.tlds.split(",") if t.strip()]
    fqdns, seen = [], set()
    for lb in labels:
        cands = [lb.lower()] if re.search(r"\.[a-z]{2,}$", lb.lower()) else \
                [f"{lb.lower()}.{t}" for t in tlds]
        for c in cands:
            if c not in seen:
                seen.add(c)
                fqdns.append(c)

    with ThreadPoolExecutor(max_workers=max(1, a.concurrency)) as ex:
        rows = list(ex.map(
            lambda f: check_one(f, a.provider, key, a.currency, a.country), fqdns))

    if a.available_only:
        rows = [r for r in rows if r.get("available")]
    if a.standard_only:
        rows = [r for r in rows if r.get("tier") == "standard"]
    # Cheapest first, but unknown prices sink to the bottom rather than sorting as free.
    rows.sort(key=lambda r: (r.get("renewal") is None, r.get("renewal") or 0, r["domain"]))

    if _AUTH_WARNING:
        print(f"\n  !! {_AUTH_WARNING}\n     Falling back to availability only - "
              "the prices below are missing, not free.\n", file=sys.stderr)

    if a.json:
        print(json.dumps(rows, indent=2))
    else:
        print(fmt(rows, a.currency))
        notes = [r for r in rows if r.get("note")]
        if notes:
            print("", file=sys.stderr)
            for r in notes:
                print(f"  ? {r['domain']}: {r['note']}", file=sys.stderr)
        errs = [r for r in rows if r.get("error")]
        if errs:
            print(f"\n{len(errs)} lookup(s) failed:", file=sys.stderr)
            for r in errs[:5]:
                print(f"  {r['domain']}: {r['error']}", file=sys.stderr)


if __name__ == "__main__":
    main()
